import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import date, datetime
import io

# -----------------------------------------------------------------------------
# KONFIGURASI HALAMAN & CUSTOM CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="OAMS - Sistem Sanksi Karyawan",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* Menyembunyikan Header, Toolbar Web, dan Ikon GitHub/Fork */
    header {visibility: hidden !important;}
    .stAppToolbar {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    
    /* Memangkas ruang kosong di bagian paling atas layar */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }

    /* Styling Kartu Statistik Kustom */
    .stat-card {
        background-color: #f8f9fa;
        border: 1px solid #e1e4e8;
        border-radius: 8px;
        padding: 10px 12px;
        text-align: center;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        margin-bottom: 8px;
    }
    .stat-label {
        font-size: 12px;
        font-weight: 600;
        color: #57606a;
        margin-bottom: 2px;
    }
    .stat-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1f2328;
        line-height: 1.2;
    }
    
    /* Merapatkan jarak vertikal antar input form */
    div[data-testid="stVerticalBlock"] {
        gap: 0.2rem !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px;
        background-color: #ffffff;
    }

    /* Memaksa Tabel Auto-Size & Fit Layar */
    div[data-testid="stDataFrame"] {
        width: 100% !important;
        border-radius: 8px;
        border: 1px solid #e1e4e8;
    }
    div[data-testid="stDataFrame"] > div {
        width: 100% !important;
    }
    
    /* Menyembunyikan Toolbar Bawaan Tabel sepenuhnya */
    div[data-testid="stElementToolbar"] {
        display: none !important;
    }
    
    /* Dropdown pagination tidak tenggelam oleh tabel */
    div[data-baseweb="select"] {
        z-index: 9999 !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 1. KONEKSI SUPABASE
# -----------------------------------------------------------------------------
SUPABASE_URL = "https://zuctywyaxznjhzwckery.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp1Y3R5d3lheHpuamh6d2NrZXJ5Iiwicm9sZSI6ImFub24iOjE3ODc5MjI1OTcsImV4cCI6MjEwMzQ5ODU5N30.14uuKR3VoXkTE48jBS2NzX57NCDMwcFtXhKkLjJKJTg"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# -----------------------------------------------------------------------------
# 2. LOAD MASTER DATA
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
# 3. HEADER & NAVIGASI UTAMA (MENGGANTIKAN SIDEBAR)
# -----------------------------------------------------------------------------
st.markdown("<h2 style='text-align: center; margin-top: -20px; margin-bottom: 5px;'>📋 OAMS System</h2>", unsafe_allow_html=True)

with st.expander("⚙️ Login & Navigasi Utama", expanded=True):
    col_nav1, col_nav2 = st.columns(2)
    
    with col_nav1:
        role = st.radio("Akses Sebagai:", ["User (Read-Only)", "Admin"], horizontal=True)
        is_admin = False
        if role == "Admin":
            password = st.text_input("Masukkan PIN Admin:", type="password")
            if password == "1234":
                is_admin = True
                st.success("✅ Akses Admin Aktif")
    
    with col_nav2:
        if is_admin:
            menu = st.radio("Menu Utama:", ["Dashboard & Input", "History & Pencarian"], horizontal=True)
        else:
            menu = "History & Pencarian"
            st.info("Mode User: Hanya dapat melihat history pencarian data.")

def parse_date(date_str):
    if not date_str or pd.isna(date_str):
        return date.today()
    try:
        return datetime.strptime(str(date_str), "%Y-%m-%d").date()
    except Exception:
        return date.today()

COLUMN_CONFIG_TABLE = {
    "tanggal": st.column_config.TextColumn("Tanggal Input"),
    "nrp": st.column_config.TextColumn("NRP"),
    "nama": st.column_config.TextColumn("Nama Karyawan"),
    "pasal": st.column_config.TextColumn("Pasal Pelanggaran"),
    "sanksi": st.column_config.TextColumn("Jenis Sanksi"),
    "tgl_in": st.column_config.TextColumn("Tgl IN"),
    "tgl_out": st.column_config.TextColumn("Tgl OUT"),
    "status": st.column_config.TextColumn("Status"),
    "sanksi_tambahan": st.column_config.TextColumn("Sanksi Tambahan"),
    "pelanggaran": st.column_config.TextColumn("Uraian Pelanggaran"),
    "pic": st.column_config.TextColumn("PIC / Atasan"),
    "keterangan": st.column_config.TextColumn("Keterangan")
}

# -----------------------------------------------------------------------------
# 4. DASHBOARD & INPUT SANKSI
# -----------------------------------------------------------------------------
if menu == "Dashboard & Input" and is_admin:
    st.markdown("---")
    res = supabase.table("sanksi").select("*").execute()
    df = pd.DataFrame(res.data)
    
    total_data = len(df) if not df.empty else 0
    sp3_count = len(df[df['sanksi'] == 'SP3']) if not df.empty and 'sanksi' in df.columns else 0
    sp1_count = len(df[df['sanksi'] == 'SP1']) if not df.empty and 'sanksi' in df.columns else 0
    pk_count = len(df[df['sanksi'] == 'PERSONAL KONTAK']) if not df.empty and 'sanksi' in df.columns else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class='stat-card'><div class='stat-label'>Total Sanksi</div><div class='stat-value'>{total_data}</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class='stat-card'><div class='stat-label'>Total SP3</div><div class='stat-value'>{sp3_count}</div></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class='stat-card'><div class='stat-label'>Total SP1</div><div class='stat-value'>{sp1_count}</div></div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class='stat-card'><div class='stat-label'>Personal Kontak</div><div class='stat-value'>{pk_count}</div></div>""", unsafe_allow_html=True)
    
    st.markdown("<hr style='margin: 10px 0px;'>", unsafe_allow_html=True)
    st.markdown("<h4 style='margin-bottom: 10px;'>📝 Form Input Sanksi Baru</h4>", unsafe_allow_html=True)
    
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

    with st.container(border=True):
        col_f1, col_f2 = st.columns(2)

        with col_f1:
            tgl = st.date_input("Tanggal Input", date.today())
            nrp = st.text_input("NRP Karyawan", key="input_nrp", on_change=auto_fill_nama, placeholder="Ketik NRP lalu tekan Enter...")
            nama = st.text_input("Nama Karyawan", key="input_nama", placeholder="Terisi otomatis jika NRP ada di master...")
            
            pasal_options = [""] + LIST_PASAL + ["+ Ketik Pasal Baru..."]
            selected_pasal = st.selectbox("Pasal Pelanggaran", options=pasal_options)
            pasal = st.text_input("Ketik Pasal Baru") if selected_pasal == "+ Ketik Pasal Baru..." else selected_pasal

            sanksi = st.selectbox("Jenis Sanksi", ["PERSONAL KONTAK", "PERINGATAN TERTULIS", "SP1", "SP2", "SP3", "DIKEMBALIKAN KE HC"])
            tgl_in = st.date_input("Tanggal IN (Mulai Sanksi)", date.today())

        with col_f2:
            tgl_out = st.date_input("Tanggal OUT (Selesai Sanksi)", date.today())
            sanksi_tambahan = st.text_input("Sanksi Tambahan", placeholder="Opsional")
            pelanggaran = st.text_area("Uraian Pelanggaran")

            pic_options = [""] + LIST_PIC + ["+ Ketik PIC Baru..."]
            selected_pic = st.selectbox("PIC / Atasan", options=pic_options)
            pic = st.text_input("Ketik PIC Baru") if selected_pic == "+ Ketik PIC Baru..." else selected_pic

            ket = st.text_input("Keterangan Tambahan")

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
# 5. HISTORY & PENCARIAN (FITUR PAGINATION & TABEL ADAPTIF)
# -----------------------------------------------------------------------------
elif menu == "History & Pencarian":
    st.markdown("---")
    
    res = supabase.table("sanksi").select("*").execute()
    df = pd.DataFrame(res.data)
    
    if "last_search" not in st.session_state:
        st.session_state.last_search = ""
        
    search_query = st.text_input("🔎 Cari berdasarkan NRP atau Nama Karyawan:", placeholder="Ketik nama atau NRP...")
    
    if search_query != st.session_state.last_search:
        st.session_state.current_page = 0
        st.session_state.last_search = search_query
    
    if not df.empty:
        today_date = date.today()
        
        def calculate_status(tgl_out_val):
            try:
                t_out = datetime.strptime(str(tgl_out_val), "%Y-%m-%d").date()
                return "🔴 AKTIF" if today_date <= t_out else "⚪ NON-AKTIF"
            except Exception:
                return "⚪ NON-AKTIF"

        df['status'] = df['tgl_out'].apply(calculate_status)

        if search_query:
            df_filtered = df[
                df['nrp'].astype(str).str.contains(search_query, case=False, na=False) | 
                df['nama'].astype(str).str.contains(search_query, case=False, na=False)
            ]
        else:
            df_filtered = df

        df_sorted = df_filtered.sort_values(by="id", ascending=False)
        total_rows = len(df_sorted)

        # DOWNLOAD EXCEL (Selalu mengunduh semua 12 kolom secara utuh)
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
            label="📥 Download Data Excel (Semua Kolom)",
            data=buffer.getvalue(),
            file_name=f"Data_Sanksi_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        col_t1, col_t2 = st.columns([1, 1])
        with col_t1:
            st.write(f"Total data: **{total_rows}** baris")
        with col_t2:
            show_all_cols = st.toggle("Tampilkan Semua 12 Kolom (Mode Geser)")

        # =====================================================================
        # LOGIKA PAGINATION (10, 50, 100, ALL)
        # =====================================================================
        if "current_page" not in st.session_state:
            st.session_state.current_page = 0
            
        page_options = [10, 50, 100, "All"]
        col_p1, col_p2 = st.columns([1, 3])
        with col_p1:
            selected_size = st.selectbox("Tampilkan baris:", page_options, index=0)
            
        page_size_val = total_rows if selected_size == "All" else int(selected_size)
        
        if total_rows == 0:
            total_pages = 1
        else:
            total_pages = (total_rows - 1) // page_size_val + 1 if page_size_val > 0 else 1
            
        if st.session_state.current_page >= total_pages:
            st.session_state.current_page = 0
            
        start_idx = st.session_state.current_page * page_size_val
        end_idx = start_idx + page_size_val
        df_display = df_sorted.iloc[start_idx:end_idx]

        # FILTER KOLOM: Jika tidak ditoggle, hanya tampilkan 4 kolom inti agar muat penuh di HP
        if show_all_cols:
            df_table = df_display.drop(columns=['id', 'created_at'], errors='ignore')
        else:
            core_cols = ['nama', 'pasal', 'sanksi', 'status']
            avail_core = [c for c in core_cols if c in df_display.columns]
            df_table = df_display[avail_core]

        # RENDER TABEL
        st.dataframe(
            df_table,
            use_container_width=True,
            hide_index=True,
            column_config=COLUMN_CONFIG_TABLE
        )
        
        # RENDER TOMBOL BACK & NEXT
        if selected_size != "All" and total_pages > 1:
            col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
            with col_b1:
                if st.button("⬅️ Back", use_container_width=True, disabled=(st.session_state.current_page == 0)):
                    st.session_state.current_page -= 1
                    st.rerun()
            with col_b2:
                st.markdown(f"<div style='text-align:center; padding-top: 5px; font-weight:bold; color: #57606a;'>Halaman {st.session_state.current_page + 1} dari {total_pages}</div>", unsafe_allow_html=True)
            with col_b3:
                if st.button("Next ➡️", use_container_width=True, disabled=(st.session_state.current_page >= total_pages - 1)):
                    st.session_state.current_page += 1
                    st.rerun()

        # =====================================================================
        # PANEL KHUSUS ADMIN (EDIT / HAPUS)
        # =====================================================================
        if is_admin:
            st.markdown("---")
            st.subheader("🛠️ Panel Edit / Hapus Data (Khusus Admin)")
            st.caption("Ketik NRP atau Nama karyawan untuk menampilkan daftar riwayat data yang ingin diubah atau dihapus.")
            
            search_admin = st.text_input("🔎 Ketik NRP / Nama Karyawan untuk Edit / Hapus:", placeholder="Contoh: 0211002", key="search_admin_input")
            
            if search_admin:
                df_admin_target = df_sorted[
                    df_sorted['nrp'].astype(str).str.contains(search_admin, case=False, na=False) | 
                    df_sorted['nama'].astype(str).str.contains(search_admin, case=False, na=False)
                ]
            else:
                df_admin_target = pd.DataFrame()

            if search_admin and df_admin_target.empty:
                st.warning(f"Tidak ditemukan data sanksi dengan NRP / Nama: **{search_admin}**")
            elif not search_admin:
                st.info("💡 Masukkan NRP atau Nama Karyawan di atas untuk memunculkan daftar opsi edit dan hapus.")
            else:
                st.write(f"Ditemukan **{len(df_admin_target)}** data untuk target **{search_admin}**:")
                
                for _, row_target in df_admin_target.iterrows():
                    target_id = row_target['id']
                    t_nrp = row_target.get('nrp', '-')
                    t_nama = row_target.get('nama', '-')
                    t_sanksi = row_target.get('sanksi', '-')
                    t_tgl = row_target.get('tanggal', '-')
                    t_pasal = row_target.get('pasal', '-')
                    t_status = row_target.get('status', '-')

                    with st.container(border=True):
                        c_info, c_btn_edit, c_btn_del = st.columns([6, 2, 2])
                        
                        with c_info:
                            st.markdown(
                                f"**📅 {t_tgl}** | **NRP:** {t_nrp} - **{t_nama}** | **[{t_sanksi}]** `{t_status}`  \n"
                                f"<small>Pasal: {t_pasal} | PIC: {row_target.get('pic', '-')}</small>", 
                                unsafe_allow_html=True
                            )
                        
                        with c_btn_edit:
                            with st.popover("✏️ Edit Data", use_container_width=True):
                                st.subheader(f"✏️ Edit Data: {t_nama}")
                                with st.form(f"form_edit_panel_{target_id}"):
                                    e_tgl = st.date_input("Tanggal Input", parse_date(row_target.get('tanggal')))
                                    e_nrp = st.text_input("NRP", value=str(t_nrp))
                                    e_nama = st.text_input("Nama Karyawan", value=str(t_nama))
                                    e_pasal = st.text_input("Pasal Pelanggaran", value=str(row_target.get('pasal', '')))
                                    
                                    s_list = ["PERSONAL KONTAK", "PERINGATAN TERTULIS", "SP1", "SP2", "SP3", "DIKEMBALIKAN KE HC"]
                                    curr_s = row_target.get('sanksi', "PERSONAL KONTAK")
                                    e_sanksi = st.selectbox("Jenis Sanksi", s_list, index=s_list.index(curr_s) if curr_s in s_list else 0)
                                    
                                    e_tgl_in = st.date_input("Tanggal IN", parse_date(row_target.get('tgl_in')))
                                    e_tgl_out = st.date_input("Tanggal OUT", parse_date(row_target.get('tgl_out')))
                                    e_sanksi_tambahan = st.text_input("Sanksi Tambahan", value=str(row_target.get('sanksi_tambahan', '')))
                                    e_pelanggaran = st.text_area("Uraian Pelanggaran", value=str(row_target.get('pelanggaran', '')))
                                    e_pic = st.text_input("PIC / Atasan", value=str(row_target.get('pic', '')))
                                    e_ket = st.text_input("Keterangan", value=str(row_target.get('keterangan', '')))
                                    
                                    if st.form_submit_button("💾 Simpan Perubahan", type="primary", use_container_width=True):
                                        upd_payload = {
                                            "tanggal": str(e_tgl), "nrp": e_nrp, "nama": e_nama, "pasal": e_pasal,
                                            "sanksi": e_sanksi, "tgl_in": str(e_tgl_in), "tgl_out": str(e_tgl_out),
                                            "sanksi_tambahan": e_sanksi_tambahan, "pelanggaran": e_pelanggaran,
                                            "pic": e_pic, "keterangan": e_ket
                                        }
                                        supabase.table("sanksi").update(upd_payload).eq("id", target_id).execute()
                                        st.toast(f"Data {e_nama} berhasil diperbarui!", icon="✅")
                                        st.rerun()
                                        
                        with c_btn_del:
                            with st.popover("🗑️ Hapus", use_container_width=True):
                                st.warning(f"Hapus permanen sanksi **{t_nama}** (ID: {target_id})?")
                                if st.button("🔴 Ya, Hapus", key=f"del_panel_{target_id}", type="primary", use_container_width=True):
                                    supabase.table("sanksi").delete().eq("id", target_id).execute()
                                    st.toast(f"Data ID {target_id} berhasil dihapus!", icon="🗑️")
                                    st.rerun()

    else:
        st.info("Belum ada data sanksi.")