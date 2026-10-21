# -*- coding: utf-8 -*-
"""
Dialog Helper Functions - Antigravity Conversation Renamer
Provides styled pop-up dialogs (Info, Warning, Critical, Question) with dark DWM title bar support.
"""
from PyQt5.QtWidgets import QMessageBox

try:
    from src.styles import apply_dark_window_titlebar
except ImportError:
    from styles import apply_dark_window_titlebar


def show_info(parent, title: str, text: str):
    """Displays an Information message box with dark title bar."""
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setStandardButtons(QMessageBox.Ok)
    apply_dark_window_titlebar(msg)
    return msg.exec_()


def show_warning(parent, title: str, text: str):
    """Displays a Warning message box with dark title bar."""
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setStandardButtons(QMessageBox.Ok)
    apply_dark_window_titlebar(msg)
    return msg.exec_()


def show_critical(parent, title: str, text: str):
    """Displays a Critical Error message box with dark title bar."""
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setStandardButtons(QMessageBox.Ok)
    apply_dark_window_titlebar(msg)
    return msg.exec_()


def show_question(
    parent,
    title: str,
    text: str,
    buttons=QMessageBox.Yes | QMessageBox.No,
    default=QMessageBox.Yes
):
    """Displays a Question/Confirmation message box with dark title bar."""
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Question)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setStandardButtons(buttons)
    msg.setDefaultButton(default)
    apply_dark_window_titlebar(msg)
    return msg.exec_()
