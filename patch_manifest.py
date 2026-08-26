#!/usr/bin/env python3
"""
Ajoute les permissions nécessaires (Internet, Caméra, Stockage) et le nom
affiché de l'application dans le AndroidManifest.xml généré par
`flutter create`. Exécuté par le workflow GitHub Actions juste après le
scaffold Flutter, avant `flutter build apk`.
"""
import re
import sys
from pathlib import Path

MANIFEST_PATH = Path("android/app/src/main/AndroidManifest.xml")
APP_LABEL = "Reçus Airbnb"

PERMISSIONS = [
    '    <uses-permission android:name="android.permission.INTERNET"/>',
    '    <uses-permission android:name="android.permission.CAMERA"/>',
    '    <uses-permission android:name="android.permission.READ_MEDIA_IMAGES"/>',
    '    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" android:maxSdkVersion="32"/>',
]


def main() -> None:
    if not MANIFEST_PATH.exists():
        print(f"ERREUR : {MANIFEST_PATH} introuvable.", file=sys.stderr)
        sys.exit(1)

    content = MANIFEST_PATH.read_text(encoding="utf-8")

    # Ajoute les permissions manquantes juste après la balise <manifest ...>.
    manifest_open_match = re.search(r"<manifest[^>]*>", content)
    if not manifest_open_match:
        print("ERREUR : balise <manifest> introuvable.", file=sys.stderr)
        sys.exit(1)

    insert_at = manifest_open_match.end()
    to_add = [p for p in PERMISSIONS if p.split('"')[1] not in content]
    if to_add:
        block = "\n" + "\n".join(to_add)
        content = content[:insert_at] + block + content[insert_at:]

    # Remplace le label de l'application (nom affiché sous l'icône).
    content = re.sub(
        r'android:label="[^"]*"',
        f'android:label="{APP_LABEL}"',
        content,
        count=1,
    )

    MANIFEST_PATH.write_text(content, encoding="utf-8")
    print("AndroidManifest.xml mis à jour :")
    print(f"  - label : {APP_LABEL}")
    print(f"  - permissions ajoutées : {len(to_add)}")


if __name__ == "__main__":
    main()
