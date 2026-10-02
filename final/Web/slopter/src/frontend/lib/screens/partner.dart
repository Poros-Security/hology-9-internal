import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../api.dart';
import '../icons.dart';
import '../theme.dart';
import '../ui/kit.dart';
import '../ui/shell.dart';
import '../ui/ticket.dart';
import '../ui/toast.dart';

const _tiers = [
  (
    'Merchant',
    'Run campaigns and redeem codes with your primary key.',
    ['redeem', 'campaigns:read', 'campaigns:write'],
    false,
  ),
  ('Analytics', 'Adds campaign analytics to your primary key.', ['+ campaigns:analytics'], true),
  (
    'Platform partner',
    'You get a second key that can only read platform settings, separate from your everyday key '
        'so you can hand it to staff.',
    ['new key: settings:read'],
    true,
  ),
];

class PartnerProgram extends StatefulWidget {
  const PartnerProgram({super.key});

  @override
  State<PartnerProgram> createState() => _PartnerProgramState();
}

class _PartnerProgramState extends State<PartnerProgram> {
  final _tillUrl = TextEditingController();
  Partner? _partner;
  String? _error;
  bool _saving = false;
  bool _tillLoaded = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _tillUrl.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() => _error = null);
    try {
      final partner = await Api.partner();
      if (mounted) setState(() => _partner = partner);
    } on ApiError catch (e) {
      if (mounted) setState(() => _error = e.message);
    }
  }

  Future<void> _saveTillUrl() async {
    setState(() => _saving = true);
    try {
      final saved = await Api.setTillUrl(_tillUrl.text.trim());
      await app.load();
      if (mounted) _tillUrl.text = saved;
      showToast(
        'Till notification URL saved',
        description: saved.isEmpty
            ? 'Slopter will not post anywhere.'
            : 'Slopter will post every redemption to $saved.',
      );
    } on ApiError catch (e) {
      showToast('Could not save the URL', description: e.message, kind: ToastKind.err);
    }
    if (mounted) setState(() => _saving = false);
  }

  @override
  Widget build(BuildContext context) {
    return Shell(
      page: 'partner',
      builder: (context) {
        final t = Tokens.of(context);
        final padding = pagePadding(context);
        final me = app.me!;
        if (!_tillLoaded) {
          _tillLoaded = true;
          _tillUrl.text = me.tillUrl;
        }
        final tier = _partner?.tier ?? me.tier;

        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            PageHead(
              title: Text('Partner Program', style: T.hPage.copyWith(color: t.ink)),
              subtitle: 'Higher tiers connect your account more closely to the platform.',
            ),
            Padding(
              padding: EdgeInsets.fromLTRB(padding.left, 20, padding.right, 0),
              child: _TierTrack(tier: tier),
            ),
            Padding(
              padding: EdgeInsets.fromLTRB(padding.left, 24, padding.right, 24),
              child: _error != null
                  ? SCard(
                      child: EmptyState(
                        icon: 'alert',
                        title: 'Could not load partner details',
                        description: _error,
                        action: Btn(onPressed: _load, child: const Text('Try again')),
                      ),
                    )
                  : _partner == null
                  ? const SCard(child: Loader())
                  : _UpgradeCard(partner: _partner!),
            ),
            Padding(
              padding: EdgeInsets.fromLTRB(padding.left, 0, padding.right, 56),
              child: _TillUrlCard(
                controller: _tillUrl,
                saving: _saving,
                onSave: _saveTillUrl,
                current: me.tillUrl,
              ),
            ),
          ],
        );
      },
    );
  }
}

class _TillUrlCard extends StatelessWidget {
  const _TillUrlCard({
    required this.controller,
    required this.saving,
    required this.onSave,
    required this.current,
  });

  final TextEditingController controller;
  final bool saving;
  final VoidCallback onSave;
  final String current;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final wide = MediaQuery.sizeOf(context).width >= 1024;
    final field = Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Field(
          controller: controller,
          icon: 'link',
          style: T.m(13),
          hint: 'https://till.example.com/hooks/slopter',
          onSubmitted: (_) => onSave(),
        ),
        Hint(
          current.isEmpty ? 'Empty, so Slopter does not post anywhere yet.' : 'Posting to $current',
        ),
      ],
    );

    return SCard(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Container(
                width: 40,
                height: 40,
                alignment: Alignment.center,
                decoration: BoxDecoration(color: t.accentSoft, borderRadius: r12),
                child: Ico('bolt', size: 20, color: t.accent),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Till notification URL', style: T.hSec.copyWith(color: t.ink)),
                    const SizedBox(height: 4),
                    Text(
                      'Slopter posts to this address whenever one of your codes is redeemed, '
                      'from any campaign.',
                      style: T.sub.copyWith(color: t.muted),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          const FieldLabel('Endpoint'),
          if (wide)
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(child: field),
                const SizedBox(width: 12),
                Btn(
                  kind: BtnKind.primary,
                  height: 44,
                  radius: 12,
                  busy: saving,
                  onPressed: onSave,
                  child: const Text('Save URL'),
                ),
              ],
            )
          else
            Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                field,
                const SizedBox(height: 12),
                Btn(
                  kind: BtnKind.primary,
                  height: 44,
                  radius: 12,
                  expand: true,
                  busy: saving,
                  onPressed: onSave,
                  child: const Text('Save URL'),
                ),
              ],
            ),
        ],
      ),
    );
  }
}

class _TierTrack extends StatelessWidget {
  const _TierTrack({required this.tier});

  final int tier;

  @override
  Widget build(BuildContext context) {
    final cards = [
      for (final (i, (name, body, scopes, additive)) in _tiers.indexed)
        _TierCard(
          index: i,
          name: name,
          body: body,
          scopes: scopes,
          additive: additive,
          current: i == tier,
          reached: i <= tier,
          next: i == tier + 1,
        ),
    ];
    if (MediaQuery.sizeOf(context).width < 768) {
      return Column(
        children: stagger([
          for (final card in cards)
            Padding(padding: const EdgeInsets.only(top: 20, bottom: 4), child: card),
        ]),
      );
    }
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          for (final (i, card) in stagger(cards).indexed) ...[
            if (i > 0) const SizedBox(width: 16),
            Expanded(child: Padding(padding: const EdgeInsets.only(top: 20), child: card)),
          ],
        ],
      ),
    );
  }
}

class _TierCard extends StatefulWidget {
  const _TierCard({
    required this.index,
    required this.name,
    required this.body,
    required this.scopes,
    required this.additive,
    required this.current,
    required this.reached,
    required this.next,
  });

  final int index;
  final String name;
  final String body;
  final List<String> scopes;
  final bool additive;
  final bool current;
  final bool reached;
  final bool next;

  @override
  State<_TierCard> createState() => _TierCardState();
}

class _TierCardState extends State<_TierCard> {
  bool _hover = false;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return MouseRegion(
      onEnter: (_) => setState(() => _hover = true),
      onExit: (_) => setState(() => _hover = false),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        transform: Matrix4.translationValues(0, _hover && !widget.current ? -4 : 0, 0),
        child: Stack(
          clipBehavior: Clip.none,
          alignment: Alignment.topCenter,
          children: [
            Padding(
              padding: const EdgeInsets.only(top: 20),
              child: SCard(
                ring: widget.current ? t.accent.withValues(alpha: 0.6) : null,
                ringWidth: widget.current ? 2 : 1,
                padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      widget.name,
                      textAlign: TextAlign.center,
                      style: T.d(19, em: -0.01).copyWith(color: t.ink),
                    ),
                    const SizedBox(height: 8),
                    Pill(
                      widget.current
                          ? 'You are here'
                          : widget.next
                          ? 'Next'
                          : widget.reached
                          ? 'Unlocked'
                          : 'Locked',
                      kind: widget.current || widget.reached ? PillKind.ok : PillKind.off,
                    ),
                    const SizedBox(height: 12),
                    Text(
                      widget.body,
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontFamily: sans,
                        fontSize: 13.5,
                        height: 1.6,
                        color: t.muted,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Wrap(
                      alignment: WrapAlignment.center,
                      spacing: 4,
                      runSpacing: 4,
                      children: [
                        for (final scope in widget.scopes)
                          ScopeChip(
                            scope,
                            color: widget.additive ? t.accent : null,
                            background: widget.additive ? t.accentSoft : null,
                            border: widget.additive ? t.accent.withValues(alpha: 0.2) : null,
                          ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            Container(
              width: 40,
              height: 40,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: widget.current ? t.accent : t.surface,
                shape: BoxShape.circle,
                border: Border.all(color: t.surface, width: 4),
                boxShadow: widget.current
                    ? null
                    : [BoxShadow(color: t.line, spreadRadius: 1, blurStyle: BlurStyle.solid)],
              ),
              child: Text(
                '${widget.index}',
                style: TextStyle(
                  fontFamily: display,
                  fontSize: 15,
                  height: 1,
                  fontWeight: FontWeight.w600,
                  color: widget.current ? t.onAccent : t.muted,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _UpgradeCard extends StatelessWidget {
  const _UpgradeCard({required this.partner});

  final Partner partner;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final wide = MediaQuery.sizeOf(context).width >= 1024;
    final sm = MediaQuery.sizeOf(context).width >= 640;

    final left = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Your upgrade code', style: T.hSec.copyWith(color: t.ink)),
        const SizedBox(height: 4),
        Text(
          'Each account gets one. It works once and moves you up a tier.',
          style: T.sub.copyWith(color: t.muted),
        ),
        const SizedBox(height: 24),
        Ticket(
          stub: sm ? 120 : 96,
          filledStub: true,
          body: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  'Partner upgrade',
                  style: TextStyle(fontFamily: sans, fontSize: 13, color: t.muted),
                ),
                const SizedBox(height: 12),
                Text(
                  partner.upgradeCode,
                  style: T.m(sm ? 24 : 19).copyWith(
                    letterSpacing: (sm ? 24 : 19) * 0.14,
                    color: t.ink,
                    decoration: partner.used ? TextDecoration.lineThrough : null,
                  ),
                ),
              ],
            ),
          ),
          stubChild: Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text('+1', style: T.d(30, em: -0.02).copyWith(color: t.accent)),
                const SizedBox(height: 4),
                Text(
                  'tier',
                  style: TextStyle(fontFamily: sans, fontSize: 12, color: t.muted),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 24),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            Btn(
              kind: BtnKind.primary,
              onPressed: partner.used
                  ? null
                  : () => Navigator.of(context).pushReplacementNamed(
                      '/redeem',
                      arguments: partner.upgradeCode,
                    ),
              child: const Text('Redeem this code'),
            ),
            Btn(
              icon: 'copy',
              onPressed: () async {
                await Clipboard.setData(ClipboardData(text: partner.upgradeCode));
                showToast(
                  'Copied to clipboard',
                  description: partner.upgradeCode,
                  kind: ToastKind.info,
                );
              },
              child: const Text('Copy code'),
            ),
          ],
        ),
      ],
    );

    final rows = [
      ('Code status', partner.used ? 'Used' : 'Unused'),
      ('Tier now', '${partner.tier}, ${_tiers[partner.tier.clamp(0, 2)].$1}'),
      (
        'After redeeming',
        partner.tier >= 2
            ? 'Already at the top tier'
            : '${partner.tier + 1}, ${_tiers[partner.tier + 1].$1}',
      ),
    ];

    final table = Container(
      decoration: BoxDecoration(borderRadius: r16, border: Border.all(color: t.line)),
      child: Column(
        children: [
          for (final (i, (label, value)) in rows.indexed)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              decoration: BoxDecoration(
                border: i == rows.length - 1 ? null : Border(bottom: BorderSide(color: t.line)),
              ),
              child: Row(
                children: [
                  Text(
                    label,
                    style: TextStyle(fontFamily: sans, fontSize: 13.5, color: t.muted),
                  ),
                  const Spacer(),
                  if (i == 0)
                    Pill(value, kind: partner.used ? PillKind.off : PillKind.ok)
                  else
                    Text(
                      value,
                      style: TextStyle(
                        fontFamily: sans,
                        fontSize: 13.5,
                        fontWeight: FontWeight.w500,
                        color: i == 2 ? t.accent : t.ink,
                      ),
                    ),
                ],
              ),
            ),
        ],
      ),
    );

    return SCard(
      padding: EdgeInsets.all(sm ? 32 : 24),
      child: wide
          ? Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Expanded(child: left),
                const SizedBox(width: 40),
                SizedBox(width: 300, child: table),
              ],
            )
          : Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [left, const SizedBox(height: 32), table],
            ),
    );
  }
}
