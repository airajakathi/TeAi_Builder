# Publishing

TeAi Builder ships to real targets. Web deploys are gated behind verification.

## Web

Supported targets: **Vercel, Netlify, Railway, Render, Fly.io, or a VPS**.

### Verified deploy gate (hard requirement)

Before a web project's phase can advance to "shipped", TeAi Builder must:

1. Run **`run_verification`** and get a passing report.
2. Hit the live URL with a **health check**.
3. Capture a live **`screenshot`** of the deployed site.
4. Advance the phase via **`project_gate`** only after the above succeed.

## Mobile

Real Expo / React Native apps are published with **Expo EAS**:

```bash
eas login
eas build:configure
eas build --platform android   # or ios
eas submit --platform android  # or ios
```

Submitting to the **Play Store** / **App Store** requires your developer credentials.
TeAi Builder will stop and ask for these rather than guessing.

## Desktop

Web apps are packaged into native installers with **Tauri** (preferred) or **Electron**,
producing `.exe`, `.dmg`, or `.AppImage` artifacts. Cross-compilation and code-signing
have OS-specific requirements; builds are verified before being declared done.

See the in-agent skills (`deploy`, `publish-mobile`, `desktop`) for the detailed,
enforced procedures.
