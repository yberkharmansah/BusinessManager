# database.py
import sqlite3
import os
from datetime import datetime, timedelta

DB_NAME = "business_manager.db"

def get_db_connection():
    """Veritabanı bağlantısını oluşturur"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    """Tüm tabloları oluşturur"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Şubeler tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS branches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            address TEXT,
            created_date TEXT NOT NULL
        )
    ''')
    
    # Ürünler tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            branch_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            barcode TEXT,
            quantity INTEGER NOT NULL DEFAULT 0,
            min_stock INTEGER DEFAULT 10,
            unit_price REAL DEFAULT 0,
            created_date TEXT NOT NULL,
            FOREIGN KEY (branch_id) REFERENCES branches(id)
        )
    ''')
    
    # Stok hareketleri tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            type TEXT NOT NULL, -- 'IN' (ekleme) veya 'OUT' (çıkarma)
            quantity INTEGER NOT NULL,
            old_quantity INTEGER NOT NULL,
            new_quantity INTEGER NOT NULL,
            note TEXT,
            date TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    
    # Toptancılar tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            branch_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            supplier_type TEXT, -- Serbest metin: Meşrubat, Süt, Yemek vb.
            phone TEXT,
            email TEXT,
            created_date TEXT NOT NULL,
            FOREIGN KEY (branch_id) REFERENCES branches(id)
        )
    ''')
    
    # Toptancı bakiyeleri tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS supplier_balances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            type TEXT NOT NULL, -- 'BORC' veya 'ALACAK'
            amount REAL NOT NULL,
            due_date TEXT,
            status TEXT DEFAULT 'AKTIF', -- 'AKTIF', 'ODENDI', 'GECIKMIS'
            description TEXT,
            date TEXT NOT NULL,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
        )
    ''')
    
    # Gelir/Gider tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            branch_id INTEGER NOT NULL,
            type TEXT NOT NULL, -- 'GELIR' veya 'GIDER'
            category TEXT,
            amount REAL NOT NULL,
            payment_method TEXT, -- 'NAKIT', 'KREDI', 'BANKA', 'DIGER'
            date TEXT NOT NULL,
            description TEXT,
            FOREIGN KEY (branch_id) REFERENCES branches(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Veritabanı başarıyla oluşturuldu!")

# === BRANCH OPERASYONLARI ===
def create_branch(name, address=""):
    """Yeni şube oluşturur"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO branches (name, address, created_date)
            VALUES (?, ?, ?)
        ''', (name, address, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        branch_id = cursor.lastrowid
        print(f"✅ Şube oluşturuldu: {name}")
        return branch_id
    except sqlite3.IntegrityError:
        print(f"❌ '{name}' adlı şube zaten var!")
        return None
    finally:
        conn.close()

def get_all_branches():
    """Tüm şubeleri getirir"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM branches ORDER BY name")
    branches = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return branches

def get_branch_by_id(branch_id):
    """ID ile şube getirir"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM branches WHERE id = ?", (branch_id,))
    branch = cursor.fetchone()
    conn.close()
    return dict(branch) if branch else None

# === PRODUCT OPERASYONLARI ===
def get_all_products(branch_id):
    """Tüm ürünleri getirir"""
    return fetch_all(
        "SELECT * FROM products WHERE branch_id = ? ORDER BY name",
        (branch_id,)
    )

def add_product(branch_id, name, barcode, quantity, min_stock=10, unit_price=0):
    """Yeni ürün ekler"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO products (branch_id, name, barcode, quantity, min_stock, unit_price, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (branch_id, name, barcode, quantity, min_stock, unit_price, 
              datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Ürün ekleme hatası: {e}")
        return None
    finally:
        conn.close()

def update_product_quantity(product_id, move_type, quantity, note=""):
    """Stok miktarını günceller ve hareket kaydeder"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Mevcut miktarı al
        cursor.execute("SELECT quantity FROM products WHERE id = ?", (product_id,))
        current = cursor.fetchone()
        
        if not current:
            return None
        
        old_qty = current['quantity']
        
        # Yeni miktarı hesapla
        if move_type == "IN":
            new_qty = old_qty + quantity
        else:
            new_qty = old_qty - quantity
            if new_qty < 0:
                return None
        
        # Ürünü güncelle
        cursor.execute(
            "UPDATE products SET quantity = ? WHERE id = ?",
            (new_qty, product_id)
        )
        
        # Hareket kaydet
        cursor.execute('''
            INSERT INTO stock_movements (product_id, type, quantity, old_quantity, new_quantity, note, date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (product_id, move_type, quantity, old_qty, new_qty, note,
              datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        conn.commit()
        return new_qty
        
    except Exception as e:
        print(f"Stok güncelleme hatası: {e}")
        return None
    finally:
        conn.close()

def update_product_info(product_id, name, barcode, min_stock, unit_price):
    """Ürün bilgilerini günceller (stok hariç)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE products 
            SET name = ?, barcode = ?, min_stock = ?, unit_price = ?
            WHERE id = ?
        ''', (name, barcode if barcode else None, min_stock, unit_price, product_id))
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Ürün güncelleme hatası: {e}")
        return False
    finally:
        conn.close()

def delete_product(product_id):
    """Ürünü siler"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM stock_movements WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Ürün silme hatası: {e}")
        return False
    finally:
        conn.close()

# === TOPTANCI (SUPPLIER) OPERASYONLARI ===
def get_all_suppliers(branch_id):
    """Tüm toptancıları getirir"""
    return fetch_all(
        "SELECT * FROM suppliers WHERE branch_id = ? ORDER BY name",
        (branch_id,)
    )

def add_supplier(branch_id, name, supplier_type, phone="", email=""):
    """Yeni toptancı ekler - supplier_type artık serbest metin"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO suppliers (branch_id, name, supplier_type, phone, email, created_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (branch_id, name, supplier_type.strip(), phone, email,
              datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Toptancı ekleme hatası: {e}")
        return None
    finally:
        conn.close()

def update_supplier(supplier_id, name, supplier_type, phone, email):
    """Toptancı bilgilerini günceller - supplier_type serbest metin"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE suppliers 
            SET name = ?, supplier_type = ?, phone = ?, email = ?
            WHERE id = ?
        ''', (name, supplier_type.strip(), phone, email, supplier_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Toptancı güncelleme hatası: {e}")
        return False
    finally:
        conn.close()

def delete_supplier(supplier_id):
    """Toptancıyı siler (bakiyeleri de)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM supplier_balances WHERE supplier_id = ?", (supplier_id,))
        cursor.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Toptancı silme hatası: {e}")
        return False
    finally:
        conn.close()

# === AKILLI BAKİYE SİSTEMİ ===
def add_smart_balance_transaction(supplier_id, transaction_type, amount, due_date=None, description="", transaction_date=None):
    """Akıllı bakiye sistemi - otomatik borç/alacak dengeler"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Mevcut toplam bakiyeyi al
        current_balance = get_supplier_total_balance(supplier_id)
        
        if transaction_date is None:
            transaction_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # İŞLEM TÜRÜNE GÖRE AKILLI HESAPLAMA
        if transaction_type == "ODEME":
            # ÖDEME: Borçtan düş, fazla varsa alacak oluştur
            if current_balance < 0:  # Borcumuz var
                if amount <= abs(current_balance):  # Borçtan düş
                    new_balance = current_balance + amount
                    description = f"Ödeme: ₺{amount:.2f} borçtan düşüldü"
                else:  # Fazla ödeme - alacak oluşur
                    excess = amount - abs(current_balance)
                    new_balance = excess  # Artık alacağımız var
                    description = f"Ödeme: ₺{amount:.2f} (₺{abs(current_balance):.2f} borç kapatıldı, ₺{excess:.2f} alacak)"
            else:  # Alacağımız var ya da sıfır
                new_balance = current_balance + amount  # Alacağımız artar
                description = f"Ödeme: ₺{amount:.2f} alacak eklendi"
                
            # Ödeme işlemini kaydet
            cursor.execute('''
                INSERT INTO supplier_balances (supplier_id, type, amount, due_date, status, description, date)
                VALUES (?, 'ALACAK', ?, ?, 'ODENDI', ?, ?)
            ''', (supplier_id, amount, due_date, description, transaction_date))
            
        elif transaction_type == "ALIS":
            # ALIŞ: Alacağımızdan düş, fazla varsa borç oluştur
            if current_balance > 0:  # Alacağımız var
                if amount <= current_balance:  # Alacağımızdan düş
                    new_balance = current_balance - amount
                    description = f"Alış: ₺{amount:.2f} alacağımızdan düşüldü"
                else:  # Fazla alış - borç oluşur
                    excess = amount - current_balance
                    new_balance = -excess  # Artık borcumuz var
                    description = f"Alış: ₺{amount:.2f} (₺{current_balance:.2f} alacağımız kapatıldı, ₺{excess:.2f} borç)"
            else:  # Borcumuz var ya da sıfır
                new_balance = current_balance - amount  # Borcumuz artar
                description = f"Alış: ₺{amount:.2f} borç eklendi"
                
            # Alış işlemini kaydet
            cursor.execute('''
                INSERT INTO supplier_balances (supplier_id, type, amount, due_date, status, description, date)
                VALUES (?, 'BORC', ?, ?, 'AKTIF', ?, ?)
            ''', (supplier_id, amount, due_date, description, transaction_date))
            
        elif transaction_type == "BORC":
            # BORÇ: Direkt borç ekle
            new_balance = current_balance - amount
            cursor.execute('''
                INSERT INTO supplier_balances (supplier_id, type, amount, due_date, status, description, date)
                VALUES (?, 'BORC', ?, ?, 'AKTIF', ?, ?)
            ''', (supplier_id, amount, due_date, description, transaction_date))
            
        elif transaction_type == "ALACAK":
            # ALACAK: Direkt alacak ekle
            new_balance = current_balance + amount
            cursor.execute('''
                INSERT INTO supplier_balances (supplier_id, type, amount, due_date, status, description, date)
                VALUES (?, 'ALACAK', ?, ?, 'AKTIF', ?, ?)
            ''', (supplier_id, amount, due_date, description, transaction_date))
        
        conn.commit()
        return new_balance
        
    except Exception as e:
        print(f"Akıllı bakiye hatası: {e}")
        return None
    finally:
        conn.close()

def get_supplier_balances(branch_id):
    """Toptancı bakiyelerini getirir (birleştirilmiş)"""
    return fetch_all('''
        SELECT 
            sb.id,
            sb.supplier_id,
            sup.name as supplier_name,
            sup.supplier_type,
            sb.type as balance_type,
            sb.amount,
            sb.due_date,
            sb.status,
            sb.description,
            sb.date
        FROM supplier_balances sb
        JOIN suppliers sup ON sb.supplier_id = sup.id
        WHERE sup.branch_id = ?
        ORDER BY CASE 
            WHEN sb.status = 'AKTIF' AND sb.due_date >= date('now') THEN 1
            WHEN sb.status = 'GECIKMIS' OR sb.due_date < date('now') THEN 2
            ELSE 3
        END, sb.due_date ASC
    ''', (branch_id,))

def get_supplier_total_balance(supplier_id):
    """Toptancının toplam bakiyesini hesaplar"""
    result = fetch_one('''
        SELECT 
            SUM(CASE WHEN type = 'ALACAK' THEN amount ELSE -amount END) as total
        FROM supplier_balances
        WHERE supplier_id = ? AND status = 'AKTIF'
    ''', (supplier_id,))
    
    return result['total'] if result and result['total'] else 0

def get_due_supplier_balances(branch_id, days=7):
    """Yaklaşan ödemeleri getirir – NULL vade tarihleri hariç"""
    from datetime import datetime, timedelta   # 🔥 iç import

    target_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

    return fetch_all('''
        SELECT 
            sb.id,
            sb.supplier_id,
            sup.name as supplier_name,
            sb.type,
            sb.amount,
            sb.due_date,
            sb.status,
            sb.description,
            sb.date
        FROM supplier_balances sb
        JOIN suppliers sup ON sb.supplier_id = sup.id
        WHERE sup.branch_id = ?
          AND sb.due_date IS NOT NULL        -- 🔥 NULL'ları atlama
          AND sb.due_date <= ?
          AND sb.status = 'AKTIF'
        ORDER BY sb.due_date ASC
    ''', (branch_id, target_date))

def get_supplier_transaction_history(supplier_id):
    """Toptancının tüm hareketlerini getirir"""
    return fetch_all('''
        SELECT 
            date,
            type,
            amount,
            due_date,
            status,
            description
        FROM supplier_balances
        WHERE supplier_id = ?
        ORDER BY date DESC
    ''', (supplier_id,))

def update_balance_status(balance_id, new_status):
    """Bakiye durumunu günceller"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE supplier_balances SET status = ? WHERE id = ?",
            (new_status, balance_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Durum güncelleme hatası: {e}")
        return False
    finally:
        conn.close()

# === YARDIMCI FONKSIYONLAR ===
def execute_query(query, params=()):
    """Genel sorgu çalıştırıcı"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()

def fetch_all(query, params=()):
    """Tüm satırları getirir"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results

def fetch_one(query, params=()):
    """Tek satır getirir"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = cursor.fetchone()
    conn.close()
    return dict(result) if result else None

def get_low_stock_products(branch_id, threshold=None):
    """Stoğu azalan ürünleri getirir"""
    if threshold is None:
        return fetch_all('''
            SELECT * FROM products 
            WHERE branch_id = ? AND quantity <= min_stock
            ORDER BY quantity ASC
        ''', (branch_id,))
    else:
        return fetch_all('''
            SELECT * FROM products 
            WHERE branch_id = ? AND quantity <= ?
            ORDER BY quantity ASC
        ''', (branch_id, threshold))

def get_stock_movements_report(branch_id, product_id=None, start_date=None, end_date=None):
    """Stok hareketlerini filtreli getirir"""
    query = """
        SELECT 
            sm.id,
            sm.product_id,
            p.name as product_name,
            p.barcode,
            sm.type,
            sm.quantity,
            sm.old_quantity,
            sm.new_quantity,
            sm.note,
            sm.date
        FROM stock_movements sm
        JOIN products p ON sm.product_id = p.id
        WHERE p.branch_id = ?
    """
    params = [branch_id]
    
    if product_id:
        query += " AND sm.product_id = ?"
        params.append(product_id)
    
    if start_date:
        query += " AND sm.date >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND sm.date <= ?"
        params.append(end_date + " 23:59:59")
    
    query += " ORDER BY sm.date DESC"
    
    return fetch_all(query, params)

# === UYARI SISTEMI ===
def get_due_payments(branch_id, days=7):
    """Yaklaşan ödemeleri getirir"""
    target_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    
    return fetch_all('''
        SELECT sb.*, s.name as supplier_name 
        FROM supplier_balances sb
        JOIN suppliers s ON sb.supplier_id = s.id
        WHERE s.branch_id = ? 
        AND sb.due_date <= ? 
        AND sb.status = 'AKTIF'
        ORDER BY sb.due_date ASC
    ''', (branch_id, target_date))

if __name__ == "__main__":
    initialize_database()
# === GELIR/GIDER (FINANCE) OPERASYONLARI ===

def add_transaction(branch_id, trans_type, amount, payment_method, date=None, description="", category=""):
    """Yeni gelir/gider kaydı ekle"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute('''
            INSERT INTO transactions (branch_id, type, amount, payment_method, date, description, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (branch_id, trans_type, amount, payment_method, date, description, category))
        
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Gelir/Gider ekleme hatası: {e}")
        return None
    finally:
        conn.close()

def get_transactions(branch_id, start_date=None, end_date=None, trans_type=None, payment_method=None):
    """Tarih aralığına ve filtrelere göre işlemleri getir"""
    query = """
        SELECT * FROM transactions 
        WHERE branch_id = ?
    """
    params = [branch_id]
    
    if start_date:
        query += " AND DATE(date) >= ?"
        params.append(start_date)
    if end_date:
        query += " AND DATE(date) <= ?"
        params.append(end_date)
    if trans_type:
        query += " AND type = ?"
        params.append(trans_type)
    if payment_method:
        query += " AND payment_method = ?"
        params.append(payment_method)
    
    query += " ORDER BY date DESC"
    
    return fetch_all(query, params)

def get_daily_total(branch_id, date=None):
    """Belirli tarihin gelir/gider toplamını getir"""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    result = fetch_one('''
        SELECT 
            SUM(CASE WHEN type = 'GELIR' THEN amount ELSE 0 END) as total_income,
            SUM(CASE WHEN type = 'GIDER' THEN amount ELSE 0 END) as total_expense,
            SUM(CASE WHEN type = 'GELIR' THEN amount ELSE -amount END) as net_profit
        FROM transactions 
        WHERE branch_id = ? AND DATE(date) = ?
    ''', (branch_id, date))
    
    return {
        'income': result['total_income'] or 0,
        'expense': result['total_expense'] or 0,
        'net': result['net_profit'] or 0
    }

def get_period_summary(branch_id, start_date, end_date):
    """Belirli tarih aralığının özetini getir"""
    result = fetch_one('''
        SELECT 
            SUM(CASE WHEN type = 'GELIR' THEN amount ELSE 0 END) as total_income,
            SUM(CASE WHEN type = 'GIDER' THEN amount ELSE 0 END) as total_expense,
            SUM(CASE WHEN type = 'GELIR' THEN amount ELSE -amount END) as net_profit,
            COUNT(*) as transaction_count
        FROM transactions 
        WHERE branch_id = ? AND DATE(date) BETWEEN ? AND ?
    ''', (branch_id, start_date, end_date))
    
    return {
        'income': result['total_income'] or 0,
        'expense': result['total_expense'] or 0,
        'net': result['net_profit'] or 0,
        'count': result['transaction_count'] or 0
    }

def update_transaction(trans_id, trans_type, amount, payment_method, date, description="", category=""):
    """İşlem kaydını güncelle"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE transactions 
            SET type = ?, amount = ?, payment_method = ?, date = ?, description = ?, category = ?
            WHERE id = ?
        ''', (trans_type, amount, payment_method, date, description, category, trans_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Güncelleme hatası: {e}")
        return False
    finally:
        conn.close()

def delete_transaction(trans_id):
    """İşlem kaydını sil"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM transactions WHERE id = ?", (trans_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Silme hatası: {e}")
        return False
    finally:
        conn.close()

def get_transaction_stats(branch_id):
    """Genel istatistikler"""
    stats = fetch_one('''
        SELECT 
            COUNT(*) as total_count,
            SUM(CASE WHEN type = 'GELIR' THEN 1 ELSE 0 END) as income_count,
            SUM(CASE WHEN type = 'GIDER' THEN 1 ELSE 0 END) as expense_count,
            SUM(CASE WHEN payment_method = 'NAKIT' THEN amount ELSE 0 END) as cash_total,
            SUM(CASE WHEN payment_method = 'KREDI' THEN amount ELSE 0 END) as credit_total,
            SUM(CASE WHEN payment_method = 'BANKA' THEN amount ELSE 0 END) as bank_total
        FROM transactions 
        WHERE branch_id = ?
    ''', (branch_id,))
    
    return stats
