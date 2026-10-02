import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../api.dart';
import '../icons.dart';
import '../theme.dart';
import '../ui/kit.dart';
import '../ui/shell.dart';
import '../ui/ticket.dart';
import '../ui/toast.dart';

const _sampleCode = 'SLP-XXXX-XXXX';

class CampaignNew extends StatefulWidget {
  const CampaignNew({super.key});

  @override
  State<CampaignNew> createState() => _CampaignNewState();
}

class _CampaignNewState extends State<CampaignNew> {
  final _name = TextEditingController();
  final _value = TextEditingController(text: '5');
  final _count = TextEditingController(text: '10');
  final _callback = TextEditingController();
  bool _busy = false;

  @override
  void dispose() {
    _name.dispose();
    _value.dispose();
    _count.dispose();
    _callback.dispose();
    super.dispose();
  }

  String get _displayName => _name.text.trim().isEmpty ? 'Weekend Flat 5' : _name.text.trim();
  double get _amount => (double.tryParse(_value.text) ?? 0).clamp(0, 1000000);
  int get _codes => (int.tryParse(_count.text) ?? 0).clamp(0, 50);
  String get _url => _callback.text.trim();

  bool? get _urlValid {
    if (_url.isEmpty) return null;
    final parsed = Uri.tryParse(_url);
    return parsed != null && (parsed.scheme == 'http' || parsed.scheme == 'https');
  }

  void _step(TextEditingController controller, num delta, num min, num max) {
    final current = double.tryParse(controller.text) ?? 0;
    final next = (current + delta).clamp(min, max);
    controller.text = delta is int ? next.toInt().toString() : _trim(next.toDouble());
    setState(() {});
  }

  static String _trim(double v) =>
      v == v.roundToDouble() ? v.toInt().toString() : v.toStringAsFixed(1);

  Future<void> _submit() async {
    if (_busy) return;
    if (_name.text.trim().isEmpty || _codes < 1 || _urlValid != true) {
      showToast(
        'Check the form',
        description: 'Enter a name, at least one code and a full https URL.',
        kind: ToastKind.err,
      );
      return;
    }
    setState(() => _busy = true);
    try {
      await Api.createCampaign(
        name: _name.text.trim(),
        value: _amount,
        codeCount: _codes,
        callbackUrl: _url,
      );
      showToast('Campaign created', description: '$_codes codes minted for $_displayName.');
      if (!mounted) return;
      Navigator.of(context).pushReplacementNamed('/campaigns');
      return;
    } on ApiError catch (e) {
      showToast('Could not create the campaign', description: e.message, kind: ToastKind.err);
    }
    if (mounted) setState(() => _busy = false);
  }

  @override
  Widget build(BuildContext context) {
    return Shell(
      page: 'campaigns',
      builder: (context) {
        final t = Tokens.of(context);
        final padding = pagePadding(context);
        final wide = MediaQuery.sizeOf(context).width >= 1024;

        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            PageHead(
              crumb: Crumb(
                'Campaigns',
                onTap: () => Navigator.of(context).pushReplacementNamed('/campaigns'),
              ),
              title: Text('New campaign', style: T.hPage.copyWith(color: t.ink)),
            ),
            Padding(
              padding: EdgeInsets.fromLTRB(padding.left, 0, padding.right, 56),
              child: wide
                  ? Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(child: _form(context)),
                        const SizedBox(width: 32),
                        SizedBox(width: 420, child: _preview(context)),
                      ],
                    )
                  : Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [_form(context), const SizedBox(height: 32), _preview(context)],
                    ),
            ),
          ],
        );
      },
    );
  }

  Widget _form(BuildContext context) {
    final t = Tokens.of(context);
    final sm = MediaQuery.sizeOf(context).width >= 640;
    final pad = EdgeInsets.all(sm ? 28 : 24);
    final divider = Border(bottom: BorderSide(color: t.line));

    return SCard(
      clip: true,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            padding: pad,
            decoration: BoxDecoration(border: divider),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                FieldLabel(
                  'Name',
                  trailing: Text(
                    '${_name.text.length}/40',
                    style: TextStyle(
                      fontFamily: sans,
                      fontSize: 12,
                      fontFeatures: tabular,
                      color: t.faint,
                    ),
                  ),
                ),
                Field(
                  controller: _name,
                  icon: 'tag',
                  hint: 'Weekend Flat 5',
                  maxLength: 40,
                  onChanged: (_) => setState(() {}),
                ),
              ],
            ),
          ),
          Container(
            padding: pad,
            decoration: BoxDecoration(border: divider),
            child: sm
                ? Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(child: _valueField(context)),
                      const SizedBox(width: 24),
                      Expanded(child: _countField(context)),
                    ],
                  )
                : Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      _valueField(context),
                      const SizedBox(height: 24),
                      _countField(context),
                    ],
                  ),
          ),
          Container(
            padding: pad,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const FieldLabel('Callback URL'),
                Field(
                  controller: _callback,
                  icon: 'link',
                  style: T.m(13),
                  hint: 'https://till.example.com/hooks/slopter',
                  valid: _urlValid,
                  onChanged: (_) => setState(() {}),
                  trailing: [
                    if (_urlValid == true) Ico('check', size: 18, color: t.accent),
                    if (_urlValid == false) Ico('alert', size: 18, color: t.danger),
                  ],
                ),
                Hint(
                  _urlValid == false
                      ? 'Enter a full URL starting with https://'
                      : 'Your till must reply with a 2xx before a redemption goes through.',
                  color: _urlValid == false ? t.danger : null,
                ),
              ],
            ),
          ),
          Container(
            padding: EdgeInsets.symmetric(horizontal: sm ? 28 : 24, vertical: 16),
            color: t.raised.withValues(alpha: 0.5),
            child: Wrap(
              spacing: 12,
              runSpacing: 12,
              alignment: WrapAlignment.spaceBetween,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                Text.rich(
                  TextSpan(
                    style: TextStyle(fontFamily: sans, fontSize: 13, color: t.muted),
                    children: [
                      const TextSpan(text: 'Mints '),
                      TextSpan(
                        text: '$_codes',
                        style: TextStyle(
                          fontWeight: FontWeight.w500,
                          fontFeatures: tabular,
                          color: t.ink,
                        ),
                      ),
                      const TextSpan(text: ' codes worth up to '),
                      TextSpan(
                        text: money(_amount * _codes),
                        style: TextStyle(
                          fontWeight: FontWeight.w500,
                          fontFeatures: tabular,
                          color: t.ink,
                        ),
                      ),
                    ],
                  ),
                ),
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Btn(
                      onPressed: () =>
                          Navigator.of(context).pushReplacementNamed('/campaigns'),
                      child: const Text('Cancel'),
                    ),
                    const SizedBox(width: 8),
                    Btn(
                      kind: BtnKind.primary,
                      busy: _busy,
                      onPressed: _submit,
                      child: const Text('Create campaign'),
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

  Widget _valueField(BuildContext context) {
    final t = Tokens.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const FieldLabel('Discount value'),
        Field(
          controller: _value,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'[0-9.]'))],
          onChanged: (_) => setState(() {}),
          trailing: [
            Text(
              'credits',
              style: TextStyle(fontFamily: sans, fontSize: 12.5, color: t.faint),
            ),
            const SizedBox(width: 4),
            _StepButton(icon: 'minus', onTap: () => _step(_value, -0.5, 0.5, 1000000)),
            _StepButton(icon: 'plus', onTap: () => _step(_value, 0.5, 0.5, 1000000)),
          ],
        ),
        const Hint('Added to your balance each time a code is redeemed.'),
      ],
    );
  }

  Widget _countField(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const FieldLabel('Codes to mint'),
        Field(
          controller: _count,
          keyboardType: TextInputType.number,
          inputFormatters: [FilteringTextInputFormatter.digitsOnly],
          onChanged: (_) => setState(() {}),
          trailing: [
            _StepButton(icon: 'minus', onTap: () => _step(_count, -5, 1, 50)),
            _StepButton(icon: 'plus', onTap: () => _step(_count, 5, 1, 50)),
          ],
        ),
        const SizedBox(height: 10),
        Seg<int>(
          expand: true,
          value: _codes,
          onChanged: (v) => setState(() => _count.text = '$v'),
          items: const [
            SegItem(10, label: '10'),
            SegItem(20, label: '20'),
            SegItem(35, label: '35'),
            SegItem(50, label: '50'),
          ],
        ),
        const Hint('The platform mints up to 50 codes per campaign.'),
      ],
    );
  }

  Widget _preview(BuildContext context) {
    final t = Tokens.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: Text('Preview', style: T.hSec.copyWith(color: t.ink)),
        ),
        Ticket(
          stub: 104,
          filledStub: true,
          body: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  _displayName,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(fontFamily: sans, fontSize: 13, color: t.muted),
                ),
                const SizedBox(height: 12),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.baseline,
                  textBaseline: TextBaseline.alphabetic,
                  children: [
                    Text(
                      money(_amount),
                      style: TextStyle(
                        fontFamily: display,
                        fontSize: 40,
                        height: 1,
                        fontWeight: FontWeight.w600,
                        letterSpacing: -1.2,
                        color: t.ink,
                      ),
                    ),
                    const SizedBox(width: 6),
                    Text(
                      'off',
                      style: TextStyle(
                        fontFamily: sans,
                        fontSize: 16,
                        fontWeight: FontWeight.w500,
                        color: t.muted,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Text(
                  _sampleCode,
                  style: T.m(14).copyWith(letterSpacing: 1.96, color: t.ink),
                ),
              ],
            ),
          ),
          stubChild: Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  '$_codes',
                  style: TextStyle(
                    fontFamily: display,
                    fontSize: 22,
                    height: 1,
                    fontWeight: FontWeight.w600,
                    color: t.ink,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'codes',
                  style: TextStyle(fontFamily: sans, fontSize: 11.5, color: t.muted),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 24),
        Text('What your till receives', style: T.hSec.copyWith(color: t.ink)),
        const SizedBox(height: 4),
        Text(
          'Sent on every redemption. A non-2xx reply or timeout cancels it.',
          style: T.sub.copyWith(color: t.muted),
        ),
        const SizedBox(height: 12),
        _RequestPreview(
          url: _url.isEmpty ? 'https://till.example.com/hooks/slopter' : _url,
          name: _displayName,
          value: _amount,
        ),
      ],
    );
  }
}

class _StepButton extends StatelessWidget {
  const _StepButton({required this.icon, required this.onTap});

  final String icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return Btn(
      kind: BtnKind.ghost,
      height: 32,
      square: true,
      onPressed: onTap,
      child: Ico(icon, size: 16, color: t.ink),
    );
  }
}

class _RequestPreview extends StatelessWidget {
  const _RequestPreview({required this.url, required this.name, required this.value});

  final String url;
  final String name;
  final double value;

  static const _dim = Color(0xFF7F8F88);
  static const _base = Color(0xFFC9D4CF);
  static const _bright = Color(0xFFFFFFFF);
  static const _mint = Color(0xFF8FD3B8);
  static const _sand = Color(0xFFF0D28A);
  static const _lilac = Color(0xFFB9A8F5);

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final code = T.m(12.5, height: 1.7);
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: t.isDark ? t.raised : const Color(0xFF0F1714),
        borderRadius: r16,
        border: t.isDark ? Border.all(color: t.line) : null,
      ),
      child: Text.rich(
        TextSpan(
          style: code.copyWith(color: _base),
          children: [
            const TextSpan(text: 'POST ', style: TextStyle(color: _dim)),
            TextSpan(text: url, style: const TextStyle(color: _bright)),
            const TextSpan(
              text: '\nContent-Type: application/json\n\n',
              style: TextStyle(color: _dim),
            ),
            const TextSpan(text: '{\n  '),
            const TextSpan(text: '"code"', style: TextStyle(color: _mint)),
            const TextSpan(text: ': '),
            const TextSpan(text: '"$_sampleCode"', style: TextStyle(color: _sand)),
            const TextSpan(text: ',\n  '),
            const TextSpan(text: '"campaign"', style: TextStyle(color: _mint)),
            const TextSpan(text: ': '),
            TextSpan(text: '"$name"', style: const TextStyle(color: _sand)),
            const TextSpan(text: ',\n  '),
            const TextSpan(text: '"value"', style: TextStyle(color: _mint)),
            const TextSpan(text: ': '),
            TextSpan(
              text: value == value.roundToDouble()
                  ? value.toInt().toString()
                  : value.toString(),
              style: const TextStyle(color: _lilac),
            ),
            const TextSpan(text: '\n}'),
          ],
        ),
      ),
    );
  }
}
