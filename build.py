#!/usr/bin/env python3
"""
打包脚本 - 将邮件助手打包为可执行文件

使用方法:
1. 安装依赖: pip install pyinstaller
2. 运行打包: python build.py

打包完成后，可执行文件在 dist/邮件助手/ 目录下
"""

import subprocess
import sys
import os

def main():
    # 确保在正确的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Data file separator (Windows uses semicolon, Unix uses colon)
    sep = ';' if sys.platform == 'win32' else ':'
    
    # PyInstaller arguments
    args = [
        sys.executable, '-m', 'PyInstaller',
        '--name=邮件助手',
        '--onedir',
        '--windowed',  # Windows下不显示控制台窗口
        '--noconfirm',
        '--clean',
        f'--add-data=mail_assistant/db/migrations.sql{sep}db',
        # PySide6 hidden imports for PyInstaller compatibility
        '--hidden-import=PySide6.QtCore',
        '--hidden-import=PySide6.QtGui',
        '--hidden-import=PySide6.QtWidgets',
        '--collect-all=PySide6',
        'mail_assistant/app.py'
    ]
    
    print("开始打包...")
    print(f"命令: {' '.join(args)}")
    
    result = subprocess.run(args)
    
    if result.returncode == 0:
        print("\n打包成功!")
        print("可执行文件位置: dist/邮件助手/")
    else:
        print("\n打包失败!")
        sys.exit(1)

if __name__ == '__main__':
    main()
