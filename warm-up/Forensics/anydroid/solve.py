from pwn import *
p = remote('challenge-c34-tadmin.chall.ctf.hackitbraw.site', 32826)
print(p.recvuntil(b'Answer: ').decode())
answers = [
    'Ķαѕρегśķу.apk',
    'f9e0682f3a0f5e6b7cc2d76ef1b196c4c3d2c43584b908743cd4bbeb15e94184',
    'Banker',
    'app.rxlalqzo.f2dmarq38gsu',
    'http://193.233.112.224:1136',
    '/mypx',
    '54f6b56110d72277851a809009d0a0a0',
    '2028',
    '801b7921c57e2976',
    'telegram',
    'update.apk',
    '25fa6eef5dfc103a5aa1bf8c5f462e0bfec4a209685175e43838cdc6ba59f2b6',
    'app.zqalusxwx.fv4iujmq4u.s8f9mw147lyt7f',
    '1111111111111111111111111111111111111111111111111111111111111111:22222222222222222222222222222222'
]

for answer in answers:
    p.sendline(answer.encode())
    response = p.recv().decode()
    print(response)
print(p.recvall().decode())
