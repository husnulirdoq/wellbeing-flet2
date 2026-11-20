import "package:flet/flet.dart";
import "package:flutter/widgets.dart";

import "health_connect_control.dart";

class Extension extends FletExtension {
  @override
  Widget? createWidget(Key? key, Control control) {
    if (control.type == "HealthConnect") {
      return HealthConnectControl(key: key, control: control);
    }
    return null;
  }
}
