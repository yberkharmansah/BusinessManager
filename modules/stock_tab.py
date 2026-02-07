# modules/stock_tab.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import (
    get_all_products, add_product, update_product_quantity,
    get_low_stock_products, update_product_info, fetch_one, delete_product
)

from modules.stock_reports import StockReportsDialog

class StockTab:
    def __init__(self, parent, branch_id):
        self.parent = parent
        self.branch_id = branch_id
        
        # Sıralama için değişkenler
        self.sort_column = None
        self.sort_reverse = False
        
        self.create_widgets()
        self.load_products()
    
    def create_widgets(self):
        # Üst çerçeve - Kontroller
        top_frame = ttk.Frame(self.parent)
        top_frame.pack(fill=tk.X, padx=16, pady=12)
        
        # Arama
        ttk.Label(top_frame, text="🔍 Ara:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.on_search_change)
        self.search_entry = ttk.Entry(top_frame, textvariable=self.search_var, width=25)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        
        # Düşük stok filtresi
        self.low_stock_var = tk.BooleanVar()
        ttk.Checkbutton(
            top_frame,
            text="Düşük Stok",
            variable=self.low_stock_var,
            command=self.load_products
        ).pack(side=tk.LEFT, padx=10)

        ttk.Button(
            top_frame,
            text="📈 Stok Ekle",
            command=self.increase_stock
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            top_frame,
            text="📉 Stok Azalt",
            command=self.decrease_stock
        ).pack(side=tk.LEFT, padx=5)
        
        # Butonlar
        ttk.Button(
            top_frame,
            text="➕ Ürün Ekle",
            command=self.add_product_dialog
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            top_frame,
            text="📋 Stok Raporları",
            command=self.open_stock_reports
        ).pack(side=tk.RIGHT, padx=5)
        
        # Orta çerçeve - Ürün listesi
        list_frame = ttk.Frame(self.parent)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)
        
        # Scrollbar'lar
        y_scroll = tk.Scrollbar(list_frame)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        x_scroll = tk.Scrollbar(list_frame, orient=tk.HORIZONTAL)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Treeview
        self.tree = ttk.Treeview(
            list_frame,
            columns=("ID", "Name", "Barcode", "Quantity", "MinStock", "Price", "Created"),
            show="headings",
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set
        )
        
        # Kolon başlıkları - SIRALAMA EKLENDİ
        columns_config = [
            ("ID", "ID", 50, "center", "ID"),
            ("Name", "Ürün Adı", 200, "w", "isim"),
            ("Barcode", "Barkod", 120, "center", "barkod"),
            ("Quantity", "Miktar", 80, "center", "miktar"),
            ("MinStock", "Min Stok", 80, "center", "minStok"),
            ("Price", "Birim Fiyat", 100, "e", "fiyat"),
            ("Created", "Eklenme Tarihi", 140, "center", "tarih"),
        ]
        
        for col_id, header_text, width, anchor, sort_key in columns_config:
            self.tree.heading(
                col_id, 
                text=header_text, 
                command=lambda c=col_id: self.sort_by_column(c)
            )
            self.tree.column(col_id, width=width, anchor=anchor)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        y_scroll.config(command=self.tree.yview)
        x_scroll.config(command=self.tree.xview)
        
        # Sağ tık menüsü
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="📈 Stok Ekle", command=self.increase_stock)
        self.context_menu.add_command(label="📉 Stok Azalt", command=self.decrease_stock)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="✏️ Düzenle", command=self.edit_product)
        self.context_menu.add_command(label="🗑️ Sil", command=self.delete_product)
        
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-1>", lambda e: self.edit_product())
        
        # Alt çerçeve - Bilgi
        bottom_frame = ttk.Frame(self.parent)
        bottom_frame.pack(fill=tk.X, padx=16, pady=12)
        
        self.info_label = ttk.Label(bottom_frame, text="Toplam Ürün: 0 | Düşük Stok: 0")
        self.info_label.pack(side=tk.LEFT)
        
        # Refresh butonu
        ttk.Button(
            bottom_frame,
            text="🔄 Yenile",
            command=self.load_products
        ).pack(side=tk.RIGHT)
    
    def sort_by_column(self, col):
        """Sütuna göre sıralama yapar"""
        # Aynı sütuna tekrar tıklanırsa yönü değiştir
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = col
            self.sort_reverse = False
        
        # Başlık okunu güncelle
        for c in self.tree["columns"]:
            self.tree.heading(c, text=self.tree.heading(c, "text").split(" ")[0])
        
        # Ok ekle
        arrow = "↓" if self.sort_reverse else "↑"
        current_text = self.tree.heading(col, "text")
        self.tree.heading(col, text=f"{current_text} {arrow}")
        
        # Ürünleri yeniden yükle
        self.load_products()
    
    def load_products(self):
        """Ürünleri listeye yükler (sıralamalı)"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Düşük stok filtresi
        if self.low_stock_var.get():
            products = get_low_stock_products(self.branch_id)
        else:
            products = get_all_products(self.branch_id)
        
        # Arama filtresi
        search_term = self.search_var.get().lower()
        
        # Filtrelenmiş ürünleri al
        filtered_products = []
        for product in products:
            if search_term:
                if (search_term not in product['name'].lower() and 
                    search_term not in (product['barcode'] or '').lower()):
                    continue
            filtered_products.append(product)
        
        # SIRALA
        if self.sort_column:
            def sort_key(product):
                if self.sort_column == "ID":
                    return product['id']
                elif self.sort_column == "Name":
                    return product['name'].lower()
                elif self.sort_column == "Barcode":
                    return (product['barcode'] or "").lower()
                elif self.sort_column == "Quantity":
                    return product['quantity']
                elif self.sort_column == "MinStock":
                    return product['min_stock']
                elif self.sort_column == "Price":
                    # ₺ işaretini temizle
                    return float(product['unit_price'])
                elif self.sort_column == "Created":
                    return product['created_date']
                return 0
            
            filtered_products.sort(key=sort_key, reverse=self.sort_reverse)
        
        count = 0
        low_stock_count = 0
        
        # Sıralanmış ürünleri ekle
        for product in filtered_products:
            # Renklendirme
            quantity = product['quantity']
            min_stock = product['min_stock']
            
            if quantity <= min_stock:
                tag = 'low_stock'
                low_stock_count += 1
            else:
                tag = 'normal'
            
            self.tree.insert("", tk.END, values=(
                product['id'],
                product['name'],
                product['barcode'] or "-",
                quantity,
                min_stock,
                f"₺{product['unit_price']:.2f}",
                product['created_date']
            ), tags=(tag,))
            
            count += 1
        
        # Bilgi etiketini güncelle
        self.info_label.config(text=f"Toplam Ürün: {count} | Düşük Stok: {low_stock_count}")
        
        # Renk ayarları
        self.tree.tag_configure('low_stock', background='#ffebee', foreground='#c62828')
        self.tree.tag_configure('normal', background='#e8f5e9', foreground='#2e7d32')
    
    def on_search_change(self, *args):
        """Arama kutusu değiştiğinde"""
        self.load_products()
    
    def show_context_menu(self, event):
        """Sağ tık menüsünü gösterir"""
        selection = self.tree.selection()
        if selection:
            self.context_menu.post(event.x_root, event.y_root)
    
    def add_product_dialog(self):
        """Ürün ekleme penceresi"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("➕ Yeni Ürün Ekle")
        dialog.geometry("400x400")
        dialog.configure(bg="#f5f7fb")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Form alanları
        fields = [
            ("Ürün Adı *:", "name", ttk.Entry),
            ("Barkod:", "barcode", ttk.Entry),
            ("Miktar *:", "quantity", tk.Spinbox, {"from_": 0, "to_": 99999}),
            ("Min Stok:", "min_stock", tk.Spinbox, {"from_": 0, "to_": 99999, "value": 10}),
            ("Birim Fiyat:", "unit_price", ttk.Entry),
        ]
        
        entries = {}
        
        for i, field_info in enumerate(fields):
            label_text = field_info[0]
            field_name = field_info[1]
            widget_type = field_info[2]
            
            ttk.Label(dialog, text=label_text).grid(row=i, column=0, padx=10, pady=5, sticky="w")
            
            if len(field_info) > 3:
                widget = widget_type(dialog, **field_info[3])
            else:
                widget = widget_type(dialog)
            
            widget.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            entries[field_name] = widget
        
        # Butonlar
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)
        
        ttk.Button(
            button_frame,
            text="💾 Kaydet",
            command=lambda: self.save_product(dialog, entries)
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(
            button_frame,
            text="❌ İptal",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=10)
    
    def save_product(self, dialog, entries):
        """Ürünü kaydeder"""
        name = entries['name'].get().strip()
        barcode = entries['barcode'].get().strip()
        
        try:
            quantity = int(entries['quantity'].get())
            min_stock = int(entries['min_stock'].get())
            unit_price = float(entries['unit_price'].get() or 0)
        except ValueError:
            messagebox.showwarning("Hatalı Değer", "Miktar, min stok ve fiyat sayısal olmalı!")
            return
        
        if not name:
            messagebox.showwarning("Eksik Bilgi", "Ürün adı zorunludur!")
            return
        
        # Ürünü ekle
        product_id = add_product(
            self.branch_id,
            name,
            barcode if barcode else None,
            quantity,
            min_stock,
            unit_price
        )
        
        if product_id:
            messagebox.showinfo("Başarılı", f"Ürün eklendi: {name}")
            dialog.destroy()
            self.load_products()
        else:
            messagebox.showerror("Hata", "Ürün eklenemedi!")
    
    def increase_stock(self):
        """Stok artırma"""
        self.stock_change_dialog("IN")
    
    def decrease_stock(self):
        """Stok azaltma"""
        self.stock_change_dialog("OUT")
    
    def stock_change_dialog(self, move_type):
        """Stok değişikliği penceresi"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Seçim Yok", "Lütfen bir ürün seçin!")
            return
        
        product_id = self.tree.item(selection[0])['values'][0]
        product_name = self.tree.item(selection[0])['values'][1]
        current_qty = self.tree.item(selection[0])['values'][3]
        
        dialog = tk.Toplevel(self.parent)
        dialog.title("📦 Stok Değişikliği")
        dialog.geometry("400x300")
        dialog.configure(bg="#f5f7fb")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Bilgi
        ttk.Label(dialog, text=f"Ürün: {product_name}").pack(pady=10)
        ttk.Label(dialog, text=f"Mevcut Miktar: {current_qty}").pack()
        
        # Form
        ttk.Label(dialog, text="Miktar:").pack(pady=10)
        qty_spinbox = tk.Spinbox(dialog, from_=1, to_=99999, font=("Arial", 12))
        qty_spinbox.pack()
        
        ttk.Label(dialog, text="Not:").pack(pady=10)
        note_text = tk.Text(dialog, height=3, width=40, relief="solid", borderwidth=1)
        note_text.pack()
        
        # Butonlar
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        action_text = "Stok Ekle" if move_type == "IN" else "Stok Azalt"
        ttk.Button(
            button_frame,
            text=action_text,
            command=lambda: self.apply_stock_change(
                dialog, product_id, move_type, qty_spinbox, note_text, current_qty
            ),
            style="Primary.TButton"
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(
            button_frame,
            text="İptal",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=10)
    
    def apply_stock_change(self, dialog, product_id, move_type, qty_widget, note_widget, old_qty):
        """Stok değişikliğini uygular"""
        try:
            quantity = int(qty_widget.get())
            note = note_widget.get("1.0", tk.END).strip()
            
            if quantity <= 0:
                messagebox.showwarning("Hatalı Miktar", "Miktar 0'dan büyük olmalı!")
                return
            
            # Stok güncelle
            new_qty = update_product_quantity(product_id, move_type, quantity, note)
            
            if new_qty is not None:
                action_text = "eklendi" if move_type == "IN" else "azaltıldı"
                messagebox.showinfo(
                    "Başarılı",
                    f"Stok {action_text}!\nYeni miktar: {new_qty}"
                )
                dialog.destroy()
                self.load_products()
            else:
                messagebox.showerror("Hata", "Stok güncellenemedi!")
        
        except ValueError:
            messagebox.showwarning("Hatalı Değer", "Miktar sayısal olmalı!")
    
    def edit_product(self):
        """✏️ Ürün düzenleme"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Seçim Yok", "Lütfen bir ürün seçin!")
            return
        
        product_id = self.tree.item(selection[0])['values'][0]
        product = fetch_one("SELECT * FROM products WHERE id = ?", (product_id,))
        
        if not product:
            messagebox.showerror("Hata", "Ürün bulunamadı!")
            return
        
        dialog = tk.Toplevel(self.parent)
        dialog.title(f"✏️ Ürün Düzenle: {product['name']}")
        dialog.geometry("400x450")
        dialog.configure(bg="#f5f7fb")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Form alanları
        fields = [
            ("Ürün Adı *:", "name", ttk.Entry, product['name']),
            ("Barkod:", "barcode", ttk.Entry, product['barcode'] or ""),
            ("Min Stok:", "min_stock", tk.Spinbox, {"from_": 0, "to_": 99999}, product['min_stock']),
            ("Birim Fiyat:", "unit_price", ttk.Entry, str(product['unit_price'])),
        ]
        
        entries = {}
        
        for i, field_info in enumerate(fields):
            label_text = field_info[0]
            field_name = field_info[1]
            widget_type = field_info[2]
            
            ttk.Label(dialog, text=label_text).grid(row=i, column=0, padx=10, pady=5, sticky="w")
            
            if widget_type == tk.Spinbox:
                widget = widget_type(dialog, **field_info[3])
                widget.delete(0, tk.END)
                widget.insert(0, field_info[4])
            else:
                widget = widget_type(dialog)
                widget.insert(0, field_info[3])
            
            widget.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            entries[field_name] = widget
        
        # Miktar bilgisi (read-only)
        i = len(fields)
        ttk.Label(dialog, text="Miktar:", foreground="#64748b").grid(row=i, column=0, padx=10, pady=5, sticky="w")
        ttk.Label(dialog, text=str(product['quantity'])).grid(row=i, column=1, padx=10, pady=5, sticky="w")
        
        ttk.Label(
            dialog,
            text="⚠️ Miktar değişikliği için sağ tık → Stok Ekle/Azalt kullanın",
            foreground="#f59e0b",
            wraplength=350
        ).grid(row=i+1, column=0, columnspan=2, padx=10, pady=5)
        
        # Butonlar
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=i+2, column=0, columnspan=2, pady=20)
        
        ttk.Button(
            button_frame,
            text="💾 Güncelle",
            command=lambda: self.save_edited_product(dialog, product_id, entries)
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(
            button_frame,
            text="❌ İptal",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=10)
    
    def save_edited_product(self, dialog, product_id, entries):
        """Düzenlenmiş ürünü kaydeder"""
        name = entries['name'].get().strip()
        barcode = entries['barcode'].get().strip()
        
        try:
            min_stock = int(entries['min_stock'].get())
            unit_price = float(entries['unit_price'].get() or 0)
        except ValueError:
            messagebox.showwarning("Hatalı Değer", "Min stok ve fiyat sayısal olmalı!")
            return
        
        if not name:
            messagebox.showwarning("Eksik Bilgi", "Ürün adı zorunludur!")
            return
        
        success = update_product_info(product_id, name, barcode, min_stock, unit_price)
        
        if success:
            messagebox.showinfo("Başarılı", f"Ürün güncellendi: {name}")
            dialog.destroy()
            self.load_products()
        else:
            messagebox.showerror("Hata", "Ürün güncellenemedi!")
    
    def delete_product(self):
        """Ürün silme"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Seçim Yok", "Lütfen bir ürün seçin!")
            return

        product_id = self.tree.item(selection[0])['values'][0]
        product_name = self.tree.item(selection[0])['values'][1]

        if not messagebox.askyesno("Silme Onayı", f"'{product_name}' ürününü silmek istiyor musunuz?"):
            return

        success = delete_product(product_id)
        if success:
            messagebox.showinfo("Başarılı", f"Ürün silindi: {product_name}")
            self.load_products()
        else:
            messagebox.showerror("Hata", "Ürün silinemedi!")
    
    def open_stock_reports(self):
        """Stok raporları penceresini açar"""
        StockReportsDialog(self.parent, self.branch_id)
