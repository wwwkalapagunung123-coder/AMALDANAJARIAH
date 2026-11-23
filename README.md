# Amal Transparan

Platform penggalangan dana transparan berbasis blockchain untuk sedekah jariyah. Setiap program amal, donasi, penyaluran, dan penyelesaian program dicatat di smart contract sehingga alirannya bisa ditelusuri.

**Teknologi:** Solidity + Hardhat (blockchain lokal), Web3.py, Streamlit.

## Alur program

```
Dibuat  ->  Terkumpul  ->  Disalurkan  ->  Selesai
```

| Tahap | Terjadi saat | Siapa |
|---|---|---|
| Dibuat | Program didaftarkan, NFT sertifikat dicetak | Pengelola |
| Terkumpul | Total donasi mencapai target (otomatis) | Donatur |
| Disalurkan | Dana dikirim ke alamat penerima manfaat | Pengelola |
| Selesai | Program ditutup dengan catatan penyelesaian | Pengelola |

## Kebutuhan

- Node.js 18 atau lebih baru
- Python 3.10 atau lebih baru
- Browser (MetaMask opsional, hanya untuk fitur sambung wallet)

## Instalasi (sekali saja)

Dari folder proyek:

```bash
# 1. Dependensi Hardhat dan OpenZeppelin
npm install

# 2. Dependensi Python
pip install -U streamlit web3
```

Aplikasi memakai `streamlit.components.v2`, jadi pakai Streamlit versi terbaru (`pip install -U streamlit`).

## Struktur folder

```
proyek/
├── contracts/
│   └── crowdfunding.sol      # smart contract AmalTransparan
├── scripts/                  # skrip deploy (menulis deployment.json)
├── artifacts/                # hasil compile (dibuat otomatis)
├── deployment.json           # alamat kontrak hasil deploy
├── app.py                    # aplikasi Streamlit
└── hardhat.config.js
```

## Menjalankan aplikasi

Buka **tiga terminal** di folder proyek.

**Terminal 1: jalankan blockchain lokal**

```bash
npx hardhat node
```

Biarkan terminal ini terus berjalan. Node berjalan di `http://127.0.0.1:8545` (Chain ID 31337) dan menampilkan 20 akun uji beserta private key-nya.

**Terminal 2: compile dan deploy kontrak**

```bash
npx hardhat compile
npx hardhat run scripts/deploy.js --network localhost
```

Ganti `scripts/deploy.js` dengan nama skrip deploy yang Anda pakai. Skrip itu harus menulis alamat kontrak ke `deployment.json`, misalnya:

```json
{ "address": "0x5FbDB2315678afecb367f032d93F642f64180aa3" }
```

**Terminal 3: jalankan aplikasi**

```bash
streamlit run app.py
```

Buka alamat yang ditampilkan (biasanya `http://localhost:8501`).

> Setiap kali Anda **mengubah kontrak** atau **me-restart `npx hardhat node`**, ulangi compile dan deploy, lalu muat ulang browser (Ctrl+Shift+R). Data di node lokal hilang saat node dimatikan.

## Cara memakai

1. **Buat Program:** isi nama, deskripsi, dan target dana (mis. `0.001` ETH untuk mencoba).
2. **Sedekah:** pilih program, isi nominal, kirim donasi. Ulangi sampai target tercapai (status berubah menjadi Terkumpul).
3. **Penyaluran:** isi alamat penerima dan keterangan, lalu salurkan dana. Untuk simulasi, pakai akun Hardhat lain sebagai penerima, misalnya Hardhat #1:
   `0x70997970C51812dc3A010C7d01b50e0d17dc79C8`
4. **Penyaluran (lanjutan):** isi catatan penyelesaian lalu klik **Tandai program selesai**.
5. **Detail & Riwayat:** lihat alur status dan jejak dana dari awal sampai akhir.

Penyaluran dan penyelesaian hanya bisa dilakukan oleh **pengelola** (akun yang membuat program).

## Akun penandatangan transaksi

Transaksi ditandatangani lewat Web3.py. Urutan akun yang dipakai:

1. Environment variable `PRIVATE_KEY`, jika ada
2. Private key yang diisi di menu **Dompet**
3. Akun Hardhat #0 (bawaan, khusus development)

Untuk mencoba sebagai akun lain, isi private key-nya di menu **Dompet**.

> Jangan pernah memakai private key dompet asli di aplikasi ini. Private key akun Hardhat sudah publik dan hanya aman untuk jaringan lokal.

## Catatan

Proyek ini dibuat untuk praktikum blockchain di jaringan lokal. Kontraknya belum diaudit dan belum disiapkan untuk jaringan publik.
