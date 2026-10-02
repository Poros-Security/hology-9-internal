"""Recover three masked parameters, then decrypt captured ciphertext."""
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

key_part_1_blob = bytes.fromhex("5fec8130f3f84abd5bc8152321dd0223")
key_part_2_blob = bytes.fromhex("6298791a9e1a044ae1d4ee6de6a55de4")
iv_blob = bytes.fromhex("c4aa7f60912989328f0da2b3")
tag_blob = bytes.fromhex("097d9005402ef0fa0229a661d8e116fa")
ct = bytes.fromhex("194d089b70f96522c805dfb2ae44b7917c54b1525340ee80af3e0b5e19364013a6bc797315941d293617bbb49de6be4feb2a59d5aee6c871a2901554891a2c371aba67674f664002b7a95976d5a6")

key = bytes(c ^ 0x6d for c in key_part_1_blob + key_part_2_blob)
iv = bytes(c ^ 0x31 for c in iv_blob)
tag = bytes(c ^ 167 for c in tag_blob)

print(AESGCM(key).decrypt(iv, ct + tag, None).decode())
