import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../icons.dart';
import '../theme.dart';
import 'toast.dart';

enum BtnKind { normal, primary, danger, ghost }

class Btn extends StatefulWidget {
  const Btn({
    required this.child,
    this.onPressed,
    this.kind = BtnKind.normal,
    this.icon,
    this.height = 36,
    this.radius = 10,
    this.fontSize = 13.5,
    this.horizontal = 14,
    this.busy = false,
    this.expand = false,
    this.square = false,
    this.tip,
    super.key,
  });

  final Widget child;
  final VoidCallback? onPressed;
  final BtnKind kind;
  final String? icon;
  final double height;
  final double radius;
  final double fontSize;
  final double horizontal;
  final bool busy;
  final bool expand;
  final bool square;
  final String? tip;

  @override
  State<Btn> createState() => _BtnState();
}

class _BtnState extends State<Btn> {
  bool _hover = false;
  bool _down = false;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final disabled = widget.onPressed == null;
    final primary = widget.kind == BtnKind.primary;
    final danger = widget.kind == BtnKind.danger;
    final ghost = widget.kind == BtnKind.ghost;

    final foreground = primary
        ? t.onAccent
        : danger
        ? Colors.white
        : t.ink;

    Color background;
    if (primary) {
      background = t.accent;
    } else if (danger) {
      background = t.danger;
    } else if (ghost) {
      background = _hover ? t.ink.withValues(alpha: 0.05) : Colors.transparent;
    } else {
      background = _hover ? t.raised : t.surface;
    }

    final shadows = <BoxShadow>[];
    if (primary) {
      shadows.addAll([
        BoxShadow(
          color: t.shadow.withValues(alpha: 0.15),
          offset: Offset(0, _hover ? 2 : 1),
          blurRadius: _hover ? 4 : 2,
        ),
        BoxShadow(
          color: t.accent.withValues(alpha: _hover ? 0.7 : 0.55),
          offset: Offset(0, _hover ? 10 : 6),
          blurRadius: _hover ? 24 : 16,
          spreadRadius: _hover ? -8 : -6,
        ),
      ]);
    } else if (danger) {
      shadows.add(
        BoxShadow(
          color: t.danger.withValues(alpha: 0.6),
          offset: const Offset(0, 6),
          blurRadius: 16,
          spreadRadius: -6,
        ),
      );
    } else if (!ghost) {
      shadows.add(
        BoxShadow(color: t.shadow.withValues(alpha: 0.05), offset: const Offset(0, 1), blurRadius: 2),
      );
    }

    Widget label = DefaultTextStyle(
      style: TextStyle(
        fontFamily: sans,
        fontSize: widget.fontSize,
        fontWeight: FontWeight.w500,
        height: 1.2,
        color: foreground,
      ),
      child: IconTheme(
        data: IconThemeData(color: foreground),
        child: Row(
          mainAxisSize: widget.expand ? MainAxisSize.max : MainAxisSize.min,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            if (widget.icon != null) ...[
              Ico(widget.icon!, size: 16, color: primary || danger ? foreground : t.faint),
              const SizedBox(width: 8),
            ],
            widget.child,
          ],
        ),
      ),
    );

    if (widget.busy) {
      label = Stack(
        alignment: Alignment.center,
        children: [
          Opacity(opacity: 0, child: label),
          SizedBox(
            width: 16,
            height: 16,
            child: CircularProgressIndicator(strokeWidth: 2, color: foreground),
          ),
        ],
      );
    }

    Widget button = AnimatedContainer(
      duration: Duration(milliseconds: _down ? 75 : 150),
      curve: Curves.easeOut,
      transform: Matrix4.identity()
        ..translateByDouble(0, _down ? 0 : (_hover ? -1 : 0), 0, 1)
        ..scaleByDouble(_down ? 0.96 : 1, _down ? 0.96 : 1, 1, 1),
      transformAlignment: Alignment.center,
      height: widget.height,
      width: widget.square ? widget.height : null,
      padding: widget.square
          ? EdgeInsets.zero
          : EdgeInsets.symmetric(horizontal: widget.horizontal),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(widget.radius),
        border: primary || danger || ghost ? null : Border.all(color: t.line),
        boxShadow: shadows,
        gradient: primary
            ? LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  Color.alphaBlend(Colors.white.withValues(alpha: 0.12), background),
                  background,
                ],
              )
            : null,
      ),
      child: widget.expand || widget.square ? Center(child: label) : label,
    );

    Widget result = Opacity(
      opacity: disabled ? 0.4 : 1,
      child: MouseRegion(
        cursor: disabled || widget.busy
            ? SystemMouseCursors.basic
            : SystemMouseCursors.click,
        onEnter: (_) => setState(() => _hover = true),
        onExit: (_) => setState(() {
          _hover = false;
          _down = false;
        }),
        child: GestureDetector(
          onTapDown: disabled || widget.busy ? null : (_) => setState(() => _down = true),
          onTapUp: (_) => setState(() => _down = false),
          onTapCancel: () => setState(() => _down = false),
          onTap: disabled || widget.busy ? null : widget.onPressed,
          child: button,
        ),
      ),
    );

    if (widget.tip != null) result = Tip(widget.tip!, child: result);
    return widget.expand ? SizedBox(width: double.infinity, child: result) : result;
  }
}

class Tip extends StatelessWidget {
  const Tip(this.message, {required this.child, this.below = false, super.key});

  final String message;
  final Widget child;
  final bool below;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return Tooltip(
      message: message,
      waitDuration: const Duration(milliseconds: 250),
      preferBelow: below,
      verticalOffset: 18,
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(color: t.ink, borderRadius: r6),
      textStyle: TextStyle(
        fontFamily: sans,
        fontSize: 11.5,
        fontWeight: FontWeight.w500,
        color: t.surface,
      ),
      child: child,
    );
  }
}

class Panel extends StatelessWidget {
  const Panel({required this.child, this.padding, super.key});

  final Widget child;
  final EdgeInsets? padding;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return Container(
      padding: padding,
      decoration: BoxDecoration(
        color: t.raised.withValues(alpha: 0.7),
        borderRadius: r16,
        border: Border.all(color: t.line),
      ),
      child: child,
    );
  }
}

class SCard extends StatelessWidget {
  const SCard({
    required this.child,
    this.padding,
    this.clip = false,
    this.ring,
    this.ringWidth = 1,
    super.key,
  });

  final Widget child;
  final EdgeInsets? padding;
  final bool clip;
  final Color? ring;
  final double ringWidth;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return Container(
      padding: padding,
      clipBehavior: clip ? Clip.antiAlias : Clip.none,
      decoration: BoxDecoration(
        color: t.surface,
        borderRadius: r16,
        border: Border.all(color: ring ?? t.line, width: ringWidth),
        boxShadow: cardShadow(t),
      ),
      child: child,
    );
  }
}

class ScopeChip extends StatelessWidget {
  const ScopeChip(this.label, {this.color, this.background, this.border, this.strike = false, super.key});

  final String label;
  final Color? color;
  final Color? background;
  final Color? border;
  final bool strike;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return Container(
      height: 24,
      padding: const EdgeInsets.symmetric(horizontal: 8),
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: background ?? t.raised,
        borderRadius: r6,
        border: Border.all(color: border ?? t.line),
      ),
      child: Text(
        label,
        style: T.m(11.5, height: 1).copyWith(
          color: color ?? t.muted,
          decoration: strike ? TextDecoration.lineThrough : null,
        ),
      ),
    );
  }
}

enum PillKind { ok, off, bad }

class Pill extends StatefulWidget {
  const Pill(this.label, {this.kind = PillKind.ok, this.live = false, this.height = 24, super.key});

  final String label;
  final PillKind kind;
  final bool live;
  final double height;

  @override
  State<Pill> createState() => _PillState();
}

class _PillState extends State<Pill> with SingleTickerProviderStateMixin {
  AnimationController? _pulse;

  @override
  void initState() {
    super.initState();
    if (widget.live) {
      _pulse = AnimationController(vsync: this, duration: const Duration(seconds: 2))..repeat();
    }
  }

  @override
  void dispose() {
    _pulse?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final (fg, bg) = switch (widget.kind) {
      PillKind.ok => (t.accent, t.accentSoft),
      PillKind.off => (t.muted, t.raised),
      PillKind.bad => (t.danger, t.dangerSoft),
    };
    Widget dot = Container(
      width: 6,
      height: 6,
      decoration: BoxDecoration(color: fg, shape: BoxShape.circle),
    );
    if (_pulse != null) {
      dot = AnimatedBuilder(
        animation: _pulse!,
        builder: (context, child) {
          final p = Curves.easeOut.transform((_pulse!.value / 0.7).clamp(0, 1));
          return Stack(
            alignment: Alignment.center,
            clipBehavior: Clip.none,
            children: [
              Container(
                width: 6 + 12 * p,
                height: 6 + 12 * p,
                decoration: BoxDecoration(
                  color: fg.withValues(alpha: (1 - p) * 0.5),
                  shape: BoxShape.circle,
                ),
              ),
              child!,
            ],
          );
        },
        child: dot,
      );
    }
    return Container(
      height: widget.height,
      padding: const EdgeInsets.symmetric(horizontal: 10),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(999),
        border: widget.kind == PillKind.off ? Border.all(color: t.line) : null,
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          dot,
          const SizedBox(width: 6),
          Text(
            widget.label,
            style: TextStyle(
              fontFamily: sans,
              fontSize: 12,
              height: 1,
              fontWeight: FontWeight.w500,
              color: fg,
            ),
          ),
        ],
      ),
    );
  }
}

class Kbd extends StatelessWidget {
  const Kbd(this.label, {super.key});

  final String label;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return Container(
      constraints: const BoxConstraints(minWidth: 20),
      height: 20,
      padding: const EdgeInsets.symmetric(horizontal: 4),
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: t.surface,
        borderRadius: const BorderRadius.all(Radius.circular(4)),
        border: Border.all(color: t.line),
        boxShadow: [BoxShadow(color: t.line, offset: const Offset(0, 1))],
      ),
      child: Text(
        label,
        style: TextStyle(
          fontFamily: sans,
          fontSize: 11,
          height: 1,
          fontWeight: FontWeight.w500,
          color: t.muted,
        ),
      ),
    );
  }
}

class Field extends StatefulWidget {
  const Field({
    this.controller,
    this.icon,
    this.hint,
    this.height = 44,
    this.obscure = false,
    this.autofocus = false,
    this.style,
    this.trailing,
    this.keyboardType,
    this.onChanged,
    this.onSubmitted,
    this.valid,
    this.maxLength,
    this.inputFormatters,
    this.label,
    this.focusNode,
    super.key,
  });

  final TextEditingController? controller;
  final String? icon;
  final String? hint;
  final double height;
  final bool obscure;
  final bool autofocus;
  final TextStyle? style;
  final List<Widget>? trailing;
  final TextInputType? keyboardType;
  final ValueChanged<String>? onChanged;
  final ValueChanged<String>? onSubmitted;
  final bool? valid;
  final int? maxLength;
  final List<TextInputFormatter>? inputFormatters;
  final String? label;
  final FocusNode? focusNode;

  @override
  State<Field> createState() => _FieldState();
}

class _FieldState extends State<Field> {
  bool _focused = false;
  bool _hover = false;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final invalid = widget.valid == false;
    final ringColor = invalid
        ? (_focused ? t.danger : t.danger.withValues(alpha: 0.6))
        : _focused
        ? t.accent
        : widget.valid == true
        ? t.accent.withValues(alpha: 0.5)
        : _hover
        ? t.faint.withValues(alpha: 0.6)
        : t.line;
    final glow = invalid ? t.danger : t.accent;

    return MouseRegion(
      onEnter: (_) => setState(() => _hover = true),
      onExit: (_) => setState(() => _hover = false),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        height: widget.height,
        padding: const EdgeInsets.symmetric(horizontal: 12),
        decoration: BoxDecoration(
          color: t.surface,
          borderRadius: r12,
          border: Border.all(color: ringColor, width: _focused ? 2 : 1),
          boxShadow: _focused
              ? [BoxShadow(color: glow.withValues(alpha: 0.12), blurRadius: 0, spreadRadius: 5)]
              : [
                  BoxShadow(
                    color: t.shadow.withValues(alpha: 0.04),
                    offset: const Offset(0, 1),
                    blurRadius: 2,
                  ),
                ],
        ),
        child: Row(
          children: [
            if (widget.icon != null) ...[
              Ico(widget.icon!, size: 18, color: _focused ? t.accent : t.faint),
              const SizedBox(width: 8),
            ],
            Expanded(
              child: Focus(
                onFocusChange: (v) => setState(() => _focused = v),
                child: TextField(
                  controller: widget.controller,
                  focusNode: widget.focusNode,
                  obscureText: widget.obscure,
                  autofocus: widget.autofocus,
                  keyboardType: widget.keyboardType,
                  onChanged: widget.onChanged,
                  onSubmitted: widget.onSubmitted,
                  maxLength: widget.maxLength,
                  inputFormatters: widget.inputFormatters,
                  cursorWidth: 1.5,
                  cursorColor: t.accent,
                  style: (widget.style ?? T.body).copyWith(color: t.ink),
                  decoration: InputDecoration(
                    isCollapsed: true,
                    counterText: '',
                    border: InputBorder.none,
                    hintText: widget.hint,
                    hintStyle: (widget.style ?? T.body).copyWith(color: t.faint),
                  ),
                ),
              ),
            ),
            if (widget.trailing != null) ...widget.trailing!,
          ],
        ),
      ),
    );
  }
}

class FieldLabel extends StatelessWidget {
  const FieldLabel(this.text, {this.trailing, super.key});

  final String text;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Text(
            text,
            style: TextStyle(
              fontFamily: sans,
              fontSize: 13,
              fontWeight: FontWeight.w500,
              color: t.ink,
            ),
          ),
          const Spacer(),
          if (trailing != null) trailing!,
        ],
      ),
    );
  }
}

class Hint extends StatelessWidget {
  const Hint(this.text, {this.color, super.key});

  final String text;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: Text(
        text,
        style: TextStyle(fontFamily: sans, fontSize: 12.5, height: 1.45, color: color ?? t.muted),
      ),
    );
  }
}

class SegItem<V> {
  const SegItem(this.value, {this.label, this.icon, this.tip});

  final V value;
  final String? label;
  final String? icon;
  final String? tip;
}

class Seg<V> extends StatefulWidget {
  const Seg({
    required this.items,
    required this.value,
    required this.onChanged,
    this.expand = false,
    super.key,
  });

  final List<SegItem<V>> items;
  final V value;
  final ValueChanged<V> onChanged;
  final bool expand;

  @override
  State<Seg<V>> createState() => _SegState<V>();
}

class _SegState<V> extends State<Seg<V>> {
  final _keys = <int, GlobalKey>{};
  final _track = GlobalKey();
  Rect? _thumb;

  @override
  void didUpdateWidget(Seg<V> old) {
    super.didUpdateWidget(old);
    WidgetsBinding.instance.addPostFrameCallback((_) => _measure());
  }

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _measure());
  }

  void _measure() {
    if (!mounted) return;
    final index = widget.items.indexWhere((i) => i.value == widget.value);
    final box = _keys[index]?.currentContext?.findRenderObject() as RenderBox?;
    final track = _track.currentContext?.findRenderObject() as RenderBox?;
    if (box == null || track == null || !box.hasSize || !track.hasSize) return;
    final offset = box.localToGlobal(Offset.zero, ancestor: track);
    final next = Rect.fromLTWH(offset.dx, 0, box.size.width, box.size.height);
    if (next != _thumb) setState(() => _thumb = next);
  }

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final buttons = <Widget>[];
    for (var i = 0; i < widget.items.length; i++) {
      final item = widget.items[i];
      final on = item.value == widget.value;
      final key = _keys.putIfAbsent(i, GlobalKey.new);
      Widget button = _SegButton(
        key: key,
        selected: on,
        label: item.label,
        icon: item.icon,
        onTap: () => widget.onChanged(item.value),
      );
      if (item.tip != null) button = Tip(item.tip!, below: true, child: button);
      buttons.add(widget.expand ? Expanded(child: button) : button);
    }
    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: t.raised,
        borderRadius: r12,
        border: Border.all(color: t.line),
      ),
      child: Stack(
        children: [
          if (_thumb != null)
            AnimatedPositioned(
              duration: const Duration(milliseconds: 300),
              curve: spring,
              left: _thumb!.left,
              width: _thumb!.width,
              top: 0,
              bottom: 0,
              child: DecoratedBox(
                decoration: BoxDecoration(
                  color: t.surface,
                  borderRadius: r8,
                  border: Border.all(color: t.line),
                  boxShadow: [
                    BoxShadow(
                      color: t.shadow.withValues(alpha: 0.1),
                      offset: const Offset(0, 1),
                      blurRadius: 3,
                    ),
                  ],
                ),
              ),
            ),
          Row(
            key: _track,
            mainAxisSize: widget.expand ? MainAxisSize.max : MainAxisSize.min,
            children: buttons,
          ),
        ],
      ),
    );
  }
}

class _SegButton extends StatelessWidget {
  const _SegButton({
    required this.selected,
    required this.onTap,
    this.label,
    this.icon,
    super.key,
  });

  final bool selected;
  final VoidCallback onTap;
  final String? label;
  final String? icon;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final color = selected ? t.ink : t.muted;
    return MouseRegion(
      cursor: SystemMouseCursors.click,
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          height: 28,
          padding: EdgeInsets.symmetric(horizontal: icon != null ? 8 : 12),
          alignment: Alignment.center,
          color: Colors.transparent,
          child: icon != null
              ? Ico(icon!, size: 16, color: color)
              : Text(
                  label!,
                  style: TextStyle(
                    fontFamily: sans,
                    fontSize: 12.5,
                    height: 1,
                    fontWeight: FontWeight.w500,
                    color: color,
                  ),
                ),
        ),
      ),
    );
  }
}

class Toggle extends StatelessWidget {
  const Toggle({required this.value, required this.onChanged, super.key});

  final bool value;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return MouseRegion(
      cursor: SystemMouseCursors.click,
      child: GestureDetector(
        onTap: () => onChanged(!value),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          width: 36,
          height: 20,
          decoration: BoxDecoration(
            color: value ? t.accent : t.line,
            borderRadius: BorderRadius.circular(999),
          ),
          child: AnimatedAlign(
            duration: const Duration(milliseconds: 300),
            curve: spring,
            alignment: value ? Alignment.centerRight : Alignment.centerLeft,
            child: Container(
              margin: const EdgeInsets.all(2),
              width: 16,
              height: 16,
              decoration: const BoxDecoration(
                color: Colors.white,
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(color: Color(0x33000000), offset: Offset(0, 1), blurRadius: 2),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class Shimmer extends StatefulWidget {
  const Shimmer({this.width, this.height = 14, this.delay = Duration.zero, this.radius = 6, super.key});

  final double? width;
  final double height;
  final Duration delay;
  final double radius;

  @override
  State<Shimmer> createState() => _ShimmerState();
}

class _ShimmerState extends State<Shimmer> with SingleTickerProviderStateMixin {
  late final AnimationController _c = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1600),
  );

  @override
  void initState() {
    super.initState();
    Future.delayed(widget.delay, () {
      if (mounted) _c.repeat();
    });
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return Container(
      width: widget.width,
      height: widget.height,
      clipBehavior: Clip.hardEdge,
      decoration: BoxDecoration(
        color: t.raised,
        borderRadius: BorderRadius.circular(widget.radius),
        border: Border.all(color: t.line),
      ),
      child: AnimatedBuilder(
        animation: _c,
        builder: (context, _) => ShaderMask(
          blendMode: BlendMode.srcATop,
          shaderCallback: (bounds) => LinearGradient(
            begin: Alignment.centerLeft,
            end: Alignment.centerRight,
            colors: [Colors.transparent, t.ink.withValues(alpha: 0.06), Colors.transparent],
            transform: _SlideGradient(_c.value * 2 - 1),
          ).createShader(bounds),
          child: const SizedBox.expand(child: ColoredBox(color: Colors.transparent)),
        ),
      ),
    );
  }
}

class _SlideGradient extends GradientTransform {
  const _SlideGradient(this.offset);

  final double offset;

  @override
  Matrix4 transform(Rect bounds, {TextDirection? textDirection}) =>
      Matrix4.translationValues(bounds.width * offset, 0, 0);
}

class Rise extends StatefulWidget {
  const Rise({required this.child, this.delay = Duration.zero, this.distance = 8, super.key});

  final Widget child;
  final Duration delay;
  final double distance;

  @override
  State<Rise> createState() => _RiseState();
}

class _RiseState extends State<Rise> with SingleTickerProviderStateMixin {
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
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final curve = CurvedAnimation(parent: _c, curve: easeOutSoft);
    return AnimatedBuilder(
      animation: curve,
      builder: (context, child) => Opacity(
        opacity: curve.value,
        child: Transform.translate(
          offset: Offset(0, widget.distance * (1 - curve.value)),
          child: child,
        ),
      ),
      child: widget.child,
    );
  }
}

List<Widget> stagger(List<Widget> children, {int step = 45}) => [
  for (var i = 0; i < children.length; i++)
    Rise(delay: Duration(milliseconds: i * step), child: children[i]),
];

class CopyButton extends StatefulWidget {
  const CopyButton(this.text, {this.always = false, super.key});

  final String text;
  final bool always;

  @override
  State<CopyButton> createState() => _CopyButtonState();
}

class _CopyButtonState extends State<CopyButton> {
  bool _hover = false;
  bool _done = false;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return MouseRegion(
      cursor: SystemMouseCursors.click,
      onEnter: (_) => setState(() => _hover = true),
      onExit: (_) => setState(() => _hover = false),
      child: GestureDetector(
        onTap: () async {
          await Clipboard.setData(ClipboardData(text: widget.text));
          if (!mounted) return;
          setState(() => _done = true);
          showToast('Copied to clipboard', description: widget.text, kind: ToastKind.info);
          await Future.delayed(const Duration(milliseconds: 1400));
          if (mounted) setState(() => _done = false);
        },
        child: Container(
          width: 28,
          height: 28,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: _hover ? t.ink.withValues(alpha: 0.06) : Colors.transparent,
            borderRadius: r6,
          ),
          child: Ico(
            _done ? 'tick' : 'copy',
            size: 14,
            color: _done
                ? t.accent
                : _hover
                ? t.ink
                : t.faint,
          ),
        ),
      ),
    );
  }
}

class Glyph extends StatelessWidget {
  const Glyph({required this.label, required this.color, this.size = 36, this.radius = 12, super.key});

  final String label;
  final Color color;
  final double size;
  final double radius;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(radius),
        gradient: LinearGradient(
          begin: const Alignment(-0.34, -1),
          end: const Alignment(0.34, 1),
          colors: [color, color.withValues(alpha: 0.8)],
        ),
        boxShadow: [
          BoxShadow(color: Colors.white.withValues(alpha: 0.25), offset: const Offset(0, 1)),
        ],
      ),
      child: Text(
        label.isEmpty ? '?' : label.substring(0, 1).toUpperCase(),
        style: TextStyle(
          fontFamily: display,
          fontSize: size * 0.39,
          height: 1,
          fontWeight: FontWeight.w600,
          color: Colors.white,
        ),
      ),
    );
  }
}

class CountUp extends StatelessWidget {
  const CountUp(this.value, {this.decimals = 0, this.style, super.key});

  final num value;
  final int decimals;
  final TextStyle? style;

  @override
  Widget build(BuildContext context) {
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: value.toDouble()),
      duration: const Duration(milliseconds: 1100),
      curve: Curves.easeOutQuart,
      builder: (context, v, _) => Text(money(v, decimals), style: style),
    );
  }
}

String formatVoucherCode(String raw) {
  final clean = raw.toUpperCase().replaceAll(RegExp('[^A-Z0-9]'), '');
  final head = clean.length > 11 ? clean.substring(0, 11) : clean;
  return [
    if (head.isNotEmpty) head.substring(0, head.length.clamp(0, 3)),
    if (head.length > 3) head.substring(3, head.length.clamp(0, 7)),
    if (head.length > 7) head.substring(7),
  ].join('-');
}

String money(num value, [int decimals = 2]) {
  final text = value.toStringAsFixed(decimals);
  final parts = text.split('.');
  final digits = parts[0];
  final grouped = StringBuffer();
  for (var i = 0; i < digits.length; i++) {
    if (i > 0 && (digits.length - i) % 3 == 0) grouped.write(',');
    grouped.write(digits[i]);
  }
  return parts.length > 1 ? '$grouped.${parts[1]}' : grouped.toString();
}

class Shake extends StatefulWidget {
  const Shake({required this.child, required this.trigger, super.key});

  final Widget child;
  final int trigger;

  @override
  State<Shake> createState() => _ShakeState();
}

class _ShakeState extends State<Shake> with SingleTickerProviderStateMixin {
  late final AnimationController _c = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 450),
  );

  @override
  void didUpdateWidget(Shake old) {
    super.didUpdateWidget(old);
    if (old.trigger != widget.trigger) _c.forward(from: 0);
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  static const _frames = [0.0, -2.0, 4.0, -7.0, 7.0, -7.0, 7.0, -7.0, 4.0, -2.0, 0.0];

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _c,
      builder: (context, child) {
        final p = _c.value * (_frames.length - 1);
        final i = p.floor().clamp(0, _frames.length - 2);
        final dx = _frames[i] + (_frames[i + 1] - _frames[i]) * (p - i);
        return Transform.translate(offset: Offset(_c.isAnimating ? dx : 0, 0), child: child);
      },
      child: widget.child,
    );
  }
}

class EmptyState extends StatelessWidget {
  const EmptyState({
    required this.icon,
    required this.title,
    this.description,
    this.action,
    super.key,
  });

  final String icon;
  final String title;
  final String? description;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return Rise(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 64, horizontal: 24),
        child: Column(
          children: [
            Container(
              width: 48,
              height: 48,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: t.raised,
                borderRadius: r16,
                border: Border.all(color: t.line),
              ),
              child: Ico(icon, size: 20, color: t.faint),
            ),
            const SizedBox(height: 16),
            Text(
              title,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontFamily: sans,
                fontSize: 14,
                fontWeight: FontWeight.w500,
                color: t.ink,
              ),
            ),
            if (description != null) ...[
              const SizedBox(height: 4),
              Text(
                description!,
                textAlign: TextAlign.center,
                style: T.sub.copyWith(color: t.muted),
              ),
            ],
            if (action != null) ...[const SizedBox(height: 16), action!],
          ],
        ),
      ),
    );
  }
}

class Loader extends StatelessWidget {
  const Loader({super.key});

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 72),
      child: Center(
        child: SizedBox(
          width: 20,
          height: 20,
          child: CircularProgressIndicator(strokeWidth: 2, color: t.faint),
        ),
      ),
    );
  }
}
