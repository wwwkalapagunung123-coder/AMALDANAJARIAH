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
    / "donasi.sol"
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
    page_icon="🤝",
    layout="wide",
)

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
STATUS_COLOR = {
    "DIBUAT": "🟡",
    "TERKUMPUL": "🟢",
    "DISALURKAN": "🔵",
    "SELESAI": "⚪",
}


def eth(wei_value):
    return w3.from_wei(wei_value, "ether")


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
        st.caption("⚠️ Menggunakan akun Hardhat #0 (development).")
    try:
        acct = w3.eth.account.from_key(key)
        return acct.address, key
    except Exception:
        return None, None


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


def show_tx_result(result):
    if result.get("ok"):
        st.success("✅ Transaksi berhasil dikonfirmasi!")
        st.write(f"**Dari:** `{result['from']}`")
        st.write(f"**Block:** {result['block']} | **Gas used:** {result['gas_used']}")
        st.code(result["tx_hash"], language="text")
    else:
        st.error(f"❌ Transaksi gagal: {result.get('error', 'unknown error')}")


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
# HEADER & NAVIGASI
# =========================================================

st.title("🤝 Amal Transparan")
st.caption("Platform penggalangan dana transparan berbasis blockchain (Hardhat + Web3.py)")

if not w3.is_connected():
    st.error("Tidak dapat terhubung ke Hardhat node di `http://127.0.0.1:8545`. Jalankan `npx hardhat node`.")
    st.stop()

menu = st.sidebar.radio(
    "🧭 Navigasi",
    [
        "📊 Dashboard",
        "📋 Campaign List",
        "➕ Create Campaign",
        "🔍 Campaign Detail",
        "💸 Donation Page",
        "👛 Wallet & Transaction",
    ],
)

st.sidebar.divider()
st.sidebar.subheader("⚙️ Konfigurasi")
st.sidebar.code(CONTRACT_ADDRESS, language="text")
st.sidebar.caption(f"Chain ID: {w3.eth.chain_id} | Block: {w3.eth.block_number}")

# =========================================================
# PAGE: DASHBOARD
# =========================================================

if menu == "📊 Dashboard":
    st.header("📊 Dashboard")

    programs = get_all_programs()
    total_raised = sum(p["terkumpul"] for p in programs)
    total_target = sum(p["target"] for p in programs)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Kampanye", len(programs))
    c2.metric("Total Dana Terkumpul", f"{float(eth(total_raised)):.6f} ETH")
    c3.metric("Total Target Dana", f"{float(eth(total_target)):.6f} ETH")
    c4.metric("Block Terbaru", w3.eth.block_number)

    st.divider()
    st.subheader("Status Blockchain")
    bc1, bc2 = st.columns(2)
    bc1.metric("RPC", RPC_URL)
    bc2.metric("Contract", CONTRACT_ADDRESS[:10] + "..." + CONTRACT_ADDRESS[-6:])

    st.divider()
    st.subheader("Kampanye Terbaru")
    if not programs:
        st.info("Belum ada kampanye. Buat kampanye pertama di menu **Create Campaign**.")
    else:
        for p in programs[-5:][::-1]:
            pct = (p["terkumpul"] / p["target"] * 100) if p["target"] else 0
            status = STATUS_LIST[p["status_enum"]] if p["status_enum"] < 4 else "UNKNOWN"
            with st.container(border=True):
                st.markdown(f"**#{p['token_id']} — {p['nama']}** {STATUS_COLOR.get(status, '')} `{status}`")
                st.progress(min(pct / 100, 1.0), text=f"{pct:.1f}% — {float(eth(p['terkumpul'])):.6f} / {float(eth(p['target'])):.6f} ETH")

# =========================================================
# PAGE: CAMPAIGN LIST
# =========================================================

elif menu == "📋 Campaign List":
    st.header("📋 Daftar Kampanye")
    programs = get_all_programs()

    if not programs:
        st.info("Belum ada kampanye di blockchain.")
    else:
        for p in programs:
            pct = (p["terkumpul"] / p["target"] * 100) if p["target"] else 0
            status = STATUS_LIST[p["status_enum"]] if p["status_enum"] < 4 else "UNKNOWN"
            with st.container(border=True):
                st.markdown(f"### #{p['token_id']} — {p['nama']}")
                st.caption(p["deskripsi"][:120] + ("..." if len(p["deskripsi"]) > 120 else ""))
                st.progress(min(pct / 100, 1.0), text=f"Progres: {pct:.1f}%")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Target", f"{float(eth(p['target'])):.6f} ETH")
                c2.metric("Terkumpul", f"{float(eth(p['terkumpul'])):.6f} ETH")
                c3.metric("Status", f"{STATUS_COLOR.get(status, '')} {status}")
                c4.metric("Dibuat", datetime.fromtimestamp(p["created_at"]).strftime("%d %b %Y"))

# =========================================================
# PAGE: CREATE CAMPAIGN
# =========================================================

elif menu == "➕ Create Campaign":
    st.header("➕ Buat Kampanye Baru")
    st.write("Form ini memanggil fungsi `buatProgramAmal()` pada smart contract (mint NFT sertifikat + simpan data program).")

    with st.form("form_buat_kampanye"):
        nama = st.text_input("Nama Kampanye *")
        deskripsi = st.text_area("Deskripsi Program Amal")
        target_eth = st.number_input("Target Dana (ETH) *", min_value=0.000001, value=0.01, format="%.6f")
        metadata_uri = st.text_input("Metadata URI (opsional)", value="https://example.com/amal.json")
        submitted = st.form_submit_button("Deploy Kampanye ke Blockchain", type="primary")

    if submitted:
        if not nama.strip():
            st.warning("⚠️ Nama kampanye wajib diisi.")
        elif target_eth <= 0:
            st.warning("⚠️ Target dana harus lebih dari 0.")
        else:
            target_wei = w3.to_wei(target_eth, "ether")
            fn = amal_contract.functions.buatProgramAmal(
                nama.strip(), deskripsi.strip(), target_wei, metadata_uri.strip()
            )
            with st.spinner("Mengirim transaksi... (konfirmasi di node Hardhat)"):
                result = send_transaction(fn)
            show_tx_result(result)
            if result.get("ok"):
                st.balloons()
                st.rerun()

# =========================================================
# PAGE: CAMPAIGN DETAIL
# =========================================================

elif menu == "🔍 Campaign Detail":
    st.header("🔍 Detail Kampanye")

    programs = get_all_programs()
    if not programs:
        st.info("Belum ada kampanye.")
    else:
        options = {f"#{p['token_id']} — {p['nama']}": p["token_id"] for p in programs}
        selected = st.selectbox("Pilih Kampanye", list(options.keys()))
        token_id = options[selected]

        data = amal_contract.functions.daftarProgram(token_id).call()
        _, nama, deskripsi, target, terkumpul, status_enum, created_at = data
        status = STATUS_LIST[status_enum] if status_enum < 4 else "UNKNOWN"
        pct = (terkumpul / target * 100) if target else 0

        st.markdown(f"### #{token_id} — {nama}")
        st.write(deskripsi)
        st.progress(min(pct / 100, 1.0), text=f"{pct:.1f}% terkumpul")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Target", f"{float(eth(target)):.6f} ETH")
        c2.metric("Terkumpul", f"{float(eth(terkumpul)):.6f} ETH")
        c3.metric("Status", f"{STATUS_COLOR.get(status, '')} {status}")
        c4.metric("Dibuat", datetime.fromtimestamp(created_at).strftime("%d %b %Y %H:%M"))

        try:
            pengelola = amal_contract.functions.getPengelolaProgram(token_id).call()
            st.write(f"**Pengelola / Pemilik NFT:** `{pengelola}`")
        except Exception:
            pass

        st.divider()
        st.subheader("📜 Riwayat Aliran Dana (Transparansi)")
        try:
            riwayat = amal_contract.functions.getRiwayat(token_id).call()
            if not riwayat:
                st.info("Belum ada riwayat.")
            else:
                rows = [
                    {
                        "Aksi": r[0],
                        "Aktor": r[1],
                        "Jumlah (ETH)": float(eth(r[2])),
                        "Waktu": datetime.fromtimestamp(r[3]).strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    for r in riwayat
                ]
                st.dataframe(rows, width="stretch", hide_index=True)
        except Exception as e:
            st.error(f"Gagal mengambil riwayat: {e}")

# =========================================================
# PAGE: DONATION PAGE
# =========================================================

elif menu == "💸 Donation Page":
    st.header("💸 Halaman Donasi")

    programs = get_all_programs()
    if not programs:
        st.info("Belum ada kampanye untuk didonasikan.")
    else:
        options = {f"#{p['token_id']} — {p['nama']}": p["token_id"] for p in programs}
        selected = st.selectbox("Pilih Kampanye", list(options.keys()), key="donasi_select")
        token_id = options[selected]

        data = amal_contract.functions.daftarProgram(token_id).call()
        _, nama, _, target, terkumpul, status_enum, _ = data
        sisa = max(target - terkumpul, 0)
        pct = (terkumpul / target * 100) if target else 0

        with st.container(border=True):
            st.markdown(f"**{nama}**")
            st.progress(min(pct / 100, 1.0), text=f"{pct:.1f}% dari target")
            st.write(f"Sisa target: **{float(eth(sisa)):.6f} ETH**")

        st.divider()
        with st.form("form_donasi"):
            col_a, col_b = st.columns(2)
            with col_a:
                nominal = st.number_input(
                    "Nominal Donasi (ETH)",
                    min_value=0.000001,
                    max_value=float(eth(sisa)) if sisa > 0 else 0.000001,
                    value=min(0.001, float(eth(sisa)) if sisa > 0 else 0.001),
                    format="%.6f",
                )
            with col_b:
                st.write("")
                st.write("")
                confirm = st.checkbox("Saya mengonfirmasi donasi ini")
            submitted = st.form_submit_button("Kirim Donasi", type="primary")

        if submitted:
            if not confirm:
                st.warning("⚠️ Centang konfirmasi donasi terlebih dahulu.")
            elif nominal <= 0:
                st.warning("⚠️ Nominal donasi harus lebih dari 0.")
            else:
                fn = amal_contract.functions.donasi(token_id)
                with st.spinner(f"Mengirim donasi {nominal} ETH..."):
                    result = send_transaction(fn, value_eth=nominal)
                show_tx_result(result)
                if result.get("ok"):
                    st.rerun()

# =========================================================
# PAGE: WALLET & TRANSACTION
# =========================================================

elif menu == "👛 Wallet & Transaction":
    st.header("👛 Wallet & Transaction")

    st.subheader("Koneksi MetaMask")
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
        st.success(f"Wallet terhubung: `{address}`")

        try:
            wallet_chain = int(wallet["chainId"], 16)
            if wallet_chain == w3.eth.chain_id:
                if st.button("Periksa Saldo ETH"):
                    bal = w3.eth.get_balance(address)
                    st.metric("Saldo ETH", f"{float(eth(bal)):.6f} ETH")
            else:
                st.warning(f"Chain ID MetaMask ({wallet_chain}) ≠ Hardhat ({w3.eth.chain_id}).")
        except Exception as e:
            st.error(f"Gagal memproses wallet: {e}")
    else:
        st.info("Klik **Connect Wallet** untuk menghubungkan MetaMask.")

    st.divider()
    st.subheader("Akun Transaksi (Penandatangan)")
    st.caption(
        "Transaksi dikirim via Web3.py menggunakan private key. "
        "Isi private key akun Hardhat Anda, atau kosongkan untuk pakai akun #0 default."
    )
    pk = st.text_input(
        "Private Key (opsional)",
        type="password",
        key="private_key_input",
        help="Disimpan di session state saja.",
    )
    if pk:
        st.session_state["private_key"] = pk

    tx_address, _ = get_account()
    if tx_address:
        st.write(f"**Akun pengirim transaksi:** `{tx_address}`")
        bal = w3.eth.get_balance(tx_address)
        st.write(f"**Saldo:** {float(eth(bal)):.6f} ETH")

    st.divider()
    st.subheader("Status Transaksi")
    st.info(
        "Setiap hasil transaksi (berhasil / gagal / menunggu konfirmasi) "
        "ditampilkan langsung di halaman Create Campaign dan Donation Page."
    )

st.divider()
st.caption("Amal Transparan — Praktikum Blockchain | Smart contract: `AmalTransparan.sol`")
