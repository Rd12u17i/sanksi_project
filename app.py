import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import date, datetime
import io

st.set_page_config(
    page_title="OAMS - Sistem Sanksi Karyawan",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# CSS
# =========================
st.markdown("""
<style>
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
    max-width: 100% !important;
}

/* Statistik: satu blok HTML utuh agar tag tidak pernah tampil sebagai teks */
.stats-row {
    display: grid;
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: 7px;
    width: 100%;
    margin: 4px 0 12px 0;
}
.stat-card {
    box-sizing: border-box;
    min-width: 0;
    background: #f8f9fa;
    border: 1px solid #dfe3e8;
    border-radius: 8px;
    padding: 7px 4px;
    text-align: center;
    overflow: hidden;
}
.stat-label {
    font-size: 11px;
    font-weight: 600;
    line-height: 1.15;
    overflow-wrap: anywhere;
}
.stat-value {
    font-size: 1.25rem;
    font-weight: 700;
    line-height: 1.15;
    margin-top: 3px;
}

/* Tabel utama selalu memakai lebar container */
div[data-testid="stDataFrame"] {
    width: 100% !important;
    max-width: 100% !important;
}
div[data-testid="stDataFrame"] > div {
    width: 100% !important;
    max-width: 100% !important;
}

/* Pada HP statistik tetap horizontal dan diperkecil */
@media (max-width: 700px) {
    .stats-row {
        gap: 3px;
    }
    .stat-card {
        padding: 5px 2px;
        border-radius: 6px;
    }
    .stat-label {
        font-size: 8px;
    }
    .stat-value {
        font-size: .95rem;
    }
}
</style>
""", unsafe_allow_html=True)

# =========================
# SUPABASE
# =========================
SUPABASE_URL = "https://zuctywyaxznjhzwckery.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp1Y3R5d3lheHpuamh6d2NrZXJ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc5MjI1OTcsImV4cCI6MjEwMzQ5ODU5N30.14uuKR3VoXkTE48jBS2NzX57NCDMwcFtXhKkLjJKJTg"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# =========================
# MASTER DATA
# =========================
@st.cache_data(ttl=300)
def load_supabase_master():
    master_karyawan = {}
    list_pasal = set()
    list_pic = set()

    try:
        res = supabase.table("master_karyawan").select("nrp, nama").execute()
        for r in (res.data or []):
            if r.get("nrp") and r.get("nama"):
                master_karyawan[str(r["nrp"]).strip()] = str(r["nama"]).strip()
    except Exception:
        pass

    try:
        res = supabase.table("master_pasal").select("pasal").execute()
        for r in (res.data or []):
            if r.get("pasal"):
                list_pasal.add(str(r["pasal"]).strip())
    except Exception:
        pass

    try:
        res = supabase.table("master_pic").select("nama_pic").execute()
        for r in (res.data or []):
            if r.get("nama_pic"):
                list_pic.add(str(r["nama_pic"]).strip())
    except Exception:
        pass

    try:
        res = supabase.table("sanksi").select("nrp, nama, pasal, pic").execute()
        for r in (res.data or []):
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

# =========================
# SIDEBAR
# =========================
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

# =========================
# FUNGSI
# =========================
SANKSI_LIST = [
    "PERSONAL KONTAK",
    "PERINGATAN TERTULIS",
    "SP1",
    "SP2",
    "SP3",
    "DIKEMBALIKAN KE HC"
]

DISPLAY_COLUMNS = [
    "tanggal", "nrp", "nama", "pasal", "sanksi",
    "tgl_in", "tgl_out", "status", "sanksi_tambahan",
    "pelanggaran", "pic", "keterangan"
]

COLUMN_CONFIG_TABLE = {
    "tanggal": st.column_config.TextColumn("Tanggal Input", width="small"),
    "nrp": st.column_config.TextColumn("NRP", width="small"),
    "nama": st.column_config.TextColumn("Nama Karyawan", width="medium"),
    "pasal": st.column_config.TextColumn("Pasal Pelanggaran", width="medium"),
    "sanksi": st.column_config.TextColumn("Jenis Sanksi", width="medium"),
    "tgl_in": st.column_config.TextColumn("Tgl IN", width="small"),
    "tgl_out": st.column_config.TextColumn("Tgl OUT", width="small"),
    "status": st.column_config.TextColumn("Status", width="small"),
    "sanksi_tambahan": st.column_config.TextColumn("Sanksi Tambahan", width="medium"),
    "pelanggaran": st.column_config.TextColumn("Uraian Pelanggaran", width="large"),
    "pic": st.column_config.TextColumn("PIC / Atasan", width="medium"),
    "keterangan": st.column_config.TextColumn("Keterangan", width="medium")
}

def parse_date(value):
    if value is None or value == "" or pd.isna(value):
        return date.today()
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except Exception:
        return date.today()

def normalize_text(value):
    if value is None or pd.isna(value):
        return ""
    return " ".join(str(value).strip().lower().split())

def is_duplicate_sanksi(nrp, sanksi, tgl_in, pelanggaran, exclude_id=None):
    """Duplikat = NRP + Jenis Sanksi + Tanggal IN + Uraian Pelanggaran sama."""
    try:
        res = (
            supabase.table("sanksi")
            .select("id, nrp, sanksi, tgl_in, pelanggaran")
            .eq("nrp", str(nrp).strip())
            .eq("sanksi", str(sanksi).strip())
            .eq("tgl_in", str(tgl_in))
            .execute()
        )
    except Exception as e:
        st.error(f"Gagal mengecek data ganda: {e}")
        return True

    target = normalize_text(pelanggaran)
    for row in (res.data or []):
        if exclude_id is not None and str(row.get("id")) == str(exclude_id):
            continue
        if normalize_text(row.get("pelanggaran")) == target:
            return True
    return False

def add_master_data(nrp, nama, selected_pasal, pasal, selected_pic, pic):
    try:
        if nrp not in MASTER_KARYAWAN:
            supabase.table("master_karyawan").insert(
                {"nrp": nrp, "nama": nama}
            ).execute()

        if selected_pasal == "+ Ketik Pasal Baru..." and pasal.strip():
            supabase.table("master_pasal").insert(
                {"pasal": pasal.strip()}
            ).execute()

        if selected_pic == "+ Ketik PIC Baru..." and pic.strip():
            supabase.table("master_pic").insert(
                {"nama_pic": pic.strip()}
            ).execute()
    except Exception:
        pass

# =========================
# DASHBOARD & INPUT ADMIN
# =========================
if menu == "Dashboard & Input" and is_admin:

    st.markdown(
        "<h3 style='margin-top:-10px;margin-bottom:8px;'>📊 Dashboard & Kelola Sanksi</h3>",
        unsafe_allow_html=True
    )

    try:
        res = supabase.table("sanksi").select("*").execute()
        df = pd.DataFrame(res.data or [])
    except Exception as e:
        st.error(f"Gagal mengambil data sanksi: {e}")
        df = pd.DataFrame()

    if not df.empty and "sanksi" in df.columns:
        s = df["sanksi"].fillna("").astype(str).str.strip().str.upper()
        total_data = len(df)
        personal_count = int((s == "PERSONAL KONTAK").sum())
        peringatan_count = int((s == "PERINGATAN TERTULIS").sum())
        sp1_count = int((s == "SP1").sum())
        sp2_count = int((s == "SP2").sum())
        sp3_count = int((s == "SP3").sum())
    else:
        total_data = personal_count = peringatan_count = 0
        sp1_count = sp2_count = sp3_count = 0

    # PENTING: seluruh kartu berada dalam SATU st.markdown().
    stats_html = f"""
<div class="stats-row">
  <div class="stat-card"><div class="stat-label">Total Sanksi</div><div class="stat-value">{total_data}</div></div>
  <div class="stat-card"><div class="stat-label">Personal Kontak</div><div class="stat-value">{personal_count}</div></div>
  <div class="stat-card"><div class="stat-label">Peringatan Tertulis</div><div class="stat-value">{peringatan_count}</div></div>
  <div class="stat-card"><div class="stat-label">SP1</div><div class="stat-value">{sp1_count}</div></div>
  <div class="stat-card"><div class="stat-label">SP2</div><div class="stat-value">{sp2_count}</div></div>
  <div class="stat-card"><div class="stat-label">SP3</div><div class="stat-value">{sp3_count}</div></div>
</div>
"""
    st.markdown(stats_html, unsafe_allow_html=True)

    st.markdown("<hr style='margin:5px 0 8px 0;'>", unsafe_allow_html=True)
    st.markdown("<h4 style='margin-bottom:6px;'>📝 Form Input Sanksi Baru</h4>", unsafe_allow_html=True)

    # Versi key membuat SEMUA widget form kembali kosong setelah simpan.
    if "form_version" not in st.session_state:
        st.session_state.form_version = 0

    if "notif_success" in st.session_state:
        st.toast(st.session_state.pop("notif_success"), icon="✅")
    if "notif_error" in st.session_state:
        st.error(st.session_state.pop("notif_error"))

    v = st.session_state.form_version

    def auto_fill_nama():
        typed = st.session_state.get(f"input_nrp_{v}", "").strip()
        if typed in MASTER_KARYAWAN:
            st.session_state[f"input_nama_{v}"] = MASTER_KARYAWAN[typed]

    with st.container(border=True):
        col_f1, col_f2 = st.columns(2)

        with col_f1:
            tgl = st.date_input("Tanggal Input", date.today(), key=f"tgl_{v}")
            nrp = st.text_input(
                "NRP Karyawan",
                key=f"input_nrp_{v}",
                on_change=auto_fill_nama,
                placeholder="Ketik NRP lalu tekan Enter..."
            )
            nama = st.text_input(
                "Nama Karyawan",
                key=f"input_nama_{v}",
                placeholder="Terisi otomatis jika NRP ada di master..."
            )

            pasal_options = [""] + LIST_PASAL + ["+ Ketik Pasal Baru..."]
            selected_pasal = st.selectbox(
                "Pasal Pelanggaran",
                pasal_options,
                key=f"pasal_select_{v}"
            )
            if selected_pasal == "+ Ketik Pasal Baru...":
                pasal = st.text_input("Ketik Pasal Baru", key=f"pasal_baru_{v}")
            else:
                pasal = selected_pasal

            sanksi = st.selectbox(
                "Jenis Sanksi", SANKSI_LIST, key=f"sanksi_{v}"
            )
            tgl_in = st.date_input(
                "Tanggal IN (Mulai Sanksi)",
                date.today(),
                key=f"tgl_in_{v}"
            )

        with col_f2:
            tgl_out = st.date_input(
                "Tanggal OUT (Selesai Sanksi)",
                date.today(),
                key=f"tgl_out_{v}"
            )
            sanksi_tambahan = st.text_input(
                "Sanksi Tambahan",
                placeholder="Opsional",
                key=f"tambahan_{v}"
            )
            pelanggaran = st.text_area(
                "Uraian Pelanggaran", key=f"pelanggaran_{v}"
            )

            pic_options = [""] + LIST_PIC + ["+ Ketik PIC Baru..."]
            selected_pic = st.selectbox(
                "PIC / Atasan", pic_options, key=f"pic_select_{v}"
            )
            if selected_pic == "+ Ketik PIC Baru...":
                pic = st.text_input("Ketik PIC Baru", key=f"pic_baru_{v}")
            else:
                pic = selected_pic

            ket = st.text_input(
                "Keterangan Tambahan", key=f"ket_{v}"
            )

        submitted = st.button(
            "💾 Simpan Data Sanksi",
            type="primary",
            use_container_width=True,
            key=f"submit_{v}"
        )

    if submitted:
        nrp_clean = nrp.strip()
        nama_clean = nama.strip()
        pelanggaran_clean = pelanggaran.strip()

        if not nrp_clean or not nama_clean:
            st.session_state.notif_error = "NRP dan Nama Karyawan wajib diisi!"
            st.rerun()

        if is_duplicate_sanksi(
            nrp_clean, sanksi, tgl_in, pelanggaran_clean
        ):
            st.session_state.notif_error = (
                "⚠️ Data sudah ada! NRP, Jenis Sanksi, Tanggal IN, "
                "dan Uraian Pelanggaran sama."
            )
            st.rerun()

        payload = {
            "tanggal": str(tgl),
            "nrp": nrp_clean,
            "nama": nama_clean,
            "pasal": pasal,
            "sanksi": sanksi,
            "tgl_in": str(tgl_in),
            "tgl_out": str(tgl_out),
            "sanksi_tambahan": sanksi_tambahan.strip(),
            "pelanggaran": pelanggaran_clean,
            "pic": pic.strip(),
            "keterangan": ket.strip()
        }

        try:
            supabase.table("sanksi").insert(payload).execute()
            add_master_data(
                nrp_clean, nama_clean,
                selected_pasal, pasal,
                selected_pic, pic
            )
            st.cache_data.clear()

            st.session_state.form_version += 1
            st.session_state.notif_success = (
                f"Berhasil menyimpan sanksi untuk {nama_clean} ({nrp_clean})!"
            )
            st.rerun()
        except Exception as e:
            st.session_state.notif_error = f"Gagal menyimpan data: {e}"
            st.rerun()

    st.markdown(
        "<h4 style='margin-top:12px;margin-bottom:4px;'>📋 5 Record Terbaru</h4>",
        unsafe_allow_html=True
    )

    if not df.empty:
        df_dash = df.sort_values(by="id", ascending=False).head(5)
        df_dash = df_dash.drop(columns=["id", "created_at"], errors="ignore")
        df_dash = df_dash[
            [c for c in DISPLAY_COLUMNS if c in df_dash.columns]
        ]
        st.dataframe(
            df_dash,
            use_container_width=True,
            hide_index=True,
            column_config=COLUMN_CONFIG_TABLE
        )
    else:
        st.info("Belum ada data sanksi.")

# =========================
# HISTORY
# =========================
elif menu == "History & Pencarian":

    st.markdown(
        "<h3 style='margin-top:-10px;margin-bottom:8px;'>🔍 History & Pencarian Sanksi</h3>",
        unsafe_allow_html=True
    )

    try:
        res = supabase.table("sanksi").select("*").execute()
        df = pd.DataFrame(res.data or [])
    except Exception as e:
        st.error(f"Gagal mengambil data sanksi: {e}")
        df = pd.DataFrame()

    search_query = st.text_input(
        "🔎 Cari berdasarkan NRP atau Nama Karyawan:",
        placeholder="Ketik nama atau NRP..."
    )

    if not df.empty:
        today_date = date.today()

        def calculate_status(value):
            try:
                t_out = datetime.strptime(
                    str(value)[:10], "%Y-%m-%d"
                ).date()
                return "🔴 AKTIF" if today_date <= t_out else "⚪ NON-AKTIF"
            except Exception:
                return "⚪ NON-AKTIF"

        df["status"] = df["tgl_out"].apply(calculate_status)

        if search_query.strip():
            q = search_query.strip()
            df_filtered = df[
                df["nrp"].astype(str).str.contains(q, case=False, na=False)
                | df["nama"].astype(str).str.contains(q, case=False, na=False)
            ]
        else:
            df_filtered = df

        df_sorted = df_filtered.sort_values(by="id", ascending=False)

        col1, col2 = st.columns([2, 1])
        with col1:
            st.write(f"Total data ditemukan: **{len(df_sorted)}** baris")
        with col2:
            rows_option = st.selectbox(
                "Tampilkan baris:",
                [10, 50, 100, "All"],
                index=0
            )

        if rows_option == "All":
            df_show = df_sorted
        else:
            df_show = df_sorted.head(int(rows_option))

        st.caption(
            f"Menampilkan {len(df_show)} dari {len(df_sorted)} data."
        )

        # Excel berisi seluruh hasil pencarian.
        avail_excel = [c for c in DISPLAY_COLUMNS if c in df_sorted.columns]
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_sorted[avail_excel].to_excel(
                writer, index=False, sheet_name="Data Sanksi"
            )

        st.download_button(
            "📥 Download Data Terupdate ke Excel",
            data=buffer.getvalue(),
            file_name=f"Data_Sanksi_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        st.markdown("---")

        df_table = df_show.drop(
            columns=["id", "created_at"], errors="ignore"
        )
        df_table = df_table[
            [c for c in DISPLAY_COLUMNS if c in df_table.columns]
        ]

        # HANYA SATU MODE TABEL. Tidak ada Mode Kartu.
        st.dataframe(
            df_table,
            use_container_width=True,
            hide_index=True,
            column_config=COLUMN_CONFIG_TABLE,
            height=min(620, max(250, 38 * len(df_table) + 45))
        )

        # =========================
        # ADMIN EDIT / HAPUS
        # =========================
        if is_admin:
            st.markdown("---")
            st.subheader("🛠️ Panel Edit / Hapus Data (Khusus Admin)")
            st.caption(
                "Ketik NRP atau Nama karyawan untuk menampilkan data "
                "yang ingin diubah atau dihapus."
            )

            search_admin = st.text_input(
                "🔎 Ketik NRP / Nama Karyawan untuk Edit / Hapus:",
                placeholder="Contoh: 0211002",
                key="search_admin_input"
            )

            if search_admin.strip():
                q_admin = search_admin.strip()
                target_df = df_sorted[
                    df_sorted["nrp"].astype(str).str.contains(
                        q_admin, case=False, na=False
                    )
                    | df_sorted["nama"].astype(str).str.contains(
                        q_admin, case=False, na=False
                    )
                ]

                if target_df.empty:
                    st.warning(
                        f"Tidak ditemukan data sanksi dengan NRP / Nama: "
                        f"**{search_admin}**"
                    )
                else:
                    st.write(
                        f"Ditemukan **{len(target_df)}** data untuk target "
                        f"**{search_admin}**:"
                    )

                    for _, row in target_df.iterrows():
                        target_id = row["id"]
                        t_nrp = row.get("nrp", "-")
                        t_nama = row.get("nama", "-")
                        t_sanksi = row.get("sanksi", "-")
                        t_tgl = row.get("tanggal", "-")
                        t_pasal = row.get("pasal", "-")
                        t_status = row.get("status", "-")

                        with st.container(border=True):
                            c_info, c_edit, c_del = st.columns([6, 2, 2])

                            with c_info:
                                st.markdown(
                                    f"**📅 {t_tgl}** | **NRP:** {t_nrp} - "
                                    f"**{t_nama}** | **[{t_sanksi}]** `{t_status}`  \n"
                                    f"<small>Pasal: {t_pasal} | "
                                    f"PIC: {row.get('pic', '-')}</small>",
                                    unsafe_allow_html=True
                                )

                            with c_edit:
                                with st.popover(
                                    "✏️ Edit Data", use_container_width=True
                                ):
                                    st.subheader(f"✏️ Edit Data: {t_nama}")

                                    with st.form(f"form_edit_{target_id}"):
                                        e_tgl = st.date_input(
                                            "Tanggal Input",
                                            parse_date(row.get("tanggal"))
                                        )
                                        e_nrp = st.text_input(
                                            "NRP", value=str(t_nrp)
                                        )
                                        e_nama = st.text_input(
                                            "Nama Karyawan", value=str(t_nama)
                                        )
                                        e_pasal = st.text_input(
                                            "Pasal Pelanggaran",
                                            value=str(row.get("pasal", ""))
                                        )

                                        current_s = row.get(
                                            "sanksi", "PERSONAL KONTAK"
                                        )
                                        e_sanksi = st.selectbox(
                                            "Jenis Sanksi",
                                            SANKSI_LIST,
                                            index=(
                                                SANKSI_LIST.index(current_s)
                                                if current_s in SANKSI_LIST else 0
                                            )
                                        )

                                        e_tgl_in = st.date_input(
                                            "Tanggal IN",
                                            parse_date(row.get("tgl_in"))
                                        )
                                        e_tgl_out = st.date_input(
                                            "Tanggal OUT",
                                            parse_date(row.get("tgl_out"))
                                        )
                                        e_tambahan = st.text_input(
                                            "Sanksi Tambahan",
                                            value=str(
                                                row.get("sanksi_tambahan") or ""
                                            )
                                        )
                                        e_pelanggaran = st.text_area(
                                            "Uraian Pelanggaran",
                                            value=str(
                                                row.get("pelanggaran") or ""
                                            )
                                        )
                                        e_pic = st.text_input(
                                            "PIC / Atasan",
                                            value=str(row.get("pic") or "")
                                        )
                                        e_ket = st.text_input(
                                            "Keterangan",
                                            value=str(row.get("keterangan") or "")
                                        )

                                        save_edit = st.form_submit_button(
                                            "💾 Simpan Perubahan",
                                            type="primary",
                                            use_container_width=True
                                        )

                                    if save_edit:
                                        if is_duplicate_sanksi(
                                            e_nrp.strip(),
                                            e_sanksi,
                                            e_tgl_in,
                                            e_pelanggaran.strip(),
                                            exclude_id=target_id
                                        ):
                                            st.error(
                                                "⚠️ Data sudah ada! NRP, Jenis "
                                                "Sanksi, Tanggal IN, dan Uraian "
                                                "Pelanggaran sama."
                                            )
                                        else:
                                            upd_payload = {
                                                "tanggal": str(e_tgl),
                                                "nrp": e_nrp.strip(),
                                                "nama": e_nama.strip(),
                                                "pasal": e_pasal,
                                                "sanksi": e_sanksi,
                                                "tgl_in": str(e_tgl_in),
                                                "tgl_out": str(e_tgl_out),
                                                "sanksi_tambahan": e_tambahan.strip(),
                                                "pelanggaran": e_pelanggaran.strip(),
                                                "pic": e_pic.strip(),
                                                "keterangan": e_ket.strip()
                                            }
                                            try:
                                                supabase.table("sanksi").update(
                                                    upd_payload
                                                ).eq(
                                                    "id", target_id
                                                ).execute()
                                                st.toast(
                                                    f"Data {e_nama} berhasil diperbarui!",
                                                    icon="✅"
                                                )
                                                st.rerun()
                                            except Exception as e:
                                                st.error(
                                                    f"Gagal memperbarui data: {e}"
                                                )

                            with c_del:
                                with st.popover(
                                    "🗑️ Hapus", use_container_width=True
                                ):
                                    st.warning(
                                        f"Hapus permanen sanksi **{t_nama}** "
                                        f"(ID: {target_id})?"
                                    )
                                    if st.button(
                                        "🔴 Ya, Hapus",
                                        key=f"del_{target_id}",
                                        type="primary",
                                        use_container_width=True
                                    ):
                                        try:
                                            supabase.table("sanksi").delete().eq(
                                                "id", target_id
                                            ).execute()
                                            st.toast(
                                                f"Data ID {target_id} berhasil dihapus!",
                                                icon="🗑️"
                                            )
                                            st.rerun()
                                        except Exception as e:
                                            st.error(
                                                f"Gagal menghapus data: {e}"
                                            )
            else:
                st.info(
                    "💡 Masukkan NRP atau Nama Karyawan di atas "
                    "untuk memunculkan daftar opsi edit dan hapus."
                )

    else:
        st.info("Belum ada data sanksi.")
