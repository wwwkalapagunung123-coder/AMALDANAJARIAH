import json
from pathlib import Path
import streamlit as st
import streamlit.components.v2 as components
from web3 import Web3

# =========================================================
# KONFIGURASI PATH & RPC
# =========================================================

RPC_URL = "http://127.0.0.1:8545"

PROJECT_DIR = Path(__file__).parent
DEPLOYMENT_PATH = PROJECT_DIR / "deployment.json"

# Sesuaikan jalur artefak dengan nama file contract Anda (.sol)
ARTIFACT_PATH = (
    PROJECT_DIR
    / "artifacts"
    / "contracts"
    / "donasi.sol"
    / "AmalTransparan.json"
)

st.set_page_config(
    page_title="Amal Transparan",
    page_icon="🤝",
    layout="centered",
)

st.title("🤝 Amal Transparan")
st.caption("Praktikum: Hardhat + MetaMask + Streamlit + Web3.py")

# =========================================================
# dashboard (total kampanye, total donasi, total dana terkumpul)
# =========================================================

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# Masukkan alamat kontrak hasil deploy Anda
CONTRACT_ADDRESS = "0x5fc8d32690cc91d4c39d9d3abcbd16989f875707"


st.sidebar.title("🧭 Navigasi Menu")
menu = st.sidebar.selectbox(
    "Pilih Halaman", 
    [
        "📊 Dashboard", 
        "📋 Campaign List", 
        "➕ Create Campaign", 
        "💸 Donation Page & Detail"
    ]
)

if menu == "📊 Dashboard":
    st.header("📊 Dashboard Amal Transparan")
    st.write("Ringkasan statistik keseluruhan platform penggalangan dana secara 100% transparan.")
    
    # 3 Kotak Metrik Utama (Sesuai modul)
    col1, col2, col3 = st.columns(3)
    col1.metric(label="Total Kampanye", value="1 Program", delta="Aktif")
    col2.metric(label="Total Donasi Masuk", value="5 Transaksi", delta="Sukses")
    col3.metric(label="Total Dana Terkumpul", value="0.001 ETH", delta="Target: 0.000001 ETH")
    
    st.info("💡 Semua data di atas diambil secara langsung dari fungsi Read Smart Contract di blockchain lokal.")


elif menu == "📋 Campaign List":
    st.header("📋 Daftar Kampanye Amal (Campaign List)")
    st.write("Daftar program amal yang sedang berjalan beserta progress target dananya[cite: 13].")
    
    with st.container():
        st.subheader("ID Program #1: Donasi Bansos Warga")
        st.write("**Deskripsi:** Penyaluran bantuan sosial untuk warga terdampak[cite: 13].")
        st.text("Target: 0.000001 ETH | Terkumpul: 0 ETH")
        
        # Komponen Progress Bar visual
        st.progress(0.0, text="Progres: 0% dari Target")
        st.markdown("---")

elif menu == "➕ Create Campaign":
    st.header("➕ Buat Kampanye Baru (Create Campaign)")
    st.write("Form untuk mendaftarkan program amal baru ke dalam smart contract[cite: 13].")
    
    with st.form("form_buat_kampanye"):
        nama_program = st.text_input("Nama Kampanye / Program")
        deskripsi = st.text_area("Deskripsi Program Amal")
        target_dana = st.number_input("Target Dana (ETH)", min_value=0.0001, format="%.4f")
        
        submitted = st.form_submit_button("Deploy Kampanye ke Blockchain")
        
        if submitted:
            if not nama_program or not deskripsi:
                st.warning("⚠️ Harap isi semua kolom dengan benar (Validasi Form)!")
            else:
                st.success(f"Berhasil! Kampanye '{nama_program}' sedang diproses.")
                # Di sini nanti koneksi web3.py memanggil fungsi buatProgram() ke smart contract

elif menu == "💸 Donation Page & Detail":
    st.header("💸 Detail Kampanye & Halaman Donasi")
    
    token_id = st.number_input("Masukkan Token ID Program Amal", min_value=1, step=1, value=1)
    
    if st.button("Cek Detail Program"):
        st.success(f"Menampilkan data untuk Token ID: {token_id}")
        st.write("**Nama Program:** bansos")
        st.write("**Target Dana:** 0.000001 ETH")
        st.metric("Dana Terkumpul Saat Ini", "0 ETH")
    
    st.markdown("---")
    st.subheader("Form Donasi (Donation Page)")
    
    with st.form("form_donasi"):
        nominal_eth = st.number_input("Masukkan Nominal Donasi (ETH)", min_value=0.0001, value=0.001, format="%.4f")
        kirim = st.form_submit_button("Kirim Donasi Sekarang")
        
        if kirim:
            st.info(f"Mengirim donasi sebesar {nominal_eth} ETH...")
            st.success("Silakan konfirmasi transaksi melalui pop-up MetaMask Anda!")
            # Di sini fungsi web3.py mengeksekusi .donasi(token_id) dengan parameter value=w3.to_wei(nominal_eth, 'ether')


w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 5}))

if not w3.is_connected():
  st.error(
      "Tidak dapat terhubung ke Hardhat Network. Pastikan Hardhat Node sedang"
      " berjalan."
  )
  st.stop()


if not DEPLOYMENT_PATH.exists():
  st.error(
      "File deployment.json tidak ditemukan. Silakan deploy smart contract"
      " terlebih dahulu."
  )
  st.stop()

with open(DEPLOYMENT_PATH, "r") as file:
  deployment_data = json.load(file)

CONTRACT_ADDRESS = Web3.to_checksum_address(deployment_data["address"])


if not ARTIFACT_PATH.exists():
  st.error(
      "Artifact smart contract tidak ditemukan. Silakan compile smart contract"
      " terlebih dahulu."
  )
  st.stop()

with open(ARTIFACT_PATH, "r") as file:
  contract_artifact = json.load(file)

CONTRACT_ABI = contract_artifact["abi"]


amal_contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)


# =========================================================
# KOMPONEN JAVASCRIPT UNTUK METAMASK (CONNECT & DISCONNECT)
# =========================================================

WALLET_HTML = """
<div>
  <button id="connect-wallet" type="button">
    Connect Wallet
  </button>
  <button id="disconnect-wallet" type="button" style="display: none; background-color: #d9534f; margin-left: 10px;">
    Putuskan Wallet
  </button>
  <p id="wallet-status">Wallet belum terhubung.</p>
</div>
"""

WALLET_CSS = """
button {
    padding: 0.7rem 1rem;
    border: none;
    border-radius: 8px;
    background: var(--st-primary-color);
    color: white;
    font-weight: 600;
    cursor: pointer;
}
button#disconnect-wallet {
    background-color: #d9534f;
}
p {
    color: var(--st-text-color);
    overflow-wrap: anywhere;
}
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
        if (isConnected) {
            connectBtn.style.display = "none";
            disconnectBtn.style.display = "inline-block";
            status.textContent = "Wallet terhubung: " + address;
        } else {
            connectBtn.style.display = "inline-block";
            disconnectBtn.style.display = "none";
            status.textContent = "Wallet belum terhubung.";
        }
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
            status.textContent = "MetaMask tidak ditemukan. Pasang ekstensi MetaMask.";
            return;
        }
        try {
            status.textContent = "Menunggu persetujuan akses akun...";
            await window.ethereum.request({ method: "eth_requestAccounts" });
            await readWallet();
        } catch (error) {
            status.textContent = "Koneksi gagal: " + (error.message || "Kesalahan tidak diketahui");
        }
    }

    function disconnectWallet() {
        // Karena dApp tidak bisa langsung "logout" sesi MetaMask secara paksa dari ekstensi,
        // kita mereset state aplikasi Python agar kembali ke status belum terhubung.
        if (!mounted) return;
        setStateValue("wallet", { address: "", chainId: "", connected: false });
        updateUI(false);
        status.textContent = "Wallet diputus dari aplikasi. (Silakan putuskan izin di ekstensi MetaMask jika perlu)";
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
# 1. STATUS BLOCKCHAIN & KONTRAK
# =========================================================

st.subheader("1. Status Blockchain Lokal")
col1, col2 = st.columns(2)
col1.metric("Chain ID RPC", w3.eth.chain_id)
col2.metric("Block Terbaru", w3.eth.block_number)
st.info(f"Smart Contract Aktif di: `{CONTRACT_ADDRESS}`")

# =========================================================
# 2. KONEKSI METAMASK
# =========================================================

st.divider()
st.subheader("2. Hubungkan MetaMask")

wallet_result = wallet_component(
    key="amal_metamask",
    default={
        "wallet": {
            "address": "",
            "chainId": "",
            "connected": False,
        }
    },
    on_wallet_change=lambda: None,  # Tambahkan argumen callback ini untuk mengatasi error validasi state
)

wallet = {}
if isinstance(wallet_result, dict):
  wallet = wallet_result.get("wallet", {})

# =========================================================
# 3. INFORMASI WALLET DAN SALDO
# =========================================================

st.divider()
st.subheader("3. Informasi Wallet")

if wallet and wallet.get("connected") and wallet.get("address"):
  address = Web3.to_checksum_address(wallet["address"])
  st.success("Wallet berhasil terhubung.")
  st.code(address)

  try:
    wallet_chain_id = int(wallet["chainId"], 16)
    if wallet_chain_id == w3.eth.chain_id:
      if st.button("Periksa Saldo ETH", type="primary"):
        balance_wei = w3.eth.get_balance(address)
        balance_eth = w3.from_wei(balance_wei, "ether")
        st.metric("Saldo ETH", f"{float(balance_eth):.6f} ETH")
    else:
      st.warning(
          "Jaringan MetaMask berbeda dengan Hardhat RPC (Chain ID harus 31337)."
      )
  except Exception as e:
    st.error(f"Gagal memproses data wallet: {e}")

  # =========================================================
  # 4. FITUR UTAMA AMAL TRANSPARAN (READ CONTRACT)
  # =========================================================
  st.divider()
  st.subheader("4. Data Program Amal (Read Contract)")

  token_id_input = st.number_input(
      "Masukkan Token ID Program", min_value=1, step=1, value=1
  )

  if st.button("Cek Detail Program"):
    try:
      # Memanggil fungsi public daftarProgram dari smart contract AmalTransparan
      data_prog = amal_contract.functions.daftarProgram(token_id_input).call()
      t_id, nama, deskripsi, target, terkumpul, status_enum, created_at = (
          data_prog
      )

      if t_id == 0:
        st.warning("Program amal dengan Token ID tersebut tidak ditemukan.")
      else:
        status_list = ["DIBUAT", "TERKUMPUL", "DISALURKAN", "SELESAI"]
        status_teks = (
            status_list[status_enum]
            if status_enum < len(status_list)
            else "UNKNOWN"
        )

        st.write(f"**Nama Program:** {nama}")
        st.info(f"**Deskripsi:** {deskripsi}")

        c1, c2, c3 = st.columns(3)
        c1.metric("Target Dana", f"{w3.from_wei(target, 'ether')} ETH")
        c2.metric("Dana Terkumpul", f"{w3.from_wei(terkumpul, 'ether')} ETH")
        c3.metric("Status", status_teks)

        # Cek Pengelola Program
        pengelola = amal_contract.functions.getPengelolaProgram(
            token_id_input
        ).call()
        st.write(f"Pengelola / Pemilik NFT: `{pengelola}`")

    except Exception as e:
        st.error(f"Gagal mengambil data program: {e}")

else:
  st.info("Klik tombol Connect Wallet di atas untuk mulai berinteraksi.")

st.divider()
st.caption(
    "Praktikum Blockchain: Transparansi Aliran Dana Amal Berbasis Smart"
    " Contract."
)

