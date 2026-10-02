import 'package:flutter/material.dart';

import '../icons.dart';
import '../theme.dart';

enum ToastKind { ok, err, info }

class _Toast {
  _Toast(this.title, this.description, this.kind, this.duration);

  final String title;
  final String? description;
  final ToastKind kind;
  final Duration duration;
  final key = UniqueKey();
}

final _toasts = ValueNotifier<List<_Toast>>(const []);

void showToast(
  String title, {
  String? description,
  ToastKind kind = ToastKind.ok,
  Duration duration = const Duration(milliseconds: 4500),
}) {
  _toasts.value = [..._toasts.value, _Toast(title, description, kind, duration)];
}

class ToastHost extends StatelessWidget {
  const ToastHost({super.key});

  @override
  Widget build(BuildContext context) {
    return Positioned(
      right: 16,
      bottom: 16,
      left: MediaQuery.sizeOf(context).width < 640 ? 16 : null,
      child: ValueListenableBuilder(
        valueListenable: _toasts,
        builder: (context, list, _) => Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          mainAxisSize: MainAxisSize.min,
          children: [
            for (final toast in list)
              Padding(
                key: toast.key,
                padding: const EdgeInsets.only(top: 8),
                child: _ToastCard(
                  toast,
                  onClose: () =>
                      _toasts.value = _toasts.value.where((t) => t != toast).toList(),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _ToastCard extends StatefulWidget {
  const _ToastCard(this.toast, {required this.onClose});

  final _Toast toast;
  final VoidCallback onClose;

  @override
  State<_ToastCard> createState() => _ToastCardState();
}

class _ToastCardState extends State<_ToastCard> with TickerProviderStateMixin {
  late final AnimationController _in = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 450),
  )..forward();
  late final AnimationController _bar = AnimationController(
    vsync: this,
    duration: widget.toast.duration,
  )..forward();
  late final AnimationController _out = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 300),
  );

  @override
  void initState() {
    super.initState();
    _bar.addStatusListener((status) {
      if (status == AnimationStatus.completed) _leave();
    });
  }

  Future<void> _leave() async {
    if (_out.isAnimating || _out.isCompleted) return;
    await _out.forward();
    if (mounted) widget.onClose();
  }

  @override
  void dispose() {
    _in.dispose();
    _bar.dispose();
    _out.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final toast = widget.toast;
    final (color, iconName) = switch (toast.kind) {
      ToastKind.ok => (t.accent, 'check'),
      ToastKind.err => (t.danger, 'alert'),
      ToastKind.info => (t.muted, 'info'),
    };

    return MouseRegion(
      onEnter: (_) => _bar.stop(),
      onExit: (_) {
        if (!_out.isAnimating) _bar.forward();
      },
      child: AnimatedBuilder(
        animation: Listenable.merge([_in, _out]),
        builder: (context, child) {
          final enter = const Cubic(0.2, 1.3, 0.4, 1).transform(_in.value);
          final exit = Curves.easeIn.transform(_out.value);
          return Opacity(
            opacity: (enter * (1 - exit)).clamp(0, 1),
            child: Transform.translate(
              offset: Offset(24 * exit, 16 * (1 - enter)),
              child: Transform.scale(
                scale: (0.94 + 0.06 * enter) * (1 - 0.04 * exit),
                child: child,
              ),
            ),
          );
        },
        child: Container(
          width: 360,
          clipBehavior: Clip.antiAlias,
          decoration: BoxDecoration(
            color: t.surface,
            borderRadius: r16,
            border: Border.all(color: t.line),
            boxShadow: [
              BoxShadow(
                color: t.shadow.withValues(alpha: 0.35),
                offset: const Offset(0, 20),
                blurRadius: 50,
                spreadRadius: -12,
              ),
              BoxShadow(
                color: t.shadow.withValues(alpha: 0.06),
                offset: const Offset(0, 2),
                blurRadius: 6,
              ),
            ],
          ),
          child: Stack(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 16, 40, 16),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Padding(
                      padding: const EdgeInsets.only(top: 1),
                      child: Ico(iconName, size: 20, color: color),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            toast.title,
                            style: TextStyle(
                              fontFamily: sans,
                              fontSize: 13.5,
                              fontWeight: FontWeight.w500,
                              color: t.ink,
                            ),
                          ),
                          if (toast.description != null) ...[
                            const SizedBox(height: 2),
                            Text(
                              toast.description!,
                              style: TextStyle(
                                fontFamily: sans,
                                fontSize: 13,
                                height: 1.4,
                                color: t.muted,
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              Positioned(
                top: 12,
                right: 12,
                child: _CloseButton(onTap: _leave),
              ),
              Positioned(
                left: 0,
                bottom: 0,
                child: AnimatedBuilder(
                  animation: _bar,
                  builder: (context, _) => Container(
                    width: 360 * (1 - _bar.value),
                    height: 3,
                    color: color.withValues(alpha: 0.4),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _CloseButton extends StatefulWidget {
  const _CloseButton({required this.onTap});

  final VoidCallback onTap;

  @override
  State<_CloseButton> createState() => _CloseButtonState();
}

class _CloseButtonState extends State<_CloseButton> {
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
        child: Container(
          padding: const EdgeInsets.all(4),
          decoration: BoxDecoration(
            color: _hover ? t.ink.withValues(alpha: 0.06) : Colors.transparent,
            borderRadius: r6,
          ),
          child: Ico('x', size: 16, color: _hover ? t.ink : t.faint),
        ),
      ),
    );
  }
}
