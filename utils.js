// utils.js

const { LAMPORTS_PER_SOL } = require('@solana/web3.js');

function displayTransaction(tx) {
    const signature = tx.signature;
    const blockTime = tx.blockTime ? new Date(tx.blockTime * 1000).toLocaleString() : 'N/A';
    const fee = tx.meta && tx.meta.fee ? (tx.meta.fee / LAMPORTS_PER_SOL).toFixed(6) : 'N/A';
    const instructionCount = tx.transaction.message.instructions.length;
    
    console.log(`  Sygnatura: ${signature.slice(0, 40)}...`);
    console.log(`  Czas Bloku: ${blockTime}`);
    console.log(`  Opłata (SOL): ${fee}`);
    console.log(`  Instrukcje: ${instructionCount}`);
    
    // Proste wyświetlanie pierwszych 2 instrukcji
    console.log('  Instrukcje (przykładowe):');
    tx.transaction.message.instructions.slice(0, 2).forEach((ix, i) => {
        console.log(`    - [${i + 1}] Program: ${ix.programId.toBase58().slice(0, 8)}...`);
    });
}

function displayWalletInfo(walletInfo) {
    console.log(`  Saldo: **${walletInfo.balanceSOL.toFixed(2)} SOL**`);
    console.log(`  Ostatnie ${walletInfo.recentTransactions.length} Transakcje:`);
    
    if (walletInfo.recentTransactions.length > 0) {
        walletInfo.recentTransactions.forEach((tx, index) => {
            const blockTime = tx.blockTime ? new Date(tx.blockTime * 1000).toLocaleString() : 'N/A';
            console.log(`    - [${index + 1}] Sygnatura: ${tx.signature.slice(0, 15)}... | Czas: ${blockTime}`);
        });
    } else {
        console.log('    Brak ostatnich transakcji do wyświetlenia.');
    }
}

module.exports = {
    displayTransaction,
    displayWalletInfo
};