# -*- coding: utf-8 -*-
"""Views module - PySide6 UI components and utilities."""

from .base import (
    create_table,
    update_table,
    show_error,
    show_info,
    show_toast,
    Toast,
    confirm,
    create_button,
    create_input,
    create_label,
    create_separator,
    DEFAULT_FONT,
)
from .send_view import SendView
from .contact_view import ContactView
from .category_view import CategoryView
from .mapping_view import MappingView, MappingDialog
from .config_view import ConfigView

__all__ = [
    # Base utilities
    'create_table',
    'update_table',
    'show_error',
    'show_info',
    'show_toast',
    'Toast',
    'confirm',
    'create_button',
    'create_input',
    'create_label',
    'create_separator',
    'DEFAULT_FONT',
    # View widgets
    'SendView',
    'ContactView',
    'CategoryView',
    'MappingView',
    'MappingDialog',
    'ConfigView',
]
