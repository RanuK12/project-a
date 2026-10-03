# project-a: Bounty Scout & Verified Skills

Dua alat penghasil pendapatan ≥ US$10/minggu:

1. **Verified Skills**: toko skill AI berbayar yang aman (lihat di bawah).
2. **Bounty Scout**: agen mingguan pencari bounty open-source (lihat bagian berikutnya).

## Verified Skills

Skill AI (format `SKILL.md`, dipakai Claude dan dapat diadaptasi untuk ChatGPT/Gemini)
yang **hanya berisi instruksi** (tanpa kode yang dapat dieksekusi), dipindai,
di-*hash*, dan ditandatangani sehingga pembeli dapat memastikan skill tidak
disusupi kode berbahaya. Rencana bisnis lengkap: [docs/SKILL_STORE.md](docs/SKILL_STORE.md).

| Komponen | Isi |
|---|---|
| `skills/skill-safety-check/` | Skill **gratis**: mengaudit skill pihak ketiga sebelum dipasang |
| `skill_store/scan.py` | Pemindai statis: tipe file, prompt injection, Unicode tersembunyi, *payload* terenkode, endpoint eksfiltrasi, akses kredensial |
| `skill_store/release.py` | Build rilis reprodusibel + manifest SHA-256 + tanda tangan SSH; `verify` untuk pembeli |
| `docs/EULA.md` | Lisensi satu pengguna untuk skill berbayar |
| `paid-skills/` | **Tidak di-commit** (di-*gitignore*). Skill berbayar disimpan di repositori privat |

```bash
python -m skill_store.scan skills/*                       # pindai
python -m skill_store.release build <folder-skill> --version 1.0.0 --license docs/EULA.md --key ~/.ssh/skill_signing
python -m skill_store.release verify dist/<nama>-1.0.0.skill --allowed-signers allowed_signers --identity <id>
```

## Bounty Scout

Agen mingguan yang mencari **open-source bounty berbayar** (≥ US$10) di GitHub yang
cocok dengan keahlian AI/ML, Computer Vision, GIS, IoT, dan Python, lalu
menerbitkan laporan berperingkat sebagai *issue* setiap Senin pagi.

Strategi pendapatan dari riset (produk digital, jasa metodologi, kompetisi)
ada di [docs/INCOME_PLAYBOOK.md](docs/INCOME_PLAYBOOK.md).

## Cara kerja

1. `.github/workflows/weekly-bounty-scout.yml` berjalan tiap Senin 07:47 WIB
   (atau manual lewat tab *Actions → Run workflow*).
2. `bounty_scout/scout.py` menelusuri issue terbuka tanpa assignee berlabel
   `💎 Bounty` (Algora), `bounty`, dan `issuehunt`.
3. Issue dibuang jika: tanpa nominal, di bawah `--min-amount`, di luar bidang
   (tidak ada kata kunci AI/ML/CV/GIS/IoT/Python), bukan repositori milik
   organisasi, bintang < `--min-stars` (default 500), atau nama repositorinya
   mengandung "bounty" (indikasi *bounty farm*).
4. Sisanya diberi skor: kecocokan bidang, nilai bounty, bonus label Algora
   (dana di-*escrow* platform), tingkat persaingan, dan kebaruan.
5. 20 teratas beserta ringkasan alasan penyaringan diterbitkan sebagai issue
   berlabel `bounty-scout`.

## Menjalankan lokal

```bash
export GITHUB_TOKEN=ghp_...        # opsional, menaikkan rate limit
python -m bounty_scout.scout --min-amount 25 --top 10
python -m unittest discover -s tests -v
```

Sesuaikan `KEYWORDS` dan `PENALTIES` di `bounty_scout/scout.py` dengan keahlian Anda.

## Batasan

Agen ini **mencari dan memeringkat** peluang. Klaim bounty, pengiriman PR, dan
penerimaan dana tetap dilakukan melalui akun Anda sendiri, setelah kode Anda
tinjau.
