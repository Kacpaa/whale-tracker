# 🚀 Solana Tracker: Transaction and Wallet Monitoring

A Node.js project utilizing the `@solana/web3.js` library to interact with the Solana network. 
It is designed to review recent large transactions and monitor the balance and activity of key wallets.

## ⚙️ Prerequisites

* Node.js (version 18+)
* Internet access (to communicate with the Solana RPC node)

## 🛠️ Installation

1.  Clone the repository:
    ```bash
    git clone [YOUR_REPO_LINK]
    cd solana-tracker
    ```

2.  Install dependencies:
    ```bash
    npm install
    ```

3.  Configure Environment Variables:
    * Create a `.env` file based on the `.env.example`.
    * Enter your RPC node address in the `.env` file (using a dedicated node is recommended).

## ▶️ Running the Project

Start the project using the run script:

```bash
npm start