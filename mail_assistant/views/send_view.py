# -*- coding: utf-8 -*-
"""Performance email sending view using PySide6."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QTableWidget, QPushButton, QLineEdit, QTextEdit,
    QLabel, QFileDialog, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from pathlib import Path
from typing import Optional, List

from views.base import (
    create_table, update_table, create_button, create_input,
    create_label, show_error, show_toast, DEFAULT_FONT
)
from services.file_parser import FileParser, ParsedFile
from services.task_service import TaskService, SendResult
from models.recipient_mapping import RecipientMappingRepository


class SendWorker(QThread):
    """Worker thread for sending emails asynchronously."""
    
    log_message = Signal(str)  # Emit log messages
    finished_result = Signal(list)  # Emit final results
    
    def __init__(self, parsed_files: List[ParsedFile]):
        super().__init__()
        self._parsed_files = parsed_files
    
    def run(self) -> None:
        def callback(msg: str):
            self.log_message.emit(msg)
        
        results = TaskService.process_files(self._parsed_files, callback)
        self.finished_result.emit(results)


class SendView(QWidget):
    """Performance email sending widget."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._parsed_files: List[ParsedFile] = []
        self._mapping_cache: dict = {}  # category_id -> (recipient_name, cc_names)
        self._worker: Optional[SendWorker] = None
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Hint box
        hint_frame = QFrame()
        hint_frame.setStyleSheet('''
            QFrame {
                background-color: #e7f3ff;
                border: 1px solid #0078d4;
                border-radius: 4px;
                padding: 10px;
            }
        ''')
        hint_layout = QHBoxLayout(hint_frame)
        hint_layout.setContentsMargins(10, 10, 10, 10)
        hint_label = QLabel('💡 提示：文件会根据"分类管理"中配置的正则表达式自动匹配分类，并使用对应的收件人和抄送人发送邮件。')
        hint_label.setFont(DEFAULT_FONT)
        hint_label.setWordWrap(True)
        hint_label.setStyleSheet('background: transparent; border: none;')
        hint_layout.addWidget(hint_label)
        layout.addWidget(hint_frame)
        
        # Folder selection group
        folder_group = QGroupBox('选择文件夹')
        folder_group.setFont(DEFAULT_FONT)
        folder_layout = QHBoxLayout(folder_group)
        
        self._folder_input = create_input(placeholder='选择或输入绩效文件所在目录')
        self._folder_input.setMinimumWidth(400)
        folder_layout.addWidget(self._folder_input, 1)
        
        self._browse_btn = create_button('选择文件夹')
        self._scan_btn = create_button('扫描文件', primary=True)
        folder_layout.addWidget(self._browse_btn)
        folder_layout.addWidget(self._scan_btn)
        layout.addWidget(folder_group)
        
        # Files table group
        table_group = QGroupBox('文件列表')
        table_group.setFont(DEFAULT_FONT)
        table_layout = QVBoxLayout(table_group)
        
        self._table = create_table(
            headings=['文件名', '分类', '收件人', '抄送人', '月份', '状态'],
            data=[]
        )
        self._table.setColumnWidth(0, 280)
        self._table.setColumnWidth(1, 100)
        self._table.setColumnWidth(2, 80)
        self._table.setColumnWidth(3, 120)
        self._table.setColumnWidth(4, 50)
        self._table.setColumnWidth(5, 80)
        self._table.setMinimumHeight(250)
        table_layout.addWidget(self._table)
        
        # Send button row
        send_layout = QHBoxLayout()
        send_layout.addStretch()
        self._send_btn = create_button('开始发送', primary=True)
        self._send_btn.setMinimumWidth(120)
        send_layout.addWidget(self._send_btn)
        send_layout.addStretch()
        table_layout.addLayout(send_layout)
        
        layout.addWidget(table_group, 1)  # stretch factor 1
        
        # Log area group
        log_group = QGroupBox('发送日志')
        log_group.setFont(DEFAULT_FONT)
        log_layout = QVBoxLayout(log_group)
        
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setFont(QFont('Consolas', 10))
        self._log_text.setStyleSheet('''
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                border: none;
                padding: 8px;
            }
        ''')
        self._log_text.setMinimumHeight(150)
        self._log_text.setMaximumHeight(200)
        log_layout.addWidget(self._log_text)
        
        layout.addWidget(log_group)
    
    def _connect_signals(self) -> None:
        self._browse_btn.clicked.connect(self._on_browse)
        self._scan_btn.clicked.connect(self._on_scan)
        self._send_btn.clicked.connect(self._on_send)
    
    def refresh(self) -> None:
        """Refresh view - no action needed for this view."""
        pass
    
    def _on_browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, '选择绩效文件夹')
        if folder:
            self._folder_input.setText(folder)
    
    def _on_scan(self) -> None:
        folder = self._folder_input.text().strip()
        
        if not folder:
            show_error('请先选择或输入文件夹路径', parent=self)
            return
        
        if not Path(folder).exists():
            show_error('文件夹不存在', parent=self)
            return
        
        self._parsed_files = FileParser.scan_directory(folder)
        
        if not self._parsed_files:
            show_toast('目录为空或没有找到 xlsx 文件', parent=self)
            return
        
        # Build mapping cache for recipient/cc display and check owner matching
        self._mapping_cache.clear()
        for pf in self._parsed_files:
            if pf.category_id and pf.owner:
                cache_key = (pf.category_id, pf.owner)
                if cache_key not in self._mapping_cache:
                    mapping = RecipientMappingRepository.get_by_category_and_owner(pf.category_id, pf.owner)
                    if mapping:
                        cc_names = ', '.join([c.name for c in mapping.cc_contacts]) if mapping.cc_contacts else '-'
                        self._mapping_cache[cache_key] = (mapping.recipient.name, cc_names, True)
                    else:
                        self._mapping_cache[cache_key] = ('-', '-', False)
                        # Mark file as having no matching recipient
                        pf.status = "无匹配收件人"
                        pf.error_message = f"分类 '{pf.category_name}' 下未找到 owner '{pf.owner}' 的收件人映射"
        
        data = []
        for pf in self._parsed_files:
            if pf.category_id and pf.owner:
                cache_key = (pf.category_id, pf.owner)
                if cache_key in self._mapping_cache:
                    recipient_name, cc_names, matched = self._mapping_cache[cache_key]
                    if not matched:
                        recipient_name, cc_names = '-', '-'
                else:
                    recipient_name, cc_names = '-', '-'
            else:
                recipient_name, cc_names = '-', '-'
            data.append([
                pf.filename, 
                pf.category_name or '-', 
                recipient_name, 
                cc_names, 
                pf.month or '-', 
                pf.status
            ])
        update_table(self._table, data)
        self._log(f'扫描完成，共找到 {len(self._parsed_files)} 个文件')
    
    def _on_send(self) -> None:
        if not self._parsed_files:
            show_error('请先扫描文件', parent=self)
            return
        
        # Filter files that can be sent (must have category and not be in error state)
        valid_files = [
            pf for pf in self._parsed_files 
            if pf.status not in ('解析失败', '无匹配收件人') and pf.category_id
        ]
        
        if not valid_files:
            show_error('没有可发送的文件（需要匹配到分类且有对应的收件人映射）', parent=self)
            return
        
        # Disable button during send
        self._send_btn.setEnabled(False)
        self._log('开始发送...')
        
        # Start worker thread
        self._worker = SendWorker(self._parsed_files)
        self._worker.log_message.connect(self._on_log_message)
        self._worker.finished_result.connect(self._on_send_complete)
        self._worker.start()
    
    def _on_log_message(self, message: str) -> None:
        self._log(message)
    
    def _on_send_complete(self, results: List[SendResult]) -> None:
        self._send_btn.setEnabled(True)
        
        # Build result map
        result_map = {r.filename: r.status for r in results} if results else {}
        
        # Update parsed files status
        for pf in self._parsed_files:
            if pf.filename in result_map:
                new_status = result_map[pf.filename]
                if new_status == "跳过":
                    pf.status = "跳过"
                else:
                    pf.status = "发送" + new_status
        
        # Refresh table with updated status
        data = []
        for pf in self._parsed_files:
            if pf.category_id and pf.owner:
                cache_key = (pf.category_id, pf.owner)
                if cache_key in self._mapping_cache:
                    recipient_name, cc_names, matched = self._mapping_cache[cache_key]
                    if not matched:
                        recipient_name, cc_names = '-', '-'
                else:
                    recipient_name, cc_names = '-', '-'
            else:
                recipient_name, cc_names = '-', '-'
            data.append([
                pf.filename, 
                pf.category_name or '-', 
                recipient_name, 
                cc_names, 
                pf.month or '-', 
                pf.status
            ])
        update_table(self._table, data)
        
        # Log summary
        success_count = sum(1 for r in results if r.status == '成功') if results else 0
        skip_count = sum(1 for r in results if r.status == '跳过') if results else 0
        fail_count = len(results) - success_count - skip_count if results else 0
        self._log(f'发送完成! 成功: {success_count}, 跳过: {skip_count}, 失败: {fail_count}')
    
    def _log(self, message: str) -> None:
        self._log_text.append(message)
        # Scroll to bottom
        scrollbar = self._log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
