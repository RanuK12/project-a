# project-a: Bounty Scout

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
