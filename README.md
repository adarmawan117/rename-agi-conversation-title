# Antigravity IDE Conversation Renamer

A powerful Desktop GUI application built with Python and PyQt5 to force-rename conversation titles in the Google Antigravity IDE without breaking its internal Protobuf binary cache.

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-GUI-green.svg)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey.svg)
![Protobuf](https://img.shields.io/badge/Data-Protobuf-orange.svg)

---

## 📖 Latar Belakang (The Story)

Secara bawaan, IDE _Advanced Agentic_ dari Google (Antigravity IDE) menyusun judul percakapan secara otomatis dari _prompt_ pengguna. Sayangnya, tidak ada antarmuka atau tombol bawaan di dalam UI IDE untuk me-_rename_ atau mengganti judul percakapan tersebut sesuai keinginan pengguna. Hal ini menyulitkan manajemen riwayat pekerjaan jika banyak _thread_ obrolan dengan _prompt_ awal yang bertele-tele.

Eksplorasi awal menemukan bahwa Antigravity IDE tidak menyimpan konfigurasi UI mentah (seperti file konfigurasi atau teks JSON sederhana) untuk daftar percakapan di _sidebar_, melainkan menanam data utamanya di dalam sekumpulan _file database_ SQLite (berakhiran `.db`) di dalam folder profil lokal:
`~/.gemini/antigravity-ide/conversations/`

### Tantangan Protobuf (The Length Prefix Curse)

Masalah utama terjadi ketika mencoba memanipulasi _database_ secara langsung:

1. Data tidak disimpan dalam bentuk tabel yang mudah diurai, melainkan dalam **Blob Biner** yang dienkode menggunakan format **Protocol Buffers (Protobuf)**.
2. Protobuf menggunakan skema **Varint Length-Prefixing** yang melacak ketat ukuran _bytes_ pada setiap struktur _(nested messages)_.
3. Mencoba menyuntikkan judul baru (yang panjangnya berbeda dari judul aslinya) melalui teknik injeksi biner/heksadesimal _brute force_ akan **membuat _database_ korup**. IDE menolak membaca biner tersebut dan mekanisme _fallback_-nya akan merusak tampilan, mengganti judul dengan teks prompt awal yang sangat panjang.
4. Teknik _padding_ (mengganti string persis sama panjang dengan menambahkan spasi) sempat berhasil sebagai penambal _hack_, namun tidak memberikan kebebasan mutlak kepada pengguna untuk menggunakan judul sebebas mungkin.

### Solusi Final (Blackboxprotobuf)

Untuk memberikan manipulasi judul yang mutlak dan permanen, _tool_ ini memanfaatkan pustaka **`blackboxprotobuf`**.

- Skrip ini akan menarik _Blob_ biner SQLite.
- Secara harafiah membongkar dan menebak skema Protobuf menjadi objek _dictionary_ Python (`decode_message`).
- Mencari field `30.4` yang berisi judul dan menimpanya dengan teks baru.
- Menghitung ulang **semua varints dan length prefixes** dari tingkat anak _(child)_ sampai ke induk _(root)_ secara otomatis!
- Mem-bungkusnya kembali menjadi biner murni (`encode_message`) dan menyuntikkannya ke SQLite.

Hasilnya: Judul bisa diperpendek menjadi 2 karakter atau dipanjangkan hingga 500 karakter dengan aman tanpa menimbulkan korupsi _database_!

---

## 🚀 Fitur Utama (Features)

1. **Aman 100% (Protobuf Aware):** Manipulasi judul tanpa merusak struktur _Length Prefix_ Protobuf.
2. **GUI Interaktif (PyQt5):** Antarmuka Desktop modern, bersih, dan fungsional yang mudah digunakan tanpa perlu bermain-main dengan terminal CLI.
3. **Auto-Discovery Database:** Mendeteksi otomatis file SQLite (`.db`) yang menampung "Judul Lama" di antara belasan _database_ obrolan di PC Anda.
4. **Auto-Restart IDE:** Secara instan dan aman me-_reload_ `Antigravity IDE.exe` (menggunakan _taskkill_) agar judul baru langsung ter-render di _sidebar_ Antigravity IDE.
5. **Konfigurasi Otomatis (Zero-Setup):** Mendeteksi lokasi instalasi Antigravity IDE secara otomatis. File `settings.json` dibuat secara otomatis saat aplikasi pertama kali dijalankan tanpa perlu pengaturan manual (`settings.json.example` hanya sebagai cetak biru skema).

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
3. Buat dan aktifkan _Virtual Environment_:
   ```cmd
   python -m venv .venv
   ```
4. Install semua pustaka yang dibutuhkan menggunakan _pip_ lokal:
   ```cmd
   .venv\Scripts\python -m pip install -r requirements.txt
   ```
5. Jalankan aplikasi GUI:
   ```cmd
   .venv\Scripts\python run.py
   ```
   _(Tersedia juga file batch `install libs requirement.cmd` dan `run from venv.cmd` di dalam repositori untuk kemudahan klik ganda)._

> [!TIP]
> **Zero Configuration:** Aplikasi otomatis mendeteksi path instalasi Antigravity IDE di komputer Anda dan membuat file `settings.json` sendiri secara otomatis. Anda tidak perlu membuat atau mengedit konfigurasi secara manual (`settings.json.example` hanya sebagai cetak biru skema opsional).

### Panduan Layar (Usage):

1. Buka aplikasi **AGI Renamer**.
2. Pastikan letak instalasi AGI Anda (`Antigravity IDE.exe`) benar di kolom pertama.
3. Ketikkan nama/judul percakapan lama yang masih muncul di sidebar IDE.
4. Ketikkan judul pengganti yang baru.
5. Klik **Process Rename**.
6. Klik **Yes** pada popup notifikasi yang muncul, dan biarkan sistem menutup serta membuka kembali IDE Anda.
7. Setelah IDE terbuka kembali, klik _conversation_ lain dan buka kembali _conversation_ yang baru saja Anda ubah namanya agar IDE mereload judul tersebut dengan benar.
   > **💡 Info Teknis:** Berdasarkan temuan saat proses _reverse engineering_, meskipun _database_ SQLite berhasil dimodifikasi dan IDE di-_restart_, mekanisme _caching_ internal dari _frontend_ IDE kadang masih menahan _state_ UI terakhir dari percakapan yang sedang aktif. Dengan mereload percakapan dan membukanya kembali, kita memaksa IDE untuk melakukan proses _re-fetch_ dan merender ulang _metadata_ percakapan (termasuk judul yang baru) langsung dari _database_.

---

## 📚 Dokumentasi Teknis (`.docs`)

Panduan arsitektur mendalam, spesifikasi reverse engineering, dan panduan keamanan tersedia di dalam folder [`.docs/`](.docs/README.md):

* [**`AI_CONTEXT.md`**](.docs/AI_CONTEXT.md): Rekam jejak riset, solusi bug hilang percakapan via Dual-Sync UPSERT, zombie cleaner, subprocess detached flags, dan theming DWM.
* [**`ARCHITECTURE.md`**](.docs/ARCHITECTURE.md): Diagram alur komponen, sequence diagram dual-sync pipeline, Protobuf wire format (Field 30/4 vs 1/2.1), dan modul responsibilities.
* [**`BUILD_AND_PACKAGING.md`**](.docs/BUILD_AND_PACKAGING.md): Panduan kompilasi PyInstaller (`AGI Renamer.spec`), hidden imports dynamic blackboxprotobuf, dan bundling resources.

---

## 📝 Catatan Tambahan (Disclaimer)

* Aplikasi ini bekerja dengan membaca dan memodifikasi file penyimpanan lokal Antigravity IDE di komputer Anda secara langsung.
* Sebelum memodifikasi database, aplikasi otomatis membuat file cadangan (`.bak`) untuk menjamin keamanan integritas data percakapan Anda.

---

Dikembangkan dengan ❤️ oleh [ADR Programming](https://www.instagram.com/adr_programming/)
