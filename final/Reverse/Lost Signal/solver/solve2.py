from cryptography.hazmat.primitives.ciphers.aead import AESGCM

key = bytes.fromhex("78e6d4199a0315bca744e3cf097abd21""e91f30ae026e80647658f96c70c15943")
iv = bytes.fromhex("9e6c4a2871b503d8fa2049c6")
tag = bytes.fromhex("25dff2f928b2d464ac2cd1432ea0000a")
ciphertext = bytes.fromhex("446fbce75b7f3462520e8f4399abf9a0ced1cee36aeb9a8ae608504471d136b8e50f7b46175d0bebac27795d4619ef301e325c730b3b9692338cf16dcb96585906bb6438774a4c32e5106136d349")
flag = AESGCM(key).decrypt(iv, ciphertext + tag, None)
print(flag.decode("utf-8"))