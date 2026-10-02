import 'package:flutter/material.dart';

import '../api.dart';
import '../icons.dart';
import '../theme.dart';
import '../ui/kit.dart';
import '../ui/shell.dart';

enum _Filter { all, active, done }

enum _Sort { name, usage, value }

class Campaigns extends StatefulWidget {
  const Campaigns({super.key});

  @override
  State<Campaigns> createState() => _CampaignsState();
}

class _CampaignsState extends State<Campaigns> {
  final _query = TextEditingController();
  _Filter _filter = _Filter.all;
  _Sort _sort = _Sort.name;
  List<Campaign>? _all;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _query.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() => _error = null);
    try {
      final list = await Api.campaigns();
      if (mounted) setState(() => _all = list);
    } on ApiError catch (e) {
      if (mounted) setState(() => _error = e.message);
    }
  }

  List<Campaign> get _rows {
    final q = _query.text.trim().toLowerCase();
    final rows = (_all ?? [])
        .where(
          (c) =>
              c.name.toLowerCase().contains(q) &&
              switch (_filter) {
                _Filter.all => true,
                _Filter.active => !c.done,
                _Filter.done => c.done,
              },
        )
        .toList();
    rows.sort(switch (_sort) {
      _Sort.name => (a, b) => a.name.toLowerCase().compareTo(b.name.toLowerCase()),
      _Sort.usage => (a, b) => b.fraction.compareTo(a.fraction),
      _Sort.value => (a, b) => b.value.compareTo(a.value),
    });
    return rows;
  }

  @override
  Widget build(BuildContext context) {
    return Shell(
      page: 'campaigns',
      builder: (context) {
        final t = Tokens.of(context);
        final padding = pagePadding(context);
        final wide = MediaQuery.sizeOf(context).width >= 768;

        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            PageHead(
              title: Text('Campaigns', style: T.hPage.copyWith(color: t.ink)),
              subtitle:
                  'Each campaign sets a discount, mints a batch of codes, and calls your till '
                  'on every redemption.',
              actions: [
                Btn(
                  kind: BtnKind.primary,
                  icon: 'plus',
                  onPressed: () => Navigator.of(context).pushNamed('/campaigns/new'),
                  child: const Text('New campaign'),
                ),
              ],
            ),
            Padding(
              padding: EdgeInsets.fromLTRB(padding.left, 0, padding.right, 16),
              child: Wrap(
                spacing: 12,
                runSpacing: 12,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: [
                  SizedBox(
                    width: 288,
                    child: Field(
                      controller: _query,
                      icon: 'search',
                      height: 40,
                      hint: 'Search campaigns',
                      onChanged: (_) => setState(() {}),
                    ),
                  ),
                  Seg<_Filter>(
                    value: _filter,
                    onChanged: (v) => setState(() => _filter = v),
                    items: const [
                      SegItem(_Filter.all, label: 'All'),
                      SegItem(_Filter.active, label: 'Active'),
                      SegItem(_Filter.done, label: 'All used'),
                    ],
                  ),
                  Seg<_Sort>(
                    value: _sort,
                    onChanged: (v) => setState(() => _sort = v),
                    items: const [
                      SegItem(_Sort.name, label: 'Name'),
                      SegItem(_Sort.usage, label: 'Usage'),
                      SegItem(_Sort.value, label: 'Discount'),
                    ],
                  ),
                ],
              ),
            ),
            Padding(
              padding: EdgeInsets.fromLTRB(padding.left, 0, padding.right, 48),
              child: SCard(
                clip: true,
                child: _error != null
                    ? EmptyState(
                        icon: 'alert',
                        title: 'Could not load campaigns',
                        description: _error,
                        action: Btn(onPressed: _load, child: const Text('Try again')),
                      )
                    : _all == null
                    ? const Loader()
                    : Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          if (wide) const _ListHead(),
                          if (_rows.isEmpty)
                            EmptyState(
                              icon: 'search',
                              title: 'No campaigns match',
                              description: 'Try a different name or filter.',
                              action: Btn(
                                onPressed: () => setState(() {
                                  _query.clear();
                                  _filter = _Filter.all;
                                }),
                                child: const Text('Clear filters'),
                              ),
                            )
                          else
                            ...stagger([
                              for (final campaign in _rows)
                                _Row(campaign: campaign, wide: wide),
                            ], step: 40),
                        ],
                      ),
              ),
            ),
          ],
        );
      },
    );
  }
}

class _ListHead extends StatelessWidget {
  const _ListHead();

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final style = TextStyle(
      fontFamily: sans,
      fontSize: 12.5,
      fontWeight: FontWeight.w500,
      color: t.muted,
    );
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
      decoration: BoxDecoration(
        color: t.raised.withValues(alpha: 0.5),
        border: Border.symmetric(horizontal: BorderSide(color: t.line)),
      ),
      child: Row(
        children: [
          Expanded(flex: 20, child: Text('Campaign', style: style)),
          const SizedBox(width: 24),
          SizedBox(width: 90, child: Text('Discount', style: style, textAlign: TextAlign.right)),
          const SizedBox(width: 24),
          Expanded(flex: 16, child: Text('Codes used', style: style)),
          const SizedBox(width: 24),
          Expanded(flex: 12, child: Text('Callback host', style: style)),
          const SizedBox(width: 24),
          SizedBox(width: 110, child: Text('Status', style: style, textAlign: TextAlign.right)),
        ],
      ),
    );
  }
}

class _Row extends StatefulWidget {
  const _Row({required this.campaign, required this.wide});

  final Campaign campaign;
  final bool wide;

  @override
  State<_Row> createState() => _RowState();
}

class _RowState extends State<_Row> {
  bool _hover = false;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final c = widget.campaign;
    return MouseRegion(
      cursor: SystemMouseCursors.click,
      onEnter: (_) => setState(() => _hover = true),
      onExit: (_) => setState(() => _hover = false),
      child: GestureDetector(
        onTap: () => Navigator.of(context).pushNamed('/campaigns/${c.id}'),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
          decoration: BoxDecoration(
            color: _hover ? t.raised.withValues(alpha: 0.7) : Colors.transparent,
            border: Border(bottom: BorderSide(color: t.line)),
          ),
          child: Row(
            children: [
              Expanded(
                flex: 20,
                child: Row(
                  children: [
                    Glyph(label: c.name, color: c.color),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            c.name,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(
                              fontFamily: sans,
                              fontSize: 14,
                              fontWeight: FontWeight.w500,
                              color: _hover ? t.accent : t.ink,
                            ),
                          ),
                          Text(c.id, style: T.m(11.5).copyWith(color: t.faint)),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 24),
              SizedBox(
                width: 90,
                child: Text(
                  money(c.value),
                  textAlign: TextAlign.right,
                  style: TextStyle(
                    fontFamily: sans,
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                    fontFeatures: tabular,
                    color: t.ink,
                  ),
                ),
              ),
              if (widget.wide) ...[
                const SizedBox(width: 24),
                Expanded(
                  flex: 16,
                  child: Row(
                    children: [
                      Expanded(
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(999),
                          child: SizedBox(
                            height: 6,
                            child: Stack(
                              children: [
                                Positioned.fill(
                                  child: ColoredBox(color: t.line.withValues(alpha: 0.7)),
                                ),
                                TweenAnimationBuilder<double>(
                                  tween: Tween(begin: 0, end: 1),
                                  duration: const Duration(milliseconds: 700),
                                  curve: easeOutSoft,
                                  builder: (context, v, _) => FractionallySizedBox(
                                    alignment: Alignment.centerLeft,
                                    widthFactor: c.fraction * v,
                                    child: ColoredBox(color: c.done ? t.faint : c.color),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      SizedBox(
                        width: 64,
                        child: Text(
                          '${c.usedCount} / ${c.codeCount}',
                          textAlign: TextAlign.right,
                          style: TextStyle(
                            fontFamily: sans,
                            fontSize: 12.5,
                            fontFeatures: tabular,
                            color: t.muted,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 24),
                Expanded(
                  flex: 12,
                  child: Text(
                    c.host,
                    overflow: TextOverflow.ellipsis,
                    style: T.m(12).copyWith(color: t.muted),
                  ),
                ),
                const SizedBox(width: 24),
                SizedBox(
                  width: 110,
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      Pill(
                        c.done ? 'All used' : 'Active',
                        kind: c.done ? PillKind.off : PillKind.ok,
                      ),
                      const SizedBox(width: 8),
                      AnimatedOpacity(
                        opacity: _hover ? 1 : 0,
                        duration: const Duration(milliseconds: 200),
                        child: Ico('chevron', size: 16, color: t.faint),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
