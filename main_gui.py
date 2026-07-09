import os
import sys
import subprocess
import time

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QApplication, QFrame, QLabel, QLineEdit, 
                             QPushButton, QMessageBox, QFileDialog)

from rename_logic import rename_conversation
from settings_manager import get_agi_path, save_agi_path


class Ui_Frame(object):
    def setupUi(self, Frame):
        Frame.setObjectName("Frame")
        Frame.resize(500, 320)
        Frame.setWindowTitle("Antigravity Conversation Renamer")
        
        # Styles
        label_style = "font-weight: bold; font-size: 10pt;"
        input_style = "padding: 5px; font-size: 10pt; border: 1px solid #ccc; border-radius: 4px;"
        btn_style = "background-color: #2b78e4; color: white; font-weight: bold; border-radius: 4px; padding: 5px;"
        browse_style = "background-color: #666; color: white; font-weight: bold; border-radius: 4px; padding: 5px;"

        y_pos = 20
        
        # AGI Path Section
        self.lbl_path = QLabel(Frame)
        self.lbl_path.setGeometry(QtCore.QRect(20, y_pos, 150, 20))
        self.lbl_path.setText("AGI Executable Path:")
        self.lbl_path.setStyleSheet(label_style)
        
        y_pos += 25
        self.txt_path = QLineEdit(Frame)
        self.txt_path.setGeometry(QtCore.QRect(20, y_pos, 380, 30))
        self.txt_path.setStyleSheet(input_style)
        self.txt_path.setText(get_agi_path())
        
        self.btn_browse = QPushButton(Frame)
        self.btn_browse.setGeometry(QtCore.QRect(410, y_pos, 70, 30))
        self.btn_browse.setText("Browse")
        self.btn_browse.setStyleSheet(browse_style)
        self.btn_browse.clicked.connect(self.browse_path)

        y_pos += 45
        
        # Old Title Section
        self.lbl_old = QLabel(Frame)
        self.lbl_old.setGeometry(QtCore.QRect(20, y_pos, 150, 20))
        self.lbl_old.setText("Nama Asli (Old Title):")
        self.lbl_old.setStyleSheet(label_style)
        
        y_pos += 25
        self.txt_old = QLineEdit(Frame)
        self.txt_old.setGeometry(QtCore.QRect(20, y_pos, 460, 30))
        self.txt_old.setStyleSheet(input_style)
        self.txt_old.setPlaceholderText("Masukkan judul persis seperti di sidebar...")
        
        y_pos += 45
        
        # New Title Section
        self.lbl_new = QLabel(Frame)
        self.lbl_new.setGeometry(QtCore.QRect(20, y_pos, 150, 20))
        self.lbl_new.setText("Nama Baru (New Title):")
        self.lbl_new.setStyleSheet(label_style)
        
        y_pos += 25
        self.txt_new = QLineEdit(Frame)
        self.txt_new.setGeometry(QtCore.QRect(20, y_pos, 460, 30))
        self.txt_new.setStyleSheet(input_style)
        self.txt_new.setPlaceholderText("Masukkan judul baru yang Anda inginkan...")
        
        y_pos += 50
        
        # Process Button
        self.btn_process = QPushButton(Frame)
        self.btn_process.setGeometry(QtCore.QRect(20, y_pos, 460, 40))
        self.btn_process.setText("Process Rename")
        self.btn_process.setStyleSheet(btn_style)
        self.btn_process.clicked.connect(self.process_rename)

    def browse_path(self):
        file_path, _ = QFileDialog.getOpenFileName(None, "Pilih Antigravity IDE.exe", "C:\\", "Executable (*.exe)")
        if file_path:
            self.txt_path.setText(file_path)
            save_agi_path(file_path)

    def process_rename(self):
        old_title = self.txt_old.text().strip()
        new_title = self.txt_new.text().strip()
        agi_path = self.txt_path.text().strip()
        
        if not old_title or not new_title:
            QMessageBox.warning(None, "Peringatan", "Nama Asli dan Nama Baru tidak boleh kosong!")
            return
            
        save_agi_path(agi_path)
            
        # Panggil fungsi logika
        success, message = rename_conversation(old_title, new_title)
        
        if success:
            # Memunculkan dialog untuk mereload AGI
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Question)
            msg_box.setWindowTitle("Sukses")
            msg_box.setText(f"{message}\n\nBerhasil mengubah judul!\nApakah Anda ingin mereload AGI untuk menerapkan judul baru?")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.Yes)
            
            result = msg_box.exec_()
            if result == QMessageBox.Yes:
                self.reload_agi(agi_path)
                
            # Kosongkan form setelah sukses
            self.txt_old.clear()
            self.txt_new.clear()
        else:
            QMessageBox.critical(None, "Gagal", message)
            
    def reload_agi(self, agi_path):
        try:
            # Matikan AGI
            subprocess.run('taskkill /F /IM "Antigravity IDE.exe" /T', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2) # Beri jeda sistem untuk menutup cache LevelDB
            
            # Jalankan kembali AGI jika path valid
            if agi_path and os.path.exists(agi_path):
                # Detach process
                subprocess.Popen([agi_path], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                QMessageBox.warning(None, "Path Tidak Valid", "Path AGI tidak valid. Silakan buka AGI secara manual.")
        except Exception as e:
            QMessageBox.warning(None, "Error Reload", f"Gagal mereload AGI: {e}")

if __name__ == '__main__':
    # Untuk membersihkan log sampah Font
    os.environ["QT_LOGGING_RULES"] = "qt.qpa.fonts=false"

    app = QApplication(sys.argv)
    Frame = QFrame()
    ui = Ui_Frame()
    ui.setupUi(Frame)
    Frame.show()
    sys.exit(app.exec_())
