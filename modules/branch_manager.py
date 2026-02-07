import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import create_branch, get_all_branches

class BranchManagerDialog:
    def __init__(self, parent, callback):
        self.parent = parent
        self.callback = callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Şube Yönetimi")
        self.dialog.geometry("500x400")
        self.dialog.configure(bg="#f5f7fb")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.create_widgets()
    
    def create_widgets(self):
        # Üst çerçeve - Yeni şube ekleme
        add_frame = ttk.LabelFrame(self.dialog, text="Yeni Şube Oluştur", padding=12)
        add_frame.pack(fill=tk.X, padx=12, pady=12)
        
        ttk.Label(add_frame, text="Şube Adı *:").grid(row=0, column=0, sticky="w", pady=6)
        self.name_entry = ttk.Entry(add_frame, width=30)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(add_frame, text="Adres:").grid(row=1, column=0, sticky="w", pady=6)
        self.address_entry = tk.Text(add_frame, width=30, height=3, relief="solid", borderwidth=1)
        self.address_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Button(
            add_frame,
            text="➕ Şube Oluştur",
            command=self.create_new_branch
        ).grid(row=2, columnspan=2, pady=10)
        
        # Alt çerçeve - Mevcut şubeler
        list_frame = ttk.LabelFrame(self.dialog, text="Mevcut Şubeler", padding=12)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        
        # Scrollbar ile liste
        tree_scroll = tk.Scrollbar(list_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree = ttk.Treeview(
            list_frame,
            columns=("ID", "Name", "Date"),
            show="headings",
            height=6,
            yscrollcommand=tree_scroll.set
        )
        
        self.tree.heading("ID", text="ID")
        self.tree.heading("Name", text="Şube Adı")
        self.tree.heading("Date", text="Oluşturulma Tarihi")
        
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Name", width=200)
        self.tree.column("Date", width=150)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.tree.yview)
        
        # Treeview'e tıklama olayı
        self.tree.bind("<Double-1>", self.on_branch_select)
        self.tree.bind("<Return>", self.on_branch_select)
        
        # Seç butonu
        ttk.Button(
            list_frame,
            text="✅ Şubeyi Seç",
            command=self.select_branch
        ).pack(fill=tk.X, pady=5)
        
        # Şubeleri yükle
        self.load_branches()
    
    def create_new_branch(self):
        """Yeni şube oluşturur"""
        name = self.name_entry.get().strip()
        address = self.address_entry.get("1.0", tk.END).strip()
        
        if not name:
            messagebox.showwarning("Eksik Bilgi", "Şube adı zorunludur!")
            return
        
        branch_id = create_branch(name, address)
        if branch_id:
            self.name_entry.delete(0, tk.END)
            self.address_entry.delete("1.0", tk.END)
            self.load_branches()
    
    def load_branches(self):
        """Mevcut şubeleri listeye yükler"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        branches = get_all_branches()
        for branch in branches:
            self.tree.insert("", tk.END, values=(
                branch['id'],
                branch['name'],
                branch['created_date']
            ))
    
    def on_branch_select(self, event):
        """Treeview'de çift tıklama/Enter olayı"""
        self.select_branch()
    
    def select_branch(self):
        """Seçili şubeyi ana uygulamaya gönderir"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Seçim Yok", "Lütfen bir şube seçin!")
            return
        
        branch_data = {
            'id': self.tree.item(selection[0])['values'][0],
            'name': self.tree.item(selection[0])['values'][1],
        }
        
        self.callback(branch_data)
        self.dialog.destroy()
