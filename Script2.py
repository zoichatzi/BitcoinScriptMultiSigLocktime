from datetime import datetime
from decimal import *

import requests
from bitcoinutils.keys import P2pkhAddress, P2shAddress, PrivateKey, PublicKey
from bitcoinutils.proxy import NodeProxy
from bitcoinutils.script import Script
from bitcoinutils.setup import setup
from bitcoinutils.transactions import Transaction, TxInput, TxOutput
from bitcoinutils.utils import to_satoshis

# In this case the 'test' node credentials has been added. Feel free to change them
# with any other.
USERNAME = "test"
PASSWORD_HASH = "ti8KMfu1Afeh8UZYYN32Lqo5NfBIN6tC-pnSW-OBp7A="

# Connect to Regtest
print("Hello,", USERNAME, ". Connecting to regtest...")
setup("regtest")
proxy = NodeProxy(USERNAME, PASSWORD_HASH).get_proxy()


print("To continue, 4 signers should be provided. 2 Private Keys and two Public Keys")

while True:
    try:
        signer1 = input("Please input the PRIVATE of the first signer: ")
        privateKey1 = PrivateKey(signer1)
        break
    except ValueError:
        print("You should provide a valid Private Key for the first signer")

while True:
    try:
        signer2 = input("Please input the PRIVATE of the second signer: ")
        privateKey2 = PrivateKey(signer2)
        break
    except ValueError:
        print("You should provide a valid Private Key for the second signer")

while True:
    try:
        signer3 = input("Please input the PUBLIC of the third signer: ")
        publicKey3 = PublicKey(signer3)
        break
    except ValueError:
        print("You should provide a valid Public Key for the thirdsigner")
while True:
    try:
        signer4 = input("Please input the PUBLIC of the forth signer: ")
        publicKey4 = PublicKey(signer4)
        break
    except ValueError:
        print("You should provide a valid Public Key for the forth signer")

# get a future Unix Epoch TimeStamp
try:
    timestamp = int(
        input(
            "Please insert a valid timestamp that you wish the transaction to complete in "
            "any case:"
        )
    )
    theDate = datetime.utcfromtimestamp(timestamp)
except ValueError:
    print("Not valid date.")

print("The time date that you have provided is: ", theDate)

if timestamp < datetime.timestamp(datetime.now()):
    print(
        "The given Date is in the past. If you continue, the transaction will "
        "be able to be completed by the first signer..."
    )
    answer = input(
        "Do you wish to continue? [Press 0 for exit or any key to continue...]"
    )
    if answer == "0":
        exit()

# Get the public keys for the first two signers
publicKey1 = privateKey1.get_public_key()
publicKey2 = privateKey2.get_public_key()

# Get the addresses
address1 = publicKey1.get_address()
address2 = publicKey2.get_address()
address3 = publicKey3.get_address()
address4 = publicKey4.get_address()

# Get the hash
hash1 = address1.to_hash160()
hash2 = address2.to_hash160()
hash3 = address3.to_hash160()
hash4 = address4.to_hash160()

print(publicKey1)
print(publicKey1.to_bytes().hex())

# remake the redeem script
redeem_script = Script(
    [
        "OP_IF",
        timestamp,
        "OP_CHECKLOCKTIMEVERIFY",
        "OP_DROP",
        "OP_DUP",
        "OP_HASH160",
        hash1,
        "OP_EQUALVERIFY",
        "OP_CHECKSIG",
        "OP_ELSE",
        2,
        publicKey1.to_bytes().hex(),
        publicKey2.to_bytes().hex(),
        signer3,
        signer4,
        4,
        "OP_CHECKMULTISIG",
        "OP_ENDIF",
    ]
)

# Recreate the P2SH address to get the funds from.
from_p2sh = P2shAddress.from_script(redeem_script)
print("     source: " + from_p2sh.to_string())

# Check if the P2SH address has any UTXOs to get funds from

utxos = {}
funds = Decimal(0)
txids = proxy.listreceivedbyaddress(0, True, True, from_p2sh.to_string())[0]["txids"]

for txid in txids:
    tx = proxy.gettransaction(txid)
    utxos[txid] = tx
    amount = tx["amount"]
    funds -= amount

    print(" utxo tx id: " + str(txid))
    print(tx)
    print("utxo amount: " + str(amount))

funds = int(to_satoshis(funds))
if funds == 0:
    print("no funds")
    exit
print("      funds: " + str(funds) + " satoshis")

# Accept a P2PKH address to send the funds to
addressP2SH = P2shAddress.from_script(redeem_script)
print(addressP2SH.to_string())

# Calculate the appropriate fees with respect to the size of the transaction
data = requests.get("https://api.blockcypher.com/v1/btc/test3").json()
satoshi_per_byte = data["high_fee_per_kb"] / 1024.0
print("      price: " + str(satoshi_per_byte) + " satoshi per byte")

fee = int(0)
for i in range(2):

    #  Send all funds that the P2SH address received to the P2PKH address provided

    # transaction inputs with absolute locktime
    txins = []
    for txid in txids:
        txins.append(
            TxInput(
                txid, utxos[txid]["details"][0]["vout"], sequence=b"\xfe\xff\xff\xff"
            )
        )

    # transaction output
    amount = funds - fee
    txout = TxOutput(amount, addressP2SH.to_script_pub_key())

    # create transaction
    tx = Transaction(txins, [txout], timestamp)

    if i:
        print("     amount: " + str(amount) + " satoshis")
        print("        fee: " + str(fee) + " satoshis")

    #  Show the raw unsigned transaction
    if i:
        print("raw unsigned transaction:\n" + tx.serialize())

    #  Sign the transaction
    j = 0
    for txin in txins:
        signature = publicKey1.sign_input(tx, j, redeem_script)
        txin.script_sig = Script(
            [signature, publicKey1.to_hex(), redeem_script.to_hex()]
        )
        j += 1

    #  Display the raw signed transaction
    if i:
        print("raw signed transaction:\n" + tx.serialize())

    fee = int(tx.get_size() * satoshi_per_byte)

# Display the transaction id
print("   transaction id: " + tx.get_txid())

# Verify that the transaction is valid and will be accepted by the Bitcoin nodes
isvalid = proxy.testmempoolaccept([tx.serialize()])[0]["allowed"]
print("transaction valid: " + str(isvalid))

# If the transaction is valid, send it to the blockchain
if isvalid:
    proxy.sendrawtransaction(tx.serialize())
    print("The transaction has been successfully sent.")
else:
    print("The transaction could not be sent.")
