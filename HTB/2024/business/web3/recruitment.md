> Difficulty : Very easy

> [Source files](https://github.com/hackthebox/business-ctf-2024/tree/main/blockchain/Recruitment%20%5BVery%20Easy%5D)

>Do you think you have what it takes to live up to this crew? apply and prove it.

# Introduction

The challenge need us to "apply" by sending some specific value to fill the requirements.

# Recon

This challenge was my first blockchain challenge solved in CTF (except in [root-me](https://www.root-me.org/en/Challenges/Programming/)).
I used a VM with debian to solve this but is possible on any linux distro (maybe windows but idk)

## Reading the smart contract

We can apply by interacting with the function `application(uint16 input1, string memory input2)` by supplying two parameters.

Reading the contract `Recruitment.sol`: 

```solidity
function application(uint16 input1, string memory input2) public {
        // In order to be eligible, you must match the following set of skills:
        // - Hacker
        // - Stealth Specialist
        // - Engineer
        // - Demolition Specialist

        // Let's start!
        // Some preliminary checks: we do not hire unlucky people.
        require(block.timestamp % 2 == 0, "Natural selection people say..");

        // CAPTCHA (Completely Automated Public Turing test to tell Computers and Humans Apart)
        require(tx.origin == msg.sender, "Are you even human?");

        // Now let's start for real.
        // 1. Are you an hacker?
           require(input1 == 1337, "You lack hacking skills.");
        // yeah you definitely are.

        // 2. Are you stealthy?
        require(block.number < 20, "You lack stealth skills.");

        // 3. Are you an engineer?
        require(gasleft() <= 50000, "You lack engineering skills.");

        // 4. Are you a demolition specialist?
        require(keccak256(abi.encodePacked(input2)) == keccak256(abi.encodePacked("BOOM")), "You lack demolition skills"

        // Congratulations! Welcome to the crew.
        crew[msg.sender] = true;
        // here is your reward :)
        payable(msg.sender).transfer(1 wei);
        }
```

We understand that to get recruited we need to:

- send an interaction when the timestamp is odd (we can't influence on that, just call the function a few time)
- input1 == 1337
- block.number < 20 : we have to solve in under 20 transaction
- gasleft <= 50000 
- input2 == BOOM

# Solve

## Getting familiar with the instance 

Blockchain challenges on hackthebox are not on sepolia network but on a local networ using [anvil](https://book.getfoundry.sh/reference/anvil/)

Starting the instance we got two ip, one for the RPC endpoint and one to get the flag and other informations.

We have got two IPs but the first time i saw it i didn't understand the frick it was for. Then i used netcat to contact them and one gave me a response:

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

But i was still not familiar with HackTheBox's game so i decided to try basic command on the second IP which did not respond at first.

For that i used the INCREDIBLE, ONLY and ONE [cast](https://book.getfoundry.sh/reference/cli/cast) cli utility from foundry-rs framework.

I can for instance check the balance of my contract with this noob tier command without environment variables : `cast balance 0xF7b5424a61fFD3Afa8B2a1350d94Ff06D1f13eF7 --rpc-url http://<IP>:<PORT>` 

So now i understand that i got my address, my private key and the target contract address and how to interact with it.

To make commands easier, i will set environment variables:

```
PRIVATE_KEY=0x0a5c3d2e7717a2f9292d5f13084352a800cad51eb923b169184b22f9863ad554
RPC_URL=http://94.237.61.244:38424/
TARGET=0x03d65b9e5740f7a8b8c9aAfAc74fB26Ff2328eC4
ATTACKER=0xF7b5424a61fFD3Afa8B2a1350d94Ff06D1f13eF7
```

I also noticed that cast blockchain spells with `cast send` doesn't increase block number if the transaction fail due to the `require` in the target contract. So i can try multiple time until i got it right..


## Getting recruited

For applying we need to interact with the function `application` which has the signature : `application(uint16,string)`

- To prove we are not unlucky, just run the transaction couple of times until it work. If it doesn't, the transaction will just revert.

- To pass the captcha, we need to have tx.origin == msg.sender. To be short, `msg.sender` is the address of the "account" running the transaction, where the ether will be taken for gas transaction  for instance. And `tx.origin` is the address of the contract which has interacted with the destination contract.
     - If it is a smart contract, tx.origin == address of the smart contract.
     - If it is a person, tx.origin == msg.sender, address of the account publishing the transaction.

- To fill hacker and demolition skills we need to call the contract wit values: `1337` and `"BOOM"`.

- To fill the engineer skills we can set --gas-limit close to 50000 but above of it. I had got some trouble wtih this part and thanks to HTB support i found that my gas limit was to low (50000). So i send with --gas-value = 60000.

Here is the final command:

`cast send $TARGET --gas-limit 60000 --from $ATTACKER --rpc-url $RPC_URL --private-key $PRIVATE_KEY "application(uint16,string)" 1337 "BOOM"`

We can fire this command until there are no more require error and get the flag.


`HTB{th3y_s4id_W3lc0m3_Ab0ard}`

# Ressources

https://book.getfoundry.sh/reference/cast/cast-send

https://docs.soliditylang.org/en/latest/cheatsheet.html
