const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
    console.log("Memulai deployment Amal Transparan...");

    const ContractFactory =
        await hre.ethers.getContractFactory("AmalTransparan");

    const contract = await ContractFactory.deploy();

    await contract.waitForDeployment();

    const contractAddress = await contract.getAddress();

    console.log("Deployment berhasil!");
    console.log("Alamat kontrak:", contractAddress);

    // Simpan alamat kontrak ke file deployment.json
    const deploymentData = {
        contractName: "AmalTransparan",
        address: contractAddress,
        network: "localhost",
        chainId: 31337,
    };

    const deploymentFilePath = path.join(
        __dirname,
        "..",
        "deployment.json", // Disimpan sebagai deployment.json (tanpa 's') agar sinkron dengan app.py
    );

    fs.writeFileSync(
        deploymentFilePath,
        JSON.stringify(deploymentData, null, 2),
    );

    console.log("Alamat kontrak telah disimpan ke file deployment.json");
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});