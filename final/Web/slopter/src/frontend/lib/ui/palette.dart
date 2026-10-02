import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../icons.dart';
import '../theme.dart';
import 'kit.dart';
import 'shell.dart';
import 'theme_control.dart';

class _Command {
  const _Command(this.label, this.group, this.icon, this.run);

  final String label;
  final String group;
  final String icon;
  final void Function(NavigatorState) run;
}

List<_Command> _commands() => [
  for (final (_, label, route, icon, _) in navItems)
    _Command(label, 'Go to', icon, (nav) => nav.pushReplacementNamed(route)),
  _Command('New campaign', 'Actions', 'plus', (nav) => nav.pushNamed('/campaigns/new')),
  _Command('Redeem a code', 'Actions', 'check', (nav) => nav.pushReplacementNamed('/redeem')),
  _Command('Narrow a key', 'Actions', 'shield', (nav) => nav.pushReplacementNamed('/keys')),
  _Command('Use light theme', 'Preferences', 'sun', (_) => setThemeMode(ThemeMode.light)),
  _Command('Use dark theme', 'Preferences', 'moon', (_) => setThemeMode(ThemeMode.dark)),
  _Command('Use system theme', 'Preferences', 'monitor', (_) => setThemeMode(ThemeMode.system)),
  const _Command('Sign out', 'Account', 'logout', signOut),
];

Future<void> openPalette(BuildContext context) => showDialog(
  context: context,
  barrierColor: const Color(0x73050A08),
  builder: (context) => const _Palette(),
);

class _Palette extends StatefulWidget {
  const _Palette();

  @override
  State<_Palette> createState() => _PaletteState();
}

class _PaletteState extends State<_Palette> {
  final _controller = TextEditingController();
  late final FocusNode _node = FocusNode(onKeyEvent: _onKey);
  final _scroll = ScrollController();
  int _selected = 0;

  List<_Command> get _matches {
    final q = _controller.text.trim().toLowerCase();
    return _commands().where((c) => c.label.toLowerCase().contains(q)).toList();
  }

  KeyEventResult _onKey(FocusNode node, KeyEvent event) {
    if (event is! KeyDownEvent && event is! KeyRepeatEvent) return KeyEventResult.ignored;
    final items = _matches;
    if (items.isEmpty) return KeyEventResult.ignored;
    if (event.logicalKey == LogicalKeyboardKey.arrowDown) {
      setState(() => _selected = (_selected + 1) % items.length);
      return KeyEventResult.handled;
    }
    if (event.logicalKey == LogicalKeyboardKey.arrowUp) {
      setState(() => _selected = (_selected - 1 + items.length) % items.length);
      return KeyEventResult.handled;
    }
    if (event.logicalKey == LogicalKeyboardKey.enter) {
      _run(items[_selected.clamp(0, items.length - 1)]);
      return KeyEventResult.handled;
    }
    return KeyEventResult.ignored;
  }

  void _run(_Command command) {
    final navigator = Navigator.of(context);
    navigator.pop();
    command.run(navigator);
  }

  @override
  void dispose() {
    _controller.dispose();
    _node.dispose();
    _scroll.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final items = _matches;
    final selected = _selected.clamp(0, items.isEmpty ? 0 : items.length - 1);
    final rows = <Widget>[];
    var group = '';
    for (var i = 0; i < items.length; i++) {
      final item = items[i];
      if (item.group != group) {
        group = item.group;
        rows.add(
          Padding(
            padding: const EdgeInsets.fromLTRB(10, 12, 10, 6),
            child: Text(
              group,
              style: TextStyle(
                fontFamily: sans,
                fontSize: 12,
                fontWeight: FontWeight.w500,
                color: t.faint,
              ),
            ),
          ),
        );
      }
      rows.add(
        _PaletteRow(
          command: item,
          selected: i == selected,
          onHover: () => setState(() => _selected = i),
          onTap: () => _run(item),
        ),
      );
    }

    return Align(
      alignment: Alignment.topCenter,
      child: Padding(
        padding: EdgeInsets.only(top: MediaQuery.sizeOf(context).height * 0.12, left: 16, right: 16),
        child: Material(
          color: t.surface,
          clipBehavior: Clip.antiAlias,
          shape: RoundedRectangleBorder(borderRadius: r16, side: BorderSide(color: t.line)),
          child: SizedBox(
            width: 580,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  height: 56,
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  decoration: BoxDecoration(
                    border: Border(bottom: BorderSide(color: t.line)),
                  ),
                  child: Row(
                    children: [
                      Ico('search', size: 20, color: t.faint),
                      const SizedBox(width: 12),
                      Expanded(
                        child: TextField(
                          controller: _controller,
                          focusNode: _node,
                          autofocus: true,
                          cursorWidth: 1.5,
                          cursorColor: t.accent,
                          onChanged: (_) => setState(() => _selected = 0),
                          style: TextStyle(fontFamily: sans, fontSize: 15, color: t.ink),
                          decoration: InputDecoration(
                            isCollapsed: true,
                            border: InputBorder.none,
                            hintText: 'Search pages and actions',
                            hintStyle: TextStyle(fontFamily: sans, fontSize: 15, color: t.faint),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      const Kbd('Esc'),
                    ],
                  ),
                ),
                ConstrainedBox(
                  constraints: BoxConstraints(maxHeight: MediaQuery.sizeOf(context).height * 0.5),
                  child: items.isEmpty
                      ? Padding(
                          padding: const EdgeInsets.symmetric(vertical: 40, horizontal: 12),
                          child: Text(
                            'Nothing matches "${_controller.text}".',
                            style: T.sub.copyWith(color: t.muted),
                          ),
                        )
                      : SingleChildScrollView(
                          controller: _scroll,
                          padding: const EdgeInsets.all(8),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: rows,
                          ),
                        ),
                ),
                Container(
                  height: 40,
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  decoration: BoxDecoration(
                    color: t.raised.withValues(alpha: 0.5),
                    border: Border(top: BorderSide(color: t.line)),
                  ),
                  child: Row(
                    children: [
                      const Kbd('↑'),
                      const SizedBox(width: 2),
                      const Kbd('↓'),
                      const SizedBox(width: 6),
                      Text(
                        'Move',
                        style: TextStyle(fontFamily: sans, fontSize: 12, color: t.faint),
                      ),
                      const SizedBox(width: 16),
                      const Kbd('↵'),
                      const SizedBox(width: 6),
                      Text(
                        'Open',
                        style: TextStyle(fontFamily: sans, fontSize: 12, color: t.faint),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _PaletteRow extends StatelessWidget {
  const _PaletteRow({
    required this.command,
    required this.selected,
    required this.onHover,
    required this.onTap,
  });

  final _Command command;
  final bool selected;
  final VoidCallback onHover;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return MouseRegion(
      cursor: SystemMouseCursors.click,
      onEnter: (_) => onHover(),
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
          decoration: BoxDecoration(
            color: selected ? t.raised : Colors.transparent,
            borderRadius: r8,
          ),
          child: Row(
            children: [
              Container(
                width: 32,
                height: 32,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: selected ? t.accentSoft : t.raised,
                  borderRadius: r8,
                  border: Border.all(
                    color: selected ? t.accent.withValues(alpha: 0.2) : t.line,
                  ),
                ),
                child: Ico(command.icon, size: 16, color: selected ? t.accent : t.muted),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  command.label,
                  style: TextStyle(
                    fontFamily: sans,
                    fontSize: 13.5,
                    fontWeight: FontWeight.w500,
                    color: t.ink,
                  ),
                ),
              ),
              if (selected) Ico('enter', size: 16, color: t.faint),
            ],
          ),
        ),
      ),
    );
  }
}

Future<bool> confirmDialog(
  BuildContext context, {
  required String title,
  required Widget body,
  required String confirmLabel,
  bool danger = false,
}) async {
  final result = await showDialog<bool>(
    context: context,
    barrierColor: const Color(0x73050A08),
    builder: (context) {
      final t = Tokens.of(context);
      return Center(
        child: Material(
          color: t.surface,
          clipBehavior: Clip.antiAlias,
          shape: RoundedRectangleBorder(borderRadius: r16, side: BorderSide(color: t.line)),
          child: SizedBox(
            width: 420,
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        width: 40,
                        height: 40,
                        alignment: Alignment.center,
                        decoration: BoxDecoration(
                          color: danger ? t.dangerSoft : t.accentSoft,
                          shape: BoxShape.circle,
                        ),
                        child: Ico(
                          danger ? 'alert' : 'info',
                          size: 20,
                          color: danger ? t.danger : t.accent,
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(title, style: T.hSec.copyWith(color: t.ink)),
                            const SizedBox(height: 6),
                            body,
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      Btn(
                        onPressed: () => Navigator.of(context).pop(false),
                        child: const Text('Cancel'),
                      ),
                      const SizedBox(width: 8),
                      Btn(
                        kind: danger ? BtnKind.danger : BtnKind.primary,
                        onPressed: () => Navigator.of(context).pop(true),
                        child: Text(confirmLabel),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      );
    },
  );
  return result ?? false;
}
