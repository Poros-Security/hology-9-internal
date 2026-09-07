import struct, argparse, subprocess
from pathlib import Path

def build_flag():
    local_238 = 0x6c5f6c6d53584443
    uStack_230 = 0x6347
    uStack_22e = 0x704434726b33
    uStack_228 = 0x3363
    uStack_226 = 0x7d216f3021735373
    region = struct.pack('<Q', local_238) + struct.pack('<H', uStack_230) + uStack_22e.to_bytes(6, 'little') + struct.pack('<H', uStack_228) + struct.pack('<Q', uStack_226)
    local_258 = "OE{1P3f4_hcE_n_4kR55!!_!!"
    s2 = ['\x00'] * 0x34
    s2[0] = 'C'
    seq = region[1:26]
    for i in range(25):
        s2[2*i + 1] = local_258[i]
        s2[2*(i+1)] = chr(seq[i])
    return ''.join(s2).rstrip('\x00')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", "-b", type=Path, help="Path to binary to feed flag to")
    args = parser.parse_args()
    flag = build_flag()
    print(flag)
    if args.binary:
        if not args.binary.exists():
            print("Binary not found:", args.binary)
            return
        res = subprocess.run([str(args.binary)], input=(flag+"\n").encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(res.stdout.decode(errors='replace'))
        print(res.stderr.decode(errors='replace'))

if __name__ == "__main__":
    main()
