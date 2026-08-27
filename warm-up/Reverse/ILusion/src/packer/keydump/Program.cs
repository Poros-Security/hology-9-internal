using System;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;

namespace KeyDump
{
    /// <summary>
    /// Ground truth for pack.py. Loads the built ILusion.exe through the real
    /// runtime, asks reflection for Gate's IL, and prints
    ///
    ///     &lt;sha256 of the IL&gt; &lt;the derived AES key&gt;
    ///
    /// build.sh diffs this against pack.py and fails the build on mismatch.
    /// If these two ever disagree, pack.py's method-header parsing is wrong
    /// and the shipped core.bin would be undecryptable.
    /// </summary>
    internal static class Program
    {
        private static int Main(string[] args)
        {
            if (args.Length < 1)
            {
                Console.Error.WriteLine("usage: KeyDump.exe <ILusion.exe>");
                return 2;
            }

            Assembly asm = Assembly.LoadFrom(args[0]);
            Type program = asm.GetType("ILusion.Program", true);
            MethodInfo gate = program.GetMethod("Gate",
                                  BindingFlags.NonPublic | BindingFlags.Static);
            if (gate == null)
            {
                Console.Error.WriteLine("Gate not found");
                return 1;
            }

            byte[] il = gate.GetMethodBody().GetILAsByteArray();
            byte[] salt = Encoding.ASCII.GetBytes("ILusion/v1");

            using (var sha = SHA256.Create())
            {
                string ilHash = Hex(sha.ComputeHash(il));

                byte[] material = new byte[il.Length + salt.Length + 1];
                Buffer.BlockCopy(il, 0, material, 0, il.Length);
                Buffer.BlockCopy(salt, 0, material, il.Length, salt.Length);
                material[material.Length - 1] = 0x00;

                Console.WriteLine("{0} {1} {2}", il.Length, ilHash, Hex(sha.ComputeHash(material)));
            }

            return 0;
        }

        private static string Hex(byte[] b)
        {
            var sb = new StringBuilder(b.Length * 2);
            foreach (byte x in b)
            {
                sb.Append(x.ToString("x2"));
            }
            return sb.ToString();
        }
    }
}
