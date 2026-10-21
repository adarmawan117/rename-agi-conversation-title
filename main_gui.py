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

QFrame#RootContainer {
    background-color: #0c1a3a;
    border: 1px solid #1e3a8a;
    border-radius: 0px;
}

QFrame#RootContainerMaximized {
    background-color: #0c1a3a;
    border: none;
}

/* Custom In-App Title Bar */
QWidget#CustomTitleBar {
    background-color: #081329;
    border-bottom: 1px solid #1e3a8a;
}

QLabel#windowTitleText {
    font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
    font-size: 9pt;
    font-weight: 500;
    color: #bfdbfe;
    letter-spacing: 0.2px;
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

QPushButton#titleMinBtn, QPushButton#titleMaxBtn {
    background-color: transparent;
    border: none;
    color: #60a5fa;
    font-size: 11pt;
    font-weight: bold;
    padding: 0px;
}

QPushButton#titleMinBtn:hover, QPushButton#titleMaxBtn:hover {
    background-color: #1e3a8a;
    color: #ffffff;
}

QPushButton#titleCloseBtn {
    background-color: transparent;
    border: none;
    color: #60a5fa;
    font-size: 11pt;
    font-weight: bold;
    padding: 0px;
}

QPushButton#titleCloseBtn:hover {
    background-color: #e11d48;
    color: #ffffff;
}

QPushButton#titleCloseBtn:pressed {
    background-color: #be123c;
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


def setup_windows_frameless(window):
    """
    Mengonfigurasi jendela frameless di Windows:
    - Mengaktifkan WS_MINIMIZEBOX, WS_MAXIMIZEBOX, WS_SYSMENU agar klik taskbar berfungsi
    - Mengaktifkan WS_THICKFRAME agar Windows mengizinkan resize border
    - Mengaktifkan DWM drop shadow native
    - Menghormati sudut bulat di Windows 11 jika didukung
    """
    if sys.platform != "win32":
        return

    try:
        hwnd = int(window.winId())
        if not hwnd:
            return

        GWL_STYLE = -16
        WS_MINIMIZEBOX = 0x00020000
        WS_MAXIMIZEBOX = 0x00010000
        WS_SYSMENU     = 0x00080000
        WS_THICKFRAME  = 0x00040000
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
        ctypes.windll.user32.SetWindowLongW(
            hwnd,
            GWL_STYLE,
            style | WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_SYSMENU | WS_THICKFRAME
        )
        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0027)

        # Drop shadow via DwmExtendFrameIntoClientArea
        class MARGINS(ctypes.Structure):
            _fields_ = [
                ("cxLeftWidth", ctypes.c_int),
                ("cxRightWidth", ctypes.c_int),
                ("cyTopHeight", ctypes.c_int),
                ("cyBottomHeight", ctypes.c_int)
            ]
        margins = MARGINS(1, 1, 1, 1)
        ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margins))

        # Windows 11 Rounded corners
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        DWMWCP_ROUND = 2
        corner_pref = ctypes.c_int(DWMWCP_ROUND)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_WINDOW_CORNER_PREFERENCE,
            ctypes.byref(corner_pref),
            ctypes.sizeof(corner_pref)
        )
    except Exception as e:
        pass


def apply_dark_dialog_titlebar(dialog):
    """Menerapkan dark title bar pada pop-up dialog di Windows."""
    if sys.platform != "win32":
        return
    try:
        hwnd = int(dialog.winId())
        if hwnd:
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            val = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(val), ctypes.sizeof(val)
            )
            DWMWA_CAPTION_COLOR = 35
            caption_col = ctypes.c_int(0x003A1A0C)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_CAPTION_COLOR, ctypes.byref(caption_col), ctypes.sizeof(caption_col)
            )
    except Exception:
        pass


def show_info(parent, title, text):
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setStandardButtons(QMessageBox.Ok)
    apply_dark_dialog_titlebar(msg)
    return msg.exec_()


def show_warning(parent, title, text):
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setStandardButtons(QMessageBox.Ok)
    apply_dark_dialog_titlebar(msg)
    return msg.exec_()


def show_critical(parent, title, text):
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setStandardButtons(QMessageBox.Ok)
    apply_dark_dialog_titlebar(msg)
    return msg.exec_()


def show_question(parent, title, text, buttons=QMessageBox.Yes | QMessageBox.No, default=QMessageBox.Yes):
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Question)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setStandardButtons(buttons)
    msg.setDefaultButton(default)
    apply_dark_dialog_titlebar(msg)
    return msg.exec_()


class CustomTitleBar(QWidget):
    """
    Custom in-app title bar bergaya modern frameless
    mengikuti tema Ocean Gelap ADR Prompt Manager.
    """
    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.setFixedHeight(36)
        self.setObjectName("CustomTitleBar")
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 0, 0)
        layout.setSpacing(8)

        # Icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(18, 18)
        self.icon_label.setScaledContents(True)
        self.icon_label.setAttribute(Qt.WA_TransparentForMouseEvents)

        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "google-antigravity.ico")
        if getattr(sys, 'frozen', False):
            icon_path = os.path.join(sys._MEIPASS, "google-antigravity.ico")
        if os.path.exists(icon_path):
            self.icon_label.setPixmap(QtGui.QPixmap(icon_path))

        layout.addWidget(self.icon_label)

        # Title
        self.title_label = QLabel("Antigravity Conversation Renamer")
        self.title_label.setObjectName("windowTitleText")
        self.title_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(self.title_label)

        # Badge
        self.badge = QLabel("v1.0")
        self.badge.setObjectName("windowBadge")
        self.badge.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(self.badge)

        layout.addStretch()

        # Window Controls
        self.btn_min = QPushButton("―")
        self.btn_min.setObjectName("titleMinBtn")
        self.btn_min.setToolTip("Minimalkan")
        self.btn_min.setFixedSize(44, 36)
        self.btn_min.clicked.connect(self.parent_window.showMinimized)
        layout.addWidget(self.btn_min)

        self.btn_max = QPushButton("□")
        self.btn_max.setObjectName("titleMaxBtn")
        self.btn_max.setToolTip("Maksimalkan")
        self.btn_max.setFixedSize(44, 36)
        self.btn_max.clicked.connect(self.parent_window.toggle_maximize)
        layout.addWidget(self.btn_max)

        self.btn_close = QPushButton("✕")
        self.btn_close.setObjectName("titleCloseBtn")
        self.btn_close.setToolTip("Tutup")
        self.btn_close.setFixedSize(46, 36)
        self.btn_close.clicked.connect(self.parent_window.close)
        layout.addWidget(self.btn_close)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.parent_window.windowHandle():
                self.parent_window.windowHandle().startSystemMove()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.parent_window.toggle_maximize()
        super().mouseDoubleClickEvent(event)


class DataLoaderThread(QThread):
    """Thread for loading conversations & scanning zombie entries in background."""
    data_loaded = pyqtSignal(list, int)

    def run(self):
        convs = list_conversations()
        zombie_count, _ = scan_zombie_conversations()
        self.data_loaded.emit(convs, zombie_count)


class MainApp(QMainWindow):
    BORDER_WIDTH = 8

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Antigravity Conversation Renamer")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window | Qt.WindowMinMaxButtonsHint)
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
        setup_windows_frameless(self)

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.WindowStateChange:
            if self.isMaximized():
                self.title_bar.btn_max.setText("❐")
                self.title_bar.btn_max.setToolTip("Pulihkan")
                self.root_container.setObjectName("RootContainerMaximized")
                self.root_container.setStyle(self.root_container.style())
            else:
                self.title_bar.btn_max.setText("□")
                self.title_bar.btn_max.setToolTip("Maksimalkan")
                self.root_container.setObjectName("RootContainer")
                self.root_container.setStyle(self.root_container.style())
        super().changeEvent(event)

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def nativeEvent(self, eventType, message):
        """
        Gunakan penanganan native Windows:
        - WM_NCCALCSIZE (0x0083): Menghilangkan border frame putih non-client DWM bawaan Windows
        - WM_NCHITTEST (0x0084): Mengatur area resize border kursor secara native & responsif
        """
        if sys.platform == "win32" and eventType == b"windows_generic_MSG":
            try:
                msg = wintypes.MSG.from_address(message.__int__())
                if msg.message == 0x0083:  # WM_NCCALCSIZE - Hilangkan frame border putih non-client DWM
                    return True, 0

                if not self.isMaximized() and msg.message == 0x0084:  # WM_NCHITTEST
                    x = ctypes.c_short(msg.lParam & 0xFFFF).value
                    y = ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value
                    local_pt = self.mapFromGlobal(QtCore.QPoint(x, y))
                    lx = local_pt.x()
                    ly = local_pt.y()
                    w = self.width()
                    h = self.height()
                    b = self.BORDER_WIDTH

                    # Sudut (Corner Resizing)
                    if lx <= b and ly <= b:
                        return True, 13  # HTTOPLEFT
                    elif lx >= w - b and ly <= b:
                        return True, 14  # HTTOPRIGHT
                    elif lx <= b and ly >= h - b:
                        return True, 16  # HTBOTTOMLEFT
                    elif lx >= w - b and ly >= h - b:
                        return True, 17  # HTBOTTOMRIGHT
                    # Tepi (Edge Resizing)
                    elif lx <= b:
                        return True, 10  # HTLEFT
                    elif lx >= w - b:
                        return True, 11  # HTRIGHT
                    elif ly <= b:
                        return True, 12  # HTTOP
                    elif ly >= h - b:
                        return True, 15  # HTBOTTOM
            except Exception:
                pass

        return super().nativeEvent(eventType, message)

    def init_ui(self):
        # Root Frame with subtle border
        self.root_container = QFrame(self)
        self.root_container.setObjectName("RootContainer")
        self.setCentralWidget(self.root_container)

        root_layout = QVBoxLayout(self.root_container)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Custom In-App Title Bar
        self.title_bar = CustomTitleBar(self)
        root_layout.addWidget(self.title_bar)

        # 2. Main Content Container
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(16, 12, 16, 10)
        content_layout.setSpacing(10)

        # --- 1. Header Hero Bar ---
        header_layout = QHBoxLayout()
        header_info = QVBoxLayout()
        header_info.setSpacing(2)

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

        root_layout.addWidget(content_widget, stretch=1)

        # --- 6. Status Bar with Size Grip ---
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Siap.")
        self.size_grip = QSizeGrip(self)
        self.status_bar.addPermanentWidget(self.size_grip)
        root_layout.addWidget(self.status_bar)

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
