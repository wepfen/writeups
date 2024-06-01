> Difficulty : easy

> [Source files](https://github.com/GCC-ENSIBS/GCC-CTF-2024/tree/main/Crypto/GCC_News)

> We've launched a brand new website with lots of articles about CTF world. Can you access it as a subscriber? 

# Introduction

We need to connect ourself as an admin abusing of a weak cryptographic signing method to access to the news.

# Recon 

## Interacting with the website

Accessing to the webpage at its address, we can either login or see the news.

But see the news need us to be logged as admin.

When creating an account and trying to access news page, the url look like this :

`http://worker02.gcc-ctf.com:12087/news?token=51816479678544860789205817956792347222422223739416909533792838824330799892508088600548749347686978414433102103745516643115716031985693240243091851305710126012438456120411885440990451062207733612019150266443358710746141779660513712502912356256730590171496329015143780590064512898839213592087008040314904536688517272644527957355579296550263702755869863019492282564083007158478207437390306619837226534557048260824678363108194422787738684127780383714906987061676046665853308427857868198981215396222656764654866977510612110433711379600274374398826032658632188971438616021846678185052961795893909723564297305415934241385892668460580937&message=eyd0ZXN0MSc6IFtGYWxzZV19`

Where the parameter `message` is base64 encoded "{'test1': [False]}" and the parameter `token` is the `message` parameter encrypted with rsa

## Reading the code

Here is the source code

```python
from flask import Flask, render_template, request, redirect, url_for, jsonify
import hashlib
import base64
import json
import time
import random
import hashlib
from Crypto.Util.number import bytes_to_long, isPrime
import math

app = Flask(__name__)

def hash_string_sha256(message):
    message_bytes = message.encode('utf-8')
    sha256_hash = hashlib.sha256()
    sha256_hash.update(message_bytes)
    hashed_message = sha256_hash.digest()

    return int.from_bytes(hashed_message, byteorder='big')

def generate_signature(message, private_key):
    n, d = private_key
    hashed_message = hash_string_sha256(message)
    signature = pow(hashed_message, d, n)
    
    return signature

def verify_signature(msg, public_key, signature):
    initial_hash = hash_string_sha256(msg)
    
    n, e = public_key
    
    recoved_hash = pow(int(signature),e,n)
    
    return initial_hash == recoved_hash

@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    # Check if the user exists
    if username not in users:
        return redirect(url_for('login', reason='unknown_user'))

    # Check if the password is correct
    if password != users[username][0]:
        return redirect(url_for('login', reason='incorrect_password'))
    
    public_key, private_key = generate_key(username)
    
    public_key_users[username] = public_key
    
    signature = generate_signature(str({username : [users[username][1]]}), private_key)
    
    return redirect(url_for('news', token=signature, message=base64.b64encode(str({username : [users[username][1]]}).encode()).decode()))

@app.route('/news', methods=['GET'])
def news():
    signature = request.args.get('token')
    message = base64.b64decode(request.args.get('message')).decode()
    
    message = json.loads(message.replace("'", '"').replace("False", "false").replace("True", "true"))
    
    username = list(message.keys())[0]
    subscribe = list(message.values())[0][0]

    if signature:
        is_sign = verify_signature(str(message), public_key_users[username], signature)
        if is_sign:
            return render_template('news.html', username=username, subscribe=subscribe)

    return redirect(url_for('login', reason='unauthorized'))

@app.route('/login', methods=['GET'])
def show_login():
    # Extract the reason from the query parameters
    reason = request.args.get('reason')

    # Display a pop-up message based on the reason
    if reason == 'unknown_user':
        pop_up_message = "Unknown user. Please check your credentials."
    elif reason == 'incorrect_password':
        pop_up_message = "Incorrect password. Please try again."
    elif reason == 'unauthorized':
        pop_up_message = "Unauthorized access. Please log in."
    else:
        pop_up_message = None

    return render_template('login.html', pop_up_message=pop_up_message)

@app.route('/create_user', methods=['POST'])
def create_user():
    new_username = request.form.get('new_username')
    new_password = request.form.get('new_password')

    # Check if the username already exists
    if new_username in users:
        return redirect(url_for('login', reason='username_exists'))

    # Add the new user to the dictionary
    users[new_username] = [new_password, False]

    # Display a pop-up message
    pop_up_message = "Thanks for registering! The admin will soon activate your profile if you have subscribed."

    return render_template('login.html', pop_up_message=pop_up_message)

def generate_key(username):
    
	length = lambda x : len(bin(x)[2:])

	s = bytes_to_long(username.encode())

	random.seed(s)

	e = 0x1001
	phi = 0
    
	while math.gcd(phi,e) != 1:
		n = 1
		factors = []

		while length(n) < 2048:
			temp_n = random.getrandbits(48)
			if isPrime(temp_n):
				n *= temp_n
				factors.append(temp_n)
		phi = 1
		for f in factors:
			phi *= (f - 1)

	d = pow(e, -1, phi)

	return (n,e), (n,d)

# A simple dictionary to store user credentials and subscription status
users = {
    'GCC': ['securePassword', False]
}
public_key_users = {}

if __name__ == '__main__':
    app.run(debug=False)
```

There is a kind of handmade database to manage users.

The DB got the users, its password, a boolean (True or False) for describing the admin role and the public key of the users.

```python
users = {
    'GCC': ['securePassword', False]
}
public_key_users = {}
```

When creating an user, it is appended to the dict of users :

`users[new_username] = [new_password, False]`

So when creating an "test1" account with "password" as password :

users["test1"][0] = "password"
users["test1"][1] = False

And also filling the public key database:

public_key_users[test] = `its public key` 

The public and private keys are generated with the random module and a seed based on the username. So knowing the username we can recover the public key and ce private key.

We can just reuse the challenge `generate_key` function for that :

```python
def generate_key(username):
    
	length = lambda x : len(bin(x)[2:])

	s = bytes_to_long(username.encode())

	random.seed(s)

	e = 0x1001
	phi = 0
    
	while math.gcd(phi,e) != 1:
		n = 1
		factors = []

		while length(n) < 2048:
			temp_n = random.getrandbits(48)
			if isPrime(temp_n):
				n *= temp_n
				factors.append(temp_n)
		phi = 1
		for f in factors:
			phi *= (f - 1)

	d = pow(e, -1, phi)

	return (n,e), (n,d)
```

# Solving

Now we know how to recover the private key, the steps for solving are : 

- Create an user
- Use the function `generate_key` to get it's private_key and sign the message : {'test1': [True]} which will give us our token.
- Send a GET request with our forged `token` and `message` 

So for test_1 using generate_key:

```
n = 1457342553157259295407930365261800696748888551794075108779100697531249469132443259759166251334393209534527011340120848417513504763172687425603817169965420203182841446416766927653960650018998669899183487322211178874589822726651093254803792218788609932755617725086287444735520634631250205847736080158111696592654206975607049821230615196941817479903763249457613376371498407355381921851845673217419213581082634290438881135049162320418983797388015232666055696476182329585445835040160266557584246137158655921759590380096558137315519737417711810732976599747165793134280706192438024871206616099076425065259626152010714200822870951819946361

e = 4097

d = 1169929132860778172266790416717795055395425023673769128941398634078612313645586470723460559979322746878492767894986894386607392692140809768119253135545569481619614863351561130269497874373374376730775005845964346721784822629714480091633306912534377109787422319793085109077376760278513449726222323801791791327104545390490456210290681860991997191841252970404345272643125273777571879120765801234951744562986758112686603976623970900646525392530237245486976063443733613254268981773171814398056537380882163353704864394235638123739162367944267985527667019876092910225809715528375163004211021207853239200740123762076468891204439491139858433
```

I can now sign the message and get my token :

```
1328296459116198513481005775994265654367244256157496762561215663749001313544888752691095431811838915662861275916069253599131094326519037807982403437366383963609593961610229519349629126583667198784483067627762487710405124208069398517977162311635739503788545076940068444011356528681958458727410341989686589824878872706145702838453900839690220411045955898590237403687023436729802836403464839928576644511341708090007448358389413162908097505464282026490604831559303689920713332959415629965026776263798033479321497305831022519726249152589296200270547520256311793654758651445601039583377445016016582341166189227484558460201850695658065
```

And encode `{'test1': [True]}` in base64: `eyd0ZXN0MSc6IFtUcnVlXX0=`

And send this GET request :

`http://worker02.gcc-ctf.com:13307/news?token=1328296459116198513481005775994265654367244256157496762561215663749001313544888752691095431811838915662861275916069253599131094326519037807982403437366383963609593961610229519349629126583667198784483067627762487710405124208069398517977162311635739503788545076940068444011356528681958458727410341989686589824878872706145702838453900839690220411045955898590237403687023436729802836403464839928576644511341708090007448358389413162908097505464282026490604831559303689920713332959415629965026776263798033479321497305831022519726249152589296200270547520256311793654758651445601039583377445016016582341166189227484558460201850695658065&message=eyd0ZXN0MSc6IFtUcnVlXX0%3D`

> Flag `GCC{f1x3d_533d_d154bl3_r4nd0mn355}`
