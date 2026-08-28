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
    initial_sidebar_state="expanded"
)

# Custom CSS untuk merapatkan layout, metrik, dan input
st.markdown("""
<style>
    /* 1. Memangkas ruang kosong di bagian paling atas layar */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }

    /* 2. Styling Kartu Metrik: Angka lebih kecil & kotak lebih rapat */
    div[data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
        padding-bottom: 0px !important;
    }
    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        border: 1px solid #e1e4e8;
        border-radius: 8px;
        padding: 8px 15px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        text-align: center;
    }
    div[data-testid="stMetricLabel"] {
        justify-content: center;
        font-size: 13px !important;
        color: #57606a;
    }
    
    /* 3. Merapatkan jarak vertikal antar input */
    div[data-testid="stVerticalBlock"] {
        gap: 0.2rem !important;
    }
    
    /* Styling Container Input (Pengganti Form) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px;
        background-color: #ffffff;
    }

    /* 4. Styling Kartu Data Sanksi & Tabel */
    .stExpander {
        border: 1px solid #e1e4e8 !important;
        border-radius: 10px !important;
        background-color: #ffffff !important;
        margin-bottom: 8px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
    }
    div[data-testid="stDataFrame"] {
        border-radius: 8px;
        border: 1px solid #e1e4e8;
        display: inline-block !important;
        max-width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 1. KONEKSI SUPABASE
# -----------------------------------------------------------------------------
SUPABASE_URL = "https://zuctywyaxznjhzwckery.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp1Y3R5d3lheHpuamh6d2NrZXJ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc5MjI1OTcsImV4cCI6MjEwMzQ5ODU5N30.14uuKR3VoXkTE48jBS2NzX57NCDMwcFtXhKkLjJKJTg"

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
# 3. SIDEBAR
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

if is_admin:
    menu_options = ["Dashboard & Input", "History & Pencarian"]
else:
    menu_options = ["History & Pencarian"]

menu = st.sidebar.radio("Menu Utama", menu_options)

def parse_date(date_str):
    if not date_str or pd.isna(date_str):
        return date.today()
    try:
        return datetime.strptime(str(date_str), "%Y-%m-%d").date()
    except Exception:
        return date.today()

COLUMN_CONFIG_TABLE = {
    "tanggal": st.column_config.TextColumn("Tanggal Input", width=110),
    "nrp": st.column_config.TextColumn("NRP", width=90),
    "nama": st.column_config.TextColumn("Nama Karyawan", width=160),
    "pasal": st.column_config.TextColumn("Pasal Pelanggaran", width=150),
    "sanksi": st.column_config.TextColumn("Jenis Sanksi", width=160),
    "tgl_in": st.column_config.TextColumn("Tgl IN", width=100),
    "tgl_out": st.column_config.TextColumn("Tgl OUT", width=100),
    "status": st.column_config.TextColumn("Status", width=110),
    "sanksi_tambahan": st.column_config.TextColumn("Sanksi Tambahan", width=140),
    "pelanggaran": st.column_config.TextColumn("Uraian Pelanggaran", width=220),
    "pic": st.column_config.TextColumn("PIC / Atasan", width=140),
    "keterangan": st.column_config.TextColumn("Keterangan", width=160)
}

# -----------------------------------------------------------------------------
# 4. DASHBOARD & INPUT SANKSI
# -----------------------------------------------------------------------------
if menu == "Dashboard & Input" and is_admin:
    
    st.markdown("<h3 style='margin-top: -15px; margin-bottom: 10px;'>📊 Dashboard & Kelola Sanksi</h3>", unsafe_allow_html=True)
    
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
    
    st.markdown("<hr style='margin: 15px 0px;'>", unsafe_allow_html=True)
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

    # PERUBAHAN: Menggunakan st.container(border=True) sebagai pengganti st.form
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

        # PERUBAHAN: Menggunakan st.button sebagai pengganti st.form_submit_button
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
    
    st.markdown("<h4 style='margin-top: 15px; margin-bottom: 5px;'>📋 5 Record Terbaru</h4>", unsafe_allow_html=True)
    if not df.empty:
        df_dash = df.sort_values(by="id", ascending=False).head(5)
        df_dash_clean = df_dash.drop(columns=['id', 'created_at'], errors='ignore')
        st.dataframe(
            df_dash_clean,
            use_container_width=False,
            hide_index=True,
            column_config=COLUMN_CONFIG_TABLE
        )
    else:
        st.info("Belum ada data sanksi.")

# -----------------------------------------------------------------------------
# 5. HISTORY & PENCARIAN
# -----------------------------------------------------------------------------
elif menu == "History & Pencarian":
    st.markdown("<h3 style='margin-top: -15px;'>🔍 History & Pencarian Sanksi</h3>", unsafe_allow_html=True)
    
    res = supabase.table("sanksi").select("*").execute()
    df = pd.DataFrame(res.data)
    
    search_query = st.text_input("🔎 Cari berdasarkan NRP atau Nama Karyawan:", placeholder="Ketik nama atau NRP...")
    
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
        
        col_top1, col_top2 = st.columns([2, 1])
        with col_top1:
            st.write(f"Total data ditemukan: **{len(df_filtered)}** baris")
        with col_top2:
            view_mode = st.radio("Mode Tampilan:", ["📱 Mode Kartu (HP)", "💻 Mode Tabel (PC)"], horizontal=True)

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
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        st.markdown("---")

        if view_mode == "📱 Mode Kartu (HP)":
            for _, row in df_sorted.iterrows():
                row_id = row['id']
                nama_emp = row.get('nama', '-')
                nrp_emp = row.get('nrp', '-')
                jenis_sanksi = row.get('sanksi', '-')
                st_badge = row.get('status', '⚪ NON-AKTIF')
                tgl_input = row.get('tanggal', '-')
                
                expander_title = f"👤 {nama_emp} | NRP: {nrp_emp}  —  [{jenis_sanksi}]  {st_badge}"
                
                with st.expander(expander_title):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"<div class='detail-label'>📅 Tanggal Input</div><div class='detail-value'>{tgl_input}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='detail-label'>⚖️ Pasal Pelanggaran</div><div class='detail-value'>{row.get('pasal', '-')}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='detail-label'>⏱️ Masa Sanksi (IN - OUT)</div><div class='detail-value'>{row.get('tgl_in', '-')} s/d {row.get('tgl_out', '-')}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='detail-label'>🏷️ Status Sanksi</div><div class='detail-value'>{st_badge}</div>", unsafe_allow_html=True)
                    
                    with c2:
                        st.markdown(f"<div class='detail-label'>👤 PIC / Atasan</div><div class='detail-value'>{row.get('pic', '-')}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='detail-label'>➕ Sanksi Tambahan</div><div class='detail-value'>{row.get('sanksi_tambahan') or '-'}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='detail-label'>📌 Keterangan</div><div class='detail-value'>{row.get('keterangan') or '-'}</div>", unsafe_allow_html=True)
                    
                    st.markdown("<div class='detail-label'>⚠️ Uraian Pelanggaran:</div>", unsafe_allow_html=True)
                    st.info(row.get('pelanggaran') or "Tidak ada uraian detail.")
                    
                    if is_admin:
                        st.markdown("---")
                        col_act1, col_act2 = st.columns(2)
                        
                        with col_act1:
                            with st.popover("✏️ Edit Data Sanksi Ini", use_container_width=True):
                                st.subheader(f"✏️ Edit Data: {nama_emp}")
                                with st.form(f"form_edit_card_{row_id}"):
                                    e_tgl = st.date_input("Tanggal Input", parse_date(row.get('tanggal')))
                                    e_nrp = st.text_input("NRP", value=str(nrp_emp))
                                    e_nama = st.text_input("Nama Karyawan", value=str(nama_emp))
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

                        with col_act2:
                            with st.popover("🗑️ Hapus Data Ini", use_container_width=True):
                                st.warning(f"Hapus permanen data sanksi **{nama_emp}**?")
                                if st.button("🔴 Ya, Hapus Permanen", key=f"del_card_{row_id}", type="primary", use_container_width=True):
                                    supabase.table("sanksi").delete().eq("id", row_id).execute()
                                    st.toast(f"Data ID {row_id} berhasil dihapus!", icon="🗑️")
                                    st.rerun()

        else:
            df_table = df_sorted.drop(columns=['id', 'created_at'], errors='ignore')
            st.dataframe(
                df_table,
                use_container_width=False,
                hide_index=True,
                column_config=COLUMN_CONFIG_TABLE
            )
            
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