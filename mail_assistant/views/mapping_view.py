# -*- coding: utf-8 -*-
"""Recipient mapping view using PySide6."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QTableWidget, QPushButton, QDialog, QComboBox,
    QListWidget, QListWidgetItem, QLabel, QDialogButtonBox,
    QFormLayout, QAbstractItemView
)
from PySide6.QtCore import Qt
from typing import Optional, List

from views.base import (
    create_table, update_table, create_button, create_label,
    show_error, show_toast, confirm, DEFAULT_FONT
)
from models.contact import Contact, ContactRepository
from models.category import Category, CategoryRepository
from models.recipient_mapping import RecipientMapping, RecipientMappingRepository


class MappingDialog(QDialog):
    """Dialog for adding/editing recipient mappings."""
    
    def __init__(
        self,
        categories: List[Category],
        contacts: List[Contact],
        mapping: Optional[RecipientMapping] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._categories = categories
        self._contacts = contacts
        self._mapping = mapping
        self._setup_ui()
        self._populate_data()
    
    def _setup_ui(self) -> None:
        self.setWindowTitle('编辑映射' if self._mapping else '新增映射')
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # Category dropdown
        self._category_combo = QComboBox()
        self._category_combo.setFont(DEFAULT_FONT)
        form_layout.addRow('分类:', self._category_combo)
        
        # Recipient dropdown
        self._recipient_combo = QComboBox()
        self._recipient_combo.setFont(DEFAULT_FONT)
        form_layout.addRow('收件人:', self._recipient_combo)
        
        # CC multi-select list
        self._cc_list = QListWidget()
        self._cc_list.setFont(DEFAULT_FONT)
        self._cc_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self._cc_list.setMaximumHeight(150)
        form_layout.addRow('抄送人:', self._cc_list)
        
        # Hint for multi-selection
        hint_label = QLabel('(按住 Ctrl 可多选)')
        hint_label.setStyleSheet('color: gray; font-size: 9pt;')
        form_layout.addRow('', hint_label)
        
        layout.addLayout(form_layout)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _populate_data(self) -> None:
        # Populate categories
        for cat in self._categories:
            self._category_combo.addItem(cat.name, cat.id)
        
        # Populate contacts for recipient and CC
        for contact in self._contacts:
            self._recipient_combo.addItem(f'{contact.name} ({contact.email})', contact.id)
            item = QListWidgetItem(f'{contact.name} ({contact.email})')
            item.setData(Qt.UserRole, contact.id)
            self._cc_list.addItem(item)
        
        # Pre-select if editing
        if self._mapping:
            # Select category
            idx = self._category_combo.findData(self._mapping.category.id)
            if idx >= 0:
                self._category_combo.setCurrentIndex(idx)
            
            # Select recipient
            idx = self._recipient_combo.findData(self._mapping.recipient.id)
            if idx >= 0:
                self._recipient_combo.setCurrentIndex(idx)
            
            # Select CC contacts
            cc_ids = [c.id for c in self._mapping.cc_contacts]
            for i in range(self._cc_list.count()):
                item = self._cc_list.item(i)
                if item.data(Qt.UserRole) in cc_ids:
                    item.setSelected(True)
    
    def _on_accept(self) -> None:
        if self._category_combo.currentIndex() < 0:
            show_error('请选择分类', parent=self)
            return
        if self._recipient_combo.currentIndex() < 0:
            show_error('请选择收件人', parent=self)
            return
        self.accept()
    
    def get_result(self) -> dict:
        """Get the dialog result data."""
        cc_ids = [
            self._cc_list.item(i).data(Qt.UserRole)
            for i in range(self._cc_list.count())
            if self._cc_list.item(i).isSelected()
        ]
        return {
            'category_id': self._category_combo.currentData(),
            'recipient_id': self._recipient_combo.currentData(),
            'cc_ids': cc_ids
        }


class MappingView(QWidget):
    """Recipient mapping management widget."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()
        self._load_data()
    
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        # Top buttons
        btn_layout = QHBoxLayout()
        self._add_btn = create_button('新增映射', primary=True)
        btn_layout.addWidget(self._add_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Table
        self._table = create_table(
            headings=['ID', '分类', '收件人', '抄送人'],
            data=[]
        )
        self._table.setColumnWidth(0, 50)
        self._table.setColumnWidth(1, 120)
        self._table.setColumnWidth(2, 200)
        layout.addWidget(self._table)
        
        # Bottom buttons
        bottom_btn_layout = QHBoxLayout()
        self._edit_btn = create_button('编辑')
        self._delete_btn = create_button('删除', danger=True)
        bottom_btn_layout.addWidget(self._edit_btn)
        bottom_btn_layout.addWidget(self._delete_btn)
        bottom_btn_layout.addStretch()
        layout.addLayout(bottom_btn_layout)
    
    def _connect_signals(self) -> None:
        self._add_btn.clicked.connect(self._on_add)
        self._edit_btn.clicked.connect(self._on_edit)
        self._delete_btn.clicked.connect(self._on_delete)
    
    def _load_data(self) -> None:
        mappings = RecipientMappingRepository.get_all()
        data = []
        for m in mappings:
            cc_names = ', '.join([c.name for c in m.cc_contacts]) if m.cc_contacts else '-'
            data.append([
                m.id,
                m.category.name,
                f'{m.recipient.name} ({m.recipient.email})',
                cc_names
            ])
        update_table(self._table, data)
    
    def refresh(self) -> None:
        self._load_data()
    
    def _on_add(self) -> None:
        categories = CategoryRepository.get_all()
        contacts = ContactRepository.get_all()
        
        if not categories:
            show_error('请先添加分类', parent=self)
            return
        if not contacts:
            show_error('请先添加联系人', parent=self)
            return
        
        dialog = MappingDialog(categories, contacts, parent=self)
        if dialog.exec() == QDialog.Accepted:
            result = dialog.get_result()
            try:
                RecipientMappingRepository.create(
                    result['category_id'],
                    result['recipient_id'],
                    result['cc_ids']
                )
                show_toast('映射已添加', parent=self)
                self._load_data()
            except Exception as e:
                show_error(f'添加失败: {e}', parent=self)
    
    def _on_edit(self) -> None:
        row = self._table.currentRow()
        if row < 0:
            show_error('请先选择要编辑的映射', parent=self)
            return
        
        mapping_id = int(self._table.item(row, 0).text())
        mapping = RecipientMappingRepository.get_by_id(mapping_id)
        
        if not mapping:
            show_error('映射不存在', parent=self)
            return
        
        categories = CategoryRepository.get_all()
        contacts = ContactRepository.get_all()
        
        dialog = MappingDialog(categories, contacts, mapping, parent=self)
        if dialog.exec() == QDialog.Accepted:
            result = dialog.get_result()
            try:
                RecipientMappingRepository.update(
                    mapping_id,
                    result['category_id'],
                    result['recipient_id'],
                    result['cc_ids']
                )
                show_toast('映射已更新', parent=self)
                self._load_data()
            except Exception as e:
                show_error(f'更新失败: {e}', parent=self)
    
    def _on_delete(self) -> None:
        row = self._table.currentRow()
        if row < 0:
            show_error('请先选择要删除的映射', parent=self)
            return
        
        mapping_id = int(self._table.item(row, 0).text())
        
        if not confirm('确定要删除此映射吗？', parent=self):
            return
        
        try:
            RecipientMappingRepository.delete(mapping_id)
            show_toast('映射已删除', parent=self)
            self._load_data()
        except Exception as e:
            show_error(f'删除失败: {e}', parent=self)
