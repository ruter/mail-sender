# -*- coding: utf-8 -*-
"""Base view utilities for PySide6 components."""

from PySide6.QtWidgets import (
    QWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QPushButton, QLineEdit, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QSizePolicy, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont
from typing import List, Any, Optional

# Default font for Chinese display
DEFAULT_FONT = QFont('Microsoft YaHei', 10)


def create_table(
    headings: List[str],
    data: List[List[Any]],
    parent: Optional[QWidget] = None
) -> QTableWidget:
    """Create a standardized QTableWidget.
    
    Args:
        headings: Column header names.
        data: Table data as list of rows.
        parent: Parent widget.
    
    Returns:
        Configured QTableWidget instance.
    """
    table = QTableWidget(parent)
    table.setColumnCount(len(headings))
    table.setHorizontalHeaderLabels(headings)
    table.setRowCount(len(data))
    
    # Configure table appearance
    table.setFont(DEFAULT_FONT)
    table.horizontalHeader().setFont(DEFAULT_FONT)
    table.setAlternatingRowColors(True)
    table.setSelectionBehavior(QTableWidget.SelectRows)
    table.setSelectionMode(QTableWidget.SingleSelection)
    table.horizontalHeader().setStretchLastSection(True)
    table.verticalHeader().setVisible(False)
    
    # Populate data
    for row_idx, row_data in enumerate(data):
        for col_idx, value in enumerate(row_data):
            item = QTableWidgetItem(str(value) if value is not None else '')
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Read-only
            table.setItem(row_idx, col_idx, item)
    
    return table


def update_table(table: QTableWidget, data: List[List[Any]]) -> None:
    """Update table with new data.
    
    Args:
        table: QTableWidget to update.
        data: New data as list of rows.
    """
    table.setRowCount(len(data))
    for row_idx, row_data in enumerate(data):
        for col_idx, value in enumerate(row_data):
            item = QTableWidgetItem(str(value) if value is not None else '')
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row_idx, col_idx, item)


def show_error(message: str, title: str = '错误', parent: Optional[QWidget] = None) -> None:
    """Display an error message box."""
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setFont(DEFAULT_FONT)
    msg_box.exec()


def show_info(message: str, title: str = '提示', parent: Optional[QWidget] = None) -> None:
    """Display an information message box."""
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Information)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setFont(DEFAULT_FONT)
    msg_box.exec()


def confirm(message: str, title: str = '确认', parent: Optional[QWidget] = None) -> bool:
    """Display a confirmation dialog.
    
    Returns:
        True if user clicked Yes, False otherwise.
    """
    result = QMessageBox.question(
        parent, title, message,
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )
    return result == QMessageBox.Yes


def create_button(
    text: str,
    primary: bool = False,
    danger: bool = False,
    parent: Optional[QWidget] = None
) -> QPushButton:
    """Create a styled button."""
    btn = QPushButton(text, parent)
    btn.setFont(DEFAULT_FONT)
    btn.setMinimumWidth(80)
    
    if primary:
        btn.setStyleSheet('''
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #106ebe; }
            QPushButton:pressed { background-color: #005a9e; }
            QPushButton:disabled { background-color: #cccccc; }
        ''')
    elif danger:
        btn.setStyleSheet('''
            QPushButton {
                background-color: #d43b3b;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #c02020; }
            QPushButton:pressed { background-color: #a01010; }
        ''')
    else:
        btn.setStyleSheet('''
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                padding: 6px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #e0e0e0; }
            QPushButton:pressed { background-color: #d0d0d0; }
        ''')
    
    return btn


def create_input(
    placeholder: str = '',
    password: bool = False,
    parent: Optional[QWidget] = None
) -> QLineEdit:
    """Create a styled line edit."""
    line_edit = QLineEdit(parent)
    line_edit.setFont(DEFAULT_FONT)
    line_edit.setPlaceholderText(placeholder)
    if password:
        line_edit.setEchoMode(QLineEdit.Password)
    line_edit.setStyleSheet('''
        QLineEdit {
            padding: 6px;
            border: 1px solid #cccccc;
            border-radius: 4px;
        }
        QLineEdit:focus { border-color: #0078d4; }
    ''')
    return line_edit


def create_label(text: str, bold: bool = False, parent: Optional[QWidget] = None) -> QLabel:
    """Create a styled label."""
    label = QLabel(text, parent)
    font = QFont('Microsoft YaHei', 10)
    if bold:
        font.setBold(True)
    label.setFont(font)
    return label


def create_separator(parent: Optional[QWidget] = None) -> QFrame:
    """Create a horizontal separator line."""
    line = QFrame(parent)
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    return line


class Toast(QLabel):
    """Non-blocking toast notification widget.
    
    Displays a message at the bottom of the parent widget
    and automatically fades out after a short duration.
    """
    
    def __init__(self, message: str, parent: QWidget, duration: int = 2000):
        """Create a toast notification.
        
        Args:
            message: Text to display.
            parent: Parent widget to attach to.
            duration: Display duration in milliseconds.
        """
        super().__init__(message, parent)
        self.setFont(DEFAULT_FONT)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet('''
            QLabel {
                background-color: rgba(50, 50, 50, 0.9);
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
            }
        ''')
        self.adjustSize()
        
        # Position at bottom center of parent
        self._reposition()
        
        # Setup fade effect
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)
        
        # Show and start timer
        self.show()
        self.raise_()
        
        # Fade out after duration
        QTimer.singleShot(duration, self._fade_out)
    
    def _reposition(self) -> None:
        """Position toast at bottom center of parent."""
        if self.parent():
            parent_rect = self.parent().rect()
            x = (parent_rect.width() - self.width()) // 2
            y = parent_rect.height() - self.height() - 30
            self.move(x, y)
    
    def _fade_out(self) -> None:
        """Animate fade out and delete."""
        self._animation = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._animation.setDuration(300)
        self._animation.setStartValue(1.0)
        self._animation.setEndValue(0.0)
        self._animation.setEasingCurve(QEasingCurve.OutQuad)
        self._animation.finished.connect(self.deleteLater)
        self._animation.start()


def show_toast(message: str, parent: Optional[QWidget] = None, duration: int = 2000) -> None:
    """Display a non-blocking toast notification.
    
    Args:
        message: Text to display.
        parent: Parent widget. If None, toast won't show.
        duration: Display duration in milliseconds.
    """
    if parent is None:
        return
    Toast(message, parent, duration)
