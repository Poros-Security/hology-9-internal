using System;

namespace Core
{
    /// <summary>
    /// Stage 2. The licence check is not C# - it is a byte program in
    /// <see cref="Tables.CODE"/> interpreted by this stack machine.
    /// </summary>
    public static class Machine
    {
        private const byte OP_PUSH_IMM = 0x11;
        private const byte OP_PUSH_IN = 0x12;
        private const byte OP_PUSH_ST = 0x13;
        private const byte OP_XOR = 0x21;
        private const byte OP_ADD = 0x22;
        private const byte OP_ROL = 0x23;
        private const byte OP_SBOX = 0x24;
        private const byte OP_STORE_ST = 0x31;
        private const byte OP_CMP = 0x32;
        private const byte OP_LEN = 0x41;
        private const byte OP_HALT = 0xFF;

        public static bool Verify(string input)
        {
            if (input == null)
            {
                return false;
            }

            byte[] code = Tables.CODE;
            byte[] stack = new byte[64];
            int sp = 0;
            int pc = 0;
            byte state = Tables.STATE0;
            int fail = 0;
            bool running = true;

            while (running && pc < code.Length)
            {
                byte op = code[pc++];
                byte a, b;

                switch (op)
                {
                    case OP_PUSH_IMM:
                        stack[sp++] = code[pc++];
                        break;

                    case OP_PUSH_IN:
                        stack[sp++] = (byte)input[code[pc++]];
                        break;

                    case OP_PUSH_ST:
                        stack[sp++] = state;
                        break;

                    case OP_XOR:
                        b = stack[--sp];
                        a = stack[--sp];
                        stack[sp++] = (byte)(a ^ b);
                        break;

                    case OP_ADD:
                        b = stack[--sp];
                        a = stack[--sp];
                        stack[sp++] = (byte)((a + b) & 0xFF);
                        break;

                    case OP_ROL:
                        {
                            int n = code[pc++] & 7;
                            b = stack[--sp];
                            stack[sp++] = (byte)(((b << n) | (b >> (8 - n))) & 0xFF);
                        }
                        break;

                    case OP_SBOX:
                        b = stack[--sp];
                        stack[sp++] = Tables.SBOX[b];
                        break;

                    case OP_STORE_ST:
                        state = stack[--sp];
                        break;

                    case OP_CMP:
                        // No early exit: every index is compared, and the
                        // verdict is only read after HALT. A wrong byte costs
                        // exactly as much as a right one.
                        b = stack[--sp];
                        if (b != Tables.TARGET[code[pc++]])
                        {
                            fail = 1;
                        }
                        break;

                    case OP_LEN:
                        if (input.Length != code[pc++])
                        {
                            fail = 1;
                            running = false;
                        }
                        break;

                    case OP_HALT:
                        running = false;
                        break;

                    default:
                        fail = 1;
                        running = false;
                        break;
                }
            }

            return fail == 0;
        }
    }
}
