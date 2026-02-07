# BusinessManager

Tkinter tabanlı işletme yönetim uygulaması. Şube bazlı stok takibi, toptancı (borç/alacak) yönetimi ve gelir/gider kayıtları için tek arayüz sunar.

## Özellikler
- **Şube yönetimi**: Şube oluşturma ve aktif şube seçimi.
- **Stok takibi**: Ürün ekleme/düzenleme, stok giriş-çıkış, düşük stok filtresi.
- **Toptancı yönetimi**: Toptancı ekleme/düzenleme, borç/alacak işlemleri, ödeme takibi.
- **Gelir/Gider**: İşlem ekleme, filtreleme, günlük/haftalık/aylık raporlar.
- **Raporlar**: Stok hareket raporları ve Excel dışa aktarma.
- **Modern UI**: Tutarlı dialog/uyarı/toast deneyimi ve temiz görünüm.

## Gereksinimler
- Python 3.10+ (önerilen)
- Standart kütüphaneler: `tkinter`, `sqlite3`
- Excel dışa aktarma için (opsiyonel):
  ```bash
  pip install openpyxl
  ```

## Kurulum
```bash
git clone <repo-url>
cd BusinessManager
```

## Çalıştırma
```bash
python main.py
```

Uygulama ilk çalıştırmada `business_manager.db` SQLite veritabanını oluşturur.

## Proje Yapısı
```
.
├─ main.py               # Uygulama girişi ve ana UI
├─ database.py           # SQLite işlemleri
└─ modules/
   ├─ branch_manager.py  # Şube yönetimi dialogları
   ├─ stock_tab.py       # Stok modülü
   ├─ supplier_tab.py    # Toptancı modülü
   ├─ finance_tab.py     # Gelir/Gider modülü
   ├─ stock_reports.py   # Stok raporları
   └─ ui_helpers.py      # Ortak dialog/toast yardımcıları
```

## Notlar
- Veriler `business_manager.db` dosyasında saklanır.
- Excel dışa aktarma için `openpyxl` gerekir.
- Uygulama tek kullanıcı/tek makine senaryosu için tasarlanmıştır.

## Katkı
Öneri ve geliştirmeler için PR gönderebilirsiniz.
