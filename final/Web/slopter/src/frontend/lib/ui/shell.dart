import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../api.dart';
import '../icons.dart';
import '../theme.dart';
import 'kit.dart';
import 'palette.dart';
import 'theme_control.dart';
import 'toast.dart';

const navItems = [
  ('home', 'Home', '/home', 'home', null),
  ('campaigns', 'Campaigns', '/campaigns', 'ticket', null),
  ('redeem', 'Redeem', '/redeem', 'check', null),
  ('partner', 'Partner Program', '/partner', 'trend', null),
  ('keys', 'API keys', '/keys', 'key', null),
  ('settings', 'Settings', '/settings', 'sliders', 'settings:read'),
];

bool isWide(BuildContext context) => MediaQuery.sizeOf(context).width >= 1024;

class Shell extends StatefulWidget {
  const Shell({required this.page, required this.builder, super.key});

  final String page;
  final WidgetBuilder builder;

  @override
  State<Shell> createState() => _ShellState();
}

class _ShellState extends State<Shell> {
  bool _drawer = false;
  String? _error;
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    if (app.me == null) _load();
    HardwareKeyboard.instance.addHandler(_onKey);
  }

  @override
  void dispose() {
    HardwareKeyboard.instance.removeHandler(_onKey);
    super.dispose();
  }

  bool _onKey(KeyEvent event) {
    final keyboard = HardwareKeyboard.instance;
    if (event is! KeyDownEvent ||
        event.logicalKey != LogicalKeyboardKey.keyK ||
        !(keyboard.isControlPressed || keyboard.isMetaPressed) ||
        ModalRoute.of(context)?.isCurrent != true) {
      return false;
    }
    openPalette(context);
    return true;
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await app.load();
    } on ApiError catch (e) {
      if (!mounted) return;
      if (e.unauthorized) {
        Navigator.of(context).pushNamedAndRemoveUntil('/login', (_) => false);
        return;
      }
      setState(() => _error = e.message);
    }
    if (mounted) setState(() => _loading = false);
  }

  @override
  Widget build(BuildContext context) =>
      ListenableBuilder(listenable: app, builder: _build);

  Widget _build(BuildContext context, Widget? _) {
    final t = Tokens.of(context);
    final wide = isWide(context);

    final panel = Container(
      decoration: BoxDecoration(
        color: t.surface,
        borderRadius: wide ? r16 : null,
        border: wide ? Border.all(color: t.line) : null,
        boxShadow: wide
            ? [
                BoxShadow(
                  color: t.shadow.withValues(alpha: 0.05),
                  offset: const Offset(0, 1),
                  blurRadius: 3,
                ),
              ]
            : null,
      ),
      clipBehavior: wide ? Clip.antiAlias : Clip.none,
      child: Column(
        children: [
          _Topbar(onMenu: wide ? null : () => setState(() => _drawer = true)),
          Expanded(
            child: _loading
                ? const Loader()
                : _error != null
                ? Center(
                    child: EmptyState(
                      icon: 'alert',
                      title: 'Could not load your account',
                      description: _error,
                      action: Btn(onPressed: _load, child: const Text('Try again')),
                    ),
                  )
                : app.me == null
                ? const SizedBox.shrink()
                : SingleChildScrollView(child: widget.builder(context)),
          ),
        ],
      ),
    );

    return Scaffold(
      backgroundColor: t.canvas,
      body: Stack(
        alignment: Alignment.topLeft,
        children: [
          Row(
            children: [
              if (wide) SizedBox(width: 256, child: _Sidebar(page: widget.page)),
              Expanded(
                child: Padding(
                  padding: wide
                      ? const EdgeInsets.only(top: 8, right: 8, bottom: 8)
                      : EdgeInsets.zero,
                  child: panel,
                ),
              ),
            ],
          ),
          if (!wide) ...[
            IgnorePointer(
              ignoring: !_drawer,
              child: AnimatedOpacity(
                opacity: _drawer ? 1 : 0,
                duration: const Duration(milliseconds: 300),
                child: GestureDetector(
                  onTap: () => setState(() => _drawer = false),
                  child: const ColoredBox(color: Color(0x66000000)),
                ),
              ),
            ),
            AnimatedPositioned(
              duration: const Duration(milliseconds: 300),
              curve: Curves.easeOut,
              left: _drawer ? 0 : -256,
              top: 0,
              bottom: 0,
              width: 256,
              child: _Sidebar(
                page: widget.page,
                onNavigate: () => setState(() => _drawer = false),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _Sidebar extends StatelessWidget {
  const _Sidebar({required this.page, this.onNavigate});

  final String page;
  final VoidCallback? onNavigate;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final me = app.me;
    final tier = me?.tier ?? 0;
    return ColoredBox(
      color: t.canvas,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          SizedBox(
            height: 64,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Align(
                alignment: Alignment.centerLeft,
                child: Logo(onTap: () => Navigator.of(context).pushNamed('/home')),
              ),
            ),
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  for (final (id, label, route, icon, needs) in navItems)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 2),
                      child: _NavLink(
                        label: label,
                        icon: icon,
                        active: id == page,
                        locked: needs != null && !app.can(needs),
                        needs: needs,
                        onTap: () {
                          onNavigate?.call();
                          if (id != page) Navigator.of(context).pushReplacementNamed(route);
                        },
                      ),
                    ),
                ],
              ),
            ),
          ),
          _TierCard(tier: tier, onTap: () {
            onNavigate?.call();
            if (page != 'partner') Navigator.of(context).pushReplacementNamed('/partner');
          }),
          Container(
            height: 64,
            padding: const EdgeInsets.symmetric(horizontal: 20),
            decoration: BoxDecoration(border: Border(top: BorderSide(color: t.line))),
            child: Row(
              children: [
                Container(
                  width: 32,
                  height: 32,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: t.accentSoft,
                    shape: BoxShape.circle,
                    border: Border.all(color: t.surface, width: 2),
                  ),
                  child: Text(
                    me?.initials ?? '',
                    style: TextStyle(
                      fontFamily: sans,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: t.accent,
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        me?.merchant ?? '',
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontFamily: sans,
                          fontSize: 13,
                          height: 1.2,
                          fontWeight: FontWeight.w500,
                          color: t.ink,
                        ),
                      ),
                      Text(
                        'Merchant',
                        style: TextStyle(
                          fontFamily: sans,
                          fontSize: 12,
                          height: 1.3,
                          color: t.muted,
                        ),
                      ),
                    ],
                  ),
                ),
                Btn(
                  kind: BtnKind.ghost,
                  height: 32,
                  square: true,
                  tip: 'Sign out',
                  onPressed: () => signOut(Navigator.of(context)),
                  child: Ico('logout', size: 18, color: t.faint),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

Future<void> signOut(NavigatorState navigator) async {
  try {
    await Api.logout();
  } on ApiError catch (_) {}
  app.clear();
  navigator.pushNamedAndRemoveUntil('/', (_) => false);
}

class _NavLink extends StatefulWidget {
  const _NavLink({
    required this.label,
    required this.icon,
    required this.active,
    required this.locked,
    required this.onTap,
    this.needs,
  });

  final String label;
  final String icon;
  final bool active;
  final bool locked;
  final String? needs;
  final VoidCallback onTap;

  @override
  State<_NavLink> createState() => _NavLinkState();
}

class _NavLinkState extends State<_NavLink> {
  bool _hover = false;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final color = widget.active || _hover ? t.ink : t.muted;
    return MouseRegion(
      cursor: SystemMouseCursors.click,
      onEnter: (_) => setState(() => _hover = true),
      onExit: (_) => setState(() => _hover = false),
      child: GestureDetector(
        onTap: widget.onTap,
        child: Container(
          height: 36,
          padding: const EdgeInsets.symmetric(horizontal: 12),
          decoration: BoxDecoration(
            color: widget.active
                ? t.surface
                : _hover
                ? t.ink.withValues(alpha: 0.04)
                : Colors.transparent,
            borderRadius: r10,
            border: widget.active ? Border.all(color: t.line) : null,
            boxShadow: widget.active
                ? [
                    BoxShadow(
                      color: t.shadow.withValues(alpha: 0.06),
                      offset: const Offset(0, 1),
                      blurRadius: 2,
                    ),
                  ]
                : null,
          ),
          child: Row(
            children: [
              AnimatedScale(
                scale: _hover ? 1.1 : 1,
                duration: const Duration(milliseconds: 200),
                child: Ico(
                  widget.icon,
                  size: 18,
                  color: widget.active
                      ? t.accent
                      : _hover
                      ? t.muted
                      : t.faint,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  widget.label,
                  style: TextStyle(
                    fontFamily: sans,
                    fontSize: 13.5,
                    fontWeight: FontWeight.w500,
                    color: color,
                  ),
                ),
              ),
              if (widget.locked)
                Tip(
                  'Needs ${widget.needs}',
                  child: Ico('lock', size: 14, color: t.faint),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _TierCard extends StatefulWidget {
  const _TierCard({required this.tier, required this.onTap});

  final int tier;
  final VoidCallback onTap;

  @override
  State<_TierCard> createState() => _TierCardState();
}

class _TierCardState extends State<_TierCard> {
  bool _hover = false;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final labelStyle = TextStyle(fontFamily: sans, fontSize: 11.5, color: t.faint);
    return MouseRegion(
      cursor: SystemMouseCursors.click,
      onEnter: (_) => setState(() => _hover = true),
      onExit: (_) => setState(() => _hover = false),
      child: GestureDetector(
        onTap: widget.onTap,
        child: Container(
          margin: const EdgeInsets.fromLTRB(12, 0, 12, 12),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: _hover ? t.ink.withValues(alpha: 0.04) : Colors.transparent,
            borderRadius: r12,
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.baseline,
                textBaseline: TextBaseline.alphabetic,
                children: [
                  Text(
                    'Partner tier ${widget.tier}',
                    style: TextStyle(
                      fontFamily: sans,
                      fontSize: 13,
                      fontWeight: FontWeight.w500,
                      color: t.ink,
                    ),
                  ),
                  const Spacer(),
                  Text(
                    'Upgrade',
                    style: TextStyle(
                      fontFamily: sans,
                      fontSize: 13,
                      color: _hover ? t.accent : t.faint,
                    ),
                  ),
                ],
              ),
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
                        duration: const Duration(milliseconds: 900),
                        curve: easeOutSoft,
                        builder: (context, v, _) => FractionallySizedBox(
                          alignment: Alignment.centerLeft,
                          widthFactor: (widget.tier / 2).clamp(0.03, 1) * v,
                          child: ColoredBox(color: t.accent),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('Merchant', style: labelStyle),
                  Text('Analytics', style: labelStyle),
                  Text('Partner', style: labelStyle),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Topbar extends StatelessWidget {
  const _Topbar({this.onMenu});

  final VoidCallback? onMenu;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final narrow = MediaQuery.sizeOf(context).width < 640;
    return Container(
      height: 56,
      padding: EdgeInsets.symmetric(horizontal: narrow ? 16 : 40),
      decoration: BoxDecoration(
        color: t.surface,
        border: Border(bottom: BorderSide(color: t.line)),
      ),
      child: Row(
        children: [
          if (onMenu != null) ...[
            Btn(
              kind: BtnKind.ghost,
              square: true,
              onPressed: onMenu,
              child: Ico('menu', size: 20, color: t.ink),
            ),
            const SizedBox(width: 8),
          ],
          const Flexible(child: KeyPicker()),
          const SizedBox(width: 12),
          _SearchButton(narrow: narrow),
          const Spacer(),
          const ThemeSeg(),
        ],
      ),
    );
  }
}

class _SearchButton extends StatelessWidget {
  const _SearchButton({required this.narrow});

  final bool narrow;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return Btn(
      height: 32,
      horizontal: 10,
      onPressed: () => openPalette(context),
      child: SizedBox(
        width: narrow ? 16 : 236,
        child: Row(
          children: [
            Ico('search', size: 16, color: t.faint),
            if (!narrow) ...[
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  'Search or jump to',
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontFamily: sans,
                    fontSize: 13,
                    fontWeight: FontWeight.w400,
                    color: t.muted,
                  ),
                ),
              ),
              const Kbd('Ctrl'),
              const SizedBox(width: 2),
              const Kbd('K'),
            ],
          ],
        ),
      ),
    );
  }
}

class KeyPicker extends StatelessWidget {
  const KeyPicker({super.key});

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final keys = app.me?.keys ?? const <ApiKey>[];
    final acting = app.actingKey;
    return PopupMenuButton<String>(
      tooltip: '',
      offset: const Offset(0, 38),
      position: PopupMenuPosition.under,
      color: t.surface,
      elevation: 0,
      shadowColor: Colors.transparent,
      padding: EdgeInsets.zero,
      menuPadding: const EdgeInsets.all(6),
      constraints: const BoxConstraints.tightFor(width: 340),
      shape: RoundedRectangleBorder(borderRadius: r12, side: BorderSide(color: t.line)),
      onSelected: (id) {
        app.actAs(id);
        final key = app.actingKey;
        showToast(
          'Now acting as $id',
          description: key == null
              ? null
              : '${key.label} with ${key.scope.length} '
                    'permission${key.scope.length == 1 ? '' : 's'}',
          kind: ToastKind.info,
        );
      },
      itemBuilder: (context) => [
        PopupMenuItem<String>(
          enabled: false,
          height: 30,
          padding: const EdgeInsets.symmetric(horizontal: 10),
          child: Text(
            'Act as key',
            style: TextStyle(
              fontFamily: sans,
              fontSize: 12,
              fontWeight: FontWeight.w500,
              color: t.faint,
            ),
          ),
        ),
        for (final key in keys)
          PopupMenuItem<String>(
            value: key.id,
            height: 0,
            padding: EdgeInsets.zero,
            child: _KeyMenuRow(apiKey: key, selected: key.id == acting?.id),
          ),
      ],
      child: Container(
        height: 32,
        padding: const EdgeInsets.symmetric(horizontal: 10),
        decoration: BoxDecoration(
          color: t.surface,
          borderRadius: r10,
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
            Ico('key', size: 16, color: t.faint),
            const SizedBox(width: 8),
            if (MediaQuery.sizeOf(context).width >= 1024) ...[
              Text(
                'Acting as',
                style: TextStyle(fontFamily: sans, fontSize: 13, color: t.muted),
              ),
              const SizedBox(width: 8),
            ],
            Flexible(
              child: Text(
                acting?.id ?? 'no key',
                overflow: TextOverflow.ellipsis,
                style: T.m(12.5).copyWith(color: t.ink),
              ),
            ),
            const SizedBox(width: 8),
            Ico('updown', size: 14, color: t.faint),
          ],
        ),
      ),
    );
  }
}

class _KeyMenuRow extends StatelessWidget {
  const _KeyMenuRow({required this.apiKey, required this.selected});

  final ApiKey apiKey;
  final bool selected;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            margin: const EdgeInsets.only(top: 2),
            width: 20,
            height: 20,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: selected ? t.accent : null,
              shape: BoxShape.circle,
              border: selected ? null : Border.all(color: t.line),
            ),
            child: selected ? Ico('tick', size: 12, color: t.onAccent) : null,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        apiKey.id,
                        style: T.m(12.5, weight: FontWeight.w500).copyWith(color: t.ink),
                      ),
                    ),
                    Text(
                      apiKey.active ? apiKey.label : 'Suspended',
                      style: TextStyle(
                        fontFamily: sans,
                        fontSize: 12,
                        color: apiKey.active ? t.muted : t.danger,
                      ),
                    ),
                  ],
                ),
                if (apiKey.scope.isNotEmpty) ...[
                  const SizedBox(height: 6),
                  Wrap(
                    spacing: 4,
                    runSpacing: 4,
                    children: [for (final s in apiKey.scope) ScopeChip(s)],
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class PageHead extends StatelessWidget {
  const PageHead({required this.title, this.subtitle, this.actions, this.leading, this.crumb, super.key});

  final Widget title;
  final String? subtitle;
  final List<Widget>? actions;
  final Widget? leading;
  final Widget? crumb;

  @override
  Widget build(BuildContext context) {
    final t = Tokens.of(context);
    final narrow = MediaQuery.sizeOf(context).width < 640;
    final left = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (crumb != null) crumb!,
        title,
        if (subtitle != null)
          Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Text(subtitle!, style: T.sub.copyWith(color: t.muted)),
          ),
      ],
    );
    return Padding(
      padding: EdgeInsets.fromLTRB(narrow ? 24 : 40, 36, narrow ? 24 : 40, 28),
      child: Wrap(
        spacing: 16,
        runSpacing: 16,
        alignment: WrapAlignment.spaceBetween,
        crossAxisAlignment: WrapCrossAlignment.end,
        children: [
          if (leading != null)
            Row(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [leading!, const SizedBox(width: 16), left],
            )
          else
            left,
          if (actions != null)
            Row(mainAxisSize: MainAxisSize.min, children: actions!),
        ],
      ),
    );
  }
}

class Crumb extends StatefulWidget {
  const Crumb(this.label, {required this.onTap, super.key});

  final String label;
  final VoidCallback onTap;

  @override
  State<Crumb> createState() => _CrumbState();
}

class _CrumbState extends State<Crumb> {
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
        child: Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Ico('back', size: 14, color: _hover ? t.ink : t.muted),
              const SizedBox(width: 4),
              Text(
                widget.label,
                style: TextStyle(
                  fontFamily: sans,
                  fontSize: 13,
                  color: _hover ? t.ink : t.muted,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

EdgeInsets pagePadding(BuildContext context) =>
    EdgeInsets.symmetric(horizontal: MediaQuery.sizeOf(context).width < 640 ? 24 : 40);
