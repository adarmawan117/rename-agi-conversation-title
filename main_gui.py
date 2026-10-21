import datetime
import os
import subprocess
import sys
import time

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QFrame, QStatusBar, QProgressBar
)

from rename_logic import (
    list_conversations,
    rename_conversation_by_id,
    rename_conversation,
    scan_zombie_conversations,
    clean_zombie_conversations,
    get_conversations_dir
)
from settings_manager import get_agi_path, save_agi_path


# --- Dark Theme QSS ---
DARK_THEME_QSS = """
QMainWindow, QWidget#CentralWidget {
    background-color: #12131c;
    color: #cdd6f4;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
}

QFrame.card {
    background-color: #1a1b29;
    border: 1px solid #2b2d42;
    border-radius: 8px;
    padding: 10px;
}

QLabel {
    color: #cdd6f4;
}

QLabel#titleLabel {
    font-size: 14pt;
    font-weight: bold;
    color: #ffffff;
}

QLabel#subtitleLabel {
    font-size: 9pt;
    color: #89b4fa;
}

QLabel#sectionTitle {
    font-size: 10pt;
    font-weight: bold;
    color: #cdd6f4;
}

QLineEdit {
    background-color: #13141f;
    border: 1px solid #363a4f;
    border-radius: 6px;
    padding: 6px 10px;
    color: #cdd6f4;
    selection-background-color: #3b82f6;
}

QLineEdit:focus {
    border: 1px solid #3b82f6;
    background-color: #181926;
}

QLineEdit::placeholder {
    color: #6c7086;
}

QPushButton {
    background-color: #27293d;
    border: 1px solid #3d415b;
    border-radius: 6px;
    color: #cdd6f4;
    padding: 6px 14px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #353852;
    border-color: #5c6287;
}

QPushButton:pressed {
    background-color: #202232;
}

QPushButton#primaryBtn {
    background-color: #2563eb;
    border: 1px solid #3b82f6;
    color: #ffffff;
    font-weight: bold;
    font-size: 10pt;
    padding: 8px 16px;
}

QPushButton#primaryBtn:hover {
    background-color: #1d4ed8;
    border-color: #60a5fa;
}

QPushButton#primaryBtn:pressed {
    background-color: #1e40af;
}

QPushButton#primaryBtn:disabled {
    background-color: #1e293b;
    border-color: #334155;
    color: #64748b;
}

QPushButton#dangerBtn {
    background-color: #3b2333;
    border: 1px solid #853753;
    color: #f38ba8;
    font-weight: bold;
}

QPushButton#dangerBtn:hover {
    background-color: #4e293f;
    border-color: #c24b72;
    color: #ffffff;
}

QTableWidget {
    background-color: #13141f;
    border: 1px solid #2b2d42;
    border-radius: 6px;
    gridline-color: #222436;
    color: #cdd6f4;
    selection-background-color: #2b395d;
    selection-color: #ffffff;
}

QTableWidget::item {
    padding: 6px;
}

QTableWidget::item:selected {
    background-color: #253355;
}

QHeaderView::section {
    background-color: #1e1f30;
    color: #89b4fa;
    font-weight: bold;
    padding: 6px;
    border: none;
    border-bottom: 2px solid #2b2d42;
    border-right: 1px solid #222436;
}

QScrollBar:vertical {
    background: #13141f;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #363a4f;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #585b70;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QStatusBar {
    background-color: #12131c;
    color: #a6adc8;
    border-top: 1px solid #222436;
    font-size: 9pt;
}
"""


class DataLoaderThread(QThread):
    """Thread for loading conversations & scanning zombie entries in background."""
    data_loaded = pyqtSignal(list, int)

    def run(self):
        convs = list_conversations()
        zombie_count, _ = scan_zombie_conversations()
        self.data_loaded.emit(convs, zombie_count)


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Antigravity Conversation Renamer")
        self.resize(880, 680)
        self.setMinimumSize(720, 560)

        # Application Icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "google-antigravity.ico")
        if getattr(sys, 'frozen', False):
            icon_path = os.path.join(sys._MEIPASS, "google-antigravity.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))

        self.all_conversations = []
        self.selected_conv = None

        self.init_ui()
        self.refresh_data()

    def init_ui(self):
        central_widget = QWidget(self)
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 14, 16, 10)
        main_layout.setSpacing(10)

        # --- 1. Header Bar ---
        header_layout = QHBoxLayout()
        header_info = QVBoxLayout()
        header_info.setSpacing(2)

        title_lbl = QLabel("⚡ Antigravity Conversation Renamer")
        title_lbl.setObjectName("titleLabel")
        subtitle_lbl = QLabel("Kelola, Sinkronisasi & Ubah Judul Percakapan Google Antigravity IDE Secara Aman")
        subtitle_lbl.setObjectName("subtitleLabel")
        header_info.addWidget(title_lbl)
        header_info.addWidget(subtitle_lbl)

        header_layout.addLayout(header_info)
        header_layout.addStretch()

        # Zombie Cleaner & Refresh Buttons
        self.btn_clean_zombies = QPushButton("👻 Scan Zombie (0)")
        self.btn_clean_zombies.setObjectName("dangerBtn")
        self.btn_clean_zombies.setToolTip("Bersihkan sisa cache percakapan yang sudah dihapus dari disk agar tidak muncul kembali")
        self.btn_clean_zombies.clicked.connect(self.on_clean_zombies_clicked)
        header_layout.addWidget(self.btn_clean_zombies)

        self.btn_refresh = QPushButton("🔄 Refresh")
        self.btn_refresh.clicked.connect(self.refresh_data)
        header_layout.addWidget(self.btn_refresh)

        main_layout.addLayout(header_layout)

        # --- 2. AGI Executable Path Bar ---
        path_card = QFrame()
        path_card.setProperty("class", "card")
        path_layout = QHBoxLayout(path_card)
        path_layout.setContentsMargins(10, 8, 10, 8)
        path_layout.setSpacing(8)

        lbl_path = QLabel("AGI Path:")
        lbl_path.setStyleSheet("font-weight: bold; color: #89b4fa;")
        self.txt_path = QLineEdit()
        self.txt_path.setText(get_agi_path())
        self.txt_path.setPlaceholderText("Path ke Antigravity IDE.exe...")

        btn_browse = QPushButton("Browse")
        btn_browse.clicked.connect(self.browse_path)

        path_layout.addWidget(lbl_path)
        path_layout.addWidget(self.txt_path, stretch=1)
        path_layout.addWidget(btn_browse)
        main_layout.addWidget(path_card)

        # --- 3. Conversation Explorer Card ---
        explorer_card = QFrame()
        explorer_card.setProperty("class", "card")
        explorer_layout = QVBoxLayout(explorer_card)
        explorer_layout.setContentsMargins(10, 10, 10, 10)
        explorer_layout.setSpacing(8)

        top_explorer_layout = QHBoxLayout()
        lbl_explorer = QLabel("📋 Daftar Percakapan Aktif (Klik untuk memilih):")
        lbl_explorer.setObjectName("sectionTitle")

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Cari percakapan (ketik judul atau ID)...")
        self.txt_search.textChanged.connect(self.filter_conversations)
        self.txt_search.setFixedWidth(280)

        top_explorer_layout.addWidget(lbl_explorer)
        top_explorer_layout.addStretch()
        top_explorer_layout.addWidget(self.txt_search)
        explorer_layout.addLayout(top_explorer_layout)

        # Table Widget
        self.table_convs = QTableWidget()
        self.table_convs.setColumnCount(4)
        self.table_convs.setHorizontalHeaderLabels(["Judul Percakapan", "Terakhir Diubah", "Ukuran", "Conversation ID"])
        self.table_convs.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_convs.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_convs.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_convs.verticalHeader().setVisible(False)
        self.table_convs.setShowGrid(True)

        header = self.table_convs.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        self.table_convs.itemSelectionChanged.connect(self.on_table_selection_changed)
        explorer_layout.addWidget(self.table_convs, stretch=1)
        main_layout.addWidget(explorer_card, stretch=1)

        # --- 4. Rename Action Panel Card ---
        action_card = QFrame()
        action_card.setProperty("class", "card")
        action_layout = QVBoxLayout(action_card)
        action_layout.setContentsMargins(12, 10, 12, 10)
        action_layout.setSpacing(8)

        self.lbl_selected_info = QLabel("Silakan pilih percakapan dari tabel di atas untuk mulai me-rename.")
        self.lbl_selected_info.setStyleSheet("color: #a6adc8; font-style: italic;")
        action_layout.addWidget(self.lbl_selected_info)

        inputs_layout = QHBoxLayout()
        inputs_layout.setSpacing(8)

        lbl_new = QLabel("Nama Baru:")
        lbl_new.setStyleSheet("font-weight: bold; color: #ffffff;")
        self.txt_new_title = QLineEdit()
        self.txt_new_title.setPlaceholderText("Masukkan judul baru yang Anda inginkan...")
        self.txt_new_title.returnPressed.connect(self.process_rename)

        self.btn_process = QPushButton("💾 Simpan Judul Baru")
        self.btn_process.setObjectName("primaryBtn")
        self.btn_process.clicked.connect(self.process_rename)
        self.btn_process.setEnabled(False)

        inputs_layout.addWidget(lbl_new)
        inputs_layout.addWidget(self.txt_new_title, stretch=1)
        inputs_layout.addWidget(self.btn_process)
        action_layout.addLayout(inputs_layout)

        main_layout.addWidget(action_card)

        # --- 5. Footer Developer Credit ---
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 4, 0, 0)

        self.lbl_footer = QLabel(
            'Dikembangkan dengan ❤️ oleh <a href="https://www.instagram.com/adr_programming/" style="color: #3b82f6; text-decoration: none; font-weight: bold;">ADR Programming</a>'
        )
        self.lbl_footer.setOpenExternalLinks(True)
        self.lbl_footer.setStyleSheet("font-size: 9pt; color: #6c7086;")
        self.lbl_footer.setAlignment(Qt.AlignCenter)

        footer_layout.addWidget(self.lbl_footer)
        main_layout.addLayout(footer_layout)

        # --- Status Bar ---
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Siap.")

    def browse_path(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Pilih Antigravity IDE.exe", "C:\\", "Executable (*.exe)"
        )
        if file_path:
            self.txt_path.setText(file_path)
            save_agi_path(file_path)
            self.status_bar.showMessage("Path AGI diperbarui dan disimpan.", 3000)

    def refresh_data(self):
        self.status_bar.showMessage("Memuat data percakapan...")
        self.btn_refresh.setEnabled(False)
        self.loader_thread = DataLoaderThread()
        self.loader_thread.data_loaded.connect(self.on_data_loaded)
        self.loader_thread.start()

    def on_data_loaded(self, convs, zombie_count):
        self.all_conversations = convs
        self.btn_refresh.setEnabled(True)

        if zombie_count > 0:
            self.btn_clean_zombies.setText(f"👻 Bersihkan Zombie ({zombie_count})")
            self.btn_clean_zombies.setEnabled(True)
        else:
            self.btn_clean_zombies.setText("👻 Cache Bersih (0)")
            self.btn_clean_zombies.setEnabled(False)

        self.populate_table(self.all_conversations)
        self.status_bar.showMessage(
            f"Berhasil memuat {len(convs)} percakapan aktif. Ditemukan {zombie_count} percakapan zombie.", 4000
        )

    def populate_table(self, conv_list):
        self.table_convs.setRowCount(len(conv_list))
        for row, conv in enumerate(conv_list):
            # Title
            item_title = QTableWidgetItem(conv["title"])
            item_title.setToolTip(f"{conv['title']}\nID: {conv['id']}")

            # Modified Time
            mtime_str = datetime.datetime.fromtimestamp(conv["mtime"]).strftime("%Y-%m-%d %H:%M") if conv["mtime"] else "-"
            item_mtime = QTableWidgetItem(mtime_str)
            item_mtime.setTextAlignment(Qt.AlignCenter)

            # Size
            size_mb = conv["size"] / (1024 * 1024)
            size_str = f"{size_mb:.1f} MB" if size_mb >= 0.1 else f"{conv['size'] / 1024:.0f} KB"
            item_size = QTableWidgetItem(size_str)
            item_size.setTextAlignment(Qt.AlignCenter)

            # Conv ID
            item_id = QTableWidgetItem(conv["id"])
            item_id.setTextAlignment(Qt.AlignCenter)

            # Store full conv in row item
            item_title.setData(Qt.UserRole, conv)

            self.table_convs.setItem(row, 0, item_title)
            self.table_convs.setItem(row, 1, item_mtime)
            self.table_convs.setItem(row, 2, item_size)
            self.table_convs.setItem(row, 3, item_id)

    def filter_conversations(self, query):
        query = query.strip().lower()
        if not query:
            self.populate_table(self.all_conversations)
            return

        filtered = [
            c for c in self.all_conversations
            if query in c["title"].lower() or query in c["id"].lower()
        ]
        self.populate_table(filtered)

    def on_table_selection_changed(self):
        selected_rows = self.table_convs.selectionModel().selectedRows()
        if not selected_rows:
            self.selected_conv = None
            self.lbl_selected_info.setText("Silakan pilih percakapan dari tabel di atas untuk mulai me-rename.")
            self.lbl_selected_info.setStyleSheet("color: #a6adc8; font-style: italic;")
            self.btn_process.setEnabled(False)
            return

        row_idx = selected_rows[0].row()
        item_title = self.table_convs.item(row_idx, 0)
        if item_title:
            conv = item_title.data(Qt.UserRole)
            self.selected_conv = conv
            self.lbl_selected_info.setText(
                f"Percakapan Terpilih: <b style='color:#ffffff;'>{conv['title']}</b> &nbsp;|&nbsp; <span style='color:#89b4fa;'>ID: {conv['id']}</span>"
            )
            self.lbl_selected_info.setStyleSheet("color: #cdd6f4;")
            self.txt_new_title.setText(conv["title"])
            self.txt_new_title.setFocus()
            self.txt_new_title.selectAll()
            self.btn_process.setEnabled(True)

    def on_clean_zombies_clicked(self):
        count, zombies = scan_zombie_conversations()
        if count == 0:
            QMessageBox.information(self, "Cache Bersih", "Tidak ada percakapan zombie yang ditemukan di cache UI.")
            return

        confirm = QMessageBox.question(
            self,
            "Konfirmasi Pembersihan",
            f"Ditemukan {count} percakapan hantu/zombie di cache UI sidebar yang file fisiknya sudah terhapus.\n\n"
            "Apakah Anda ingin membersihkannya sekarang agar sidebar Antigravity IDE bersih dan tidak memunculkan percakapan lama lagi?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if confirm == QMessageBox.Yes:
            success, msg, purged = clean_zombie_conversations()
            if success:
                QMessageBox.information(self, "Pembersihan Sukses", msg)
                self.refresh_data()
            else:
                QMessageBox.critical(self, "Gagal Membersihkan", msg)

    def process_rename(self):
        if not self.selected_conv:
            QMessageBox.warning(self, "Peringatan", "Silakan pilih percakapan dari tabel terlebih dahulu!")
            return

        new_title = self.txt_new_title.text().strip()
        if not new_title:
            QMessageBox.warning(self, "Peringatan", "Nama baru tidak boleh kosong!")
            return

        conv_id = self.selected_conv["id"]
        old_title = self.selected_conv["title"]

        if new_title == old_title:
            QMessageBox.information(self, "Info", "Nama baru sama persis dengan nama saat ini.")
            return

        # Save AGI path if edited
        agi_path = self.txt_path.text().strip()
        if agi_path:
            save_agi_path(agi_path)

        # Execute Dual-Sync Rename
        self.status_bar.showMessage("Menjalankan Dual-Sync Rename...")
        success, message = rename_conversation_by_id(conv_id, new_title)

        if success:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Question)
            msg_box.setWindowTitle("Sukses Rename")
            msg_box.setText(
                f"{message}\n\n"
                f"Judul berhasil diubah menjadi: '{new_title}'\n\n"
                "Apakah Anda ingin mereload Antigravity IDE sekarang untuk menerapkan perubahan judul di sidebar?"
            )
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.Yes)

            result = msg_box.exec_()
            if result == QMessageBox.Yes:
                self.reload_agi(agi_path)

            self.refresh_data()
        else:
            QMessageBox.critical(self, "Gagal Rename", message)
            self.status_bar.showMessage("Gagal melakukan rename.", 4000)

    def reload_agi(self, agi_path):
        self.status_bar.showMessage("Menutup dan mereload Antigravity IDE...")
        try:
            # Matikan AGI
            subprocess.run('taskkill /F /IM "Antigravity IDE.exe" /T', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Non-blocking pause menggunakan QTimer agar GUI tidak freeze
            QTimer.singleShot(2000, lambda: self._launch_agi_after_kill(agi_path))
        except Exception as e:
            QMessageBox.warning(self, "Error Reload", f"Gagal mereload AGI: {e}")

    def _launch_agi_after_kill(self, agi_path):
        try:
            if agi_path and os.path.exists(agi_path):
                subprocess.Popen([agi_path], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
                self.status_bar.showMessage("Antigravity IDE berhasil dibuka kembali.", 4000)
            else:
                QMessageBox.warning(
                    self,
                    "Path Tidak Ditemukan",
                    "Path Antigravity IDE.exe tidak valid. Silakan buka IDE Anda secara manual."
                )
                self.status_bar.showMessage("Path AGI tidak valid.", 4000)
        except Exception as e:
            QMessageBox.warning(self, "Error Meluncurkan AGI", f"Gagal membuka AGI: {e}")


if __name__ == '__main__':
    # Silence Font Spam Logs
    os.environ["QT_LOGGING_RULES"] = "qt.qpa.fonts=false"

    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME_QSS)

    window = MainApp()
    window.show()
    sys.exit(app.exec_())
