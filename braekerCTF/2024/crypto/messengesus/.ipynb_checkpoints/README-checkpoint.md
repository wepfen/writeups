# Introduction

>You encounter a bot meditating in the park. He opens his cameras and begins to speak.
>
>"Hear the word of RNGesus. Complexity is the enemy of security. Let your encryption be as simple as possible, as to secure it, thusly". He hands you a flyer with a snippet of code. "Secure every message you have with it. Only those who see can enter."
>
>What do you think? Is it simple enough to be secure?

## Source code

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


int main() {

    char secret[] = "brck{not_the_flag}";
    char *key = NULL;
    size_t read_length, buffer_length = 0;
    
    // Read One Time Key
    FILE *random_bytes = fopen("/dev/urandom", "r"); //incassable comme d'hab
    read_length = getline(&key, &buffer_length, random_bytes); 
    fclose(random_bytes); 

    // Encrypt
    for (int i = 0; i < strlen(secret); i++)
        secret[i] = secret[i] ^ key[i%read_length];

    // Return encrypted secret
    printf("%s", secret);

    free(key);
    return 0;
}
```

# Recon

Reading man for `getline()` (thanks to [admin](https://github.com/spipm) adivce), we understand that getline take bytes from a file until a `\n` or 0x0A bytes is encoutered.


So each time we connect to the server we got a ciphertext xored with a key from `/dev/urandom` and it's length can vary it only depends of the presence of `0x0A` bytes. So the key can have a length of 1 or even 500.

The solution is to request a server until the key is short enoguh, (1 or 2 bytes).

And we can know that by xoring 1st character of the known plaintext which is `'b'` from `'brck{'` and comparing it with the xor of the 2nd known character with the 2nd character of the ciphertext.

# Solve

```python
from pwn import *

host = '0.cloud.chals.io'
port = 26265



flag = b'' # known plaintext 1
kpt1 = b'b'
kpt2 = b'r'
kpt1bis = b'c'
kpt2bis = b'k'

kpt3 = b'br' 
kpt4 = b'ck'

context.log_level = 'critical'

print("[+] Début du brute force de fou bz")

print("[+] Sanity check")
conn = remote(host, port)
print(conn.recv())
conn.close()

while not flag:
    
    conn = remote(host, port)
    ciphertext = conn.recvS()

    key1 = xor(ciphertext[0], kpt1)
    key2 = xor(ciphertext[1], kpt2)
    key1bis = xor(ciphertext[2], kpt1bis)
    key2bis = xor(ciphertext[3], kpt2bis)

    key3 = xor(ciphertext[0:2], kpt3)
    key4 = xor(ciphertext[2:4], kpt4)

    if key1 == key2 and key1bis == key2bis:
        print(f"[+] Clé de taille 1 trouvée: {key1.hex()}")
        print(f"[+] Ciphertext: {ciphertext.hex()}")
        flag = xor(ciphertext, key1)
        print(f"[+] Flag: {flag}")
        conn.close()
        break
        
    if key3 == key4:
        print(f"[+] Clé de taille 2 trouvée: {key1.hex()}")
        print(f"[+] Ciphertext: {ciphertext.hex()}")
        flag = xor(ciphertext, key3)
        print(f"[+] Flag: {flag}")
        conn.close()
        break
    
    conn.close()
```

Flag: `brck{SiMPl1c1Ty_1s_K3Y_But_N0t_th3_4nSW3r}`