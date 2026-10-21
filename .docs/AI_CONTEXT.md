# AI Context - Antigravity Conversation Renamer

Dokumen ini berisi rangkuman rekam jejak teknis, arsitektur data, dan penanganan kasus ekstrem (*edge cases*) pada proyek **Antigravity Conversation Renamer**. Tujuan utama dokumen ini adalah memberikan pemahaman mendalam kepada agen AI di masa depan agar dapat melakukan modifikasi, debugging, atau pengembangan fitur tanpa risiko merusak database percakapan atau menyebabkan desinkronisasi UI Antigravity IDE.

---

## 1. Arsitektur Inti: Dual-Sync Engine

Antigravity IDE (berbasis Electron/VSCode) menyimpan riwayat percakapan di **dua lokasi berbeda yang harus selalu sinkron**:

1. **Physical Conversation Database:**
   - Direktori: `~/.gemini/antigravity-ide/conversations/<conversation_id>.db` (SQLite)
   - Berisi payload lengkap langkah percakapan (*steps*) dalam format Protobuf terkompresi.
   - Kolom target: tabel `steps`, kolom `step_payload` (biasanya pada `rowid` awal, misal `rowid 5` / `idx 5`).
   - Field judul di dalam Protobuf payload: Field `30` -> Subfield `4` (string yang berisi judul, terkadang dipisahkan dengan `\n\n` dari summary awal).

2. **Sidebar UI Cache:**
   - File: `%APPDATA%\Antigravity\User\globalStorage\state.vscdb` (SQLite)
   - Tabel: `ItemTable`, Kunci: `antigravityUnifiedStateSync.trajectorySummaries`
   - Berisi daftar percakapan aktif yang dirender di panel sidebar Antigravity IDE dalam format Protobuf yang di-Base64.
   - Struktur Item:
     - Field `1`: `conversation_id` (bytes)
     - Field `2` -> Subfield `1`: Base64 dari inner Protobuf payload:
       - Inner Field `1`: Judul percakapan (bytes)
       - Inner Field `3`, `7`, `10`: Unix timestamp (`int`)

> [!CRITICAL]
> **Aturan Wajib (Dual-Sync UPSERT):**
> Mengubah judul HANYA pada file `.db` akan menyebabkan Antigravity IDE mengabaikan perubahan atau bahkan menghilangkan percakapan dari sidebar jika proses di-reload paksa. Begitu pula sebaliknya.
> Selalu lakukan pembaruan paralel ke kedua lokasi. Jika percakapan baru belum terdaftar di `trajectorySummaries`, fungsi `update_global_storage_title()` **HARUS melakukan UPSERT** (menyisipkan entri baru di posisi paling atas `items.insert(0, new_item)`), bukan sekadar mengabaikannya!

---

## 2. Pencegahan Bug Hilang Percakapan & Zombie Cleaner

### A. Bug Percakapan Hilang Saat Rename
* **Penyebab:** Percakapan baru yang sedang aktif belum di-flush oleh Antigravity IDE ke `state.vscdb`. Jika sistem mematikan IDE dengan `taskkill /F` sebelum entri ditulis, ID percakapan tidak ditemukan di `trajectorySummaries` sehingga hilang dari daftar.
* **Solusi:** `update_global_storage_title` menggunakan mekanisme **UPSERT**: membuat inner message baru berisi `conv_id`, `new_title`, dan `now_ts`, lalu meng-encode ulang Protobuf ke `state.vscdb`.
* **Auto-Sync:** Fungsi `sync_all_active_conversations_to_sidebar()` dijalankan di background saat load data/refresh untuk menjamin semua file `.db` fisik yang ada di disk selalu terdaftar di sidebar.

### B. Zombie / Ghost Cleaner
* **Konsep:** Percakapan yang file `.db` atau `.pb`-nya sudah dihapus dari disk, tetapi sisa cache resumenya masih menggantung di `state.vscdb`.
* **Deteksi:** Membaca semua `conv_id` di `trajectorySummaries` dan membandingkannya dengan set file fisik di `~/.gemini/antigravity-ide/conversations/`.
* **Pembersihan:** Menghapus item dari `msg['1']` dan menyimpan kembali Protobuf tanpa menghapus file fisik apapun.

---

## 3. Eksekusi Reloader & Subprocess Detach

Saat pengguna memilih untuk me-reload Antigravity IDE setelah proses rename:

```python
DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200
subprocess.Popen(
    [agi_path],
    creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
    close_fds=True,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    stdin=subprocess.DEVNULL
)
```

> [!WARNING]
> **Bahaya Pewarisan Handle Console:**
> JANGAN PERNAH memanggil `subprocess.Popen([agi_path])` tanpa me-redirect `stdout`/`stderr`/`stdin` ke `subprocess.DEVNULL` dan tanpa `DETACHED_PROCESS`.
> Jika diabaikan:
> 1. Log internal Electron (onboarding server, SSL error, update checker) akan bocor dan mengotori terminal CMD pengguna.
> 2. Jendela CMD tidak akan bisa ditutup sampai Antigravity IDE dimatikan oleh pengguna karena handle stream tertahan.

---

## 4. Windowing Native OS & DWM Theming

Aplikasi menggunakan jendela native OS standar (`QMainWindow` tanpa `FramelessWindowHint`):

* **Alasan Desain:** Menggunakan `FramelessWindowHint` pada Windows menimbulkan banyak *edge cases* (kursor resize macet/stuck `<->`, border putih DWM non-client, inkonsistensi styling modal dialog `QMessageBox`).
* **Pewarnaan Native Title Bar:** Menggunakan Windows DWM API (`dwmapi.dll`):
  - `DWMWA_USE_IMMERSIVE_DARK_MODE` (Attr 20/19): Mengaktifkan mode gelap native Windows untuk title bar dan kontrol min/max/close.
  - `DWMWA_CAPTION_COLOR` (Attr 35): Mengatur background title bar menjadi warna Ocean Dark (`#0c1a3a` -> `0x003A1A0C`).
  - `DWMWA_TEXT_COLOR` (Attr 36): Teks judul putih/soft (`0x00FCFAF8`).
* **Dialog Pop-up Terstandarisasi:** Seluruh `QMessageBox` (info, warning, critical, question) dipusatkan di [`src/method/dialog.py`](../src/method/dialog.py) agar otomatis menerapkan dark title bar via DWM tanpa duplikasi kode.
* **Isolasi Tema Stylesheet:** Seluruh styling dipisahkan ke [`resources/styles/theme.qss`](../resources/styles/theme.qss) dan dimuat melalui loader adaptif [`src/styles.py`](../src/styles.py).

---

## 5. Keamanan & Kebijakan Data Sensitif

* **Path Dinamis:** Jangan pernah meng-hardcode path user seperti `C:\Users\<username>\...`. Selalu gunakan `Path.home()` atau `os.path.expanduser("~")`.
* **Settings:** `settings.json` diabaikan oleh Git (`.gitignore`). Template publik yang bersih disediakan melalui `settings.json.example`.
