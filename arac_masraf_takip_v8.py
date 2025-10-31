import streamlit as st
import pandas as pd
from datetime import datetime
import os

# ==========================
# DOSYA AYARLARI
# ==========================
DOSYA = "masraflar.csv"
YAKIT_DOSYA = "yakit_kayitlari.csv"
AKTARIM_LOG = "son_aktarim.txt"

# ==========================
# SAYFA AYARLARI
# ==========================
st.set_page_config(page_title="Araç Masraf Takip Sistemi v8", layout="wide")
st.markdown("<h1 style='text-align:center; color:#2196F3;'>🚗 Araç Masraf Takip Sistemi v8</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; font-size:18px;'>💼 Profesyonel Arayüz + Ayrı Veri Yönetimi Sekmeli Final Sürüm</p>", unsafe_allow_html=True)

# ==========================
# VERİ YÜKLEME
# ==========================
try:
    df = pd.read_csv(DOSYA)
except FileNotFoundError:
    df = pd.DataFrame(columns=["Tarih", "Masraf Türü", "Tutar (₺)", "Açıklama", "Taksit Sayısı", "Taksit No"])
    df.to_csv(DOSYA, index=False)

# ==========================
# MASRAF TÜRLERİ
# ==========================
masraf_turleri = [
    "Yakıt", "Köprü & Otoyol", "Sigorta & Kasko", "Tamir / Servis",
    "Periyodik Bakım", "Muayene", "Lastik", "Aksesuar", "Vergi & Ceza", "Otopark & Yıkama"
]

taksitli_turler = [
    "Sigorta & Kasko", "Periyodik Bakım", "Muayene", "Lastik", "Aksesuar", "Vergi & Ceza"
]

# ==========================
# SEKMELER
# ==========================
tab1, tab2, tab3 = st.tabs(["🧾 Kayıt Ekle", "📊 Analiz", "⚙️ Veri Yönetimi"])

# ============================================================
# 🧾 KAYIT EKLEME
# ============================================================
with tab1:
    st.subheader("🧾 Yeni Masraf Kaydı Ekle")

    col1, col2 = st.columns(2)
    with col1:
        tarih = st.date_input("Masraf Tarihi", datetime.now())
        tur = st.selectbox("Masraf Türü", masraf_turleri)
    with col2:
        tutar = st.number_input("Toplam Tutar (₺)", min_value=0.0, step=0.01)
        aciklama = st.text_input("Açıklama", placeholder="Örn: Sigorta yenileme, bakım, otoyol geçişi...")

    taksit_sayisi = 1
    if tur in taksitli_turler:
        taksit_sayisi = st.number_input("Taksit Sayısı", min_value=1, max_value=24, value=1, step=1)

    ekle = st.button("💾 Kaydı Ekle", use_container_width=True)

    if ekle:
        if taksit_sayisi == 1:
            yeni = pd.DataFrame([[tarih, tur, tutar, aciklama, 1, 1]], columns=df.columns)
            df = pd.concat([df, yeni], ignore_index=True)
        else:
            aylik_tutar = tutar / taksit_sayisi
            for i in range(taksit_sayisi):
                ay_tarih = (pd.to_datetime(tarih) + pd.DateOffset(months=i)).date()
                yeni = pd.DataFrame([[ay_tarih, tur, aylik_tutar, aciklama, taksit_sayisi, i + 1]], columns=df.columns)
                df = pd.concat([df, yeni], ignore_index=True)
        df.to_csv(DOSYA, index=False)
        st.success("✅ Masraf kaydedildi!")
    st.markdown("---")
    st.subheader("⛽ Yakıt Verilerini Aktar")

    # Son aktarım zamanı göster
    if os.path.exists(AKTARIM_LOG):
        with open(AKTARIM_LOG, "r") as f:
            son_aktarim = f.read().strip()
        st.info(f"🔄 Son Yakıt Aktarımı: {son_aktarim}")
    else:
        st.info("🔄 Henüz yakıt aktarımı yapılmadı.")

    if st.button("🔄 Yakıt Verilerini Aktar (yakit_takip_v8_1.py'den)", use_container_width=True):
        try:
            yakit_df = pd.read_csv(YAKIT_DOSYA)
            yeni_kayit_sayisi = 0
            for _, row in yakit_df.iterrows():
                tarih = row["Tarih"]
                tutar = row["Toplam_Tutar(₺)"]
                kontrol = (df["Tarih"] == tarih) & (df["Masraf Türü"] == "Yakıt") & (df["Tutar (₺)"] == tutar)
                if df.loc[kontrol].empty:
                    yeni = pd.DataFrame([[tarih, "Yakıt", tutar, "Yakıt alımı (otomatik aktarım)", 1, 1]], columns=df.columns)
                    df = pd.concat([df, yeni], ignore_index=True)
                    yeni_kayit_sayisi += 1
            df.to_csv(DOSYA, index=False)

            # Son aktarım zamanını kaydet
            with open(AKTARIM_LOG, "w") as f:
                f.write(datetime.now().strftime("%d.%m.%Y %H:%M:%S"))

            st.success(f"✅ {yeni_kayit_sayisi} yeni yakıt kaydı eklendi.")
        except Exception as e:
            st.error(f"🚫 Yakıt verisi aktarılırken hata oluştu: {e}")

# ============================================================
# 📊 ANALİZ
# ============================================================
with tab2:
    st.subheader("📊 Genel Analizler")

    if not df.empty:
        df["Tarih"] = pd.to_datetime(df["Tarih"], errors="coerce")

        toplam = df["Tutar (₺)"].sum()
        bu_ay = datetime.now().strftime("%Y-%m")
        df["Ay"] = df["Tarih"].dt.strftime("%Y-%m")
        bu_ay_df = df[df["Ay"] == bu_ay]
        toplam_bu_ay = bu_ay_df["Tutar (₺)"].sum()

        col1, col2 = st.columns(2)
        col1.metric("💰 Toplam Masraf", f"{toplam:,.2f} ₺")
        col2.metric(f"📅 {bu_ay} Ayı Masrafı", f"{toplam_bu_ay:,.2f} ₺")

        st.markdown("---")
        st.markdown("### 💸 Tür Bazlı Masraf Dağılımı")

        for tur in masraf_turleri:
            alt_df = df[df["Masraf Türü"] == tur]
            alt_bu_ay_df = bu_ay_df[bu_ay_df["Masraf Türü"] == tur]

            if not alt_df.empty:
                toplam_tur = alt_df["Tutar (₺)"].sum()
                bu_ay_tur = alt_bu_ay_df["Tutar (₺)"].sum()

                st.markdown(f"<h4 style='color:#4CAF50;'>🔹 {tur}</h4>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                c1.metric("Toplam", f"{toplam_tur:,.2f} ₺")
                c2.metric("Bu Ay", f"{bu_ay_tur:,.2f} ₺")
                st.dataframe(
                    alt_df.style.format({"Tutar (₺)": "{:,.2f} ₺"}),
                    use_container_width=True,
                    height=300,
                )
                st.markdown("---")
    else:
        st.info("Henüz kayıt bulunmuyor kanka.")

# ============================================================
# ⚙️ VERİ YÖNETİMİ
# ============================================================
with tab3:
    st.subheader("⚙️ Veri Yönetimi (Filtre / Arama / Düzenle / Sil)")

    if not df.empty:
        df["Tarih"] = pd.to_datetime(df["Tarih"], errors="coerce")

        with st.expander("🔎 Filtreleme & Arama", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                tur_filtre = st.selectbox("Masraf Türü", ["Tümü"] + masraf_turleri)
            with col2:
                baslangic = st.date_input("Başlangıç Tarihi", df["Tarih"].min().date())
            with col3:
                bitis = st.date_input("Bitiş Tarihi", df["Tarih"].max().date())
            kelime = st.text_input("Açıklama içinde ara", "")

        filtre_df = df.copy()
        if tur_filtre != "Tümü":
            filtre_df = filtre_df[filtre_df["Masraf Türü"] == tur_filtre]
        filtre_df = filtre_df[(filtre_df["Tarih"].dt.date >= baslangic) & (filtre_df["Tarih"].dt.date <= bitis)]
        if kelime.strip():
            filtre_df = filtre_df[filtre_df["Açıklama"].str.contains(kelime, case=False, na=False)]

        st.dataframe(filtre_df.style.format({"Tutar (₺)": "{:,.2f} ₺"}), use_container_width=True, height=350)
        st.metric("Filtrelenmiş Toplam", f"{filtre_df['Tutar (₺)'].sum():,.2f} ₺")

        if len(filtre_df) > 0:
            st.markdown("### ✏️ Düzenle veya 🗑️ Sil")
            secim = st.number_input("Satır numarası (0'dan başlar)", min_value=0, max_value=len(filtre_df)-1, step=1)
            secili = filtre_df.iloc[int(secim)]
            st.info(f"Seçilen: {secili['Masraf Türü']} | {secili['Tarih'].date()} | {secili['Tutar (₺)']} ₺")

            col1, col2 = st.columns(2)
            with col1:
                duzenle = st.button("✏️ Düzenle", use_container_width=True)
            with col2:
                sil = st.button("🗑️ Sil", use_container_width=True)

            if duzenle:
                st.markdown("#### 🔧 Düzenleme")
                yeni_tarih = st.date_input("Yeni Tarih", secili["Tarih"])
                yeni_tur = st.selectbox("Yeni Tür", masraf_turleri, index=masraf_turleri.index(secili["Masraf Türü"]))
                yeni_tutar = st.number_input("Yeni Tutar (₺)", min_value=0.0, step=0.01, value=float(secili["Tutar (₺)"]))
                yeni_aciklama = st.text_input("Yeni Açıklama", secili["Açıklama"])
                if st.button("💾 Değişiklikleri Kaydet"):
                    df.loc[secili.name, "Tarih"] = yeni_tarih
                    df.loc[secili.name, "Masraf Türü"] = yeni_tur
                    df.loc[secili.name, "Tutar (₺)"] = yeni_tutar
                    df.loc[secili.name, "Açıklama"] = yeni_aciklama
                    df.to_csv(DOSYA, index=False)
                    st.success("✅ Kayıt güncellendi! Sayfayı yenileyin.")
            if sil:
                df.drop(index=secili.name, inplace=True)
                df.to_csv(DOSYA, index=False)
                st.success("🗑️ Kayıt silindi! Sayfayı yenileyin.")
    else:
        st.info("Henüz kayıt bulunmuyor kanka.")
