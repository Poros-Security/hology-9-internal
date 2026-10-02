import 'package:flutter/material.dart';

import '../api.dart';
import '../icons.dart';
import '../theme.dart';
import '../ui/kit.dart';
import '../ui/palette.dart';
import '../ui/shell.dart';
import '../ui/toast.dart';

class Keys extends StatefulWidget {
  const Keys({super.key});

  @override
  State<Keys> createState() => _KeysState();
}

class _KeysState extends State<Keys> {
  String? _selectedId;
  Set<String> _keep = {};
  bool _busy = false;

  ApiKey get _selected {
    final keys = app.me!.keys;
    return keys.firstWhere((k) => k.id == _selectedId, orElse: () => keys.first);
  }

  void _pick(ApiKey key) {
    setState(() {
      _selectedId = key.id;
      _keep = key.scope.toSet();
    });
  }

  List<String> get _removed =>
      _selected.scope.where((s) => !_keep.contains(s)).toList();

  Future<void> _narrow() async {
    final removed = _removed;
    final key = _selected;
    final confirmed = await confirmDialog(
      context,
      title: 'Narrow ${key.id}?',
      body: _RemovedSentence(scopes: removed),
      confirmLabel: 'Narrow key',
      danger: true,
    );
    if (!confirmed) return;
    setState(() => _busy = true);
    try {
      await Api.narrow(key.id, _keep.toList());
      await app.load();
      if (!mounted) return;
      final updated = app.me!.keys.firstWhere((k) => k.id == key.id, orElse: () => key);
      setState(() => _keep = updated.scope.toSet());
      showToast(
        '${key.id} narrowed',
        description: 'It now has ${updated.scope.length} '
            'permission${updated.scope.length == 1 ? '' : 's'}.',
      );
    } on ApiError catch (e) {
      showToast('Could not narrow the key', description: e.message, kind: ToastKind.err);
    }
    if (mounted) setState(() => _busy = false);
  }

  @override
  Widget build(BuildContext context) {
    return Shell(
      page: 'keys',
      builder: (context) {
        final t = Tokens.of(context);
        final padding = pagePadding(context);
        final keys = app.me!.keys;
        if (_selectedId == null && keys.isNotEmpty) {
          _selectedId = keys.first.id;
          _keep = keys.first.scope.toSet();
        }

        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            PageHead(
              title: Text('API keys', style: T.hPage.copyWith(color: t.ink)),
              subtitle:
                  'Each key has its own permissions. The dashboard uses the key picked at the '
                  'top of the page.',
            ),
            Padding(
              padding: padding,
              child: _KeyCards(keys: keys),
            ),
            Padding(
              padding: EdgeInsets.fromLTRB(padding.left, 40, padding.right, 56),
              child: MediaQuery.sizeOf(context).width >= 1024
                  ? Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(width: 280, child: _NarrowBlurb()),
                        const SizedBox(width: 48),
                        Expanded(child: _narrowForm(context, keys)),
                      ],
                    )
                  : Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        const _NarrowBlurb(),
                        const SizedBox(height: 24),
                        _narrowForm(context, keys),
                      ],
                    ),
            ),
          ],
        );
      },
    );
  }

  Widget _narrowForm(BuildContext context, List<ApiKey> keys) {
    final t = Tokens.of(context);
    final removed = _removed;
    final selected = _selected;

    return ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 672),
      child: SCard(
        clip: true,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const FieldLabel('Key'),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      for (final key in keys)
                        SizedBox(
                          width: MediaQuery.sizeOf(context).width >= 640 ? 288 : double.infinity,
                          child: _KeyRadio(
                            apiKey: key,
                            checked: key.id == selected.id,
                            onTap: () => _pick(key),
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 24),
                  const FieldLabel('Permissions to keep'),
                  if (selected.scope.isEmpty)
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        borderRadius: r12,
                        border: Border.all(color: t.line),
                      ),
                      child: Text(
                        'This key has no permissions left to take away.',
                        style: T.sub.copyWith(color: t.muted),
                      ),
                    )
                  else
                    Container(
                      decoration: BoxDecoration(
                        borderRadius: r12,
                        border: Border.all(color: t.line),
                      ),
                      child: Column(
                        children: [
                          for (final (i, scope) in selected.scope.indexed)
                            _PermissionRow(
                              scope: scope,
                              on: _keep.contains(scope),
                              last: i == selected.scope.length - 1,
                              onChanged: (on) => setState(() {
                                if (on) {
                                  _keep.add(scope);
                                } else {
                                  _keep.remove(scope);
                                }
                              }),
                            ),
                        ],
                      ),
                    ),
                ],
              ),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
              decoration: BoxDecoration(
                color: t.raised.withValues(alpha: 0.5),
                border: Border(top: BorderSide(color: t.line)),
              ),
              child: Wrap(
                spacing: 12,
                runSpacing: 12,
                alignment: WrapAlignment.spaceBetween,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: [
                  removed.isEmpty
                      ? Text(
                          'Turn off at least one permission.',
                          style: TextStyle(fontFamily: sans, fontSize: 13, color: t.muted),
                        )
                      : Wrap(
                          spacing: 6,
                          runSpacing: 6,
                          crossAxisAlignment: WrapCrossAlignment.center,
                          children: [
                            Text(
                              'Removes',
                              style: TextStyle(fontFamily: sans, fontSize: 13, color: t.muted),
                            ),
                            for (final scope in removed)
                              Rise(
                                distance: 4,
                                child: ScopeChip(
                                  scope,
                                  strike: true,
                                  color: t.danger,
                                  background: t.dangerSoft,
                                  border: t.danger.withValues(alpha: 0.2),
                                ),
                              ),
                          ],
                        ),
                  Btn(
                    kind: BtnKind.primary,
                    busy: _busy,
                    onPressed: removed.isEmpty ? null : _narrow,
                    child: const Text('Narrow key'),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _RemovedSentence extends StatelessWidget {
  const _RemovedSentence({required this.scopes});

  final List<String> scopes;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'This removes these permissions from the key. You cannot undo this here.',
          style: TextStyle(fontFamily: sans, fontSize: 13.5, height: 1.6, color: t.muted),
        ),
        const SizedBox(height: 10),
        Wrap(
          spacing: 6,
          runSpacing: 6,
          children: [for (final scope in scopes) ScopeChip(scope)],
        ),
      ],
    );
  }
}

class _NarrowBlurb extends StatelessWidget {
  const _NarrowBlurb();

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 40,
          height: 40,
          alignment: Alignment.center,
          decoration: BoxDecoration(color: t.accentSoft, borderRadius: r12),
          child: Ico('shield', size: 20, color: t.accent),
        ),
        const SizedBox(height: 16),
        Text('Narrow a key', style: T.hSec.copyWith(color: t.ink)),
        const SizedBox(height: 4),
        Text(
          'Take permissions away before you give a key to staff. Only a scope voucher can add '
          'them back.',
          style: TextStyle(fontFamily: sans, fontSize: 13.5, height: 1.6, color: t.muted),
        ),
      ],
    );
  }
}

class _KeyCards extends StatelessWidget {
  const _KeyCards({required this.keys});

  final List<ApiKey> keys;

  @override
  Widget build(BuildContext context) {
    final cards = [for (final key in keys) _KeyCard(apiKey: key)];
    if (MediaQuery.sizeOf(context).width < 768) {
      return Column(
        children: stagger([
          for (final card in cards)
            Padding(padding: const EdgeInsets.only(bottom: 16), child: card),
        ]),
      );
    }
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          for (final (i, card) in stagger(cards).indexed) ...[
            if (i > 0) const SizedBox(width: 16),
            Expanded(child: card),
          ],
          for (var i = keys.length; i < 3; i++) ...[
            const SizedBox(width: 16),
            const Spacer(),
          ],
        ],
      ),
    );
  }
}

class _KeyCard extends StatelessWidget {
  const _KeyCard({required this.apiKey});

  final ApiKey apiKey;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final inUse = app.actingKey?.id == apiKey.id;
    return Opacity(
      opacity: apiKey.active ? 1 : 0.75,
      child: SCard(
        ring: inUse ? t.accent.withValues(alpha: 0.5) : null,
        ringWidth: inUse ? 2 : 1,
        padding: const EdgeInsets.all(20),
        child: Column(
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
                    color: apiKey.active ? t.accentSoft : t.dangerSoft,
                    borderRadius: r12,
                  ),
                  child: Ico('key', size: 20, color: apiKey.active ? t.accent : t.danger),
                ),
                const Spacer(),
                Pill(
                  apiKey.active ? (inUse ? 'In use' : 'Active') : 'Suspended',
                  kind: apiKey.active ? PillKind.ok : PillKind.bad,
                ),
              ],
            ),
            const SizedBox(height: 16),
            Text(
              apiKey.label,
              style: TextStyle(
                fontFamily: sans,
                fontSize: 14,
                fontWeight: FontWeight.w500,
                color: t.ink,
              ),
            ),
            Row(
              children: [
                Flexible(
                  child: Text(
                    apiKey.id,
                    overflow: TextOverflow.ellipsis,
                    style: T.m(12.5).copyWith(color: t.muted),
                  ),
                ),
                CopyButton(apiKey.id),
              ],
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 4,
              runSpacing: 4,
              children: [
                for (final scope in apiKey.scope) ScopeChip(scope),
                if (apiKey.scope.isEmpty)
                  Text(
                    'No permissions',
                    style: TextStyle(fontFamily: sans, fontSize: 12.5, color: t.faint),
                  ),
              ],
            ),
            const SizedBox(height: 20),
            if (!apiKey.active)
              Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Ico('alert', size: 16, color: t.danger),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        'Suspended. Any call that needs a permission comes back 403.',
                        style: TextStyle(
                          fontFamily: sans,
                          fontSize: 12.5,
                          height: 1.5,
                          color: t.danger,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            Btn(
              height: 32,
              expand: true,
              onPressed: inUse
                  ? null
                  : () {
                      app.actAs(apiKey.id);
                      showToast('Now acting as ${apiKey.id}', kind: ToastKind.info);
                    },
              child: Text(inUse ? 'In use by this dashboard' : 'Use this key'),
            ),
          ],
        ),
      ),
    );
  }
}

class _KeyRadio extends StatefulWidget {
  const _KeyRadio({required this.apiKey, required this.checked, required this.onTap});

  final ApiKey apiKey;
  final bool checked;
  final VoidCallback onTap;

  @override
  State<_KeyRadio> createState() => _KeyRadioState();
}

class _KeyRadioState extends State<_KeyRadio> {
  bool _hover = false;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return MouseRegion(
      cursor: SystemMouseCursors.click,
      onEnter: (_) => setState(() => _hover = true),
      onExit: (_) => setState(() => _hover = false),
      child: GestureDetector(
        onTap: widget.onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: widget.checked
                ? t.accentSoft.withValues(alpha: 0.4)
                : _hover
                ? t.raised
                : Colors.transparent,
            borderRadius: r12,
            border: Border.all(
              color: widget.checked ? t.accent : t.line,
              width: widget.checked ? 2 : 1,
            ),
          ),
          child: Row(
            children: [
              AnimatedContainer(
                duration: const Duration(milliseconds: 300),
                curve: spring,
                width: 20,
                height: 20,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: widget.checked ? t.accent : t.line,
                    width: widget.checked ? 6 : 1,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      widget.apiKey.active
                          ? widget.apiKey.label
                          : '${widget.apiKey.label} (suspended)',
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        fontFamily: sans,
                        fontSize: 13.5,
                        fontWeight: FontWeight.w500,
                        color: widget.apiKey.active ? t.ink : t.danger,
                      ),
                    ),
                    Text(
                      widget.apiKey.id,
                      overflow: TextOverflow.ellipsis,
                      style: T.m(12).copyWith(color: t.muted),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _PermissionRow extends StatefulWidget {
  const _PermissionRow({
    required this.scope,
    required this.on,
    required this.last,
    required this.onChanged,
  });

  final String scope;
  final bool on;
  final bool last;
  final ValueChanged<bool> onChanged;

  @override
  State<_PermissionRow> createState() => _PermissionRowState();
}

class _PermissionRowState extends State<_PermissionRow> {
  bool _hover = false;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return MouseRegion(
      cursor: SystemMouseCursors.click,
      onEnter: (_) => setState(() => _hover = true),
      onExit: (_) => setState(() => _hover = false),
      child: GestureDetector(
        onTap: () => widget.onChanged(!widget.on),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: _hover ? t.raised.withValues(alpha: 0.6) : Colors.transparent,
            border: widget.last ? null : Border(bottom: BorderSide(color: t.line)),
          ),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(widget.scope, style: T.m(12.5).copyWith(color: t.ink)),
                    Text(
                      scopeDescriptions[widget.scope] ?? '',
                      style: TextStyle(fontFamily: sans, fontSize: 12.5, color: t.muted),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              Toggle(value: widget.on, onChanged: widget.onChanged),
            ],
          ),
        ),
      ),
    );
  }
}
