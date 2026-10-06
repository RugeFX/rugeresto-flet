# RugeResto

Aplikasi pemesanan dan pembayaran tunai restoran berbasis Python. Versi extended menyediakan **GUI berbasis Flet** dan **CLI/TUI berbasis menu teks** dengan logika pemesanan serta data menu yang sama.

**Repository:** [github.com/RugeFX/rugeresto-flet](https://github.com/RugeFX/rugeresto-flet)

## Identitas dan dokumentasi

- **Nama:** Ahmad Zacky
- **NIM:** 24110300025
- **Studi kasus:** sistem pemesanan dan pembayaran restoran.
- [Dokumentasi PDF versi dasar](docs/Dokumentasi_Base_App_Restoran.pdf), berisi deskripsi program, fitur, struktur, dan catatan singkat versi extended.

## Versi aplikasi

| Versi | Lokasi | Deskripsi |
| --- | --- | --- |
| Base app | `src/base.py` | Program terminal asli dalam satu file, dengan menu langsung di dalam kode. Dipertahankan sebagai referensi. |
| Extended GUI | `src/gui/` | Antarmuka Flet dengan kartu menu, kontrol kuantitas, dan panel pembayaran. |
| Extended CLI/TUI | `src/cli/` | Antarmuka teks interaktif dengan prompt dan output mengikuti base app. |
| Shared | `src/shared/` | Logika pesanan dan data JSON yang digunakan kedua antarmuka extended. |

GUI dan CLI memakai aturan yang sama, tetapi setiap sesi membuat objek pesanan sendiri. Pesanan tidak tersinkron antarproses dan hanya tersimpan selama program berjalan.

## Fitur versi extended

- Menampilkan menu menurut kategori pada GUI, serta daftar bernomor pada CLI.
- Menambahkan item; penambahan menu yang sama memperbesar kuantitasnya.
- Menampilkan jumlah item, subtotal setiap menu, dan total pesanan.
- Mengubah kuantitas dan menghapus item. GUI menyediakan tombol tambah/kurang; CLI memilih nomor baris pesanan.
- Memvalidasi nomor menu, kuantitas positif, dan nominal pembayaran berupa bilangan bulat.
- Menolak pembayaran yang kurang dan menampilkan selisihnya.
- Menghitung kembalian dan mengosongkan pesanan setelah pembayaran berhasil.
- Menampilkan ringkasan pembayaran pada GUI dan terminal; GUI juga menyediakan tombol **Bayar pas**.
- Memuat menu dari JSON dan menghasilkan kategori secara otomatis berdasarkan urutan kemunculannya dalam data.

Pembayaran adalah pencatatan tunai lokal. Aplikasi belum menyimpan riwayat transaksi, akun pengguna, atau pesanan ke basis data. File JSON menyimpan katalog menu; aplikasi hanya membacanya.

## Persiapan

Gunakan **Python 3.10 atau lebih baru** dan [uv](https://docs.astral.sh/uv/). Dependensi serta konfigurasi proyek tersedia di `pyproject.toml`; versi dependensi dikunci oleh `uv.lock`.

```bash
git clone https://github.com/RugeFX/rugeresto-flet.git
cd rugeresto-flet
uv sync
```

Jalankan perintah berikut dari direktori utama repository.

## Menjalankan aplikasi

### GUI desktop

```bash
uv run flet run
```

Flet menjalankan `src/main.py`, yang memanggil aplikasi pada `src/gui/app.py`.

### GUI web

```bash
uv run flet run --web
```

### CLI/TUI extended

macOS / Linux:

```bash
PYTHONPATH=src uv run python -m cli
```

Windows PowerShell:

```powershell
$env:PYTHONPATH = "src"
uv run python -m cli
```

Pilihan terminal: **1** tampilkan menu, **2** tambah pesanan, **3** lihat pesanan, **4** ubah jumlah, **5** hapus pesanan, **6** bayar, dan **7** keluar. Perintah `exit` atau `q` juga menutup aplikasi.

### Base app

```bash
uv run python src/base.py
```

Base app menggunakan data menunya sendiri, sehingga perubahan JSON hanya berlaku untuk versi extended.

## Mengelola menu JSON

Edit `src/shared/menu.json`, lalu restart GUI atau CLI. Formatnya berupa array objek:

```json
[
  {
    "number": 1,
    "name": "Nasi Goreng",
    "price": 20000,
    "category": "Makanan",
    "detail": "Nasi tumis gurih"
  }
]
```

| Kolom | Aturan |
| --- | --- |
| `number` | Bilangan bulat positif dan unik; digunakan sebagai ID menu. |
| `name` | Teks nama menu yang tidak kosong. |
| `price` | Bilangan bulat nonnegatif dalam rupiah, tanpa pemisah ribuan. |
| `category` | Teks kategori yang tidak kosong. Kategori baru otomatis menjadi bagian menu GUI. |
| `detail` | Teks deskripsi singkat yang tidak kosong. |

Setiap objek harus memiliki tepat lima kolom tersebut. Loader menolak jenis data yang salah, nilai yang tidak valid, dan ID duplikat. File dicari relatif terhadap modul shared, bukan direktori kerja saat aplikasi dijalankan. Ikon serta warna tampilan diatur terpisah pada GUI; item baru memakai ikon cadangan jika tidak memiliki pemetaan khusus.

## Struktur proyek

```text
src/
├── main.py                    # Launcher Flet
├── base.py                    # Program dasar / referensi asli
├── assets/                    # Aset aplikasi
├── gui/
│   ├── __init__.py
│   ├── __main__.py            # Entry point paket GUI
│   ├── app.py                 # Setup halaman, state, dan event handler
│   ├── theme.py               # Warna dan ikon
│   └── components/
│       ├── __init__.py
│       ├── layout.py          # Kerangka halaman dan layout responsif
│       ├── menu.py            # Kategori dan kartu menu
│       ├── order_row.py       # Baris pesanan dan kontrol kuantitas
│       └── order_panel.py     # Total, pembayaran, receipt, dan feedback
├── cli/
│   ├── __init__.py            # Mengekspos run_cli
│   ├── __main__.py            # Entry point python -m cli
│   └── app.py                 # Prompt dan alur interaksi terminal
└── shared/
    ├── __init__.py
    ├── restaurant.py          # Model data, validasi, dan aturan pesanan
    └── menu.json              # Katalog menu versi extended

tests/
├── test_restaurant.py         # Aturan pesanan dan pembayaran
├── test_menu.py               # Pembacaan dan validasi JSON
├── test_cli.py                # Alur CLI dan perbandingan dengan base app
└── test_main.py               # Skenario integrasi GUI Flet

docs/
└── Dokumentasi_Base_App_Restoran.pdf
```

### Logika shared

`MenuItem`, `OrderLine`, dan `Receipt` adalah dataclass immutable. `MENU` berisi item yang dibaca dari JSON; `MENU_CATEGORIES` berisi kategori uniknya. GUI dan CLI berinteraksi dengan `RestaurantOrder`:

| Operasi | Peran |
| --- | --- |
| `add(number, quantity=1)` | Menambahkan item atau memperbesar kuantitas. |
| `set_quantity(number, quantity)` | Mengganti kuantitas item yang telah dipesan. |
| `change_quantity(number, difference)` | Menambah atau mengurangi kuantitas. |
| `remove(number)` | Menghapus item dari pesanan. |
| `pay(amount)` | Mengembalikan receipt dan membersihkan pesanan setelah berhasil. |
| `lines`, `item_count`, `total` | Properti untuk membaca keadaan pesanan. |

Operasi yang ditolak menimbulkan turunan `RestaurantError` dan mempertahankan pesanan. GUI mengelola state serta feedback di `app.py`; modul tampilan menerima data dan callback. CLI menerjemahkan input pengguna menjadi operasi shared yang sama.

## Pengujian

Jalankan pengujian logika shared, JSON, dan CLI:

```bash
uv run pytest tests/test_restaurant.py tests/test_menu.py tests/test_cli.py
```

Pengujian CLI membandingkan transcript dengan `base.py` untuk alur normal dan input tidak valid menggunakan katalog menu referensi. Jika katalog diubah, sesuaikan ekspektasi pengujian yang memakai data menu awal.

`tests/test_main.py` berisi skenario integrasi GUI untuk menambah item dan membayar pas. Skenario ini memerlukan runner integrasi Flet dan bukan bagian dari perintah unit test di atas. Pengujian unit tidak membuktikan perilaku pada perangkat atau hasil build distribusi.

## Build distribusi GUI

Gunakan CLI Flet melalui environment proyek:

```bash
uv run flet build apk -v      # Android
uv run flet build ipa -v      # iOS
uv run flet build macos -v    # macOS
uv run flet build linux -v    # Linux
uv run flet build windows -v # Windows
uv run flet build web -v     # Web
```

Toolchain, host, dan signing harus disiapkan sesuai platform target. Perintah di atas adalah entry point build; keberhasilan unit test tidak berarti semua platform telah dibuild atau diuji.
