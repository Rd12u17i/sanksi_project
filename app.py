import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import date, datetime
import io
import html

# -----------------------------------------------------------------------------
# KONFIGURASI HALAMAN
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="OAMS - Sistem Sanksi Karyawan",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# CUSTOM CSS
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    .block-container { padding-top: 0.8rem !important; padding-bottom: 1rem !important; max-width: 100% !important; }
    div[data-testid="stVerticalBlock"] { gap: 0.2rem !important; }
    div[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 12px; background-color: #ffffff; }
    .stats-row { display: grid; grid-template-columns: repeat(8, 1fr); gap: 8px; width: 100%; margin: 5px 0 15px 0; }
    .stat-card { background: #f8f9fa; border: 1px solid #e1e4e8; border-radius: 8px; padding: 8px 4px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.06); display: flex; flex-direction: column; justify-content: center; align-items: center; }
    .stat-label { font-size: 11px; line-height: 1.15; font-weight: 600; color: #57606a; margin-bottom: 4px; display: flex; align-items: center; justify-content: center; text-align: center; height: 26px; white-space: normal; }
    .stat-value { font-size: 18px; font-weight: 700; color: #1f2328; }
    .table-wrapper { width: 100%; max-width: 100%; overflow: hidden; border: 1px solid #d0d7de; border-radius: 8px; background: #ffffff; box-sizing: border-box; }
    .oams-table { width: 100%; max-width: 100%; border-collapse: collapse; table-layout: fixed; font-size: clamp(6px, 0.82vw, 11px); line-height: 1.2; }
    .oams-table th, .oams-table td { border: 1px solid #d8dee4; padding: 4px 3px; vertical-align: top; overflow-wrap: anywhere; word-break: break-word; white-space: normal; box-sizing: border-box; }
    .oams-table th { background: #f6f8fa; font-weight: 700; text-align: center; vertical-align: middle; }
    .oams-table td { text-align: left; }
    .oams-table tbody tr:nth-child(even) { background: #fbfcfd; }
    .oams-table .center { text-align: center; }
    .oams-table .status { text-align: center; font-weight: 700; }
    .col-tanggal { width: 7%; } .col-nrp { width: 7%; } .col-nama { width: 11%; } .col-pasal { width: 10%; } .col-sanksi { width: 10%; } .col-tglin { width: 7%; } .col-tglout { width: 7%; } .col-status { width: 7%; } .col-tambahan { width: 9%; } .col-pelanggaran { width: 14%; } .col-pic { width: 6%; } .col-ket { width: 5%; }
    .table-info { font-size: 12px; color: #57606a; margin: 3px 0 6px 0; }
    @media (max-width: 800px) { .stats-row { grid-template-columns: repeat(4, 1fr); gap: 6px; } }
    @media (max-width: 600px) { .stats-row { grid-template-columns: repeat(4, 1fr); gap: 4px; } .stat-card { padding: 5px 2px; border-radius: 6px; } .stat-label { font-size: 9px; height: 24px; } .stat-value { font-size: 14px; } .table-wrapper { border-radius: 5px; } .oams-table { font-size: 6px; } .oams-table th, .oams-table td { padding: 2px 2px; } }
    .stExpander { border: 1px solid #e1e4e8 !important; border-radius: 10px !important; background-color: #ffffff !important; margin-bottom: 8px !important; }
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

try:
    supabase: Client = init_supabase()
except Exception as e:
    st.error(f"Gagal terhubung ke Supabase: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# 2. LOAD DATA DENGAN PAGINASI (AGAR BISA AMBIL > 1000 DATA)
# -----------------------------------------------------------------------------
def fetch_all_data(table, columns="*"):
    """Helper untuk mengambil semua data melewati limit 1000 row Supabase."""
    res_data = []
    limit = 1000
    offset = 0
    while True:
        try:
            res = supabase.table(table).select(columns).range(offset, offset + limit - 1).execute()
            data = res.data or []
            res_data.extend(data)
            if len(data) < limit:
                break
            offset += limit
        except Exception as e:
            st.error(f"Gagal mengambil data dari {table}: {e}")
            break
    return res_data

@st.cache_data(ttl=60)
def load_all_sanksi():
    data = fetch_all_data("sanksi")
    return pd.DataFrame(data)

@st.cache_data(ttl=300)
def load_supabase_master():
    master_karyawan = {}
    list_pasal = set()
    list_pic = set()

    for r in fetch_all_data("master_karyawan", "nrp, nama"):
        if r.get("nrp") and r.get("nama"):
            master_karyawan[str(r["nrp"]).strip()] = str(r["nama"]).strip()

    for r in fetch_all_data("master_pasal", "pasal"):
        if r.get("pasal"): list_pasal.add(str(r["pasal"]).strip())

    for r in fetch_all_data("master_pic", "nama_pic"):
        if r.get("nama_pic"): list_pic.add(str(r["nama_pic"]).strip())

    # Update master dari tabel sanksi berjalan
    for r in fetch_all_data("sanksi", "nrp, nama, pasal, pic"):
        if r.get("nrp") and r.get("nama"):
            master_karyawan[str(r["nrp"]).strip()] = str(r["nama"]).strip()
        if r.get("pasal"): list_pasal.add(str(r["pasal"]).strip())
        if r.get("pic"): list_pic.add(str(r["pic"]).strip())

    return master_karyawan, sorted(list(list_pasal)), sorted(list(list_pic))

MASTER_KARYAWAN, LIST_PASAL, LIST_PIC = load_supabase_master()

# -----------------------------------------------------------------------------
# 3. FUNGSI BANTU
# -----------------------------------------------------------------------------
def parse_date(value):
    if value is None or pd.isna(value) or str(value).strip() == "": return date.today()
    if isinstance(value, datetime): return value.date()
    if isinstance(value, date): return value
    parsed = pd.to_datetime(str(value), errors="coerce")
    if pd.isna(parsed): return date.today()
    return parsed.date()

def normalize_text(value):
    if value is None: return ""
    return " ".join(str(value).strip().lower().split())

def clean_excel_text(val):
    if pd.isna(val) or val is None: return ""
    return str(val).strip()

def calculate_status(value):
    t_out = pd.to_datetime(value, errors="coerce")
    if pd.isna(t_out): return "⚪ NON-AKTIF"
    return "🔴 AKTIF" if date.today() <= t_out.date() else "⚪ NON-AKTIF"

def check_duplicate_manual(df, nrp, sanksi, tgl_in, pelanggaran, exclude_id=None):
    if df.empty: return False
    temp = df.copy()
    if exclude_id is not None and "id" in temp.columns: temp = temp[temp["id"] != exclude_id]
    
    mask = (
        temp["nrp"].map(normalize_text).eq(normalize_text(nrp))
        & temp["sanksi"].map(normalize_text).eq(normalize_text(sanksi))
        & temp["tgl_in"].map(lambda x: parse_date(x).isoformat()).eq(parse_date(tgl_in).isoformat())
        & temp["pelanggaran"].map(normalize_text).eq(normalize_text(pelanggaran))
    )
    return bool(mask.any())

def remove_duplicate_dicts(dict_list, key):
    seen = set()
    res = []
    for d in dict_list:
        if d[key] not in seen:
            seen.add(d[key])
            res.append(d)
    return res

# -----------------------------------------------------------------------------
# 4. TABEL RESPONSIVE HTML
# -----------------------------------------------------------------------------
TABLE_COLUMNS = [
    ("tanggal", "Tanggal", "col-tanggal"), ("nrp", "NRP", "col-nrp"), ("nama", "Nama Karyawan", "col-nama"),
    ("pasal", "Pasal", "col-pasal"), ("sanksi", "Jenis Sanksi", "col-sanksi"), ("tgl_in", "Tgl IN", "col-tglin"),
    ("tgl_out", "Tgl OUT", "col-tglout"), ("status", "Status", "col-status"), ("sanksi_tambahan", "Sanksi Tambahan", "col-tambahan"),
    ("pelanggaran", "Uraian Pelanggaran", "col-pelanggaran"), ("pic", "PIC / Atasan", "col-pic"), ("keterangan", "Keterangan", "col-ket"),
]

def display_value(value):
    if value is None or (isinstance(value, float) and pd.isna(value)): return "-"
    text = str(value).strip()
    return text if text else "-"

def render_html_table(df):
    if df.empty:
        st.info("Belum ada data sanksi.")
        return

    header = "".join(f"<th class='{css_class}'>{html.escape(label)}</th>" for _, label, css_class in TABLE_COLUMNS)
    rows = []
    for _, row in df.iterrows():
        cells = []
        for key, _, css_class in TABLE_COLUMNS:
            value = display_value(row.get(key, "-"))
            if key == "status": cell = f"<td class='{css_class} status'>{html.escape(value)}</td>"
            elif key in ("nrp", "tanggal", "tgl_in", "tgl_out"): cell = f"<td class='{css_class} center'>{html.escape(value)}</td>"
            else: cell = f"<td class='{css_class}'>{html.escape(value)}</td>"
            cells.append(cell)
        rows.append("<tr>" + "".join(cells) + "</tr>")

    table_html = f"""<div class="table-wrapper"><table class="oams-table"><thead><tr>{header}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"""
    st.markdown(table_html, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. SIDEBAR
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
menu_options = ["Dashboard & Input", "History & Pencarian"] if is_admin else ["History & Pencarian"]
menu = st.sidebar.radio("Menu Utama", menu_options)

# -----------------------------------------------------------------------------
# 6. DASHBOARD & INPUT ADMIN
# -----------------------------------------------------------------------------
if menu == "Dashboard & Input" and is_admin:

    st.markdown("<h3 style='margin-top:-12px;margin-bottom:7px;'>📊 Dashboard & Kelola Sanksi</h3>", unsafe_allow_html=True)

    df_all = load_all_sanksi()

    # KARTU STATISTIK
    total_data = len(df_all) if not df_all.empty else 0
    if not df_all.empty and "sanksi" in df_all.columns:
        pk_count = int((df_all["sanksi"] == "PERSONAL KONTAK").sum())
        pt_count = int((df_all["sanksi"] == "PERINGATAN TERTULIS").sum())
        sp1_count = int((df_all["sanksi"] == "SP1").sum())
        sp2_count = int((df_all["sanksi"] == "SP2").sum())
        sp3_count = int((df_all["sanksi"] == "SP3").sum())
        sppt_count = int((df_all["sanksi"] == "SP PERTAMA & TERAKHIR").sum())
        hc_count = int((df_all["sanksi"] == "DIKEMBALIKAN KE HC").sum())
    else:
        pk_count = pt_count = sp1_count = sp2_count = sp3_count = sppt_count = hc_count = 0

    stats = [
        ("Total Sanksi", total_data), ("Personal Kontak", pk_count),
        ("Peringatan Tertulis", pt_count), ("SP 1", sp1_count),
        ("SP 2", sp2_count), ("SP 3", sp3_count),
        ("SP Pertama & Terakhir", sppt_count), ("Dikembalikan HC", hc_count),
    ]
    cards = "".join(f"<div class='stat-card'><div class='stat-label'>{html.escape(label)}</div><div class='stat-value'>{value}</div></div>" for label, value in stats)
    st.markdown(f"<div class='stats-row'>{cards}</div>", unsafe_allow_html=True)
    st.markdown("<hr style='margin:7px 0px;'>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # TABS & FORM
    # -------------------------------------------------------------------------
    st.markdown("<h4 style='margin-bottom:7px;'>📝 Form Input Sanksi</h4>", unsafe_allow_html=True)
    tab_manual, tab_excel = st.tabs(["📝 Input Manual", "📂 Upload Excel (SBook1.xlsx)"])

    # TAB 1: INPUT MANUAL
    with tab_manual:
        if "input_form_version" not in st.session_state: st.session_state.input_form_version = 0
        form_version = st.session_state.input_form_version

        def auto_fill_nama():
            nrp_key = f"input_nrp_{form_version}"
            nama_key = f"input_nama_{form_version}"
            typed_nrp = str(st.session_state.get(nrp_key, "")).strip()
            st.session_state[nama_key] = MASTER_KARYAWAN.get(typed_nrp, "")

        with st.container(border=True):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                tgl = st.date_input("Tanggal Input", date.today(), key=f"input_tanggal_{form_version}")
                nrp = st.text_input("NRP Karyawan", key=f"input_nrp_{form_version}", on_change=auto_fill_nama, placeholder="Ketik NRP lalu tekan Enter...")
                nama = st.text_input("Nama Karyawan", key=f"input_nama_{form_version}", placeholder="Terisi otomatis jika NRP ada di master...")
                pasal_options = [""] + LIST_PASAL + ["+ Ketik Pasal Baru..."]
                selected_pasal = st.selectbox("Pasal Pelanggaran", options=pasal_options, key=f"input_selected_pasal_{form_version}")
                pasal = st.text_input("Ketik Pasal Baru", key=f"input_pasal_baru_{form_version}") if selected_pasal == "+ Ketik Pasal Baru..." else selected_pasal
                sanksi = st.selectbox("Jenis Sanksi", ["PERSONAL KONTAK", "PERINGATAN TERTULIS", "SP1", "SP2", "SP3", "SP PERTAMA & TERAKHIR", "DIKEMBALIKAN KE HC"], key=f"input_sanksi_{form_version}")
                tgl_in = st.date_input("Tanggal IN (Mulai Sanksi)", date.today(), key=f"input_tgl_in_{form_version}")
            with col_f2:
                tgl_out = st.date_input("Tanggal OUT (Selesai Sanksi)", date.today(), key=f"input_tgl_out_{form_version}")
                sanksi_tambahan = st.text_input("Sanksi Tambahan", placeholder="Opsional", key=f"input_tambahan_{form_version}")
                pelanggaran = st.text_area("Uraian Pelanggaran", key=f"input_pelanggaran_{form_version}")
                pic_options = [""] + LIST_PIC + ["+ Ketik PIC Baru..."]
                selected_pic = st.selectbox("PIC / Atasan", options=pic_options, key=f"input_selected_pic_{form_version}")
                pic = st.text_input("Ketik PIC Baru", key=f"input_pic_baru_{form_version}") if selected_pic == "+ Ketik PIC Baru..." else selected_pic
                ket = st.text_input("Keterangan Tambahan", key=f"input_keterangan_{form_version}")

            if st.button("💾 Simpan Data Sanksi", type="primary", use_container_width=True, key=f"save_button_{form_version}"):
                if not nrp.strip() or not nama.strip(): st.error("❌ NRP dan Nama Karyawan wajib diisi!"); st.stop()
                if not str(pelanggaran).strip(): st.error("❌ Uraian Pelanggaran wajib diisi!"); st.stop()
                if check_duplicate_manual(df_all, nrp=nrp, sanksi=sanksi, tgl_in=tgl_in, pelanggaran=pelanggaran):
                    st.error("⚠️ Data sudah ada! NRP, Jenis Sanksi, Tanggal IN, dan Uraian Pelanggaran sama dengan data yang tersimpan.")
                    st.stop()

                payload = {
                    "tanggal": str(tgl), "nrp": nrp.strip(), "nama": nama.strip(),
                    "pasal": str(pasal).strip(), "sanksi": sanksi, "tgl_in": str(tgl_in),
                    "tgl_out": str(tgl_out), "sanksi_tambahan": str(sanksi_tambahan).strip(),
                    "pelanggaran": str(pelanggaran).strip(), "pic": str(pic).strip(), "keterangan": str(ket).strip(),
                }
                try:
                    supabase.table("sanksi").insert(payload).execute()
                    if nrp.strip() not in MASTER_KARYAWAN: supabase.table("master_karyawan").insert({"nrp": nrp.strip(), "nama": nama.strip()}).execute()
                    if selected_pasal == "+ Ketik Pasal Baru..." and str(pasal).strip(): supabase.table("master_pasal").insert({"pasal": str(pasal).strip()}).execute()
                    if selected_pic == "+ Ketik PIC Baru..." and str(pic).strip(): supabase.table("master_pic").insert({"nama_pic": str(pic).strip()}).execute()
                except Exception as e:
                    st.error(f"❌ Gagal menyimpan data: {e}"); st.stop()

                st.cache_data.clear()
                st.session_state.input_form_version += 1
                st.toast(f"✅ Berhasil menyimpan sanksi untuk {nama.strip()}!", icon="✅")
                st.rerun()

    # TAB 2: UPLOAD EXCEL (BULK INSERT + ANIMASI LOADING)
    with tab_excel:
        with st.container(border=True):
            st.markdown("Unggah file Excel (`SBook1.xlsx`). Sistem otomatis mengambil **Nama** dari database web (Master) jika NRP cocok. **Batas hingga puluhan ribu baris!**")
            uploaded_file = st.file_uploader("Upload File Excel", type=["xlsx", "xls"])
            
            if uploaded_file is not None:
                try:
                    df_upload = pd.read_excel(uploaded_file)
                    total_excel_rows = len(df_upload)
                    st.write(f"📊 **Total baris terbaca dalam file:** `{total_excel_rows}` baris")

                    if st.button("🚀 Proses & Unggah Semua Data", type="primary", use_container_width=True):
                        with st.spinner(f"Memproses {total_excel_rows} baris... Mohon tunggu!"):
                            # 1. Siapkan Set Duplikat Super Cepat (O(1) Search)
                            existing_set = set()
                            if not df_all.empty:
                                for _, r in df_all.iterrows():
                                    k = (
                                        normalize_text(r.get('nrp')),
                                        normalize_text(r.get('sanksi')),
                                        parse_date(r.get('tgl_in')).isoformat(),
                                        normalize_text(r.get('pelanggaran'))
                                    )
                                    existing_set.add(k)

                            success_count = 0
                            error_count = 0
                            duplicate_count = 0
                            
                            payloads_to_insert = []
                            new_karyawan_to_insert = []
                            new_pasal_to_insert = []
                            new_pic_to_insert = []

                            progress_bar = st.progress(0, text="Mengumpulkan data valid...")

                            for index, row in df_upload.iterrows():
                                raw_nrp = clean_excel_text(row.get('NRP'))
                                if not raw_nrp or raw_nrp.lower() == 'nan':
                                    error_count += 1
                                    continue

                                raw_nama_excel = clean_excel_text(row.get('NAMA'))
                                nama_final = MASTER_KARYAWAN.get(raw_nrp, raw_nama_excel)
                                
                                raw_tanggal = parse_date(row.get('TANGGAL'))
                                raw_tgl_in = parse_date(row.get('AWAL'))
                                raw_tgl_out = parse_date(row.get('AKHIR'))
                                
                                raw_sanksi = clean_excel_text(row.get('JENIS SANKSI')).upper()
                                if raw_sanksi == "SP 1": raw_sanksi = "SP1"
                                if raw_sanksi == "SP 2": raw_sanksi = "SP2"
                                if raw_sanksi == "SP 3": raw_sanksi = "SP3"
                                
                                raw_pasal = clean_excel_text(row.get('PASAL'))
                                raw_tambahan = clean_excel_text(row.get('SANKSI TAMBAHAN'))
                                raw_pelanggaran = clean_excel_text(row.get('PELANGGARAN'))
                                raw_pic = clean_excel_text(row.get('PIC'))
                                raw_ket = clean_excel_text(row.get('KETERANGAN'))

                                # Cek Duplikat dengan Set
                                chk_key = (
                                    normalize_text(raw_nrp),
                                    normalize_text(raw_sanksi),
                                    raw_tgl_in.isoformat(),
                                    normalize_text(raw_pelanggaran)
                                )
                                if chk_key in existing_set:
                                    duplicate_count += 1
                                    continue
                                
                                # Tambahkan ke set agar tidak duplikat dengan baris selanjutnya di dalam excel itu sendiri
                                existing_set.add(chk_key)
                                
                                payloads_to_insert.append({
                                    "tanggal": str(raw_tanggal), "nrp": raw_nrp, "nama": nama_final,
                                    "pasal": raw_pasal, "sanksi": raw_sanksi, "tgl_in": str(raw_tgl_in),
                                    "tgl_out": str(raw_tgl_out), "sanksi_tambahan": raw_tambahan,
                                    "pelanggaran": raw_pelanggaran, "pic": raw_pic, "keterangan": raw_ket,
                                })

                                # Siapkan Master Baru
                                if raw_nrp not in MASTER_KARYAWAN and nama_final:
                                    new_karyawan_to_insert.append({"nrp": raw_nrp, "nama": nama_final})
                                    MASTER_KARYAWAN[raw_nrp] = nama_final
                                if raw_pasal and raw_pasal not in LIST_PASAL:
                                    new_pasal_to_insert.append({"pasal": raw_pasal})
                                    LIST_PASAL.append(raw_pasal)
                                if raw_pic and raw_pic not in LIST_PIC:
                                    new_pic_to_insert.append({"nama_pic": raw_pic})
                                    LIST_PIC.append(raw_pic)

                            # 2. BULK INSERT (Batching per 1000 data agar tidak Timeout)
                            total_valid = len(payloads_to_insert)
                            if total_valid > 0:
                                chunk_size = 1000
                                for i in range(0, total_valid, chunk_size):
                                    batch = payloads_to_insert[i:i+chunk_size]
                                    try:
                                        supabase.table("sanksi").insert(batch).execute()
                                        success_count += len(batch)
                                    except Exception as e:
                                        st.error(f"Gagal upload sebagian data: {e}")
                                    
                                    progress_bar.progress((i + len(batch)) / total_valid, text=f"Sedang mengunggah... {success_count}/{total_valid}")

                                # Insert Master (Hapus duplikat master di dictionary sebelum dikirim)
                                try:
                                    if new_karyawan_to_insert:
                                        for i in range(0, len(new_karyawan_to_insert), chunk_size):
                                            supabase.table("master_karyawan").insert(remove_duplicate_dicts(new_karyawan_to_insert[i:i+chunk_size], "nrp")).execute()
                                    if new_pasal_to_insert:
                                        for i in range(0, len(new_pasal_to_insert), chunk_size):
                                            supabase.table("master_pasal").insert(remove_duplicate_dicts(new_pasal_to_insert[i:i+chunk_size], "pasal")).execute()
                                    if new_pic_to_insert:
                                        for i in range(0, len(new_pic_to_insert), chunk_size):
                                            supabase.table("master_pic").insert(remove_duplicate_dicts(new_pic_to_insert[i:i+chunk_size], "nama_pic")).execute()
                                except: pass # Abaikan error master

                            st.success(f"✅ Upload Selesai! Berhasil: **{success_count} baris** | Duplikat dilewati: **{duplicate_count} baris** | Error/Baris Kosong: **{error_count} baris**")
                            st.balloons()
                            st.cache_data.clear()
                            
                            if st.button("🔄 Klik Disini Untuk Segarkan Dashboard"):
                                st.rerun()

                except Exception as e:
                    st.error(f"Gagal memproses file excel: {e}")

    # -------------------------------------------------------------------------
    # HAPUS SEMUA DATA (DANGER ZONE)
    # -------------------------------------------------------------------------
    st.markdown("---")
    with st.expander("⚠️ Hapus Semua Data Sanksi (DANGER ZONE)", expanded=False):
        st.warning("PERINGATAN: Tindakan ini akan menghapus SELURUH data sanksi di database dan tidak dapat dibatalkan!")
        del_pass = st.text_input("Ketik sandi khusus untuk melanjutkan:", type="password", key="delete_all_pass")
        if del_pass == "hapus":
            if st.button("🔴 KONFIRMASI HAPUS SEMUA DATA", type="primary", use_container_width=True):
                with st.spinner("Sedang menghapus data... Mohon tunggu."):
                    try:
                        # Menggunakan logic neq dummy value untuk menghapus seluruh row dalam tabel
                        supabase.table("sanksi").delete().neq("nrp", "DUMMY_XXX_123").execute()
                        st.success("✅ Seluruh data sanksi berhasil dikosongkan!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Gagal menghapus: {e}")

    # -------------------------------------------------------------------------
    # RECORD TERBARU
    # -------------------------------------------------------------------------
    st.markdown("<h4 style='margin-top:10px;margin-bottom:4px;'>📋 10 Record Terbaru</h4>", unsafe_allow_html=True)
    if not df_all.empty:
        df_dash = df_all.sort_values(by="id", ascending=False).head(10) if "id" in df_all.columns else df_all.head(10)
        df_dash = df_dash.copy()
        if "status" in df_dash.columns: df_dash["status"] = df_dash["tgl_out"].apply(calculate_status)
        render_html_table(df_dash)
    else:
        st.info("Belum ada data sanksi.")

# -----------------------------------------------------------------------------
# 7. HISTORY & PENCARIAN
# -----------------------------------------------------------------------------
elif menu == "History & Pencarian":
    st.markdown("<h3 style='margin-top:-12px;margin-bottom:7px;'>🔍 History & Pencarian Sanksi</h3>", unsafe_allow_html=True)
    df = load_all_sanksi()

    if not df.empty:
        df["status"] = df["tgl_out"].apply(calculate_status) if "tgl_out" in df.columns else "⚪ NON-AKTIF"
        search_query = st.text_input("🔎 Cari berdasarkan NRP atau Nama Karyawan:", placeholder="Ketik nama atau NRP...")
        
        if search_query:
            q = str(search_query).strip()
            df_filtered = df[df["nrp"].astype(str).str.contains(q, case=False, na=False) | df["nama"].astype(str).str.contains(q, case=False, na=False)].copy()
        else:
            df_filtered = df.copy()

        df_sorted = df_filtered.sort_values(by="id", ascending=False).copy() if "id" in df_filtered.columns else df_filtered.copy()
        
        col_top1, col_top2 = st.columns([2, 1])
        with col_top1: st.markdown(f"<div style='padding-top:8px;'>Total data ditemukan: <b>{len(df_sorted)}</b> baris</div>", unsafe_allow_html=True)
        with col_top2: page_size = st.selectbox("Jumlah baris:", ["10", "50", "100", "All"], index=0, key="history_page_size")

        df_display = df_sorted if page_size == "All" else df_sorted.head(int(page_size))
        if page_size != "All":
            st.markdown(f"<div class='table-info'>Menampilkan <b>{len(df_display)}</b> dari <b>{len(df_sorted)}</b> data</div>", unsafe_allow_html=True)

        column_order_excel = ["tanggal", "nrp", "nama", "pasal", "sanksi", "tgl_in", "tgl_out", "status", "sanksi_tambahan", "pelanggaran", "pic", "keterangan"]
        avail_excel = [c for c in column_order_excel if c in df_sorted.columns]

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_sorted[avail_excel].to_excel(writer, index=False, sheet_name="Data Sanksi")
        st.download_button(label="📥 Download Data Terupdate ke Excel", data=buffer.getvalue(), file_name=f"Data_Sanksi_{date.today()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        
        st.markdown("<div style='height:5px'></div>", unsafe_allow_html=True)
        render_html_table(df_display)

        # PANEL EDIT / HAPUS PER DATA
        if is_admin:
            st.markdown("---")
            st.subheader("🛠️ Panel Edit / Hapus Per Data")
            search_admin = st.text_input("🔎 Ketik NRP / Nama Karyawan untuk Edit / Hapus:", placeholder="Contoh: 0211002", key="search_admin_input")

            if search_admin:
                q_admin = str(search_admin).strip()
                df_admin_target = df_sorted[df_sorted["nrp"].astype(str).str.contains(q_admin, case=False, na=False) | df_sorted["nama"].astype(str).str.contains(q_admin, case=False, na=False)].copy()
                
                if df_admin_target.empty:
                    st.warning(f"Tidak ditemukan data sanksi dengan NRP / Nama: **{search_admin}**")
                else:
                    st.write(f"Ditemukan **{len(df_admin_target)}** data untuk target **{search_admin}**:")
                    for _, row_target in df_admin_target.iterrows():
                        target_id = row_target.get("id")
                        t_nrp = display_value(row_target.get("nrp"))
                        t_nama = display_value(row_target.get("nama"))
                        t_sanksi = display_value(row_target.get("sanksi"))
                        t_tgl = display_value(row_target.get("tanggal"))
                        t_pasal = display_value(row_target.get("pasal"))
                        t_status = display_value(row_target.get("status"))

                        with st.container(border=True):
                            c_info, c_btn_edit, c_btn_del = st.columns([6, 2, 2])
                            with c_info:
                                st.markdown(f"**📅 {html.escape(t_tgl)}** | **NRP:** {html.escape(t_nrp)} - **{html.escape(t_nama)}** | **[{html.escape(t_sanksi)}]** `{html.escape(t_status)}`  \n<small>Pasal: {html.escape(t_pasal)} | PIC: {html.escape(display_value(row_target.get('pic')))}</small>", unsafe_allow_html=True)
                            with c_btn_edit:
                                with st.popover("✏️ Edit", use_container_width=True):
                                    with st.form(f"edit_{target_id}"):
                                        e_tgl = st.date_input("Tanggal Input", parse_date(row_target.get("tanggal")))
                                        e_nrp = st.text_input("NRP", value=str(row_target.get("nrp", "")))
                                        e_nama = st.text_input("Nama Karyawan", value=str(row_target.get("nama", "")))
                                        e_pasal = st.text_input("Pasal Pelanggaran", value=str(row_target.get("pasal", "")))
                                        s_list = ["PERSONAL KONTAK", "PERINGATAN TERTULIS", "SP1", "SP2", "SP3", "SP PERTAMA & TERAKHIR", "DIKEMBALIKAN KE HC"]
                                        curr_s = row_target.get("sanksi", "PERSONAL KONTAK")
                                        e_sanksi = st.selectbox("Jenis Sanksi", s_list, index=(s_list.index(curr_s) if curr_s in s_list else 0))
                                        e_tgl_in = st.date_input("Tanggal IN", parse_date(row_target.get("tgl_in")))
                                        e_tgl_out = st.date_input("Tanggal OUT", parse_date(row_target.get("tgl_out")))
                                        e_sanksi_tambahan = st.text_input("Sanksi Tambahan", value=str(row_target.get("sanksi_tambahan", "") or ""))
                                        e_pelanggaran = st.text_area("Uraian Pelanggaran", value=str(row_target.get("pelanggaran", "") or ""))
                                        e_pic = st.text_input("PIC / Atasan", value=str(row_target.get("pic", "") or ""))
                                        e_ket = st.text_input("Keterangan", value=str(row_target.get("keterangan", "") or ""))

                                        if st.form_submit_button("💾 Simpan Perubahan", type="primary", use_container_width=True):
                                            if check_duplicate_manual(df, nrp=e_nrp, sanksi=e_sanksi, tgl_in=e_tgl_in, pelanggaran=e_pelanggaran, exclude_id=target_id):
                                                st.error("⚠️ Data duplikat!")
                                            else:
                                                upd_payload = {
                                                    "tanggal": str(e_tgl), "nrp": e_nrp.strip(), "nama": e_nama.strip(),
                                                    "pasal": e_pasal.strip(), "sanksi": e_sanksi, "tgl_in": str(e_tgl_in),
                                                    "tgl_out": str(e_tgl_out), "sanksi_tambahan": e_sanksi_tambahan.strip(),
                                                    "pelanggaran": e_pelanggaran.strip(), "pic": e_pic.strip(), "keterangan": e_ket.strip(),
                                                }
                                                try:
                                                    supabase.table("sanksi").update(upd_payload).eq("id", target_id).execute()
                                                    st.toast("✅ Data diperbarui!", icon="✅")
                                                    st.rerun()
                                                except Exception as e:
                                                    st.error(f"❌ Gagal update: {e}")
                            with c_btn_del:
                                with st.popover("🗑️ Hapus", use_container_width=True):
                                    st.warning(f"Hapus permanen sanksi **{t_nama}**?")
                                    if st.button("🔴 Ya, Hapus", key=f"del_{target_id}", type="primary", use_container_width=True):
                                        try:
                                            supabase.table("sanksi").delete().eq("id", target_id).execute()
                                            st.toast("🗑️ Data dihapus!", icon="🗑️")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ Gagal: {e}")
            else:
                st.info("💡 Masukkan NRP atau Nama Karyawan di atas untuk opsi edit dan hapus secara individu.")
    else:
        st.info("Belum ada data sanksi.")