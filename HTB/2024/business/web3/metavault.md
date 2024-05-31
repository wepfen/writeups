> Difficulty : easy

> [Source files](https://github.com/hackthebox/business-ctf-2024/tree/main/blockchain/MetaVault%20%5BEasy%5D)

>The Ministry of Defense released the open source of "MetaVault", the country's Ethereum reserves. It's said that they keeps secrets in a meta-location, so that no one can know them.

# Introduction

The challenge introduces to the use of meta-data in a solidity contract

To validate we need to steal all ether of the target contract.

# Recon

## TL;DR

So for i solving i just have to :
- Get the bytecode of the contract
- Send it to https://playground.sourcify.dev/
- Get the plaintext password
- Interact with target and get my ethers

## Code

MetaVault.sol

```solidity
// SPDX-License-Identifier: MoD-Internal-v1.0
pragma solidity 0.8.25;

/**
 * @title MetaVault
 * @author Ministry of Defense
 * @notice MoD (Ministry of Defense) Smart Contract storing the country's ETH reserves.
 */
contract MetaVault {
    /**
     * @notice Keccak256 hashed secret passphrase to enable emergency mode.
     * @dev plaintext secret: WeLoveNukaCola!!MoD-2024 
     * @dev The secret will be stripped before open sourcing the code. Comments are not compiled anyway.
     */ 
    bytes32 constant private VAULT_SECRET_K256 = 0x42c10591ced4987005f70d29b498348ecc8ab18dd28c5b93db931375ca826b5e; 
    
    event Deposit(
        address indexed _from,
        uint256 indexed _value,
        uint256 indexed _updatedBalance
    );
    event FailedLoginAttempt(
        address indexed _from,
        string  indexed _attempt,
        bytes32 indexed _hashedAttempt
    );
    event EmergencyMode(
        address indexed _by,
        address indexed _fundsDestination
    ); 

    /**
     * @dev Retrieves the current ETH balance of the vault.
     * @return balance of the vault in wei.
     */
    function getVaultBalance() public view returns (uint256) {
        return address(this).balance;
    }

    /**
     * @notice Deposit function to receive ETH deposits.
     * @dev emits a Deposit event with the depositor, the value deposited and the updated balance after deposit.
     */
    function deposit() public payable {
        emit Deposit(
            msg.sender,
            msg.value,
            getVaultBalance()
        );        
    }

    /**
     * @notice Function to fire the emergency mode by selfdestructing the contract and transfering the funds away.
     * @param _secret The secret passphrase required to activate emergency mode.
     * @dev The secret is shared only to MoD devs.
     */
    function emergency(string memory _secret) external {
        bytes32 attempt_k256 = keccak256(bytes(_secret));
        if (attempt_k256 == VAULT_SECRET_K256) {
            emit EmergencyMode(msg.sender, msg.sender);
            selfdestruct(payable(msg.sender));
        } else {
            emit FailedLoginAttempt(msg.sender, _secret, attempt_k256);
        }
    }
}
```

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

Luckily for us, reading this [page](https://playground.sourcify.dev/) (which i find by googling `solidity meta-data lookup` and reading https://docs.sourcify.dev/docs/metadata/) we can understand that they actually are. We just have to supply the contract bytecode (the source code but [translated](https://blog.chain.link/what-are-abi-and-bytecode-in-solidity/).

## Interacting with the instance

Launching the instance i got 3 ips, one for the rpc endpoint, one which is the webpage of MetaSafe (the name of the vault for the scenario) and one IP to manage the instance an get the flag.

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

# Solve

## Casting spells

We will use foundry to solve and it's **EXTREMELY** useful **cast** command. Here is the doc: https://book.getfoundry.sh/reference/cli/cast.html.

With cast we can do everything we need: publishing a transaction, calling functions of contract WITHOUT publishing a transaction, doing data conversions, getting informations of blocs, getting transaction informations or even **getting the bytecode of a contract**.

Let's setup our envrionement:

With foundry installed installed ( i use a debian VM for the challenges ), we will set up environment variable to make everything prettier and easier.

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

5. Get the flag by contacting the instace management IP 

`HTB{wh0_tf_sh4r3s_s3cr3ts_1n_th3_c0mm3nts}`

# Ressources

https://book.getfoundry.sh/reference/cast/cast-send

https://docs.soliditylang.org/en/latest/cheatsheet.html

https://docs.soliditylang.org/en/latest/natspec-format.html

https://playground.sourcify.dev/

https://docs.sourcify.dev/docs/metadata/

https://blog.chain.link/what-are-abi-and-bytecode-in-solidity/
