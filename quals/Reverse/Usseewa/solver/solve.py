#!/usr/bin/env python3
import sys,struct,math
from pathlib import Path

P=Path(sys.argv[1] if len(sys.argv)>1 else "main.scn").read_bytes()
U=lambda o:struct.unpack_from("<I",P,o)[0]

p=P.find(b"names\0")+6
t,n=struct.unpack_from("<II",P,p); p+=8
assert t==34
N=[]
for _ in range(n):
    l=U(p); p+=4
    N.append(P[p:p+l].rstrip(b"\0").decode()); p+=l

p=P.find(b"variants\0")+9
t,n=struct.unpack_from("<II",P,p); p+=8
assert t==30

def u(f="<I"):
    global p
    v=struct.unpack_from(f,P,p)[0]; p+=4
    return v

def s():
    global p
    l=u(); v=P[p:p+l].rstrip(b"\0").decode(); p+=l
    return v

def v():
    t=u()
    if t==1:return None
    if t==2:return bool(u())
    if t==3:return u("<i")
    if t==4:return u("<f")
    if t==5:return s()
    if t==10:return u("<f"),u("<f")
    if t==18:return tuple(u("<f") for _ in range(6))
    if t==24:
        x=u()
        return ("obj",x,u()) if x in (2,3) else ("obj",0)
    raise ValueError(t)

V=[v() for _ in range(n)]

q=P.find(b"nodes\0")+6
t,l=struct.unpack_from("<II",P,q); q+=8
assert t==32
D=list(struct.unpack_from("<"+"i"*l,P,q))

i=0; nodes={}
while i<len(D):
    _,_,_,ni,_,c=D[i:i+6]; i+=6
    name=N[ni&((1<<18)-1)]
    x={}
    for _ in range(c):
        a,b=D[i:i+2]; i+=2
        x[N[a&0x7fffffff]]=V[b]
    g=D[i]; i+=1+g
    nodes[name]=x

rnd=lambda x:math.floor(x+.5) if x>=0 else math.ceil(x-.5)
rol=lambda x,r:((x<<r)|(x>>(8-r)))&255
ror=lambda x,r:((x>>r)|(x<<(8-r)))&255

cur="Memory_e59e6ba0"
flag=[0]*60
prev=66

for r in range(60):
    n=nodes[cur]
    sh,tk,tg=map(int,(n["metadata/shard"],n["metadata/ticket"],n["metadata/target"]))
    x,y=n["position"]
    k=(rnd(x)^rnd(y)^rnd(math.degrees(float(n["rotation"])))^sh)&255
    slot=tk^sh^0x5a
    rot=r%7+1

    a=(29*r+13*k+113)&255
    z=((a^tg)-(17*r+prev+45))&255
    flag[slot]=ror(z,rot)^k

    assert (a^(17*r+prev+45+rol(flag[slot]^k,rot)))&255==tg
    prev=tg
    cur=n["metadata/next"]

assert cur=="END"
print(bytes(flag).decode())
