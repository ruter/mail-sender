# -*- coding: utf-8 -*-
"""Mail configuration view using PySide6."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QTextEdit, QLabel, QFormLayout, QSpinBox
)
from PySide6.QtCore import Qt
from typing import Optional

from views.base import (
    create_button, create_input,
    show_error, show_toast, DEFAULT_FONT
)
from services.mail_sender import MailSender, SMTPConfig, MailTemplate


class ConfigView(QWidget):
    """Mail configuration widget for SMTP and signature."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()
        self._load_config()
    
    def _setup_ui(self) -> None:
        """Build the UI layout."""
        main_layout = QHBoxLayout(self)
        
        # Left: SMTP Config
        smtp_group = QGroupBox('SMTP 配置')
        smtp_group.setFont(DEFAULT_FONT)
        smtp_layout = QVBoxLayout(smtp_group)
        
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        
        self._server_input = create_input(placeholder='smtp.qq.com')
        form.addRow('SMTP服务器:', self._server_input)
        
        self._port_spin = QSpinBox()
        self._port_spin.setFont(DEFAULT_FONT)
        self._port_spin.setRange(1, 65535)
        self._port_spin.setValue(465)
        form.addRow('端口:', self._port_spin)
        
        self._email_input = create_input(placeholder='your@email.com')
        form.addRow('发件人邮箱:', self._email_input)
        
        self._password_input = create_input(password=True)
        form.addRow('密码/授权码:', self._password_input)
        
        smtp_layout.addLayout(form)
        
        # Hint
        hint = QLabel('常用: QQ邮箱 smtp.qq.com:465 | 163邮箱 smtp.163.com:465')
        hint.setStyleSheet('color: #666666; font-size: 9pt;')
        hint.setWordWrap(True)
        smtp_layout.addWidget(hint)
        
        smtp_layout.addStretch()
        
        # SMTP buttons
        smtp_btn_layout = QHBoxLayout()
        self._save_smtp_btn = create_button('保存配置', primary=True)
        self._test_smtp_btn = create_button('测试连接')
        smtp_btn_layout.addWidget(self._save_smtp_btn)
        smtp_btn_layout.addWidget(self._test_smtp_btn)
        smtp_btn_layout.addStretch()
        smtp_layout.addLayout(smtp_btn_layout)
        
        # Right: Signature (global)
        sig_group = QGroupBox('邮件签名 (全局)')
        sig_group.setFont(DEFAULT_FONT)
        sig_layout = QVBoxLayout(sig_group)
        
        sig_label = QLabel('签名会自动附加到所有邮件正文末尾:')
        sig_label.setFont(DEFAULT_FONT)
        sig_layout.addWidget(sig_label)
        
        self._signature_input = QTextEdit()
        self._signature_input.setFont(DEFAULT_FONT)
        self._signature_input.setPlaceholderText('此致\n人力资源部')
        sig_layout.addWidget(self._signature_input)
        
        sig_layout.addStretch()
        
        # Signature button
        sig_btn_layout = QHBoxLayout()
        self._save_sig_btn = create_button('保存签名', primary=True)
        sig_btn_layout.addWidget(self._save_sig_btn)
        sig_btn_layout.addStretch()
        sig_layout.addLayout(sig_btn_layout)
        
        # Add groups to main layout
        main_layout.addWidget(smtp_group)
        main_layout.addWidget(sig_group)
    
    def _connect_signals(self) -> None:
        """Connect button signals to handlers."""
        self._save_smtp_btn.clicked.connect(self._on_save_smtp)
        self._test_smtp_btn.clicked.connect(self._on_test_smtp)
        self._save_sig_btn.clicked.connect(self._on_save_signature)
    
    def _load_config(self) -> None:
        """Load existing config from database."""
        config = MailSender.get_config()
        if config:
            self._server_input.setText(config.smtp_server)
            self._port_spin.setValue(config.port)
            self._email_input.setText(config.sender_email)
            self._password_input.setText(config.password)
        
        template = MailSender.get_template()
        self._signature_input.setPlainText(template.signature)
    
    def refresh(self) -> None:
        """Refresh config data from database."""
        self._load_config()
    
    def _on_save_smtp(self) -> None:
        """Handle save SMTP config button click."""
        server = self._server_input.text().strip()
        port = self._port_spin.value()
        email = self._email_input.text().strip()
        password = self._password_input.text()
        
        if not all([server, email, password]):
            show_error('请填写完整的 SMTP 配置', parent=self)
            return
        
        try:
            config = SMTPConfig(server, port, email, password)
            MailSender.save_config(config)
            show_toast('SMTP 配置已保存', parent=self)
        except Exception as e:
            show_error(f'保存失败: {e}', parent=self)
    
    def _on_test_smtp(self) -> None:
        """Handle test SMTP connection button click."""
        server = self._server_input.text().strip()
        port = self._port_spin.value()
        email = self._email_input.text().strip()
        password = self._password_input.text()
        
        if not all([server, email, password]):
            show_error('请填写完整的 SMTP 配置', parent=self)
            return
        
        try:
            config = SMTPConfig(server, port, email, password)
            success, error = MailSender.test_connection(config)
            
            if success:
                show_toast('连接成功！', parent=self)
            else:
                show_error(f'连接失败: {error}', parent=self)
        except Exception as e:
            show_error(f'测试失败: {e}', parent=self)
    
    def _on_save_signature(self) -> None:
        """Handle save signature button click."""
        signature = self._signature_input.toPlainText()
        
        try:
            # Keep existing body_template (now unused globally, but preserve for compatibility)
            existing = MailSender.get_template()
            template = MailTemplate(existing.body_template, signature)
            MailSender.save_template(template)
            show_toast('邮件签名已保存', parent=self)
        except Exception as e:
            show_error(f'保存失败: {e}', parent=self)
