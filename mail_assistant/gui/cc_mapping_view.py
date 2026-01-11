import tkinter as tk
from tkinter import ttk, messagebox
from models.contact import ContactRepository
from models.recipient_mapping import RecipientMappingRepository


class CCMappingView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.all_contacts = []
        self._create_widgets()
        self._load_data()
    
    def _create_widgets(self):
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(top_frame, text="新增映射", command=self._add_mapping).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="编辑", command=self._edit_mapping).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="删除", command=self._delete_mapping).pack(side=tk.LEFT, padx=5)
        
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ("category", "recipient", "cc_contacts")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        self.tree.heading("category", text="分类")
        self.tree.heading("recipient", text="收件人")
        self.tree.heading("cc_contacts", text="抄送人")
        
        self.tree.column("category", width=150)
        self.tree.column("recipient", width=200)
        self.tree.column("cc_contacts", width=350)
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _load_data(self):
        self.all_contacts = ContactRepository.get_all()
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        mappings = RecipientMappingRepository.get_all()
        for mapping in mappings:
            recipient_text = f"{mapping.recipient.name} ({mapping.recipient.email})"
            cc_text = ", ".join([f"{c.name}" for c in mapping.cc_contacts])
            self.tree.insert("", tk.END, iid=str(mapping.id), values=(
                mapping.category,
                recipient_text,
                cc_text or "-"
            ))
    
    def _add_mapping(self):
        if not self.all_contacts:
            messagebox.showwarning("警告", "请先添加联系人")
            return
        MappingDialog(self, "新增映射", self.all_contacts, self._on_mapping_saved)
    
    def _edit_mapping(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要编辑的映射")
            return
        
        mapping_id = int(selection[0])
        mapping = RecipientMappingRepository.get_by_id(mapping_id)
        if mapping:
            MappingDialog(self, "编辑映射", self.all_contacts, self._on_mapping_saved, mapping)
    
    def _delete_mapping(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的映射")
            return
        
        if messagebox.askyesno("确认", "确定要删除选中的映射吗?"):
            mapping_id = int(selection[0])
            RecipientMappingRepository.delete(mapping_id)
            self._load_data()
    
    def _on_mapping_saved(self):
        self._load_data()
    
    def refresh(self):
        self._load_data()


class MappingDialog(tk.Toplevel):
    def __init__(self, parent, title, contacts, on_save, mapping=None):
        super().__init__(parent)
        self.title(title)
        self.contacts = contacts
        self.on_save = on_save
        self.mapping = mapping
        self.cc_vars = {}
        
        self.geometry("500x450")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        
        if mapping:
            self._load_mapping()
    
    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="分类:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.category_var = tk.StringVar()
        self.category_entry = ttk.Entry(main_frame, textvariable=self.category_var, width=40)
        self.category_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(main_frame, text="收件人:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.recipient_var = tk.StringVar()
        self.recipient_combo = ttk.Combobox(main_frame, textvariable=self.recipient_var, width=37, state="readonly")
        self.recipient_combo['values'] = [f"{c.name} ({c.email})" for c in self.contacts]
        self.recipient_combo.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(main_frame, text="抄送人:").grid(row=2, column=0, sticky=tk.NW, pady=5)
        
        cc_frame = ttk.Frame(main_frame)
        cc_frame.grid(row=2, column=1, sticky=tk.NSEW, pady=5)
        
        canvas = tk.Canvas(cc_frame, height=250, width=300)
        scrollbar = ttk.Scrollbar(cc_frame, orient=tk.VERTICAL, command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        for contact in self.contacts:
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(self.scrollable_frame, text=f"{contact.name} ({contact.email})", variable=var)
            cb.pack(anchor=tk.W, padx=5, pady=2)
            self.cc_vars[contact.id] = var
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=15)
        
        ttk.Button(btn_frame, text="保存", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy).pack(side=tk.LEFT, padx=5)
    
    def _load_mapping(self):
        self.category_var.set(self.mapping.category)
        
        for i, contact in enumerate(self.contacts):
            if contact.id == self.mapping.recipient.id:
                self.recipient_combo.current(i)
                break
        
        cc_ids = [c.id for c in self.mapping.cc_contacts]
        for contact_id, var in self.cc_vars.items():
            var.set(contact_id in cc_ids)
    
    def _save(self):
        category = self.category_var.get().strip()
        if not category:
            messagebox.showwarning("警告", "请输入分类名称")
            return
        
        recipient_idx = self.recipient_combo.current()
        if recipient_idx < 0:
            messagebox.showwarning("警告", "请选择收件人")
            return
        
        recipient_id = self.contacts[recipient_idx].id
        cc_ids = [cid for cid, var in self.cc_vars.items() if var.get()]
        
        try:
            if self.mapping:
                RecipientMappingRepository.update(self.mapping.id, category, recipient_id, cc_ids)
            else:
                RecipientMappingRepository.create(category, recipient_id, cc_ids)
            
            self.on_save()
            self.destroy()
            messagebox.showinfo("成功", "映射已保存")
        except Exception as e:
            messagebox.showerror("错误", str(e))
