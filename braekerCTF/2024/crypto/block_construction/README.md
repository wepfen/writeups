+++
title = 'BraekerCTF 2024 - Block construction'
date = 2024-02-24T18:39:49+01:00
draft = false
description = "braeker CTF 2024 - cryptography "
showTableOfContents = false
## below are user-defined parameters (lower case keys recommended)
tags = ["crypto","writeup"]
type = "post"
toc = false
+++

> "Sir, sir! This is a construction site." You look up at what you thought was a building 
being constructed, but you realize it is a construction bot. "Sir please move aside. 
I had to have these blocks in order since last week, but some newbie construction bot shuffled them." 
"I can move aside, " you tell the bot, "but I might be able to help you out."

## Source code

```python
import binascii 
from Crypto.Cipher import AES
from os import urandom
from string import printable
import random
from time import time

flag = "brck{not_a_flag}"
key = urandom(32)

def encrypt(raw):
	cipher = AES.new(key, AES.MODE_ECB)
	return binascii.hexlify(cipher.encrypt(raw.encode()))

# Generate random bytes
random.seed(int(time()))
rand_printable = [x for x in printable]
random.shuffle(rand_printable)

# Generate ciphertext
with open('ciphertext','w') as f:
	for x in flag:
		for y in rand_printable:
			# add random padding to block and encrypt
			f.write(encrypt(x + (y*31)).decode())
```

## Code explanation

- A seed based on the time is defined with `random.seed(x)`.
- The script shuffle `string.printable` from the string library and stock it in `rand_printable`.
- Concatenate a character of the `flag` with 31 times a caracter of `rand_printable` so the concatenation has a size of 32.
- Then encrypt the concatenation with AES ECB and a randomly generated key of size 32, and repeat the concatenation with every character of `rand_printable`. This process is repeated for every character of `flag`.
- Each encryption is encoded in hex and appended to the file `ciphertext`

## Solving

### Understanding the encryption

First of all, we need to know that AES encrypt block of 16 characters. 
However, in this challenge, strings of 32 characters are encrypted. Meaning thatm the first 16 characters are encrypted, then the 16 other and finally the two cipher are concatenated to make the final ciphertext.

![Explanation of AES encryption](../../images/explanation_aes_encrypt.png)

In this image, we can understand that if the two 16 chars halves of a 32 chars bloc are the same, thus the encryption of the two halves will be the same.

For the challenge we have each character of the flag concatenated with every chars of `rand_printable`.

Exemple for first knwon char 'b': Encrypt('b' + 31 * 'M') , then encrypt('b' + 31 * '8') and so on for all 100 characters of `rand_printable`. 

> I chose '8' and 'M' randomly because `rand_printable` also is.


So there will be a moment where our first character 'b' will be concatened with 31 * 'b' from rand_printable and as we said earlier, then the two halves of the 32 chars (64 chars in hex) of th 32 chars encrypted will be the same. It is how we know which character of the flag is actually encrypted.

To get the flag, knowing all flag characters are encrypted 100 times into 64 hex blocs:
- loop every 6400 chars in `ciphertext` 
- inside this 6400 chars, loop 100 times until we find a 64 hex chars encrypted blocks where its first half is equal to its second half. 
- Note the position of this block in his group of 100 encrypted blocks.

This position will be the position of the char in `rand_printable`.

For instance, if the good bloc is at the position `24`, then the corresponding character will be `rand_printable[24]`, supposing we know rand_printable.

Now after getting every position, we need to find the right `rand_printable` shuffle to get the flag.

### Retrieving the correct rand_printable

The list of the correct indices is the following:

`blocPositions = [85, 89, 11, 63, 32, 51, 84, 74, 40, 36, 42, 14, 23, 36, 84, 75]`

So `flag[0] = rand_printable[blocPositions[0]]` with of course the correct rand_printable.

As said in the **code explanation** section, `rand_printable` is a `random.shuffle()` of `string.printable` with the random seed defined by the time.

We can get the file creation date which is `2024:02:21 14:37:16+01:00` get the unix time of it : `1708526236`.

In the description of the challenge, a bot said the blocks were in place a "week" ago, so i also got the unix time une week before and bruteforced the timestamp from here: `1707865200`.

In a for loop, define the seed, generate a new `rand_printable`, reconstructing a flag with the indice list, and look for 'brck' in the reconstructed flag.


### Script

```python
import random
import string


# get the indice of blocks where block[:32] == block[32:]

def getLetterIndices(blocs) -> list: 

    indicesList = []
    for window in range(0, len(blocs), 6400): # un caractère = 100 blocs de 64 caractères en hex

        blocChunk = blocs[window:window+6400] 

        for bloc in range(0, len(blocChunk), 64): # un bloc fait 64 caractères
            
            # check if the two half are equal
            if blocChunk[bloc:bloc+32] == blocChunk[bloc+32:bloc+64]:
                indicesList.append(bloc//64)
                # passe au caractères chiffré suivant
                break
                
    return indicesList

def getFlag(indicesList):

    initialTimestamp = 1707865200 # a week before file creation
    lastTimestamp = 1708556400 # file creation timestamp
    flag = ''
    rollback = 0

    timestp = initialTimestamp
    rand_printable = string.printable
    
    while flag[0:4] != 'brck':

        #(re)define rand_printable
        rand_printable = list(string.printable)
        
        #define seed
        random.seed(timestp + rollback)
        
        #shuffle string.printable
        random.shuffle(rand_printable)

        flag = "".join([rand_printable[i] for i in indicesList])
        
        #if 'brck' in flag:
        #    print(timestp)

        rollback += 1

    return flag
        
if __name__ == '__main__':
    
    rawBlocs = open("ciphertext.old", 'r').read()
    indicesList = getLetterIndices(rawBlocs)
    flag = getFlag(indicesList)
    print(flag)
```


## TL;DR

- Each character are concatenated with 31 times a random character of a charset and then encrypted.

- Some times the random character will be the flag character

- In this case, the two halves of the encrypted block will be the same and we can determine the position of this block in his group of 100 other encrypted blocks.

- Get the flag like this:

	- Set the seed of random with the timestamp of the file
	- shuffle hte charset string.printable
	- Map the blocks position with the chars position of the right charset like that: `flag[i] = rand_printable[blocPositions[i]]`
	- Try to find 'brck' in the generated flag
	- Iterate again till it works




> Flag: `brck{EZP3n9u1nZ}`


