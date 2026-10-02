final _values = <String, String>{};

String? storeGet(String key) => _values[key];

void storeSet(String key, String value) => _values[key] = value;

void storeRemove(String key) => _values.remove(key);
