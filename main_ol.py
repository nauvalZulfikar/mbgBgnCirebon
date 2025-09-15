# app.py
import os, re, uuid, datetime as dt
from pathlib import Path
import pandas as pd
import streamlit as st

import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Form Pendaftaran SPPG Cirebon", page_icon="📝", layout="centered")

# --- Mock data for cascading dropdowns (extend as needed) ---
WILAYAH = {
    "Kota Cirebon": {
        "Harjamukti": ['Argasunya','Harjamukti','Kalijaga','Kecapi','Larangan'],
        "Kejaksan": ['Kebonbaru','Kejaksan','Kesenden','Sukapura'],
        'Kesambi': ['Drajat','Karyamulya','Kesambi','Pekiringan','Sunyaragi'],
        "Lemahwungkuk": ['Kasepuhan','Lemahwungkuk','Panjunan','Pegambiran'],
        'Pekalipan': ['Jagasatru','Pekalangan','Pekalipan','Pulasaren']
    },
    "Kabupaten Cirebon": {
        "Arjawinangun": ['Arjawinangun','Bulak''Geyongan','Jungjang Wetan','Jungjang','Karang sambung','Kebonturi','Rawagatel','Sende','Tegalgubug','Tegalgubug Lor'],
        'Astanajapura': ['Astanajapura','Buntet','Japura Kidul''Japura bakti','Kanci','Kanci Kulon','Kendal','Mertapada Kulon','Mertapada Wetan','Munjul','Sidamulya'],
        'Babakan': ['Babakan','Babakangebang','Bojonggebang','Cangkuang','Gembongan','Gembonganmekar','KarangwangunvKudukeras','Kudumulya','Pakusamben','Serang Kulon','Serang Wetan','Sumber Kidul','Sumber Lor'],
        'Beber': ['Beber','Ciawigajah','Cikancas','Cipinang','Halimpu','Kondangsari','Patapan','Sindanghayu','Sindangkasih','Wanayasa'],
        'Ciledug': ['Bojongnegara','Ciledug Kulon','Ciledug Lor','Ciledug Tengah','Ciledug Wetan','Damarguna','Jatiseeng','Jatiseeng Kidul','Leuweunggajah','Tenjomaya'],
        'Ciwaringin': ['Babakan','Bringin','Budur','Ciwaringin','Galagamba','Gintung Kidul','Gintung Tengah','Gintungranjeng'],
        'Depok': ['Cikeduk','Depok','Getasan','Karangwangi','Kasugengan Kidul','Kasugengan Lor','Keduanan','Kejuden','Warugede','Warujaya','Warukawung','Waruroyom'],
        'Dukupuntang': ['Balad','Bobos','Cangkoak','Cikalahang','Cipanas','Cisaat','Dukupuntang','Girinata','Kedongdong Kidul','Kepunduan','Mandala','Sindangjawa','Sindangmekar'],
        'Gebang': ['Dompyong Kulon','Dompyong Wetan','Gagasari','Gebang','Gebangilir','Gebangkulon','Gebangmekar','Gebangudik','Kalimaro','Kalimekar','Kalipasung','Melakasari','Pelayangan'],
        'Gegesik': ['Bayalangu Kidul','Bayalangu Lor','Gegesik Kidul','Gegesik Kulon','Gegesik Lor','Gegesik Wetan','Jagapura Kidul','Jagapura Kulon','Jagapura Lor','Jagapura Wetan','Kedungdalem','Panunggul','Sibubut','Slendra'],
        'Gempol': ['Cupang','Cikeusal','Gempol','Kedungbunder','Kempek','Palimanan Barat','Walahar','Winong'],
        'Greged': ['Durajaya','Greged','Gumulunglebak','Gumulungtonggoh','Jatipancur','Kamarang','Kamarang Lebak','Lebakmekar','Nanggela','Sindangkempeng'],
        'Gunungjati': ['Adidharma','Astana','Babadan','Buyut','Grogol','Jadimulya','Jatimerta','Kalisapu','Klayan','Mayung','Mertasinga','Pasindangan','Sambeng','Sirnabaya','Wanakaya'],
        'Jamblang': ['Bakung Kidul','Bakung Lor','Bojong Lor','Bojong Wetan','Jamblang','Orimalang','Sitiwinangun','Wangunharja'],
        'Kaliwedi': ['Guwa Kidul','Guwa Lor','Kalideres','Kaliwedi Kidul','Kaliwedi Lor','Prajawinangun Kulon','Prajawinangun Wetan','Ujungsemi','Wargabinangun'],
        'Kapetakan': ['Bungko','Bungko Lor','Dukuh','Grogol','Kapetakan','Karangkendal','Kertasura','Pegagan Kidul','Pegagan Lor'],
        'karangsembung': ['Kalimeang','Karangmalang','Karangmekar','Karangsembung','Karangsuwung','Karangtengah','Kubangkarang','Tambelang'],
        'Karangwareng': ['Blender','Jatipiring','Karanganyar','Karangasem','Karangwangi','Karangwareng','Kubangdeleg','Seuseupan','Sumurkondang'],
        'Kedawung': ['Kalikoa','Kedawung','Kedungdawa','Kedungjaya','Kertawinangun','Pilangsari','Sutawinangun','Tuk'],
        'Klangenan': ['Bangodua','Danawinangun','Jemaras Kidul','Jemaras Lor','Klangenan','Kreyo','Pekantingan','Serang','Slangit'],
        'Lemah Abang': ['AsemBelawa','Cipeujeuh Kulon','Cipeujeuh Wetan','Lemahabang','Lemahabang Kulon','Leuwidingding','Picungpugur','Sarajaya','Sigong','Sindanglaut','Tuk Karangsuwung','Wangkelang'],
        'Losari': ['Ambulu','Astanalanggar','Barisan','Kalirahayu','Kalisari','Losari Kidul','Losari Lor','Mulyasari','Panggangsari','Tawangsari'],
        'Mundu': ['Bandengan','Banjarwangunan','Citemu','Luwung','Mundumesigit','Mundupesisir','Pamengkang','Penpen','Setupatok','Sinarancang','Suci','Waruduwur'],
        'Pabedilan': ['Babakan Losari','Babakan Losari Lor','Dukuhwidara','Kalibuntu','Kalimukti','Pabedilan Kaler','Pabedilan Kidul','Pabedilan Kulon','Pabedilan Wetan','Pasuruan','Sidaresmi','Silihasih','Tersana'],
        'Pabuaran': ['Hulubanteng','Hulubanteng Lor','Jatirenggang','Pabuaran Kidul','Pabuaran Lor','Pabuaran Wetan','Sukadana'],
        'Palimanan': ['Balerante','Beberan','Cengkuang','Ciawi','Cilukrak','Kepuh','Lungbenda','Palimanan Timur','Panongan','Pegagan','Semplo','Tegalkarang'],
        'Pangenan': ['Astanamukti','Bendungan','Beringin','Ender','Getrakmoyan','Japura Lor','Pangenan','Pangarengan','Rawaurip'],
        'Panguragan': ['Gujeg','Kalianyar','Karanganyar','Kroya','Lemahtamba','Panguragan','Panguragan Kulon','Panguragan Lor','Panguragan Wetan'],
        'Pasaleman': ['Cigobang','Cigobangwangi','Cilengkrang','Cilengkranggirang','Pasaleman','Tanjunganom','Tonjong'],
        'Plered': ['Cangkring','Gamel','Kaliwulu','Panembahan','Pangkalan','Sarabau','Tegalsari','Trusmi Kulon','Trusmi Wetan','Wotgali'],
        'Plumbon': ['Bodelor','Bodesari','Cempaka','Danamulya','Gombang','Karangasem','Karangmulya','Kebarepan','Kedungsana','Lurah','Marikangen','Pamijahan','Pasanggrahan','Plumbon','Purbawinangun'],
        'Sedong': ['Karangwuni','Kertawangun','Panambangan','Panongan','Panongan Lor','Putat','Sedong Kidul','Sedong Lor','Winduhaji','Windujaya'],
        'Sumber': ['Matangaji','Sidawangi','Babakan','Gegunung','Kaliwadas','Kemantren','Kenanga','Pasalakan','Pejambon','Perbutulan','Sendang','Sumber','Tukmudal','Watubelah'],
        'Suranenggala': ['Karangreja','Keraton','Muara','Purwawinangun','Surakarta','Suranenggala','Suranenggala Kidul','Suranenggala Lor','Suranenggala Kulon'],
        'Susukan': ['Bojong Kulon','Bunder','Gintung Lor','Jatianom','Jatipura','Kedongdong','Kejiwan','Luwungkencana','Susukan','Tangkil','Ujunggebang','Wiyong'],
        'Susukanlebak': ['Ciawiasih','Ciawijapura','Curug','Curug Wetan','Kaligawe','Kaligawe Wetan','Karangmanggu','Pasawahan','Sampih','Susukanagung','Susukanlebak','Susukantonggoh','Wilulang'],
        'Talun': ['Cempaka','Ciperna','Cirebon Girang','Kecomberan','Kepongpongan','Kerandon','Kubang','Sampiran','Sarwadadi','Wanasaba Kidul','Wanasaba Lor'],
        'Tengahtani': ['Astapada','Battembat','Dawuan','Gesik','Kalibaru','Kalitengah','Kemlakagede','Palir'],
        'Waled': ['Ambit','Cibogo','Cikulak','Cikulak Kidul','Cisaat','Ciuyah','Gunungsari','Karangsari','Mekarsari','Waledasem','Waleddesa','Waledkota'],
        'Weru': ['','Karangsari','Kertasari','Megu Cilik','Megu Gede','Setu Kulon','Setu Wetan','Tegalwangi','Weru Kidul','Weru Lo'],
    },
}

# --- Storage for local media (kept) ---
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# --- Google Sheets config ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_ID = st.secrets.get("sheets", {}).get("sheet_id")
WS_NAME  = st.secrets.get("sheets", {}).get("worksheet", "FormResponses")

# Define your header order in the sheet:
COLUMNS = [
    "submit_id", "timestamp",
    "nama", "no_telp", "alamat",
    "kota_kab", "kecamatan", "desa",
    "koordinat", "lat", "lon",
    "nama_pemilik", "jenis_sertifikat",
    "luas_tanah_m2", "luas_bangunan_m2", "harga_sewa_rp",
    "foto_luar_path", "foto_dalam_path", "video_path",
]

# --- Helpers ---
COORD_RE = re.compile(r"^\s*(-?\d+(\.\d+)?)\s*,\s*(-?\d+(\.\d+)?)\s*$")

def parse_coords(text: str):
    if not text:
        return None
    m = COORD_RE.match(text)
    if not m:
        return None
    lat, lon = float(m.group(1)), float(m.group(3))
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    return lat, lon

def save_uploaded_file(dest_dir: Path, file):
    if not file:
        return None
    dest_dir.mkdir(parents=True, exist_ok=True)
    fname = dest_dir / file.name
    with open(fname, "wb") as f:
        f.write(file.getbuffer())
    return str(fname)

@st.cache_resource
def get_gs_client():
    if "gcp_service_account" not in st.secrets:
        raise RuntimeError(
            "Missing [gcp_service_account] in secrets. "
            "Add your service account JSON to .streamlit/secret.toml."
        )
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
    return gspread.authorize(creds)

@st.cache_resource
def get_ws():
    if not SHEET_ID:
        raise RuntimeError("Missing [sheets.sheet_id] in secrets.")
    gc = get_gs_client()
    sh = gc.open_by_key(SHEET_ID)
    try:
        ws = sh.worksheet(WS_NAME)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=WS_NAME, rows=1000, cols=len(COLUMNS))
        ws.update([COLUMNS])  # write header
    # Ensure header exists
    values = ws.get_all_values()
    if not values:
        ws.update([COLUMNS])
    return ws

def append_to_gsheet(row: dict):
    """Append a single submission as a row to the worksheet."""
    ws = get_ws()
    # Build row in the declared column order
    out = [row.get(col, "") for col in COLUMNS]
    ws.append_row(out, value_input_option="USER_ENTERED")

# --- UI ---
st.title("FORM PENDAFTARAN SPPG • Kab/Kota Cirebon")
st.caption("Isilah data di bawah. Koordinat format: `-6.71, 108.56`")

# Always visible
nama = st.text_input("NAMA*", placeholder="Nama lengkap")
telp = st.text_input("NO TELP*", placeholder="08xxxxxxxxxx")
alamat = st.text_area("ALAMAT LENGKAP*", placeholder="Jalan, RT/RW, No. Rumah")
kota_kab = st.selectbox("KOTA / KAB*", options=sorted(WILAYAH.keys()), index=None, placeholder="Pilih…")

# KECAMATAN after KOTA/KAB
if kota_kab:
    kec_options = sorted(WILAYAH[kota_kab].keys())
    kecamatan = st.selectbox("KECAMATAN*", options=kec_options, index=None, placeholder="Pilih…")
else:
    kecamatan = None

# DESA after KECAMATAN
if kecamatan:
    desa_options = sorted(WILAYAH[kota_kab][kecamatan])
    desa = st.selectbox("DESA / KELURAHAN*", options=desa_options, index=None, placeholder="Pilih…")
else:
    desa = None

# Reveal the rest after DESA
if desa:
    st.markdown("---")
    koordinat = st.text_input("KOORDINAT LOKASI*", placeholder="-6.71, 108.56 (lat, lon)")
    nama_pemilik = st.text_input("NAMA PEMILIK SHM/SHGB*", placeholder="Nama di sertifikat")
    jenis_sertifikat = st.selectbox("JENIS SERTIFIKAT*", options=["SHM", "SHGB"], index=0)
    luas_tanah = st.number_input("LUAS TANAH (m²)*", min_value=0, step=1)
    luas_bangunan = st.number_input("LUAS BANGUNAN (m²)*", min_value=0, step=1)
    harga_sewa = st.number_input("HARGA SEWA (Rp)*", min_value=0, step=100000)

    st.markdown("**FOTO & VIDEO BANGUNAN**")
    foto_luar = st.file_uploader("BAGIAN LUAR (jpg/png)*", type=["jpg","jpeg","png"], key="foto_luar")
    foto_dalam = st.file_uploader("BAGIAN DALAM (jpg/png)*", type=["jpg","jpeg","png"], key="foto_dalam")
    video = st.file_uploader("VIDEO BANGUNAN (mp4/mov) (opsional)", type=["mp4","mov","m4v"], key="video")

    submit = st.button("KIRIM", use_container_width=True)
else:
    koordinat = nama_pemilik = jenis_sertifikat = None
    luas_tanah = luas_bangunan = harga_sewa = None
    foto_luar = foto_dalam = video = None
    submit = False

# --- Handle submission ---
if submit:
    # Basic required checks
    errors = []
    for k, v in {
        "NAMA": nama, "NO TELP": telp, "ALAMAT": alamat,
        "KOTA/KAB": kota_kab, "KECAMATAN": kecamatan, "DESA": desa,
        "KOORDINAT": koordinat, "NAMA PEMILIK": nama_pemilik,
        "JENIS SERTIFIKAT": jenis_sertifikat,
    }.items():
        if not v and v != 0:
            errors.append(f"- **{k}** wajib diisi.")

    coords = parse_coords(koordinat) if koordinat else None
    if not coords:
        errors.append("- **Koordinat** harus format `lat, lon`, contoh: `-6.71, 108.56`.")
    if foto_luar is None:
        errors.append("- **Foto Bagian Luar** wajib diunggah.")
    if foto_dalam is None:
        errors.append("- **Foto Bagian Dalam** wajib diunggah.")

    if errors:
        st.error("Mohon perbaiki isian berikut:")
        for e in errors:
            st.markdown(e)
    else:
        submit_id = str(uuid.uuid4())[:8]
        stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dest = UPLOAD_DIR / submit_id

        path_luar = save_uploaded_file(dest, foto_luar)
        path_dalam = save_uploaded_file(dest, foto_dalam)
        path_video = save_uploaded_file(dest, video) if video else None

        row = {
            "submit_id": submit_id,
            "timestamp": stamp,
            "nama": nama,
            "no_telp": telp,
            "alamat": alamat,
            "kota_kab": kota_kab,
            "kecamatan": kecamatan,
            "desa": desa,
            "koordinat": koordinat,
            "lat": coords[0],
            "lon": coords[1],
            "nama_pemilik": nama_pemilik,
            "jenis_sertifikat": jenis_sertifikat,
            "luas_tanah_m2": int(luas_tanah) if luas_tanah is not None else None,
            "luas_bangunan_m2": int(luas_bangunan) if luas_bangunan is not None else None,
            "harga_sewa_rp": int(harga_sewa) if harga_sewa is not None else None,
            "foto_luar_path": path_luar,
            "foto_dalam_path": path_dalam,
            "video_path": path_video,
        }

        # === Append to Google Sheets ===
        try:
            append_to_gsheet(row)
            st.success(f"Data terkirim ke Google Sheet! ID: {submit_id}")
        except Exception as e:
            st.error(f"Gagal kirim ke Google Sheet: {e}")
            st.stop()

        # Show summary + previews
        st.subheader("Ringkasan")
        st.json(row)

        st.subheader("Lokasi (preview)")
        st.map(pd.DataFrame([{"lat": row["lat"], "lon": row["lon"]}]), size=10)

        st.subheader("Pratinjau Media")
        if path_luar:
            st.caption("Foto Bagian Luar")
            st.image(path_luar, use_container_width=True)
        if path_dalam:
            st.caption("Foto Bagian Dalam")
            st.image(path_dalam, use_container_width=True)
        if path_video:
            st.caption("Video Bangunan")
            with open(path_video, "rb") as vf:
                st.video(vf.read())

# Optional admin viewer (reads from local CSV no longer needed; view Sheet in Google UI)
st.info("Semua data tersimpan ke Google Sheets. Gunakan spreadsheet untuk melihat/menyaring data.")
