# RugeResto

Aplikasi pemesanan dan pembayaran tunai restoran untuk UAS Programming Fundamentals.

**Nama:** Ahmad Zacky · **NIM:** 24110300025
**Repository:** [github.com/RugeFX/rugeresto-flet](https://github.com/RugeFX/rugeresto-flet)

**Versi GitHub:** [`main` - UAS](https://github.com/RugeFX/rugeresto-flet/tree/main) · [`uts` - versi UTS](https://github.com/RugeFX/rugeresto-flet/tree/uts)

## Versi aplikasi

| Versi | Kode | Data default |
| --- | --- | --- |
| Base app standalone | `src/base.py`: seluruh class, CSV, dan terminal berada dalam satu file; standard library saja | `data/` |
| GUI Flet | `src/main.py` → `src/gui/` → `src/shared/restaurant.py` | `data/` |
| CLI extended | `src/cli/` → `src/shared/restaurant.py` | `data/` |

**Kode base app tetap standalone dan terpisah.** GUI dan CLI extended memakai satu core yang sama, tanpa mengimpor `base.py`. Ketiga antarmuka memakai katalog, pesanan aktif, dan riwayat pembayaran yang sama di `data/`. Pesanan yang disimpan lewat base app dapat dilanjutkan lewat GUI/CLI extended, dan sebaliknya.

[Dokumentasi UAS (PDF, 2 halaman)](docs/Dokumentasi_UAS_RugeResto.pdf) merangkum fitur, class, CSV, dan cuplikan hasil eksekusi program.

[Dokumentasi PDF UTS](docs/Dokumentasi_Base_App_Restoran.pdf) menjelaskan versi lama, sebelum pengembangan UAS dan migrasi CSV ini.

## Fitur UAS

- Class `RestaurantSystem` dengan constructor, atribut bertipe, methods, dan model `MenuItem`, `OrderLine`, `Receipt`.
- Katalog CSV; penambahan menu yang sama memperbesar kuantitas pesanan.
- Add, update, delete, subtotal, total, pembayaran tunai, dan kembalian.
- Pesanan aktif disimpan setiap perubahan dan dipulihkan setelah restart.
- Receipt itemized dengan ID, timestamp WIB (`+07:00`), harga saat pemesanan, cash, dan change.
- Riwayat transaksi, pembukaan receipt berdasarkan ID, dan total penjualan per transaksi.
- Pencarian menu memakai `strip()`, `lower()`, `split()`, dan `join()`; `  NASI   GORENG  ` menemukan `Nasi Goreng`.
- Validasi input dan CSV, pesan kegagalan baca/tulis, penulisan file sementara sebelum replace.
- Pembayaran disimpan sebelum pesanan dibersihkan; restart mengenali receipt yang sudah dibayar jika cleanup sempat gagal.

GUI menyediakan pencarian, **Riwayat transaksi**, **Lihat struk**, **Muat ulang data**, tombol kuantitas, dan **Bayar pas**. Jika data awal tidak dapat dibuka, GUI menampilkan masalah dan tombol **Coba lagi**. Kategori diambil dari katalog CSV secara dinamis.

## Menjalankan

Python 3.10+ diperlukan. Untuk environment GUI dan pengujian, gunakan `uv sync` dari direktori repository.

### Base app standalone

```bash
python src/base.py
```

Tidak membutuhkan Flet, modul `shared`, atau modul `cli`.

### GUI desktop / web

```bash
uv run flet run
uv run flet run --web
```

### CLI extended

macOS / Linux:

```bash
PYTHONPATH=src uv run python -m cli
```

Windows PowerShell:

```powershell
$env:PYTHONPATH = "src"
uv run python -m cli
```

Urutan menu terminal untuk base maupun extended: **1** display menu, **2** add, **3** view, **4** update, **5** delete, **6** payment, **7** search, **8** transaction history, **9** view receipt, **10** exit. `q` dan `exit` juga menutup program. Update/delete terminal memilih nomor baris pesanan.

Gunakan direktori lain yang berisi ketiga CSV untuk demonstrasi atau pengujian:

```bash
python src/base.py --data-dir /path/to/data-copy
PYTHONPATH=src uv run python -m cli --data-dir /path/to/data-copy
RUGERESTO_DATA_DIR=/path/to/data-copy uv run flet run
```

Environment `RUGERESTO_DATA_DIR` berlaku untuk core extended saja dan harus diatur sebelum proses dimulai. Untuk PowerShell gunakan `$env:RUGERESTO_DATA_DIR = "C:\path\to\data-copy"` sebelum menjalankan GUI/CLI extended.

## Data CSV

| File | Header |
| --- | --- |
| `menu.csv` | `number,name,price,category,detail` |
| `active_order.csv` | `order_id,menu_number,name,unit_price,quantity` |
| `transactions.csv` | `order_id,paid_at,menu_number,name,unit_price,quantity,line_total,order_total,paid,change` |

Harga rupiah berupa bilangan bulat nonnegatif; nomor menu positif dan unik; kuantitas positif; nama/kategori/deskripsi tidak kosong. File tanpa pesanan/transaksi tetap harus memiliki header. Riwayat yang disertakan dalam repository berisi data uji lokal. CSV memakai UTF-8. Katalog JSON lama sudah dimigrasikan dan bukan lagi sumber data runtime.

Satu receipt dapat berisi beberapa baris item dengan ID yang sama; total penjualan dihitung sekali per receipt. Mengedit katalog tidak mengubah nama/harga pada receipt lama.

Jalankan satu aplikasi pada satu waktu untuk direktori data ini. Tutup base, GUI, atau CLI sebelum beralih ke antarmuka lainnya; perubahan yang sudah tersimpan akan dimuat saat aplikasi berikutnya dibuka. Gunakan **Muat ulang data** pada GUI untuk membaca ulang CSV secara manual. Jangan mengedit CSV saat aplikasi sedang menyimpan data.

File hilang/rusak tidak diganti diam-diam dengan data kosong. CLI menawarkan perbaikan lalu `retry`; GUI menyediakan **Coba lagi**. Jangan menghapus file yang berisi pesanan atau transaksi penting.

## Struktur

```text
src/
├── base.py                    # Standalone; tidak mengimpor extended
├── main.py                    # Launcher Flet
├── gui/
│   ├── app.py                 # State dan event adapter
│   ├── theme.py
│   └── components/            # Layout, menu, order row/panel, history
├── cli/
│   ├── __main__.py            # python -m cli
│   └── app.py                 # Prompt dan output terminal
└── shared/
    └── restaurant.py          # Model, search, validasi, CSV, pembayaran

data/                         # Data bersama base, GUI, dan CLI extended
├── menu.csv
├── active_order.csv
└── transactions.csv
```

## Interface shared

`RestaurantSystem(data_dir)` memuat CSV; import modul tidak membaca katalog. GUI dan CLI menangani input/output, sedangkan core menangani aturan serta persistence.

| Operasi | Peran |
| --- | --- |
| `search_menu(query)` | Pencarian nama menu yang dinormalisasi. |
| `add_order(menu_number, quantity=1)` | Tambah atau gabungkan item. |
| `update_order(row_number, quantity)` / `delete_order(row_number)` | Operasi berdasarkan nomor baris terminal. |
| `change_quantity(menu_number, difference)` / `remove_item(menu_number)` | Operasi berdasarkan ID menu untuk GUI. |
| `calculate_total()` / `orders` / `menu` | Membaca snapshot untuk tampilan. |
| `payment(amount)` | Simpan receipt lalu bersihkan pesanan. |
| `get_transactions()` / `get_receipt(id)` | Membaca history dan rincian receipt. |
| `refresh()` | Muat ulang data dan pulihkan cleanup pembayaran tertunda. |

## Pengujian

```bash
uv run pytest
```

Pengujian memakai direktori sementara sehingga tidak mengubah data kerja. Mencakup base standalone, CSV, restart, failure recovery, CLI subprocess, serta konstruksi kontrol dan callback GUI yang memanggil core sebenarnya.

Tes GUI tersebut tidak memerlukan runner Flutter dan bukan pengujian visual atau screenshot. Pengujian perangkat dan build distribusi tidak dibuktikan oleh suite ini.

## Distribusi

Entry point build tetap `uv run flet build <platform> -v`. Sebelum distribusi, sertakan seed CSV dalam aset paket dan tentukan lokasi data writable pada target. Layout `data/` saat ini ditujukan untuk menjalankan repository secara lokal; build Android/iOS/web statis belum diverifikasi pada migrasi ini. Toolchain dan signing mengikuti platform target.
