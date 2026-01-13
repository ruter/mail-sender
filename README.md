# 邮件助手 (Mail Assistant)

基于 PySide6 + SQLite 的邮件批量发送工具，提供桌面 GUI 操作。支持自定义文件匹配规则、邮件模板和收件人配置。

## 功能特性

- **分类管理**: 使用正则表达式定义文件匹配规则，支持自定义邮件主题和正文模板
- **文件扫描解析**: 自动扫描目录中的 `.xlsx` 文件，根据分类规则匹配并提取负责人、月份等信息
- **联系人管理**: 支持联系人增删改查，邮箱格式校验
- **收件人配置**: 为每个分类配置收件人和抄送人列表
- **邮件发送**: 通过 SMTP 批量发送邮件，支持附件、异步发送
- **发送日志**: 实时显示发送状态和日志

## 安装运行

```bash
# 安装依赖
pip install -r requirements.txt

# 进入项目目录并运行
cd mail_assistant
python app.py
```

## 使用流程

1. **配置 SMTP** - 在「邮件配置」页面填写 SMTP 服务器信息
2. **创建分类** - 在「分类管理」页面添加文件匹配规则和邮件模板
3. **添加联系人** - 在「联系人管理」页面添加收件人和抄送人
4. **配置收件人** - 在「收件人配置」页面为每个分类设置收件人和抄送人
5. **发送邮件** - 在「邮件发送」页面选择文件夹、扫描文件、开始发送

## 分类配置说明

分类使用正则表达式匹配文件名，需包含两个捕获组：
- 第一个捕获组: 负责人姓名 (`{owner}`)
- 第二个捕获组: 月份 (`{month}`)

### 示例

| 分类名称 | 正则表达式 | 匹配文件示例 |
|---------|-----------|-------------|
| 绩效考勤 | `(.+?)\s*-\s*(\d+)月绩效考勤系数&名单\.xlsx` | `张三 - 3月绩效考勤系数&名单.xlsx` |
| 月度报表 | `(\S+)_(\d+)月报表\.xlsx` | `李四_12月报表.xlsx` |

### 邮件模板变量

- `{owner}` - 负责人姓名
- `{month}` - 月份

## 项目结构

```
mail_assistant/
├── app.py                 # 程序入口 (PySide6 主窗口)
├── views/                 # GUI 视图模块
│   ├── base.py            # 基础组件和工具函数
│   ├── send_view.py       # 邮件发送页面
│   ├── contact_view.py    # 联系人管理页面
│   ├── category_view.py   # 分类管理页面
│   ├── mapping_view.py    # 收件人配置页面
│   └── config_view.py     # 邮件配置页面
├── services/              # 业务逻辑
│   ├── file_parser.py     # 文件扫描和解析
│   ├── mail_sender.py     # SMTP 邮件发送
│   └── task_service.py    # 发送任务处理
├── models/                # 数据模型和仓库
│   ├── category.py        # 分类模型
│   ├── contact.py         # 联系人模型
│   └── recipient_mapping.py # 收件人映射模型
├── db/                    # 数据库
│   ├── database.py        # 数据库连接管理
│   └── migrations.sql     # 数据库表结构
├── utils/                 # 工具类
│   └── template.py        # 邮件模板渲染
└── data/                  # 数据文件目录
```

## 常用 SMTP 配置

| 邮箱 | 服务器 | 端口 |
|------|--------|------|
| QQ邮箱 | smtp.qq.com | 465 |
| 163邮箱 | smtp.163.com | 465 |
| Gmail | smtp.gmail.com | 587 |
| Outlook | smtp.office365.com | 587 |

## 打包为可执行文件

### Windows 打包

```bash
# 安装 PyInstaller
pip install pyinstaller

# 运行打包脚本
python build.py
```

打包完成后，可执行文件在 `dist/邮件助手/` 目录下。

## 依赖

- Python 3.8+
- PySide6 >= 6.5
- PyInstaller >= 6.0 (打包用)
