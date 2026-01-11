# 📄 PRD｜邮件助手（MVP）

## 1. 产品概述

### 1.1 产品名称

**邮件助手（Mail Assistant）**

### 1.2 产品目标

通过 **Python + SQLite + GUI** 实现绩效结果 Excel 的**自动识别、自动匹配收件人、自动发送邮件**，减少重复人工操作，并为未来扩展其他邮件自动化任务预留空间。

### 1.3 MVP 边界（非常重要）

**本期只实现：**

* 单一任务类型：绩效结果发送
* 本地运行（非 Web）
* 手动触发发送（不含定时）
* SMTP 邮件发送

**本期不做：**

* 权限系统
* 审批流
* 多任务并行
* 云部署
* 企业邮箱 API（如 Outlook/Gmail）

---

## 2. 用户画像

| 角色        | 描述                |
| --------- | ----------------- |
| HR / 管理人员 | 每月需要向各部门负责人发送绩效结果 |
| 技术背景      | 非技术 / 初级技术        |
| 使用频率      | 每月 1 次（但步骤多、重复性高） |

---

## 3. 使用场景（User Story）

### 3.1 核心 Story（必须支持）

> 我每月将各部门绩效 Excel 放入一个目录，文件命名为
> `{部门负责人} - {month}月绩效数据结果.xlsx`
> 我希望系统能自动：
>
> * 识别部门负责人
> * 找到对应邮箱
> * 附件发送
> * 自动抄送固定人员

---

## 4. 功能需求（Functional Requirements）

### 4.1 文件扫描与解析

#### 4.1.1 文件目录选择

* 用户可通过 GUI 选择一个本地文件夹
* 系统扫描该目录下的 `.xlsx` 文件

#### 4.1.2 文件命名规则（固定）

```text
{owner} - {month}月绩效数据结果.xlsx
```

#### 4.1.3 解析结果

对每个文件解析出：

```json
{
  "filename": "张三 - 3月绩效数据结果.xlsx",
  "owner": "张三",
  "month": "3"
}
```

#### 4.1.4 异常处理

| 情况     | 行为            |
| ------ | ------------- |
| 文件名不匹配 | 标记为“解析失败”，不发送 |
| 目录为空   | 提示用户          |

---

### 4.2 联系人管理

#### 4.2.1 联系人字段

| 字段    | 类型      | 必填 |
| ----- | ------- | -- |
| id    | INTEGER | 是  |
| name  | TEXT    | 是  |
| email | TEXT    | 是  |

#### 4.2.2 功能

* 新增联系人
* 编辑联系人
* 删除联系人
* 列表查看

#### 4.2.3 限制

* name 唯一
* email 格式校验

---

### 4.3 抄送关系管理（核心）

#### 4.3.1 数据结构

一个部门负责人对应一组抄送人

```json
{
  "owner_name": "张三",
  "cc_contact_ids": [2, 3]
}
```

#### 4.3.2 功能

* 为部门负责人配置抄送人
* 抄送人来自联系人表
* 一个负责人可对应多个抄送人

---

### 4.4 邮件模板

#### 4.4.1 模板内容（固定）

```text
@{owner} 这是{month}月的绩效数据结果，请查收。
```

#### 4.4.2 变量支持

| 变量    | 来源    |
| ----- | ----- |
| owner | 文件名解析 |
| month | 文件名解析 |

---

### 4.5 邮件发送

#### 4.5.1 邮件规则

* TO：部门负责人邮箱
* CC：该负责人对应的抄送人邮箱
* 附件：对应 Excel 文件

#### 4.5.2 发送方式

* SMTP
* 配置项：

  * SMTP Server
  * Port
  * 发件人邮箱
  * 密码 / 授权码

#### 4.5.3 发送结果

| 状态 | 说明              |
| -- | --------------- |
| 成功 | 邮件成功发送          |
| 失败 | SMTP 错误 / 联系人缺失 |

---

## 5. GUI 需求（桌面应用）

### 5.1 技术建议

* Python GUI：

  * Tkinter

---

### 5.2 页面结构

#### 页面 1：绩效发送主界面

* 文件夹选择按钮
* 文件扫描结果表格：

  * 文件名
  * 负责人
  * 月份
  * 状态
* 「开始发送」按钮
* 发送日志输出区域

---

#### 页面 2：联系人管理

* 联系人列表
* 新增 / 编辑 / 删除

---

#### 页面 3：抄送关系配置

* 左侧：部门负责人下拉框
* 右侧：联系人多选（抄送人）
* 保存按钮

---

#### 页面 4：邮件配置

* SMTP Server
* 端口
* 发件人邮箱
* 密码 / 授权码
* 测试发送按钮

---

## 6. 数据库设计（SQLite）

### 6.1 表结构

#### contacts

```sql
id INTEGER PRIMARY KEY AUTOINCREMENT
name TEXT UNIQUE NOT NULL
email TEXT NOT NULL
```

#### cc_mappings

```sql
id INTEGER PRIMARY KEY AUTOINCREMENT
owner_name TEXT NOT NULL
contact_id INTEGER NOT NULL
```

#### send_logs

```sql
id INTEGER PRIMARY KEY AUTOINCREMENT
filename TEXT
owner_name TEXT
status TEXT
error_message TEXT
created_at DATETIME
```

---

## 7. 非功能性需求

### 7.1 稳定性

* 单次支持 ≥ 100 个 Excel 文件
* 单文件失败不影响整体流程

### 7.2 可维护性

* 文件解析、邮件发送、GUI 解耦
* 使用 Service / Repository 分层

---

## 8. 项目结构建议（强烈建议）

```text
mail_assistant/
├── app.py                 # 程序入口
├── gui/
│   ├── main_window.py
│   ├── contact_view.py
│   ├── cc_mapping_view.py
│   └── config_view.py
├── services/
│   ├── file_parser.py
│   ├── mail_sender.py
│   └── task_service.py
├── db/
│   ├── database.py
│   └── migrations.sql
├── models/
│   ├── contact.py
│   └── cc_mapping.py
├── utils/
│   └── template.py
└── config.yaml
```

---

## 9. 验收标准（Acceptance Criteria）

* ✔ 能正确解析文件名
* ✔ 能正确匹配负责人邮箱
* ✔ 抄送人准确
* ✔ 邮件内容变量正确替换
* ✔ 发送结果可追踪
* ✔ GUI 可完成全流程，无需命令行

---

## 10. 后续可扩展方向（不做，但需预留）

* 多任务支持
* 定时发送
* 多模板
* 发送前预览
* 邮件发送统计

