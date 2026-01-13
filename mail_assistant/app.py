# -*- coding: utf-8 -*-
"""Mail Assistant - PySide6 Desktop Application Entry Point.

This module provides the main GUI interface for the mail assistant application.
Run this file directly to start the desktop application.

Usage:
    python app.py
"""

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from views.send_view import SendView
from views.contact_view import ContactView
from views.category_view import CategoryView
from views.mapping_view import MappingView
from views.config_view import ConfigView


class MainWindow(QMainWindow):
    """Main application window with tabbed interface."""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self) -> None:
        """Setup the main window UI."""
        self.setWindowTitle('邮件助手')
        self.resize(950, 700)
        
        # Set default font for entire application
        font = QFont('Microsoft YaHei', 10)
        self.setFont(font)
        
        # Create tab widget
        self._tab_widget = QTabWidget()
        self._tab_widget.setFont(font)
        self.setCentralWidget(self._tab_widget)
        
        # Create and add views
        self._send_view = SendView()
        self._contact_view = ContactView()
        self._category_view = CategoryView()
        self._mapping_view = MappingView()
        self._config_view = ConfigView()
        
        self._tab_widget.addTab(self._send_view, '邮件发送')
        self._tab_widget.addTab(self._contact_view, '联系人管理')
        self._tab_widget.addTab(self._category_view, '分类管理')
        self._tab_widget.addTab(self._mapping_view, '收件人配置')
        self._tab_widget.addTab(self._config_view, '邮件配置')
        
        # Apply stylesheet for modern look
        self.setStyleSheet('''
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: white;
            }
            QTabBar::tab {
                padding: 8px 20px;
                margin-right: 2px;
                background-color: #e0e0e0;
                border: 1px solid #cccccc;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #d0d0d0;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        ''')
    
    def _connect_signals(self) -> None:
        """Connect tab change signal to refresh views."""
        self._tab_widget.currentChanged.connect(self._on_tab_changed)
    
    def _on_tab_changed(self, index: int) -> None:
        """Refresh the current tab's data when switched to."""
        current_widget = self._tab_widget.widget(index)
        if hasattr(current_widget, 'refresh'):
            current_widget.refresh()


def main() -> None:
    """Main entry point for the GUI application."""
    app = QApplication(sys.argv)
    
    # Set application-wide font
    font = QFont('Microsoft YaHei', 10)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
