from pwn import *
p = remote('localhost', 6113)
print(p.recvuntil(b'Answer: ').decode())
answers = [
    '$RQED0TU.enc',
    'AES-CBC',
    '11-9-2026_05:47:42',
    r'C:\Users\MJ\Documents\letters',
    '.txt',
    'MachineGuid',
    '75f5f2a5-e21d-4ff0-affe-a5ee925aad80',
    'peter_parker',
    'C:\\Users\\MJ\\Documents\\letters\\first_letter.txt',
    'IALWAYSLOVEU'
]

for answer in answers:
    p.sendline(answer.encode())
    response = p.recv().decode()
    print(response)
print(p.recvall().decode())
