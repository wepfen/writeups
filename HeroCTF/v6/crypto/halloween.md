+++
title = 'Heroctf v6 - Halloween [crypto]'
date = 2024-10-30T00:21:39+01:00
draft = false
## below are user-defined parameters (lower case keys recommended)
tags = []
type = "post"
toc = true

[params]
  math = true
+++

<br>
My solve from a noob point a view for the halloween challenge at heroCTF v6.

<!--more-->

> Difficulty : Hard

> Team : Langskip

> [Source files](https://github.com/HeroCTF/HeroCTF_v6/tree/main/Crypto/Halloween/halloween)

> Boo! Do you believe in ghost ? I sure don't

> Author : alol

<br>

# TL;DR

The GOST cipher used for the challenge is badly implemented.

Using the CTR mode, the counter reset after 256 count. So we can regenerate the keystream used to encrypt the flag and decrypt the flag.

<br>

# Introduction

For this challenge, a server sends us a welcome message with the encrypted flag inside.
It will then encrypt each message (encoded in hexadecimal) we send to it.

The algorithm used is an implementation of [GOST](https://en.wikipedia.org/wiki/GOST_(block_cipher)#), a symmetrical algorithm like AES.

<br>

# Solving

## Challenge source code

The challenge code is quite simple.

```python
#!/usr/bin/env python3
import gostcrypto
import os

with open("flag.txt", "rb") as f:
    flag = f.read()

key, iv = os.urandom(32), os.urandom(8)
cipher = gostcrypto.gostcipher.new(
    "kuznechik", key, gostcrypto.gostcipher.MODE_CTR, init_vect=iv
)

print(f"It's almost Halloween, time to get sp00{cipher.encrypt(flag).hex()}00ky 👻!")

while True:
    print(cipher.encrypt(bytes.fromhex(input())).hex())
```

- A 32-byte random key is generated
- An 8-byte initialization vector is generated
- `cipher` is initialized with gostcrypto with the CTR mode, the key, the IV and the algorithm we don't yet know 'kuznechik'.

Once this is done, the server sends us a string with the encrypted flag in it, for example : 

```
It's almost Halloween, time to get sp00361e2084c41bd4ddf3748a49442d2c99670f6d235d2429e3d6e445f07d5415f2ebd38bee6bf50fecd23ae33db8a76c48d1ab7bb7591512b354762afbfa7153e494f8eb3bd93ad1151d3c36f4c1913400ky 👻!
```

So far, there's no obvious vulnerability, so you'll have to dive into the source code (it's a tough challenge, though!).

And then you can send strings of characters encoded in hex and the server will reply with its encrypted version.

## Reading gostcrypto module source code

For python modules, just look on pypi.

After a quick google search on pypi you'll find [this page](https://pypi.org/project/gostcrypto/). 

And in "project links" you'll find a link to github with all the [source code](https://github.com/drobotun/gostcrypto) and a [user doc](https://gostcrypto.readthedocs.io/en/stable/intro.html#overview) but the doc won't be useful.

### Reading the parts used for encryption

Let's dive straight into the source code, i.e. the `gostcrypto.gostcipher` module at this [page](https://github.com/drobotun/gostcrypto/tree/master/gostcrypto/gostcipher).

There are two files:

- gost_34_12_2015.py
- gost_34_13_2015.py

A quick look at the first file reveals that this is where the 'kuznechik' and 'magma' algo are defined. Here we have the source code for encrypting plaintext in ECB mode. In other words, classic encryption without mode, as with AES:


<img src="https://upload.wikimedia.org/wikipedia/commons/d/d6/ECB_encryption.svg" style="filter: invert(70%) sepia(100%) saturate(700%) " alt="ECB encryption mode"/>

<br> 

In the second file, all modes are defined, including `CTR` on line 802 in the `GOST34132015ctr` class: `class GOST34132015ctr(GOST34132015Cipher):`.

It contains the `encrypt()`, `decrypt()`, `counter()`, `_inc_ctr()` methods.

The simplest is the `decrypt()` method:


```python
    def decrypt(self, data: bytearray) -> bytearray:
        """
        Ciphertext decryption in CTR mode.

        Args:
            data: Ciphertext data to be decrypted (as a byte object).

        Returns:
            Plaintext data (as a byte object).

        Raises:
            GOSTCipherError('GOSTCipherError: invalid ciphertext data'): In
              case where the ciphertext data is not byte object.
        """
        data = super().decrypt(data)
        return self.encrypt(data)
```

`super().decrypt(data)` will not alter data, it corresponds to the `decrypt()` method of the `GOST34132015Cipher` class inherited by `GOST34132015ctr` which does :

```python
def decrypt(self, data: bytearray) -> bytearray:
	if not isinstance(data, (bytes, bytearray)):
		self.clear()
		raise GOSTCipherError('GOSTCipherError: invalid ciphertext data')
	return data
```

So `super().decrypt(data)` checks whether the data is of type `bytes or bytearray` and then encrypts it with `self.encrypt(data)`.

Encrypting a ciphertext with CTR mode is like deciphering it.

<img src="https://upload.wikimedia.org/wikipedia/commons/4/4d/CTR_encryption_2.svg" style="filter: invert(70%) sepia(100%) saturate(700%) " alt="CTR encryption mode"/>


> The CTR mode is a [stream cipher](https://en.wikipedia.org/wiki/Stream_cipher) which means that the cipher can be xoried with the plaintext and therefore the plaintext size is equal to the cipher size.
> If we know the plaintext, we can xor it with the ciphertext to recover the keystream, and if we know the keystream, we can xor it with the ciphertext to recover the plaintext.

Then, the `counter()` method only returns the counter and the method `_inc_ctr()` increments the counter. 

At class initialization, `gostcrypto.gostcipher.new("kuznechik", key, gostcrypto.gostcipher.MODE_CTR, init_vect=iv)` in the challenge amounts to executing the `__init__()` method, which takes the algo, key and IV as parameters:

- A counter is defined as `iv + b"\x00"*8`, i.e. the first half of the counter is a random nonce and the lower half is the counter starting at 0.
- The `GOST34132015` class (and not `GOST34132015Cipher`, as the latter doesn't have a `__init__` method, so the class above is initialized instead) is initialized with `super().__init__(algorithm,key)`, which defines :
  - the algorithm, i.e. 'kuznechik' for us
  - `self._cipher_obj: CipherObjType = GOST34122015Kuznechik(key)`, defines `_cipher_obj` with `kuznechik`, which will be used to encrypt our plain text.

### CTR mode execution flow

The execution flow is defined in the `encrypt()` method [line 855](https://github.com/drobotun/gostcrypto/blob/master/gostcrypto/gostcipher/gost_34_13_2015.py#L189)

- The current counter (starting at 0) is encrypted and the result stored in `gamma`: `gamma = self._cipher_obj.encrypt(self._counter)`.
- The counter is incremented: `self._counter = self._inc_ctr(self._counter)` 
- a XOR operation is applied between the encrypted counter and the current block: `result + add_xor(self._get_block(data, i), gamma)`

The 'if' block corresponds to the same thing, but for a block that isn't 16 characters long.
By the way, block size is defined [here](https://github.com/drobotun/gostcrypto/blob/1590311620d6d03d1d8e1b6abe1966da4c8550ed/gostcrypto/gostcipher/gost_34_12_2015.py#L26)

```python
if len(data) % self.block_size != 0:
	gamma = self._cipher_obj.encrypt(self._counter)
	self._counter = self._inc_ctr(self._counter)
	result = result + add_xor(
		data[self.block_size * self._get_num_block(data)::], gamma
	)
```

We could go and analyze the `kuznechik` function in depth, but there were no papers talking about an exploitable vulnerability there so i slowed down.

So I decided to test all the functions of the [GOST34132015ctr class](https://github.com/drobotun/gostcrypto/blob/1590311620d6d03d1d8e1b6abe1966da4c8550ed/gostcrypto/gostcipher/gost_34_13_2015.py#L802C7-L802C22).

### Analysis of counter incrementation

Testing `_inc_ctr()`, we notice something interesting. Here's the code:

```python
def _inc_ctr(self, ctr: bytearray) -> bytearray:
	internal = 0
	bit = bytearray(self.block_size)
	bit[self.block_size - 1] = 0x01
	for i in range(self.block_size):
		internal = ctr[i] + bit[i] + (internal << 8)
		ctr[i] = internal & 0xff
	return ctr
```

Actually i didn't see anything at first sight, i just put the fonction in a jupyter notebook and tested a lil.

I discovered that by taking an example counter: `12916ac66cc1cbfe0000000000000000`, notice that the part that must be incremented is `0000000000000000` being 8 bytes long and therefore $ 256^{8} = 18446744073709551616 $ counter possibilities.

Except that, in this implementation, the counter rises to `00000000000000ff` and then, on the next increment, resets to `0000000000000000`.

As a result, there are only 256 possible counter values, which greatly reduces the list of possibilities and allows us to recover the keystream used to encrypt the flag.

Knowing that the counter is incremented with each block, we need to find out how many times the counter has been incremented to encrypt the flag, subtract this number from 256, increment the counter by the number we obtain and recover the keystream by sending a null byte string of the same size as the flag (since the keystream is encrypted with the plaintext, sending null bytes enables us to directly recover the key because 0 xor n = n).


### Exploit 

```python
from pwn import remote, context, xor

import re

BLOCK_SIZE = 16

context.log_level = 'CRITICAL'
host = "crypto.heroctf.fr"
port = 9001

conn = remote(host, port)

welcome_message = conn.recvS()
print(f"Got message : {welcome_message}")

flag_ct = re.search(r"(?<=sp00).*(?=00ky)", welcome_message).group() # regex to extract the encrypted flag, test it here: https://regex101.com/r/fb0QSo/1
flag_ct = bytes.fromhex(flag_ct)
print(f"Got ciphertext : {flag_ct.hex()}\n")

counter_offset = len(flag_ct)//BLOCK_SIZE + 1 if len(flag_ct)%BLOCK_SIZE!=0 else 0

print("Sending payload")

# payload to reset the counter
payload_size = 256 - counter_offset
reset_counter_payload = b"\x00"*payload_size*BLOCK_SIZE
conn.sendline(reset_counter_payload.hex().encode())
conn.recvuntilS("\n")

# payload to get the keystream
keystream_payload = b"\x00" * counter_offset * BLOCK_SIZE
conn.sendline(keystream_payload.hex().encode())
keystream = bytes.fromhex(conn.recvS().rstrip())
print(f"Got keystream {keystream.hex()} with length {len(keystream)}")

flag = xor(keystream, flag_ct)
print(f"Recovered : {flag}")
```

<br>

flag : `Hero{5p00ky_5c4ry_fl4w3d_cryp70_1mpl3m3n74710ns_53nd_5h1v3r5_d0wn_y0ur_5p1n3}`

<br>

# Conclusion

I really liked the challenge and found it intersting. I learned source code "auditing" and a new cipher.

The code was well written so easy to understand, and there was no horrible mathematics only understandable by PhDs.

# Links

- https://en.wikipedia.org/wiki/Stream_cipher
- https://pypi.org/project/gostcrypto/
- https://gostcrypto.readthedocs.io/en/stable/intro.html#overview
- https://github.com/drobotun/gostcrypto
