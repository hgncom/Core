// wallet.js

document.addEventListener('DOMContentLoaded', function() {
    // Retrieve the wallet address from the HTML
    var walletAddressElement = document.getElementById('wallet-address');
    var walletAddress = walletAddressElement.innerText;

    // Fetch wallet balance and display it
    fetchWalletBalance(walletAddress);

    // Fetch transaction history and display it
    fetchTransactionHistory(walletAddress);

    // Handle sending funds
    handleSendFunds(walletAddress);
});

// Function to fetch wallet balance from the server
function fetchWalletBalance(walletAddress) {
    fetch('/api/wallet/balance?address=' + walletAddress)
        .then(response => response.json())
        .then(data => {
            // Update the UI with the wallet balance
            document.getElementById('wallet-balance').innerText = data.balance;
        })
        .catch(error => {
            console.error('Error fetching wallet balance:', error);
        });
}

// Function to fetch transaction history from the server
function fetchTransactionHistory(walletAddress) {
    fetch('/api/wallet/transactions?address=' + walletAddress)
        .then(response => response.json())
        .then(data => {
            // Render transaction history in a table
            renderTransactionHistory(data.transactions);
        })
        .catch(error => {
            console.error('Error fetching transaction history:', error);
        });
}

// Function to render transaction history in a table
function renderTransactionHistory(transactions) {
    var tableBody = document.getElementById('transaction-history-body');
    transactions.forEach(transaction => {
        var row = tableBody.insertRow();
        var dateCell = row.insertCell(0);
        var amountCell = row.insertCell(1);
        var typeCell = row.insertCell(2);
        dateCell.innerText = transaction.date;
        amountCell.innerText = transaction.amount;
        typeCell.innerText = transaction.type;
    });
}

// Function to handle sending funds
function handleSendFunds(walletAddress) {
    var sendFundsForm = document.getElementById('send-funds-form');
    sendFundsForm.addEventListener('submit', function(event) {
        event.preventDefault();
        var recipientAddress = document.getElementById('recipient-address').value;
        var amount = document.getElementById('amount').value;
        sendFunds(walletAddress, recipientAddress, amount);
    });
}

// Function to send funds
function sendFunds(senderAddress, recipientAddress, amount) {
    fetch('/api/wallet/send', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            senderAddress: senderAddress,
            recipientAddress: recipientAddress,
            amount: amount
        })
    })
    .then(response => response.json())
    .then(data => {
        // Handle response from server (e.g., display success message)
        console.log('Transaction successful:', data);
        // Optionally, update the UI or display a success message to the user
    })
    .catch(error => {
        console.error('Error sending funds:', error);
        // Optionally, display an error message to the user
    });
}
