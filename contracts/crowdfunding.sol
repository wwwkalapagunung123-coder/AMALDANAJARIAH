// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";

/**
 * @title Crowdfunding / Amal Transparan
 * @notice Sistem donasi dengan aliran dana yang dapat dilacak 100% HALAL
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
    }

    // 4. Pengaturan Token ID
    uint256 private nextTokenId = 1;

    // Mapping untuk data program dan riwayat
    mapping(uint256 => ProgramAmal) public daftarProgram;
    mapping(uint256 => RiwayatAmal[]) private riwayatProgram;

    // Event log
    event ProgramDibuat(uint256 indexed tokenId, address indexed pembuat, string namaProgram, uint256 targetDana);
    event DonasiDiterima(uint256 indexed tokenId, address indexed donatur, uint256 jumlah);
    event DanaDisalurkan(uint256 indexed tokenId, address indexed penerima, uint256 jumlah);

    // 3. Constructor ERC-721
    constructor() ERC721("Sertifikat Amal Transparan", "AMAL") {}

    // 5. & 8. Fungsi Pembuatan Program (Minting NFT Sertifikat Bukti Program Amal)
    function buatProgramAmal(
        string memory namaProgram,
        string memory deskripsi,
        uint256 targetDana,
        string memory metadataURI
    ) public returns (uint256) {
        require(bytes(namaProgram).length > 0, "Nama program wajib diisi");
        require(targetDana > 0, "Target dana harus lebih dari 0");

        uint256 tokenId = nextTokenId;

        // Mint NFT bukti kepemilikan/pengelolaan program amal
        _safeMint(msg.sender, tokenId);
        _setTokenURI(tokenId, metadataURI);

        nextTokenId++;

        // Simpan Data Program
        daftarProgram[tokenId] = ProgramAmal({
            tokenId: tokenId,
            namaProgram: namaProgram,
            deskripsi: deskripsi,
            targetDana: targetDana,
            danaTerkumpul: 0,
            status: StatusProgram.DIBUAT,
            createdAt: block.timestamp
        });

        // Simpan Riwayat
        riwayatProgram[tokenId].push(RiwayatAmal({
            aksi: "PROGRAM_DIBUAT",
            aktor: msg.sender,
            jumlah: 0,
            timestamp: block.timestamp
        }));

        emit ProgramDibuat(tokenId, msg.sender, namaProgram, targetDana);
        return tokenId;
    }

    // Fungsi Donasi (Mencatat aliran dana secara transparan & halal)
    function donasi(uint256 tokenId) public payable {
        ProgramAmal storage program = daftarProgram[tokenId];
        require(_ownerOf(tokenId) != address(0), "Program amal tidak ditemukan");
        require(msg.value > 0, "Jumlah donasi harus lebih dari 0");

        program.danaTerkumpul += msg.value;

        if (program.danaTerkumpul >= program.targetDana && program.status == StatusProgram.DIBUAT) {
            program.status = StatusProgram.TERKUMPUL;
        }

        riwayatProgram[tokenId].push(RiwayatAmal({
            aksi: "DONASI_DITERIMA",
            aktor: msg.sender,
            jumlah: msg.value,
            timestamp: block.timestamp
        }));

        emit DonasiDiterima(tokenId, msg.sender, msg.value);
    }

    // 6. Fungsi Cek Pemilik / Pengelola Program Amal
    function getPengelolaProgram(uint256 tokenId) public view returns (address) {
        require(_ownerOf(tokenId) != address(0), "Program amal tidak ditemukan");
        return ownerOf(tokenId);
    }

    // Fungsi untuk melihat riwayat aliran dana secara transparan
    function getRiwayat(uint256 tokenId) public view returns (RiwayatAmal[] memory) {
        return riwayatProgram[tokenId];
    }
}