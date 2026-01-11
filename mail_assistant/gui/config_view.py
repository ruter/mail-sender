import tkinter as tk
from tkinter import ttk, messagebox
from services.mail_sender import MailSender, SMTPConfig


class ConfigView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._create_widgets()
        self._load_config()
    
    def _create_widgets(self):
        form_frame = ttk.LabelFrame(self, text="SMTP配置")
        form_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(form_frame, text="SMTP服务器:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.server_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.server_var, width=40).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="端口:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.port_var = tk.StringVar(value="465")
        ttk.Entry(form_frame, textvariable=self.port_var, width=10).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(form_frame, text="发件人邮箱:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.email_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.email_var, width=40).grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="密码/授权码:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.password_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.password_var, width=40, show="*").grid(row=3, column=1, padx=5, pady=5)
        
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=15)
        
        ttk.Button(btn_frame, text="保存配置", command=self._save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="测试连接", command=self._test_connection).pack(side=tk.LEFT, padx=5)
        
        hint_frame = ttk.LabelFrame(self, text="常用SMTP配置")
        hint_frame.pack(fill=tk.X, padx=10, pady=10)
        
        hints = [
            ("QQ邮箱", "smtp.qq.com", "465"),
            ("163邮箱", "smtp.163.com", "465"),
            ("Gmail", "smtp.gmail.com", "465"),
            ("Outlook", "smtp.office365.com", "587"),
        ]
        
        for i, (name, server, port) in enumerate(hints):
            ttk.Label(hint_frame, text=f"{name}: {server}:{port}").grid(row=i, column=0, padx=10, pady=2, sticky=tk.W)
    
    def _load_config(self):
        config = MailSender.get_config()
        if config:
            self.server_var.set(config.smtp_server)
            self.port_var.set(str(config.port))
            self.email_var.set(config.sender_email)
            self.password_var.set(config.password)
    
    def _get_config_from_form(self) -> SMTPConfig:
        return SMTPConfig(
            smtp_server=self.server_var.get().strip(),
            port=int(self.port_var.get().strip() or "465"),
            sender_email=self.email_var.get().strip(),
            password=self.password_var.get()
        )
    
    def _save_config(self):
        try:
            config = self._get_config_from_form()
            if not config.smtp_server or not config.sender_email or not config.password:
                messagebox.showwarning("警告", "请填写完整的配置信息")
                return
            
            MailSender.save_config(config)
            messagebox.showinfo("成功", "配置已保存")
        except Exception as e:
            messagebox.showerror("错误", str(e))
    
    def _test_connection(self):
        try:
            config = self._get_config_from_form()
            if not config.smtp_server or not config.sender_email or not config.password:
                messagebox.showwarning("警告", "请填写完整的配置信息")
                return
            
            success, error = MailSender.test_connection(config)
            if success:
                messagebox.showinfo("成功", "SMTP连接测试成功!")
            else:
                messagebox.showerror("失败", f"连接失败: {error}")
        except Exception as e:
            messagebox.showerror("错误", str(e))
