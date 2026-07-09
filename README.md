# Antigravity IDE Conversation Renamer

A powerful Desktop GUI application built with Python and PyQt5 to force-rename conversation titles in the Google Antigravity IDE without breaking its internal Protobuf binary cache.

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-GUI-green.svg)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey.svg)
![Protobuf](https://img.shields.io/badge/Data-Protobuf-orange.svg)

---

## 📖 Latar Belakang (The Story)

Secara bawaan, IDE *Advanced Agentic* dari Google (Antigravity IDE) menyusun judul percakapan secara otomatis dari *prompt* pengguna. Sayangnya, tidak ada antarmuka atau tombol bawaan di dalam UI IDE untuk me-*rename* atau mengganti judul percakapan tersebut sesuai keinginan pengguna. Hal ini menyulitkan manajemen riwayat pekerjaan jika banyak *thread* obrolan dengan *prompt* awal yang bertele-tele.

Eksplorasi awal menemukan bahwa Antigravity IDE tidak menyimpan konfigurasi UI mentah (seperti file konfigurasi atau teks JSON sederhana) untuk daftar percakapan di *sidebar*, melainkan menanam data utamanya di dalam sekumpulan *file database* SQLite (berakhiran `.db`) di dalam folder profil lokal:
`~/.gemini/antigravity-ide/conversations/`

### Tantangan Protobuf (The Length Prefix Curse)

Masalah utama terjadi ketika mencoba memanipulasi *database* secara langsung:
1. Data tidak disimpan dalam bentuk tabel yang mudah diurai, melainkan dalam **Blob Biner** yang dienkode menggunakan format **Protocol Buffers (Protobuf)**.
2. Protobuf menggunakan skema **Varint Length-Prefixing** yang melacak ketat ukuran *bytes* pada setiap struktur *(nested messages)*.
3. Mencoba menyuntikkan judul baru (yang panjangnya berbeda dari judul aslinya) melalui teknik injeksi biner/heksadesimal *brute force* akan **membuat *database* korup**. IDE menolak membaca biner tersebut dan mekanisme *fallback*-nya akan merusak tampilan, mengganti judul dengan teks prompt awal yang sangat panjang.
4. Teknik *padding* (mengganti string persis sama panjang dengan menambahkan spasi) sempat berhasil sebagai penambal *hack*, namun tidak memberikan kebebasan mutlak kepada pengguna untuk menggunakan judul sebebas mungkin.

### Solusi Final (Blackboxprotobuf)

Untuk memberikan manipulasi judul yang mutlak dan permanen, *tool* ini memanfaatkan pustaka **`blackboxprotobuf`**.
- Skrip ini akan menarik *Blob* biner SQLite.
- Secara harafiah membongkar dan menebak skema Protobuf menjadi objek *dictionary* Python (`decode_message`).
- Mencari field `30.4` yang berisi judul dan menimpanya dengan teks baru.
- Menghitung ulang **semua varints dan length prefixes** dari tingkat anak *(child)* sampai ke induk *(root)* secara otomatis!
- Mem-bungkusnya kembali menjadi biner murni (`encode_message`) dan menyuntikkannya ke SQLite.

Hasilnya: Judul bisa diperpendek menjadi 2 karakter atau dipanjangkan hingga 500 karakter dengan aman tanpa menimbulkan korupsi *database*!

---

## 🚀 Fitur Utama (Features)

1. **Aman 100% (Protobuf Aware):** Manipulasi judul tanpa merusak struktur *Length Prefix* Protobuf.
2. **GUI Interaktif (PyQt5):** Antarmuka Desktop modern, bersih, dan fungsional yang mudah digunakan tanpa perlu bermain-main dengan terminal CLI.
3. **Auto-Discovery Database:** Mendeteksi otomatis file SQLite (`.db`) yang menampung "Judul Lama" di antara belasan *database* obrolan di PC Anda.
4. **Auto-Restart IDE:** Secara instan dan aman me-*reload* `Antigravity IDE.exe` (menggunakan *taskkill*) agar judul baru langsung ter-render di *sidebar* Chromium seketika.
5. **Konfigurasi Otomatis:** Mengingat lokasi instalasi *executable* AGI Anda (`settings.json`).

---

## ⚙️ Persyaratan Sistem (Requirements)

- Windows 10 / 11
- Python 3.7+
- Modul Python bawaan: `os`, `sys`, `sqlite3`, `json`, `subprocess`, `time`
- Modul pihak ketiga:
  - `PyQt5`
  - `blackboxprotobuf`

---

## 🛠️ Instalasi & Penggunaan

1. **Clone/Download** repositori ini ke dalam PC Anda.
2. Buka terminal (CMD / PowerShell) dan navigasikan ke dalam direktori proyek ini.
3. Buat dan aktifkan *Virtual Environment*:
   ```cmd
   python -m venv .venv
   ```
4. Install semua pustaka yang dibutuhkan menggunakan *pip* lokal:
   ```cmd
   .venv\Scripts\python -m pip install -r requirements.txt
   ```
5. Jalankan aplikasi GUI:
   ```cmd
   .venv\Scripts\python main_gui.py
   ```
   *(Tersedia juga file batch `install libs requirement.cmd` dan `run from venv.cmd` di dalam repositori untuk kemudahan klik ganda).*

### Panduan Layar (Usage):
1. Buka aplikasi **AGI Renamer**.
2. Pastikan letak instalasi AGI Anda (`Antigravity IDE.exe`) benar di kolom pertama.
3. Ketikkan nama/judul percakapan lama yang masih muncul di sidebar IDE.
4. Ketikkan judul pengganti yang baru.
5. Klik **Process Rename**.
6. Klik **Yes** pada popup notifikasi yang muncul, dan biarkan sistem menutup serta membuka kembali IDE Anda.
7. Setelah IDE terbuka kembali, klik *conversation* lain dan buka kembali *conversation* yang baru saja Anda ubah namanya agar IDE mereload judul tersebut dengan benar.

---

## 📝 Catatan Tambahan (Disclaimer)

*Tool* ini bekerja dengan mengubah file *database cache* (UI State) AGI secara langsung dan *offline*. Meskipun secara struktur biner hal ini dibuktikan aman 100% dengan menghitung ulang Varints, sangat disarankan untuk tidak mengubah judul secara drastis bersamaan ketika jendela percakapan tersebut sedang aktif/di-generate oleh asisten IDE untuk menghindari *lock file*.

**Dibuat oleh Adarmawan - 2026**
