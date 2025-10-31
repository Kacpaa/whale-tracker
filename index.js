// index.js

require('dotenv').config();
const { PublicKey } = require('@solana/web3.js');
const { getRecentLargeTransactions, getWalletInfo } = require('./solanaService');
const { displayTransaction, displayWalletInfo } = require('./utils');

// Adresy portfeli do monitorowania (przykładowe: System Program ID i duży znany portfel)
const WALLETS_TO_MONITOR = [
    new PublicKey('11111111111111111111111111111111'), // System Program (często używany w dużych transferach SOL)
    // Zastąp poniższy adres innym adresem dużego portfela, który chcesz monitorować.
    new PublicKey('9gP2kP7jA91r92N5K7t5T5P2L7z5R5Q5J5N5F5R5Q5A5') // Przykładowy duży portfel (zmień na rzeczywisty)
];

async function main() {
    console.log('✨ Rozpoczęcie monitorowania ekosystemu Solana...');
    console.log('====================================================\n');

    try {
        // 1. Przegląd ostatnich dużych transakcji
        console.log('🔍 **Ostatnie Duże Transakcje na Solana (Top 5)**');
        console.log('----------------------------------------------------');
        const largeTxs = await getRecentLargeTransactions();
        
        if (largeTxs.length > 0) {
            largeTxs.forEach((tx, index) => {
                console.log(`\n--- Transakcja #${index + 1} ---`);
                displayTransaction(tx);
            });
        } else {
            console.log('Brak dużych transakcji do wyświetlenia w ostatnim bloku.');
        }

        console.log('\n====================================================');
        
        // 2. Monitorowanie największych portfeli
        console.log('💰 **Monitorowanie Najważniejszych Portfeli**');
        console.log('----------------------------------------------------');

        for (const pubKey of WALLETS_TO_MONITOR) {
            console.log(`\n--- Portfel: ${pubKey.toBase58()} ---`);
            const walletInfo = await getWalletInfo(pubKey);
            displayWalletInfo(walletInfo);
        }

    } catch (error) {
        console.error('\n❌ Wystąpił błąd podczas komunikacji z Solana:', error.message);
        console.error('Upewnij się, że twój węzeł RPC jest poprawnie skonfigurowany.');
    }
    
    console.log('\n====================================================');
    console.log('✅ Monitorowanie zakończone.');
}

main();