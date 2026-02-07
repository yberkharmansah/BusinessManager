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
        self.root.configure(bg="#f5f7fb")
        self.setup_styles()
        
        # Veritabanını başlat
        initialize_database()
        
        # Aktif şube
        self.current_branch = None
        
        # Ana çerçeve
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Şube seçim ekranını göster
        self.show_branch_selection()
    
    def show_branch_selection(self):
        """Şube seçim ekranını gösterir"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # Başlık
        hero_frame = ttk.Frame(self.main_frame)
        hero_frame.pack(fill=tk.X, padx=40, pady=(30, 20))
        ttk.Label(
            hero_frame,
            text="🏪 İşletme Yönetim Sistemi",
            style="Hero.TLabel"
        ).pack(anchor="w")
        ttk.Label(
            hero_frame,
            text="Şubenizi seçin veya yeni şube oluşturarak yönetimi başlatın.",
            style="Subtitle.TLabel"
        ).pack(anchor="w", pady=(8, 0))
        
        # Şube seçim butonu
        action_frame = ttk.Frame(self.main_frame)
        action_frame.pack(fill=tk.X, padx=40, pady=(0, 20))
        ttk.Button(
            action_frame,
            text="📍 Şube Seç / Oluştur",
            command=self.select_branch,
            style="Primary.TButton"
        ).pack(anchor="w")
        
        # Mevcut şubeleri listele
        branches = get_all_branches()
        if branches:
            ttk.Label(
                self.main_frame,
                text="Mevcut Şubeler",
                style="Section.TLabel"
            ).pack(anchor="w", padx=40, pady=(10, 10))
            
            for branch in branches:
                branch_frame = ttk.Frame(self.main_frame, style="Card.TFrame")
                branch_frame.pack(fill=tk.X, padx=40, pady=6)
                
                ttk.Label(
                    branch_frame,
                    text=f"📍 {branch['name']}",
                    style="Body.TLabel"
                ).pack(side=tk.LEFT, padx=12, pady=12)
                
                ttk.Button(
                    branch_frame,
                    text="Seç",
                    command=lambda b=branch: self.set_branch(b),
                    style="Secondary.TButton"
                ).pack(side=tk.RIGHT, padx=12, pady=10)
    
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
        top_bar = ttk.Frame(self.main_frame, style="Topbar.TFrame")
        top_bar.pack(fill=tk.X)
        
        # Şube bilgisi
        branch_label = ttk.Label(
            top_bar,
            text=f"🏪 Aktif Şube: {self.current_branch['name']}",
            style="Topbar.TLabel"
        )
        branch_label.pack(side=tk.LEFT, padx=20, pady=14)
        
        # Geri dönüş butonu
        ttk.Button(
            top_bar,
            text="Şube Değiştir",
            command=self.show_branch_selection,
            style="Danger.TButton"
        ).pack(side=tk.RIGHT, padx=20, pady=10)
        
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

    def setup_styles(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background="#f5f7fb")
        style.configure("Card.TFrame", background="#ffffff", relief="solid", borderwidth=1)
        style.configure("Topbar.TFrame", background="#0f172a")
        style.configure("TLabel", background="#f5f7fb", foreground="#0f172a", font=("Segoe UI", 10))
        style.configure("Hero.TLabel", font=("Segoe UI Semibold", 24), foreground="#0f172a")
        style.configure("Subtitle.TLabel", font=("Segoe UI", 11), foreground="#64748b")
        style.configure("Section.TLabel", font=("Segoe UI Semibold", 12), foreground="#0f172a")
        style.configure("Body.TLabel", font=("Segoe UI", 11), foreground="#0f172a", background="#ffffff")
        style.configure("Topbar.TLabel", background="#0f172a", foreground="#ffffff", font=("Segoe UI Semibold", 11))

        style.configure("Primary.TButton", font=("Segoe UI Semibold", 10), padding=(14, 8),
                        background="#2563eb", foreground="#ffffff")
        style.map("Primary.TButton", background=[("active", "#1d4ed8")])

        style.configure("Secondary.TButton", font=("Segoe UI Semibold", 10), padding=(12, 6),
                        background="#e2e8f0", foreground="#0f172a")
        style.map("Secondary.TButton", background=[("active", "#cbd5f5")])

        style.configure("Danger.TButton", font=("Segoe UI Semibold", 10), padding=(12, 6),
                        background="#ef4444", foreground="#ffffff")
        style.map("Danger.TButton", background=[("active", "#dc2626")])

        style.configure("TNotebook", background="#f5f7fb", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(12, 8), font=("Segoe UI Semibold", 10))
        

def main():
    root = tk.Tk()
    app = BusinessManagerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
