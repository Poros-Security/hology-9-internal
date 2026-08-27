1. Run volatility3 `windows.pslist` to enumerate processes and note PIDs for
   `loyalist.exe`, `sovereign.exe` (`svchost_helper.exe`), and `envoy.exe`.
2. Run `windows.malfind` or `windows.vadinfo` on `loyalist.exe` to locate the
   `PAGE_EXECUTE_READWRITE` region holding flag part 1.
3. Run `windows.malfind` or `heap scan` on `sovereign.exe` to locate flag part 2
   in heap memory.
4. Both parts are XOR-encoded with a 2-byte rolling key derived from the
   `Sovereign PID` and `Loyalist PID`.
5. Decode both parts and concatenate to recover the full flag.
