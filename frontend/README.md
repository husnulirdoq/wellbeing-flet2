# Android Health Connect

The tracking page reads sleep, exercise sessions, hydration, and heart rate
from Google Health Connect in the Android app. The user must grant the
requested read permissions. Data that is available is saved to the signed-in
user's daily tracking entry; values that are not available remain unchanged.

This integration is native and is not available in the browser preview. Build
the APK or AAB with these commands from this directory:

```sh
pip install -r requirements.txt
pip install ./health_connect_extension
flet build apk
```

Use `flet build aab` instead to create a Play Store bundle.
