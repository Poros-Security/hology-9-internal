import 'package:flutter/material.dart';

class Tokens {
  const Tokens({
    required this.canvas,
    required this.surface,
    required this.raised,
    required this.ink,
    required this.muted,
    required this.faint,
    required this.line,
    required this.accent,
    required this.accentSoft,
    required this.onAccent,
    required this.danger,
    required this.dangerSoft,
    required this.warn,
    required this.warnSoft,
    required this.shadow,
  });

  final Color canvas, surface, raised, ink, muted, faint, line;
  final Color accent, accentSoft, onAccent;
  final Color danger, dangerSoft, warn, warnSoft, shadow;

  static const light = Tokens(
    canvas: Color(0xFFF3F4F1),
    surface: Color(0xFFFFFFFF),
    raised: Color(0xFFF7F8F6),
    ink: Color(0xFF16201C),
    muted: Color(0xFF5C6863),
    faint: Color(0xFF8A9490),
    line: Color(0xFFE0E4E0),
    accent: Color(0xFF0B7A5B),
    accentSoft: Color(0xFFE2F2EB),
    onAccent: Color(0xFFFFFFFF),
    danger: Color(0xFFBE342D),
    dangerSoft: Color(0xFFFBEBE9),
    warn: Color(0xFF965C06),
    warnSoft: Color(0xFFFBF2DE),
    shadow: Color(0xFF101814),
  );

  static const dark = Tokens(
    canvas: Color(0xFF0B100E),
    surface: Color(0xFF131A17),
    raised: Color(0xFF1A221F),
    ink: Color(0xFFE6ECE9),
    muted: Color(0xFF96A29D),
    faint: Color(0xFF6A7671),
    line: Color(0xFF28332E),
    accent: Color(0xFF3DCB9A),
    accentSoft: Color(0xFF123227),
    onAccent: Color(0xFF051A13),
    danger: Color(0xFFF0756A),
    dangerSoft: Color(0xFF381614),
    warn: Color(0xFFE8B24E),
    warnSoft: Color(0xFF32250C),
    shadow: Color(0xFF000000),
  );

  static Tokens of(BuildContext context) =>
      Theme.of(context).brightness == Brightness.dark ? dark : light;

  bool get isDark => canvas == dark.canvas;
}

const sans = 'Geist';
const display = 'Bricolage';
const mono = 'GeistMono';

const tabular = [FontFeature.tabularFigures()];

class T {
  static const body = TextStyle(fontFamily: sans, fontSize: 14, height: 1.45);
  static const hPage = TextStyle(
    fontFamily: display,
    fontSize: 28,
    height: 1.15,
    fontWeight: FontWeight.w600,
    letterSpacing: -0.56,
  );
  static const hSec = TextStyle(
    fontFamily: sans,
    fontSize: 15,
    height: 1.35,
    fontWeight: FontWeight.w600,
    letterSpacing: -0.075,
  );
  static const sub = TextStyle(fontFamily: sans, fontSize: 13.5, height: 1.45);
  static const statNum = TextStyle(
    fontFamily: display,
    fontSize: 34,
    height: 1,
    fontWeight: FontWeight.w600,
    letterSpacing: -0.85,
    fontFeatures: tabular,
  );

  static TextStyle m(double size, {FontWeight? weight, double? height}) => TextStyle(
    fontFamily: mono,
    fontSize: size,
    height: height,
    fontWeight: weight,
  );

  static TextStyle d(double size, {FontWeight weight = FontWeight.w600, double em = -0.02}) =>
      TextStyle(
        fontFamily: display,
        fontSize: size,
        height: 1.1,
        fontWeight: weight,
        letterSpacing: size * em,
      );
}

const r6 = BorderRadius.all(Radius.circular(6));
const r8 = BorderRadius.all(Radius.circular(8));
const r10 = BorderRadius.all(Radius.circular(10));
const r12 = BorderRadius.all(Radius.circular(12));
const r16 = BorderRadius.all(Radius.circular(16));

const spring = Cubic(0.2, 1.4, 0.4, 1);
const easeOutSoft = Cubic(0.2, 0.8, 0.2, 1);

List<BoxShadow> cardShadow(Tokens t) => [
  BoxShadow(color: t.shadow.withValues(alpha: 0.04), offset: const Offset(0, 1), blurRadius: 2),
  BoxShadow(
    color: t.shadow.withValues(alpha: 0.08),
    offset: const Offset(0, 4),
    blurRadius: 16,
    spreadRadius: -8,
  ),
];

List<BoxShadow> menuShadow(Tokens t) => [
  BoxShadow(
    color: t.shadow.withValues(alpha: 0.3),
    offset: const Offset(0, 16),
    blurRadius: 48,
    spreadRadius: -12,
  ),
  BoxShadow(color: t.shadow.withValues(alpha: 0.06), offset: const Offset(0, 2), blurRadius: 6),
];

ThemeData themeFor(Brightness brightness) {
  final t = brightness == Brightness.dark ? Tokens.dark : Tokens.light;
  return ThemeData(
    brightness: brightness,
    scaffoldBackgroundColor: t.canvas,
    canvasColor: t.canvas,
    fontFamily: sans,
    colorScheme: ColorScheme.fromSeed(
      seedColor: t.accent,
      brightness: brightness,
    ).copyWith(primary: t.accent, onPrimary: t.onAccent, surface: t.surface),
    textSelectionTheme: TextSelectionThemeData(
      cursorColor: t.accent,
      selectionColor: t.accent.withValues(alpha: 0.2),
      selectionHandleColor: t.accent,
    ),
    textTheme: Typography.englishLike2021.apply(
      fontFamily: sans,
      bodyColor: t.ink,
      displayColor: t.ink,
    ),
    splashFactory: NoSplash.splashFactory,
    highlightColor: Colors.transparent,
    hoverColor: Colors.transparent,
    visualDensity: VisualDensity.standard,
  );
}
