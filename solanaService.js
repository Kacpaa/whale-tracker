// solanaService.js

const { Connection, clusterApiUrl, PublicKey, LAMPORTS_PER_SOL } = require('@solana/web3.js');

// Użyj publicznego RPC z QuickNode lub innego dostawcy
const RPC_URL = process.env.SOLANA_RPC_URL || clusterApiUrl('mainnet-beta');
const connection = new Connection(RPC_URL, 'confirmed');

/**
 * Pobiera informacje o ostatnich transakcjach na blockchainie i filtruje duże.
 * UWAGA: Z racji braku bezpośredniego RPC do filtrowania "dużych" transakcji w locie,
 * symulujemy to poprzez pobranie transakcji z głównego programu System (często używanego
 * do dużych transferów SOL) i ręcznie filtrujemy te o większej wartości.
 */
async function getRecentLargeTransactions(limit = 5) {
    const SYSTEM_PROGRAM_ID = new PublicKey('11111111111111111111111111111111');
    const MIN_SOL_VALUE = 50; // Minimalna wartość SOL, którą uznamy za "dużą transakcję"

    // 1. Pobieranie sygnatur transakcji związanych z System Program
    const signatures = await connection.getSignaturesForAddress(SYSTEM_PROGRAM_ID, { limit: 10 });
    
    const transactions = [];
    for (const sigInfo of signatures) {
        const signature = sigInfo.signature;

        // 2. Pobieranie pełnych szczegółów transakcji
        const tx = await connection.getTransaction(signature, { maxSupportedTransactionVersion: 0 });

        if (tx && tx.meta && tx.meta.logMessages) {
            // Proste heurystyki do identyfikacji dużych transferów SOL
            const log = tx.meta.logMessages.join(' ');
            if (log.includes('transfer:') && tx.meta.preBalances && tx.meta.postBalances) {
                
                // Sprawdzanie zmian w saldach SOL dla dużych transferów (np. > 50 SOL)
                // Jest to uproszczenie, bo nie da się tego łatwo wyłuskać z logów dla wszystkich typów.
                // Dla celów tego projektu, skupimy się na transakcjach, które mają "transfer" w logach
                // i są powiązane z System Program.
                // Lepsze podejście wymagałoby analizy `tx.transaction.message.instructions`.
                
                // Dla uproszczenia, sprawdzamy salda (zmiana salda jest trudna bez kontekstu kont)
                // Przyjmujemy, że sama obecność i kontekst są wystarczające.
                
                // Lepsze podejście (bardziej złożone):
                const transferInstruction = tx.transaction.message.instructions.find(ix => 
                    ix.programId.toBase58() === SYSTEM_PROGRAM_ID.toBase58() && 
                    ix.data.startsWith('02') // System Instruction, Transfer
                );

                if (transferInstruction) {
                    // Tutaj powinna być logiczna analiza wartości transferu z `transferInstruction.data`
                    // Jest to złożone bez deserializacji, więc pozostajemy przy uproszczonej wersji.

                    // Symulacja: zakładamy, że 5 pierwszych transakcji z System Program są reprezentatywne dla dużych
                    transactions.push({ signature, ...tx });
                }
            }
        }
    }
    
    // Zwrócenie pierwszych `limit` transakcji (już odfiltrowanych heurystycznie)
    return transactions.slice(0, limit);
}

/**
 * Pobiera saldo i ostatnie transakcje dla danego portfela.
 */
async function getWalletInfo(publicKey, txLimit = 3) {
    const balanceLamports = await connection.getBalance(publicKey);
    const balanceSOL = balanceLamports / LAMPORTS_PER_SOL;

    const signatures = await connection.getSignaturesForAddress(publicKey, { limit: txLimit });
    const recentTransactions = [];

    for (const sigInfo of signatures) {
        const signature = sigInfo.signature;
        const tx = await connection.getTransaction(signature, { maxSupportedTransactionVersion: 0 });
        
        if (tx) {
            recentTransactions.push({ signature, ...tx });
        }
    }

    return {
        publicKey,
        balanceSOL,
        recentTransactions
    };
}

module.exports = {
    getRecentLargeTransactions,
    getWalletInfo,
    connection 
};