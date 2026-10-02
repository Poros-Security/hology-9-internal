import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../api.dart';
import '../icons.dart';
import '../theme.dart';
import '../ui/kit.dart';
import '../ui/shell.dart';
import '../ui/ticket.dart';
import '../ui/toast.dart';

class Redeem extends StatefulWidget {
  const Redeem({this.prefill, super.key});

  final String? prefill;

  @override
  State<Redeem> createState() => _RedeemState();
}

class _RedeemState extends State<Redeem> {
  final _controller = TextEditingController();
  final _focus = FocusNode();
  bool _busy = false;
  int _shake = 0;
  String? _stamp;

  @override
  void initState() {
    super.initState();
    if (widget.prefill != null) _controller.text = formatVoucherCode(widget.prefill!);
    _focus.addListener(_onFocus);
  }

  void _onFocus() => setState(() {});

  @override
  void dispose() {
    _focus.removeListener(_onFocus);
    _controller.dispose();
    _focus.dispose();
    super.dispose();
  }

  void _setCode(String raw) {
    final formatted = formatVoucherCode(raw);
    _controller.value = TextEditingValue(
      text: formatted,
      selection: TextSelection.collapsed(offset: formatted.length),
    );
    setState(() {});
  }

  int get _length => _controller.text.replaceAll('-', '').length;

  Future<void> _submit() async {
    if (_busy) return;
    final code = _controller.text;
    if (!RegExp(r'^SLP-[A-Z0-9]{4}-[A-Z0-9]{4}$').hasMatch(code)) {
      setState(() => _shake++);
      showToast(
        'That code is incomplete',
        description: 'Codes look like SLP-XXXX-XXXX.',
        kind: ToastKind.err,
      );
      return;
    }
    setState(() {
      _busy = true;
      _stamp = null;
    });
    try {
      final result = await Api.redeem(code);
      await app.load();
      if (!mounted) return;
      setState(() => _stamp = result.partnerTier ? 'Tier up' : 'Redeemed');
      showToast(
        result.partnerTier ? 'Partner tier raised' : 'Code redeemed',
        description: result.message,
      );
    } on ApiError catch (e) {
      if (!mounted) return;
      setState(() => _shake++);
      showToast('$code was not redeemed', description: e.message, kind: ToastKind.err);
    }
    if (mounted) setState(() => _busy = false);
  }

  Future<void> _paste() async {
    final data = await Clipboard.getData(Clipboard.kTextPlain);
    if (data?.text == null) {
      showToast(
        'Clipboard is blocked',
        description: 'Paste into the field with Ctrl+V instead.',
        kind: ToastKind.err,
      );
      return;
    }
    _setCode(data!.text!);
    _focus.requestFocus();
  }

  @override
  Widget build(BuildContext context) {
    return Shell(
      page: 'redeem',
      builder: (context) {
        final t = Tokens.of(context);
        final padding = pagePadding(context);
        final width = MediaQuery.sizeOf(context).width;
        final sm = width >= 640;
        final wide = width >= 1024;

        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            PageHead(
              title: Text('Redeem a code', style: T.hPage.copyWith(color: t.ink)),
              subtitle:
                  'Discount vouchers, scope vouchers and partner upgrade codes all go here.',
            ),
            Padding(
              padding: EdgeInsets.fromLTRB(padding.left, 0, padding.right, 56),
              child: wide
                  ? Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(child: _form(context, sm)),
                        const SizedBox(width: 40),
                        const SizedBox(width: 360, child: _EffectCard()),
                      ],
                    )
                  : Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        _form(context, sm),
                        const SizedBox(height: 40),
                        const _EffectCard(),
                      ],
                    ),
            ),
          ],
        );
      },
    );
  }

  Widget _form(BuildContext context, bool sm) {
    final t = Tokens.of(context);
    final acting = app.actingKey;
    final stub = sm ? 176.0 : 120.0;

    return ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 672),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Shake(
            trigger: _shake,
            child: Stack(
              clipBehavior: Clip.none,
              children: [
                Ticket(
                  stub: stub,
                  filledStub: true,
                  focused: _focus.hasFocus,
                  body: Padding(
                    padding: EdgeInsets.all(sm ? 32 : 24),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Row(
                          children: [
                            Text(
                              'Voucher code',
                              style: TextStyle(fontFamily: sans, fontSize: 13, color: t.muted),
                            ),
                            const Spacer(),
                            Text(
                              '$_length/11',
                              style: TextStyle(
                                fontFamily: sans,
                                fontSize: 12,
                                fontFeatures: tabular,
                                color: t.faint,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        TextField(
                          controller: _controller,
                          focusNode: _focus,
                          autofocus: true,
                          cursorWidth: 2,
                          cursorColor: t.accent,
                          onChanged: _setCode,
                          onSubmitted: (_) => _submit(),
                          inputFormatters: [
                            FilteringTextInputFormatter.allow(RegExp('[A-Za-z0-9-]')),
                          ],
                          style: T.m(sm ? 30 : 19).copyWith(
                            letterSpacing: (sm ? 30 : 19) * 0.14,
                            color: t.ink,
                          ),
                          decoration: InputDecoration(
                            isCollapsed: true,
                            border: InputBorder.none,
                            hintText: 'SLP-XXXX-XXXX',
                            hintStyle: T.m(sm ? 30 : 19).copyWith(
                              letterSpacing: (sm ? 30 : 19) * 0.14,
                              color: t.faint.withValues(alpha: 0.5),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  stubChild: Padding(
                    padding: EdgeInsets.all(sm ? 24 : 16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          'Applies to',
                          style: TextStyle(fontFamily: sans, fontSize: 12.5, color: t.muted),
                        ),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              acting?.id ?? 'no key',
                              style: T.m(
                                sm ? 12.5 : 11,
                                weight: FontWeight.w500,
                              ).copyWith(color: t.ink),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              acting == null
                                  ? ''
                                  : acting.active
                                  ? acting.label
                                  : 'Suspended',
                              style: TextStyle(
                                fontFamily: sans,
                                fontSize: 12,
                                color: acting?.active == false ? t.danger : t.faint,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
                if (_stamp != null)
                  Positioned(
                    right: sm ? 240 : 128,
                    bottom: -24,
                    child: Stamp(key: ValueKey(_stamp), label: _stamp!, fontSize: 20),
                  ),
              ],
            ),
          ),
          const SizedBox(height: 32),
          Wrap(
            spacing: 12,
            runSpacing: 12,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              Btn(
                kind: BtnKind.primary,
                height: 44,
                horizontal: 24,
                radius: 12,
                fontSize: 14.5,
                busy: _busy,
                onPressed: _submit,
                child: const Text('Redeem code'),
              ),
              Btn(
                height: 44,
                radius: 12,
                icon: 'copy',
                onPressed: _paste,
                child: const Text('Paste'),
              ),
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    'or press ',
                    style: TextStyle(fontFamily: sans, fontSize: 13, color: t.faint),
                  ),
                  const Kbd('Enter'),
                ],
              ),
            ],
          ),
          if (!app.can('redeem')) ...[
            const SizedBox(height: 24),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: t.warnSoft,
                borderRadius: r16,
                border: Border.all(color: t.warn.withValues(alpha: 0.2)),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Ico('lock', size: 18, color: t.warn),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      acting?.active == false
                          ? 'This key is suspended, so every redemption is rejected. '
                                'Pick another key from the menu at the top.'
                          : 'This key cannot redeem. Pick a key with the redeem permission '
                                'from the menu at the top.',
                      style: TextStyle(
                        fontFamily: sans,
                        fontSize: 13.5,
                        height: 1.5,
                        color: t.ink,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _EffectCard extends StatelessWidget {
  const _EffectCard();

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    const rows = [
      ('Discount voucher', 'Adds credit'),
      ('Scope voucher', 'Adds permissions'),
      ('Upgrade code', 'Raises tier by one'),
    ];
    return SCard(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text('What a code can do', style: T.hSec.copyWith(color: t.ink)),
          const SizedBox(height: 6),
          Text(
            'Whatever a code does, it applies to the key you are acting as.',
            style: T.sub.copyWith(color: t.muted),
          ),
          const SizedBox(height: 20),
          Container(
            decoration: BoxDecoration(borderRadius: r12, border: Border.all(color: t.line)),
            child: Column(
              children: [
                for (final (i, (label, effect)) in rows.indexed)
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
                          effect,
                          style: TextStyle(fontFamily: sans, fontSize: 13, color: t.ink),
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
}
