import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import streamlit as st
from datetime import date

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Olist E-Commerce Dashboard",
    page_icon="🛒",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #f0f4ff;
        border-radius: 12px;
        padding: 18px 22px;
        border-left: 5px solid #4f6ef7;
    }
    .metric-label { font-size: 13px; color: #666; font-weight: 600; margin-bottom: 4px; }
    .metric-value { font-size: 28px; font-weight: 800; color: #1a1a2e; }
    .metric-sub   { font-size: 12px; color: #4f6ef7; margin-top: 4px; }
    .section-title { font-size: 18px; font-weight: 700; color: #1a1a2e; margin: 8px 0 4px; }
    [data-testid="stSidebar"] { background: #1a1a2e; }
    [data-testid="stSidebar"] * { color: #e8eaf6 !important; }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stDateInput label,
    [data-testid="stSidebar"] .stMultiSelect label { color: #b0bec5 !important; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

# ── Load & Cache Data ─────────────────────────────────────────────────────────
BASE_DIR =os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "../data")

@st.cache_data
def load_data(data_path=DATA_PATH):
    orders      = pd.read_csv(os.path.join(data_path, "olist_orders_dataset.csv"))
    payments    = pd.read_csv(os.path.join(data_path, "olist_order_payments_dataset.csv"))
    reviews     = pd.read_csv(os.path.join(data_path, "olist_order_reviews_dataset.csv"))
    customers   = pd.read_csv(os.path.join(data_path, "olist_customers_dataset.csv"))
    products    = pd.read_csv(os.path.join(data_path, "olist_products_dataset.csv"))
    order_items = pd.read_csv(os.path.join(data_path, "olist_order_items_dataset.csv"))
    cat_trans   = pd.read_csv(os.path.join(data_path, "product_category_name_translation.csv"))

    # Merge utama
    df = (orders
          .merge(customers, on="customer_id", how="inner")
          .merge(payments,  on="order_id",    how="inner")
          .merge(reviews,   on="order_id",    how="inner"))

    # Gabung produk + kategori
    oi = (order_items
          .merge(products,  on="product_id",           how="inner")
          .merge(cat_trans, on="product_category_name", how="left"))
    df = df.merge(
        oi[["order_id", "product_category_name_english", "price"]],
        on="order_id", how="inner"
    )

    # Parsing tanggal
    date_cols = ["order_purchase_timestamp", "order_approved_at",
                 "order_delivered_carrier_date", "order_delivered_customer_date",
                 "order_estimated_delivery_date"]
    for c in date_cols:
        df[c] = pd.to_datetime(df[c])

    # Cleaning
    df.dropna(subset=["order_delivered_customer_date"], inplace=True)
    drop_cols = ["review_comment_title", "review_comment_message",
                 "review_creation_date", "review_answer_timestamp"]
    df.drop(columns=[c for c in drop_cols if c in df.columns], inplace=True)

    # Filter 2017-2018
    df = df[df["order_purchase_timestamp"].dt.year.isin([2017, 2018])]

    # Feature Engineering
    df["delivery_time_days"]  = (df["order_delivered_customer_date"] - df["order_purchase_timestamp"]).dt.days
    df["delivery_delay_days"] = (df["order_delivered_customer_date"] - df["order_estimated_delivery_date"]).dt.days
    df["purchase_month"]      = df["order_purchase_timestamp"].dt.to_period("M").astype(str)
    df["purchase_year"]       = df["order_purchase_timestamp"].dt.year
    df["purchase_hour"]       = df["order_purchase_timestamp"].dt.hour
    df["purchase_date"]       = df["order_purchase_timestamp"].dt.date
    df["payment_category"]    = pd.qcut(df["payment_value"], q=3, labels=["Low", "Medium", "High"])

    return df

# ── Try load data ─────────────────────────────────────────────────────────────
try:
    raw_df = load_data(DATA_PATH)
    data_loaded = True
except FileNotFoundError as e:
    data_loaded = False
    missing_file = str(e)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛒 Olist Dashboard")
    st.markdown("**Brazilian E-Commerce 2017–2018**")
    st.markdown("---")

    if data_loaded:
        st.markdown("### 📅 Filter Rentang Tanggal")
        min_date = raw_df["purchase_date"].min()
        max_date = raw_df["purchase_date"].max()

        date_range = st.date_input(
            "Pilih rentang tanggal",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )

        st.markdown("### 🗂️ Filter Metode Pembayaran")
        all_payment_types = sorted(raw_df["payment_type"].unique().tolist())
        selected_payments = st.multiselect(
            "Metode Pembayaran",
            options=all_payment_types,
            default=all_payment_types,
            placeholder="Pilih metode pembayaran...",
        )
        if not selected_payments:
            selected_payments = all_payment_types

        st.markdown("### ⭐ Filter Review Score")
        score_range = st.slider("Rentang Review Score", 1, 5, (1, 5))

        st.markdown("### 🏷️ Filter Top N Kategori")
        top_n = st.slider("Tampilkan Top N Kategori", 5, 20, 10)

        st.markdown("---")
        st.markdown("**Lintang Zidan Dzaki**")
        st.markdown("CDCC009D6Y2739")

# ── FILTER DATA ───────────────────────────────────────────────────────────────
if data_loaded:
    # Handle single date selection gracefully
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range if not isinstance(date_range, (list, tuple)) else date_range[0]

    df = raw_df[
        (raw_df["purchase_date"] >= start_date) &
        (raw_df["purchase_date"] <= end_date) &
        (raw_df["payment_type"].isin(selected_payments)) &
        (raw_df["review_score"] >= score_range[0]) &
        (raw_df["review_score"] <= score_range[1])
    ].copy()

# ── MAIN CONTENT ──────────────────────────────────────────────────────────────
st.title("🛒 Brazilian E-Commerce Dashboard")
st.markdown("**Analisis Data Olist | Periode 2017–2018**")

if not data_loaded:
    st.error(f"""
    ⚠️ **Dataset tidak ditemukan!**

    Pastikan semua file CSV dataset Olist berada di folder `../data/` relatif terhadap `dashboard.py`:
    - `olist_orders_dataset.csv`
    - `olist_order_payments_dataset.csv`
    - `olist_order_reviews_dataset.csv`
    - `olist_customers_dataset.csv`
    - `olist_products_dataset.csv`
    - `olist_order_items_dataset.csv`
    - `product_category_name_translation.csv`

    Error: `{missing_file}`
    """)
    st.stop()

if df.empty:
    st.warning("⚠️ Tidak ada data yang sesuai dengan filter yang dipilih. Coba perluas rentang tanggal atau filter lainnya.")
    st.stop()

# ── KPI METRICS ───────────────────────────────────────────────────────────────
total_revenue  = df["payment_value"].sum()
total_orders   = df["order_id"].nunique()
total_customers = df["customer_id"].nunique()
avg_review     = df["review_score"].mean()
avg_delivery   = df["delivery_time_days"].mean()
avg_delay      = df["delivery_delay_days"].mean()

col1, col2, col3, col4, col5 = st.columns(5)

def metric_card(label, value, sub=""):
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-sub">{sub}</div>
    </div>"""

with col1:
    st.markdown(metric_card("💰 Total Revenue", f"R$ {total_revenue:,.0f}", "periode terpilih"), unsafe_allow_html=True)
with col2:
    st.markdown(metric_card("📦 Total Pesanan", f"{total_orders:,}", "order unik"), unsafe_allow_html=True)
with col3:
    st.markdown(metric_card("👥 Total Pelanggan", f"{total_customers:,}", "customer unik"), unsafe_allow_html=True)
with col4:
    st.markdown(metric_card("⭐ Avg Review Score", f"{avg_review:.2f} / 5", "rata-rata kepuasan"), unsafe_allow_html=True)
with col5:
    delay_label = f"{'⚠️ terlambat' if avg_delay > 0 else '✅ lebih cepat'} {abs(avg_delay):.1f} hari"
    st.markdown(metric_card("🚚 Avg Pengiriman", f"{avg_delivery:.1f} hari", delay_label), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# PERTANYAAN 1: KATEGORI PRODUK & TREN REVENUE
# ══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 📊 Pertanyaan 1: Kategori Produk dengan Revenue Tertinggi & Tren Penjualan (2017–2018)")

category_revenue_df = (
    df.groupby("product_category_name_english")
    .agg(total_orders=("order_id", "nunique"), total_revenue=("payment_value", "sum"))
    .reset_index()
    .sort_values("total_revenue", ascending=False)
)
top_cat = category_revenue_df.head(top_n)

monthly_sales_df = (
    df.groupby("purchase_month")
    .agg(total_orders=("order_id", "nunique"), total_revenue=("payment_value", "sum"))
    .reset_index()
    .sort_values("purchase_month")
)

col_a, col_b = st.columns([1, 1.3])

with col_a:
    fig1, ax1 = plt.subplots(figsize=(7, 5))
    colors = sns.color_palette("viridis", len(top_cat))
    bars = ax1.barh(top_cat["product_category_name_english"][::-1],
                    top_cat["total_revenue"][::-1], color=colors[::-1])
    ax1.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"R${x/1e6:.1f}M"))
    ax1.set_xlabel("Total Revenue")
    ax1.set_title(f"Top {top_n} Kategori Produk berdasarkan Revenue", fontweight="bold", fontsize=12)
    ax1.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig1)
    plt.close()

with col_b:
    fig2, ax_r = plt.subplots(figsize=(9, 5))
    ax_r.plot(monthly_sales_df["purchase_month"], monthly_sales_df["total_revenue"],
              marker="o", color="#e74c3c", linewidth=2.2, label="Revenue")
    ax_r.fill_between(monthly_sales_df["purchase_month"], monthly_sales_df["total_revenue"],
                      alpha=0.12, color="#e74c3c")
    ax_r.set_ylabel("Total Revenue (R$)", color="#e74c3c")
    ax_r.tick_params(axis="y", labelcolor="#e74c3c")
    ax_r.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"R${x/1e6:.1f}M"))
    plt.xticks(rotation=45, ha="right", fontsize=8)

    ax_o = ax_r.twinx()
    ax_o.bar(monthly_sales_df["purchase_month"], monthly_sales_df["total_orders"],
             alpha=0.25, color="#3498db", label="Total Orders")
    ax_o.set_ylabel("Total Orders", color="#3498db")
    ax_o.tick_params(axis="y", labelcolor="#3498db")

    ax_r.set_title("Tren Revenue & Jumlah Pesanan per Bulan", fontweight="bold", fontsize=12)
    ax_r.spines[["top"]].set_visible(False)
    fig2.tight_layout()
    st.pyplot(fig2)
    plt.close()

with st.expander("💡 Insight Pertanyaan 1"):
    st.markdown("""
    - Kategori **health_beauty**, **watches_gifts**, dan **bed_bath_table** menjadi penyumbang revenue tertinggi selama 2017–2018.
    - Revenue mencapai **puncak pada November 2017**, kemungkinan dipicu oleh event **Black Friday**.
    - Volume pesanan tumbuh signifikan sepanjang 2018 dibanding 2017, menunjukkan pertumbuhan organik platform.
    """)

# ══════════════════════════════════════════════════════════════════
# PERTANYAAN 2: KETERLAMBATAN PENGIRIMAN vs REVIEW SCORE
# ══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🚚 Pertanyaan 2: Pengaruh Keterlambatan Pengiriman terhadap Kepuasan Pelanggan (2017–2018)")

delay_review_df = (
    df.groupby("review_score")
    .agg(delivery_delay_days=("delivery_delay_days", "mean"),
         delivery_time_days=("delivery_time_days", "mean"))
    .reset_index()
)

col_c, col_d = st.columns(2)

palette_rdylgn = ["#d73027", "#f46d43", "#fee08b", "#66bd63", "#1a9850"]

with col_c:
    fig3, ax3 = plt.subplots(figsize=(7, 5))
    bars3 = ax3.bar(delay_review_df["review_score"].astype(str),
                    delay_review_df["delivery_delay_days"],
                    color=palette_rdylgn)
    ax3.axhline(0, color="black", linestyle="--", linewidth=0.9, alpha=0.6)
    ax3.set_xlabel("Review Score (Bintang)")
    ax3.set_ylabel("Rata-rata Keterlambatan (Hari)\n(negatif = lebih cepat dari estimasi)")
    ax3.set_title("Rata-rata Keterlambatan Berdasarkan\nReview Score (2017–2018)", fontweight="bold", fontsize=12)
    for bar in bars3:
        h = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width() / 2, h + (0.3 if h >= 0 else -0.8),
                 f"{h:.1f}d", ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax3.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig3)
    plt.close()

with col_d:
    fig4, ax4 = plt.subplots(figsize=(7, 5))
    ax4.bar(delay_review_df["review_score"].astype(str),
            delay_review_df["delivery_time_days"],
            color=palette_rdylgn)
    ax4.set_xlabel("Review Score (Bintang)")
    ax4.set_ylabel("Rata-rata Waktu Pengiriman (Hari)")
    ax4.set_title("Rata-rata Waktu Pengiriman Berdasarkan\nReview Score (2017–2018)", fontweight="bold", fontsize=12)
    for bar in ax4.patches:
        ax4.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
                 f"{bar.get_height():.1f}d", ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax4.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig4)
    plt.close()

with st.expander("💡 Insight Pertanyaan 2"):
    st.markdown("""
    - Pelanggan yang memberikan **rating bintang 1** rata-rata mengalami keterlambatan pengiriman terlama.
    - Pesanan yang tiba **lebih cepat dari estimasi** (nilai negatif) cenderung mendapatkan **rating 4–5**.
    - Terdapat **korelasi negatif** yang jelas antara keterlambatan dan kepuasan pelanggan.
    """)

# ══════════════════════════════════════════════════════════════════
# PERTANYAAN 3: METODE PEMBAYARAN & JAM TRANSAKSI
# ══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 💳 Pertanyaan 3: Metode Pembayaran & Pola Jam Transaksi (2017–2018)")

payment_method_df = (
    df.groupby("payment_type")
    .agg(total_orders=("order_id", "nunique"), total_revenue=("payment_value", "sum"))
    .reset_index()
    .sort_values("total_orders", ascending=False)
)
hour_df = (
    df.groupby("purchase_hour")
    .agg(total_orders=("order_id", "nunique"))
    .reset_index()
)

col_e, col_f = st.columns(2)

with col_e:
    fig5, ax5 = plt.subplots(figsize=(7, 5))
    colors5 = sns.color_palette("viridis", len(payment_method_df))
    ax5.barh(payment_method_df["payment_type"][::-1],
             payment_method_df["total_orders"][::-1], color=colors5[::-1])
    ax5.set_xlabel("Total Pesanan")
    ax5.set_title("Jumlah Pesanan per Metode Pembayaran (2017–2018)", fontweight="bold", fontsize=12)
    ax5.spines[["top", "right"]].set_visible(False)
    for bar in ax5.patches:
        ax5.text(bar.get_width() + 100, bar.get_y() + bar.get_height() / 2,
                 f"{int(bar.get_width()):,}", va="center", fontsize=10)
    plt.tight_layout()
    st.pyplot(fig5)
    plt.close()

with col_f:
    fig6, ax6 = plt.subplots(figsize=(7, 5))
    ax6.plot(hour_df["purchase_hour"], hour_df["total_orders"],
             marker="o", color="#3498db", linewidth=2.2)
    ax6.fill_between(hour_df["purchase_hour"], hour_df["total_orders"],
                     alpha=0.18, color="#3498db")
    ax6.set_xlabel("Jam Transaksi (0 = tengah malam)")
    ax6.set_ylabel("Total Pesanan")
    ax6.set_title("Pola Transaksi Berdasarkan Jam (2017–2018)", fontweight="bold", fontsize=12)
    ax6.set_xticks(range(0, 24))
    ax6.axvspan(10, 16, alpha=0.08, color="orange", label="Jam sibuk siang")
    ax6.axvspan(20, 22, alpha=0.08, color="purple", label="Jam sibuk malam")
    ax6.legend(fontsize=9)
    ax6.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig6)
    plt.close()

with st.expander("💡 Insight Pertanyaan 3"):
    st.markdown("""
    - **Kartu kredit (credit_card)** mendominasi metode pembayaran dengan selisih sangat signifikan.
    - Terdapat **dua puncak transaksi** harian: pukul **10.00–16.00** (jam kerja) dan **20.00–22.00** (malam hari).
    - Ini mengindikasikan dua segmen perilaku belanja: saat jam istirahat/kerja dan setelah pulang kerja.
    """)

# ══════════════════════════════════════════════════════════════════
# PERTANYAAN 4: DISTRIBUSI CICILAN
# ══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 💸 Pertanyaan 4: Distribusi Cicilan Berdasarkan Kategori Belanja (2017–2018)")

installment_trend_df = (
    df.groupby("payment_category", observed=True)
    .agg(avg_installments=("payment_installments", "mean"),
         total_orders=("order_id", "nunique"),
         avg_payment=("payment_value", "mean"))
    .reset_index()
)

col_g, col_h = st.columns([1, 1])

with col_g:
    fig7, ax7 = plt.subplots(figsize=(7, 5))
    order_cat  = ["Low", "Medium", "High"]
    colors_cat = ["#74b9ff", "#a29bfe", "#6c5ce7"]
    data_plot  = installment_trend_df.set_index("payment_category").reindex(order_cat).reset_index()
    bars7 = ax7.bar(data_plot["payment_category"], data_plot["avg_installments"], color=colors_cat, width=0.5)
    for bar in bars7:
        h = bar.get_height()
        ax7.text(bar.get_x() + bar.get_width() / 2, h + 0.05,
                 f"{h:.2f}x", ha="center", va="bottom", fontsize=13, fontweight="bold")
    ax7.set_xlabel("Kategori Belanja")
    ax7.set_ylabel("Rata-rata Jumlah Cicilan")
    ax7.set_title("Rata-rata Cicilan per Kategori Belanja (2017–2018)", fontweight="bold", fontsize=12)
    ax7.set_ylim(0, data_plot["avg_installments"].max() * 1.25)
    ax7.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig7)
    plt.close()

with col_h:
    # Tabel ringkasan
    summary_table = installment_trend_df.copy()
    summary_table = summary_table.set_index("payment_category").reindex(order_cat)
    summary_table.columns = ["Rata-rata Cicilan", "Total Pesanan", "Rata-rata Nilai Belanja"]
    summary_table["Rata-rata Cicilan"] = summary_table["Rata-rata Cicilan"].map("{:.2f}x".format)
    summary_table["Total Pesanan"]    = summary_table["Total Pesanan"].map("{:,}".format)
    summary_table["Rata-rata Nilai Belanja"] = summary_table["Rata-rata Nilai Belanja"].map("R$ {:,.2f}".format)
    st.markdown("#### 📋 Ringkasan Kategori Belanja")
    st.dataframe(summary_table, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Distribusi installment keseluruhan
    fig8, ax8 = plt.subplots(figsize=(7, 3.5))
    installment_counts = df["payment_installments"].value_counts().sort_index().head(12)
    ax8.bar(installment_counts.index.astype(str), installment_counts.values, color="#6c5ce7", alpha=0.8)
    ax8.set_xlabel("Jumlah Cicilan")
    ax8.set_ylabel("Frekuensi")
    ax8.set_title("Distribusi Jumlah Cicilan yang Dipilih", fontweight="bold", fontsize=11)
    ax8.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig8)
    plt.close()

with st.expander("💡 Insight Pertanyaan 4"):
    st.markdown("""
    - Pelanggan kategori **High spending** menggunakan rata-rata cicilan paling banyak dibanding Low dan Medium.
    - Terdapat **korelasi positif** antara nilai belanja dan jumlah cicilan — semakin mahal, semakin banyak dicicil.
    - Fitur installment sangat penting untuk mendorong konversi pada transaksi bernilai tinggi.
    """)

# ══════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#aaa; font-size:13px;'>"
    "📊 Olist E-Commerce Dashboard | Proyek Analisis Data Dicoding | "
    "<b>Lintang Zidan Dzaki</b> — CDCC009D6Y2739"
    "</div>",
    unsafe_allow_html=True
)