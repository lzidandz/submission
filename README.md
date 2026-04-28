# Proyek Analisis Data: Brazilian E-Commerce (Olist)

## Deskripsi Proyek
Proyek ini merupakan analisis data pada dataset Brazilian E-Commerce dari Olist. Analisis mencakup eksplorasi tren penjualan, pengaruh pengiriman terhadap kepuasan pelanggan, pola transaksi, serta perilaku penggunaan cicilan.

## Pertanyaan Bisnis
1. Produk kategori apa yang paling banyak menghasilkan revenue dan bagaimana tren penjualannya dari waktu ke waktu?
2. Apakah terdapat hubungan antara keterlambatan pengiriman dengan kepuasan pelanggan?
3. Pada metode pembayaran apa dan di rentang jam berapa transaksi paling sering terjadi?
4. Bagaimana distribusi penggunaan cicilan berdasarkan kategori nilai belanja pelanggan?

## Struktur Direktori
```
submission
├── dashboard
│   ├── main_data.csv
│   └── dashboard.py
├── data
│   ├── olist_orders_dataset.csv
│   ├── olist_order_payments_dataset.csv
│   ├── olist_order_reviews_dataset.csv
│   └── olist_customers_dataset.csv
├── notebook.ipynb
├── README.md
├── requirements.txt
└── url.txt
```

## Setup Environment

### Menggunakan pip (virtual environment)
```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

### Menggunakan conda
```bash
conda create --name olist-env python=3.11
conda activate olist-env
pip install -r requirements.txt
```

## Menjalankan Dashboard Streamlit

1. Masuk ke folder dashboard:
```bash
cd dashboard
```

2. Jalankan Streamlit:
```bash
streamlit run dashboard.py
```

3. Dashboard akan terbuka otomatis di browser pada `http://localhost:8501`

> **Catatan:** Pastikan file `main_data.csv` ada di dalam folder `dashboard/` sebelum menjalankan dashboard.

## Menjalankan Notebook

Buka file `notebook.ipynb` menggunakan Jupyter Notebook atau Google Colab, lalu jalankan seluruh cell secara berurutan. Pastikan semua file CSV dataset tersedia di folder `data/`.
