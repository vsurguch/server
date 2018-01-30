

from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import AES, PKCS1_OAEP
# import utils.message as msg

# secret_code = "Unguessable"
# key = RSA.generate(1024)
# public = key.publickey()
# print(public.exportKey())
# cipher_rsa = PKCS1_OAEP.new(public)
# print(cipher_rsa)
# cipher_rsa_private = PKCS1_OAEP.new(key)
# enc_data = cipher_rsa.encrypt(b'My data')
# decrypted = cipher_rsa_private.decrypt(enc_data)
# print(decrypted)

#server
def generate_key_public_key():
    key = RSA.generate(1024)
    public = key.publickey()
    return key, public

def generate_cipher_rsa_private(key):
    return PKCS1_OAEP.new(key)

#client
def generate_cipher_rsa(public_key):
    public_key = RSA.import_key(public_key)
    return PKCS1_OAEP.new(public_key)

def generate_session_key(cipher_rsa, session_key):
    return cipher_rsa.encrypt(session_key)

#both
def padding_text(text):
    pad_len = (16 - len(text) % 16) % 16
    return text + b' ' * pad_len

def encrypt(data_to_encrypt, key):
    padded_data = padding_text(data_to_encrypt)
    pad_len = len(padded_data) - len(data_to_encrypt)
    bpad = pad_len.to_bytes(4, 'big')
    cipher = AES.new(key, AES.MODE_CBC)
    ciphtertext = cipher.iv + bpad + cipher.encrypt(padded_data)
    return ciphtertext

def decrypt(ciphertext, key):
    cipher = AES.new(key, AES.MODE_CBC, iv=ciphertext[:16])
    bpad = ciphertext[16:20]
    pad = int.from_bytes(bpad, 'big')
    msg = cipher.decrypt(ciphertext[20:])
    # msg = msg[0:-pad]
    return msg

def encrypt_file(filename, key):
    with open(filename, 'rb') as f:
        data = f.read()
        if data != b'':
            return encrypt(data, key)
    return None

def decrypt_file(ciphertext, key, filename):
    data = decrypt(ciphertext, key)
    with open(filename, 'wb') as f:
        f.write(data)

# def encrypt(plaintext, key):
#     cipher = AES.new(key, AES.MODE_CBC)
#     ciphtertext = cipher.iv + cipher.encrypt(plaintext)
#     return ciphtertext
#
# def decrypt(ciphertext, key):
#     cipher = AES.new(key, AES.MODE_CBC, iv=ciphertext[:16])
#     msg = cipher.decrypt(ciphertext[16:])
#     return msg

# def decrypt(ciphertext, key):
#     cipher = AES.new(key, AES.MODE_CBC, iv=ciphertext[:16])
#     bpad = ciphertext[16:20]
#     pad = int.from_bytes(bpad, 'big')
#     msg = cipher.decrypt(ciphertext[20:])
#     return msg
#
# def encrypt_file(filename, key):
#     with open(filename, 'rb') as f:
#         data = f.read()
#         if data != b'':
#             return encrypt(data, key)
#     return None
#
# def decrypt_file(ciphertext, key, filename):
#     data = decrypt(ciphertext, key)
#     with open(filename, 'wb') as f:
#         f.write(data)
#     return data

#
# #server:
# key, public = generate_key_public_key()
# message = msg.Message('public_key')
# decoded_public = public.exportKey(format='PEM').decode('utf-8')
# message.add_key_value('key', decoded_public)
# bm = message.get_binary_json('utf-8')
#
# cipher_rsa_private = PKCS1_OAEP.new(key)
#
#
#
# #client:
# recieved_message = msg.Message()
# recieved_message.make_from_binary_json(bm, 'utf-8')
# public_key_str = recieved_message['key']
# cipher_rsa = generate_cipher_rsa(public_key_str)
#
# #generate session key
# session_key = b'Sixteen byte key'
# session_key_encrypted = generate_session_key(session_key)
#
# somemessage = msg.MessageAuthenticate('Vladimir', 'password')
# bm = somemessage.get_binary_json('utf-8')
# encrypted_bm = encrypt(padding_text(bm), session_key)
#
# #server
# session_key_recieved = cipher_rsa_private.decrypt(session_key_encrypted)
# print(session_key_recieved)
# bm2 = decrypt(encrypted_bm, session_key_recieved)
# m2 = msg.Message()
# m2.make_from_binary_json(bm2, 'utf-8')
# print(m2)