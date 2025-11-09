import hashlib
import time
import sys

start_time = time.monotonic()

# sys.argv[1] is the hashed password
# sys.argv[2] should have something if a caeser cipher was used, otherwise nothing

# Confirm that there are the right number of arguments
if(len(sys.argv) < 2):
    raise EnvironmentError("Missing Password")

h_pass = sys.argv[1]

# Converts a string into l33t speak, but based on the bits of a number as a mask
def l33t(string:str, mask:int):
    if (mask & 1):
        string = string.replace('a', '4')
    if (mask & 2):
        string = string.replace('b', '8')
    if (mask & 4):
        string = string.replace('e', '3')
    if (mask & 8):
        string = string.replace('g', '6')
    if (mask & 16):
        string = string.replace('i', '!')
    if (mask & 32):
        string = string.replace('l', '1')
    if (mask & 64):
        string = string.replace('o', '0')
    if (mask & 128):
        string = string.replace('s', '5')
    if (mask & 256):
        string = string.replace('t', '7')
    if (mask & 512):
        string = string.replace('z', '2')
    return string

# Performs a caeser cipher on the input, moving it offset number of times
def ceaser(string:str, offset:int):
    output = ''
    for char in string:
        if 'a' <= char <= 'z':
            char = chr((ord(char) - ord('a') + offset) % 26 + ord('a'))
        elif 'A' <= char <= 'Z':
            char = chr((ord(char) - ord('A') + offset) % 26 + ord('A'))
        output += char
    return output
    

# Import the list of common passwords
password_dictionary = []
with open('dictionary.txt') as file:
    content = file.read()
    password_dictionary = content.split()

# Determine the right hash
hashed_length = len(h_pass)
hash_function = None
match hashed_length:
    case 32:
        hash_function = hashlib.md5
    case 40:
        hash_function = hashlib.sha1
    case 56:
        # There are two common ones which give this length, so both must be checked.
        hash_function = hashlib.sha3_224
        #hash_function = hashlib.sha224
    case 64:
        hash_function = hashlib.sha256
    case 128:
        hash_function = hashlib.sha512
    case default: 
        raise EnvironmentError("Incorrect Length of Hashed Password")

if (len(sys.argv) < 3): # nothing for using ceaser cipher
    # This is if there is no modification to the password in the dictionary
    for password in password_dictionary:
        hasher = hash_function(password.encode("utf-8"))
        if (h_pass == hasher.hexdigest()):
            print_output = "\nHashed Password: " + h_pass + "\nPassword: " + password + "\n Time: " + str(time.monotonic() - start_time)
            print(print_output)
            sys.exit(0)
    print("Not directly in dictionary")

    # Check for L33T speak, the password dictionary looks to be in common order, so better to go through common passwords first
    for password in password_dictionary:
        for mask in range(1024):
            l33t_password = l33t(password, mask)
            hasher = hash_function(l33t_password.encode("utf-8"))
            if (h_pass == hasher.hexdigest()):
                print_output = "Hashed Password: " + h_pass + "\nPassword: " + password + "\n Time: " + str(time.monotonic() - start_time) + "\n L33T Mask:" + str(mask)
                print(print_output)
                sys.exit(0)
    print("Not with L33T")

    # This checks against all five digit salts, the password dictionary looks to be in common order, so better to go through common passwords first
    for password in password_dictionary:
        for salt in range(100000):
            salt = str(salt).zfill(5)
            salted_password = password + salt
            hasher = hash_function(salted_password.encode("utf-8"))
            if (h_pass == hasher.hexdigest()):
                print_output = "Hashed Password: " + h_pass + "\nPassword: " + password + "\n Time: " + str(time.monotonic() - start_time) + "\nSalt: " + salt
                print(print_output)
                sys.exit(0)
    print("Not with salt")
    # This is time to fail
    print("Time: " + str(time.monotonic() - start_time))
else:
    # This is if there is no modification to the password in the dictionary
    for password in password_dictionary:
        for offset in range(26):
            caeser_password = ceaser(password, offset)
            hasher = hash_function(caeser_password.encode("utf-8"))
            if (h_pass == hasher.hexdigest()):
                print_output = "Hashed Password: " + h_pass + "\nPassword: " + password + "\n Time: " + str(time.monotonic() - start_time)
                print(print_output)
                sys.exit(0)
    print("Not directly in dictionary")

    
    # Check for L33T speak, the password dictionary looks to be in common order, so better to go through common passwords first
    for password in password_dictionary:
        for offset in range(26):
            caeser_password = ceaser(password, offset)
            for mask in range(1024):
                l33t_password = l33t(caeser_password, mask)
                hasher = hash_function(l33t_password.encode("utf-8"))
                if (h_pass == hasher.hexdigest()):
                    print_output = "Hashed Password: " + h_pass + "\nPassword: " + password + "\n Time: " + str(time.monotonic() - start_time) + "\n L33T Mask:" + str(mask)
                    print(print_output)
                    sys.exit(0)
    print("Not with L33T")

    # This checks against all five digit salts, the password dictionary looks to be in common order, so better to go through common passwords first
    for password in password_dictionary:
        for offset in range(26):
            caeser_password = ceaser(password, offset)
            for salt in range(100000):
                salt = str(salt).zfill(5)
                salted_password = caeser_password + salt
                hasher = hash_function(salted_password.encode("utf-8"))
                if (h_pass == hasher.hexdigest()):
                    print_output = "Hashed Password: " + h_pass + "\nPassword: " + password + "\n Time: " + str(time.monotonic() - start_time) + "\nSalt: " + salt
                    print(print_output)
                    sys.exit(0)
    print("Not with salt")
    # This is time to fail
    print("Time: " + str(time.monotonic() - start_time))

print("Something went wrong, no clue what the password is")
sys.exit(-1)