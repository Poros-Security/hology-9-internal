import 'package:flutter/material.dart';

import 'screens/campaign.dart';
import 'screens/campaign_new.dart';
import 'screens/campaigns.dart';
import 'screens/home.dart';
import 'screens/keys.dart';
import 'screens/landing.dart';
import 'screens/login.dart';
import 'screens/partner.dart';
import 'screens/redeem.dart';
import 'screens/settings.dart';
import 'theme.dart';
import 'ui/theme_control.dart';
import 'ui/toast.dart';

void main() => runApp(const SlopterApp());

class SlopterApp extends StatelessWidget {
  const SlopterApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder(
      valueListenable: themeMode,
      builder: (context, mode, _) => MaterialApp(
        title: 'Slopter',
        debugShowCheckedModeBanner: false,
        themeMode: mode,
        theme: themeFor(Brightness.light),
        darkTheme: themeFor(Brightness.dark),
        initialRoute: '/',
        onGenerateRoute: _route,
        builder: (context, child) => Stack(
          alignment: Alignment.topLeft,
          children: [child ?? const SizedBox.shrink(), const ToastHost()],
        ),
      ),
    );
  }
}

Route<dynamic> _route(RouteSettings settings) {
  final name = settings.name ?? '/';
  final page = switch (name) {
    '/' => const Landing(),
    '/login' => const Login(),
    '/home' => const Home(),
    '/campaigns' => const Campaigns(),
    '/campaigns/new' => const CampaignNew(),
    '/redeem' => Redeem(prefill: settings.arguments as String?),
    '/partner' => const PartnerProgram(),
    '/keys' => const Keys(),
    '/settings' => const Settings(),
    _ when name.startsWith('/campaigns/') => CampaignDetail(id: name.substring(11)),
    _ => const Landing(),
  };
  return PageRouteBuilder(
    settings: settings,
    transitionDuration: const Duration(milliseconds: 380),
    reverseTransitionDuration: const Duration(milliseconds: 160),
    pageBuilder: (context, animation, _) => FadeTransition(
      opacity: animation,
      child: SlideTransition(
        position: Tween(
          begin: const Offset(0, 0.015),
          end: Offset.zero,
        ).chain(CurveTween(curve: easeOutSoft)).animate(animation),
        child: page,
      ),
    ),
  );
}
