import 'dart:convert';
import 'dart:math';

import 'package:http/http.dart' as http;
import 'package:shelf/shelf.dart';
import 'package:shelf_router/shelf_router.dart';

import 'store.dart';

const sessionCookie = 'slopter_session';
const callbackTimeout = Duration(seconds: 15);

Handler buildApi(Store store) {
  final api = Api(store);
  final router = Router()
    ..post('/api/login', api.login)
    ..post('/api/logout', api.logout)
    ..get('/api/me', api.me)
    ..patch('/api/me', api.updateTill)
    ..get('/api/keys', api.keys)
    ..post('/api/keys/<id>/narrow', api.narrow)
    ..get('/api/partner', api.partner)
    ..get('/api/campaigns', api.campaigns)
    ..post('/api/campaigns', api.createCampaign)
    ..get('/api/campaigns/<id>', api.campaign)
    ..patch('/api/campaigns/<id>', api.updateCampaign)
    ..get('/api/campaigns/<id>/analytics', api.analytics)
    ..post('/api/redeem', api.redeem)
    ..get('/api/settings', api.settings);

  return Pipeline().addMiddleware(_jsonErrors).addHandler(router.call);
}

class Api {
  Api(this.store);

  final Store store;

  Future<Response> login(Request request) async {
    final body = await _body(request);
    final merchant = store.authenticate(
        _string(body['merchant']), _string(body['password']));
    if (merchant == null) return _error(401, 'wrong merchant name or password');

    final session = store.openSession(merchant);
    return _json({'merchant': merchant.name}, headers: {
      'set-cookie': '$sessionCookie=$session; Path=/; HttpOnly; SameSite=Lax',
    });
  }

  Response logout(Request request) {
    store.sessions.remove(_sessionId(request));
    return _json({'ok': true}, headers: {
      'set-cookie': '$sessionCookie=; Path=/; HttpOnly; Max-Age=0',
    });
  }

  Response me(Request request) {
    final merchant = _merchant(request);
    if (merchant == null) return _noSession;
    return _json({
      'merchant': merchant.name,
      'initials': merchant.initials,
      'login': merchant.login,
      'tier': merchant.tier,
      'balance': merchant.balance,
      'tillUrl': merchant.tillUrl,
      'keys': merchant.keys.map(_keyJson).toList(),
      'redemptions': merchant.redemptions.take(5).toList(),
    });
  }

  Future<Response> updateTill(Request request) async {
    final merchant = _merchant(request);
    if (merchant == null) return _noSession;
    final body = await _body(request);
    merchant.tillUrl = _string(body['tillUrl']);
    return _json({'tillUrl': merchant.tillUrl});
  }

  Response keys(Request request) {
    final merchant = _merchant(request);
    if (merchant == null) return _noSession;
    return _json(merchant.keys.map(_keyJson).toList());
  }

  Future<Response> narrow(Request request, String id) async {
    final merchant = _merchant(request);
    if (merchant == null) return _noSession;

    final key = merchant.keyById(id);
    if (key == null) return _error(404, 'no such key');

    final body = await _body(request);
    final next = _stringList(body['scope']);
    if (next.any((p) => !allPermissions.contains(p))) {
      return _error(400, 'unknown permission');
    }
    if (next.isEmpty) return _error(400, 'a key needs at least one permission');
    if (!key.grant.admitsAsNarrowing(next)) {
      return _error(400, 'new scope must be a strict subset of the current scope');
    }

    key.grant.replaceScope(next);
    return _json(_keyJson(key));
  }

  Response partner(Request request) {
    final merchant = _merchant(request);
    if (merchant == null) return _noSession;
    final upgrade = store.vouchers[merchant.upgradeCode]!;
    return _json({
      'tier': merchant.tier,
      'upgradeCode': merchant.upgradeCode,
      'upgradeCodeUsed': upgrade.used,
    });
  }

  Response campaigns(Request request) => _scoped(request, 'campaigns:read',
      (merchant, key) => _json(merchant.campaigns.map(_campaignJson).toList()));

  Future<Response> createCampaign(Request request) async {
    final body = await _body(request);
    return _scoped(request, 'campaigns:write', (merchant, key) {
      final name = _string(body['name']);
      final value = body['value'] is num ? body['value'] as num : 0;
      final codeCount = body['codeCount'] is num
          ? min(50, max(1, (body['codeCount'] as num).toInt()))
          : 1;
      if (name.isEmpty) return _error(400, 'campaign needs a name');
      if (merchant.campaigns.length >= 25) {
        return _error(400, 'campaign limit reached');
      }

      final campaign = store.createCampaign(
          merchant, name, value, codeCount, _string(body['callbackUrl']));
      return _json(_campaignDetailJson(campaign));
    });
  }

  Response campaign(Request request, String id) =>
      _scoped(request, 'campaigns:read', (merchant, key) {
        final campaign = merchant.campaignById(id);
        if (campaign == null) return _error(404, 'no such campaign');
        return _json(_campaignDetailJson(campaign));
      });

  Future<Response> updateCampaign(Request request, String id) async {
    final body = await _body(request);
    return _scoped(request, 'campaigns:write', (merchant, key) {
      final campaign = merchant.campaignById(id);
      if (campaign == null) return _error(404, 'no such campaign');
      campaign.callbackUrl = _string(body['callbackUrl']);
      return _json(_campaignDetailJson(campaign));
    });
  }

  Response analytics(Request request, String id) =>
      _scoped(request, 'campaigns:analytics', (merchant, key) {
        final campaign = merchant.campaignById(id);
        if (campaign == null) return _error(404, 'no such campaign');
        return _json({
          'id': campaign.id,
          'minted': campaign.codes.length,
          'redeemed': campaign.usedCount,
          'creditMoved': campaign.usedCount * campaign.value,
        });
      });

  Future<Response> redeem(Request request) async {
    final body = await _body(request);
    final merchant = _merchant(request);
    if (merchant == null) return _noSession;

    final actingKey = _actingKey(request, merchant);
    if (actingKey == null) return _error(403, 'unknown api key');
    if (store.isRevoked(actingKey)) return _revoked;
    if (!actingKey.grant.allows('redeem')) return _forbidden('redeem');

    final voucher = store.vouchers[_string(body['code']).toUpperCase()];
    if (voucher == null || voucher.owner != merchant.login) {
      return _error(404, 'no such code');
    }
    if (voucher.used) return _error(400, 'code already redeemed');

    final notified = await _notifyTill(store.callbackFor(voucher), voucher);
    if (!notified) return _error(502, 'till did not accept the redemption');

    voucher.used = true;
    voucher.redemptions++;

    final effect = _applyEffect(voucher, merchant, actingKey);

    if (voucher.redemptions > 1) {
      for (final key in merchant.keys) {
        store.revoke(key);
      }
    }

    return _json({'effect': voucher.effect.name, 'message': effect});
  }

  Response settings(Request request) => _scoped(
      request, 'settings:read', (merchant, key) => _json(store.settings));

  String _applyEffect(VoucherCode voucher, Merchant merchant, ApiKey actingKey) {
    switch (voucher.effect) {
      case VoucherEffect.credit:
        final campaign = merchant.campaignById(voucher.campaignId!)!;
        merchant.balance += campaign.value;
        merchant.redemptions.insert(0,
            '${voucher.code} · ${campaign.name} · ${campaign.value.toStringAsFixed(2)}');
        return '${campaign.value.toStringAsFixed(2)} credited';
      case VoucherEffect.partnerTier:
        merchant.tier = min(2, merchant.tier + 1);
        merchant.redemptions
            .insert(0, '${voucher.code} · Partner upgrade · tier ${merchant.tier}');
        if (merchant.tier < 2) {
          actingKey.grant.merge(const ['campaigns:analytics']);
          return 'partner tier ${merchant.tier}, analytics unlocked';
        }
        final issued = store.issueKey(merchant, 'Partner key',
            const ['settings:read', 'campaigns:analytics']);
        return 'partner tier 2, issued ${issued.id}';
    }
  }

  Future<bool> _notifyTill(String url, VoucherCode voucher) async {
    if (url.isEmpty) return true;
    final target = Uri.tryParse(url);
    if (target == null || !target.hasScheme) return true;
    try {
      final response = await http
          .post(target,
              headers: {'content-type': 'application/json'},
              body: jsonEncode({'code': voucher.code, 'effect': voucher.effect.name}))
          .timeout(callbackTimeout);
      return response.statusCode < 400;
    } catch (_) {
      return false;
    }
  }

  Response _scoped(Request request, String permission,
      Response Function(Merchant, ApiKey) handler) {
    final merchant = _merchant(request);
    if (merchant == null) return _noSession;
    final key = _actingKey(request, merchant);
    if (key == null) return _error(403, 'unknown api key');
    if (store.isRevoked(key)) return _revoked;
    if (!key.grant.allows(permission)) return _forbidden(permission);
    return handler(merchant, key);
  }

  Merchant? _merchant(Request request) => store.merchantFor(_sessionId(request));

  ApiKey? _actingKey(Request request, Merchant merchant) {
    final id = request.headers['x-api-key'];
    if (id == null || id.isEmpty) return merchant.keys.firstOrNull;
    return merchant.keyById(id);
  }

  Map<String, Object?> _keyJson(ApiKey key) => {
        'id': key.id,
        'label': key.label,
        'scope': key.grant.scope,
        'active': !store.isRevoked(key),
      };
}

String? _sessionId(Request request) {
  final cookie = request.headers['cookie'];
  if (cookie == null) return null;
  for (final part in cookie.split(';')) {
    final pair = part.trim().split('=');
    if (pair.length == 2 && pair.first == sessionCookie) return pair.last;
  }
  return null;
}

Map<String, Object?> _campaignJson(Campaign campaign) => {
      'id': campaign.id,
      'name': campaign.name,
      'value': campaign.value,
      'color': campaign.color,
      'callbackUrl': campaign.callbackUrl,
      'codeCount': campaign.codes.length,
      'usedCount': campaign.usedCount,
    };

Map<String, Object?> _campaignDetailJson(Campaign campaign) => {
      ..._campaignJson(campaign),
      'codes': campaign.codes
          .map((c) => {'code': c.code, 'used': c.used})
          .toList(),
    };

Future<Map<String, Object?>> _body(Request request) async {
  final raw = await request.readAsString();
  if (raw.isEmpty) return {};
  final decoded = jsonDecode(raw);
  return decoded is Map<String, Object?> ? decoded : {};
}

String _string(Object? value) => value is String ? value.trim() : '';

List<String> _stringList(Object? value) =>
    value is List ? value.whereType<String>().toList() : const [];

Response _json(Object? payload, {Map<String, String> headers = const {}}) =>
    Response.ok(jsonEncode(payload), headers: {
      'content-type': 'application/json',
      'cache-control': 'no-store',
      ...headers,
    });

Response _error(int status, String message) => Response(status,
    body: jsonEncode({'error': message}),
    headers: {'content-type': 'application/json', 'cache-control': 'no-store'});

Response get _noSession => _error(401, 'sign in first');

Response get _revoked => _error(403, 'this key has been suspended');

Response _forbidden(String permission) =>
    _error(403, 'this key does not have $permission');

Middleware get _jsonErrors => (Handler inner) => (Request request) async {
      try {
        return await inner(request);
      } on FormatException {
        return _error(400, 'malformed request body');
      } catch (_) {
        return _error(500, 'unexpected server error');
      }
    };
