import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:slopter/api.dart';
import 'package:slopter/screens/campaign.dart';
import 'package:slopter/screens/campaign_new.dart';
import 'package:slopter/screens/campaigns.dart';
import 'package:slopter/screens/home.dart';
import 'package:slopter/screens/keys.dart';
import 'package:slopter/screens/landing.dart';
import 'package:slopter/screens/login.dart';
import 'package:slopter/screens/partner.dart';
import 'package:slopter/screens/redeem.dart';
import 'package:slopter/screens/settings.dart';
import 'package:slopter/theme.dart';
import 'package:slopter/ui/kit.dart';
import 'package:slopter/ui/toast.dart';

const _me = {
  'merchant': 'Halden Coffee Co.',
  'initials': 'HC',
  'login': 'halden.co',
  'tier': 1,
  'balance': 1240.5,
  'tillUrl': 'https://till.halden.coffee/hooks/slopter',
  'keys': [
    {
      'id': 'slp_live_MKPXFH52',
      'label': 'Counter key',
      'scope': ['campaigns:read', 'campaigns:write', 'redeem', 'campaigns:analytics'],
      'active': true,
    },
    {'id': 'slp_live_SUSPEND1', 'label': 'Partner key', 'scope': ['settings:read'], 'active': false},
  ],
  'redemptions': ['SLP-LN4B-FGXB · Weekend Flat 5 · 5.00'],
};

const _campaign = {
  'id': 'cmp_s7fdq8',
  'name': 'Weekend Flat 5',
  'value': 5.0,
  'color': '#7c5cff',
  'callbackUrl': 'https://till.halden.coffee/hooks/slopter',
  'codeCount': 2,
  'usedCount': 1,
  'codes': [
    {'code': 'SLP-LN4B-FGXB', 'used': true},
    {'code': 'SLP-SGYB-6GWF', 'used': false},
  ],
};

final _responses = <String, Object>{
  '/api/me': _me,
  '/api/keys': _me['keys']!,
  '/api/campaigns': [_campaign],
  '/api/campaigns/cmp_s7fdq8': _campaign,
  '/api/campaigns/cmp_s7fdq8/analytics': {
    'id': 'cmp_s7fdq8',
    'minted': 2,
    'redeemed': 1,
    'creditMoved': 5.0,
  },
  '/api/partner': {'tier': 1, 'upgradeCode': 'SLP-PTNR-7K2Q', 'upgradeCodeUsed': false},
  '/api/settings': {'Instance name': 'slopter-demo', 'Callback timeout': '15s'},
};

http.Client _client() => MockClient((request) async {
  final body = _responses[request.url.path];
  if (body == null) return http.Response(jsonEncode({'error': 'not found'}), 404);
  return http.Response(
    jsonEncode(body),
    200,
    headers: {'content-type': 'application/json'},
  );
});

Future<void> _render(WidgetTester tester, Widget screen) async {
  await tester.pumpWidget(
    MaterialApp(
      theme: themeFor(Brightness.light),
      home: screen,
      builder: (context, child) => Stack(
        alignment: Alignment.topLeft,
        children: [child!, const ToastHost()],
      ),
    ),
  );
  for (var i = 0; i < 6; i++) {
    await tester.pump(const Duration(milliseconds: 400));
  }
  expect(tester.takeException(), isNull);
}

Future<void> _loadFonts() async {
  const families = {
    'Geist': ['Geist-400.ttf', 'Geist-500.ttf', 'Geist-600.ttf'],
    'Bricolage': ['Bricolage-500.ttf', 'Bricolage-600.ttf', 'Bricolage-700.ttf'],
    'GeistMono': ['GeistMono-400.ttf', 'GeistMono-500.ttf'],
  };
  for (final entry in families.entries) {
    final loader = FontLoader(entry.key);
    for (final file in entry.value) {
      loader.addFont(rootBundle.load('fonts/$file'));
    }
    await loader.load();
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUpAll(_loadFonts);
  setUp(() => app.me = Me.fromJson(Map<String, dynamic>.from(_me)));
  tearDown(() => app.clear());

  final screens = <String, Widget Function()>{
    'landing': Landing.new,
    'login': Login.new,
    'home': Home.new,
    'campaigns': Campaigns.new,
    'campaign': () => const CampaignDetail(id: 'cmp_s7fdq8'),
    'campaign-new': CampaignNew.new,
    'redeem': () => const Redeem(prefill: 'SLP-PTNR-7K2Q'),
    'partner': PartnerProgram.new,
    'keys': Keys.new,
    'settings': Settings.new,
  };

  for (final size in [const Size(1440, 2400), const Size(820, 2600), const Size(430, 3200)]) {
    for (final entry in screens.entries) {
      testWidgets('${entry.key} at ${size.width.toInt()}px', (tester) async {
        tester.view.physicalSize = size;
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.reset);
        await http.runWithClient(() => _render(tester, entry.value()), _client);
      });
    }
  }

  for (final entry in {
    'home': Home.new,
    'campaign': () => const CampaignDetail(id: 'cmp_s7fdq8'),
    'settings': Settings.new,
  }.entries) {
    testWidgets('${entry.key} renders its permission-denied state', (tester) async {
      tester.view.physicalSize = const Size(1440, 2400);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      await http.runWithClient(
        () => _render(tester, entry.value()),
        () => MockClient(
          (request) async => request.url.path == '/api/me'
              ? http.Response(jsonEncode(_me), 200)
              : http.Response(jsonEncode({'error': 'this key has been suspended'}), 403),
        ),
      );
    });
  }

  testWidgets('a fresh single-key account lays out', (tester) async {
    tester.view.physicalSize = const Size(1440, 2400);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    app.me = Me.fromJson({
      ..._me,
      'tier': 0,
      'tillUrl': '',
      'keys': [
        {
          'id': 'slp_live_MKPXFH52',
          'label': 'Counter key',
          'scope': ['campaigns:read', 'campaigns:write', 'redeem'],
          'active': true,
        },
      ],
      'redemptions': <String>[],
    });
    await http.runWithClient(() async {
      await _render(tester, const Keys());
      await _render(tester, const Home());
      await _render(tester, const PartnerProgram());
    }, _client);
  });

  test('voucher codes group into SLP-XXXX-XXXX', () {
    expect(formatVoucherCode('slp7q4mk2xdzzz'), 'SLP-7Q4M-K2XD');
    expect(formatVoucherCode('slp7'), 'SLP-7');
    expect(formatVoucherCode(''), '');
  });

  test('money groups thousands', () {
    expect(money(1240.5), '1,240.50');
    expect(money(7, 0), '7');
  });
}
