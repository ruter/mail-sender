# -*- coding: utf-8 -*-
"""Recipient mapping view using PySide6."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QDialog, QComboBox,
    QListWidget, QListWidgetItem, QLabel, QDialogButtonBox,
    QFormLayout, QAbstractItemView, QLineEdit
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


class SearchableComboBox(QWidget):
    """ComboBox with search/filter functionality."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._items: List[tuple] = []  # (text, data)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Search input
        self._search_input = QLineEdit()
        self._search_input.setFont(DEFAULT_FONT)
        self._search_input.setPlaceholderText('输入姓名或邮箱搜索...')
        self._search_input.textChanged.connect(self._on_search_changed)
        layout.addWidget(self._search_input)
        
        # Combo box
        self._combo = QComboBox()
        self._combo.setFont(DEFAULT_FONT)
        layout.addWidget(self._combo)
    
    def addItem(self, text: str, data: object = None) -> None:
        """Add item to the combo box."""
        self._items.append((text, data))
        self._combo.addItem(text, data)
    
    def _on_search_changed(self, text: str) -> None:
        """Filter combo items based on search text."""
        self._combo.clear()
        search_lower = text.lower()
        for item_text, item_data in self._items:
            if not text or search_lower in item_text.lower():
                self._combo.addItem(item_text, item_data)
    
    def currentData(self) -> object:
        """Get current selected data."""
        return self._combo.currentData()
    
    def currentIndex(self) -> int:
        """Get current index."""
        return self._combo.currentIndex()
    
    def setCurrentIndex(self, index: int) -> None:
        """Set current index."""
        self._combo.setCurrentIndex(index)
    
    def findData(self, data: object) -> int:
        """Find index by data."""
        for i, (_, item_data) in enumerate(self._items):
            if item_data == data:
                return i
        return -1


class FilterableListWidget(QWidget):
    """ListWidget with search/filter functionality for multi-selection."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._items: List[tuple] = []  # (text, data, item)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Search input
        self._search_input = QLineEdit()
        self._search_input.setFont(DEFAULT_FONT)
        self._search_input.setPlaceholderText('输入姓名或邮箱搜索...')
        self._search_input.textChanged.connect(self._on_search_changed)
        layout.addWidget(self._search_input)
        
        # List widget
        self._list = QListWidget()
        self._list.setFont(DEFAULT_FONT)
        self._list.setSelectionMode(QAbstractItemView.MultiSelection)
        self._list.setMaximumHeight(120)
        layout.addWidget(self._list)
    
    def addItem(self, text: str, data: object = None) -> None:
        """Add item to the list."""
        item = QListWidgetItem(text)
        item.setData(Qt.UserRole, data)
        self._items.append((text, data, item))
        self._list.addItem(item)
    
    def _on_search_changed(self, text: str) -> None:
        """Filter list items based on search text."""
        self._list.clear()
        search_lower = text.lower()
        for item_text, item_data, item in self._items:
            if not text or search_lower in item_text.lower():
                # Preserve selection state
                new_item = QListWidgetItem(item_text)
                new_item.setData(Qt.UserRole, item_data)
                if item.isSelected():
                    new_item.setSelected(True)
                self._list.addItem(new_item)
    
    def count(self) -> int:
        """Get visible item count."""
        return self._list.count()
    
    def item(self, index: int) -> Optional[QListWidgetItem]:
        """Get item at index."""
        return self._list.item(index)
    
    def selectedItems(self) -> List[QListWidgetItem]:
        """Get all selected items."""
        return self._list.selectedItems()


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
        
        # Owner name input
        self._owner_input = QLineEdit()
        self._owner_input.setFont(DEFAULT_FONT)
        self._owner_input.setPlaceholderText('文件名正则匹配出的 owner 名称')
        form_layout.addRow('Owner:', self._owner_input)
        
        # Recipient searchable combo
        self._recipient_combo = SearchableComboBox()
        form_layout.addRow('收件人:', self._recipient_combo)
        
        # CC filterable list
        self._cc_list = FilterableListWidget()
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
            display_text = f'{contact.name} ({contact.email})'
            self._recipient_combo.addItem(display_text, contact.id)
            self._cc_list.addItem(display_text, contact.id)
        
        # Pre-select if editing
        if self._mapping:
            # Select category
            idx = self._category_combo.findData(self._mapping.category.id)
            if idx >= 0:
                self._category_combo.setCurrentIndex(idx)
            
            # Set owner name
            self._owner_input.setText(self._mapping.owner_name)
            
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
        if not self._owner_input.text().strip():
            show_error('请输入 Owner 名称', parent=self)
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
            'owner_name': self._owner_input.text().strip(),
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
            headings=['ID', '分类', 'Owner', '收件人', '抄送人'],
            data=[]
        )
        self._table.setColumnWidth(0, 50)
        self._table.setColumnWidth(1, 100)
        self._table.setColumnWidth(2, 80)
        self._table.setColumnWidth(3, 180)
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
                m.owner_name,
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
                    result['owner_name'],
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
                    result['owner_name'],
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
