"""Build and verify signed, reproducible skill releases.

build:  scan -> write MANIFEST.json (SHA-256 of every file) -> deterministic
        .skill zip -> .sha256 file -> optional SSH signature (.sig).
verify: zip-slip check -> manifest hashes -> checksum -> signature -> re-scan.

    python -m skill_store.release build paid-skills/tutor-coding-sma \
        --version 1.0.0 --license docs/EULA.md --key ~/.ssh/skill_signing
    python -m skill_store.release verify dist/tutor-coding-sma-1.0.0.skill \
        --allowed-signers allowed_signers --identity aria@skillstore

Signatures use `ssh-keygen -Y sign` (OpenSSH >= 8.1), which every buyer on
Linux, macOS, and Windows 10+ already has, so no extra install is needed.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from skill_store.scan import is_blocking, scan_skill

NAMESPACE = "skill-release"
FIXED_DATE = (1980, 1, 1, 0, 0, 0)
SKIP_PARTS = {"__pycache__", ".git", "evals"}


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def collect_files(skill_dir):
    files = {}
    for path in sorted(skill_dir.rglob("*")):
        rel = path.relative_to(skill_dir)
        if path.is_file() and not SKIP_PARTS.intersection(rel.parts) and rel.name != "MANIFEST.json":
            files[rel.as_posix()] = path.read_bytes()
    return files


def build(skill_dir, version, out_dir, publisher, license_path=None, key=None):
    skill_dir = Path(skill_dir).resolve()
    findings = scan_skill(skill_dir)
    if is_blocking(findings):
        raise SystemExit("scan failed; fix HIGH findings first:\n" +
                         "\n".join(str(f) for f in findings))

    name = skill_dir.name
    files = collect_files(skill_dir)
    if license_path:
        files["LICENSE.md"] = Path(license_path).read_bytes()
    manifest = {
        "name": name,
        "version": version,
        "publisher": publisher,
        "policy": "instruction-only: no executable code, no network access",
        "files": {rel: sha256_bytes(data) for rel, data in sorted(files.items())},
    }
    files["MANIFEST.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    archive = out_dir / f"{name}-{version}.skill"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in sorted(files):
            info = zipfile.ZipInfo(f"{name}/{rel}", date_time=FIXED_DATE)
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, files[rel])

    digest = sha256_bytes(archive.read_bytes())
    Path(f"{archive}.sha256").write_text(f"{digest}  {archive.name}\n")
    if key:
        subprocess.run(["ssh-keygen", "-Y", "sign", "-f", str(key), "-n", NAMESPACE, str(archive)],
                       check=True, capture_output=True)
    return archive, digest


def _safe_members(zf):
    for member in zf.namelist():
        path = PurePosixPath(member)
        if path.is_absolute() or ".." in path.parts or "\\" in member:
            raise ValueError(f"unsafe path in archive: {member}")
    return zf.namelist()


def verify(archive, allowed_signers=None, identity=None):
    """Return a list of human-readable check results; raise ValueError on failure."""
    archive = Path(archive)
    report = []
    data = archive.read_bytes()
    digest = sha256_bytes(data)

    checksum_file = Path(f"{archive}.sha256")
    if checksum_file.exists():
        expected = checksum_file.read_text().split()[0]
        if expected != digest:
            raise ValueError("checksum mismatch: archive was modified after release")
        report.append("checksum OK")

    sig = Path(f"{archive}.sig")
    if allowed_signers:
        if not sig.exists() or not identity:
            raise ValueError("signature check requested but .sig file or identity is missing")
        result = subprocess.run(
            ["ssh-keygen", "-Y", "verify", "-f", str(allowed_signers), "-I", identity,
             "-n", NAMESPACE, "-s", str(sig)],
            input=data, capture_output=True)
        if result.returncode != 0:
            raise ValueError("signature INVALID: " + result.stderr.decode(errors="replace").strip())
        report.append(f"signature OK ({identity})")

    with zipfile.ZipFile(archive) as zf:
        members = _safe_members(zf)
        roots = {PurePosixPath(m).parts[0] for m in members}
        if len(roots) != 1:
            raise ValueError(f"archive must contain exactly one top folder, found {sorted(roots)}")
        root = roots.pop()
        manifest = json.loads(zf.read(f"{root}/MANIFEST.json"))
        listed = set(manifest["files"])
        present = {m[len(root) + 1:] for m in members if not m.endswith("/")} - {"MANIFEST.json"}
        if listed != present:
            raise ValueError(f"manifest/file mismatch: extra={sorted(present - listed)} "
                             f"missing={sorted(listed - present)}")
        for rel, expected in manifest["files"].items():
            if sha256_bytes(zf.read(f"{root}/{rel}")) != expected:
                raise ValueError(f"hash mismatch for {rel}")
        report.append(f"manifest OK ({len(listed)} files, {manifest['name']} {manifest['version']})")

        with tempfile.TemporaryDirectory() as tmp:
            zf.extractall(tmp, members)
            findings = scan_skill(Path(tmp) / root)
    if is_blocking(findings):
        raise ValueError("safety scan FAILED:\n" + "\n".join(str(f) for f in findings))
    report.append(f"safety scan OK ({len(findings)} non-blocking finding(s))")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build or verify skill releases.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="package a skill folder into a signed .skill")
    b.add_argument("skill_dir")
    b.add_argument("--version", required=True)
    b.add_argument("--out", default="dist")
    b.add_argument("--publisher", default="Aria Hendrawan")
    b.add_argument("--license", dest="license_path")
    b.add_argument("--key", help="SSH private key used to sign the release")

    v = sub.add_parser("verify", help="check a .skill before installing it")
    v.add_argument("archive")
    v.add_argument("--allowed-signers")
    v.add_argument("--identity")

    args = parser.parse_args(argv)
    if args.cmd == "build":
        if args.key and not shutil.which("ssh-keygen"):
            raise SystemExit("ssh-keygen not found; install OpenSSH to sign releases")
        archive, digest = build(args.skill_dir, args.version, args.out, args.publisher,
                                args.license_path, args.key)
        print(f"built {archive}\nsha256 {digest}")
        return 0
    try:
        for line in verify(args.archive, args.allowed_signers, args.identity):
            print(f"✔ {line}")
    except (ValueError, KeyError, zipfile.BadZipFile) as exc:
        print(f"✘ {exc}")
        return 1
    print("SAFE TO INSTALL")
    return 0


if __name__ == "__main__":
    sys.exit(main())
