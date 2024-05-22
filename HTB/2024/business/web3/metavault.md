>MetaVault - Blockchain - Easy

>The Ministry of Defense released the open source of "MetaVault", the country's Ethereum reserves. It's said that they keeps secrets in a meta-location, so that no one can know them.

# Introduction

The challenge introduces to the use of meta-data in a solidity contract

To validate we need to stole all ether of the target contract.

# Recon


## Code

The source codes can be found [here]() (insert link to my github)

Looking at the source code of `MetaVault.sol` we can notice 

- A function `deposit()` allowing us to deposit ether on the contract
- A function `getVaultBalance()` to return balance of the vault in wei
- An intersting function `emergency(string memory _secret)` which will send all the ether of the vault if we find the correct password.
- And also many comments in the [NatSpec](https://docs.soliditylang.org/en/latest/natspec-format.html) format.

Reading comments, we understand that the password for `emergency` was stored in plaintext. But the devs affirms that `comments are not compiled`: 

```solidity
* @dev plaintext secret: [REDACTED]
* @dev The secret will be stripped before open sourcing the code. Comments are not compiled anyway.     
```

Luckily for us, reading this [page](https://playground.sourcify.dev/) we can understand that they actually are. We just have to supply the contract bytecode.

## Interacting with the instance

Launching the instance i got 3 ips, one for the rpc endpoint, one which is the webpage of MetaSafe (the name of the vault for the scenario) and on IP to manage the instance an get the flag.

I contact the last IP with nc `nc 94.237.61.244 38186` and request the information for the challenge:

```
1 - Connection information
2 - Restart Instance
3 - Get flag
action? 1

Private key     :  0x0a5c3d2e7717a2f9292d5f13084352a800cad51eb923b169184b22f9863ad554
Address         :  0xF7b5424a61fFD3Afa8B2a1350d94Ff06D1f13eF7
Target contract :  0x03d65b9e5740f7a8b8c9aAfAc74fB26Ff2328eC4
Setup contract  :  0x6224fF48Af65663fB8b10CF830ECAC6F75B674f6

```

So now i got my address, my private key and the target address.

# Solving

## TL;DR

So for i solving i just have to :
- Get the bytecode of the contract
- Send it to https://playground.sourcify.dev/
- Get the plaintext password
- Interact with target and get my ethers

## Using foundry

We will use foundry to solve and it's **EXTREMELY** useful **cast** command. Here is the doc: https://book.getfoundry.sh/reference/cli/cast.html.

With cast we cast we can do everything we need: publishing a transaction, call functions of contract WITHOUT publishing a transaction, doing data conversions, getting informations of blocs, getting transaction informations and **getting the bytecode of a contract**.

Let's setup our envrionement:

With foundry installed installed ( i use a debian VM by the way ), we will set up environment variable to make everything prettier and easier.

### environment variables

create a `.env` (or whatever you want to call it) file with this content: 

```
PRIVATE_KEY=0x0a5c3d2e7717a2f9292d5f13084352a800cad51eb923b169184b22f9863ad554
RPC_URL=http://94.237.61.244:38424/
TARGET=0x03d65b9e5740f7a8b8c9aAfAc74fB26Ff2328eC4
ATTACKER=0xF7b5424a61fFD3Afa8B2a1350d94Ff06D1f13eF7
```

And then execute : `source .env` to have all our variable set 

> Notice that they will be set for the shell where you executed the command only.

### foundry.toml

In the challenge files we got a foundry.toml

We will only append the RPC endpoint url at the end of it:

```
[rpc_endpoints]

sepolia = "http://94.237.61.244:38424"
```

Now we are ready to exploit.

1. Let's get first the bytecode of the target contract with the `cast code` function:

`cast code -r $RPC_URL $TARGET`

> We will need to copy the result of it.

2. Paste the bytecode in https://playground.sourcify.dev/

> The result will output a json similar to this one https://ipfs.io/ipfs/QmX9L9Q9QkM3ytQ1Wk3jKAqNDXYhK8RFQHcfq8QXyfffkN

3. Copy the vault password in the json: `WeLoveNukaCola!!MoD-2024`

4. Interact with the `emercgency` command in the contract with the recovered password

`cast send $TARGET -r $RPC_URL -f $ATTACKER --private-key $PRIVATE_KEY  "emergency(string)" 'WeLoveNukaCola!!MoD-2024'`

5. Get the flag by contacting the instace managing IP 

`HTB{wh0_tf_sh4r3s_s3cr3ts_1n_th3_c0mm3nts}`

# Ressources

https://book.getfoundry.sh/reference/cast/cast-send

https://docs.soliditylang.org/en/latest/cheatsheet.html
