import hashlib
import time
#TODO Comments

# Start time to keep track of how long things take
start_time_cipher = time.monotonic()

# Create a list of all English words from an outside library
word_list = []
with open('words_alpha.txt') as file:
    word_list = file.read().split()

# Create a empty dict for future use
word_by_length = {}

# Read the encrypted text
encrypted = ''
with open('encrypted.txt') as file:
    encrypted = file.read()
# Keep track of where punctuation should be
punctuation_dict = {}
for i in range(len(encrypted)):
    if encrypted[i] in ['.', ',', '!', '?', ';']:
        punctuation_dict[i] = encrypted[i]
# Strip the punctuation and then split at spaces
encrypted = encrypted.replace('.', '')
encrypted = encrypted.replace(',', '')
encrypted = encrypted.replace('!', '')
encrypted = encrypted.replace('?', '')
encrypted = encrypted.replace(';', '')
encrypted_text = encrypted.split()

# A recursive function which checks that the current map could end up with the current target_word, filling in missing character mappings. It then checks for the next incomplete word, where it checks every option for that word, and so on
def decrypt(encrypted_text:list, word_index:int, letter_map:dict, target_word:str, word_list:list, word_by_length:dict):
    # Find the length of the encrypted word
    word = encrypted_text[word_index]
    word_length = len(word)

    # Iterate through the words to check against the map
    for i in range(word_length):
        if word[i] in letter_map and letter_map[word[i]] != target_word[i]:
            return False, letter_map
        if not word[i] in letter_map and target_word[i] in letter_map.values():
            return False, letter_map
        # Fill in missing letter in the map
        letter_map[word[i]] = target_word[i]
    
    # Start to work on next word
    word_index += 1

    # Check that the next words are not already completed or the whole string has been completed
    b = True
    while b:
        if word_index == len(encrypted_text):
            return True, letter_map
        b = all(char in letter_map for char in encrypted_text[word_index])
        if b:
            b = all(letter_map[char] for char in encrypted_text[word_index])
        if b:
            new_word = ''.join(letter_map[char] for char in encrypted_text[word_index])
            if new_word in word_list:
                word_index += 1
            else:
                b = False

    # Print to console to keep track
    print("Word Index: " + str(word_index) + " Time: " + str(time.monotonic() - start_time_cipher))
    print(' '.join(''.join(letter_map[char] for char in word) for word in encrypted_text[:word_index]))

    # Calculate next word length
    word = encrypted_text[word_index]
    word_length = len(word)
    # Register the list of words with word_length
    if not word_length in word_by_length:
        word_by_length[word_length] = [word for word in word_list if (len(word) == word_length)]
    # Iterate through all options for the next word
    for new_target_word in word_by_length[word_length]:
            new_target_word = new_target_word.lower()
            letter_map_copy = letter_map.copy()
            correct, result = decrypt(encrypted_text, word_index, letter_map_copy, new_target_word, word_list, word_by_length)
            if correct: # If it reached the end of the encrypted string, it is the correct map
                return correct, result

    return False, letter_map

# Start running recursive algorithm using the same as the recursive part of the algorithm
word = encrypted_text[0]
word_length = len(word)
# Register the list of words with word_length
if not word_length in word_by_length:
    word_by_length[word_length] = [word for word in word_list if (len(word) == word_length)]
# Initialize the map
letter_map = {}
# Checking that it actually worked
finished = False
# Iterate through possible words
for target_word in word_by_length[word_length]:
    target_word = target_word.lower()
    letter_map_copy = letter_map.copy()
    correct, result = decrypt(encrypted_text, 0, letter_map_copy, target_word, word_list, word_by_length)
    # Exit from the loop if correct map is found
    if correct:
        letter_map = result
        finished = True
        break
# Checking that it actually worked
if not finished:
    print("Got to the end without finishing")

# Printing results
print(letter_map)
decrypted = ' '.join(''.join(letter_map[char] for char in word) for word in encrypted_text)
for punct in punctuation_dict:
    decrypted = decrypted[:punct] + punctuation_dict[punct] + decrypted[punct:]
print(decrypted)
print("Time: " + str(time.monotonic() - start_time_cipher))

# Inverts map to find password post-substitution
solver = {value: key for key, value in letter_map.items()}

# Keep track of how long it takes
start_time_pass = time.monotonic()

# Hash function for 512 bits
hash_function = hashlib.sha3_512

# Import the list of common passwords
password_dictionary = []
with open('dictionary.txt') as file:
    content = file.read()
    password_dictionary = content.split()

# This is the hash to crack
h_pass = "bb69ac60ca2cdff95b8a64d48006a0fa7c277af39fdedb70f18e51bfce2172020547146dc57c180d82551816f6c996170fcaa70f1e62f914097a50debf0f559e"
print(h_pass)

# Iterate through all passwords in the password list
for password in password_dictionary:
        if all(char in solver for char in password):
            encrypted_password = ''.join(solver[char] for char in password)
            hasher = hash_function(encrypted_password.encode("utf-8"))
            if (h_pass == hasher.hexdigest()):
                print_output = "\nHashed Password: " + h_pass + "\nPassword: " + password + "\n Time: " + str(time.monotonic() - start_time_pass)
                print(print_output)
                break
print('Done')