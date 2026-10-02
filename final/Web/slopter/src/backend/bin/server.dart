import 'dart:io';

import 'package:shelf/shelf_io.dart' as shelf_io;
import 'package:slopter_api/api.dart';
import 'package:slopter_api/store.dart';

Future<void> main() async {
  final flag = Platform.environment['GZCTF_FLAG'];
  if (flag == null || flag.isEmpty) {
    stderr.writeln('GZCTF_FLAG is not set');
    exit(1);
  }

  final store = Store({
    'Instance name': 'slopter-demo',
    'Deployment region': 'ap-southeast-1',
    'Callback timeout': '${callbackTimeout.inSeconds}s',
    'Voucher code format': 'SLP-XXXX-XXXX',
    'Support contact': 'partners@slopter.example',
  })
    ..seed(flag);

  final port = int.parse(Platform.environment['PORT'] ?? '8080');
  await shelf_io.serve(buildApi(store), '127.0.0.1', port);
  stdout.writeln('slopter api on 127.0.0.1:$port');
}
