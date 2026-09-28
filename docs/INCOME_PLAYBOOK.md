# Playbook: ≥ US$10/Minggu dari Kode dan Riset

Target: US$10/minggu ≈ US$43/bulan ≈ US$520/tahun. Tidak harus tiap minggu ada
transaksi; satu *payout* US$50 menutup ±5 minggu. Yang dibutuhkan adalah
**pipeline** yang konsisten, bukan keberuntungan.

## 1. Portofolio sumber pendapatan

| # | Kanal | Jenis | Kisaran nilai | Waktu ke uang pertama | Kecocokan bidang | Catatan risiko |
|---|-------|-------|---------------|-----------------------|------------------|----------------|
| A | Open-source bounty (Algora, IssueHunt, label "bounty") | Kode | US$20–500/issue | 1–3 minggu | Python, ML, CV, GIS | Kompetitif; banyak repo melarang PR AI berkualitas rendah |
| B | Kaggle / DrivenData / Zindi competitions | Riset + kode | Hadiah tim, sering > US$1.000 | 1–3 bulan | ML, CV, geospasial | Tidak pasti; hanya top-N dibayar |
| C | Jasa analisis data/ML mikro (Upwork, Fiverr, Sribulancer, Projects.co.id) | Kode | US$15–150/proyek | 2–4 minggu | Semua | Butuh profil & ulasan awal |
| D | Produk digital: template LaTeX, notebook tutorial CV/GIS, dataset beranotasi (Gumroad, Lynk.id, Karyakarsa) | Riset | US$3–30/unit, pasif | 1–2 bulan | Buku ajar, modul | Perhatikan hak cipta dan lisensi data |
| E | GitHub Sponsors / Ko-fi / Trakteer untuk tool open-source | Kode | US$1–10/sponsor/bulan | 2–6 bulan | Tool riset yang berguna | Butuh basis pengguna |
| F | Honorarium narasumber, reviewer proposal hibah, penilai eksternal, pelatihan metodologi | Riset | Rp500 rb–3 jt/kegiatan | Tergantung undangan | Penjaminan mutu, akreditasi | Ikuti aturan konflik kepentingan institusi |
| G | Konsultasi statistik/metodologi untuk mahasiswa pascasarjana dan peneliti | Riset | Rp250 rb–1 jt/sesi | 1–2 minggu | Metodologi | **Jangan** mengerjakan tugas atau tesis orang lain (pelanggaran integritas akademik) |

> Catatan: peer review jurnal Scopus umumnya **tidak dibayar tunai**. Voucher APC
> atau kredit Web of Science Reviewer Recognition bukan pendapatan. Jangan
> jadikan itu target.

## 2. Rekomendasi kombinasi (paling realistis)

1. **A (bounty)**: otomatis lewat `bounty_scout`. Ambil 1 issue/bulan senilai ≥ US$50.
2. **D (produk digital)**: ubah materi ajar yang sudah ada (mis. modul YOLO, praktikum
   QGIS, template artikel Scopus) menjadi paket berbayar US$5–15. Pendapatan pasif.
3. **F/G**: jasa yang memanfaatkan reputasi sebagai editor/reviewer. Nilai per jam
   tertinggi, dan sering sudah cukup untuk melampaui target.

## 3. Siklus mingguan (PPEPP diterapkan pada pendapatan pribadi)

| Tahap | Aktivitas | Waktu | Indikator |
|-------|-----------|-------|-----------|
| **Penetapan** | Target ≥ US$10/minggu; batas waktu maks. 4 jam/minggu | – | Target tertulis |
| **Pelaksanaan** | Senin: baca issue *Bounty Scout*; pilih ≤ 1 issue; kerjakan 2–3 jam | 3 jam | 1 PR/klaim per 2 minggu |
| **Evaluasi** | Jumat: catat pendapatan, jam kerja, tingkat merge PR | 15 menit | US$/jam, *win-rate* |
| **Pengendalian** | Win-rate < 25% selama sebulan → sempitkan `KEYWORDS` atau alihkan waktu ke kanal D/F | 15 menit | Tren membaik |
| **Peningkatan** | Tiap kuartal: naikkan `--min-amount`, tambah produk digital | 1 jam | Pendapatan per jam naik |

## 4. Etika dan kepatuhan

- Seluruh pembayaran masuk ke akun milik Anda sendiri (Algora/Stripe/PayPal/Wise).
  Agen tidak dapat dan tidak boleh memegang akun atau dana.
- Tinjau dan pahami setiap kode sebelum dikirim. Banyak maintainer menutup atau
  memblokir PR hasil AI yang tidak diverifikasi.
- Laporkan pendapatan dalam SPT (PPh orang pribadi).
- Pekerjaan luar institusi mengikuti ketentuan kepegawaian dan konflik kepentingan kampus.
