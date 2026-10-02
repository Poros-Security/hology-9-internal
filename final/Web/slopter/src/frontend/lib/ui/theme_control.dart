import 'package:flutter/material.dart';

import '../store.dart';
import 'kit.dart';

const _storeKey = 'slopter-theme';

ThemeMode _read() => switch (storeGet(_storeKey)) {
  'light' => ThemeMode.light,
  'dark' => ThemeMode.dark,
  _ => ThemeMode.system,
};

final themeMode = ValueNotifier<ThemeMode>(_read());

void setThemeMode(ThemeMode mode) {
  themeMode.value = mode;
  storeSet(_storeKey, mode.name);
}

class ThemeSeg extends StatelessWidget {
  const ThemeSeg({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder(
      valueListenable: themeMode,
      builder: (context, mode, _) => Seg<ThemeMode>(
        value: mode,
        onChanged: setThemeMode,
        items: const [
          SegItem(ThemeMode.light, icon: 'sun', tip: 'Light'),
          SegItem(ThemeMode.system, icon: 'monitor', tip: 'System'),
          SegItem(ThemeMode.dark, icon: 'moon', tip: 'Dark'),
        ],
      ),
    );
  }
}
