> Recruitment - Blockchain
> Very easy

>Do you think you have what it takes to live up to this crew? apply and prove it.

# Introduction

The challenge need us to "apply" by sending some specific value

# Recon

We can apply by interacting with the function `application(uint16 input1, string memory input2)` by supplying two parameters.

Reading the contract `Recruitment.sol`: 

```
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

Starting the instance we got two ip, one for the RPC endpoint and one to get the flag and other informations.

One ip respond to nc and i get the contract addresses:

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

I can set environment variables:

PRIVATE_KEY=0x0a5c3d2e7717a2f9292d5f13084352a800cad51eb923b169184b22f9863ad554
RPC_URL=http://94.237.61.244:38424/
TARGET=0x03d65b9e5740f7a8b8c9aAfAc74fB26Ff2328eC4
ATTACKER=0xF7b5424a61fFD3Afa8B2a1350d94Ff06D1f13eF7

To solve we will use foundry and it's incredible [cast](https://book.getfoundry.sh/reference/cli/cast) command.

Cast is useful because i can easily make transaction.

If the transaction is not succesful, no block will be published so we can validate stealth skill.

We can specify arguments, in this challenge it is `1337 and "BOOM"`.

Finally we can set --gas-limit close to 50000 but above of it. I had got some trouble wtih this part and thanks to HTB support i found that my gas limit was to low (50000).

Here is the command:

`cast send $TARGET --gas-limit 60000 --from $ATTACKER --rpc-url $RPC_URL --private-key $PRIVATE_KEY "application(uint16,string)" 1337 "BOOM"`

We can fire this command until there are no more require error and get the flag.


`HTB{th3y_s4id_W3lc0m3_Ab0ard}`

# Ressources

https://book.getfoundry.sh/reference/cast/cast-send

https://docs.soliditylang.org/en/latest/cheatsheet.html
