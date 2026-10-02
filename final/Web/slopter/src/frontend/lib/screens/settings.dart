import 'package:flutter/material.dart';

import '../api.dart';
import '../icons.dart';
import '../theme.dart';
import '../ui/kit.dart';
import '../ui/shell.dart';

class Settings extends StatefulWidget {
  const Settings({super.key});

  @override
  State<Settings> createState() => _SettingsState();
}

class _SettingsState extends State<Settings> {
  Map<String, String>? _fields;
  ApiError? _error;
  String? _loadedFor;

  Future<void> _load() async {
    setState(() {
      _fields = null;
      _error = null;
    });
    try {
      final fields = await Api.settings();
      if (mounted) setState(() => _fields = fields);
    } on ApiError catch (e) {
      if (mounted) setState(() => _error = e);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Shell(
      page: 'settings',
      builder: (context) {
        final t = Tokens.of(context);
        final padding = pagePadding(context);
        final acting = app.actingKey;
        if (acting != null && _loadedFor != acting.id) {
          _loadedFor = acting.id;
          WidgetsBinding.instance.addPostFrameCallback((_) => _load());
        }

        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            PageHead(
              title: Text('Settings', style: T.hPage.copyWith(color: t.ink)),
              subtitle: 'Platform configuration. Read only.',
            ),
            Padding(
              padding: EdgeInsets.fromLTRB(padding.left, 0, padding.right, 56),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 896),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: stagger([
                    if (_error != null) _Denied(error: _error!, keyId: acting?.id ?? ''),
                    Padding(
                      padding: EdgeInsets.only(top: _error != null ? 24 : 0),
                      child: SCard(
                        clip: true,
                        child: _fields == null
                            ? const _SkeletonFields()
                            : _fields!.isEmpty
                            ? const EmptyState(
                                icon: 'sliders',
                                title: 'No configuration to show',
                                description: 'The platform returned an empty settings map.',
                              )
                            : _Fields(fields: _fields!),
                      ),
                    ),
                  ]),
                ),
              ),
            ),
          ],
        );
      },
    );
  }
}

class _Denied extends StatelessWidget {
  const _Denied({required this.error, required this.keyId});

  final ApiError error;
  final String keyId;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final suspended = app.actingKey?.active == false;
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: t.warnSoft,
        borderRadius: r16,
        border: Border.all(color: t.warn.withValues(alpha: 0.2)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 40,
            height: 40,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: t.surface.withValues(alpha: 0.7),
              borderRadius: r12,
            ),
            child: Ico('lock', size: 20, color: t.warn),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  error.forbidden
                      ? suspended
                            ? 'This key is suspended'
                            : "This key can't read platform settings"
                      : 'Settings are unavailable',
                  style: TextStyle(
                    fontFamily: sans,
                    fontSize: 13.5,
                    fontWeight: FontWeight.w500,
                    color: t.ink,
                  ),
                ),
                const SizedBox(height: 4),
                Wrap(
                  crossAxisAlignment: WrapCrossAlignment.center,
                  spacing: 6,
                  runSpacing: 6,
                  children: [
                    Text(
                      keyId,
                      style: T.m(12.5).copyWith(color: t.ink),
                    ),
                    Text(
                      'reported: ${error.message}.',
                      style: TextStyle(
                        fontFamily: sans,
                        fontSize: 13.5,
                        height: 1.6,
                        color: t.muted,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  'Partner tier 2 gives you a separate key that can read configuration. Once you '
                  'have it, pick it from the key menu at the top.',
                  style: TextStyle(
                    fontFamily: sans,
                    fontSize: 13.5,
                    height: 1.6,
                    color: t.muted,
                  ),
                ),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    Btn(
                      height: 32,
                      onPressed: () =>
                          Navigator.of(context).pushReplacementNamed('/partner'),
                      child: const Text('Go to Partner Program'),
                    ),
                    const Padding(
                      padding: EdgeInsets.only(top: 4),
                      child: ScopeChip('settings:read'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SkeletonFields extends StatelessWidget {
  const _SkeletonFields();

  static const _widths = [0.40, 0.28, 0.18, 0.44, 0.52, 0.86];

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final wide = MediaQuery.sizeOf(context).width >= 640;
    return Column(
      children: [
        for (final (i, width) in _widths.indexed)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
            decoration: BoxDecoration(
              border: i == _widths.length - 1
                  ? null
                  : Border(bottom: BorderSide(color: t.line)),
            ),
            child: wide
                ? Row(
                    children: [
                      SizedBox(
                        width: 220,
                        child: Row(
                          children: [
                            Ico('lock', size: 14, color: t.faint),
                            const SizedBox(width: 8),
                            Shimmer(
                              width: 92,
                              height: 12,
                              delay: Duration(milliseconds: i * 80),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 24),
                      Expanded(
                        child: FractionallySizedBox(
                          alignment: Alignment.centerLeft,
                          widthFactor: width,
                          child: Shimmer(
                            height: 14,
                            delay: Duration(milliseconds: i * 80),
                          ),
                        ),
                      ),
                    ],
                  )
                : Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Row(
                        children: [
                          Ico('lock', size: 14, color: t.faint),
                          const SizedBox(width: 8),
                          Shimmer(
                            width: 92,
                            height: 12,
                            delay: Duration(milliseconds: i * 80),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      FractionallySizedBox(
                        alignment: Alignment.centerLeft,
                        widthFactor: width,
                        child: Shimmer(height: 14, delay: Duration(milliseconds: i * 80)),
                      ),
                    ],
                  ),
          ),
      ],
    );
  }
}

class _Fields extends StatelessWidget {
  const _Fields({required this.fields});

  final Map<String, String> fields;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final entries = fields.entries.toList();
    final wide = MediaQuery.sizeOf(context).width >= 640;
    final labelStyle = TextStyle(fontFamily: sans, fontSize: 13.5, color: t.muted);
    final valueStyle = TextStyle(
      fontFamily: sans,
      fontSize: 13.5,
      height: 1.5,
      fontWeight: FontWeight.w500,
      color: t.ink,
    );

    return Column(
      children: [
        for (final (i, entry) in entries.indexed)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
            decoration: BoxDecoration(
              border: i == entries.length - 1
                  ? null
                  : Border(bottom: BorderSide(color: t.line)),
            ),
            child: wide
                ? Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      SizedBox(width: 220, child: Text(entry.key, style: labelStyle)),
                      const SizedBox(width: 24),
                      Expanded(
                        child: SelectableText(entry.value, style: valueStyle),
                      ),
                    ],
                  )
                : Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(entry.key, style: labelStyle),
                      const SizedBox(height: 4),
                      SelectableText(entry.value, style: valueStyle),
                    ],
                  ),
          ),
      ],
    );
  }
}
