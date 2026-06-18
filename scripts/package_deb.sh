#!/usr/bin/env bash
set -euo pipefail

DIST_DIR="${1:-dist-desktop/local}"
PKG_NAME="teai-builder-desktop"
VERSION="${TEAI_BUILDER_VERSION:-0.2.1}"
INSTALL_DIR="${DIST_DIR}/${PKG_NAME}_${VERSION}_amd64"
ICON_PATH="${INSTALL_DIR}/usr/share/icons/hicolor/256x256/apps/teai-builder-desktop.png"

mkdir -p "${INSTALL_DIR}/DEBIAN"
mkdir -p "${INSTALL_DIR}/opt/${PKG_NAME}"
mkdir -p "${INSTALL_DIR}/usr/share/applications"
mkdir -p "${INSTALL_DIR}/usr/share/icons/hicolor/256x256/apps"

cat > "${INSTALL_DIR}/DEBIAN/control" <<EOF
Package: ${PKG_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: amd64
Depends: libgtk-3-0, libwebkit2gtk-4.1-0, libayatana-appindicator3-1, librsvg2-2, libappindicator3-1, libasound2, libnss3, libxss1, libxtst6, libx11-xcb1, libxcb-dri3-0, libgbm1, libdrm2
Maintainer: TeAi Builder <support@example.com>
Description: TeAi Builder Desktop App
EOF

cp "${DIST_DIR}/teai_builder_desktop/teai_builder_desktop" "${INSTALL_DIR}/opt/${PKG_NAME}/"
chmod 0755 "${INSTALL_DIR}/opt/${PKG_NAME}/teai_builder_desktop"

cp -r "${DIST_DIR}/teai_builder_desktop/_internal" "${INSTALL_DIR}/opt/${PKG_NAME}/"

cp "webui/public/brand/teai_builder_icon.png" "${ICON_PATH}"

cat > "${INSTALL_DIR}/usr/share/applications/${PKG_NAME}.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=TeAi Builder
Exec=/opt/${PKG_NAME}/teai_builder_desktop
Icon=teai-builder-desktop
Categories=Development;IDE;
EOF

dpkg-deb --build "${INSTALL_DIR}" "${DIST_DIR}/${PKG_NAME}_${VERSION}_amd64.deb"
echo "Built ${DIST_DIR}/${PKG_NAME}_${VERSION}_amd64.deb"
