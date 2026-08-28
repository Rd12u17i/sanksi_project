import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import date

# Konfigurasi Halaman Web
st.set_page_config(
    page_title="OAMS - Sistem Sanksi Karyawan",
    page_icon="📋",
    layout="wide"
)

# KONEKSI SUPABASE (Ganti dengan data dari Supabase Anda)
SUPABASE_URL = "https://zuctywyaxznjhzwckery.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp1Y3R5d3lheHpuamh6d2NrZXJ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc5MjI1OTcsImV4cCI6MjEwMzQ5ODU5N30.14uuKR3VoXkTE48jBS2NzX57NCDMwcFtXhKkLjJKJTg"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Sidebar Navigasi
st.sidebar.title("📌 Navigasi OAMS")
menu = st.sidebar.radio("Pilih Menu", ["Dashboard", "Input Sanksi", "History & Pencarian"])

# --- 1. HALAMAN DASHBOARD ---
if menu == "Dashboard":
    st.title("📊 Dashboard Sanksi Karyawan")
    st.caption("Ringkasan data pelanggaran dan sanksi karyawan secara real-time.")
    
    # Ambil data dari Supabase
    res = supabase.table("sanksi").select("*").execute()
    df = pd.DataFrame(res.data)
    
    # Summary Cards
    col1, col2, col3, col4 = st.columns(4)
    total_data = len(df) if not df.empty else 0
    sp3_count = len(df[df['sanksi'] == 'SP3']) if not df.empty and 'sanksi' in df.columns else 0
    sp1_count = len(df[df['sanksi'] == 'SP1']) if not df.empty and 'sanksi' in df.columns else 0
    pk_count = len(df[df['sanksi'] == 'PERSONAL KONTAK']) if not df.empty and 'sanksi' in df.columns else 0
    
    col1.metric("Total Sanksi Terdata", total_data)
    col2.metric("Total SP3", sp3_count)
    col3.metric("Total SP1", sp1_count)
    col4.metric("Personal Kontak", pk_count)
    
    st.markdown("---")
    st.subheader("📋 10 Record Terbaru")
    if not df.empty:
        # Menampilkan tabel data terbaru
        st.dataframe(df.sort_values(by="id", ascending=False).head(10), use_container_width=True)
    else:
        st.info("Belum ada data sanksi yang tersimpan.")

# --- 2. HALAMAN INPUT SANKSI ---
elif menu == "Input Sanksi":
    st.title("📝 Form Input Sanksi Karyawan")
    st.caption("Masukkan detail sanksi karyawan di bawah ini.")
    
    with st.form("form_sanksi", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            tgl = st.date_input("Tanggal Input", date.today())
            nrp = st.text_input("NRP Karyawan", placeholder="Masukkan NRP")
            nama = st.text_input("Nama Karyawan", placeholder="Masukkan Nama Lengkap")
            pasal = st.text_input("Pasal Pelanggaran", placeholder="Contoh: Pasal 12 Ayat 3")
            sanksi = st.selectbox("Jenis Sanksi", [
                "PERSONAL KONTAK", "PERINGATAN TERTULIS", "SP1", "SP2", "SP3", "DIKEMBALIKAN KE HC"
            ])
            tgl_in = st.date_input("Tanggal IN (Mulai Sanksi)", date.today())
        
        with col2:
            tgl_out = st.date_input("Tanggal OUT (Selesai Sanksi)", date.today())
            sanksi_tambahan = st.text_input("Sanksi Tambahan", placeholder="Opsional")
            pelanggaran = st.text_area("Uraian Pelanggaran", placeholder="Jelaskan detail pelanggaran")
            pic = st.text_input("PIC / Atasan", placeholder="Nama Penanggung Jawab")
            ket = st.text_input("Keterangan", placeholder="Keterangan tambahan")
        
        submitted = st.form_submit_button("💾 Simpan Data Sanksi")
        
        if submitted:
            if not nrp or not nama:
                st.error("NRP dan Nama Karyawan wajib diisi!")
            else:
                payload = {
                    "tanggal": str(tgl),
                    "nrp": nrp,
                    "nama": nama,
                    "pasal": pasal,
                    "sanksi": sanksi,
                    "tgl_in": str(tgl_in),
                    "tgl_out": str(tgl_out),
                    "sanksi_tambahan": sanksi_tambahan,
                    "pelanggaran": pelanggaran,
                    "pic": pic,
                    "keterangan": ket
                }
                supabase.table("sanksi").insert(payload).execute()
                st.success(f"Berhasil! Data sanksi untuk {nama} ({nrp}) telah disimpan.")

# --- 3. HALAMAN HISTORY & PENCARIAN ---
elif menu == "History & Pencarian":
    st.title("🔍 History & Pencarian Sanksi")
    
    res = supabase.table("sanksi").select("*").execute()
    df = pd.DataFrame(res.data)
    
    search_query = st.text_input("🔎 Cari berdasarkan NRP atau Nama Karyawan:")
    
    if not df.empty:
        if search_query:
            df_filtered = df[
                df['nrp'].astype(str).str.contains(search_query, case=False, na=False) | 
                df['nama'].astype(str).str.contains(search_query, case=False, na=False)
            ]
        else:
            df_filtered = df
            
        st.dataframe(df_filtered, use_container_width=True)
        st.write(f"Total data ditemukan: **{len(df_filtered)}** baris")
    else:
        st.info("Database masih kosong.")