#!/usr/bin/env python3
import sys
import os
import json
import webbrowser
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TKINTER_AVAILABLE = False
try:
    import tkinter as tk
    from tkinter import filedialog
    TKINTER_AVAILABLE = True
except ImportError:
    pass


def choose_folder_dialog():
    if not TKINTER_AVAILABLE:
        return None
    result = [None]
    def ask():
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        folder = filedialog.askdirectory(title="选择绩效文件夹")
        root.destroy()
        result[0] = folder if folder else None
    t = threading.Thread(target=ask)
    t.start()
    t.join()
    return result[0]

from services.file_parser import FileParser
from services.mail_sender import MailSender, SMTPConfig, MailTemplate
from services.task_service import TaskService
from models.contact import ContactRepository
from models.cc_mapping import CCMappingRepository

HOST = "127.0.0.1"
PORT = 8080


class RequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _send_html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length).decode("utf-8")) if length else {}

    def do_GET(self):
        path = urlparse(self.path).path
        query = parse_qs(urlparse(self.path).query)

        if path == "/":
            self._send_html(HTML_PAGE)
        elif path == "/api/contacts":
            contacts = [{"id": c.id, "name": c.name, "email": c.email} for c in ContactRepository.get_all()]
            self._send_json(contacts)
        elif path == "/api/smtp":
            config = MailSender.get_config()
            if config:
                self._send_json({"smtp_server": config.smtp_server, "port": config.port, "sender_email": config.sender_email, "password": config.password})
            else:
                self._send_json({})
        elif path == "/api/template":
            template = MailSender.get_template()
            self._send_json({"body_template": template.body_template, "signature": template.signature})
        elif path == "/api/cc_mapping":
            owner = query.get("owner", [""])[0]
            if owner:
                ids = CCMappingRepository.get_cc_contact_ids(owner)
                self._send_json({"owner": owner, "cc_ids": ids})
            else:
                self._send_json({"error": "owner required"}, 400)
        elif path == "/api/scan":
            folder = query.get("folder", [""])[0]
            if folder:
                files = FileParser.scan_directory(folder)
                self._send_json([{"filename": f.filename, "filepath": f.filepath, "owner": f.owner, "month": f.month, "status": f.status, "error": f.error_message} for f in files])
            else:
                self._send_json({"error": "folder required"}, 400)
        elif path == "/api/choose_folder":
            folder = choose_folder_dialog()
            self._send_json({"folder": folder, "available": TKINTER_AVAILABLE})
        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        data = self._read_body()

        try:
            if path == "/api/contacts":
                contact = ContactRepository.create(data["name"], data["email"])
                self._send_json({"id": contact.id, "name": contact.name, "email": contact.email})
            elif path == "/api/contacts/update":
                contact = ContactRepository.update(data["id"], data["name"], data["email"])
                self._send_json({"id": contact.id, "name": contact.name, "email": contact.email})
            elif path == "/api/contacts/delete":
                ContactRepository.delete(data["id"])
                self._send_json({"success": True})
            elif path == "/api/smtp":
                config = SMTPConfig(data["smtp_server"], int(data["port"]), data["sender_email"], data["password"])
                MailSender.save_config(config)
                self._send_json({"success": True})
            elif path == "/api/template":
                template = MailTemplate(data["body_template"], data["signature"])
                MailSender.save_template(template)
                self._send_json({"success": True})
            elif path == "/api/smtp/test":
                config = SMTPConfig(data["smtp_server"], int(data["port"]), data["sender_email"], data["password"])
                success, error = MailSender.test_connection(config)
                self._send_json({"success": success, "error": error})
            elif path == "/api/cc_mapping":
                CCMappingRepository.set_cc_contacts(data["owner"], data["cc_ids"])
                self._send_json({"success": True})
            elif path == "/api/send":
                files = data.get("files", [])
                parsed = [type("PF", (), {"filepath": f["filepath"], "filename": f["filename"], "owner": f["owner"], "month": f["month"], "status": f["status"], "error_message": f.get("error")})() for f in files]
                results = []
                for pf in parsed:
                    res = TaskService.process_files([pf])
                    if res:
                        results.append({"filename": res[0].filename, "owner": res[0].owner_name, "status": res[0].status, "error": res[0].error_message})
                self._send_json(results)
            else:
                self._send_json({"error": "not found"}, 404)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {args[0]}")


HTML_PAGE = '''<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>邮件助手</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f5f5; padding: 20px; }
.container { max-width: 900px; margin: 0 auto; }
h1 { text-align: center; margin-bottom: 20px; color: #333; }
.tabs { display: flex; border-bottom: 2px solid #ddd; margin-bottom: 20px; }
.tab { padding: 10px 20px; cursor: pointer; border: none; background: none; font-size: 16px; color: #666; }
.tab.active { color: #007bff; border-bottom: 2px solid #007bff; margin-bottom: -2px; }
.panel { display: none; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.panel.active { display: block; }
.form-group { margin-bottom: 15px; }
.form-group label { display: block; margin-bottom: 5px; font-weight: 500; }
.form-group input, .form-group select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
.btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; margin-right: 8px; }
.btn-primary { background: #007bff; color: #fff; }
.btn-danger { background: #dc3545; color: #fff; }
.btn-success { background: #28a745; color: #fff; }
.btn-secondary { background: #6c757d; color: #fff; }
table { width: 100%; border-collapse: collapse; margin-top: 15px; }
th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
th { background: #f8f9fa; }
tr:hover { background: #f5f5f5; }
.log { background: #1e1e1e; color: #0f0; padding: 15px; border-radius: 4px; height: 200px; overflow-y: auto; font-family: monospace; margin-top: 15px; }
.checkbox-group { max-height: 200px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; border-radius: 4px; }
.checkbox-group label { display: block; padding: 5px 0; }
.status-success { color: #28a745; }
.status-fail { color: #dc3545; }
.hint { color: #666; font-size: 12px; margin-top: 5px; }
.editor-container { border: 1px solid #ddd; border-radius: 4px; background: #fff; }
.editor-toolbar { display: flex; flex-wrap: wrap; gap: 2px; padding: 5px; border-bottom: 1px solid #ddd; background: #f8f9fa; }
.editor-toolbar button { padding: 4px 8px; border: 1px solid #ccc; background: #fff; cursor: pointer; border-radius: 3px; font-size: 12px; }
.editor-toolbar button:hover { background: #e9ecef; }
.editor-toolbar select { padding: 3px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px; }
.editor-content { min-height: 100px; padding: 10px; outline: none; }
</style>
</head>
<body>
<div class="container">
<h1>📧 邮件助手</h1>
<div class="tabs">
<button class="tab active" data-tab="send">绩效发送</button>
<button class="tab" data-tab="contacts">联系人管理</button>
<button class="tab" data-tab="cc">抄送配置</button>
<button class="tab" data-tab="smtp">邮件配置</button>
</div>

<div id="send" class="panel active">
<div style="background:#fff3cd;border:1px solid #ffc107;border-radius:4px;padding:10px 15px;margin-bottom:15px">
<strong>📋 文件命名规范：</strong><code style="background:#ffeeba;padding:2px 6px;border-radius:3px">{负责人} - {月份}月绩效考勤系数&名单.xlsx</code><br>
<span style="color:#856404;font-size:13px">示例：张三 - 3月绩效考勤系数&名单.xlsx</span>
</div>
<div class="form-group">
<label>文件夹路径</label>
<div style="display:flex;gap:10px">
<input type="text" id="folder" placeholder="输入文件夹完整路径，如 C:\\绩效文件 或 /Users/xxx/绩效文件" style="flex:1">
<button class="btn btn-secondary" id="chooseFolderBtn" onclick="chooseFolder()" style="display:none">选择</button>
</div>
</div>
<button class="btn btn-primary" onclick="scanFiles()">扫描文件</button>
<table id="fileTable"><thead><tr><th>文件名</th><th>负责人</th><th>月份</th><th>状态</th></tr></thead><tbody></tbody></table>
<button class="btn btn-success" onclick="sendEmails()" style="margin-top:15px">开始发送</button>
<div class="log" id="sendLog"></div>
</div>

<div id="contacts" class="panel">
<div style="display:flex;gap:20px">
<div style="flex:1">
<div class="form-group"><label>姓名</label><input type="text" id="cName"></div>
<div class="form-group"><label>邮箱</label><input type="email" id="cEmail"></div>
<input type="hidden" id="cId">
<button class="btn btn-primary" onclick="saveContact()">保存</button>
<button class="btn btn-secondary" onclick="clearContactForm()">清空</button>
</div>
<div style="flex:2">
<table id="contactTable"><thead><tr><th>ID</th><th>姓名</th><th>邮箱</th><th>操作</th></tr></thead><tbody></tbody></table>
</div>
</div>
</div>

<div id="cc" class="panel">
<div class="form-group">
<label>部门负责人</label>
<select id="ccOwner" onchange="loadCCMapping()"><option value="">选择负责人</option></select>
</div>
<div class="form-group">
<label>抄送人列表</label>
<div class="checkbox-group" id="ccList"></div>
</div>
<button class="btn btn-primary" onclick="saveCCMapping()">保存</button>
</div>

<div id="smtp" class="panel">
<div style="display:flex;gap:20px">
<div style="flex:1">
<h3 style="margin-bottom:15px">SMTP配置</h3>
<div class="form-group"><label>SMTP服务器</label><input type="text" id="smtpServer" placeholder="smtp.qq.com"></div>
<div class="form-group"><label>端口</label><input type="number" id="smtpPort" value="465"></div>
<div class="form-group"><label>发件人邮箱</label><input type="email" id="smtpEmail"></div>
<div class="form-group"><label>密码/授权码</label><input type="password" id="smtpPass"></div>
<button class="btn btn-primary" onclick="saveSMTP()">保存配置</button>
<button class="btn btn-secondary" onclick="testSMTP()">测试连接</button>
<div class="hint">常用: QQ邮箱 smtp.qq.com:465 | 163邮箱 smtp.163.com:465 | Gmail smtp.gmail.com:465</div>
</div>
<div style="flex:1">
<h3 style="margin-bottom:15px">邮件内容配置</h3>
<div class="form-group">
<label>正文模板 <span class="hint">可用变量: {owner} {month}</span></label>
<div class="editor-container">
<div class="editor-toolbar">
<button onclick="execCmd('bold')" title="加粗"><b>B</b></button>
<button onclick="execCmd('italic')" title="斜体"><i>I</i></button>
<button onclick="execCmd('underline')" title="下划线"><u>U</u></button>
<select onchange="execCmd('fontSize',this.value);this.selectedIndex=0">
<option value="">字号</option>
<option value="1">小</option>
<option value="3">中</option>
<option value="5">大</option>
<option value="7">超大</option>
</select>
<input type="color" onchange="execCmd('foreColor',this.value)" title="文字颜色" style="width:25px;height:22px;padding:0;border:1px solid #ccc">
<button onclick="execCmd('justifyLeft')" title="左对齐">≡</button>
<button onclick="execCmd('justifyCenter')" title="居中">≡</button>
<button onclick="execCmd('insertUnorderedList')" title="列表">•</button>
</div>
<div id="bodyTemplate" class="editor-content" contenteditable="true">@{owner} 这是{month}月的绩效数据结果，请查收。</div>
</div>
</div>
<div class="form-group">
<label>邮件签名</label>
<div class="editor-container">
<div class="editor-toolbar">
<button onclick="execCmd('bold','sig')" title="加粗"><b>B</b></button>
<button onclick="execCmd('italic','sig')" title="斜体"><i>I</i></button>
<button onclick="execCmd('underline','sig')" title="下划线"><u>U</u></button>
<select onchange="execCmd('fontSize',this.value,'sig');this.selectedIndex=0">
<option value="">字号</option>
<option value="1">小</option>
<option value="3">中</option>
<option value="5">大</option>
<option value="7">超大</option>
</select>
<input type="color" onchange="execCmd('foreColor',this.value,'sig')" title="文字颜色" style="width:25px;height:22px;padding:0;border:1px solid #ccc">
<button onclick="execCmd('justifyLeft','sig')" title="左对齐">≡</button>
<button onclick="execCmd('justifyCenter','sig')" title="居中">≡</button>
<button onclick="execCmd('insertUnorderedList','sig')" title="列表">•</button>
<button onclick="document.getElementById('imgUpload').click()" title="插入图片">🖼</button>
<input type="file" id="imgUpload" accept="image/*" style="display:none" onchange="insertImage(this)">
</div>
<div id="signatureEditor" class="editor-content" contenteditable="true"></div>
</div>
</div>
<button class="btn btn-primary" onclick="saveTemplate()">保存模板</button>
</div>
</div>
</div>

<script>
let scannedFiles = [];
let contacts = [];

document.querySelectorAll('.tab').forEach(tab => {
  tab.onclick = () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById(tab.dataset.tab).classList.add('active');
    if (tab.dataset.tab === 'contacts') loadContacts();
    if (tab.dataset.tab === 'cc') { loadContacts(); loadOwners(); }
    if (tab.dataset.tab === 'smtp') loadSMTP();
  };
});

async function api(path, data) {
  const opts = data ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) } : {};
  const res = await fetch(path, opts);
  return res.json();
}

let currentEditor = 'bodyTemplate';
function focusEditor(id) { currentEditor = id; }
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('bodyTemplate').addEventListener('focus', () => focusEditor('bodyTemplate'));
  document.getElementById('signatureEditor').addEventListener('focus', () => focusEditor('signatureEditor'));
});

function execCmd(cmd, valOrTarget, target) {
  let value = null;
  let editorId = currentEditor;
  if (valOrTarget === 'sig') {
    editorId = 'signatureEditor';
  } else if (target === 'sig') {
    editorId = 'signatureEditor';
    value = valOrTarget;
  } else if (valOrTarget) {
    value = valOrTarget;
  }
  document.getElementById(editorId).focus();
  document.execCommand(cmd, false, value);
}

function insertImage(input) {
  if (!input.files || !input.files[0]) return;
  const file = input.files[0];
  const reader = new FileReader();
  reader.onload = function(e) {
    const img = document.createElement('img');
    img.src = e.target.result;
    img.style.maxWidth = '200px';
    img.style.height = 'auto';
    const editor = document.getElementById('signatureEditor');
    editor.focus();
    const selection = window.getSelection();
    if (selection.rangeCount > 0) {
      const range = selection.getRangeAt(0);
      range.insertNode(img);
      range.setStartAfter(img);
      range.collapse(true);
      selection.removeAllRanges();
      selection.addRange(range);
    } else {
      editor.appendChild(img);
    }
  };
  reader.readAsDataURL(file);
  input.value = '';
}

async function checkFolderPicker() {
  const res = await api('/api/choose_folder');
  if (res.available) {
    document.getElementById('chooseFolderBtn').style.display = 'block';
    if (res.folder) {
      document.getElementById('folder').value = res.folder;
      scanFiles();
    }
  }
}

async function chooseFolder() {
  const res = await api('/api/choose_folder');
  if (res.folder) {
    document.getElementById('folder').value = res.folder;
    scanFiles();
  }
}

async function scanFiles() {
  const folder = document.getElementById('folder').value;
  if (!folder) return alert('请输入文件夹路径');
  scannedFiles = await api('/api/scan?folder=' + encodeURIComponent(folder));
  const tbody = document.querySelector('#fileTable tbody');
  tbody.innerHTML = scannedFiles.map(f => `<tr><td>${f.filename}</td><td>${f.owner||'-'}</td><td>${f.month||'-'}</td><td>${f.status}</td></tr>`).join('');
}

async function sendEmails() {
  if (!scannedFiles.length) return alert('请先扫描文件');
  const log = document.getElementById('sendLog');
  const tbody = document.querySelector('#fileTable tbody');
  log.innerHTML = '';
  addLog('开始发送...');
  
  for (let i = 0; i < scannedFiles.length; i++) {
    const f = scannedFiles[i];
    if (f.status === '解析失败') {
      addLog(`[跳过] ${f.filename}: 文件名格式不匹配`);
      continue;
    }
    const results = await api('/api/send', { files: [f] });
    if (results.length > 0) {
      const r = results[0];
      if (r.status === '成功') {
        addLog(`[成功] ${r.filename}`);
        scannedFiles[i].status = '已发送';
        tbody.rows[i].cells[3].textContent = '已发送';
        tbody.rows[i].cells[3].style.color = '#28a745';
      } else {
        addLog(`[失败] ${r.filename}: ${r.error || '未知错误'}`);
        scannedFiles[i].status = '发送失败';
        tbody.rows[i].cells[3].textContent = '发送失败';
        tbody.rows[i].cells[3].style.color = '#dc3545';
      }
    }
  }
  addLog('发送完成!');
}

function addLog(msg) {
  const log = document.getElementById('sendLog');
  log.innerHTML += msg + '<br>';
  log.scrollTop = log.scrollHeight;
}

async function loadContacts() {
  contacts = await api('/api/contacts');
  const tbody = document.querySelector('#contactTable tbody');
  tbody.innerHTML = contacts.map(c => `<tr><td>${c.id}</td><td>${c.name}</td><td>${c.email}</td><td><button class="btn btn-secondary" onclick="editContact(${c.id})">编辑</button><button class="btn btn-danger" onclick="deleteContact(${c.id})">删除</button></td></tr>`).join('');
  
  const ccList = document.getElementById('ccList');
  if (ccList) ccList.innerHTML = contacts.map(c => `<label><input type="checkbox" value="${c.id}"> ${c.name} (${c.email})</label>`).join('');
}

function editContact(id) {
  const c = contacts.find(x => x.id === id);
  document.getElementById('cId').value = c.id;
  document.getElementById('cName').value = c.name;
  document.getElementById('cEmail').value = c.email;
}

async function saveContact() {
  const id = document.getElementById('cId').value;
  const name = document.getElementById('cName').value;
  const email = document.getElementById('cEmail').value;
  if (!name || !email) return alert('请填写姓名和邮箱');
  try {
    if (id) await api('/api/contacts/update', { id: parseInt(id), name, email });
    else await api('/api/contacts', { name, email });
    clearContactForm();
    loadContacts();
  } catch (e) { alert('保存失败: ' + e.message); }
}

async function deleteContact(id) {
  if (!confirm('确定删除?')) return;
  await api('/api/contacts/delete', { id });
  loadContacts();
}

function clearContactForm() {
  document.getElementById('cId').value = '';
  document.getElementById('cName').value = '';
  document.getElementById('cEmail').value = '';
}

function loadOwners() {
  const select = document.getElementById('ccOwner');
  const current = select.value;
  select.innerHTML = '<option value="">选择负责人</option>' + contacts.map(c => `<option value="${c.name}">${c.name}</option>`).join('');
  if (current) select.value = current;
}

async function loadCCMapping() {
  const owner = document.getElementById('ccOwner').value;
  if (!owner) return;
  const data = await api('/api/cc_mapping?owner=' + encodeURIComponent(owner));
  document.querySelectorAll('#ccList input').forEach(cb => {
    cb.checked = data.cc_ids.includes(parseInt(cb.value));
  });
}

async function saveCCMapping() {
  const owner = document.getElementById('ccOwner').value;
  if (!owner) return alert('请选择负责人');
  const cc_ids = Array.from(document.querySelectorAll('#ccList input:checked')).map(cb => parseInt(cb.value));
  await api('/api/cc_mapping', { owner, cc_ids });
  alert('保存成功');
}

async function loadSMTP() {
  const data = await api('/api/smtp');
  if (data.smtp_server) {
    document.getElementById('smtpServer').value = data.smtp_server;
    document.getElementById('smtpPort').value = data.port;
    document.getElementById('smtpEmail').value = data.sender_email;
    document.getElementById('smtpPass').value = data.password;
  }
  const tpl = await api('/api/template');
  if (tpl.body_template) {
    document.getElementById('bodyTemplate').innerHTML = tpl.body_template;
  }
  if (tpl.signature) {
    document.getElementById('signatureEditor').innerHTML = tpl.signature;
  }
}

async function saveTemplate() {
  const data = {
    body_template: document.getElementById('bodyTemplate').innerHTML,
    signature: document.getElementById('signatureEditor').innerHTML
  };
  await api('/api/template', data);
  alert('模板已保存');
}

async function saveSMTP() {
  const data = { smtp_server: document.getElementById('smtpServer').value, port: document.getElementById('smtpPort').value, sender_email: document.getElementById('smtpEmail').value, password: document.getElementById('smtpPass').value };
  await api('/api/smtp', data);
  alert('配置已保存');
}

async function testSMTP() {
  const data = { smtp_server: document.getElementById('smtpServer').value, port: document.getElementById('smtpPort').value, sender_email: document.getElementById('smtpEmail').value, password: document.getElementById('smtpPass').value };
  const res = await api('/api/smtp/test', data);
  alert(res.success ? '连接成功!' : '连接失败: ' + res.error);
}

loadContacts();
checkFolderPicker();
</script>
</body>
</html>
'''


def main():
    server = HTTPServer((HOST, PORT), RequestHandler)
    url = f"http://{HOST}:{PORT}"
    print(f"邮件助手已启动: {url}")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
        server.shutdown()


if __name__ == "__main__":
    main()
