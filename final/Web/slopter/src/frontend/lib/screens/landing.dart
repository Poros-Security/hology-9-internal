import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../icons.dart';
import '../theme.dart';
import '../ui/kit.dart';
import '../ui/theme_control.dart';
import '../ui/ticket.dart';

class Landing extends StatelessWidget {
  const Landing({super.key});

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final width = MediaQuery.sizeOf(context).width;
    final sm = width >= 640;
    final lg = width >= 1024;
    final gutter = sm ? 32.0 : 20.0;

    return Scaffold(
      backgroundColor: t.canvas,
      body: SingleChildScrollView(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 1152),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Padding(
                  padding: EdgeInsets.symmetric(horizontal: gutter),
                  child: SizedBox(
                    height: 80,
                    child: Row(
                      children: [
                        Logo(onTap: () {}),
                        const Spacer(),
                        const ThemeSeg(),
                        const SizedBox(width: 12),
                        Btn(
                          onPressed: () => Navigator.of(context).pushNamed('/login'),
                          child: const Text('Sign in'),
                        ),
                      ],
                    ),
                  ),
                ),
                Padding(
                  padding: EdgeInsets.fromLTRB(gutter, lg ? 80 : 40, gutter, lg ? 112 : 80),
                  child: lg
                      ? Row(
                          crossAxisAlignment: CrossAxisAlignment.center,
                          children: [
                            Expanded(flex: 105, child: _Pitch(sm: sm)),
                            const SizedBox(width: 40),
                            const Expanded(flex: 100, child: _Hero()),
                          ],
                        )
                      : Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            _Pitch(sm: sm),
                            const SizedBox(height: 56),
                            const _Hero(),
                          ],
                        ),
                ),
                Container(
                  padding: EdgeInsets.fromLTRB(gutter, lg ? 64 : 56, gutter, lg ? 64 : 56),
                  decoration: BoxDecoration(border: Border(top: BorderSide(color: t.line))),
                  child: const _Benefits(),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _Pitch extends StatelessWidget {
  const _Pitch({required this.sm});

  final bool sm;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: stagger([
        Container(
          height: 28,
          padding: const EdgeInsets.only(left: 4, right: 12),
          decoration: BoxDecoration(
            color: t.surface,
            borderRadius: BorderRadius.circular(999),
            border: Border.all(color: t.line),
            boxShadow: [
              BoxShadow(
                color: t.shadow.withValues(alpha: 0.05),
                offset: const Offset(0, 1),
                blurRadius: 2,
              ),
            ],
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Pill('Live', live: true, height: 20),
              const SizedBox(width: 8),
              Flexible(
                child: Text(
                  'Till callbacks on every redemption',
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(fontFamily: sans, fontSize: 12.5, color: t.muted),
                ),
              ),
            ],
          ),
        ),
        Padding(
          padding: const EdgeInsets.only(top: 24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 460),
            child: Text(
              'Vouchers your till signs off on.',
              style: TextStyle(
                fontFamily: display,
                fontSize: sm ? 66 : 44,
                height: 0.97,
                fontWeight: FontWeight.w600,
                letterSpacing: (sm ? 66 : 44) * -0.035,
                color: t.ink,
              ),
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.only(top: 24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 480),
            child: Text(
              'Mint codes for a campaign, hand them to customers, and redeem '
              'them at the counter.',
              style: TextStyle(fontFamily: sans, fontSize: 17, height: 1.6, color: t.muted),
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.only(top: 36),
          child: Align(
            alignment: Alignment.centerLeft,
            child: Btn(
              kind: BtnKind.primary,
              height: 48,
              horizontal: 24,
              radius: 12,
              fontSize: 15,
              onPressed: () => Navigator.of(context).pushNamed('/login'),
              child: const Text('Sign in to your dashboard'),
            ),
          ),
        ),
      ]),
    );
  }
}

class _Hero extends StatefulWidget {
  const _Hero();

  @override
  State<_Hero> createState() => _HeroState();
}

class _HeroState extends State<_Hero> with TickerProviderStateMixin {
  late final AnimationController _enter = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 800),
  );
  late final AnimationController _float = AnimationController(
    vsync: this,
    duration: const Duration(seconds: 7),
  );

  @override
  void initState() {
    super.initState();
    Future.delayed(const Duration(milliseconds: 150), () {
      if (mounted) _enter.forward();
    });
    Future.delayed(const Duration(milliseconds: 1400), () {
      if (mounted) _float.repeat();
    });
  }

  @override
  void dispose() {
    _enter.dispose();
    _float.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final width = MediaQuery.sizeOf(context).width;
    final sm = width >= 640;
    final stub = sm ? 144.0 : 104.0;
    final sideInset = sm ? 40.0 : 24.0;

    return AnimatedBuilder(
      animation: _enter,
      builder: (context, child) {
        final p = easeOutSoft.transform(_enter.value);
        return Opacity(
          opacity: p,
          child: Transform.translate(offset: Offset(0, 8 * (1 - p)), child: child),
        );
      },
      child: SizedBox(
        height: sm ? 370 : 340,
        child: Stack(
          clipBehavior: Clip.none,
          children: [
            Positioned(
              left: sideInset,
              right: sideInset,
              top: 0,
              child: Transform.rotate(
                angle: 4 * 3.1415926535 / 180,
                child: Ticket(
                  stub: stub,
                  height: 230,
                  opacity: 0.7,
                  body: const SizedBox.shrink(),
                  stubChild: const SizedBox.shrink(),
                ),
              ),
            ),
            Positioned(
              left: 0,
              right: 0,
              top: 48,
              child: AnimatedBuilder(
                animation: _float,
                builder: (context, child) => Transform.translate(
                  offset: Offset(
                    0,
                    -3 + 3 * math.cos(_float.value * 2 * math.pi),
                  ),
                  child: child,
                ),
                child: Transform.rotate(
                  angle: -2 * 3.1415926535 / 180,
                  child: Stack(
                    clipBehavior: Clip.none,
                    children: [
                      Ticket(
                        stub: stub,
                        body: Padding(
                          padding: EdgeInsets.all(sm ? 28 : 24),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Row(
                                children: [
                                  Text(
                                    'Weekend Flat 5',
                                    style: TextStyle(
                                      fontFamily: sans,
                                      fontSize: 13,
                                      color: t.muted,
                                    ),
                                  ),
                                  const Spacer(),
                                  if (sm)
                                    Text(
                                      'Halden Coffee Co.',
                                      style: TextStyle(
                                        fontFamily: sans,
                                        fontSize: 13,
                                        color: t.muted,
                                      ),
                                    ),
                                ],
                              ),
                              const SizedBox(height: 20),
                              Row(
                                crossAxisAlignment: CrossAxisAlignment.baseline,
                                textBaseline: TextBaseline.alphabetic,
                                children: [
                                  Text(
                                    '5.00',
                                    style: TextStyle(
                                      fontFamily: display,
                                      fontSize: sm ? 58 : 50,
                                      height: 1,
                                      fontWeight: FontWeight.w600,
                                      letterSpacing: (sm ? 58 : 50) * -0.03,
                                      color: t.ink,
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  Text(
                                    'off',
                                    style: TextStyle(
                                      fontFamily: sans,
                                      fontSize: 22,
                                      fontWeight: FontWeight.w500,
                                      color: t.muted,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 24),
                              Text(
                                'SLP-7Q4M-K2XD',
                                style: T.m(sm ? 19 : 16).copyWith(
                                  letterSpacing: (sm ? 19 : 16) * 0.14,
                                  color: t.ink,
                                ),
                              ),
                            ],
                          ),
                        ),
                        stubChild: const Padding(
                          padding: EdgeInsets.all(20),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              _StubFact(label: 'Till reply', value: '200 OK', accent: true),
                              _StubFact(label: 'Round trip', value: '142 ms'),
                            ],
                          ),
                        ),
                      ),
                      Positioned(
                        right: sm ? 160 : 96,
                        bottom: -20,
                        child: const Stamp(
                          label: 'Redeemed',
                          sub: '01 Oct 2026',
                          delay: Duration(milliseconds: 900),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _StubFact extends StatelessWidget {
  const _StubFact({required this.label, required this.value, this.accent = false});

  final String label;
  final String value;
  final bool accent;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: TextStyle(fontFamily: sans, fontSize: 12, color: t.faint)),
        const SizedBox(height: 4),
        Text(value, style: T.m(13).copyWith(color: accent ? t.accent : t.ink)),
      ],
    );
  }
}

class _Benefits extends StatelessWidget {
  const _Benefits();

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final lg = MediaQuery.sizeOf(context).width >= 1024;
    final sm = MediaQuery.sizeOf(context).width >= 640;
    final heading = ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 260),
      child: Text(
        'Campaigns, start to finish',
        style: TextStyle(
          fontFamily: display,
          fontSize: 26,
          height: 1.2,
          fontWeight: FontWeight.w600,
          letterSpacing: -0.52,
          color: t.ink,
        ),
      ),
    );
    const items = [
      (
        'Mint a batch of codes',
        'Name the campaign, set the discount, pick how many codes you need. Print them, email '
            'them, or put them on a flyer.',
      ),
      (
        'See what is left',
        'Each campaign tracks how many codes are still out and how much discount you have '
            'handed over.',
      ),
    ];
    final cards = [
      for (final (title, body) in items)
        _BenefitCard(title: title, body: body),
    ];
    final grid = sm
        ? IntrinsicHeight(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Expanded(child: cards[0]),
                const SizedBox(width: 12),
                Expanded(child: cards[1]),
              ],
            ),
          )
        : Column(children: [cards[0], const SizedBox(height: 12), cards[1]]);

    return lg
        ? Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(flex: 10, child: heading),
              const SizedBox(width: 40),
              Expanded(flex: 24, child: grid),
            ],
          )
        : Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [heading, const SizedBox(height: 40), grid],
          );
  }
}

class _BenefitCard extends StatefulWidget {
  const _BenefitCard({required this.title, required this.body});

  final String title;
  final String body;

  @override
  State<_BenefitCard> createState() => _BenefitCardState();
}

class _BenefitCardState extends State<_BenefitCard> {
  bool _hover = false;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return MouseRegion(
      onEnter: (_) => setState(() => _hover = true),
      onExit: (_) => setState(() => _hover = false),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        transform: Matrix4.translationValues(0, _hover ? -2 : 0, 0),
        child: SCard(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(widget.title, style: T.hSec.copyWith(color: t.ink)),
              const SizedBox(height: 4),
              Text(
                widget.body,
                style: TextStyle(fontFamily: sans, fontSize: 14, height: 1.6, color: t.muted),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
