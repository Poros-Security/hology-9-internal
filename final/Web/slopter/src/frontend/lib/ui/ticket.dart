import 'package:flutter/material.dart';

import '../theme.dart';

const _notch = 10.0;
const _radius = 16.0;

Path _ticketPath(Size size, double stub) {
  final body = Path()
    ..addRRect(
      RRect.fromRectAndRadius(Offset.zero & size, const Radius.circular(_radius)),
    );
  final x = size.width - stub;
  final holes = Path()
    ..addOval(Rect.fromCircle(center: Offset(x, 0), radius: _notch))
    ..addOval(Rect.fromCircle(center: Offset(x, size.height), radius: _notch));
  return Path.combine(PathOperation.difference, body, holes);
}

class TicketClipper extends CustomClipper<Path> {
  const TicketClipper(this.stub);

  final double stub;

  @override
  Path getClip(Size size) => _ticketPath(size, stub);

  @override
  bool shouldReclip(TicketClipper old) => old.stub != stub;
}

class _TicketOutline extends CustomPainter {
  const _TicketOutline(this.stub, this.line, this.ring, this.ringWidth);

  final double stub;
  final Color line;
  final Color ring;
  final double ringWidth;

  @override
  void paint(Canvas canvas, Size size) {
    final inset = ringWidth / 2;
    final outline = _ticketPath(
      Size(size.width - ringWidth, size.height - ringWidth),
      stub - inset,
    ).shift(Offset(inset, inset));
    canvas.drawPath(
      outline,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = ringWidth
        ..color = ring,
    );

    final x = size.width - stub;
    const dash = 5.0;
    const gap = 4.0;
    final perforation = Paint()
      ..strokeWidth = 2
      ..color = line
      ..strokeCap = StrokeCap.butt;
    for (var y = _notch + 1; y < size.height - _notch - 1; y += dash + gap) {
      canvas.drawLine(
        Offset(x - 1, y),
        Offset(x - 1, (y + dash).clamp(0, size.height - _notch - 1)),
        perforation,
      );
    }
  }

  @override
  bool shouldRepaint(_TicketOutline old) =>
      old.stub != stub || old.line != line || old.ring != ring || old.ringWidth != ringWidth;
}

class _TicketShadow extends CustomPainter {
  const _TicketShadow(this.stub, this.dark);

  final double stub;
  final bool dark;

  @override
  void paint(Canvas canvas, Size size) {
    final path = _ticketPath(size, stub);
    if (dark) {
      canvas.drawPath(
        path.shift(const Offset(0, 14)),
        Paint()
          ..color = const Color(0xFF000000).withValues(alpha: 0.55)
          ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 15),
      );
      return;
    }
    canvas.drawPath(
      path.shift(const Offset(0, 14)),
      Paint()
        ..color = const Color(0xFF101814).withValues(alpha: 0.12)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 15),
    );
    canvas.drawPath(
      path.shift(const Offset(0, 1)),
      Paint()
        ..color = const Color(0xFF101814).withValues(alpha: 0.06)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 1),
    );
  }

  @override
  bool shouldRepaint(_TicketShadow old) => old.stub != stub || old.dark != dark;
}

class Ticket extends StatelessWidget {
  const Ticket({
    required this.stub,
    required this.body,
    required this.stubChild,
    this.height,
    this.filledStub = false,
    this.focused = false,
    this.shadow = true,
    this.opacity = 1,
    super.key,
  });

  final double stub;
  final Widget body;
  final Widget stubChild;
  final double? height;
  final bool filledStub;
  final bool focused;
  final bool shadow;
  final double opacity;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final ringWidth = focused ? 2.0 : 1.0;
    final ring = focused ? t.accent.withValues(alpha: 0.5) : t.line;

    final content = Stack(
      children: [
        ClipPath(
          clipper: TicketClipper(stub),
          child: Container(
            height: height,
            color: t.surface,
            child: IntrinsicHeight(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Expanded(child: body),
                  Container(
                    width: stub,
                    color: filledStub ? t.raised.withValues(alpha: 0.6) : null,
                    child: stubChild,
                  ),
                ],
              ),
            ),
          ),
        ),
        Positioned.fill(
          child: IgnorePointer(
            child: CustomPaint(painter: _TicketOutline(stub, t.line, ring, ringWidth)),
          ),
        ),
      ],
    );

    final layered = shadow
        ? Stack(
            children: [
              Positioned.fill(
                child: IgnorePointer(child: CustomPaint(painter: _TicketShadow(stub, t.isDark))),
              ),
              content,
            ],
          )
        : content;

    return opacity == 1 ? layered : Opacity(opacity: opacity, child: layered);
  }
}

class Stamp extends StatefulWidget {
  const Stamp({required this.label, this.sub, this.fontSize = 17, this.delay = Duration.zero, super.key});

  final String label;
  final String? sub;
  final double fontSize;
  final Duration delay;

  @override
  State<Stamp> createState() => _StampState();
}

class _StampState extends State<Stamp> with SingleTickerProviderStateMixin {
  late final AnimationController _c = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 500),
  );

  @override
  void initState() {
    super.initState();
    Future.delayed(widget.delay, () {
      if (mounted) _c.forward();
    });
  }

  @override
  void didUpdateWidget(Stamp old) {
    super.didUpdateWidget(old);
    if (old.label != widget.label) _c.forward(from: 0);
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return AnimatedBuilder(
      animation: _c,
      builder: (context, child) {
        final p = const Cubic(0.2, 1.6, 0.4, 1).transform(_c.value);
        return Opacity(
          opacity: _c.value.clamp(0, 1),
          child: Transform.scale(scale: 2.4 - 1.4 * p, child: child),
        );
      },
      child: Transform.rotate(
        angle: -9 * 3.1415926535 / 180,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            color: t.surface.withValues(alpha: 0.78),
            borderRadius: r6,
            border: Border.all(color: t.accent, width: 2),
            boxShadow: [
              BoxShadow(color: t.accent.withValues(alpha: 0.5), spreadRadius: 3),
              BoxShadow(color: t.surface.withValues(alpha: 0.78), spreadRadius: 2),
            ],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                widget.label.toUpperCase(),
                style: TextStyle(
                  fontFamily: display,
                  fontSize: widget.fontSize,
                  height: 1,
                  fontWeight: FontWeight.w700,
                  letterSpacing: widget.fontSize * 0.12,
                  color: t.accent,
                ),
              ),
              if (widget.sub != null) ...[
                const SizedBox(height: 4),
                Text(
                  widget.sub!.toUpperCase(),
                  style: TextStyle(
                    fontFamily: display,
                    fontSize: 9,
                    height: 1,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 1.8,
                    color: t.accent,
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
