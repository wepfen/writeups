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