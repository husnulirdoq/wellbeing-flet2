import "dart:convert";
import "package:flet/flet.dart";
import "package:flutter/foundation.dart";
import "package:flutter/services.dart";
import "package:flutter/widgets.dart";

const _channel = MethodChannel("com.wellbeing.tracker/health_connect");

class HealthConnectControl extends StatefulWidget {
  final Control control;

  const HealthConnectControl({
    super.key,
    required this.control,
  });

  @override
  State<HealthConnectControl> createState() => _HealthConnectControlState();
}

class _HealthConnectControlState extends State<HealthConnectControl> {
  String _requestId = "";

  @override
  void didUpdateWidget(covariant HealthConnectControl oldWidget) {
    super.didUpdateWidget(oldWidget);
    final requestId = widget.control.getString("request_id", "") ?? "";
    if (requestId.isNotEmpty && requestId != _requestId) {
      _requestId = requestId;
      _sync();
    }
  }

  Future<void> _sync() async {
    if (kIsWeb || defaultTargetPlatform != TargetPlatform.android) {
      _emit({"ok": false, "message": "Google Health Connect hanya tersedia di aplikasi Android."});
      return;
    }

    try {
      final result = await _channel.invokeMapMethod<String, dynamic>("sync");
      _emit(result ?? {"ok": false, "message": "Health Connect tidak memberikan data."});
    } on PlatformException catch (error) {
      _emit({
        "ok": false,
        "message": error.message ?? "Gagal membaca data Health Connect.",
      });
    } catch (_) {
      _emit({"ok": false, "message": "Gagal membaca data Health Connect."});
    }
  }

  void _emit(Map<String, dynamic> result) {
    widget.control.triggerEvent("on_result", jsonEncode(result));
  }

  @override
  Widget build(BuildContext context) => const SizedBox.shrink();
}
