---
name: android-device
description: Reach the user's Android phone. Use for adb (wireless debugging, pairing, empty device lists) or to send a file to the phone.
---

- Wireless ADB: empty `adb devices`/`adb mdns services` does not prove debugging is off; check Avahi, try the
  advertised endpoint, and reconnect before asking the user to re-pair.
- Phone: `scp <file> phone:~/storage/downloads/` (Termux over Tailscale, port 8022).
