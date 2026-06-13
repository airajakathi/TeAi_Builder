---
name: mobile
description: Build real Android/iOS apps with Expo. MVP first — get it running in 10 minutes, then add features.
metadata: {"teai_builder": {"emoji": "📱", "always": true}}
---

# Mobile App Development — Expo (React Native)

## The Golden Rule: Running App in 10 Minutes or Less

**Do NOT spend hours planning architecture before the app runs. Get it running FIRST, then improve.**

| Phase | Time limit | Goal |
|-------|-----------|------|
| Scaffold + basic screen | 5 min | `npx expo start` shows QR code |
| Core game logic | 15 min | App playable end-to-end |
| Polish | later | Animations, sounds, polish |

If you cannot get the app to start within 10 minutes, something is wrong. Stop and report.

---

## Correct Expo Workflow (Follow Exactly)

### Step 1: Scaffold (2 minutes)
```bash
cd projects/
npx create-expo-app <name> --template blank-typescript
cd <name>
```
This gives you a working `App.tsx` that already runs. **Do not break it.**

### Step 2: Install deps INCLUDING web preview support (2 minutes)
For a board game (Ludo, Chess, etc.) — use React Native's built-in drawing, no Skia needed for MVP:
```bash
npm install  # installs what create-expo-app added
# MANDATORY: web preview deps so the live preview iframe in canvas works
./node_modules/.bin/expo install react-dom react-native-web @expo/metro-runtime
```

**`react-dom` + `react-native-web` + `@expo/metro-runtime` are REQUIRED.** Without them, the canvas live-preview shows a blank screen because expo cannot serve the web bundle.

**DO NOT install Skia, Reanimated, or heavy deps for the MVP.** They cause install failures and TS errors. Get the app running first with simple `View`, `Text`, and `TouchableOpacity`.

### Step 2b: Fix app.json — NEVER reference assets that don't exist
When you create files inline (instead of via `create-expo-app`), the `assets/` folder is EMPTY. If `app.json` references `./assets/icon.png`, `splash.png`, etc., **Metro fails to bundle and the phone shows a WHITE SCREEN.**

Write a minimal `app.json` with NO asset references:
```json
{
  "expo": {
    "name": "<App Name>",
    "slug": "<slug>",
    "version": "1.0.0",
    "orientation": "portrait",
    "userInterfaceStyle": "light",
    "assetBundlePatterns": ["**/*"],
    "ios": { "supportsTablet": true },
    "android": {},
    "web": { "bundler": "metro" }
  }
}
```
Add `icon`/`splash` only AFTER you actually generate the image files. **A missing asset = white screen = failed delivery.**

### Step 3: Write the game in ONE file first (5 minutes)
Put ALL game code in `App.tsx`. Use ONLY:
- `View` — for board squares and layout
- `Text` — for labels, scores, dice face
- `TouchableOpacity` or `Pressable` — for tappable pieces
- `StyleSheet.create({})` — for all styling
- `useState`, `useCallback` — for game state

No Canvas, no Skia, no complex components for the MVP. A Ludo board is just `View` grids with colored squares.

### Step 4: Start Expo immediately after writing App.tsx

**TWO SEPARATE exec calls — never combine them!**

**Call 1: Get the LAN IP first**
```bash
LAN_IP=$(hostname -I | awk '{print $1}'); echo "LAN IP: $LAN_IP"
```

**Call 2: Start expo as a persistent systemd user service**
```bash
LAN_IP=$(hostname -I | awk '{print $1}')
# Stop any previous expo service for this project
systemctl --user stop expo-<name> 2>/dev/null || true
# Start as a persistent service (won't be killed when exec command ends)
systemd-run --user --unit=expo-<name> \
  --setenv=REACT_NATIVE_PACKAGER_HOSTNAME=$LAN_IP \
  bash -c 'cd "/home/sharan/Teai builder/instance/workspace/projects/<name>" && ./node_modules/.bin/expo start --port 8081'
echo "Expo service started"
```

**Why systemd-run?** Unlike `nohup` or `&`, `systemd-run` creates a true persistent background service that survives exec command exits and cannot be accidentally killed by subsequent `pkill` commands.

**Wait 20 seconds, then Call 3: Confirm Metro started**
```bash
sleep 20 && journalctl --user -u expo-<name> --no-pager -n 20
```

**Call 4: Build the exp:// URL and show in canvas**
```bash
LAN_IP=$(hostname -I | awk '{print $1}'); echo "exp://$LAN_IP:8081"
```

Then call canvas:
```
canvas(type="mobile_url", content="exp://192.168.x.x:8081", title="<App> — Scan with Expo Go")
```

**CRITICAL**: 
- `REACT_NATIVE_PACKAGER_HOSTNAME=<LAN_IP>` — without it, expo uses `127.0.0.1` in the manifest and phones can't download the bundle
- `systemd-run` is the ONLY reliable way to keep expo running across exec commands
- To stop the service later: `systemctl --user stop expo-<name>`

### Step 5: VERIFY the bundle compiles (catches white screen BEFORE delivery)

**This step is MANDATORY. A QR code that opens to a white screen = failed delivery.**

Compile the web bundle and confirm it returns HTTP 200 with real content:
```bash
# Warm up + verify the web bundle (this is what the live preview loads)
BUNDLE_URL="http://127.0.0.1:8081/node_modules/expo/AppEntry.bundle?platform=web&dev=true"
SIZE=$(curl -s -o /dev/null -w "%{size_download}" "$BUNDLE_URL")
echo "Web bundle size: $SIZE bytes"
# Also verify the native (ios) bundle compiles — this is what Expo Go downloads
NATIVE_URL="http://127.0.0.1:8081/node_modules/expo/AppEntry.bundle?platform=ios&dev=true"
NSIZE=$(curl -s -o /dev/null -w "%{size_download}" "$NATIVE_URL")
echo "Native bundle size: $NSIZE bytes"
```
- If size is **< 10000 bytes**, the bundle FAILED — read the response body for the error (likely a missing asset or a JS error). Fix it before delivering.
- A healthy bundle is **hundreds of KB to several MB**.
- Common white-screen cause: missing asset in `app.json` (see Step 2b) or a runtime error in `App.tsx`.

### Step 6: Show in canvas (live preview + QR together)
```bash
LAN_IP=$(hostname -I | awk '{print $1}'); echo "exp://$LAN_IP:8081"
```

Then call canvas:
```
canvas(type="mobile_url", content="exp://192.168.x.x:8081", title="<App> — Scan with Expo Go")
```

The canvas `mobile_url` view automatically shows BOTH:
- **Live preview** — the running app inside a phone mockup (via the web bundle)
- **QR code** — for scanning with Expo Go on a real Android/iOS phone

**The user scans the QR with Expo Go (free app), OR watches the live preview right in the canvas.**

---

## What to use for different game types

| Game type | Approach |
|-----------|----------|
| Board game (Ludo, Chess) | `View` grid + `TouchableOpacity` tokens — pure React Native, no Canvas |
| Endless runner (Temple Run) | Expo + `react-native-game-engine` — installed AFTER app starts |
| Graphics-heavy | Expo + `@shopify/react-native-skia` — only add after MVP works |

---

## TypeScript Error Rule

If `npx tsc --noEmit` shows errors:
1. Fix **maximum 3 errors at a time**, then re-run
2. **Time limit: 5 minutes on TS errors**. If not clean in 5 minutes, use `// @ts-ignore` on the specific line and move on
3. **Never spend 30+ minutes fixing TS errors before the app even starts**
4. A working app with some `@ts-ignore` is infinitely better than a broken app with perfect types

---

## Common Mistakes That Cause Failures

- ❌ **Referencing `./assets/icon.png` etc. in app.json when the files don't exist** → white screen
- ❌ **Skipping `expo install react-dom react-native-web @expo/metro-runtime`** → blank live preview
- ❌ **Delivering without verifying the bundle compiles (Step 5)** → QR opens to white screen
- ❌ Installing Skia + Reanimated + GestureHandler ALL at once before testing
- ❌ Building 10 separate component files before running `expo start` once
- ❌ Trying to fix all TypeScript errors before the app even starts
- ❌ Using complex architecture (layers, engines, hooks) for a game MVP
- ❌ Starting Expo with `--tunnel` (requires Expo account, often fails)

---

## Reporting to CEO

After starting Expo:
1. Report the `exp://IP:PORT` URL
2. Report the verified bundle sizes (web + native) from Step 5
3. Report any startup errors from the log
4. CEO shows the URL in canvas as `mobile_url` with QR + live preview
5. CEO tells user to open Expo Go and scan, or watch the live preview

**Never report "done" without completing Step 5 (bundle verification). A white screen is a failed delivery.**
**Never report "still working on TypeScript errors" after 10 minutes. That means something is wrong.**
