# Bluehens CTF 2023 - Least significant color


>I can't decide which color is the least significant... red xor green?
>
> -azroberts

So for this challenge we got an image file provided `encoded.png`. <br>
All we have to know is in the title AND in the description. 

Before giving the solution, we need to have in mind two things: Least significant bit (LSB) and the representation of an image.

## Reminder

### Images

An image is basically a 2D list of tuples (R=red, G=green, B=blue) of 3 values.
The tuple define a number from 0 to 255 defining the intensity of each color 

The width of an image define the number of tuples per lines.<br>
The height of an image define the number of lines.

![representation of an image](https://raw.githubusercontent.com/1Tyron140/writeups/main/Bluehens_CTF/2023/misc/least_significant_color/pixel_in_image.png)


### Least Significant Bit 

The least signifcant bit is the last bit of byte. It is used in stego to hide text or else.
So we can get multiple bytes and get edit the LSB of each so if we concatenate the LSB of each we get a message.
 
Here is in image before and after editing the LSB (no difference, i think)

![LSB vs original](https://raw.githubusercontent.com/1Tyron140/writeups/main/Bluehens_CTF/2023/misc/least_significant_color/lsb_orginal_vs_edited.png)


## Solution

As the description tell us, i will xor the red value of a tuple with it's green one and iterate this for 30 character = 30 bytes = 30*8 LSB = 240 pixels = 240 tuples.


### Script

I will use a python script with the PIL module for image processing found after some research.

```
from PIL import Image

flag = Image.open('encoded.png')

lsb = []

b = ""

pixels = list(flag.getdata())

for c,p in enumerate(pixels):

    b+=bin(p[1]^p[0])[-1]
    
    if len(b) == 8:
        lsb.append(int(b, 2))
        b=""
    if c == 240:
        break
        
for char in (lsb):
    print(chr(char), end="")
```

1. XOR red with green and append the least significant bit to b
2. If b is 8 bits, empty it's value in 'lsb' list
3. For each bytes in lsb[], print its ascii value


Output after cleaning : `UDCTF{y0u_R_1mag3_wizZarD}`
