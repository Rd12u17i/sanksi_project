import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import date, datetime
import io

# Konfigurasi Halaman Modern & Mobile Responsive
st.set_page_config(
    page_title="OAMS - Sistem Sanksi Karyawan",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk Kerapian Tabel & Mencegah Text-Wrap
st.markdown("""
<style>
    /* Menjaga teks tabel tetap 1 baris (no-wrap) & border grid rapi */
    .stDataFrame {
        border: 1px solid #e6e8eb;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 1. KONEKSI SUPABASE
# -----------------------------------------------------------------------------
SUPABASE_URL = "https://zuctywyaxznjhzwckery.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp1Y3R5d3lheHpuamh6d2NrZXJ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc5MjI1OTcsImV4cCI6MjEwMzQ5ODU5N30.14uuKR3VoXkTE48jBS2NzX57NCDMwcFtXhKkLjJKJTg"  # Ganti dengan anon key Anda

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# -----------------------------------------------------------------------------
# 2. LOAD MASTER DATA (DENGAN CACHE MEMORI)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=300)
def load_supabase_master():
    master_karyawan = {}
    list_pasal = set()
    list_pic = set()
    
    try:
        res_k = supabase.table("master_karyawan").select("nrp, nama").execute()
        if res_k.data:
            for r in res_k.data:
                if r.get("nrp") and r.get("nama"):
                    master_karyawan[str(r["nrp"]).strip()] = str(r["nama"]).strip()
    except Exception:
        pass

    try:
        res_p = supabase.table("master_pasal").select("pasal").execute()
        if res_p.data:
            for r in res_p.data:
                if r.get("pasal"):
                    list_pasal.add(str(r["pasal"]).strip())
    except Exception:
        pass

    try:
        res_pic = supabase.table("master_pic").select("nama_pic").execute()
        if res_pic.data:
            for r in res_pic.data:
                if r.get("nama_pic"):
                    list_pic.add(str(r["nama_pic"]).strip())
    except Exception:
        pass

    try:
        res_s = supabase.table("sanksi").select("nrp, nama, pasal, pic").execute()
        if res_s.data:
            for r in res_s.data:
                if r.get("nrp") and r.get("nama"):
                    master_karyawan[str(r["nrp"]).strip()] = str(r["nama"]).strip()
                if r.get("pasal"):
                    list_pasal.add(str(r["pasal"]).strip())
                if r.get("pic"):
                    list_pic.add(str(r["pic"]).strip())
    except Exception:
        pass

    return master_karyawan, sorted(list(list_pasal)), sorted(list(list_pic))

MASTER_KARYAWAN, LIST_PASAL, LIST_PIC = load_supabase_master()

# -----------------------------------------------------------------------------
# 3. SIDEBAR (LOGGING & ROLE)
# -----------------------------------------------------------------------------
st.sidebar.title("🔐 OAMS System")
role = st.sidebar.radio("Akses Sebagai:", ["User (Read-Only)", "Admin"])

is_admin = False
if role == "Admin":
    password = st.sidebar.text_input("Masukkan PIN Admin:", type="password")
    if password == "1234":
        is_admin = True
        st.sidebar.success("✅ Akses Admin Aktif")
    elif password:
        st.sidebar.error("❌ Password Salah!")

st.sidebar.markdown("---")
menu_options = ["Dashboard", "Input Sanksi", "History & Pencarian"] if is_admin else ["History & Pencarian"]
menu = st.sidebar.radio("Menu Utama", menu_options)

def parse_date(date_str):
    if not date_str or pd.isna(date_str):
        return date.today()
    try:
        return datetime.strptime(str(date_str), "%Y-%m-%d").date()
    except Exception:
        return date.today()

# -----------------------------------------------------------------------------
# 4. DASHBOARD (Rapi Bergaris, Tanpa ID & Indeks Nomor)
# -----------------------------------------------------------------------------
if menu == "Dashboard" and is_admin:
    st.title("📊 Dashboard Sanksi Karyawan")
    st.caption("Ringkasan data sanksi secara real-time dari Supabase.")
    
    res = supabase.table("sanksi").select("*").execute()
    df = pd.DataFrame(res.data)
    
    col1, col2, col3, col4 = st.columns(4)
    total_data = len(df) if not df.empty else 0
    sp3_count = len(df[df['sanksi'] == 'SP3']) if not df.empty and 'sanksi' in df.columns else 0
    sp1_count = len(df[df['sanksi'] == 'SP1']) if not df.empty and 'sanksi' in df.columns else 0
    pk_count = len(df[df['sanksi'] == 'PERSONAL KONTAK']) if not df.empty and 'sanksi' in df.columns else 0
    
    col1.metric("Total Sanksi", total_data)
    col2.metric("Total SP3", sp3_count)
    col3.metric("Total SP1", sp1_count)
    col4.metric("Personal Kontak", pk_count)
    
    st.markdown("---")
    st.subheader("📋 5 Record Terbaru")
    if not df.empty:
        # Hapus kolom id dan created_at dari tampilan dashboard
        df_dash = df.sort_values(by="id", ascending=False).head(5)
        df_dash_clean = df_dash.drop(columns=['id', 'created_at'], errors='ignore')
        
        # Tampilkan tabel bergaris tanpa indeks nomor
        st.dataframe(df_dash_clean, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada data sanksi.")

# -----------------------------------------------------------------------------
# 5. FORM INPUT SANKSI (Khusus Admin)
# -----------------------------------------------------------------------------
elif menu == "Input Sanksi" and is_admin:
    st.title("📝 Form Input Sanksi Karyawan")
    
    if st.session_state.get("should_reset", False):
        st.session_state.input_nama = ""
        st.session_state.input_nrp = ""
        st.session_state.should_reset = False

    if "notif_success" in st.session_state:
        st.toast(st.session_state.pop("notif_success"), icon="✅")
    if "notif_error" in st.session_state:
        st.error(st.session_state.pop("notif_error"))

    if "input_nama" not in st.session_state:
        st.session_state.input_nama = ""
    if "input_nrp" not in st.session_state:
        st.session_state.input_nrp = ""

    def auto_fill_nama():
        typed_nrp = st.session_state.input_nrp.strip()
        if typed_nrp in MASTER_KARYAWAN:
            st.session_state.input_nama = MASTER_KARYAWAN[typed_nrp]

    col1, col2 = st.columns(2)

    with col1:
        tgl = st.date_input("Tanggal Input", date.today())
        nrp = st.text_input("NRP Karyawan", key="input_nrp", on_change=auto_fill_nama, placeholder="Ketik NRP lalu tekan Enter...")
        nama = st.text_input("Nama Karyawan", key="input_nama", placeholder="Terisi otomatis jika NRP ada di master...")
        
        pasal_options = [""] + LIST_PASAL + ["+ Ketik Pasal Baru..."]
        selected_pasal = st.selectbox("Pasal Pelanggaran (Ketik untuk filter)", options=pasal_options)
        pasal = st.text_input("Ketik Pasal Baru") if selected_pasal == "+ Ketik Pasal Baru..." else selected_pasal

        sanksi = st.selectbox("Jenis Sanksi", ["PERSONAL KONTAK", "PERINGATAN TERTULIS", "SP1", "SP2", "SP3", "DIKEMBALIKAN KE HC"])
        tgl_in = st.date_input("Tanggal IN (Mulai Sanksi)", date.today())

    with col2:
        tgl_out = st.date_input("Tanggal OUT (Selesai Sanksi)", date.today())
        sanksi_tambahan = st.text_input("Sanksi Tambahan", placeholder="Opsional")
        pelanggaran = st.text_area("Uraian Pelanggaran")

        pic_options = [""] + LIST_PIC + ["+ Ketik PIC Baru..."]
        selected_pic = st.selectbox("PIC / Atasan (Ketik untuk filter)", options=pic_options)
        pic = st.text_input("Ketik PIC Baru") if selected_pic == "+ Ketik PIC Baru..." else selected_pic

        ket = st.text_input("Keterangan Tambahan")

    st.markdown("<br>", unsafe_allow_html=True)
    submitted = st.button("💾 Simpan Data Sanksi", type="primary", use_container_width=True)

    if submitted:
        if not nrp or not nama:
            st.session_state.notif_error = "NRP dan Nama Karyawan wajib diisi!"
            st.rerun()
        else:
            payload = {
                "tanggal": str(tgl), "nrp": nrp, "nama": nama, "pasal": pasal,
                "sanksi": sanksi, "tgl_in": str(tgl_in), "tgl_out": str(tgl_out),
                "sanksi_tambahan": sanksi_tambahan, "pelanggaran": pelanggaran,
                "pic": pic, "keterangan": ket
            }
            supabase.table("sanksi").insert(payload).execute()

            is_new_master = False
            try:
                if nrp not in MASTER_KARYAWAN:
                    supabase.table("master_karyawan").insert({"nrp": nrp, "nama": nama}).execute()
                    is_new_master = True
                if selected_pasal == "+ Ketik Pasal Baru..." and pasal:
                    supabase.table("master_pasal").insert({"pasal": pasal}).execute()
                    is_new_master = True
                if selected_pic == "+ Ketik PIC Baru..." and pic:
                    supabase.table("master_pic").insert({"nama_pic": pic}).execute()
                    is_new_master = True
            except Exception:
                pass

            if is_new_master:
                st.cache_data.clear()

            st.session_state.should_reset = True
            st.session_state.notif_success = f"Berhasil menyimpan sanksi untuk {nama} ({nrp})!"
            st.rerun()

# -----------------------------------------------------------------------------
# 6. HISTORY & PENCARIAN (User & Admin - Tombol Ringkas Mengikuti Tinggi Sel)
# -----------------------------------------------------------------------------
elif menu == "History & Pencarian":
    st.title("🔍 History & Pencarian Sanksi")
    
    res = supabase.table("sanksi").select("*").execute()
    df = pd.DataFrame(res.data)
    
    search_query = st.text_input("🔎 Cari berdasarkan NRP atau Nama Karyawan:")
    
    if not df.empty:
        # 1. Hitung Status Otomatis
        today_date = date.today()
        
        def calculate_status(tgl_out_val):
            try:
                t_out = datetime.strptime(str(tgl_out_val), "%Y-%m-%d").date()
                return "🔴 AKTIF" if today_date <= t_out else "⚪ NON-AKTIF"
            except Exception:
                return "⚪ NON-AKTIF"

        df['status'] = df['tgl_out'].apply(calculate_status)

        # 2. Filter Pencarian
        if search_query:
            df_filtered = df[
                df['nrp'].astype(str).str.contains(search_query, case=False, na=False) | 
                df['nama'].astype(str).str.contains(search_query, case=False, na=False)
            ]
        else:
            df_filtered = df

        df_sorted = df_filtered.sort_values(by="id", ascending=False)
        st.write(f"Total data ditemukan: **{len(df_filtered)}** baris")

        # 3. Fitur Unduh Excel
        column_order_excel = [
            'tanggal', 'nrp', 'nama', 'pasal', 'sanksi', 
            'tgl_in', 'tgl_out', 'status', 'sanksi_tambahan', 
            'pelanggaran', 'pic', 'keterangan'
        ]
        avail_excel = [c for c in column_order_excel if c in df_sorted.columns]
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_sorted[avail_excel].to_excel(writer, index=False, sheet_name='Data Sanksi')

        st.download_button(
            label="📥 Download Data Terupdate ke Excel",
            data=buffer.getvalue(),
            file_name=f"Data_Sanksi_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.markdown("---")

        # 4. CSS KHUSUS UNTUK MEMAKSA TOMBOL AKSI MENJADI KECIL & PRESISI
        st.markdown("""
        <style>
            /* Menghilangkan sela antar kolom Streamlit */
            div[data-testid="stHorizontalBlock"] {
                gap: 0px !important;
                align-items: center !important;
            }
            /* Reset margin/padding elemen turunan di dalam kolom */
            div[data-testid="stHorizontalBlock"] div[data-testid="column"] {
                padding: 0px !important;
                margin: 0px !important;
            }
            div[data-testid="stElementContainer"] {
                margin: 0px !important;
                padding: 0px !important;
            }
            
            /* Styling Sel Header Tabel */
            .tbl-hdr {
                font-weight: bold;
                background-color: #f8f9fa;
                border-top: 1px solid #d0d7de;
                border-bottom: 2px solid #d0d7de;
                border-right: 1px solid #d0d7de;
                font-size: 12px;
                padding: 0px 8px;
                white-space: nowrap;
                height: 36px !important;
                line-height: 36px !important;
                box-sizing: border-box;
                width: 100%;
            }
            /* Styling Sel Data Tabel (Tinggi Kunci 36px) */
            .tbl-cell {
                padding: 0px 8px;
                border-bottom: 1px solid #e1e4e8;
                border-right: 1px solid #e1e4e8;
                font-size: 12px;
                white-space: nowrap;
                background-color: #ffffff;
                height: 36px !important;
                line-height: 36px !important;
                box-sizing: border-box;
                width: 100%;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            /* Styling Sel Aksi Admin (Menjaga garis tabel tetap utuh) */
            .tbl-cell-action {
                border-bottom: 1px solid #e1e4e8;
                border-right: 1px solid #e1e4e8;
                height: 36px !important;
                background-color: #ffffff;
                box-sizing: border-box;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 0px 2px;
            }

            /* MEMAKSA TOMBOL POPOVER BERUKURAN KECIL (HEIGHT 24px) */
            div[data-testid="stPopover"] {
                display: flex !important;
                justify-content: center !important;
                align-items: center !important;
                height: 36px !important;
            }
            div[data-testid="stPopover"] > button {
                height: 24px !important;
                min-height: 24px !important;
                max-height: 24px !important;
                line-height: 22px !important;
                padding: 0px 4px !important;
                margin: 0px !important;
                font-size: 11px !important;
                border-radius: 4px !important;
                border: 1px solid #d0d7de !important;
                background-color: #ffffff !important;
                box-shadow: none !important;
            }
            div[data-testid="stPopover"] > button:hover {
                background-color: #f3f4f6 !important;
                border-color: #0969da !important;
            }
        </style>
        """, unsafe_allow_html=True)

        # 5. SKEMA DAN PROPORSI LEBAR KOLOM
        if is_admin:
            cols_width = [1.0, 0.9, 1.4, 1.4, 1.6, 1.0, 1.0, 1.1, 1.3, 1.4, 1.4, 1.3, 0.8]
            headers = ['Tanggal', 'NRP', 'Nama', 'Pasal', 'Sanksi', 'Tgl IN', 'Tgl OUT', 'Status', 'Sanksi Tambahan', 'Pelanggaran', 'PIC', 'Keterangan', 'Aksi']
        else:
            cols_width = [1.0, 0.9, 1.4, 1.4, 1.6, 1.0, 1.0, 1.1, 1.3, 1.4, 1.4, 1.3]
            headers = ['Tanggal', 'NRP', 'Nama', 'Pasal', 'Sanksi', 'Tgl IN', 'Tgl OUT', 'Status', 'Sanksi Tambahan', 'Pelanggaran', 'PIC', 'Keterangan']

        # Render Header Tabel
        hdr_cols = st.columns(cols_width)
        for idx, h_text in enumerate(headers):
            border_left = "border-left: 1px solid #d0d7de;" if idx == 0 else ""
            hdr_cols[idx].markdown(f"<div class='tbl-hdr' style='{border_left}'>{h_text}</div>", unsafe_allow_html=True)

        # Render Baris Data
        for _, row in df_sorted.iterrows():
            row_cols = st.columns(cols_width)
            
            # Render Teks Data (Sel 0 sampai 11)
            for idx, val in enumerate([
                row.get('tanggal', ''), row.get('nrp', ''), row.get('nama', ''),
                row.get('pasal', ''), row.get('sanksi', ''), row.get('tgl_in', ''),
                row.get('tgl_out', ''), row.get('status', ''), row.get('sanksi_tambahan', ''),
                row.get('pelanggaran', ''), row.get('pic', ''), row.get('keterangan', '')
            ]):
                border_left = "border-left: 1px solid #e1e4e8;" if idx == 0 else ""
                row_cols[idx].markdown(f"<div class='tbl-cell' style='{border_left}'>{val}</div>", unsafe_allow_html=True)

            # Render Kolom Aksi Admin (Sel 12)
            if is_admin:
                row_id = row['id']
                c_edit, c_del = row_cols[12].columns(2)
                
                with c_edit:
                    with st.popover("✏️", help="Edit Data"):
                        st.subheader(f"✏️ Edit Data: {row.get('nama')}")
                        with st.form(f"form_edit_{row_id}"):
                            e_tgl = st.date_input("Tanggal Input", parse_date(row.get('tanggal')))
                            e_nrp = st.text_input("NRP", value=str(row.get('nrp', '')))
                            e_nama = st.text_input("Nama Karyawan", value=str(row.get('nama', '')))
                            e_pasal = st.text_input("Pasal Pelanggaran", value=str(row.get('pasal', '')))
                            
                            s_list = ["PERSONAL KONTAK", "PERINGATAN TERTULIS", "SP1", "SP2", "SP3", "DIKEMBALIKAN KE HC"]
                            curr_s = row.get('sanksi', "PERSONAL KONTAK")
                            e_sanksi = st.selectbox("Jenis Sanksi", s_list, index=s_list.index(curr_s) if curr_s in s_list else 0)
                            e_tgl_in = st.date_input("Tanggal IN", parse_date(row.get('tgl_in')))
                            e_tgl_out = st.date_input("Tanggal OUT", parse_date(row.get('tgl_out')))
                            e_sanksi_tambahan = st.text_input("Sanksi Tambahan", value=str(row.get('sanksi_tambahan', '')))
                            e_pelanggaran = st.text_area("Uraian Pelanggaran", value=str(row.get('pelanggaran', '')))
                            e_pic = st.text_input("PIC / Atasan", value=str(row.get('pic', '')))
                            e_ket = st.text_input("Keterangan", value=str(row.get('keterangan', '')))
                            
                            if st.form_submit_button("💾 Simpan Perubahan", type="primary", use_container_width=True):
                                upd_payload = {
                                    "tanggal": str(e_tgl), "nrp": e_nrp, "nama": e_nama, "pasal": e_pasal,
                                    "sanksi": e_sanksi, "tgl_in": str(e_tgl_in), "tgl_out": str(e_tgl_out),
                                    "sanksi_tambahan": e_sanksi_tambahan, "pelanggaran": e_pelanggaran,
                                    "pic": e_pic, "keterangan": e_ket
                                }
                                supabase.table("sanksi").update(upd_payload).eq("id", row_id).execute()
                                st.toast(f"Data {e_nama} berhasil diperbarui!", icon="✅")
                                st.rerun()

                with c_del:
                    with st.popover("🗑️", help="Hapus Data"):
                        st.warning(f"Hapus permanen sanksi **{row.get('nama')}**?")
                        if st.button("🔴 Ya, Hapus", key=f"del_{row_id}", type="primary", use_container_width=True):
                            supabase.table("sanksi").delete().eq("id", row_id).execute()
                            st.toast(f"Data ID {row_id} berhasil dihapus!", icon="🗑️")
                            st.rerun()

    else:
        st.info("Belum ada data sanksi.")
