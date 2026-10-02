import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../api.dart';
import '../icons.dart';
import '../theme.dart';
import '../ui/kit.dart';
import '../ui/shell.dart';

class Home extends StatefulWidget {
  const Home({super.key});

  @override
  State<Home> createState() => _HomeState();
}

class _HomeState extends State<Home> {
  List<Campaign>? _campaigns;
  String? _campaignError;

  @override
  void initState() {
    super.initState();
    _loadCampaigns();
  }

  Future<void> _loadCampaigns() async {
    try {
      final list = await Api.campaigns();
      if (mounted) setState(() => _campaigns = list);
    } on ApiError catch (e) {
      if (mounted) setState(() => _campaignError = e.message);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Shell(
      page: 'home',
      builder: (context) {
        final t = Tokens.of(context);
        final me = app.me!;
        final width = MediaQuery.sizeOf(context).width;
        final padding = pagePadding(context);

        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            PageHead(
              title: Text(me.merchant, style: T.hPage.copyWith(color: t.ink)),
              subtitle: 'Merchant account, partner tier ${me.tier}',
              actions: [
                Btn(
                  icon: 'check',
                  onPressed: () => Navigator.of(context).pushReplacementNamed('/redeem'),
                  child: const Text('Redeem a code'),
                ),
                const SizedBox(width: 8),
                Btn(
                  kind: BtnKind.primary,
                  icon: 'plus',
                  onPressed: () => Navigator.of(context).pushNamed('/campaigns/new'),
                  child: const Text('New campaign'),
                ),
              ],
            ),
            Padding(
              padding: padding,
              child: _Stats(
                me: me,
                campaigns: _campaigns,
                campaignError: _campaignError,
              ),
            ),
            Padding(
              padding: EdgeInsets.fromLTRB(padding.left, 24, padding.right, 48),
              child: width >= 1280
                  ? Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(child: _Redemptions(entries: me.redemptions)),
                        const SizedBox(width: 16),
                        SizedBox(width: 340, child: _KeysPanel(keys: me.keys)),
                      ],
                    )
                  : Column(
                      children: [
                        _Redemptions(entries: me.redemptions),
                        const SizedBox(height: 16),
                        _KeysPanel(keys: me.keys),
                      ],
                    ),
            ),
          ],
        );
      },
    );
  }
}

class _Stats extends StatelessWidget {
  const _Stats({required this.me, required this.campaigns, required this.campaignError});

  final Me me;
  final List<Campaign>? campaigns;
  final String? campaignError;

  @override
  Widget build(BuildContext context) {
    final cards = [
      _BalanceCard(balance: me.balance),
      _TierCard(tier: me.tier),
      _UnusedCard(campaigns: campaigns, error: campaignError),
    ];
    if (MediaQuery.sizeOf(context).width < 768) {
      return Column(
        children: stagger([
          for (final card in cards) Padding(padding: const EdgeInsets.only(bottom: 16), child: card),
        ]),
      );
    }
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          for (final (i, child) in stagger(cards).indexed) ...[
            if (i > 0) const SizedBox(width: 16),
            Expanded(child: child),
          ],
        ],
      ),
    );
  }
}

class _StatShell extends StatelessWidget {
  const _StatShell({required this.child, this.onTap});

  final Widget child;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final card = SCard(padding: const EdgeInsets.all(20), child: child);
    if (onTap == null) return card;
    return _Lift(onTap: onTap!, child: card);
  }
}

class _Lift extends StatefulWidget {
  const _Lift({required this.child, required this.onTap});

  final Widget child;
  final VoidCallback onTap;

  @override
  State<_Lift> createState() => _LiftState();
}

class _LiftState extends State<_Lift> {
  bool _hover = false;

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      cursor: SystemMouseCursors.click,
      onEnter: (_) => setState(() => _hover = true),
      onExit: (_) => setState(() => _hover = false),
      child: GestureDetector(
        onTap: widget.onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 300),
          transform: Matrix4.translationValues(0, _hover ? -2 : 0, 0),
          child: widget.child,
        ),
      ),
    );
  }
}

class _StatLabel extends StatelessWidget {
  const _StatLabel(this.text, {this.icon});

  final String text;
  final String? icon;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return Row(
      children: [
        Text(text, style: TextStyle(fontFamily: sans, fontSize: 13, color: t.muted)),
        if (icon != null) ...[const SizedBox(width: 6), Ico(icon!, size: 14, color: t.faint)],
      ],
    );
  }
}

class _BalanceCard extends StatelessWidget {
  const _BalanceCard({required this.balance});

  final double balance;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return _StatShell(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const _StatLabel('Credit balance'),
          const SizedBox(height: 8),
          CountUp(balance, decimals: 2, style: T.statNum.copyWith(color: t.ink)),
          const SizedBox(height: 8),
          Text(
            'Added each time one of your codes is redeemed',
            style: TextStyle(fontFamily: sans, fontSize: 13, height: 1.4, color: t.muted),
          ),
        ],
      ),
    );
  }
}

class _TierRingPainter extends CustomPainter {
  const _TierRingPainter({
    required this.fraction,
    required this.progress,
    required this.line,
    required this.accent,
  });

  final double fraction;
  final double progress;
  final Color line;
  final Color accent;

  @override
  void paint(Canvas canvas, Size size) {
    final rect = Rect.fromCircle(
      center: size.center(Offset.zero),
      radius: size.width / 2 - 4,
    );
    canvas.drawArc(
      rect,
      0,
      math.pi * 2,
      false,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 7
        ..color = line,
    );
    final sweep = math.pi * 2 * fraction.clamp(0.02, 1) * progress;
    canvas.drawArc(
      rect,
      -math.pi / 2,
      sweep,
      false,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 7
        ..strokeCap = StrokeCap.round
        ..color = accent,
    );
  }

  @override
  bool shouldRepaint(_TierRingPainter old) =>
      old.progress != progress || old.fraction != fraction || old.accent != accent;
}

class _TierCard extends StatelessWidget {
  const _TierCard({required this.tier});

  final int tier;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return _StatShell(
      onTap: () => Navigator.of(context).pushReplacementNamed('/partner'),
      child: Row(
        children: [
          TweenAnimationBuilder<double>(
            tween: Tween(begin: 0, end: 1),
            duration: const Duration(milliseconds: 1000),
            curve: easeOutSoft,
            builder: (context, v, _) => CustomPaint(
              size: const Size(84, 84),
              painter: _TierRingPainter(
                fraction: tier / 2,
                progress: v,
                line: t.line,
                accent: t.accent,
              ),
            ),
          ),
          const SizedBox(width: 20),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const _StatLabel('Partner tier'),
                const SizedBox(height: 8),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.baseline,
                  textBaseline: TextBaseline.alphabetic,
                  children: [
                    Text('$tier', style: T.statNum.copyWith(color: t.ink)),
                    const SizedBox(width: 6),
                    Text(
                      'of 2',
                      style: TextStyle(
                        fontFamily: sans,
                        fontSize: 15,
                        fontWeight: FontWeight.w500,
                        color: t.muted,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Flexible(
                      child: Text(
                        tier == 0
                            ? 'Tier 1 adds analytics'
                            : tier == 1
                            ? 'Tier 2 adds a settings key'
                            : 'Top tier reached',
                        style: TextStyle(
                          fontFamily: sans,
                          fontSize: 13,
                          fontWeight: FontWeight.w500,
                          color: t.accent,
                        ),
                      ),
                    ),
                    const SizedBox(width: 4),
                    Ico('chevron', size: 14, color: t.accent),
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

class _UnusedCard extends StatelessWidget {
  const _UnusedCard({required this.campaigns, required this.error});

  final List<Campaign>? campaigns;
  final String? error;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    if (error != null) {
      return _StatShell(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const _StatLabel('Unused codes', icon: 'lock'),
            const SizedBox(height: 12),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Padding(
                  padding: const EdgeInsets.only(top: 1),
                  child: Ico('alert', size: 16, color: t.warn),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    error!,
                    style: TextStyle(
                      fontFamily: sans,
                      fontSize: 13,
                      height: 1.4,
                      color: t.muted,
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      );
    }
    final list = campaigns;
    if (list == null) {
      return const _StatShell(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _StatLabel('Unused codes'),
            SizedBox(height: 12),
            Shimmer(width: 90, height: 30, radius: 8),
            SizedBox(height: 16),
            Shimmer(height: 8, radius: 999),
          ],
        ),
      );
    }
    final live = list.where((c) => !c.done).toList();
    final total = list.fold<int>(0, (sum, c) => sum + c.unused);
    return _StatShell(
      onTap: () => Navigator.of(context).pushReplacementNamed('/campaigns'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const _StatLabel('Unused codes'),
          const SizedBox(height: 8),
          CountUp(total, style: T.statNum.copyWith(color: t.ink)),
          const SizedBox(height: 16),
          ClipRRect(
            borderRadius: BorderRadius.circular(999),
            child: SizedBox(
              height: 8,
              child: Row(
                children: [
                  for (final c in live)
                    Expanded(
                      flex: math.max(c.unused, 1),
                      child: Padding(
                        padding: const EdgeInsets.only(right: 2),
                        child: TweenAnimationBuilder<double>(
                          tween: Tween(begin: 0, end: 1),
                          duration: const Duration(milliseconds: 800),
                          curve: easeOutSoft,
                          builder: (context, v, _) => FractionallySizedBox(
                            alignment: Alignment.centerLeft,
                            widthFactor: v,
                            child: ColoredBox(color: c.color),
                          ),
                        ),
                      ),
                    ),
                  if (live.isEmpty) Expanded(child: ColoredBox(color: t.line)),
                ],
              ),
            ),
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 12,
            runSpacing: 4,
            children: [
              for (final c in live)
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 8,
                      height: 8,
                      decoration: BoxDecoration(color: c.color, shape: BoxShape.circle),
                    ),
                    const SizedBox(width: 6),
                    Text(
                      c.name,
                      style: TextStyle(fontFamily: sans, fontSize: 12, color: t.muted),
                    ),
                  ],
                ),
              if (live.isEmpty)
                Text(
                  'Every code has been redeemed.',
                  style: TextStyle(fontFamily: sans, fontSize: 12, color: t.muted),
                ),
            ],
          ),
        ],
      ),
    );
  }
}

class _PanelHead extends StatelessWidget {
  const _PanelHead({required this.title, required this.action, this.live = false});

  final String title;
  final Widget action;
  final bool live;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return Container(
      height: 56,
      padding: const EdgeInsets.symmetric(horizontal: 20),
      decoration: BoxDecoration(border: Border(bottom: BorderSide(color: t.line))),
      child: Row(
        children: [
          Flexible(
            child: Text(
              title,
              overflow: TextOverflow.ellipsis,
              style: T.hSec.copyWith(color: t.ink),
            ),
          ),
          if (live) ...[const SizedBox(width: 8), const Pill('Live', live: true, height: 20)],
          const Spacer(),
          action,
        ],
      ),
    );
  }
}

class _Redemptions extends StatelessWidget {
  const _Redemptions({required this.entries});

  final List<String> entries;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return SCard(
      clip: true,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _PanelHead(
            title: 'Recent redemptions',
            live: true,
            action: Btn(
              kind: BtnKind.ghost,
              height: 32,
              onPressed: () => Navigator.of(context).pushReplacementNamed('/campaigns'),
              child: Text(
                'View campaigns',
                style: TextStyle(fontFamily: sans, fontSize: 13.5, color: t.muted),
              ),
            ),
          ),
          if (entries.isEmpty)
            const EmptyState(
              icon: 'ticket',
              title: 'Nothing redeemed yet',
              description: 'Redeemed codes show up here.',
            )
          else
            Column(
              children: stagger([
                for (final (i, entry) in entries.indexed)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
                    decoration: BoxDecoration(
                      border: i == entries.length - 1
                          ? null
                          : Border(bottom: BorderSide(color: t.line)),
                    ),
                    child: Row(
                      children: [
                        Container(
                          width: 36,
                          height: 36,
                          alignment: Alignment.center,
                          decoration: BoxDecoration(color: t.accentSoft, borderRadius: r12),
                          child: Ico('tick', size: 16, color: t.accent),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Text(
                            entry,
                            style: T.m(13).copyWith(letterSpacing: 0.2, color: t.ink),
                          ),
                        ),
                      ],
                    ),
                  ),
              ]),
            ),
        ],
      ),
    );
  }
}

class _KeysPanel extends StatelessWidget {
  const _KeysPanel({required this.keys});

  final List<ApiKey> keys;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return SCard(
      clip: true,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _PanelHead(
            title: 'API keys',
            action: Btn(
              kind: BtnKind.ghost,
              height: 32,
              onPressed: () => Navigator.of(context).pushReplacementNamed('/keys'),
              child: Text(
                'Manage',
                style: TextStyle(fontFamily: sans, fontSize: 13.5, color: t.muted),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(8),
            child: Column(
              children: stagger([
                for (final key in keys)
                  Opacity(
                    opacity: key.active ? 1 : 0.55,
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Row(
                            children: [
                              Container(
                                width: 36,
                                height: 36,
                                alignment: Alignment.center,
                                decoration: BoxDecoration(
                                  color: key.active ? t.accentSoft : t.dangerSoft,
                                  borderRadius: r12,
                                ),
                                child: Ico(
                                  'key',
                                  size: 16,
                                  color: key.active ? t.accent : t.danger,
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      children: [
                                        Flexible(
                                          child: Text(
                                            key.id,
                                            overflow: TextOverflow.ellipsis,
                                            style: T.m(
                                              13,
                                              weight: FontWeight.w500,
                                            ).copyWith(color: t.ink),
                                          ),
                                        ),
                                        CopyButton(key.id),
                                      ],
                                    ),
                                    Text(
                                      key.label,
                                      style: TextStyle(
                                        fontFamily: sans,
                                        fontSize: 12.5,
                                        color: t.muted,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              Pill(
                                key.status,
                                kind: key.active ? PillKind.ok : PillKind.bad,
                              ),
                            ],
                          ),
                          if (key.scope.isNotEmpty)
                            Padding(
                              padding: const EdgeInsets.only(left: 48, top: 10),
                              child: Wrap(
                                spacing: 4,
                                runSpacing: 4,
                                children: [for (final s in key.scope) ScopeChip(s)],
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),
              ]),
            ),
          ),
        ],
      ),
    );
  }
}
