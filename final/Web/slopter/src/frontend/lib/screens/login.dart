import 'package:flutter/material.dart';

import '../api.dart';
import '../icons.dart';
import '../theme.dart';
import '../ui/kit.dart';
import '../ui/theme_control.dart';

class Login extends StatefulWidget {
  const Login({super.key});

  @override
  State<Login> createState() => _LoginState();
}

class _LoginState extends State<Login> {
  final _merchant = TextEditingController();
  final _password = TextEditingController();
  bool _reveal = false;
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _merchant.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await Api.login(_merchant.text.trim(), _password.text);
      await app.load();
      if (!mounted) return;
      Navigator.of(context).pushNamedAndRemoveUntil('/home', (_) => false);
      return;
    } on ApiError catch (e) {
      if (mounted) setState(() => _error = e.message);
    }
    if (mounted) setState(() => _busy = false);
  }

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final sm = MediaQuery.sizeOf(context).width >= 640;

    return Scaffold(
      backgroundColor: t.canvas,
      body: Column(
        children: [
          SizedBox(
            height: 80,
            child: Padding(
              padding: EdgeInsets.symmetric(horizontal: sm ? 32 : 20),
              child: Row(
                children: [
                  Logo(onTap: () => Navigator.of(context).pushNamed('/')),
                  const Spacer(),
                  const ThemeSeg(),
                ],
              ),
            ),
          ),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(20, 0, 20, 80),
              child: Center(
                child: SizedBox(
                  width: 400,
                  child: SCard(
                    padding: EdgeInsets.all(sm ? 36 : 28),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: stagger([
                        Align(
                          alignment: Alignment.centerLeft,
                          child: Container(
                            width: 44,
                            height: 44,
                            alignment: Alignment.center,
                            decoration: BoxDecoration(color: t.accentSoft, borderRadius: r12),
                            child: Ico('ticket', size: 24, color: t.accent),
                          ),
                        ),
                        Padding(
                          padding: const EdgeInsets.only(top: 20),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('Sign in', style: T.hPage.copyWith(color: t.ink)),
                              const SizedBox(height: 6),
                              Text(
                                'Use the merchant credentials from the challenge description.',
                                style: T.sub.copyWith(color: t.muted),
                              ),
                            ],
                          ),
                        ),
                        Padding(
                          padding: const EdgeInsets.only(top: 28),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              const FieldLabel('Merchant name'),
                              Field(
                                controller: _merchant,
                                icon: 'user',
                                autofocus: true,
                                onSubmitted: (_) => _submit(),
                              ),
                              const SizedBox(height: 20),
                              const FieldLabel('Password'),
                              Field(
                                controller: _password,
                                icon: 'lock',
                                obscure: !_reveal,
                                onSubmitted: (_) => _submit(),
                                trailing: [
                                  Btn(
                                    kind: BtnKind.ghost,
                                    height: 28,
                                    square: true,
                                    tip: _reveal ? 'Hide password' : 'Show password',
                                    onPressed: () => setState(() => _reveal = !_reveal),
                                    child: Ico(
                                      _reveal ? 'eyeoff' : 'eye',
                                      size: 16,
                                      color: t.faint,
                                    ),
                                  ),
                                ],
                              ),
                              if (_error != null) ...[
                                const SizedBox(height: 20),
                                Container(
                                  padding: const EdgeInsets.fromLTRB(12, 10, 12, 10),
                                  decoration: BoxDecoration(
                                    color: t.dangerSoft,
                                    borderRadius: r12,
                                  ),
                                  child: Row(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Padding(
                                        padding: const EdgeInsets.only(top: 1),
                                        child: Ico('alert', size: 16, color: t.danger),
                                      ),
                                      const SizedBox(width: 8),
                                      Expanded(
                                        child: Text(
                                          _error!,
                                          style: TextStyle(
                                            fontFamily: sans,
                                            fontSize: 13,
                                            height: 1.4,
                                            color: t.danger,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                              const SizedBox(height: 20),
                              Btn(
                                kind: BtnKind.primary,
                                height: 44,
                                radius: 12,
                                fontSize: 14.5,
                                expand: true,
                                busy: _busy,
                                onPressed: _submit,
                                child: const Text('Sign in'),
                              ),
                            ],
                          ),
                        ),
                      ]),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
