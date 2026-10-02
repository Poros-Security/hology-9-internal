import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../api.dart';
import '../icons.dart';
import '../theme.dart';
import '../ui/kit.dart';
import '../ui/shell.dart';
import '../ui/toast.dart';

enum _Tab { all, unused, used }

class CampaignDetail extends StatefulWidget {
  const CampaignDetail({required this.id, super.key});

  final String id;

  @override
  State<CampaignDetail> createState() => _CampaignDetailState();
}

class _CampaignDetailState extends State<CampaignDetail> {
  static const _perPage = 8;

  final _query = TextEditingController();
  final _callback = TextEditingController();
  _Tab _tab = _Tab.all;
  int _page = 0;
  Campaign? _campaign;
  String? _error;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _query.dispose();
    _callback.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() => _error = null);
    try {
      final campaign = await Api.campaign(widget.id);
      if (!mounted) return;
      _callback.text = campaign.callbackUrl;
      setState(() => _campaign = campaign);
    } on ApiError catch (e) {
      if (mounted) setState(() => _error = e.message);
    }
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      await Api.setCallback(widget.id, _callback.text.trim());
      showToast('Callback URL saved', description: 'Used from the next redemption onward.');
      await _load();
    } on ApiError catch (e) {
      showToast('Could not save the callback URL', description: e.message, kind: ToastKind.err);
    }
    if (mounted) setState(() => _saving = false);
  }

  List<VoucherCode> get _codes {
    final q = _query.text.trim().toUpperCase();
    return (_campaign?.codes ?? [])
        .where(
          (c) =>
              c.code.contains(q) &&
              switch (_tab) {
                _Tab.all => true,
                _Tab.unused => !c.used,
                _Tab.used => c.used,
              },
        )
        .toList();
  }

  @override
  Widget build(BuildContext context) {
    return Shell(
      page: 'campaigns',
      builder: (context) {
        final t = Tokens.of(context);
        final padding = pagePadding(context);
        final campaign = _campaign;

        if (_error != null) {
          return Padding(
            padding: const EdgeInsets.only(top: 40),
            child: EmptyState(
              icon: 'alert',
              title: 'Could not load this campaign',
              description: _error,
              action: Btn(onPressed: _load, child: const Text('Try again')),
            ),
          );
        }
        if (campaign == null) return const Loader();

        final wide = MediaQuery.sizeOf(context).width >= 1280;
        final aside = Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _CallbackForm(
              controller: _callback,
              saving: _saving,
              onSave: app.can('campaigns:write') ? _save : null,
            ),
            const SizedBox(height: 16),
            _AnalyticsCard(id: campaign.id),
          ],
        );

        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            PageHead(
              leading: Glyph(
                label: campaign.name,
                color: campaign.color,
                size: 48,
                radius: 16,
              ),
              crumb: Crumb(
                'Campaigns',
                onTap: () => Navigator.of(context).pushReplacementNamed('/campaigns'),
              ),
              title: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(campaign.name, style: T.hPage.copyWith(color: t.ink)),
                  const SizedBox(width: 12),
                  Pill(
                    campaign.done ? 'All used' : 'Active',
                    kind: campaign.done ? PillKind.off : PillKind.ok,
                    live: !campaign.done,
                  ),
                ],
              ),
              actions: [
                Btn(
                  icon: 'copy',
                  onPressed: () async {
                    await Clipboard.setData(ClipboardData(text: campaign.id));
                    showToast(
                      'Copied to clipboard',
                      description: campaign.id,
                      kind: ToastKind.info,
                    );
                  },
                  child: Text(campaign.id, style: T.m(12.5).copyWith(color: t.ink)),
                ),
              ],
            ),
            Padding(
              padding: padding,
              child: _StatRow(campaign: campaign),
            ),
            Padding(
              padding: EdgeInsets.fromLTRB(padding.left, 24, padding.right, 56),
              child: wide
                  ? Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(child: _codesCard(context)),
                        const SizedBox(width: 16),
                        SizedBox(width: 360, child: aside),
                      ],
                    )
                  : Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [_codesCard(context), const SizedBox(height: 16), aside],
                    ),
            ),
          ],
        );
      },
    );
  }

  Widget _codesCard(BuildContext context) {
    final t = Tokens.of(context);
    final list = _codes;
    final pages = (list.length / _perPage).ceil().clamp(1, 9999);
    final page = _page.clamp(0, pages - 1);
    final slice = list.skip(page * _perPage).take(_perPage).toList();

    return SCard(
      clip: true,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
            decoration: BoxDecoration(border: Border(bottom: BorderSide(color: t.line))),
            child: Wrap(
              spacing: 12,
              runSpacing: 12,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                Text('Codes', style: T.hSec.copyWith(color: t.ink)),
                SizedBox(
                  width: 208,
                  child: Field(
                    controller: _query,
                    icon: 'search',
                    height: 36,
                    hint: 'Find a code',
                    style: T.m(12.5),
                    onChanged: (_) => setState(() => _page = 0),
                  ),
                ),
                Seg<_Tab>(
                  value: _tab,
                  onChanged: (v) => setState(() {
                    _tab = v;
                    _page = 0;
                  }),
                  items: const [
                    SegItem(_Tab.all, label: 'All'),
                    SegItem(_Tab.unused, label: 'Unused'),
                    SegItem(_Tab.used, label: 'Redeemed'),
                  ],
                ),
              ],
            ),
          ),
          ConstrainedBox(
            constraints: const BoxConstraints(minHeight: 400),
            child: slice.isEmpty
                ? EmptyState(
                    icon: 'search',
                    title: 'No codes match',
                    description: _query.text.isEmpty
                        ? 'Try another filter.'
                        : 'Nothing matches "${_query.text}".',
                  )
                : Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      for (final (i, code) in slice.indexed)
                        Rise(
                          delay: Duration(milliseconds: i * 25),
                          child: _CodeRow(code: code, last: i == slice.length - 1),
                        ),
                    ],
                  ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
            decoration: BoxDecoration(border: Border(top: BorderSide(color: t.line))),
            child: Row(
              children: [
                Text(
                  list.isEmpty
                      ? '0 codes'
                      : '${page * _perPage + 1} to ${page * _perPage + slice.length} '
                            'of ${list.length}',
                  style: TextStyle(
                    fontFamily: sans,
                    fontSize: 12.5,
                    fontFeatures: tabular,
                    color: t.muted,
                  ),
                ),
                const Spacer(),
                Btn(
                  height: 32,
                  square: true,
                  tip: 'Previous page',
                  onPressed: page == 0 ? null : () => setState(() => _page = page - 1),
                  child: Ico('back', size: 16, color: t.ink),
                ),
                const SizedBox(width: 6),
                Btn(
                  height: 32,
                  square: true,
                  tip: 'Next page',
                  onPressed: page >= pages - 1 ? null : () => setState(() => _page = page + 1),
                  child: Ico('chevron', size: 16, color: t.ink),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _CodeRow extends StatefulWidget {
  const _CodeRow({required this.code, required this.last});

  final VoucherCode code;
  final bool last;

  @override
  State<_CodeRow> createState() => _CodeRowState();
}

class _CodeRowState extends State<_CodeRow> {
  bool _hover = false;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final used = widget.code.used;
    return MouseRegion(
      onEnter: (_) => setState(() => _hover = true),
      onExit: (_) => setState(() => _hover = false),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        height: 50,
        padding: const EdgeInsets.symmetric(horizontal: 20),
        decoration: BoxDecoration(
          color: _hover ? t.raised.withValues(alpha: 0.7) : Colors.transparent,
          border: widget.last ? null : Border(bottom: BorderSide(color: t.line)),
        ),
        child: Row(
          children: [
            Container(
              width: 8,
              height: 8,
              decoration: BoxDecoration(
                color: used ? t.faint.withValues(alpha: 0.5) : t.accent,
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Text(
                widget.code.code,
                style: T.m(13).copyWith(
                  letterSpacing: 0.3,
                  color: used ? t.faint : t.ink,
                  decoration: used ? TextDecoration.lineThrough : null,
                  decorationColor: t.faint.withValues(alpha: 0.6),
                ),
              ),
            ),
            Opacity(opacity: _hover ? 1 : 0, child: CopyButton(widget.code.code)),
            SizedBox(
              width: 96,
              child: Text(
                used ? 'Redeemed' : 'Unused',
                textAlign: TextAlign.right,
                style: TextStyle(
                  fontFamily: sans,
                  fontSize: 12.5,
                  color: used ? t.muted : t.faint,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _StatRow extends StatelessWidget {
  const _StatRow({required this.campaign});

  final Campaign campaign;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final cards = <Widget>[
      _StatTile(label: 'Discount', value: campaign.value, decimals: 2),
      _StatTile(label: 'Minted', value: campaign.codeCount),
      _StatTile(
        label: 'Redeemed',
        value: campaign.usedCount,
        bar: campaign.fraction,
      ),
      _StatTile(
        label: 'Credited',
        value: campaign.value * campaign.usedCount,
        decimals: 2,
      ),
    ];
    final columns = MediaQuery.sizeOf(context).width >= 1024 ? 4 : 2;
    final rows = <Widget>[];
    for (var i = 0; i < cards.length; i += columns) {
      rows.add(
        Padding(
          padding: EdgeInsets.only(bottom: i + columns < cards.length ? 16 : 0),
          child: IntrinsicHeight(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                for (var j = i; j < i + columns && j < cards.length; j++) ...[
                  if (j > i) const SizedBox(width: 16),
                  Expanded(child: cards[j]),
                ],
              ],
            ),
          ),
        ),
      );
    }
    return DefaultTextStyle(
      style: T.body.copyWith(color: t.ink),
      child: Column(children: stagger(rows)),
    );
  }
}

class _StatTile extends StatelessWidget {
  const _StatTile({required this.label, required this.value, this.decimals = 0, this.bar});

  final String label;
  final num value;
  final int decimals;
  final double? bar;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return SCard(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: TextStyle(fontFamily: sans, fontSize: 13, color: t.muted)),
          const SizedBox(height: 8),
          CountUp(value, decimals: decimals, style: T.statNum.copyWith(color: t.ink)),
          if (bar != null) ...[
            const SizedBox(height: 12),
            ClipRRect(
              borderRadius: BorderRadius.circular(999),
              child: SizedBox(
                height: 6,
                child: Stack(
                  children: [
                    Positioned.fill(child: ColoredBox(color: t.line)),
                    TweenAnimationBuilder<double>(
                      tween: Tween(begin: 0, end: 1),
                      duration: const Duration(milliseconds: 1000),
                      curve: easeOutSoft,
                      builder: (context, v, _) => FractionallySizedBox(
                        alignment: Alignment.centerLeft,
                        widthFactor: bar! * v,
                        child: ColoredBox(color: t.accent),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _CallbackForm extends StatelessWidget {
  const _CallbackForm({required this.controller, required this.saving, required this.onSave});

  final TextEditingController controller;
  final bool saving;
  final VoidCallback? onSave;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return SCard(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Text('Callback URL', style: T.hSec.copyWith(color: t.ink)),
              const Spacer(),
              const ScopeChip('campaigns:write'),
            ],
          ),
          const SizedBox(height: 16),
          Field(
            controller: controller,
            icon: 'link',
            style: T.m(12.5),
            hint: 'https://till.example.com/hooks/slopter',
            onSubmitted: (_) => onSave?.call(),
          ),
          Hint(
            onSave == null
                ? 'This key cannot edit campaigns. Switch to a key with campaigns:write.'
                : 'Used from the next redemption onward.',
          ),
          const SizedBox(height: 16),
          Btn(
            kind: BtnKind.primary,
            expand: true,
            busy: saving,
            onPressed: onSave,
            child: const Text('Save callback URL'),
          ),
        ],
      ),
    );
  }
}

class _AnalyticsCard extends StatefulWidget {
  const _AnalyticsCard({required this.id});

  final String id;

  @override
  State<_AnalyticsCard> createState() => _AnalyticsCardState();
}

class _AnalyticsCardState extends State<_AnalyticsCard> {
  Analytics? _data;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final data = await Api.analytics(widget.id);
      if (mounted) setState(() => _data = data);
    } on ApiError catch (e) {
      if (mounted) setState(() => _error = e.message);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final header = Row(
      children: [
        Text('Analytics', style: T.hSec.copyWith(color: t.ink)),
        const Spacer(),
        const ScopeChip('campaigns:analytics'),
      ],
    );

    if (_data != null) {
      final rows = [
        ('Minted', money(_data!.minted, 0)),
        ('Redeemed', money(_data!.redeemed, 0)),
        ('Credit moved', money(_data!.creditMoved)),
      ];
      return SCard(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            header,
            const SizedBox(height: 16),
            Container(
              decoration: BoxDecoration(borderRadius: r12, border: Border.all(color: t.line)),
              child: Column(
                children: [
                  for (final (i, (label, value)) in rows.indexed)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                      decoration: BoxDecoration(
                        border: i == rows.length - 1
                            ? null
                            : Border(bottom: BorderSide(color: t.line)),
                      ),
                      child: Row(
                        children: [
                          Text(
                            label,
                            style: TextStyle(fontFamily: sans, fontSize: 13, color: t.muted),
                          ),
                          const Spacer(),
                          Text(
                            value,
                            style: TextStyle(
                              fontFamily: sans,
                              fontSize: 13,
                              fontWeight: FontWeight.w500,
                              fontFeatures: tabular,
                              color: t.ink,
                            ),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
            ),
          ],
        ),
      );
    }

    const bars = [0.30, 0.55, 0.42, 0.80, 0.64, 1.0, 0.50];
    return SCard(
      padding: const EdgeInsets.all(20),
      child: Stack(
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              header,
              const SizedBox(height: 20),
              SizedBox(
                height: 96,
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    for (final (i, fraction) in bars.indexed) ...[
                      if (i > 0) const SizedBox(width: 6),
                      Expanded(
                        child: FractionallySizedBox(
                          heightFactor: fraction,
                          child: Shimmer(
                            height: double.infinity,
                            delay: Duration(milliseconds: i * 80),
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
          Positioned.fill(
            top: 48,
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.bottomCenter,
                  end: Alignment.topCenter,
                  colors: [
                    t.surface,
                    t.surface.withValues(alpha: 0.9),
                    t.surface.withValues(alpha: 0.4),
                  ],
                  stops: const [0, 0.55, 1],
                ),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.only(top: 48),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 40,
                  height: 40,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: t.surface,
                    shape: BoxShape.circle,
                    border: Border.all(color: t.line),
                  ),
                  child: Ico('lock', size: 16, color: t.muted),
                ),
                const SizedBox(height: 12),
                Text(
                  _error ?? 'Daily redemptions per campaign',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontFamily: sans,
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                    color: t.ink,
                  ),
                ),
                const SizedBox(height: 2),
                Text('Opens up at partner tier 1.', style: T.sub.copyWith(color: t.muted)),
                const SizedBox(height: 12),
                Btn(
                  height: 32,
                  onPressed: () => Navigator.of(context).pushReplacementNamed('/partner'),
                  child: const Text('See Partner Program'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
