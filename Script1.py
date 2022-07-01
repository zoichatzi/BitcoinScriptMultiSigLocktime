from datetime import datetime

from bitcoinutils.keys import P2pkhAddress, P2shAddress, PrivateKey, PublicKey
from bitcoinutils.proxy import NodeProxy
from bitcoinutils.script import Script
from bitcoinutils.setup import setup
from bitcoinutils.transactions import (Locktime, Sequence, Transaction,
                                       TxInput, TxOutput)

# In this case the 'test' node credentials has been added. Feel free to change them
# with any other.
USERNAME = "test"
PASSWORD_HASH = "ti8KMfu1Afeh8UZYYN32Lqo5NfBIN6tC-pnSW-OBp7A="  # test

# # Set the signers that agree with the transaction. [True->sign, False->doesn't sign]
# sign1 = True
# sign2 = False
# sign3 = True
# sign4 = False

# # Test transaction input (contained 0.1 tBTC)
# txin = TxInput("76464c2b9e2af4d63ef38a77964b3b77e629dddefc5cb9eb1a3645b1608b790f", 0)

# # test address we are spending from
# from_addr = P2pkhAddress('n4bkvTyU1dVdzsrhWBqBw8fEMbHjJvtmJR')

# Connecting to Regtest
print("Hello,", USERNAME, ". Connecting to regtest...")
setup("regtest")
proxy = NodeProxy("admin", "admin").get_proxy()

# Wait public keys for the P2PKH part of the redeem script.
print("Please insert the four public keys of the signers.")
input1 = input("Please insert the first public Key: ")
input2 = input("Please insert the second public Key: ")
input3 = input("Please insert the third public Key: ")
input4 = input("Please insert the fourth public Key: ")

# getting the public keys
publicKey1 = PublicKey(input1)
publicKey2 = PublicKey(input2)
publicKey3 = PublicKey(input2)
publicKey4 = PublicKey(input4)

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

# For future reference
# 1) get the addresses for each public key
address1 = publicKey1.get_address()
address2 = publicKey2.get_address()
address3 = publicKey3.get_address()
address4 = publicKey3.get_address()
# 2) get the hashes
hash1 = address1.to_hash160()
hash2 = address2.to_hash160()
hash3 = address3.to_hash160()
hash4 = address4.to_hash160()

# secret key corresponding to the pubkey needed for the P2SH (P2PKH) transaction
p2pkh_sk = PrivateKey("cRvyLwCPLU88jsyj94L7iJjQX5C2f8koG4G2gevN4BeSGcEvfKe9")

# get the address (from the public key)
p2pkh_addr = p2pkh_sk.get_public_key().get_address()

# Redeem Script that implements the following rules:
# 1) 2 out of 4 potential signers sign a transaction to move the funds elsewhere
# 2) a specific time in the future is reached (absolute timelock), according to
#    a provided timestamp, in which case the first signer (and he alone)
#    can move the funds elsewhere


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
        input1,
        input2,
        input3,
        input4,
        4,
        "OP_CHECKMULTISIG",
        "OP_ENDIF",
    ]
)

# Alternatively, to built the redeem script the following code can be used

# if timestamp < datetime.datetime.timestamp(datetime.datetime.now()):
#     redeem_script = Script(
#         [1656079353, 'OP_CHECKLOCKTIMEVERIFY', 'OP_DROP', 'OP_DUP', 'OP_HASH160',
#          hash1, 'OP_EQUALVERIFY', 'OP_CHECKSIG'])
# else:
#     redeem_script = Script(
#         [2, input1, input2, input3, input4, 4, 'OP_CHECKMULTISIG'])

print(redeem_script)
# create a P2SH address from a redeem script
addressP2SH = P2shAddress.from_script(redeem_script)
print(addressP2SH.to_string())
