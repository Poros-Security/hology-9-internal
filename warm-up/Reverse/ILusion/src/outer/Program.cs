using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;

namespace ILusion
{
    internal static class Program
    {
        private const string CoreFile = "core.bin";
        private const string CoreType = "Core.Machine";
        private const string CoreEntry = "Verify";

        /// <summary>
        /// Legacy v0 licence table. Kept for customers who never migrated;
        /// enable with ILUSION_LEGACY=1.
        /// </summary>
        private static readonly byte[] LegacyTable =
        {
            0x0A, 0x0B, 0x00, 0x01, 0x0A, 0x00, 0x70, 0x74, 0x39, 0x2C, 0x72, 0x36,
            0x1D, 0x33, 0x37, 0x73, 0x36, 0x71, 0x1D, 0x36, 0x2A, 0x76, 0x36, 0x1D,
            0x71, 0x76, 0x31, 0x3B, 0x3F,
        };

        private static void Main()
        {
            Console.WriteLine("ILusion licensing shim v1.0");
            Console.WriteLine("[*] mounting core module...");

            Assembly core;
            try
            {
                string path = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, CoreFile);
                core = Gate(File.ReadAllBytes(path), DeriveKey());
            }
            catch
            {
                Console.WriteLine("[-] core module integrity failure (0x8007000B)");
                return;
            }

            Console.Write("[*] enter license: ");
            string input = Console.ReadLine();
            if (input == null)
            {
                input = string.Empty;
            }

            bool ok;
            if (Environment.GetEnvironmentVariable("ILUSION_LEGACY") == "1")
            {
                ok = LegacyCheck(input);
            }
            else
            {
                try
                {
                    MethodInfo verify = core.GetType(CoreType, true).GetMethod(CoreEntry);
                    ok = (bool)verify.Invoke(null, new object[] { input });
                }
                catch
                {
                    Console.WriteLine("[-] core module integrity failure (0x8007000B)");
                    return;
                }
            }

            Console.WriteLine(ok ? "[+] Accepted." : "[-] Rejected.");
        }

        /// <summary>
        /// v0 check. Straightforward and completely readable - which is the
        /// point.
        /// </summary>
        private static bool LegacyCheck(string key)
        {
            if (key == null || key.Length != LegacyTable.Length)
            {
                return false;
            }

            for (int i = 0; i < key.Length; i++)
            {
                if ((byte)(key[i] ^ 0x42) != LegacyTable[i])
                {
                    return false;
                }
            }

            return true;
        }

        /// <summary>
        /// The key is the loader's own compiled body. Patch a single byte of
        /// <see cref="Gate"/> and the core module stops decrypting.
        /// </summary>
        private static byte[] DeriveKey()
        {
            MethodInfo m = typeof(Program).GetMethod("Gate",
                               BindingFlags.NonPublic | BindingFlags.Static);
            byte[] il = m.GetMethodBody().GetILAsByteArray();
            byte[] salt = Encoding.ASCII.GetBytes("ILusion/v1");
            byte p = Poison();
            using (var sha = SHA256.Create())
            {
                return sha.ComputeHash(il.Concat(salt).Concat(new[] { p }).ToArray());
            }
        }

        private static byte Poison()
        {
            bool d = Debugger.IsAttached || Debugger.IsLogging();
            return (byte)(d ? 0x5A : 0x00);
        }

        // No try/catch, no using, no locals worth a fat header: this body is
        // key material, so it stays as small and as stable as possible.
        private static Assembly Gate(byte[] blob, byte[] key)
        {
            Aes aes = Aes.Create();
            aes.KeySize = 256;
            aes.Mode = CipherMode.CBC;
            aes.Padding = PaddingMode.PKCS7;
            aes.Key = key;
            byte[] iv = new byte[16];
            Buffer.BlockCopy(blob, 0, iv, 0, 16);
            aes.IV = iv;
            ICryptoTransform dec = aes.CreateDecryptor();
            byte[] plain = dec.TransformFinalBlock(blob, 16, blob.Length - 16);
            return Assembly.Load(plain);
        }
    }
}
