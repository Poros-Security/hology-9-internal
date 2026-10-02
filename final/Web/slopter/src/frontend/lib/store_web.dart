import 'dart:js_interop';

extension type _Storage(JSObject _) implements JSObject {
  external String? getItem(String key);
  external void setItem(String key, String value);
  external void removeItem(String key);
}

@JS('localStorage')
external _Storage get _localStorage;

String? storeGet(String key) {
  try {
    return _localStorage.getItem(key);
  } catch (_) {
    return null;
  }
}

void storeSet(String key, String value) {
  try {
    _localStorage.setItem(key, value);
  } catch (_) {}
}

void storeRemove(String key) {
  try {
    _localStorage.removeItem(key);
  } catch (_) {}
}
