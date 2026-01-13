# -*- coding: utf-8 -*-
"""Category management view using PySide6."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QTableWidget, QLineEdit, QPushButton, QTextEdit,
    QLabel, QSplitter, QFormLayout
)
from PySide6.QtCore import Qt
from typing import Optional

from views.base import (
    create_table, update_table, create_button, create_input,
    create_label, create_separator, show_error, show_toast, confirm,
    DEFAULT_FONT
)
from models.category import Category, CategoryRepository


class CategoryView(QWidget):
    """Category management widget for file matching patterns."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._category_id: Optional[int] = None
        self._setup_ui()
        self._connect_signals()
        self._load_data()
    
    def _setup_ui(self) -> None:
        """Setup the UI layout."""
        main_layout = QHBoxLayout(self)
        
        # Left: Form
        form_group = QGroupBox('分类信息')
        form_layout = QVBoxLayout(form_group)
        
        # Name input
        form_layout.addWidget(create_label('分类名称:'))
        self._name_input = create_input(placeholder='如：绩效数据')
        form_layout.addWidget(self._name_input)
        
        # Pattern input (multiline)
        form_layout.addWidget(create_label('匹配规则 (正则表达式):'))
        self._pattern_input = QTextEdit()
        self._pattern_input.setFont(DEFAULT_FONT)
        self._pattern_input.setMaximumHeight(60)
        self._pattern_input.setPlaceholderText(r'^(.+?)\s*-\s*(\d+)月绩效.+\.xlsx$')
        form_layout.addWidget(self._pattern_input)
        
        # Hint for pattern
        hint_label = QLabel('提示: 使用括号()捕获，第一组=负责人，第二组=月份')
        hint_label.setStyleSheet('color: #666666; font-size: 9pt;')
        form_layout.addWidget(hint_label)
        
        form_layout.addWidget(create_separator())
        
        # Subject template
        form_layout.addWidget(create_label('邮件主题模板:'))
        self._subject_input = create_input(placeholder='{month}月绩效数据结果')
        form_layout.addWidget(self._subject_input)
        
        # Body template
        form_layout.addWidget(create_label('正文模板 (可用变量: {owner} {month}):'))
        self._body_input = QTextEdit()
        self._body_input.setFont(DEFAULT_FONT)
        self._body_input.setMaximumHeight(80)
        self._body_input.setPlaceholderText('@{owner} 这是{month}月的绩效数据结果，请查收。')
        form_layout.addWidget(self._body_input)
        
        form_layout.addStretch()
        form_layout.addWidget(create_separator())
        
        # Buttons
        btn_layout = QHBoxLayout()
        self._save_btn = create_button('保存', primary=True)
        self._clear_btn = create_button('清空')
        btn_layout.addWidget(self._save_btn)
        btn_layout.addWidget(self._clear_btn)
        btn_layout.addStretch()
        form_layout.addLayout(btn_layout)
        
        # Right: Table
        table_group = QGroupBox('分类列表')
        table_layout = QVBoxLayout(table_group)
        
        self._table = create_table(
            headings=['ID', '分类名称', '匹配规则', '主题模板'],
            data=[]
        )
        self._table.setColumnWidth(0, 40)
        self._table.setColumnWidth(1, 100)
        self._table.setColumnWidth(2, 200)
        self._table.setColumnWidth(3, 180)
        table_layout.addWidget(self._table)
        
        table_btn_layout = QHBoxLayout()
        self._edit_btn = create_button('编辑')
        self._delete_btn = create_button('删除', danger=True)
        table_btn_layout.addWidget(self._edit_btn)
        table_btn_layout.addWidget(self._delete_btn)
        table_btn_layout.addStretch()
        table_layout.addLayout(table_btn_layout)
        
        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(form_group)
        splitter.addWidget(table_group)
        splitter.setSizes([300, 500])
        main_layout.addWidget(splitter)
    
    def _connect_signals(self) -> None:
        self._save_btn.clicked.connect(self._on_save)
        self._clear_btn.clicked.connect(self._on_clear)
        self._edit_btn.clicked.connect(self._on_edit)
        self._delete_btn.clicked.connect(self._on_delete)
    
    def _load_data(self) -> None:
        categories = CategoryRepository.get_all()
        data = [[c.id, c.name, c.pattern, c.subject_template] for c in categories]
        update_table(self._table, data)
    
    def refresh(self) -> None:
        self._load_data()
    
    def _on_save(self) -> None:
        name = self._name_input.text().strip()
        pattern = self._pattern_input.toPlainText().strip()
        subject_template = self._subject_input.text().strip()
        body_template = self._body_input.toPlainText().strip()
        
        if not name:
            show_error('请输入分类名称', parent=self)
            return
        if not pattern:
            show_error('请输入匹配规则', parent=self)
            return
        
        try:
            if self._category_id:
                CategoryRepository.update(self._category_id, name, pattern, subject_template, body_template)
                show_toast('分类已更新', parent=self)
            else:
                CategoryRepository.create(name, pattern, subject_template, body_template)
                show_toast('分类已添加', parent=self)
            
            self._load_data()
            self._on_clear()
        except ValueError as e:
            show_error(str(e), parent=self)
        except Exception as e:
            show_error(f'保存失败: {e}', parent=self)
    
    def _on_clear(self) -> None:
        self._category_id = None
        self._name_input.clear()
        self._pattern_input.clear()
        self._subject_input.clear()
        self._body_input.clear()
    
    def _on_edit(self) -> None:
        row = self._table.currentRow()
        if row < 0:
            show_error('请先选择要编辑的分类', parent=self)
            return
        
        self._category_id = int(self._table.item(row, 0).text())
        category = CategoryRepository.get_by_id(self._category_id)
        if category:
            self._name_input.setText(category.name)
            self._pattern_input.setPlainText(category.pattern)
            self._subject_input.setText(category.subject_template)
            self._body_input.setPlainText(category.body_template)
    
    def _on_delete(self) -> None:
        row = self._table.currentRow()
        if row < 0:
            show_error('请先选择要删除的分类', parent=self)
            return
        
        category_id = int(self._table.item(row, 0).text())
        name = self._table.item(row, 1).text()
        
        if not confirm(f'删除分类 "{name}" 会同时删除相关的收件人配置，确定删除？', parent=self):
            return
        
        try:
            CategoryRepository.delete(category_id)
            show_toast('分类已删除', parent=self)
            self._load_data()
            self._on_clear()
        except Exception as e:
            show_error(f'删除失败: {e}', parent=self)
