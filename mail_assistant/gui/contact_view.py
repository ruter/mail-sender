import tkinter as tk
from tkinter import ttk, messagebox
from models.contact import Contact, ContactRepository


class ContactView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._create_widgets()
        self._load_contacts()
    
    def _create_widgets(self):
        form_frame = ttk.LabelFrame(self, text="联系人信息")
        form_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(form_frame, text="姓名:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(form_frame, textvariable=self.name_var, width=30)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="邮箱:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.email_var = tk.StringVar()
        self.email_entry = ttk.Entry(form_frame, textvariable=self.email_var, width=30)
        self.email_entry.grid(row=1, column=1, padx=5, pady=5)
        
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="新增", command=self._add_contact).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="更新", command=self._update_contact).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="删除", command=self._delete_contact).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="清空", command=self._clear_form).pack(side=tk.LEFT, padx=5)
        
        list_frame = ttk.LabelFrame(self, text="联系人列表")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("id", "name", "email")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="姓名")
        self.tree.heading("email", text="邮箱")
        
        self.tree.column("id", width=50)
        self.tree.column("name", width=150)
        self.tree.column("email", width=250)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        
        self.selected_id = None
    
    def _load_contacts(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        contacts = ContactRepository.get_all()
        for c in contacts:
            self.tree.insert("", tk.END, values=(c.id, c.name, c.email))
    
    def _on_select(self, event):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            self.selected_id = values[0]
            self.name_var.set(values[1])
            self.email_var.set(values[2])
    
    def _clear_form(self):
        self.selected_id = None
        self.name_var.set("")
        self.email_var.set("")
        for item in self.tree.selection():
            self.tree.selection_remove(item)
    
    def _add_contact(self):
        name = self.name_var.get().strip()
        email = self.email_var.get().strip()
        
        if not name or not email:
            messagebox.showwarning("警告", "请填写姓名和邮箱")
            return
        
        try:
            ContactRepository.create(name, email)
            self._load_contacts()
            self._clear_form()
            messagebox.showinfo("成功", "联系人已添加")
        except Exception as e:
            messagebox.showerror("错误", str(e))
    
    def _update_contact(self):
        if not self.selected_id:
            messagebox.showwarning("警告", "请先选择要更新的联系人")
            return
        
        name = self.name_var.get().strip()
        email = self.email_var.get().strip()
        
        if not name or not email:
            messagebox.showwarning("警告", "请填写姓名和邮箱")
            return
        
        try:
            ContactRepository.update(self.selected_id, name, email)
            self._load_contacts()
            self._clear_form()
            messagebox.showinfo("成功", "联系人已更新")
        except Exception as e:
            messagebox.showerror("错误", str(e))
    
    def _delete_contact(self):
        if not self.selected_id:
            messagebox.showwarning("警告", "请先选择要删除的联系人")
            return
        
        if messagebox.askyesno("确认", "确定要删除这个联系人吗?"):
            try:
                ContactRepository.delete(self.selected_id)
                self._load_contacts()
                self._clear_form()
                messagebox.showinfo("成功", "联系人已删除")
            except Exception as e:
                messagebox.showerror("错误", str(e))
