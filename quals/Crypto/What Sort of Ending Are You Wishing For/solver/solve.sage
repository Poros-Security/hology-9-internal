from sage.all import *
from pwn import *
from subprocess import check_output
from math import isqrt
from time import time
import re, sys

time_start=time()

def flat(B):
    s="[\n"+"\n".join("["+" ".join(map(str,r))+"]" for r in B.rows())+"\n]\n"
    a=list(map(ZZ,re.findall(rb"-?\d+",check_output(["flatter"],input=s.encode()))))
    return Matrix(ZZ,B.nrows(),B.ncols(),a)

def fac(N,z,v0,v):
    S=(1<<(2*z))*v+v0
    D=S*S-4*N
    if D<0 or not ZZ(D).is_square(): return
    r=ZZ(D).sqrt()
    if (S+r)%2: return
    p=(S+r)//2
    return p if 1<p<N and N%p==0 else None

def extract(G,N,z,v0,Y):
    V.<v>=PolynomialRing(QQ)
    T.<t>=PolynomialRing(V)

    def cv(g):
        h=T(0)
        for m,c in g.dict().items():
            a,b=map(int,m); h+=QQ(c)*v^b*t^a
        return h

    def root(f):
        if not f or f.degree()<=0 or f.degree()>64:return
        for r,_ in V(f).squarefree_part().roots(QQ):
            if r.denominator()==1:
                x=ZZ(r)
                if 0<=x<Y:
                    p=fac(N,z,v0,x)
                    if p:return p

    H=[cv(g) for g in G]

    for h in H:
        if h.degree()==0:
            p=root(h[0])
            if p:return p

    for i in range(min(10,len(H))):
        g=None
        for j in range(len(H)):
            if i==j or not H[i].degree() or not H[j].degree():continue
            try:
                r=H[i].resultant(H[j])
                if not r:continue
                r=V(r)
                if r.degree()<=0:continue
                r=r.squarefree_part().monic()

                p=root(r) if r.degree()<=12 else None
                if p:return p

                g=r if g is None else gcd(g,r).monic()
                if g.degree()<=0:break

                if g.degree()<=32:
                    p=root(g)
                    if p:return p
            except:pass

def attack(N,e,z,w):
    M=ZZ(1)<<(2*z)
    v0=(2*w+(N-w^2)*inverse_mod(w,M))%M

    a2=(ZZ(1)<<(4*z))*(N+3*v0+1)
    a1=(ZZ(1)<<(2*z))*(N^2+2*N*v0+3*v0^2-2*N+2*v0+1)
    a0=N^3+N^2*v0+N*v0^2+v0^3-N^2-2*N*v0+v0^2-N+v0+1

    k=inverse_mod(ZZ(1)<<(6*z),e)
    P.<x,y>=PolynomialRing(ZZ)
    R=x*(y^3+(k*a2%e)*y^2+(k*a1%e)*y+k*a0%e)+k

    X=(e*(ZZ(1)<<(94*N.nbits()//100))+N^3-1)//N^3+2
    Y=(3*(ZZ(isqrt(int(N)))+1)+M-1)//M+2

    S=[]
    for k in range(4):
        S += [x^r*y^s*R^k*e^(3-k) for r in range(1,4-k) for s in range(3)]
        S += [y^s*R^k*e^(3-k) for s in range(10)]

    ms=sorted({m for f in S for m in f.dict()},key=tuple)
    sc=[X^int(m[0])*Y^int(m[1]) for m in ms]

    B=Matrix(ZZ,[[ZZ(f.dict().get(m,0))*sc[j] for j,m in enumerate(ms)] for f in S])
    log.info("Reducing 58x58...")
    B=flat(B)

    n2=lambda r:sum(ZZ(a)^2 for a in r)
    rows=sorted(B.rows(),key=n2)
    G=[]

    for row in rows:
        g=P(0)
        for j,m in enumerate(ms):
            if row[j]:
                a,b=map(int,m)
                g+=(row[j]//sc[j])*x^a*y^b
        G.append(g)

    G=[g for r,g in zip(rows,G) if n2(r)*58<e^6]
    log.info(f"HG-good = {len(G)}")
    return extract(G,N,z,v0,Y)

def solve(N,e,z):
    R=list({ZZ(r) for r in Integers(ZZ(1)<<z)(N).sqrt(all=True)})
    R=[r for r in R if r.nbits()==z] or R

    for i,w in enumerate(R):
        log.info(f"w0 {i+1}/{len(R)}")
        p=attack(N,e,z,w)
        if p:return p
    raise Exception("factor not recovered")

io=remote("38.147.122.175", 32852)

io.recvuntil(b"N = "); N=ZZ(io.recvline())
io.recvuntil(b"e = "); e=ZZ(io.recvline())
io.recvuntil(b"z = "); z=int(io.recvline())
io.recvuntil(b"> ")

p=solve(N,e,z)
log.success(f"p = {p}")
io.sendline(str(p).encode())
io.interactive()

print(f"Solved in {time() - time_start:2f} s")
