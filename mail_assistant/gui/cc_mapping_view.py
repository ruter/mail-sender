import tkinter as tk
from tkinter import ttk, messagebox
from models.contact import ContactRepository
from models.cc_mapping import CCMappingRepository


class CCMappingView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._create_widgets()
        self._load_data()
    
    def _create_widgets(self):
        left_frame = ttk.LabelFrame(self, text="部门负责人")
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        ttk.Label(left_frame, text="选择负责人:").pack(padx=5, pady=5)
        
        self.owner_var = tk.StringVar()
        self.owner_combo = ttk.Combobox(left_frame, textvariable=self.owner_var, width=20, state="readonly")
        self.owner_combo.pack(padx=5, pady=5)
        self.owner_combo.bind("<<ComboboxSelected>>", self._on_owner_select)
        
        ttk.Separator(left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Label(left_frame, text="新增负责人:").pack(padx=5, pady=5)
        self.new_owner_var = tk.StringVar()
        self.new_owner_entry = ttk.Entry(left_frame, textvariable=self.new_owner_var, width=20)
        self.new_owner_entry.pack(padx=5, pady=5)
        ttk.Button(left_frame, text="添加", command=self._add_owner).pack(padx=5, pady=5)
        
        right_frame = ttk.LabelFrame(self, text="抄送人列表")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.contacts_frame = ttk.Frame(right_frame)
        self.contacts_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        canvas = tk.Canvas(self.contacts_frame)
        scrollbar = ttk.Scrollbar(self.contacts_frame, orient=tk.VERTICAL, command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas = canvas
        self.checkboxes = {}
        
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="保存", command=self._save_mapping).pack(side=tk.LEFT, padx=5)
    
    def _load_data(self):
        contacts = ContactRepository.get_all()
        self.all_contacts = contacts
        self.owner_combo['values'] = [c.name for c in contacts]
        
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.checkboxes.clear()
        
        for contact in contacts:
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(self.scrollable_frame, text=f"{contact.name} ({contact.email})", variable=var)
            cb.pack(anchor=tk.W, padx=5, pady=2)
            self.checkboxes[contact.id] = var
    
    def _on_owner_select(self, event=None):
        owner_name = self.owner_var.get()
        if not owner_name:
            return
        
        cc_ids = CCMappingRepository.get_cc_contact_ids(owner_name)
        
        for contact_id, var in self.checkboxes.items():
            var.set(contact_id in cc_ids)
    
    def _add_owner(self):
        new_owner = self.new_owner_var.get().strip()
        if not new_owner:
            messagebox.showwarning("警告", "请输入负责人姓名")
            return
        
        current_values = list(self.owner_combo['values'])
        if new_owner not in current_values:
            current_values.append(new_owner)
            self.owner_combo['values'] = current_values
        
        self.owner_var.set(new_owner)
        self.new_owner_var.set("")
        self._on_owner_select()
    
    def _save_mapping(self):
        owner_name = self.owner_var.get()
        if not owner_name:
            messagebox.showwarning("警告", "请先选择部门负责人")
            return
        
        selected_ids = [cid for cid, var in self.checkboxes.items() if var.get()]
        
        try:
            CCMappingRepository.set_cc_contacts(owner_name, selected_ids)
            messagebox.showinfo("成功", "抄送关系已保存")
        except Exception as e:
            messagebox.showerror("错误", str(e))
    
    def refresh(self):
        self._load_data()
