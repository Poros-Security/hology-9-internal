import 'dart:math';

const allPermissions = {
  'redeem',
  'campaigns:read',
  'campaigns:write',
  'campaigns:analytics',
  'settings:read',
};

class Grant {
  final String keyId;
  final List<String> scope;

  Grant(this.keyId, Iterable<String> scope)
      : scope = (scope.toSet().toList()..sort());

  bool allows(String permission) => scope.contains(permission);

  bool admitsAsNarrowing(Iterable<String> candidate) {
    final next = candidate.toSet();
    return next.length < scope.length && next.every(scope.contains);
  }

  void replaceScope(Iterable<String> next) {
    final sorted = next.toSet().toList()..sort();
    scope
      ..clear()
      ..addAll(sorted);
  }

  void merge(Iterable<String> extra) => replaceScope({...scope, ...extra});

  @override
  bool operator ==(Object other) =>
      other is Grant &&
      other.keyId == keyId &&
      other.scope.length == scope.length &&
      other.scope.every(scope.contains);

  @override
  int get hashCode => Object.hashAll([keyId, ...scope]);
}

class ApiKey {
  final String id;
  final String label;
  final Grant grant;

  ApiKey(this.id, this.label, Iterable<String> scope) : grant = Grant(id, scope);
}

enum VoucherEffect { credit, partnerTier }

class VoucherCode {
  final String code;
  final String owner;
  final String? campaignId;
  final VoucherEffect effect;
  bool used = false;
  int redemptions = 0;

  VoucherCode(this.code, this.owner, this.campaignId, this.effect);
}

class Campaign {
  final String id;
  final String name;
  final num value;
  final String color;
  String callbackUrl;
  final List<VoucherCode> codes = [];

  Campaign(this.id, this.name, this.value, this.color, this.callbackUrl);

  int get usedCount => codes.where((c) => c.used).length;
}

class Merchant {
  final String login;
  final String password;
  final String name;
  final String initials;
  late final String upgradeCode;
  int tier = 0;
  num balance = 0;
  String tillUrl = '';
  final List<ApiKey> keys = [];
  final List<Campaign> campaigns = [];
  final List<String> redemptions = [];

  Merchant(this.login, this.password, this.name, this.initials);

  ApiKey? keyById(String id) => keys.where((k) => k.id == id).firstOrNull;

  Campaign? campaignById(String id) =>
      campaigns.where((c) => c.id == id).firstOrNull;
}

class Store {
  final Map<String, Merchant> merchants = {};
  final Map<String, String> sessions = {};
  final Map<String, VoucherCode> vouchers = {};
  final Set<Grant> revoked = {};
  final Map<String, String> settings;

  Store(this.settings);

  Merchant? merchantFor(String? sessionId) {
    final login = sessionId == null ? null : sessions[sessionId];
    return login == null ? null : merchants[login];
  }

  Merchant? authenticate(String login, String password) {
    final merchant = merchants[login];
    if (merchant == null || merchant.password != password) return null;
    return merchant;
  }

  String openSession(Merchant merchant) {
    final id = _token(24);
    sessions[id] = merchant.login;
    return id;
  }

  bool isRevoked(ApiKey key) => revoked.contains(key.grant);

  void revoke(ApiKey key) => revoked.add(key.grant);

  ApiKey issueKey(Merchant merchant, String label, Iterable<String> scope) {
    final key = ApiKey('slp_live_${_token(8)}', label, scope);
    merchant.keys.add(key);
    return key;
  }

  Campaign createCampaign(Merchant merchant, String name, num value,
      int codeCount, String callbackUrl) {
    final campaign = Campaign(
      'cmp_${_token(6).toLowerCase()}',
      name,
      value,
      _palette[merchant.campaigns.length % _palette.length],
      callbackUrl,
    );
    for (var i = 0; i < codeCount; i++) {
      final voucher = VoucherCode(
          _voucherCode(), merchant.login, campaign.id, VoucherEffect.credit);
      campaign.codes.add(voucher);
      vouchers[voucher.code] = voucher;
    }
    merchant.campaigns.add(campaign);
    return campaign;
  }

  String callbackFor(VoucherCode voucher) {
    final merchant = merchants[voucher.owner]!;
    final campaign =
        voucher.campaignId == null ? null : merchant.campaignById(voucher.campaignId!);
    final url = campaign?.callbackUrl ?? '';
    return url.isEmpty ? merchant.tillUrl : url;
  }

  void seed(String flag) {
    settings['Licence key'] = flag;

    final merchant =
        Merchant('halden.co', 'slopter2026', 'Halden Coffee Co.', 'HC');
    merchant.upgradeCode = 'SLP-PTNR-7K2Q';
    merchants[merchant.login] = merchant;

    issueKey(merchant, 'Counter key',
        const ['redeem', 'campaigns:read', 'campaigns:write']);

    vouchers[merchant.upgradeCode] = VoucherCode(
        merchant.upgradeCode, merchant.login, null, VoucherEffect.partnerTier);

    final weekend = createCampaign(merchant, 'Weekend Flat 5', 5.00, 6, '');
    final spent = weekend.codes.first;
    spent.used = true;
    spent.redemptions = 1;
    merchant.redemptions.add('${spent.code} · Weekend Flat 5 · 5.00');
    merchant.balance = 5.00;

    createCampaign(merchant, 'Student Tuesday', 2.50, 4, '');
  }
}

const _palette = ['#7c5cff', '#0ea5a4', '#f59e0b', '#ef4476'];
const _alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
final _random = Random.secure();

String _token(int length) =>
    List.generate(length, (_) => _alphabet[_random.nextInt(_alphabet.length)])
        .join();

String _voucherCode() => 'SLP-${_token(4)}-${_token(4)}';
