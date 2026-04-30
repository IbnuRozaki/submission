import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import os

# Page config
st.set_page_config(
    page_title="Bike-Sharing Dashboard",
    page_icon="🚲",
    layout="wide",
)

# Load data
@st.cache_data
def load_data():
    base = os.path.dirname(__file__)
    day_df  = pd.read_csv(os.path.join(base, "main_data.csv"))

    hour_path = os.path.join(base, "..", "data", "hour.csv")
    if os.path.exists(hour_path):
        hour_df = pd.read_csv(hour_path)
    else:
        hour_df = None

    # Konversi kolom tanggal
    day_df["dteday"] = pd.to_datetime(day_df["dteday"])
    if hour_df is not None:
        hour_df["dteday"] = pd.to_datetime(hour_df["dteday"])

    # Mapping label kategorikal
    season_map     = {1: "Spring", 2: "Summer", 3: "Fall", 4: "Winter"}
    weathersit_map = {
        1: "Clear",
        2: "Mist/Cloudy",
        3: "Light Rain/Snow",
        4: "Heavy Rain/Snow",
    }
    yr_map      = {0: 2011, 1: 2012}
    weekday_map = {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed",
                   4: "Thu", 5: "Fri",  6: "Sat"}

    for df in [day_df] + ([hour_df] if hour_df is not None else []):
        df["season_label"]  = df["season"].map(season_map)
        df["weather_label"] = df["weathersit"].map(weathersit_map)
        df["yr_label"]      = df["yr"].map(yr_map)
        df["weekday_label"] = df["weekday"].map(weekday_map)
        df["temp_actual"]      = df["temp"]      * 41
        df["hum_actual"]       = df["hum"]       * 100
        df["windspeed_actual"] = df["windspeed"] * 67

    return day_df, hour_df


day_df, hour_df = load_data()

# Sidebar
st.sidebar.title("Navigasi Sidebar")
st.sidebar.markdown("---")

year_options = sorted(day_df["yr_label"].unique())
selected_years = st.sidebar.multiselect(
    "Tahun", year_options, default=year_options
)

season_options = ["Spring", "Summer", "Fall", "Winter"]
selected_seasons = st.sidebar.multiselect(
    "Musim", season_options, default=season_options
)

st.sidebar.markdown("---")
st.sidebar.caption("Data: Bike Sharing Dataset (UCI ML Repository)")


# Filter data 
mask = (
    day_df["yr_label"].isin(selected_years)
    & day_df["season_label"].isin(selected_seasons)
)
filtered = day_df[mask]

# Header
st.title("🚲 Bike-Sharing Analytics Dashboard")
st.markdown(
    "Dashboard ini menampilkan insight dari dataset **Bike-Sharing** "
    "Capital Bikeshare Washington D.C. (2011–2012)."
)

# KPI Cards
total_rides   = int(filtered["cnt"].sum())
avg_daily     = int(filtered["cnt"].mean())
max_daily     = int(filtered["cnt"].max())
registered_pct = round(filtered["registered"].sum() / filtered["cnt"].sum() * 100, 1)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Peminjaman", f"{total_rides:,}")
c2.metric("Rata-rata Harian", f"{avg_daily:,}")
c3.metric("Puncak Harian", f"{max_daily:,}")
c4.metric("% Pengguna Registered", f"{registered_pct}%")

st.markdown("---")

# Pertanyaan 1 – Cuaca & Musim
st.subheader("Pertanyaan 1: Pengaruh Cuaca & Musim terhadap Peminjaman Harian")

col_left, col_right = st.columns(2)

with col_left:
    st.markdown("##### Rata-rata Peminjaman per Musim")
    season_order = [s for s in ["Spring", "Summer", "Fall", "Winter"]
                    if s in selected_seasons]
    season_avg = (
        filtered.groupby("season_label")["cnt"]
        .mean()
        .reindex(season_order)
    )
    colors_season = {"Spring": "#4CAF50", "Summer": "#FF9800",
                     "Fall": "#F44336", "Winter": "#2196F3"}

    fig1, ax1 = plt.subplots(figsize=(5, 3.5))
    bars = ax1.bar(
        season_avg.index,
        season_avg.values,
        color=[colors_season.get(s, "#999") for s in season_avg.index],
        edgecolor="black",
        linewidth=0.5,
    )
    ax1.set_xlabel("Musim", fontsize=10)
    ax1.set_ylabel("Rata-rata Peminjaman", fontsize=10)
    ax1.set_ylim(0, season_avg.max() * 1.2 if len(season_avg) > 0 else 1)
    for i, v in enumerate(season_avg.values):
        ax1.text(i, v + season_avg.max() * 0.02, f"{v:.0f}",
                 ha="center", fontsize=9, fontweight="bold")
    ax1.tick_params(axis="both", labelsize=9)
    sns.despine(ax=ax1)
    plt.tight_layout()
    st.pyplot(fig1)
    plt.close(fig1)

with col_right:
    st.markdown("##### Distribusi Peminjaman per Kondisi Cuaca")
    weather_order = ["Clear", "Mist/Cloudy", "Light Rain/Snow"]
    weather_data  = filtered[filtered["weather_label"].isin(weather_order)]

    fig2, ax2 = plt.subplots(figsize=(5, 3.5))
    sns.boxplot(
        data=weather_data,
        x="weather_label",
        y="cnt",
        order=weather_order,
        palette="Blues",
        ax=ax2,
    )
    medians = (
        weather_data.groupby("weather_label")["cnt"]
        .median()
        .reindex(weather_order)
        .values
    )
    for i, median in enumerate(medians):
        if not pd.isna(median):
            ax2.text(
                i, median + 100, f"{median:.0f}",
                ha="center", va="bottom",
                fontweight="bold", color="black", fontsize=9,
            )
    ax2.set_title("Distribusi Peminjaman Sepeda\nper Kondisi Cuaca", fontsize=10, fontweight="bold")
    ax2.set_xlabel("Kondisi Cuaca", fontsize=10)
    ax2.set_ylabel("Jumlah Peminjaman", fontsize=10)
    ax2.set_xticklabels(weather_order, fontsize=8)
    ax2.tick_params(axis="y", labelsize=9)
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)

with st.expander("Insight Pertanyaan 1"):
    st.markdown(
        """
- **Musim Gugur** memiliki rata-rata peminjaman tertinggi, diikuti Musim Panas, Musim Salju, dan terendah Musim Semi.
- Kondisi cuaca **Cerah** menghasilkan peminjaman jauh lebih tinggi dibanding cuaca buruk.
- Cuaca **Hujan ringan/Salju** menurunkan peminjaman secara signifikan.
        """
    )

st.markdown("---")

# Pertanyaan 2 – Pola per Jam
st.subheader("Pertanyaan 2: Pola Peminjaman per Jam (Hari Kerja vs Libur)")

if hour_df is not None:
    # Filter hour_df berdasarkan tahun yang dipilih
    hour_filtered = hour_df[hour_df["yr_label"].isin(selected_years)]

    workday_hourly = (
        hour_filtered[hour_filtered["workingday"] == 1]
        .groupby("hr")["cnt"]
        .mean()
    )
    holiday_hourly = (
        hour_filtered[hour_filtered["workingday"] == 0]
        .groupby("hr")["cnt"]
        .mean()
    )

    fig3, ax3 = plt.subplots(figsize=(10, 4))
    ax3.plot(workday_hourly.index, workday_hourly.values,
             marker="o", linewidth=2, color="#1565C0", label="Hari Kerja")
    ax3.plot(holiday_hourly.index, holiday_hourly.values,
             marker="s", linewidth=2, color="#E53935", linestyle="--",
             label="Libur / Akhir Pekan")

    if len(workday_hourly) > 0:
        pk_w = workday_hourly.idxmax()
        ax3.annotate(
            f"Puncak jam {pk_w}:00\n({workday_hourly[pk_w]:.0f} sepeda)",
            xy=(pk_w, workday_hourly[pk_w]),
            xytext=(pk_w - 3, workday_hourly[pk_w] + 20),
            arrowprops=dict(arrowstyle="->", color="#1565C0"),
            fontsize=8, color="#1565C0",
        )
    if len(holiday_hourly) > 0:
        pk_h = holiday_hourly.idxmax()
        ax3.annotate(
            f"Puncak jam {pk_h}:00\n({holiday_hourly[pk_h]:.0f} sepeda)",
            xy=(pk_h, holiday_hourly[pk_h]),
            xytext=(pk_h + 1, holiday_hourly[pk_h] + 20),
            arrowprops=dict(arrowstyle="->", color="#E53935"),
            fontsize=8, color="#E53935",
        )

    ax3.set_xlabel("Jam (0–23)", fontsize=10)
    ax3.set_ylabel("Rata-rata Jumlah Peminjaman", fontsize=10)
    ax3.set_xticks(range(0, 24))
    ax3.legend(fontsize=10)
    ax3.grid(axis="y", alpha=0.3)
    sns.despine(ax=ax3)
    plt.tight_layout()
    st.pyplot(fig3)
    plt.close(fig3)
else:
    st.info("File `hour.csv` tidak ditemukan di folder dashboard. Tambahkan file tersebut untuk melihat analisis per-jam.")

with st.expander("Insight Pertanyaan 2"):
    st.markdown(
        """
- **Hari kerja** menunjukkan pola dua puncak, yaitu: jam **08:00** (berangkat kerja) dan jam **17:00–18:00** (pulang kerja).
- **Hari libur/akhir pekan** memiliki satu puncak tunggal sekitar jam **13:00–14:00** yang mencerminkan penggunaan rekreasi.
- Segmentasi pengguna sangat berbeda antara hari kerja dan hari libur.
        """
    )

st.markdown("---")

# Analisis Lanjutan – Tren Bulanan
st.subheader("📈 Analisis Lanjutan: Tren Peminjaman Bulanan")

monthly_trend = (
    filtered.groupby(["yr_label", "mnth"])["cnt"]
    .sum()
    .reset_index()
)

fig4, ax4 = plt.subplots(figsize=(10, 4))
palette = {2011: "#1565C0", 2012: "#E53935"}
for yr, grp in monthly_trend.groupby("yr_label"):
    ax4.plot(grp["mnth"], grp["cnt"], marker="o", linewidth=2,
             label=str(yr), color=palette.get(yr, "#666"))

ax4.set_xlabel("Bulan", fontsize=10)
ax4.set_ylabel("Total Peminjaman", fontsize=10)
ax4.set_xticks(range(1, 13))
ax4.set_xticklabels(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    fontsize=9,
)
ax4.legend(title="Tahun", fontsize=10)
ax4.yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f"{int(x):,}")
)
ax4.grid(axis="y", alpha=0.3)
sns.despine(ax=ax4)
plt.tight_layout()
st.pyplot(fig4)
plt.close(fig4)

# Ringkasan pertumbuhan
if set([2011, 2012]).issubset(set(selected_years)):
    total_per_yr = filtered.groupby("yr_label")["cnt"].sum()
    
    if 2011 in total_per_yr.index and 2012 in total_per_yr.index:
        growth = (
            (total_per_yr[2012] - total_per_yr[2011]) / total_per_yr[2011] * 100
        )
        st.metric("Pertumbuhan 2011 → 2012", f"{growth:.1f}%")

st.markdown("---")