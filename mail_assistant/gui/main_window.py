import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from typing import List
from services.file_parser import FileParser, ParsedFile
from services.task_service import TaskService
from models.recipient_mapping import RecipientMappingRepository


class MainWindow(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parsed_files: List[ParsedFile] = []
        self._create_widgets()
    
    def _create_widgets(self):
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(top_frame, text="分类:").pack(side=tk.LEFT)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(top_frame, textvariable=self.category_var, width=15, state="readonly")
        self.category_combo.pack(side=tk.LEFT, padx=5)
        self._load_categories()
        
        ttk.Label(top_frame, text="文件夹:").pack(side=tk.LEFT, padx=(10, 0))
        self.folder_var = tk.StringVar()
        self.folder_entry = ttk.Entry(top_frame, textvariable=self.folder_var, width=40)
        self.folder_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(top_frame, text="选择文件夹", command=self._select_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="扫描", command=self._scan_files).pack(side=tk.LEFT, padx=5)
        
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ("filename", "owner", "month", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        self.tree.heading("filename", text="文件名")
        self.tree.heading("owner", text="负责人")
        self.tree.heading("month", text="月份")
        self.tree.heading("status", text="状态")
        
        self.tree.column("filename", width=300)
        self.tree.column("owner", width=100)
        self.tree.column("month", width=60)
        self.tree.column("status", width=100)
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.send_btn = ttk.Button(btn_frame, text="开始发送", command=self._start_send)
        self.send_btn.pack(side=tk.LEFT)
        
        log_frame = ttk.LabelFrame(self, text="发送日志")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, height=10, state=tk.DISABLED)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _load_categories(self):
        categories = RecipientMappingRepository.get_all_categories()
        self.category_combo['values'] = categories
        if categories:
            self.category_combo.current(0)
    
    def _select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_var.set(folder)
    
    def _scan_files(self):
        folder = self.folder_var.get()
        if not folder:
            messagebox.showwarning("警告", "请先选择文件夹")
            return
        
        self.parsed_files = FileParser.scan_directory(folder)
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not self.parsed_files:
            messagebox.showinfo("提示", "目录为空或没有找到xlsx文件")
            return
        
        for pf in self.parsed_files:
            self.tree.insert("", tk.END, values=(
                pf.filename,
                pf.owner or "-",
                pf.month or "-",
                pf.status
            ))
    
    def _log(self, message: str):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
    
    def _start_send(self):
        category = self.category_var.get()
        if not category:
            messagebox.showwarning("警告", "请先选择分类")
            return
        
        if not self.parsed_files:
            messagebox.showwarning("警告", "请先扫描文件")
            return
        
        valid_files = [pf for pf in self.parsed_files if pf.status != "解析失败"]
        if not valid_files:
            messagebox.showwarning("警告", "没有可发送的文件")
            return
        
        self.send_btn.configure(state=tk.DISABLED)
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)
        
        def send_task():
            def callback(msg):
                self.after(0, lambda: self._log(msg))
            
            TaskService.process_files(self.parsed_files, category, callback)
            self.after(0, lambda: self.send_btn.configure(state=tk.NORMAL))
            self.after(0, lambda: self._log("发送完成!"))
        
        threading.Thread(target=send_task, daemon=True).start()
    
    def refresh(self):
        self._load_categories()
