# 邮件助手 (Mail Assistant)

基于 Python + SQLite 的绩效邮件自动发送工具，提供桌面 GUI 操作。

## 功能特性

- **文件扫描解析**: 自动识别 `{负责人} - {月份}月绩效数据结果.xlsx` 格式文件
- **联系人管理**: 支持增删改查，邮箱格式校验
- **抄送配置**: 为每个部门负责人配置抄送人列表
- **邮件发送**: 通过 SMTP 批量发送邮件，支持附件
- **发送日志**: 记录每次发送状态

## 安装运行

```bash
# 进入项目目录
cd mail_assistant

# 运行程序
python3 app.py
```

## 使用流程

1. **配置SMTP** - 在「邮件配置」页面填写SMTP服务器信息并测试连接
2. **添加联系人** - 在「联系人管理」页面添加部门负责人及抄送人
3. **配置抄送关系** - 在「抄送配置」页面为每个负责人设置抄送人
4. **发送邮件** - 在「绩效发送」页面选择文件夹、扫描文件、开始发送

## 文件命名规范

```
{负责人姓名} - {月份}月绩效考勤系数&名单.xlsx
```

示例:
- `张三 - 3月绩效考勤系数&名单.xlsx`
- `李四 - 12月绩效考勤系数&名单.xlsx`

## 项目结构

```
mail_assistant/
├── app.py                 # 程序入口 (PySide6)
├── views/                 # GUI视图模块
│   ├── base.py            # 基础组件
│   ├── send_view.py       # 绩效发送
│   ├── contact_view.py    # 联系人管理
│   ├── category_view.py   # 分类管理
│   ├── mapping_view.py    # 收件人配置
│   └── config_view.py     # 邮件配置
├── services/              # 业务逻辑
├── db/                    # 数据库
├── models/                # 数据模型
└── utils/                 # 工具类
```

## 常用SMTP配置

| 邮箱 | 服务器 | 端口 |
|------|--------|------|
| QQ邮箱 | smtp.qq.com | 465 |
| 163邮箱 | smtp.163.com | 465 |
| Gmail | smtp.gmail.com | 587 |
| Outlook | smtp.office365.com | 587 |

## 打包为可执行文件

### Windows 打包步骤

在 Windows 电脑上执行：

```bash
# 1. 安装 PyInstaller
pip install pyinstaller

# 2. 运行打包脚本
python build.py

# 或者直接使用 spec 文件打包
pyinstaller mail_assistant.spec
```

打包完成后，可执行文件在 `dist/邮件助手/` 目录下，双击 `邮件助手.exe` 即可运行。

### 分发

将 `dist/邮件助手/` 整个文件夹复制给用户即可使用。
