# Technical Documentation Index - Antigravity Conversation Renamer

Direktori `.docs` berisi panduan arsitektur mendalam, rekam jejak teknis, dan standar keamanan proyek **Antigravity Conversation Renamer**. Seluruh dokumen dirancang khusus agar mudah dipahami oleh pengembang maupun agen AI yang melanjutkan pengembangan sistem ini di masa depan.

---

## Daftar Dokumen Teknis

| Dokumen | Topik Utama |
| :--- | :--- |
| [**`AI_CONTEXT.md`**](AI_CONTEXT.md) | **Konteks Rekayasa & Edge Cases:**<br/>- Rekam jejak bug hilangnya percakapan dan solusi UPSERT.<br/>- Mekanisme pembersihan Ghost/Zombie summaries.<br/>- Protokol eksekusi reloader subprocess dengan flag `DETACHED_PROCESS` & `DEVNULL`.<br/>- DWM Immersive Dark Mode dan pewarnaan title bar native Windows. |
| [**`ARCHITECTURE.md`**](ARCHITECTURE.md) | **Arsitektur Sistem & Spesifikasi Data:**<br/>- Diagram komponen & Sequence diagram Dual-Sync pipeline.<br/>- Detail Protobuf wire format (Field 30/4 pada physical DB vs Field 1/2.1 pada state.vscdb).<br/>- Threading model (`DataLoaderThread`) dan proses reload IDE.<br/>- Strategi keandalan data (WAL checkpoints, `.bak` auto-backup). |
| [**`SENSITIVE_DATA_AND_SECURITY.md`**](SENSITIVE_DATA_AND_SECURITY.md) | **Keamanan Data & Pencegahan Kebocoran Sensitif:**<br/>- Standar resolusi path dinamis sistem operasi (`Path.home()`, `os.path.expanduser`).<br/>- Arsitektur pemisahan file konfigurasi (`settings.json` vs `settings.json.example`).<br/>- Aturan karantina `.gitignore` untuk file database dan sesi AI.<br/>- Pre-commit checklist sebelum mem-push perubahan ke Git repository. |
| [**`BUILD_AND_PACKAGING.md`**](BUILD_AND_PACKAGING.md) | **Sistem Kompilasi & Packaging Mandiri:**<br/>- Konfigurasi PyInstaller via [`AGI Renamer.spec`](../AGI%20Renamer.spec).<br/>- Penanganan dynamic hidden imports `blackboxprotobuf`.<br/>- Bundling aset ikon via `sys._MEIPASS` dan otomasi build via [`Create Installer.cmd`](../Create%20Installer.cmd). |

---

## Panduan Cepat untuk Agen AI & Kontributor Baru

1. **Jaga Konsistensi Dual-Sync:**
   Jangan pernah hanya memodifikasi file `.db` atau hanya `state.vscdb`. Selalu gunakan fungsi pembungkus di [`src/rename_logic.py`](../src/rename_logic.py).
2. **Gunakan Helper Modul Terstandarisasi:**
   Untuk dialog popup gunakan [`src/method/dialog.py`](../src/method/dialog.py) dan untuk penataan tema/DWM gunakan [`src/styles.py`](../src/styles.py).
3. **Jangan Meng-hardcode User Path:**
   Jangan pernah menuliskan nama akun lokal Windows (seperti `<username>`) ke dalam kode maupun file markdown yang ter-commit.
4. **Patuhi Git Protocol:**
   Jangan pernah menjalankan `git commit` atau `git push` tanpa instruksi eksplisit dari pengguna.
