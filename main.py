# main.py
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Proje dizinini Python path'e ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import initialize_database, get_all_branches
from modules.branch_manager import BranchManagerDialog
from modules.stock_tab import StockTab

class BusinessManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🏪 İşletme Yönetim Sistemi")
        self.root.geometry("1200x700")
        
        # Veritabanını başlat
        initialize_database()
        
        # Aktif şube
        self.current_branch = None
        
        # Ana çerçeve
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Şube seçim ekranını göster
        self.show_branch_selection()
    
    def show_branch_selection(self):
        """Şube seçim ekranını gösterir"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # Başlık
        title_label = tk.Label(
            self.main_frame, 
            text="🏪 İşletme Yönetim Sistemi", 
            font=("Arial", 24, "bold")
        )
        title_label.pack(pady=30)
        
        # Şube seçim butonu
        select_btn = tk.Button(
            self.main_frame,
            text="📍 Şube Seç / Oluştur",
            command=self.select_branch,
            font=("Arial", 14),
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=10
        )
        select_btn.pack(pady=20)
        
        # Mevcut şubeleri listele
        branches = get_all_branches()
        if branches:
            tk.Label(
                self.main_frame,
                text="Mevcut Şubeler:",
                font=("Arial", 12, "bold")
            ).pack(pady=(30, 10))
            
            for branch in branches:
                branch_frame = tk.Frame(self.main_frame)
                branch_frame.pack(fill=tk.X, padx=50, pady=5)
                
                tk.Label(
                    branch_frame,
                    text=f"📍 {branch['name']}",
                    font=("Arial", 11)
                ).pack(side=tk.LEFT)
                
                tk.Button(
                    branch_frame,
                    text="Seç",
                    command=lambda b=branch: self.set_branch(b),
                    bg="#2196F3",
                    fg="white"
                ).pack(side=tk.RIGHT)
    
    def select_branch(self):
        """Şube seçim/yaratma penceresini açar"""
        dialog = BranchManagerDialog(self.root, self.set_branch)
    
    def set_branch(self, branch_data):
        """Seçilen şubeyi ayarlar ve ana ekranı yükler"""
        self.current_branch = branch_data
        messagebox.showinfo(
            "Şube Seçildi", 
            f"'{branch_data['name']}' şubesi aktif hale getirildi."
        )
        self.load_main_interface()
    
    def load_main_interface(self):
        """Ana tab arayüzünü yükler"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # Üst bar
        top_bar = tk.Frame(self.main_frame, bg="#2c3e50", height=50)
        top_bar.pack(fill=tk.X)
        
        # Şube bilgisi
        branch_label = tk.Label(
            top_bar,
            text=f"🏪 Aktif Şube: {self.current_branch['name']}",
            bg="#2c3e50",
            fg="white",
            font=("Arial", 12, "bold")
        )
        branch_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Geri dönüş butonu
        tk.Button(
            top_bar,
            text="Şube Değiştir",
            command=self.show_branch_selection,
            bg="#e74c3c",
            fg="white"
        ).pack(side=tk.RIGHT, padx=20)
        
        # Tab kontrolü
        self.tab_control = ttk.Notebook(self.main_frame)
        self.tab_control.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab'ları oluştur
        self.stock_tab = tk.Frame(self.tab_control)
        self.supplier_tab = tk.Frame(self.tab_control)
        self.finance_tab = tk.Frame(self.tab_control)
        
        self.tab_control.add(self.stock_tab, text="📦 Stok Takibi")
        self.tab_control.add(self.supplier_tab, text="🤝 Toptancı Takibi")
        self.tab_control.add(self.finance_tab, text="💰 Gelir/Gider")
        
        # Modülleri yükle
        self.stock_module = StockTab(self.stock_tab, self.current_branch['id'])
        from modules.supplier_tab import SupplierTab
        self.supplier_module = SupplierTab(self.supplier_tab, self.current_branch['id'])
        from modules.finance_tab import FinanceTab
        self.finance_module = FinanceTab(self.finance_tab, self.current_branch['id'])
        

def main():
    root = tk.Tk()
    app = BusinessManagerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
