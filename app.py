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
    .block-container {
        padding-top: 0.8rem !important;
        padding-bottom: 1rem !important;
        max-width: 100% !important;
    }

    div[data-testid="stVerticalBlock"] {
        gap: 0.2rem !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px;
        background-color: #ffffff;
    }

    /* ============================================================
       KARTU STATISTIK - GRID SYSTEM AGAR PRESISI DI PC & HP
       ============================================================ */
    .stats-row {
        display: grid;
        grid-template-columns: repeat(8, 1fr); /* 8 Kolom sejajar untuk PC */
        gap: 8px;
        width: 100%;
        margin: 5px 0 15px 0;
    }

    .stat-card {
        background: #f8f9fa;
        border: 1px solid #e1e4e8;
        border-radius: 8px;
        padding: 8px 4px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }

    .stat-label {
        font-size: 11px;
        line-height: 1.15;
        font-weight: 600;
        color: #57606a;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        height: 26px; /* Fix height agar tulisan 2 baris rapi */
        white-space: normal;
    }

    .stat-value {
        font-size: 18px;
        font-weight: 700;
        color: #1f2328;
    }

    /* ============================================================
       TABEL RESPONSIVE
       ============================================================ */
    .table-wrapper {
        width: 100%;
        max-width: 100%;
        overflow: hidden;
        border: 1px solid #d0d7de;
        border-radius: 8px;
        background: #ffffff;
        box-sizing: border-box;
    }

    .oams-table {
        width: 100%;
        max-width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
        font-size: clamp(6px, 0.82vw, 11px);
        line-height: 1.2;
    }

    .oams-table th,
    .oams-table td {
        border: 1px solid #d8dee4;
        padding: 4px 3px;
        vertical-align: top;
        overflow-wrap: anywhere;
        word-break: break-word;
        white-space: normal;
        box-sizing: border-box;
    }

    .oams-table th {
        background: #f6f8fa;
        font-weight: 700;
        text-align: center;
        vertical-align: middle;
    }

    .oams-table td {
        text-align: left;
    }

    .oams-table tbody tr:nth-child(even) {
        background: #fbfcfd;
    }

    .oams-table .center {
        text-align: center;
    }

    .oams-table .status {
        text-align: center;
        font-weight: 700;
    }

    /* Proporsi lebar kolom */
    .col-tanggal { width: 7%; }
    .col-nrp { width: 7%; }
    .col-nama { width: 11%; }
    .col-pasal { width: 10%; }
    .col-sanksi { width: 10%; }
    .col-tglin { width: 7%; }
    .col-tglout { width: 7%; }
    .col-status { width: 7%; }
    .col-tambahan { width: 9%; }
    .col-pelanggaran { width: 14%; }
    .col-pic { width: 6%; }
    .col-ket { width: 5%; }

    .table-info {
        font-size: 12px;
        color: #57606a;
        margin: 3px 0 6px 0;
    }

    /* MEDIA QUERY UNTUK LAYAR KECIL (MOBILE) */
    @media (max-width: 800px) {
        .stats-row {
            grid-template-columns: repeat(4, 1fr); /* Menjadi 4 Kolom (2 Baris) di HP/Tablet */
            gap: 6px;
        }
    }

    @media (max-width: 600px) {
        .stats-row {
            grid-template-columns: repeat(4, 1fr);
            gap: 4px;
        }
        .stat-card {
            padding: 5px 2px;
            border-radius: 6px;
        }
        .stat-label {
            font-size: 9px;
            height: 24px;
        }
        .stat-value {
            font-size: 14px;
        }
        .table-wrapper {
            border-radius: 5px;
        }
        .oams-table {
            font-size: 6px;
        }
        .oams-table th,
        .oams-table td {
            padding: 2px 2px;
        }
    }

    .stExpander {
        border: 1px solid #e1e4e8 !important;
        border-radius: 10px !important;
        background-color: #ffffff !important;
        margin-bottom: 8px !important;
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

try:
    supabase: Client = init_supabase()
except Exception as e:
    st.error(f"Gagal terhubung ke Supabase: {e}")
    st.stop()

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
        for r in (res_k.data or []):
            if r.get("nrp") and r.get("nama"):
                master_karyawan[str(r["nrp"]).strip()] = str(r["nama"]).strip()
    except Exception:
        pass

    try:
        res_p = supabase.table("master_pasal").select("pasal").execute()
        for r in (res_p.data or []):
            if r.get("pasal"):
                list_pasal.add(str(r["pasal"]).strip())
    except Exception:
        pass

    try:
        res_pic = supabase.table("master_pic").select("nama_pic").execute()
        for r in (res_pic.data or []):
            if r.get("nama_pic"):
                list_pic.add(str(r["nama_pic"]).strip())
    except Exception:
        pass

    # Tambahkan data yang sudah pernah masuk ke tabel sanksi sebagai master
    try:
        res_s = supabase.table("sanksi").select("nrp, nama, pasal, pic").execute()
        for r in (res_s.data or []):
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
# 3. FUNGSI BANTU
# -----------------------------------------------------------------------------
def parse_date(value):
    if value is None or pd.isna(value) or str(value).strip() == "":
        return date.today()

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    parsed = pd.to_datetime(str(value), errors="coerce")
    if pd.isna(parsed):
        return date.today()
    return parsed.date()

def normalize_text(value):
    """Normalisasi teks untuk pemeriksaan data ganda."""
    if value is None:
        return ""
    return " ".join(str(value).strip().lower().split())

def calculate_status(value):
    t_out = pd.to_datetime(value, errors="coerce")
    if pd.isna(t_out):
        return "⚪ NON-AKTIF"

    return "🔴 AKTIF" if date.today() <= t_out.date() else "⚪ NON-AKTIF"

def load_sanksi():
    res = supabase.table("sanksi").select("*").execute()
    return pd.DataFrame(res.data or [])

def check_duplicate(df, nrp, sanksi, tgl_in, pelanggaran, exclude_id=None):
    if df.empty:
        return False

    temp = df.copy()

    required_cols = ["nrp", "sanksi", "tgl_in", "pelanggaran"]
    for col in required_cols:
        if col not in temp.columns:
            return False

    if exclude_id is not None and "id" in temp.columns:
        temp = temp[temp["id"] != exclude_id]

    target_nrp = normalize_text(nrp)
    target_sanksi = normalize_text(sanksi)
    target_tgl_in = parse_date(tgl_in).isoformat()
    target_pelanggaran = normalize_text(pelanggaran)

    mask = (
        temp["nrp"].map(normalize_text).eq(target_nrp)
        & temp["sanksi"].map(normalize_text).eq(target_sanksi)
        & temp["tgl_in"].map(lambda x: parse_date(x).isoformat()).eq(target_tgl_in)
        & temp["pelanggaran"].map(normalize_text).eq(target_pelanggaran)
    )

    return bool(mask.any())

# -----------------------------------------------------------------------------
# 4. KONFIGURASI KOLOM TABEL
# -----------------------------------------------------------------------------
TABLE_COLUMNS = [
    ("tanggal", "Tanggal", "col-tanggal"),
    ("nrp", "NRP", "col-nrp"),
    ("nama", "Nama Karyawan", "col-nama"),
    ("pasal", "Pasal", "col-pasal"),
    ("sanksi", "Jenis Sanksi", "col-sanksi"),
    ("tgl_in", "Tgl IN", "col-tglin"),
    ("tgl_out", "Tgl OUT", "col-tglout"),
    ("status", "Status", "col-status"),
    ("sanksi_tambahan", "Sanksi Tambahan", "col-tambahan"),
    ("pelanggaran", "Uraian Pelanggaran", "col-pelanggaran"),
    ("pic", "PIC / Atasan", "col-pic"),
    ("keterangan", "Keterangan", "col-ket"),
]

def display_value(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "-"
    text = str(value).strip()
    return text if text else "-"

def render_html_table(df):
    if df.empty:
        st.info("Belum ada data sanksi.")
        return

    header = "".join(
        f"<th class='{css_class}'>{html.escape(label)}</th>"
        for _, label, css_class in TABLE_COLUMNS
    )

    rows = []

    for _, row in df.iterrows():
        cells = []

        for key, _, css_class in TABLE_COLUMNS:
            value = display_value(row.get(key, "-"))

            if key == "status":
                cell = f"<td class='{css_class} status'>{html.escape(value)}</td>"
            elif key in ("nrp", "tanggal", "tgl_in", "tgl_out"):
                cell = f"<td class='{css_class} center'>{html.escape(value)}</td>"
            else:
                cell = f"<td class='{css_class}'>{html.escape(value)}</td>"

            cells.append(cell)

        rows.append("<tr>" + "".join(cells) + "</tr>")

    table_html = f"""
    <div class="table-wrapper">
        <table class="oams-table">
            <thead>
                <tr>{header}</tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
    </div>
    """

    st.markdown(table_html, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. SIDEBAR
# -----------------------------------------------------------------------------
st.sidebar.title("🔐 OAMS System")

role = st.sidebar.radio(
    "Akses Sebagai:",
    ["User (Read-Only)", "Admin"]
)

is_admin = False

if role == "Admin":
    password = st.sidebar.text_input(
        "Masukkan PIN Admin:",
        type="password"
    )

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

# -----------------------------------------------------------------------------
# 6. DASHBOARD & INPUT ADMIN
# -----------------------------------------------------------------------------
if menu == "Dashboard & Input" and is_admin:

    st.markdown(
        "<h3 style='margin-top:-12px;margin-bottom:7px;'>📊 Dashboard & Kelola Sanksi</h3>",
        unsafe_allow_html=True
    )

    # Ambil data terbaru
    try:
        df = load_sanksi()
    except Exception as e:
        st.error(f"Gagal mengambil data sanksi: {e}")
        st.stop()

    # -------------------------------------------------------------------------
    # TOTAL SANKSI - GRID HORIZONTAL (PRESISI)
    # -------------------------------------------------------------------------
    total_data = len(df) if not df.empty else 0

    if not df.empty and "sanksi" in df.columns:
        pk_count = int((df["sanksi"] == "PERSONAL KONTAK").sum())
        pt_count = int((df["sanksi"] == "PERINGATAN TERTULIS").sum())
        sp1_count = int((df["sanksi"] == "SP1").sum())
        sp2_count = int((df["sanksi"] == "SP2").sum())
        sp3_count = int((df["sanksi"] == "SP3").sum())
        sppt_count = int((df["sanksi"] == "SP PERTAMA & TERAKHIR").sum())
        hc_count = int((df["sanksi"] == "DIKEMBALIKAN KE HC").sum())
    else:
        pk_count = pt_count = sp1_count = sp2_count = sp3_count = sppt_count = hc_count = 0

    stats = [
        ("Total Sanksi", total_data),
        ("Personal Kontak", pk_count),
        ("Peringatan Tertulis", pt_count),
        ("SP 1", sp1_count),
        ("SP 2", sp2_count),
        ("SP 3", sp3_count),
        ("SP Pertama & Terakhir", sppt_count),
        ("Dikembalikan HC", hc_count),
    ]

    cards = "".join(
        f"<div class='stat-card'>"
        f"<div class='stat-label'>{html.escape(label)}</div>"
        f"<div class='stat-value'>{value}</div>"
        f"</div>"
        for label, value in stats
    )

    st.markdown(
        f"<div class='stats-row'>{cards}</div>",
        unsafe_allow_html=True
    )

    st.markdown("<hr style='margin:7px 0px;'>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # FORM INPUT
    # -------------------------------------------------------------------------
    if "input_form_version" not in st.session_state:
        st.session_state.input_form_version = 0

    form_version = st.session_state.input_form_version

    st.markdown(
        "<h4 style='margin-bottom:7px;'>📝 Form Input Sanksi Baru</h4>",
        unsafe_allow_html=True
    )

    def auto_fill_nama():
        nrp_key = f"input_nrp_{form_version}"
        nama_key = f"input_nama_{form_version}"

        typed_nrp = str(st.session_state.get(nrp_key, "")).strip()

        if typed_nrp in MASTER_KARYAWAN:
            st.session_state[nama_key] = MASTER_KARYAWAN[typed_nrp]
        else:
            st.session_state[nama_key] = ""

    with st.container(border=True):
        col_f1, col_f2 = st.columns(2)

        with col_f1:
            tgl = st.date_input(
                "Tanggal Input",
                date.today(),
                key=f"input_tanggal_{form_version}"
            )

            nrp = st.text_input(
                "NRP Karyawan",
                key=f"input_nrp_{form_version}",
                on_change=auto_fill_nama,
                placeholder="Ketik NRP lalu tekan Enter..."
            )

            nama = st.text_input(
                "Nama Karyawan",
                key=f"input_nama_{form_version}",
                placeholder="Terisi otomatis jika NRP ada di master..."
            )

            pasal_options = [""] + LIST_PASAL + ["+ Ketik Pasal Baru..."]
            selected_pasal = st.selectbox(
                "Pasal Pelanggaran",
                options=pasal_options,
                key=f"input_selected_pasal_{form_version}"
            )

            if selected_pasal == "+ Ketik Pasal Baru...":
                pasal = st.text_input(
                    "Ketik Pasal Baru",
                    key=f"input_pasal_baru_{form_version}"
                )
            else:
                pasal = selected_pasal

            sanksi = st.selectbox(
                "Jenis Sanksi",
                [
                    "PERSONAL KONTAK",
                    "PERINGATAN TERTULIS",
                    "SP1",
                    "SP2",
                    "SP3",
                    "SP PERTAMA & TERAKHIR",
                    "DIKEMBALIKAN KE HC"
                ],
                key=f"input_sanksi_{form_version}"
            )

            tgl_in = st.date_input(
                "Tanggal IN (Mulai Sanksi)",
                date.today(),
                key=f"input_tgl_in_{form_version}"
            )

        with col_f2:
            tgl_out = st.date_input(
                "Tanggal OUT (Selesai Sanksi)",
                date.today(),
                key=f"input_tgl_out_{form_version}"
            )

            sanksi_tambahan = st.text_input(
                "Sanksi Tambahan",
                placeholder="Opsional",
                key=f"input_tambahan_{form_version}"
            )

            pelanggaran = st.text_area(
                "Uraian Pelanggaran",
                key=f"input_pelanggaran_{form_version}"
            )

            pic_options = [""] + LIST_PIC + ["+ Ketik PIC Baru..."]
            selected_pic = st.selectbox(
                "PIC / Atasan",
                options=pic_options,
                key=f"input_selected_pic_{form_version}"
            )

            if selected_pic == "+ Ketik PIC Baru...":
                pic = st.text_input(
                    "Ketik PIC Baru",
                    key=f"input_pic_baru_{form_version}"
                )
            else:
                pic = selected_pic

            ket = st.text_input(
                "Keterangan Tambahan",
                key=f"input_keterangan_{form_version}"
            )

        submitted = st.button(
            "💾 Simpan Data Sanksi",
            type="primary",
            use_container_width=True,
            key=f"save_button_{form_version}"
        )

        if submitted:
            if not nrp.strip() or not nama.strip():
                st.error("❌ NRP dan Nama Karyawan wajib diisi!")
                st.stop()

            if not str(pelanggaran).strip():
                st.error("❌ Uraian Pelanggaran wajib diisi!")
                st.stop()

            if check_duplicate(
                df,
                nrp=nrp,
                sanksi=sanksi,
                tgl_in=tgl_in,
                pelanggaran=pelanggaran
            ):
                st.error(
                    "⚠️ Data sudah ada! NRP, Jenis Sanksi, Tanggal IN, dan Uraian Pelanggaran "
                    "sama dengan data yang sudah tersimpan."
                )
                st.stop()

            payload = {
                "tanggal": str(tgl),
                "nrp": nrp.strip(),
                "nama": nama.strip(),
                "pasal": str(pasal).strip(),
                "sanksi": sanksi,
                "tgl_in": str(tgl_in),
                "tgl_out": str(tgl_out),
                "sanksi_tambahan": str(sanksi_tambahan).strip(),
                "pelanggaran": str(pelanggaran).strip(),
                "pic": str(pic).strip(),
                "keterangan": str(ket).strip(),
            }

            try:
                supabase.table("sanksi").insert(payload).execute()
            except Exception as e:
                st.error(f"❌ Gagal menyimpan data sanksi: {e}")
                st.stop()

            try:
                if nrp.strip() not in MASTER_KARYAWAN:
                    supabase.table("master_karyawan").insert(
                        {"nrp": nrp.strip(), "nama": nama.strip()}
                    ).execute()

                if selected_pasal == "+ Ketik Pasal Baru..." and str(pasal).strip():
                    supabase.table("master_pasal").insert(
                        {"pasal": str(pasal).strip()}
                    ).execute()

                if selected_pic == "+ Ketik PIC Baru..." and str(pic).strip():
                    supabase.table("master_pic").insert(
                        {"nama_pic": str(pic).strip()}
                    ).execute()
            except Exception:
                pass

            st.cache_data.clear()
            st.session_state.input_form_version += 1

            st.toast(
                f"✅ Berhasil menyimpan sanksi untuk {nama.strip()} ({nrp.strip()})!",
                icon="✅"
            )

            st.rerun()

    # -------------------------------------------------------------------------
    # RECORD TERBARU
    # -------------------------------------------------------------------------
    st.markdown(
        "<h4 style='margin-top:10px;margin-bottom:4px;'>📋 10 Record Terbaru</h4>",
        unsafe_allow_html=True
    )

    if not df.empty:
        if "id" in df.columns:
            df_dash = df.sort_values(by="id", ascending=False).head(10)
        else:
            df_dash = df.head(10)

        df_dash = df_dash.copy()
        if "status" in df_dash.columns:
            df_dash["status"] = df_dash["tgl_out"].apply(calculate_status)

        render_html_table(df_dash)
    else:
        st.info("Belum ada data sanksi.")

# -----------------------------------------------------------------------------
# 7. HISTORY & PENCARIAN
# -----------------------------------------------------------------------------
elif menu == "History & Pencarian":

    st.markdown(
        "<h3 style='margin-top:-12px;margin-bottom:7px;'>🔍 History & Pencarian Sanksi</h3>",
        unsafe_allow_html=True
    )

    try:
        df = load_sanksi()
    except Exception as e:
        st.error(f"Gagal mengambil data sanksi: {e}")
        st.stop()

    if not df.empty:

        if "tgl_out" in df.columns:
            df["status"] = df["tgl_out"].apply(calculate_status)
        else:
            df["status"] = "⚪ NON-AKTIF"

        search_query = st.text_input(
            "🔎 Cari berdasarkan NRP atau Nama Karyawan:",
            placeholder="Ketik nama atau NRP..."
        )

        if search_query:
            q = str(search_query).strip()
            df_filtered = df[
                df["nrp"].astype(str).str.contains(q, case=False, na=False, regex=False) |
                df["nama"].astype(str).str.contains(q, case=False, na=False, regex=False)
            ].copy()
        else:
            df_filtered = df.copy()

        if "id" in df_filtered.columns:
            df_sorted = df_filtered.sort_values(by="id", ascending=False).copy()
        else:
            df_sorted = df_filtered.copy()

        col_top1, col_top2 = st.columns([2, 1])

        with col_top1:
            st.markdown(
                f"<div style='padding-top:8px;'>Total data ditemukan: "
                f"<b>{len(df_sorted)}</b> baris</div>",
                unsafe_allow_html=True
            )

        with col_top2:
            page_size = st.selectbox(
                "Jumlah baris:",
                ["10", "50", "100", "All"],
                index=0,
                key="history_page_size"
            )

        if page_size == "All":
            df_display = df_sorted
        else:
            df_display = df_sorted.head(int(page_size))

        st.markdown(
            f"<div class='table-info'>Menampilkan "
            f"<b>{len(df_display)}</b> dari <b>{len(df_sorted)}</b> data</div>",
            unsafe_allow_html=True
        )

        column_order_excel = [
            "tanggal", "nrp", "nama", "pasal", "sanksi", "tgl_in",
            "tgl_out", "status", "sanksi_tambahan", "pelanggaran",
            "pic", "keterangan"
        ]
        avail_excel = [c for c in column_order_excel if c in df_sorted.columns]

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_sorted[avail_excel].to_excel(
                writer, index=False, sheet_name="Data Sanksi"
            )

        st.download_button(
            label="📥 Download Data Terupdate ke Excel",
            data=buffer.getvalue(),
            file_name=f"Data_Sanksi_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

        st.markdown("<div style='height:5px'></div>", unsafe_allow_html=True)
        
        render_html_table(df_display)

        # PANEL EDIT / HAPUS KHUSUS ADMIN
        if is_admin:
            st.markdown("---")
            st.subheader("🛠️ Panel Edit / Hapus Data (Khusus Admin)")
            st.caption(
                "Ketik NRP atau Nama karyawan untuk menampilkan data yang ingin diubah atau dihapus."
            )

            search_admin = st.text_input(
                "🔎 Ketik NRP / Nama Karyawan untuk Edit / Hapus:",
                placeholder="Contoh: 0211002",
                key="search_admin_input"
            )

            if search_admin:
                q_admin = str(search_admin).strip()
                df_admin_target = df_sorted[
                    df_sorted["nrp"].astype(str).str.contains(q_admin, case=False, na=False, regex=False) |
                    df_sorted["nama"].astype(str).str.contains(q_admin, case=False, na=False, regex=False)
                ].copy()
            else:
                df_admin_target = pd.DataFrame()

            if search_admin and df_admin_target.empty:
                st.warning(f"Tidak ditemukan data sanksi dengan NRP / Nama: **{search_admin}**")
            elif not search_admin:
                st.info("💡 Masukkan NRP atau Nama Karyawan di atas untuk memunculkan opsi edit dan hapus.")
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
                            st.markdown(
                                f"**📅 {html.escape(t_tgl)}** | "
                                f"**NRP:** {html.escape(t_nrp)} - "
                                f"**{html.escape(t_nama)}** | "
                                f"**[{html.escape(t_sanksi)}]** "
                                f"`{html.escape(t_status)}`  \n"
                                f"<small>Pasal: {html.escape(t_pasal)} | "
                                f"PIC: {html.escape(display_value(row_target.get('pic')))}</small>",
                                unsafe_allow_html=True
                            )

                        with c_btn_edit:
                            with st.popover("✏️ Edit Data", use_container_width=True):
                                st.subheader(f"✏️ Edit Data: {t_nama}")

                                edit_key = f"edit_{target_id}"
                                with st.form(edit_key):
                                    e_tgl = st.date_input("Tanggal Input", parse_date(row_target.get("tanggal")))
                                    e_nrp = st.text_input("NRP", value=str(row_target.get("nrp", "")))
                                    e_nama = st.text_input("Nama Karyawan", value=str(row_target.get("nama", "")))
                                    e_pasal = st.text_input("Pasal Pelanggaran", value=str(row_target.get("pasal", "")))
                                    
                                    s_list = [
                                        "PERSONAL KONTAK",
                                        "PERINGATAN TERTULIS",
                                        "SP1",
                                        "SP2",
                                        "SP3",
                                        "SP PERTAMA & TERAKHIR",
                                        "DIKEMBALIKAN KE HC",
                                    ]
                                    curr_s = row_target.get("sanksi", "PERSONAL KONTAK")
                                    e_sanksi = st.selectbox(
                                        "Jenis Sanksi",
                                        s_list,
                                        index=(s_list.index(curr_s) if curr_s in s_list else 0)
                                    )

                                    e_tgl_in = st.date_input("Tanggal IN", parse_date(row_target.get("tgl_in")))
                                    e_tgl_out = st.date_input("Tanggal OUT", parse_date(row_target.get("tgl_out")))
                                    e_sanksi_tambahan = st.text_input("Sanksi Tambahan", value=str(row_target.get("sanksi_tambahan", "") or ""))
                                    e_pelanggaran = st.text_area("Uraian Pelanggaran", value=str(row_target.get("pelanggaran", "") or ""))
                                    e_pic = st.text_input("PIC / Atasan", value=str(row_target.get("pic", "") or ""))
                                    e_ket = st.text_input("Keterangan", value=str(row_target.get("keterangan", "") or ""))

                                    save_edit = st.form_submit_button("💾 Simpan Perubahan", type="primary", use_container_width=True)

                                    if save_edit:
                                        if check_duplicate(df, nrp=e_nrp, sanksi=e_sanksi, tgl_in=e_tgl_in, pelanggaran=e_pelanggaran, exclude_id=target_id):
                                            st.error("⚠️ Data sudah ada! NRP, Jenis Sanksi, Tanggal IN, dan Uraian Pelanggaran sama dengan data lain.")
                                        else:
                                            upd_payload = {
                                                "tanggal": str(e_tgl),
                                                "nrp": e_nrp.strip(),
                                                "nama": e_nama.strip(),
                                                "pasal": e_pasal.strip(),
                                                "sanksi": e_sanksi,
                                                "tgl_in": str(e_tgl_in),
                                                "tgl_out": str(e_tgl_out),
                                                "sanksi_tambahan": e_sanksi_tambahan.strip(),
                                                "pelanggaran": e_pelanggaran.strip(),
                                                "pic": e_pic.strip(),
                                                "keterangan": e_ket.strip(),
                                            }

                                            try:
                                                supabase.table("sanksi").update(upd_payload).eq("id", target_id).execute()
                                                st.toast(f"✅ Data {e_nama} berhasil diperbarui!", icon="✅")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"❌ Gagal memperbarui data: {e}")

                        with c_btn_del:
                            with st.popover("🗑️ Hapus", use_container_width=True):
                                st.warning(f"Hapus permanen sanksi **{t_nama}** (ID: {target_id})?")
                                if st.button("🔴 Ya, Hapus", key=f"del_panel_{target_id}", type="primary", use_container_width=True):
                                    try:
                                        supabase.table("sanksi").delete().eq("id", target_id).execute()
                                        st.toast(f"🗑️ Data ID {target_id} berhasil dihapus!", icon="🗑️")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Gagal menghapus data: {e}")

    else:
        st.info("Belum ada data sanksi.")