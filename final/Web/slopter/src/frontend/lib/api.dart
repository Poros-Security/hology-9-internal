import 'dart:convert';
import 'dart:ui' show Color;

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

import 'store.dart';

const scopeDescriptions = <String, String>{
  'redeem': 'Redeem voucher codes',
  'campaigns:read': 'View campaigns and their codes',
  'campaigns:write': 'Create campaigns, edit callbacks',
  'campaigns:analytics': 'View campaign analytics',
  'settings:read': 'Read platform configuration',
};

class ApiError implements Exception {
  ApiError(this.status, this.message);

  final int status;
  final String message;

  bool get forbidden => status == 403;
  bool get unauthorized => status == 401;

  @override
  String toString() => message;
}

class ApiKey {
  ApiKey.fromJson(Map<String, dynamic> json)
    : id = '${json['id']}',
      label = '${json['label'] ?? ''}',
      scope = (json['scope'] as List? ?? const []).map((s) => '$s').toList(),
      active = json['active'] != false;

  final String id;
  final String label;
  final List<String> scope;
  final bool active;

  bool can(String permission) => active && scope.contains(permission);
  String get status => active ? 'Active' : 'Suspended';
}

class Me {
  Me.fromJson(Map<String, dynamic> json)
    : merchant = '${json['merchant']}',
      initials = '${json['initials'] ?? ''}',
      login = '${json['login'] ?? ''}',
      tier = (json['tier'] as num? ?? 0).toInt(),
      balance = (json['balance'] as num? ?? 0).toDouble(),
      tillUrl = '${json['tillUrl'] ?? ''}',
      keys = (json['keys'] as List? ?? const [])
          .map((k) => ApiKey.fromJson(k as Map<String, dynamic>))
          .toList(),
      redemptions = (json['redemptions'] as List? ?? const []).map((r) => '$r').toList();

  final String merchant;
  final String initials;
  final String login;
  final int tier;
  final double balance;
  final String tillUrl;
  final List<ApiKey> keys;
  final List<String> redemptions;
}

Color parseColor(String hex) {
  final digits = hex.replaceFirst('#', '');
  final value = int.tryParse(digits.length == 6 ? 'ff$digits' : digits, radix: 16);
  return Color(value ?? 0xFF0B7A5B);
}

class Campaign {
  Campaign.fromJson(Map<String, dynamic> json)
    : id = '${json['id']}',
      name = '${json['name']}',
      value = (json['value'] as num? ?? 0).toDouble(),
      color = parseColor('${json['color'] ?? '#0b7a5b'}'),
      callbackUrl = '${json['callbackUrl'] ?? ''}',
      codeCount = (json['codeCount'] as num? ?? 0).toInt(),
      usedCount = (json['usedCount'] as num? ?? 0).toInt(),
      codes = (json['codes'] as List? ?? const [])
          .map((c) => VoucherCode.fromJson(c as Map<String, dynamic>))
          .toList();

  final String id;
  final String name;
  final double value;
  final Color color;
  final String callbackUrl;
  final int codeCount;
  final int usedCount;
  final List<VoucherCode> codes;

  bool get done => codeCount > 0 && usedCount >= codeCount;
  int get unused => (codeCount - usedCount).clamp(0, codeCount);
  double get fraction => codeCount == 0 ? 0 : usedCount / codeCount;
  String get host {
    if (callbackUrl.isEmpty) return 'Not set';
    final parsed = Uri.tryParse(callbackUrl);
    return parsed == null || parsed.host.isEmpty ? callbackUrl : parsed.host;
  }
}

class VoucherCode {
  VoucherCode.fromJson(Map<String, dynamic> json)
    : code = '${json['code']}',
      used = json['used'] == true;

  final String code;
  final bool used;
}

class Analytics {
  Analytics.fromJson(Map<String, dynamic> json)
    : minted = (json['minted'] as num? ?? 0).toInt(),
      redeemed = (json['redeemed'] as num? ?? 0).toInt(),
      creditMoved = (json['creditMoved'] as num? ?? 0).toDouble();

  final int minted;
  final int redeemed;
  final double creditMoved;
}

class Partner {
  Partner.fromJson(Map<String, dynamic> json)
    : tier = (json['tier'] as num? ?? 0).toInt(),
      upgradeCode = '${json['upgradeCode'] ?? ''}',
      used = json['upgradeCodeUsed'] == true;

  final int tier;
  final String upgradeCode;
  final bool used;
}

class RedeemResult {
  RedeemResult.fromJson(Map<String, dynamic> json)
    : effect = '${json['effect'] ?? ''}',
      message = '${json['message'] ?? ''}';

  final String effect;
  final String message;

  bool get partnerTier => effect == 'partnerTier';
}

class Api {
  static Future<dynamic> _send(String method, String path, [Object? body]) async {
    final request = http.Request(method, Uri.parse('/api$path'));
    final acting = app.actingKey?.id;
    if (acting != null) request.headers['X-Api-Key'] = acting;
    if (body != null) {
      request.headers['Content-Type'] = 'application/json';
      request.body = jsonEncode(body);
    }
    late http.Response response;
    try {
      response = await http.Response.fromStream(await request.send());
    } catch (_) {
      throw ApiError(0, 'Could not reach the server.');
    }
    final decoded = response.body.isEmpty ? null : _tryDecode(response.body);
    if (response.statusCode >= 400) {
      throw ApiError(
        response.statusCode,
        decoded is Map && decoded['error'] != null
            ? '${decoded['error']}'
            : 'Request failed with ${response.statusCode}.',
      );
    }
    return decoded;
  }

  static dynamic _tryDecode(String body) {
    try {
      return jsonDecode(body);
    } catch (_) {
      return null;
    }
  }

  static Future<void> login(String merchant, String password) =>
      _send('POST', '/login', {'merchant': merchant, 'password': password});

  static Future<void> logout() => _send('POST', '/logout');

  static Future<Me> me() async => Me.fromJson(await _send('GET', '/me') as Map<String, dynamic>);

  static Future<String> setTillUrl(String tillUrl) async {
    final result = await _send('PATCH', '/me', {'tillUrl': tillUrl}) as Map<String, dynamic>;
    return '${result['tillUrl'] ?? ''}';
  }

  static Future<List<ApiKey>> keys() async {
    final list = await _send('GET', '/keys') as List;
    return list.map((k) => ApiKey.fromJson(k as Map<String, dynamic>)).toList();
  }

  static Future<void> narrow(String id, List<String> scope) =>
      _send('POST', '/keys/$id/narrow', {'scope': scope});

  static Future<List<Campaign>> campaigns() async {
    final list = await _send('GET', '/campaigns') as List;
    return list.map((c) => Campaign.fromJson(c as Map<String, dynamic>)).toList();
  }

  static Future<void> createCampaign({
    required String name,
    required double value,
    required int codeCount,
    required String callbackUrl,
  }) => _send('POST', '/campaigns', {
    'name': name,
    'value': value,
    'codeCount': codeCount,
    'callbackUrl': callbackUrl,
  });

  static Future<Campaign> campaign(String id) async =>
      Campaign.fromJson(await _send('GET', '/campaigns/$id') as Map<String, dynamic>);

  static Future<void> setCallback(String id, String callbackUrl) =>
      _send('PATCH', '/campaigns/$id', {'callbackUrl': callbackUrl});

  static Future<Analytics> analytics(String id) async =>
      Analytics.fromJson(await _send('GET', '/campaigns/$id/analytics') as Map<String, dynamic>);

  static Future<RedeemResult> redeem(String code) async =>
      RedeemResult.fromJson(await _send('POST', '/redeem', {'code': code}) as Map<String, dynamic>);

  static Future<Partner> partner() async =>
      Partner.fromJson(await _send('GET', '/partner') as Map<String, dynamic>);

  static Future<Map<String, String>> settings() async {
    final result = await _send('GET', '/settings') as Map;
    return {for (final entry in result.entries) '${entry.key}': '${entry.value}'};
  }
}

class AppState extends ChangeNotifier {
  static const _storedKey = 'slopter-key';

  Me? me;
  String? _actingId = storeGet(_storedKey);

  ApiKey? get actingKey {
    final keys = me?.keys;
    if (keys == null || keys.isEmpty) return null;
    return keys.firstWhere((k) => k.id == _actingId, orElse: () => keys.first);
  }

  bool can(String permission) => actingKey?.can(permission) ?? false;

  void actAs(String id) {
    _actingId = id;
    storeSet(_storedKey, id);
    notifyListeners();
  }

  Future<void> load() async {
    me = await Api.me();
    notifyListeners();
  }

  void clear() {
    me = null;
    storeRemove(_storedKey);
    _actingId = null;
    notifyListeners();
  }
}

final app = AppState();
