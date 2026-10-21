import ctypes
from ctypes import wintypes
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
    QFrame, QStatusBar, QProgressBar, QSizeGrip
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


# --- ADR Prompt Manager: Ocean Dark Theme QSS ---
OCEAN_THEME_QSS = """
QMainWindow, QWidget#CentralWidget {
    background-color: #0c1a3a;
    color: #bfdbfe;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 9.5pt;
}

QLabel#titleLabel {
    font-size: 13pt;
    font-weight: 700;
    color: #ffffff;
    font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
    letter-spacing: -0.2px;
}

QLabel#windowBadge {
    background-color: #172554;
    color: #60a5fa;
    border: 1px solid #1e3a8a;
    border-radius: 4px;
    padding: 1px 6px;
    font-size: 7.5pt;
    font-weight: 600;
    font-family: 'JetBrains Mono', Consolas, monospace;
}

/* Cards & Content */
QFrame.card {
    background-color: #172554;
    border: 1px solid #1e3a8a;
    border-radius: 12px;
    padding: 12px;
}

QLabel {
    color: #bfdbfe;
    font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
}

QLabel#subtitleLabel {
    font-size: 8.5pt;
    color: #60a5fa;
    font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
}

QLabel#sectionTitle {
    font-size: 9pt;
    font-weight: 600;
    color: #93c5fd;
    letter-spacing: 0.2px;
}

QLineEdit {
    background-color: #101e42;
    border: 1px solid #1e3a8a;
    border-radius: 8px;
    padding: 6px 10px;
    color: #dbeafe;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    font-size: 9pt;
}

QLineEdit:focus {
    border: 1px solid #3b82f6;
    background-color: #13244f;
}

QLineEdit::placeholder {
    color: #3b82f6;
}

QLineEdit#monoInput {
    font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
    font-size: 8.5pt;
    color: #93c5fd;
}

QPushButton {
    background-color: #172554;
    border: 1px solid #1e3a8a;
    border-radius: 8px;
    color: #93c5fd;
    padding: 6px 14px;
    font-weight: 500;
    font-size: 9pt;
}

QPushButton:hover {
    background-color: #1e40af;
    border-color: #3b82f6;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #1d4ed8;
}

QPushButton#primaryBtn {
    background-color: #2563eb;
    border: 1px solid #60a5fa;
    color: #ffffff;
    font-weight: 600;
    font-size: 9.5pt;
    padding: 8px 16px;
    border-radius: 8px;
}

QPushButton#primaryBtn:hover {
    background-color: #3b82f6;
    border-color: #93c5fd;
}

QPushButton#primaryBtn:pressed {
    background-color: #1d4ed8;
}

QPushButton#primaryBtn:disabled {
    background-color: #101e42;
    border-color: #172554;
    color: #2d456b;
}

QPushButton#dangerBtn {
    background-color: #2b111e;
    border: 1px solid #881337;
    color: #fca5a5;
    font-weight: 500;
    padding: 6px 12px;
    border-radius: 8px;
}

QPushButton#dangerBtn:hover {
    background-color: #3f1629;
    border-color: #be123c;
    color: #ffffff;
}

QTableWidget {
    background-color: #101e42;
    border: 1px solid #1e3a8a;
    border-radius: 8px;
    gridline-color: #14244d;
    color: #bfdbfe;
    selection-background-color: #1d4ed8;
    selection-color: #ffffff;
    font-size: 9pt;
}

QTableWidget::item {
    padding: 6px 8px;
    border-bottom: 1px solid #13244f;
}

QTableWidget::item:selected {
    background-color: #1d4ed8;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #172554;
    color: #60a5fa;
    font-weight: 600;
    font-size: 8.5pt;
    padding: 7px;
    border: none;
    border-bottom: 2px solid #1e3a8a;
    border-right: 1px solid #13244f;
}

QScrollBar:vertical {
    background: #0c1a3a;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #1e3a8a;
    min-height: 24px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #2563eb;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QStatusBar {
    background-color: #081329;
    color: #60a5fa;
    border-top: 1px solid #172554;
    font-size: 8.5pt;
    padding-left: 8px;
}

QSizeGrip {
    background-color: transparent;
    width: 16px;
    height: 16px;
    margin-right: 4px;
    margin-bottom: 4px;
}

/* Dialogs & Popups (Dark Ocean Theme) */
QDialog, QMessageBox {
    background-color: #101e42;
    color: #dbeafe;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 9.5pt;
}

QMessageBox QLabel {
    color: #dbeafe;
    background-color: transparent;
    font-size: 9.5pt;
}

QMessageBox QPushButton {
    background-color: #172554;
    border: 1px solid #1e3a8a;
    border-radius: 8px;
    color: #93c5fd;
    font-weight: 600;
    font-size: 9pt;
    min-width: 72px;
    padding: 6px 16px;
}

QMessageBox QPushButton:hover {
    background-color: #1e40af;
    border-color: #3b82f6;
    color: #ffffff;
}

QMessageBox QPushButton:pressed {
    background-color: #1d4ed8;
}

QMessageBox QPushButton:default {
    background-color: #2563eb;
    border: 1px solid #60a5fa;
    color: #ffffff;
}

QMessageBox QPushButton:default:hover {
    background-color: #3b82f6;
    border-color: #93c5fd;
}
"""


def apply_dark_window_titlebar(window):
    """
    Menerapkan tema gelap pada title bar native Windows:
    - DWMWA_USE_IMMERSIVE_DARK_MODE (20 & 19): Mode gelap native Windows 10 & 11
    - DWMWA_CAPTION_COLOR (35): Background title bar Ocean Dark (#0c1a3a) di Windows 11
    - DWMWA_TEXT_COLOR (36): Teks title bar putih/soft (#f8fafc) di Windows 11
    - DWMWA_BORDER_COLOR (34): Border halus (#1e3a8a) di Windows 11
    """
    if sys.platform != "win32":
        return
    try:
        hwnd = int(window.winId())
        if not hwnd:
            return

        # 1. Immersive Dark Mode (Windows 10 Build 17763+ & Windows 11)
        val = ctypes.c_int(1)
        for attr in [20, 19]:
            res = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, attr, ctypes.byref(val), ctypes.sizeof(val)
            )
            if res == 0:
                break

        # 2. Custom Title Bar Background Color (Windows 11 Build 22000+)
        # #0c1a3a -> 0x003A1A0C (COLORREF format 0x00BBGGRR)
        DWMWA_CAPTION_COLOR = 35
        caption_color = ctypes.c_int(0x003A1A0C)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_CAPTION_COLOR, ctypes.byref(caption_color), ctypes.sizeof(caption_color)
        )

        # 3. Custom Title Bar Text Color (Windows 11 Build 22000+)
        # #f8fafc -> 0x00FCFAF8
        DWMWA_TEXT_COLOR = 36
        text_color = ctypes.c_int(0x00FCFAF8)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_TEXT_COLOR, ctypes.byref(text_color), ctypes.sizeof(text_color)
        )

        # 4. Custom Border Color (Windows 11 Build 22000+)
        # #1e3a8a -> 0x008A3A1E
        DWMWA_BORDER_COLOR = 34
        border_color = ctypes.c_int(0x008A3A1E)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_BORDER_COLOR, ctypes.byref(border_color), ctypes.sizeof(border_color)
        )
    except Exception:
        pass


def show_info(parent, title, text):
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setStandardButtons(QMessageBox.Ok)
    apply_dark_window_titlebar(msg)
    return msg.exec_()


def show_warning(parent, title, text):
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setStandardButtons(QMessageBox.Ok)
    apply_dark_window_titlebar(msg)
    return msg.exec_()


def show_critical(parent, title, text):
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setStandardButtons(QMessageBox.Ok)
    apply_dark_window_titlebar(msg)
    return msg.exec_()


def show_question(parent, title, text, buttons=QMessageBox.Yes | QMessageBox.No, default=QMessageBox.Yes):
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Question)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setStandardButtons(buttons)
    msg.setDefaultButton(default)
    apply_dark_window_titlebar(msg)
    return msg.exec_()


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

    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_window_titlebar(self)

    def init_ui(self):
        central_widget = QWidget(self)
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)

        content_layout = QVBoxLayout(central_widget)
        content_layout.setContentsMargins(16, 14, 16, 10)
        content_layout.setSpacing(10)

        # --- 1. Header Hero Bar ---
        header_layout = QHBoxLayout()
        header_info = QVBoxLayout()
        header_info.setSpacing(4)

        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)

        # App Icon in Header
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "google-antigravity.ico")
        if getattr(sys, 'frozen', False):
            icon_path = os.path.join(sys._MEIPASS, "google-antigravity.ico")
        if os.path.exists(icon_path):
            icon_lbl = QLabel()
            icon_lbl.setPixmap(QtGui.QPixmap(icon_path).scaled(22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            title_layout.addWidget(icon_lbl)

        title_lbl = QLabel("Antigravity Conversation Renamer")
        title_lbl.setObjectName("titleLabel")
        title_layout.addWidget(title_lbl)

        badge = QLabel("v1.0")
        badge.setObjectName("windowBadge")
        title_layout.addWidget(badge)
        title_layout.addStretch()

        header_info.addLayout(title_layout)

        subtitle_lbl = QLabel("Kelola, Sinkronisasi & Ubah Judul Percakapan Google Antigravity IDE Secara Aman")
        subtitle_lbl.setObjectName("subtitleLabel")
        header_info.addWidget(subtitle_lbl)

        header_layout.addLayout(header_info)
        header_layout.addStretch()

        # Zombie Cleaner & Refresh Buttons
        self.btn_clean_zombies = QPushButton("👻 Scan Zombie (0)")
        self.btn_clean_zombies.setObjectName("dangerBtn")
        self.btn_clean_zombies.setToolTip("Bersihkan sisa cache percakapan yang sudah dihapus dari disk agar tidak muncul kembali")
        self.btn_clean_zombies.clicked.connect(self.on_clean_zombies_clicked)
        header_layout.addWidget(self.btn_clean_zombies)

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.refresh_data)
        header_layout.addWidget(self.btn_refresh)

        content_layout.addLayout(header_layout)

        # --- 2. AGI Executable Path Bar ---
        path_card = QFrame()
        path_card.setProperty("class", "card")
        path_layout = QHBoxLayout(path_card)
        path_layout.setContentsMargins(10, 8, 10, 8)
        path_layout.setSpacing(8)

        lbl_path = QLabel("AGI Path:")
        lbl_path.setStyleSheet("font-weight: 500; color: #60a5fa; font-size: 9pt;")
        self.txt_path = QLineEdit()
        self.txt_path.setObjectName("monoInput")
        self.txt_path.setText(get_agi_path())
        self.txt_path.setPlaceholderText("Path ke Antigravity IDE.exe...")

        btn_browse = QPushButton("Browse")
        btn_browse.clicked.connect(self.browse_path)

        path_layout.addWidget(lbl_path)
        path_layout.addWidget(self.txt_path, stretch=1)
        path_layout.addWidget(btn_browse)
        content_layout.addWidget(path_card)

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
        self.txt_search.setPlaceholderText("Cari percakapan (ketik judul atau ID)...")
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
        content_layout.addWidget(explorer_card, stretch=1)

        # --- 4. Rename Action Panel Card ---
        action_card = QFrame()
        action_card.setProperty("class", "card")
        action_layout = QVBoxLayout(action_card)
        action_layout.setContentsMargins(12, 10, 12, 10)
        action_layout.setSpacing(8)

        self.lbl_selected_info = QLabel("Silakan pilih percakapan dari tabel di atas untuk mulai me-rename.")
        self.lbl_selected_info.setStyleSheet("color: #60a5fa; font-style: italic; font-size: 8.5pt;")
        action_layout.addWidget(self.lbl_selected_info)

        inputs_layout = QHBoxLayout()
        inputs_layout.setSpacing(8)

        lbl_new = QLabel("Nama Baru:")
        lbl_new.setStyleSheet("font-weight: 500; color: #bfdbfe; font-size: 9pt;")
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

        content_layout.addWidget(action_card)

        # --- 5. Footer Developer Credit ---
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 4, 0, 0)

        self.lbl_footer = QLabel(
            'Dikembangkan dengan ❤️ oleh <a href="https://www.instagram.com/adr_programming/" style="color: #60a5fa; text-decoration: none; font-weight: 500;">ADR Programming</a>'
        )
        self.lbl_footer.setOpenExternalLinks(True)
        self.lbl_footer.setStyleSheet("font-size: 8.5pt; color: #60a5fa;")
        self.lbl_footer.setAlignment(Qt.AlignCenter)

        footer_layout.addWidget(self.lbl_footer)
        content_layout.addLayout(footer_layout)

        # --- 6. Status Bar ---
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
        mono_font = QtGui.QFont("JetBrains Mono", 9)
        mono_font.setStyleHint(QtGui.QFont.Monospace)

        self.table_convs.setRowCount(len(conv_list))
        for row, conv in enumerate(conv_list):
            # Title: soft sand-100 / sand-200
            item_title = QTableWidgetItem(conv["title"])
            item_title.setToolTip(f"{conv['title']}\nID: {conv['id']}")
            item_title.setForeground(QtGui.QColor("#bfdbfe"))

            # Modified Time: soft sand-400
            mtime_str = datetime.datetime.fromtimestamp(conv["mtime"]).strftime("%Y-%m-%d %H:%M") if conv["mtime"] else "-"
            item_mtime = QTableWidgetItem(mtime_str)
            item_mtime.setTextAlignment(Qt.AlignCenter)
            item_mtime.setForeground(QtGui.QColor("#60a5fa"))

            # Size: soft sand-400
            size_mb = conv["size"] / (1024 * 1024)
            size_str = f"{size_mb:.1f} MB" if size_mb >= 0.1 else f"{conv['size'] / 1024:.0f} KB"
            item_size = QTableWidgetItem(size_str)
            item_size.setTextAlignment(Qt.AlignCenter)
            item_size.setFont(mono_font)
            item_size.setForeground(QtGui.QColor("#60a5fa"))

            # Conv ID: subtle sand-500
            item_id = QTableWidgetItem(conv["id"])
            item_id.setTextAlignment(Qt.AlignCenter)
            item_id.setFont(mono_font)
            item_id.setForeground(QtGui.QColor("#3b82f6"))

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
            self.lbl_selected_info.setStyleSheet("color: #60a5fa; font-style: italic; font-size: 8.5pt;")
            self.btn_process.setEnabled(False)
            return

        row_idx = selected_rows[0].row()
        item_title = self.table_convs.item(row_idx, 0)
        if item_title:
            conv = item_title.data(Qt.UserRole)
            self.selected_conv = conv
            self.lbl_selected_info.setText(
                f"Percakapan Terpilih: <b style='color:#dbeafe;'>{conv['title']}</b> &nbsp;|&nbsp; <span style='color:#60a5fa;'>ID: {conv['id']}</span>"
            )
            self.lbl_selected_info.setStyleSheet("color: #bfdbfe; font-size: 8.5pt;")
            self.txt_new_title.setText(conv["title"])
            self.txt_new_title.setFocus()
            self.txt_new_title.selectAll()
            self.btn_process.setEnabled(True)

    def on_clean_zombies_clicked(self):
        count, zombies = scan_zombie_conversations()
        if count == 0:
            show_info(self, "Cache Bersih", "Tidak ada percakapan zombie yang ditemukan di cache UI.")
            return

        confirm = show_question(
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
                show_info(self, "Pembersihan Sukses", msg)
                self.refresh_data()
            else:
                show_critical(self, "Gagal Membersihkan", msg)

    def process_rename(self):
        if not self.selected_conv:
            show_warning(self, "Peringatan", "Silakan pilih percakapan dari tabel terlebih dahulu!")
            return

        new_title = self.txt_new_title.text().strip()
        if not new_title:
            show_warning(self, "Peringatan", "Nama baru tidak boleh kosong!")
            return

        conv_id = self.selected_conv["id"]
        old_title = self.selected_conv["title"]

        if new_title == old_title:
            show_info(self, "Info", "Nama baru sama persis dengan nama saat ini.")
            return

        # Save AGI path if edited
        agi_path = self.txt_path.text().strip()
        if agi_path:
            save_agi_path(agi_path)

        # Execute Dual-Sync Rename
        self.status_bar.showMessage("Menjalankan Dual-Sync Rename...")
        success, message = rename_conversation_by_id(conv_id, new_title)

        if success:
            result = show_question(
                self,
                "Sukses Rename",
                f"{message}\n\n"
                f"Judul berhasil diubah menjadi: '{new_title}'\n\n"
                "Apakah Anda ingin mereload Antigravity IDE sekarang untuk menerapkan perubahan judul di sidebar?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if result == QMessageBox.Yes:
                self.reload_agi(agi_path)

            self.refresh_data()
        else:
            show_critical(self, "Gagal Rename", message)
            self.status_bar.showMessage("Gagal melakukan rename.", 4000)

    def reload_agi(self, agi_path):
        self.status_bar.showMessage("Menutup dan mereload Antigravity IDE...")
        try:
            # Matikan AGI
            subprocess.run('taskkill /F /IM "Antigravity IDE.exe" /T', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Non-blocking pause menggunakan QTimer agar GUI tidak freeze
            QTimer.singleShot(2000, lambda: self._launch_agi_after_kill(agi_path))
        except Exception as e:
            show_warning(self, "Error Reload", f"Gagal mereload AGI: {e}")

    def _launch_agi_after_kill(self, agi_path):
        try:
            if agi_path and os.path.exists(agi_path):
                subprocess.Popen([agi_path], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
                self.status_bar.showMessage("Antigravity IDE berhasil dibuka kembali.", 4000)
            else:
                show_warning(
                    self,
                    "Path Tidak Ditemukan",
                    "Path Antigravity IDE.exe tidak valid. Silakan buka IDE Anda secara manual."
                )
                self.status_bar.showMessage("Path AGI tidak valid.", 4000)
        except Exception as e:
            show_warning(self, "Error Meluncurkan AGI", f"Gagal membuka AGI: {e}")


if __name__ == '__main__':
    # Silence Font Spam Logs
    os.environ["QT_LOGGING_RULES"] = "qt.qpa.fonts=false"

    app = QApplication(sys.argv)
    app.setStyleSheet(OCEAN_THEME_QSS)

    window = MainApp()
    window.show()
    sys.exit(app.exec_())
