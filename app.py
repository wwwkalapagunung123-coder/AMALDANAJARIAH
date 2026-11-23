import html
import json
import os
from datetime import datetime
from pathlib import Path

import streamlit as st
import streamlit.components.v2 as components
from web3 import Web3

# =========================================================
# KONFIGURASI
# =========================================================

RPC_URL = "http://127.0.0.1:8545"
PROJECT_DIR = Path(__file__).parent
DEPLOYMENT_PATH = PROJECT_DIR / "deployment.json"
ARTIFACT_PATH = (
    PROJECT_DIR
    / "artifacts"
    / "contracts"
    / "crowdfunding.sol"
    / "AmalTransparan.json"
)

# Private key untuk menandatangani transaksi.
# Prioritas: environment variable PRIVATE_KEY, lalu session state,
# fallback: akun Hardhat #0 (hanya untuk development lokal).
HARDHAT_KEY_0 = (
    "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
)

st.set_page_config(
    page_title="Amal Transparan",
    page_icon=":material/volunteer_activism:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# TAMPILAN (CSS) — tema amal jariyah
# Biru = ketenangan, teal = air yang mengalir (jariyah), emas = cahaya kebaikan
# =========================================================

BLUE = "#2563eb"
TEAL = "#0f9d8a"
GOLD = "#d4a017"

# Pola bintang segi-delapan (motif geometris Islami), dipakai tipis di banner
STAR = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='64' height='64'%3E"
    "%3Cg fill='none' stroke='white' stroke-opacity='.13' stroke-width='1.2'%3E"
    "%3Crect x='16' y='16' width='32' height='32'/%3E"
    "%3Crect x='16' y='16' width='32' height='32' transform='rotate(45 32 32)'/%3E"
    "%3C/g%3E%3C/svg%3E"
)

STYLE = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

.stApp, .stApp p, .stApp label, .stApp input, .stApp textarea,
.stApp button, .stApp li, .stApp td, .stApp th {{
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
}}
[data-testid="stIconMaterial"] {{
    font-family: "Material Symbols Rounded" !important;
}}

.block-container {{ padding-top: 2rem; padding-bottom: 3rem; max-width: 1100px; }}
#MainMenu, footer, .stAppDeployButton {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent; }}

/* ---------- Banner utama ---------- */
.st-key-hero {{
    background: url("{STAR}"),
                linear-gradient(120deg, #1e40af 0%, {BLUE} 48%, {TEAL} 100%) !important;
    border-radius: 18px;
    padding: 1.6rem 1.9rem;
    margin-bottom: 2.2rem;
    box-shadow: 0 12px 32px rgba(37,99,235,.28);
}}
.hero-pill {{
    display: inline-block; font-size: .85rem; font-weight: 600;
    padding: .15rem .8rem; border-radius: 999px; margin-bottom: .55rem;
    background: {GOLD}33; color: #fde68a !important; border: 1px solid {GOLD}88;
}}
.hero-title {{
    font-family: 'Amiri', Georgia, serif;
    font-size: 2.4rem; font-weight: 700; line-height: 1.2;
    color: #ffffff !important;
}}
.hero-sub {{ font-size: .95rem; margin-top: .3rem; color: rgba(255,255,255,.88) !important; }}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {{ border-right: 1px solid rgba(128,128,128,.18); }}
.brand {{
    display: flex; align-items: center; gap: .75rem;
    padding: .9rem 1rem; margin-bottom: 1.1rem; border-radius: 14px;
    background: linear-gradient(120deg, #1e40af, {BLUE});
    color: #fff;
}}
.brand-logo {{
    width: 40px; height: 40px; border-radius: 12px;
    background: rgba(255,255,255,.2);
    display: flex; align-items: center; justify-content: center;
    font-family: 'Amiri', Georgia, serif; font-size: 1.6rem; font-weight: 700; color: #fff;
}}
.brand-name {{ font-family: 'Amiri', Georgia, serif; font-weight: 700; font-size: 1.3rem; line-height: 1.1; color: #fff; }}
.brand-sub {{ font-size: .74rem; color: rgba(255,255,255,.85); }}

/* Menu navigasi (tombol) */
section[data-testid="stSidebar"] .stButton > button {{
    justify-content: flex-start; width: 100%;
    padding: .55rem .85rem; border: none; border-radius: 10px;
    font-weight: 500; text-align: left;
}}
section[data-testid="stSidebar"] .stButton > button > div {{ justify-content: flex-start; gap: .55rem; }}
section[data-testid="stSidebar"] .stButton > button[kind="tertiary"] {{ background: transparent; }}
section[data-testid="stSidebar"] .stButton > button[kind="tertiary"]:hover {{ background: rgba(128,128,128,.14); }}
section[data-testid="stSidebar"] .stButton > button[kind="primary"] {{
    background: {BLUE}26; box-shadow: inset 3px 0 0 {BLUE};
}}
section[data-testid="stSidebar"] .stButton > button[kind="primary"] p,
section[data-testid="stSidebar"] .stButton > button[kind="primary"] span {{
    color: #60a5fa !important; font-weight: 700;
}}
section[data-testid="stSidebar"] .stButton {{ margin-bottom: -.35rem; }}

.node-status {{
    display: flex; align-items: center; gap: .5rem;
    padding: .6rem .8rem; border-radius: 10px;
    border: 1px solid rgba(128,128,128,.22); font-size: .82rem;
}}
.dot {{ width: 9px; height: 9px; border-radius: 50%; display: inline-block; }}
.dot.on {{ background: #22c55e; }}
.dot.off {{ background: #ef4444; }}
.net {{ font-size: .76rem; opacity: .7; margin-top: .6rem; line-height: 1.6; }}
.net code {{ font-size: .72rem; }}

.hadith {{
    margin-top: 1.2rem; padding: .9rem 1rem; border-radius: 12px;
    border: 1px solid {GOLD}66; background: {GOLD}14;
    font-family: 'Amiri', Georgia, serif; font-size: 1rem; line-height: 1.55;
}}
.hadith span {{
    display: block; margin-top: .4rem; font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: .72rem; opacity: .65;
}}

/* ---------- Judul halaman ---------- */
.page-title {{
    font-family: 'Amiri', Georgia, serif;
    font-size: 2.3rem; font-weight: 700; margin: 0; line-height: 1.2;
}}
.page-sub {{ opacity: .65; margin: .2rem 0 1.5rem 0; font-size: .95rem; }}
.stApp h2, .stApp h3 {{ font-family: 'Amiri', Georgia, serif; font-weight: 700; }}

/* ---------- Kartu statistik ---------- */
.stat {{
    border: 1px solid rgba(128,128,128,.22); border-radius: 14px;
    padding: 1rem 1.1rem; background: rgba(128,128,128,.05); height: 100%;
    border-top: 3px solid {BLUE};
}}
.stat.teal {{ border-top-color: {TEAL}; }}
.stat.gold {{ border-top-color: {GOLD}; }}
.stat-label {{ font-size: .8rem; opacity: .65; }}
.stat-value {{ font-size: 1.5rem; font-weight: 700; margin-top: .15rem; }}

/* ---------- Kartu aliran kebaikan ---------- */
.flow {{
    border: 1px solid rgba(128,128,128,.22); border-radius: 14px;
    padding: 1.1rem 1.3rem; margin-top: 1rem;
    background: linear-gradient(120deg, {BLUE}12, {TEAL}12);
}}
.flow-title {{ font-family: 'Amiri', Georgia, serif; font-size: 1.2rem; font-weight: 700; }}

/* ---------- Kartu program ---------- */
.camp {{
    border: 1px solid rgba(128,128,128,.22); border-radius: 14px;
    padding: 1.1rem 1.2rem; margin-bottom: .9rem; background: rgba(128,128,128,.04);
}}
.camp-top {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; }}
.camp-title {{ font-size: 1.05rem; font-weight: 600; }}
.camp-id {{ opacity: .5; font-weight: 500; margin-right: .35rem; }}
.camp-desc {{ opacity: .65; font-size: .88rem; margin: .3rem 0 .9rem 0; }}
.badge {{ font-size: .74rem; font-weight: 600; padding: .2rem .65rem; border-radius: 999px; white-space: nowrap; }}
.b-DIBUAT {{ background: {GOLD}26; color: #eab308; }}
.b-TERKUMPUL {{ background: {TEAL}26; color: #2dd4bf; }}
.b-DISALURKAN {{ background: {BLUE}26; color: #60a5fa; }}
.b-SELESAI, .b-UNKNOWN {{ background: rgba(128,128,128,.2); }}

.bar {{ height: 9px; border-radius: 999px; background: rgba(128,128,128,.2); overflow: hidden; }}
.bar > div {{ height: 100%; border-radius: 999px; background: linear-gradient(90deg, {BLUE}, {TEAL}); }}
.camp-meta {{
    display: flex; justify-content: space-between; flex-wrap: wrap; gap: .5rem;
    margin-top: .55rem; font-size: .82rem; opacity: .75;
}}

/* ---------- Alur status (stepper) ---------- */
.steps {{ display: flex; margin: 1.2rem 0 .5rem 0; }}
.step {{ flex: 1; text-align: center; position: relative; }}
.step:not(:first-child)::before {{
    content: ""; position: absolute; top: 21px; left: -50%; width: 100%; height: 3px;
    background: rgba(128,128,128,.28); z-index: 0;
}}
.step.done:not(:first-child)::before, .step.now:not(:first-child)::before {{
    background: linear-gradient(90deg, {BLUE}, {TEAL});
}}
.step-dot {{
    position: relative; z-index: 1; width: 44px; height: 44px; margin: 0 auto;
    border-radius: 50%; display: flex; align-items: center; justify-content: center;
    font-size: 1.05rem; font-weight: 700; background: rgba(128,128,128,.2); opacity: .6;
}}
.step.done .step-dot {{ background: linear-gradient(120deg, {BLUE}, {TEAL}); color: #fff; opacity: 1; }}
.step.now .step-dot {{
    background: rgba(128,128,128,.12); opacity: 1;
    border: 2px solid {BLUE}; box-shadow: 0 0 0 4px {BLUE}33;
}}
.step-lb {{ font-size: .8rem; margin-top: .4rem; opacity: .6; }}
.step.done .step-lb, .step.now .step-lb {{ opacity: 1; font-weight: 600; }}

/* ---------- Jejak dana (timeline) ---------- */
.tl {{ margin: .8rem 0 1rem 1.2rem; border-left: 2px solid rgba(128,128,128,.3); }}
.tl-item {{ position: relative; padding: 0 0 1.2rem 1.6rem; }}
.tl-dot {{
    position: absolute; left: -9px; top: 3px; width: 16px; height: 16px; border-radius: 50%;
    box-shadow: 0 0 0 4px rgba(128,128,128,.15);
}}
.tl-head {{ font-weight: 600; }}
.tl-meta {{ font-size: .8rem; opacity: .65; margin-top: .1rem; }}
.tl-note {{
    margin-top: .35rem; font-size: .86rem; padding: .45rem .75rem; border-radius: 8px;
    border-left: 3px solid {GOLD}; background: {GOLD}14;
}}

/* ---------- Kotak info ---------- */
.note {{
    border-left: 3px solid {GOLD}; background: {GOLD}14;
    padding: .8rem 1rem; border-radius: 0 10px 10px 0; font-size: .88rem;
}}
.doa {{
    margin-top: .6rem; padding: .8rem 1rem; border-radius: 12px; text-align: center;
    border: 1px solid {GOLD}66; background: {GOLD}14;
    font-family: 'Amiri', Georgia, serif; font-size: 1.1rem;
}}

/* Form & tombol */
div[data-testid="stForm"] {{ border-radius: 14px; border: 1px solid rgba(128,128,128,.22); padding: 1.2rem; }}
div[data-testid="stFormSubmitButton"] > button {{ border-radius: 10px; font-weight: 600; }}
div[data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"] {{
    background: linear-gradient(120deg, {BLUE}, {TEAL}); border: none; color: #fff;
}}
</style>
"""
st.markdown(STYLE, unsafe_allow_html=True)

# =========================================================
# KONEKSI BLOCKCHAIN & KONTRAK
# =========================================================

w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 5}))

if not DEPLOYMENT_PATH.exists():
    st.error("File deployment.json tidak ditemukan. Deploy contract dulu.")
    st.stop()

with open(DEPLOYMENT_PATH, "r") as f:
    deployment_data = json.load(f)

CONTRACT_ADDRESS = Web3.to_checksum_address(deployment_data["address"])

if not ARTIFACT_PATH.exists():
    st.error("Artifact contract tidak ditemukan. Jalankan `npx hardhat compile`.")
    st.stop()

with open(ARTIFACT_PATH, "r") as f:
    contract_artifact = json.load(f)

CONTRACT_ABI = contract_artifact["abi"]
amal_contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

STATUS_LIST = ["DIBUAT", "TERKUMPUL", "DISALURKAN", "SELESAI"]
STATUS_LABEL = {
    "DIBUAT": "Dibuat",
    "TERKUMPUL": "Terkumpul",
    "DISALURKAN": "Disalurkan",
    "SELESAI": "Selesai",
    "UNKNOWN": "Tidak diketahui",
}


def eth(wei_value):
    return w3.from_wei(wei_value, "ether")


def fmt_eth(wei_value):
    return f"{float(eth(wei_value)):.4f} ETH"


def status_name(status_enum):
    return STATUS_LIST[status_enum] if status_enum < len(STATUS_LIST) else "UNKNOWN"


def get_all_programs():
    """Iterasi tokenId 1..N sampai program tidak ditemukan."""
    programs = []
    token_id = 1
    while token_id <= 200:
        try:
            data = amal_contract.functions.daftarProgram(token_id).call()
        except Exception:
            break
        if data[0] == 0:
            break
        programs.append(
            {
                "token_id": data[0],
                "nama": data[1],
                "deskripsi": data[2],
                "target": data[3],
                "terkumpul": data[4],
                "status_enum": data[5],
                "created_at": data[6],
            }
        )
        token_id += 1
    return programs


def get_account():
    """Ambil private key dari env / session state, return (address, key)."""
    key = os.environ.get("PRIVATE_KEY", "").strip()
    if not key:
        key = st.session_state.get("private_key", "").strip()
    if not key:
        key = HARDHAT_KEY_0
    try:
        acct = w3.eth.account.from_key(key)
        return acct.address, key
    except Exception:
        return None, None


def using_default_key():
    return not (
        os.environ.get("PRIVATE_KEY", "").strip()
        or st.session_state.get("private_key", "").strip()
    )


def send_transaction(fn_call, value_eth=0.0):
    """Kirim transaksi, return dict berisi status receipt."""
    address, key = get_account()
    if not address:
        return {"ok": False, "error": "Private key tidak valid."}

    try:
        nonce = w3.eth.get_transaction_count(address)
        tx = fn_call.build_transaction(
            {
                "from": address,
                "nonce": nonce,
                "value": w3.to_wei(value_eth, "ether"),
                "gas": 500000,
                "gasPrice": w3.eth.gas_price,
                "chainId": w3.eth.chain_id,
            }
        )
        signed = w3.eth.account.sign_transaction(tx, key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        return {
            "ok": receipt.status == 1,
            "tx_hash": tx_hash.hex(),
            "gas_used": receipt.gasUsed,
            "block": receipt.blockNumber,
            "from": address,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def show_tx_result(result, doa=None):
    if result.get("ok"):
        st.success("Alhamdulillah, transaksi berhasil dikonfirmasi.")
        c1, c2 = st.columns(2)
        c1.write(f"**Block:** {result['block']}")
        c2.write(f"**Gas terpakai:** {result['gas_used']}")
        st.caption(f"Dari: `{result['from']}`")
        st.code(result["tx_hash"], language="text")
        if doa:
            st.markdown(f'<div class="doa">{html.escape(doa)}</div>', unsafe_allow_html=True)
    else:
        st.error(f"Transaksi gagal: {result.get('error', 'unknown error')}")


# =========================================================
# KOMPONEN UI
# =========================================================


def page_header(title, subtitle=""):
    st.markdown(
        f'<h1 class="page-title">{html.escape(title)}</h1>'
        f'<p class="page-sub">{html.escape(subtitle)}</p>',
        unsafe_allow_html=True,
    )


def stat_card(label, value, tone=""):
    return (
        f'<div class="stat {tone}"><div class="stat-label">{html.escape(label)}</div>'
        f'<div class="stat-value">{html.escape(str(value))}</div></div>'
    )


def campaign_card(p, full_desc=False):
    pct = (p["terkumpul"] / p["target"] * 100) if p["target"] else 0
    status = status_name(p["status_enum"])
    desc = p["deskripsi"]
    if not full_desc and len(desc) > 140:
        desc = desc[:140] + "..."
    created = datetime.fromtimestamp(p["created_at"]).strftime("%d %b %Y")
    return "".join(
        [
            '<div class="camp"><div class="camp-top">',
            f'<div class="camp-title"><span class="camp-id">#{p["token_id"]}</span>{html.escape(p["nama"])}</div>',
            f'<span class="badge b-{status}">{STATUS_LABEL[status]}</span></div>',
            f'<div class="camp-desc">{html.escape(desc) if desc else "Tidak ada deskripsi."}</div>',
            f'<div class="bar"><div style="width:{min(pct, 100):.1f}%"></div></div>',
            '<div class="camp-meta">',
            f'<span><b>{fmt_eth(p["terkumpul"])}</b> dari {fmt_eth(p["target"])} ({pct:.1f}%)</span>',
            f"<span>Dibuat {created}</span></div></div>",
        ]
    )


def campaign_select(label, key=None):
    programs = get_all_programs()
    if not programs:
        return None, None
    options = {f"#{p['token_id']} — {p['nama']}": p for p in programs}
    selected = st.selectbox(label, list(options.keys()), key=key)
    return options[selected], programs


ALUR_STATUS = [("1", "Dibuat"), ("2", "Terkumpul"), ("3", "Disalurkan"), ("4", "Selesai")]


def stepper(status_enum):
    parts = []
    for i, langkah in enumerate(ALUR_STATUS):
        icon, label = langkah[0], langkah[1]
        if status_enum >= 3 or i < status_enum:
            cls = "done"
        elif i == status_enum:
            cls = "now"
        else:
            cls = ""
        parts.append(
            f'<div class="step {cls}"><div class="step-dot">{icon}</div>'
            f'<div class="step-lb">{label}</div></div>'
        )
    return '<div class="steps">' + "".join(parts) + "</div>"


AKSI_META = {
    "PROGRAM_DIBUAT": ("#2563eb", "Program dibuat", "Pengelola"),
    "DONASI_DITERIMA": ("#0f9d8a", "Donasi diterima", "Donatur"),
    "DANA_DISALURKAN": ("#d4a017", "Dana disalurkan", "Penerima"),
    "PROGRAM_SELESAI": ("#22c55e", "Program selesai", "Pengelola"),
}


def short_addr(a):
    return f"{a[:8]}…{a[-6:]}"


def timeline(riwayat):
    items = []
    for r in riwayat:
        warna, label, peran = AKSI_META.get(r[0], ("#888888", r[0], "Aktor"))
        jumlah = f" · <b>{fmt_eth(r[2])}</b>" if r[2] else ""
        note = f'<div class="tl-note">{html.escape(r[4])}</div>' if len(r) > 4 and r[4] else ""
        waktu = datetime.fromtimestamp(r[3]).strftime("%d %b %Y, %H:%M")
        items.append(
            f'<div class="tl-item"><div class="tl-dot" style="background:{warna}"></div><div>'
            f'<div class="tl-head">{label}{jumlah}</div>'
            f'<div class="tl-meta">{peran}: <code>{short_addr(r[1])}</code> · {waktu}</div>'
            f"{note}</div></div>"
        )
    return '<div class="tl">' + "".join(items) + "</div>"


# =========================================================
# KOMPONEN METAMASK (display wallet saja)
# =========================================================

WALLET_HTML = """
<div>
  <button id="connect-wallet" type="button">Connect Wallet</button>
  <button id="disconnect-wallet" type="button" style="display:none; background-color:#d9534f; margin-left:10px;">Putuskan Wallet</button>
  <p id="wallet-status">Wallet belum terhubung.</p>
</div>
"""

WALLET_CSS = """
button {
    padding: 0.6rem 1rem;
    border: none;
    border-radius: 8px;
    background: var(--st-primary-color);
    color: white;
    font-weight: 600;
    cursor: pointer;
}
button#disconnect-wallet { background-color: #d9534f; }
p { color: var(--st-text-color); overflow-wrap: anywhere; }
"""

WALLET_JS = """
export default function(component) {
    const { parentElement, setStateValue } = component;
    const connectBtn = parentElement.querySelector("#connect-wallet");
    const disconnectBtn = parentElement.querySelector("#disconnect-wallet");
    const status = parentElement.querySelector("#wallet-status");
    let mounted = true;

    function updateUI(isConnected, address = "") {
        if (!mounted) return;
        connectBtn.style.display = isConnected ? "none" : "inline-block";
        disconnectBtn.style.display = isConnected ? "inline-block" : "none";
        status.textContent = isConnected ? "Wallet terhubung: " + address : "Wallet belum terhubung.";
    }

    async function readWallet() {
        if (!window.ethereum) return;
        const accounts = await window.ethereum.request({ method: "eth_accounts" });
        const chainId = await window.ethereum.request({ method: "eth_chainId" });
        if (!mounted) return;
        if (accounts && accounts.length > 0) {
            setStateValue("wallet", { address: accounts[0], chainId: chainId, connected: true });
            updateUI(true, accounts[0]);
        } else {
            setStateValue("wallet", { address: "", chainId: chainId, connected: false });
            updateUI(false);
        }
    }

    async function connectWallet() {
        if (!window.ethereum) {
            status.textContent = "MetaMask tidak ditemukan.";
            return;
        }
        try {
            status.textContent = "Menunggu persetujuan akses akun...";
            await window.ethereum.request({ method: "eth_requestAccounts" });
            await readWallet();
        } catch (error) {
            status.textContent = "Koneksi gagal: " + (error.message || "error");
        }
    }

    function disconnectWallet() {
        if (!mounted) return;
        setStateValue("wallet", { address: "", chainId: "", connected: false });
        updateUI(false);
        status.textContent = "Wallet diputus dari aplikasi.";
    }

    connectBtn.addEventListener("click", connectWallet);
    disconnectBtn.addEventListener("click", disconnectWallet);

    if (window.ethereum) {
        window.ethereum.on("accountsChanged", (accounts) => {
            if (accounts && accounts.length > 0) readWallet();
            else disconnectWallet();
        });
        readWallet().catch(() => {});
    }

    return () => {
        mounted = false;
        connectBtn.removeEventListener("click", connectWallet);
        disconnectBtn.removeEventListener("click", disconnectWallet);
    };
}
"""

wallet_component = components.component(
    name="amal_metamask_wallet_toggle",
    html=WALLET_HTML,
    css=WALLET_CSS,
    js=WALLET_JS,
)

# =========================================================
# SIDEBAR
# =========================================================

connected = w3.is_connected()

# (label, ikon Material)
NAV_ITEMS = [
    ("Beranda", ":material/dashboard:"),
    ("Program Amal", ":material/format_list_bulleted:"),
    ("Buat Program", ":material/add_circle:"),
    ("Detail & Riwayat", ":material/manage_search:"),
    ("Sedekah", ":material/volunteer_activism:"),
    ("Penyaluran", ":material/send:"),
    ("Dompet", ":material/account_balance_wallet:"),
]
NAV_LABELS = [n[0] for n in NAV_ITEMS]

if "menu" not in st.session_state:
    st.session_state["menu"] = NAV_LABELS[0]

with st.sidebar:
    st.markdown(
        "".join(
            [
                '<div class="brand"><div class="brand-logo">A</div><div>',
                '<div class="brand-name">Amal Transparan</div>',
                '<div class="brand-sub">Sedekah jariyah, tercatat jelas</div>',
                "</div></div>",
            ]
        ),
        unsafe_allow_html=True,
    )

    for i, (label, icon) in enumerate(NAV_ITEMS):
        active = st.session_state["menu"] == label
        if st.button(
            label,
            icon=icon,
            key=f"nav_{i}",
            type="primary" if active else "tertiary",
            use_container_width=True,
        ):
            st.session_state["menu"] = label
            st.rerun()

    st.divider()

    if connected:
        st.markdown(
            f'<div class="node-status"><span class="dot on"></span>'
            f"Node terhubung · Block {w3.eth.block_number}</div>"
            f'<div class="net">Kontrak: <code>{CONTRACT_ADDRESS[:8]}…{CONTRACT_ADDRESS[-6:]}</code><br>'
            f"Chain ID: {w3.eth.chain_id}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="node-status"><span class="dot off"></span>Node tidak terhubung</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="hadith">“Apabila manusia meninggal, terputuslah amalnya kecuali tiga: '
        "sedekah jariyah, ilmu yang bermanfaat, dan doa anak saleh.”"
        "<span>HR. Muslim</span></div>",
        unsafe_allow_html=True,
    )

menu = st.session_state["menu"]

if not connected:
    st.error(
        "Tidak dapat terhubung ke Hardhat node di `http://127.0.0.1:8545`. "
        "Jalankan `npx hardhat node`."
    )
    st.stop()

# =========================================================
# BANNER UTAMA (blok biru, terpisah dari konten halaman)
# =========================================================

with st.container(key="hero"):
    st.markdown(
        '<span class="hero-pill">صدقة جارية</span>'
        '<div class="hero-title">Amal Transparan</div>'
        '<div class="hero-sub">Platform penggalangan dana transparan berbasis '
        "blockchain (Hardhat + Web3.py)</div>",
        unsafe_allow_html=True,
    )

# =========================================================
# PAGE: BERANDA
# =========================================================

if menu == "Beranda":
    page_header("Beranda", "Ringkasan seluruh program amal yang tercatat di blockchain.")

    programs = get_all_programs()
    total_raised = sum(p["terkumpul"] for p in programs)
    total_target = sum(p["target"] for p in programs)
    pct_total = (total_raised / total_target * 100) if total_target else 0

    c1, c2, c3 = st.columns(3)
    c1.markdown(stat_card("Total program", len(programs)), unsafe_allow_html=True)
    c2.markdown(stat_card("Dana terkumpul", fmt_eth(total_raised), "teal"), unsafe_allow_html=True)
    c3.markdown(stat_card("Total target", fmt_eth(total_target), "gold"), unsafe_allow_html=True)

    st.markdown(
        "".join(
            [
                '<div class="flow"><div class="flow-title">Aliran kebaikan</div>',
                f'<div class="camp-meta"><span>{fmt_eth(total_raised)} dari {fmt_eth(total_target)}</span>',
                f"<span>{pct_total:.1f}%</span></div>",
                f'<div class="bar"><div style="width:{min(pct_total, 100):.1f}%"></div></div></div>',
            ]
        ),
        unsafe_allow_html=True,
    )

    st.write("")
    st.subheader("Program terbaru")
    if not programs:
        st.info("Belum ada program. Mulai kebaikan pertama di menu **Buat Program**.")
    else:
        for p in programs[-5:][::-1]:
            st.markdown(campaign_card(p), unsafe_allow_html=True)

# =========================================================
# PAGE: PROGRAM AMAL
# =========================================================

elif menu == "Program Amal":
    page_header("Program Amal", "Semua program yang tercatat di smart contract.")
    programs = get_all_programs()

    if not programs:
        st.info("Belum ada program di blockchain.")
    else:
        filter_status = st.pills(
            "Filter status",
            ["Semua"] + [s.capitalize() for s in STATUS_LIST],
            default="Semua",
        )
        shown = [
            p
            for p in programs
            if filter_status in (None, "Semua")
            or status_name(p["status_enum"]).capitalize() == filter_status
        ]
        st.caption(f"Menampilkan {len(shown)} dari {len(programs)} program")
        left, right = st.columns(2)
        for i, p in enumerate(shown):
            (left if i % 2 == 0 else right).markdown(
                campaign_card(p), unsafe_allow_html=True
            )

# =========================================================
# PAGE: BUAT PROGRAM
# =========================================================

elif menu == "Buat Program":
    page_header("Buat Program", "Niatkan kebaikan, lalu catat di blockchain agar transparan.")

    form_col, info_col = st.columns([3, 2], gap="large")

    with form_col:
        with st.form("form_buat_kampanye", border=True):
            nama = st.text_input("Nama program *")
            deskripsi = st.text_area("Deskripsi", height=120)
            target_eth = st.number_input(
                "Target dana (ETH) *", min_value=0.000001, value=0.01, format="%.6f"
            )
            metadata_uri = st.text_input(
                "Metadata URI (opsional)", value="https://example.com/amal.json"
            )
            submitted = st.form_submit_button(
                "Buat program", type="primary", use_container_width=True
            )

    with info_col:
        st.markdown(
            '<div class="note"><b>Apa yang terjadi?</b><br>'
            "Form ini memanggil <code>buatProgramAmal()</code> pada smart contract: "
            "data program disimpan dan sebuah NFT sertifikat dicetak untuk pengelola. "
            "Semua aliran dana bisa ditelusuri siapa saja.</div>",
            unsafe_allow_html=True,
        )

    if submitted:
        if not nama.strip():
            st.warning("Nama program wajib diisi.")
        elif target_eth <= 0:
            st.warning("Target dana harus lebih dari 0.")
        else:
            target_wei = w3.to_wei(target_eth, "ether")
            fn = amal_contract.functions.buatProgramAmal(
                nama.strip(), deskripsi.strip(), target_wei, metadata_uri.strip()
            )
            with st.spinner("Mengirim transaksi..."):
                result = send_transaction(fn)
            show_tx_result(result)
            if result.get("ok"):
                st.balloons()

# =========================================================
# PAGE: DETAIL & RIWAYAT
# =========================================================

elif menu == "Detail & Riwayat":
    page_header("Detail & Riwayat", "Telusuri data program dan setiap aliran dananya.")

    p, programs = campaign_select("Pilih program")
    if not programs:
        st.info("Belum ada program.")
    else:
        token_id = p["token_id"]
        st.markdown(campaign_card(p, full_desc=True), unsafe_allow_html=True)
        st.markdown(stepper(p["status_enum"]), unsafe_allow_html=True)

        try:
            pengelola = amal_contract.functions.getPengelolaProgram(token_id).call()
            st.caption("Pengelola / pemilik NFT")
            st.code(pengelola, language="text")
        except Exception:
            pass

        st.subheader("Jejak dana")
        try:
            riwayat = amal_contract.functions.getRiwayat(token_id).call()
            if not riwayat:
                st.info("Belum ada riwayat.")
            else:
                st.markdown(timeline(riwayat), unsafe_allow_html=True)
                with st.expander("Lihat tabel lengkap"):
                    rows = [
                        {
                            "Aksi": r[0],
                            "Alamat": r[1],
                            "Jumlah (ETH)": float(eth(r[2])),
                            "Waktu": datetime.fromtimestamp(r[3]).strftime("%Y-%m-%d %H:%M:%S"),
                            "Keterangan": r[4] if len(r) > 4 else "",
                        }
                        for r in riwayat
                    ]
                    st.dataframe(rows, width="stretch", hide_index=True)
        except Exception as e:
            st.error(f"Gagal mengambil riwayat: {e}")

# =========================================================
# PAGE: SEDEKAH (DONASI)
# =========================================================

elif menu == "Sedekah":
    page_header("Sedekah", "Salurkan donasi ke program pilihan Anda.")

    p, programs = campaign_select("Pilih program", key="donasi_select")
    if not programs:
        st.info("Belum ada program untuk didonasikan.")
    else:
        token_id = p["token_id"]
        sisa = max(p["target"] - p["terkumpul"], 0)

        info_col, form_col = st.columns([3, 2], gap="large")

        with info_col:
            st.markdown(campaign_card(p), unsafe_allow_html=True)
            st.caption(f"Sisa target: **{fmt_eth(sisa)}**")

        submitted = False
        nominal = 0.0
        confirm = False
        with form_col:
            if p["status_enum"] >= 2:
                st.info("Program ini sudah ditutup untuk donasi karena dana telah disalurkan.")
            elif sisa <= 0:
                st.success("Target program sudah tercapai. Terima kasih para donatur!")
            else:
                with st.form("form_donasi", border=True):
                    max_val = float(eth(sisa))
                    nominal = st.number_input(
                        "Nominal donasi (ETH)",
                        min_value=0.000001,
                        max_value=max_val,
                        value=min(0.001, max_val),
                        format="%.6f",
                    )
                    confirm = st.checkbox("Saya mengonfirmasi donasi ini")
                    submitted = st.form_submit_button(
                        "Kirim sedekah", type="primary", use_container_width=True
                    )

        if submitted:
            if not confirm:
                st.warning("Centang konfirmasi donasi terlebih dahulu.")
            elif nominal <= 0:
                st.warning("Nominal donasi harus lebih dari 0.")
            else:
                fn = amal_contract.functions.donasi(token_id)
                with st.spinner(f"Mengirim donasi {nominal} ETH..."):
                    result = send_transaction(fn, value_eth=nominal)
                show_tx_result(
                    result,
                    doa="Jazakumullahu khairan. Semoga menjadi sedekah jariyah "
                    "yang pahalanya terus mengalir.",
                )

# =========================================================
# PAGE: PENYALURAN
# =========================================================

elif menu == "Penyaluran":
    page_header("Penyaluran", "Salurkan dana terkumpul ke penerima manfaat, lalu tutup program.")

    flash = st.session_state.pop("flash_tx", None)
    if flash:
        show_tx_result(flash["result"], flash.get("doa"))

    has_salur = any(x.get("name") == "salurkanDana" for x in CONTRACT_ABI)

    p, programs = campaign_select("Pilih program", key="salur_select")
    if not programs:
        st.info("Belum ada program.")
    elif not has_salur:
        st.warning(
            "Kontrak yang ter-deploy belum punya fungsi `salurkanDana` dan `selesaikanProgram`. "
            "Pakai `crowdfunding.sol` versi terbaru, jalankan `npx hardhat compile`, "
            "lalu deploy ulang."
        )
    else:
        token_id = p["token_id"]
        status_enum = p["status_enum"]
        st.markdown(campaign_card(p), unsafe_allow_html=True)
        st.markdown(stepper(status_enum), unsafe_allow_html=True)

        try:
            pengelola = amal_contract.functions.getPengelolaProgram(token_id).call()
        except Exception:
            pengelola = None
        akun, _ = get_account()
        is_owner = bool(pengelola and akun and pengelola.lower() == akun.lower())

        st.write("")
        if is_owner:
            st.success("Akun penandatangan adalah pengelola program ini.")
        else:
            st.warning(
                "Hanya pengelola (pemilik NFT) yang bisa menyalurkan dan menyelesaikan program. "
                f"Pengelola: `{pengelola}`. Atur akun di menu **Dompet**."
            )

        if status_enum == 0:
            sisa = max(p["target"] - p["terkumpul"], 0)
            st.info(
                f"Program masih menggalang dana. Sisa target: **{fmt_eth(sisa)}**. "
                "Penyaluran dibuka setelah target tercapai."
            )

        elif status_enum == 1:
            with st.form("form_salur", border=True):
                st.markdown(f"Dana yang akan disalurkan: **{fmt_eth(p['terkumpul'])}**")
                penerima = st.text_input("Alamat penerima manfaat *", placeholder="0x...")
                keterangan = st.text_input(
                    "Keterangan penyaluran",
                    placeholder="mis. Pembangunan sumur di Desa Sukamaju",
                )
                confirm = st.checkbox("Saya memastikan alamat penerima sudah benar")
                submitted = st.form_submit_button(
                    "Salurkan dana",
                    type="primary",
                    use_container_width=True,
                    disabled=not is_owner,
                )
            st.caption(
                "Untuk simulasi, pakai akun Hardhat lain sebagai penerima, "
                "misalnya Hardhat #1: `0x70997970C51812dc3A010C7d01b50e0d17dc79C8`"
            )

            if submitted:
                if not Web3.is_address(penerima.strip()):
                    st.warning("Alamat penerima tidak valid.")
                elif not confirm:
                    st.warning("Centang konfirmasi alamat penerima terlebih dahulu.")
                else:
                    fn = amal_contract.functions.salurkanDana(
                        token_id,
                        Web3.to_checksum_address(penerima.strip()),
                        keterangan.strip(),
                    )
                    with st.spinner("Menyalurkan dana..."):
                        result = send_transaction(fn)
                    if result.get("ok"):
                        st.session_state["flash_tx"] = {
                            "result": result,
                            "doa": "Semoga amanah ini sampai kepada yang berhak dan menjadi kebaikan yang terus mengalir.",
                        }
                        st.rerun()
                    else:
                        show_tx_result(result)

        elif status_enum == 2:
            with st.form("form_selesai", border=True):
                st.markdown("Dana sudah disalurkan. Tutup program dengan catatan penyelesaian.")
                catatan = st.text_input(
                    "Catatan penyelesaian",
                    placeholder="mis. Sumur selesai dibangun dan sudah dipakai warga",
                )
                submitted = st.form_submit_button(
                    "Tandai program selesai",
                    type="primary",
                    use_container_width=True,
                    disabled=not is_owner,
                )

            if submitted:
                fn = amal_contract.functions.selesaikanProgram(token_id, catatan.strip())
                with st.spinner("Menutup program..."):
                    result = send_transaction(fn)
                if result.get("ok"):
                    st.session_state["flash_tx"] = {
                        "result": result,
                        "doa": "Alhamdulillah, program selesai. Semoga menjadi amal jariyah bagi semua yang terlibat.",
                    }
                    st.rerun()
                else:
                    show_tx_result(result)

        else:
            st.success("Program ini sudah selesai. Lihat perjalanan dananya di menu **Detail & Riwayat**.")


# =========================================================
# PAGE: DOMPET
# =========================================================

elif menu == "Dompet":
    page_header("Dompet", "Hubungkan MetaMask dan atur akun penandatangan transaksi.")

    left, right = st.columns(2, gap="large")

    with left:
        st.subheader("MetaMask")
        wallet_result = wallet_component(
            key="amal_metamask",
            default={"wallet": {"address": "", "chainId": "", "connected": False}},
            on_wallet_change=lambda: None,
        )

        wallet = {}
        if isinstance(wallet_result, dict):
            wallet = wallet_result.get("wallet", {})

        if wallet.get("connected") and wallet.get("address"):
            address = Web3.to_checksum_address(wallet["address"])
            st.success("Wallet terhubung.")
            st.code(address, language="text")

            try:
                wallet_chain = int(wallet["chainId"], 16)
                if wallet_chain == w3.eth.chain_id:
                    if st.button("Periksa saldo ETH"):
                        bal = w3.eth.get_balance(address)
                        st.metric("Saldo", fmt_eth(bal))
                else:
                    st.warning(
                        f"Chain ID MetaMask ({wallet_chain}) berbeda dengan Hardhat ({w3.eth.chain_id})."
                    )
            except Exception as e:
                st.error(f"Gagal memproses wallet: {e}")
        else:
            st.info("Klik **Connect Wallet** untuk menghubungkan MetaMask.")

    with right:
        st.subheader("Akun penandatangan")
        st.caption(
            "Transaksi dikirim lewat Web3.py memakai private key. "
            "Kosongkan untuk memakai akun Hardhat #0 (khusus development)."
        )
        pk = st.text_input(
            "Private key (opsional)",
            type="password",
            key="private_key_input",
            help="Hanya disimpan di session state.",
        )
        if pk:
            st.session_state["private_key"] = pk

        tx_address, _ = get_account()
        if tx_address:
            if using_default_key():
                st.warning("Memakai akun Hardhat #0 (development).")
            st.caption("Akun pengirim")
            st.code(tx_address, language="text")
            st.metric("Saldo", fmt_eth(w3.eth.get_balance(tx_address)))
        else:
            st.error("Private key tidak valid.")

    st.markdown(
        '<div class="note">Hasil transaksi (berhasil atau gagal) ditampilkan langsung '
        "di halaman <b>Buat Program</b> dan <b>Sedekah</b>.</div>",
        unsafe_allow_html=True,
    )

st.write("")
st.caption(
    "Amal Transparan — Praktikum Blockchain · Smart contract: `AmalTransparan.sol` · "
    "Semoga setiap kebaikan menjadi amal jariyah."
)