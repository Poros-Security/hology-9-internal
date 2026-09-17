print("SuiCar Star-Drive Telemetry Console");
print("Runtime modules: SuiArray, SuiTele, SuiDash");

if (typeof SuiArray === "undefined") throw new Error("SuiArray missing");
if (typeof SuiTele === "undefined") throw new Error("SuiTele missing");
if (typeof SuiDash === "undefined") throw new Error("SuiDash missing");

(function (loadUser, userPath) {
  globalThis.read = undefined;
  globalThis.readbuffer = undefined;
  globalThis.writeFile = undefined;
  globalThis.load = undefined;
  globalThis.os = undefined;
  globalThis.d8 = undefined;
  globalThis.Realm = undefined;
  globalThis.Worker = undefined;
  globalThis.quit = undefined;

  if (typeof userPath !== "undefined" && userPath !== "") {
    loadUser(userPath);
  }
})(load, (typeof arguments !== "undefined" && arguments.length > 0)
        ? arguments[0]
        : undefined);

