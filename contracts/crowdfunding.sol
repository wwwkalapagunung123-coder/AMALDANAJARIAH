// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";

/**
 * @title Crowdfunding / Amal Transparan
 * @notice Sistem donasi dengan aliran dana yang dapat dilacak 100% HALAL
 * Alur: DIBUAT -> TERKUMPUL -> DISALURKAN -> SELESAI
 */
contract AmalTransparan is ERC721URIStorage {

    // Enum untuk mencatat status aliran dana program amal
    enum StatusProgram {
        DIBUAT,      // Program penggalangan dana dibuka
        TERKUMPUL,   // Target dana tercapai
        DISALURKAN,  // Dana telah disalurkan ke penerima manfaat
        SELESAI      // Program selesai dan terverifikasi
    }

    // Struct untuk menyimpan data aset program amal
    struct ProgramAmal {
        uint256 tokenId;
        string namaProgram;
        string deskripsi;
        uint256 targetDana;
        uint256 danaTerkumpul;
        StatusProgram status;
        uint256 createdAt;
    }

    // Struct untuk riwayat transparansi aliran dana
    struct RiwayatAmal {
        string aksi;
        address aktor;
        uint256 jumlah;
        uint256 timestamp;
        string keterangan;
    }

    uint256 private nextTokenId = 1;

    mapping(uint256 => ProgramAmal) public daftarProgram;
    mapping(uint256 => RiwayatAmal[]) private riwayatProgram;

    // Event log
    event ProgramDibuat(uint256 indexed tokenId, address indexed pembuat, string namaProgram, uint256 targetDana);
    event DonasiDiterima(uint256 indexed tokenId, address indexed donatur, uint256 jumlah);
    event DanaDisalurkan(uint256 indexed tokenId, address indexed penerima, uint256 jumlah);
    event ProgramSelesai(uint256 indexed tokenId, address indexed pengelola);

    constructor() ERC721("Sertifikat Amal Transparan", "AMAL") {}

    // Hanya pemilik NFT (pengelola) program yang boleh memanggil
    modifier hanyaPengelola(uint256 tokenId) {
        require(_ownerOf(tokenId) != address(0), "Program amal tidak ditemukan");
        require(msg.sender == ownerOf(tokenId), "Hanya pengelola program");
        _;
    }

    // Fungsi Pembuatan Program (Minting NFT Sertifikat Bukti Program Amal)
    function buatProgramAmal(
        string memory namaProgram,
        string memory deskripsi,
        uint256 targetDana,
        string memory metadataURI
    ) public returns (uint256) {
        require(bytes(namaProgram).length > 0, "Nama program wajib diisi");
        require(targetDana > 0, "Target dana harus lebih dari 0");

        uint256 tokenId = nextTokenId;

        _safeMint(msg.sender, tokenId);
        _setTokenURI(tokenId, metadataURI);

        nextTokenId++;

        daftarProgram[tokenId] = ProgramAmal({
            tokenId: tokenId,
            namaProgram: namaProgram,
            deskripsi: deskripsi,
            targetDana: targetDana,
            danaTerkumpul: 0,
            status: StatusProgram.DIBUAT,
            createdAt: block.timestamp
        });

        riwayatProgram[tokenId].push(RiwayatAmal({
            aksi: "PROGRAM_DIBUAT",
            aktor: msg.sender,
            jumlah: 0,
            timestamp: block.timestamp,
            keterangan: "Program amal dibuat oleh pengelola"
        }));

        emit ProgramDibuat(tokenId, msg.sender, namaProgram, targetDana);
        return tokenId;
    }

    // Fungsi Donasi (Mencatat aliran dana secara transparan & halal)
    function donasi(uint256 tokenId) public payable {
        require(_ownerOf(tokenId) != address(0), "Program amal tidak ditemukan");
        require(msg.value > 0, "Jumlah donasi harus lebih dari 0");

        ProgramAmal storage program = daftarProgram[tokenId];
        require(
            program.status == StatusProgram.DIBUAT || program.status == StatusProgram.TERKUMPUL,
            "Program sudah ditutup"
        );

        program.danaTerkumpul += msg.value;

        if (program.danaTerkumpul >= program.targetDana && program.status == StatusProgram.DIBUAT) {
            program.status = StatusProgram.TERKUMPUL;
        }

        riwayatProgram[tokenId].push(RiwayatAmal({
            aksi: "DONASI_DITERIMA",
            aktor: msg.sender,
            jumlah: msg.value,
            timestamp: block.timestamp,
            keterangan: ""
        }));

        emit DonasiDiterima(tokenId, msg.sender, msg.value);
    }

    // Pengelola menyalurkan seluruh dana terkumpul ke penerima manfaat
    function salurkanDana(
        uint256 tokenId,
        address payable penerima,
        string memory keterangan
    ) public hanyaPengelola(tokenId) {
        require(penerima != address(0), "Alamat penerima tidak valid");

        ProgramAmal storage program = daftarProgram[tokenId];
        require(program.status == StatusProgram.TERKUMPUL, "Dana belum terkumpul");

        uint256 jumlah = program.danaTerkumpul;

        // Ubah status & catat riwayat SEBELUM mengirim ETH
        program.status = StatusProgram.DISALURKAN;

        riwayatProgram[tokenId].push(RiwayatAmal({
            aksi: "DANA_DISALURKAN",
            aktor: penerima,
            jumlah: jumlah,
            timestamp: block.timestamp,
            keterangan: keterangan
        }));

        (bool ok, ) = penerima.call{value: jumlah}("");
        require(ok, "Transfer ke penerima gagal");

        emit DanaDisalurkan(tokenId, penerima, jumlah);
    }

    // Pengelola menutup program setelah dana disalurkan
    function selesaikanProgram(
        uint256 tokenId,
        string memory catatan
    ) public hanyaPengelola(tokenId) {
        ProgramAmal storage program = daftarProgram[tokenId];
        require(program.status == StatusProgram.DISALURKAN, "Dana belum disalurkan");

        program.status = StatusProgram.SELESAI;

        riwayatProgram[tokenId].push(RiwayatAmal({
            aksi: "PROGRAM_SELESAI",
            aktor: msg.sender,
            jumlah: 0,
            timestamp: block.timestamp,
            keterangan: catatan
        }));

        emit ProgramSelesai(tokenId, msg.sender);
    }

    // Fungsi Cek Pemilik / Pengelola Program Amal
    function getPengelolaProgram(uint256 tokenId) public view returns (address) {
        require(_ownerOf(tokenId) != address(0), "Program amal tidak ditemukan");
        return ownerOf(tokenId);
    }

    // Fungsi untuk melihat riwayat aliran dana secara transparan
    function getRiwayat(uint256 tokenId) public view returns (RiwayatAmal[] memory) {
        return riwayatProgram[tokenId];
    }
}