+++
title = 'DefCamp quals 2024 - ctr [crypto]'
date = 2024-09-29T15:13:31+02:00
draft = false
## below are user-defined parameters (lower case keys recommended)
tags = []
description = "DefCamp quals 2024 ctr challenge writeup"
type = "post"
toc = true
+++
> Difficulty : Guessy - i didn't solved it so i'm rude >:( 

> Team : Phreaks 2600

> [source files](https://raw.githubusercontent.com/wepfen/writeups/refs/heads/main/defcampCTF/2024/ctr/ctr.txt)

> Are you feeling down? Here is a list of exciting words for you, hope you'll feel better after this. (probably not)


# TL;DR

- we got a file `ctr.txt` which is a list of ciphertexts encrypted with the same key as the oracle we deal with 
- we can send a plaintext to an oracle we send it back to us using AES CTR, so the counter will increase for the next plaintext but it resets if you reset the connexion
- send 16 null bytes and get the encrypted key that is used to get the plaintext or the ciphertext
- bruteforce the oracle until you can recover the ciphertext by xoring the encrypted key with a chipghertext from `ctr.txt` and not down the counter number (i.e: if we requested the oracle 50 times, note down 50)
- repeat till we got all the number and print their ascii values

# Introduction

We need to decrypt a list ciphertext abusing of a AES-CTR nonce reuse oracle

# Recon

## Interacting with the server

First of all, there weren't any source code >:(

On the ctf platform we can start an instance for the challenge an then get an ip and port to interact with.

next i can connect with `nc  IP PORT`

i receive this message : `Give me no more than 16 bs`

Which means 'send me 16 bytes or less' (i don't know why the author use 'bs' but it's kind of confusing)

Then i send 'a' and receive `02308264a4b8dc1a27520cbae8854516`. Then i resend 'a' and get `cc528ba18b1c9089064d80148680e30e`.

But when i open an other connexion with the server, i get the sames ciphretexts meaning the oracle reuse the same nonce. 

The key change at every encryption, but not the nonce. Knowing it is AES CTR as challenge name tells, we can understand why it changes.

Here is an illustration: 

![AES CTR mode encryption](https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/CTR_encryption_2.svg/512px-CTR_encryption_2.svg.png)

![AES CTR mode decryption](https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/CTR_decryption_2.svg/512px-CTR_decryption_2.svg.png)

So the keystream_n is the result of the encryption of a counter prepended by a nonce : `keystream_n = E(nonce+n)` where E() is AES encryption

> Note : Sometimes the nonce is reused or there is no nonce at all

Then to get the ciphertext, we XOR the keystream with the ciphertext: `ciphertext = plaintext XOR keystream_n`

> Note : The keystream_n is the same for encryption and decryption


So to get the keystream : 

- send 16 null bytes (easier with python)
- we receive the keystream and that's all, because : `ciphertext = keystream XOR b"\x00"*16 = keystream` because n XOR 0 = n
 
## Trying to recover plaintexts from the ctr.txt file

A normal (naive) person would think that flag would be in this list of plaintexts...

![clueless](https://cdn.betterttv.net/emote/60419081306b602acc5972c9/3x.webp)

The first ciphertext is `f24e8c4bb594b2590edc658609608f16`

We query the oracle, get the keystream and XOR it with our ciphertext, here is a code snippet:

```python
from pwn import remote, context, xor

host = "35.246.159.226"
port = 30724 

context.log_level = 'CRITICAL'
conn = remote(host, port)

conn.recvuntilS(b'bs\n')
conn.sendline(plaintext)
keystream = bytes.fromhex(conn.recvS().split()[3])
ciphertext = bytes.fromhex('f24e8c4bb594b2590edc658609608f16')

print(xor(keystream, ciphertext)
```

Spoiler, all we got is garbage. 
So my first reaction is 'what if first keystream is not for the first ciphertext but it is completely random?'

Then, the GOAT (but also my [teammate](https://blog.lightender.fr/)) guessed that he can recover a plaintext by bruteforcing the oracle until he got a valid plaintext.

So i implement this and i get my first plaintext : `ThrillingThrilli` at counter 67

code : 


```python
flag = bytes.fromhex("f24e8c4bb594b2590edc658609608f16")
for i in range(1000):
        conn.recvuntilS(b'bs\n')
        conn.sendline(plaintext)
        keystream = bytes.fromhex(conn.recvS().split()[3])
        
        try:
            print(xor(keystream, flag).decode())
            print(f"{i=}")
            #print(f"{keystream.hex()=}")
            sys.exit(1)
        except:
            continue
```

After that i decide to apply it to the whole  `ctr.txt`.
I managed to vontinue bruteforcing and i get another one : `ExhilaratingExhi` at counter 84

And nothing else ...

I immediately think 'what if I just restart the connexion at every plaintext the connexion' and it works !

code snippet : 

```python
from pwn import remote, context, xor

host = "35.198.191.122"
port = 31082 

context.log_level = 'CRITICAL'



def decrypt_words():

    conn = remote(host, port)
    
    words = open("ctr.txt", 'r').read().split("\n")
    words = [bytes.fromhex(word) for word in words]

    plaintext = b"\x00"*16
    recovered = []
    
    i = 0
    words_offset = 0

    
    while True:

        i += 1
        
        conn.recvuntilS(b'bs\n')
        conn.sendline(plaintext)
        keystream = bytes.fromhex(conn.recvS().split()[3])

        try:
            pt = xor(keystream, words[words_offset]).decode()
            print(f"recovered {pt}")
            recovered.append(pt)
            print(f"{i=}, word number {words_offset}")
            words_offset += 1
            conn = remote(host, port)
        except Exception as e:
            continue
        
        if len(words) == words_offset:
            break
```

The counter offsets where increasing until reaching 3000+ but i cluelessly think that it didn't matter. (naive)

![clueless](https://cdn.betterttv.net/emote/60419081306b602acc5972c9/3x.webp)

I managed to decrypt every words : 

```plaintext
ThrillingThrilli
ExhilaratingExhi
...
JoyousJoyousJoyo
JubilantJubilant
```

And then i didn't know what the f to do.

As the challenge description say there are 'exciting words', i thought about finding the non exciting word and get it sha256 sum then submit it as a flag...

It is where the intense guessing phase started. >:(


# Solving

So after the event, i went chatting with people in the discord, then 'miniaturepif' said `ctr nonce reuse, and flag was encoded in nonces, one char for each ct`.

I don't how he recovered this though. The nonce is AES encrypted, he can't really recover it and i didn't find something relevant on google.

Then 'szkalom' said `You had to guess that the counters used to encrypt the cipertexts you have are actually ascii codes of the flag chars`.

So i realized that the counter number actually MATTER.

![cries in skill issue](https://i.imgflip.com/95210h.jpg)

So I fixed my code and got the flag:

```python
import sys

from pwn import remote, context, xor

host = "35.198.191.122"
port = 31082 

context.log_level = 'CRITICAL'



def decrypt_words():

    conn = remote(host, port)
    
    words = open("ctr.txt", 'r').read().split("\n")
    words = [bytes.fromhex(word) for word in words]

    plaintext = b"\x00"*16
    recovered = []
    counter_offsets = []
    
    #get to correct counter offset
    i = 0
    words_offset = 0

    
    while True:

        i += 1
        
        conn.recvuntilS(b'bs\n')
        conn.sendline(plaintext)
        keystream = bytes.fromhex(conn.recvS().split()[3])

        try:
            pt = xor(keystream, words[words_offset]).decode()
            print(f"recovered {pt}")
            recovered.append(pt)
            print(f"{i=}, word number {words_offset}")
            words_offset += 1
            counter_offsets.append(i)
            i = 0 # this line changed my whole perception of life
            conn = remote(host, port) # reset connexion
        except Exception as e:
            continue
        
        if len(words) == words_offset:
            break

    flag = ''.join(map(chr, counter_offsets))
    print(f'{flag=}')
    
    with open('decrypted.txt', 'w') as f:
        for dec in recovered:
            f.write(dec+"\n")
    
    
    

if __name__ == '__main__':
    decrypt_words()
```

flag: `CTF{d6bd1954527310f3f831baa46582f553a9e780d8fa747637d25da1281c24edaf}`

Now i understand why there were'nt any source codes...

# Conclusion

Please chall makers, respect our mental health and limit the guessing.


