#!/usr/bin/env python3

import re
import sys
from pathlib import Path

MANIFEST_PATH = Path("android/app/src/main/AndroidManifest.xml")
PROVIDER_PATHS_PATH = Path("android/app/src/main/res/xml/provider_paths.xml")
PUBSPEC_PATH = Path("pubspec.yaml")
# Les projets Flutter récents utilisent tantôt settings.gradle (Groovy),
# tantôt settings.gradle.kts (Kotlin DSL) selon la version du template.
SETTINGS_GRADLE_CANDIDATES = [
    Path("android/settings.gradle.kts"),
    Path("android/settings.gradle"),
]
APP_LABEL = "Reçus Airbnb"
AGP_VERSION = "8.11.1"

PERMISSIONS = [
    '    <uses-permission android:name="android.permission.INTERNET"/>',
    '    <uses-permission android:name="android.permission.CAMERA"/>',
    '    <uses-permission android:name="android.permission.READ_MEDIA_IMAGES"/>',
    '    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" android:maxSdkVersion="32"/>',
]

FILE_PROVIDER_BLOCK = """        <provider
            android:name="com.pichillilorenzo.flutter_inappwebview_android.InAppWebViewFileProvider"
            android:authorities="${applicationId}.flutter_inappwebview_android.fileprovider"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/provider_paths" />
        </provider>
"""

PROVIDER_PATHS_XML = """<?xml version="1.0" encoding="utf-8"?>
<paths xmlns:android="http://schemas.android.com/apk/res/android">
    <external-path name="external-path" path="." />
    <external-cache-path name="external-cache-path" path="." />
    <external-files-path name="external-files-path" path="." />
    <cache-path name="cache-path" path="." />
    <files-path name="files-path" path="." />
    <root-path name="root-path" path="." />
</paths>
"""


def patch_manifest() -> None:
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

    # Ajoute le FileProvider (nécessaire pour la capture photo) juste après
    # l'ouverture de la balise <application ...>, s'il n'y est pas déjà.
    if "InAppWebViewFileProvider" not in content:
        application_open_match = re.search(r"<application[^>]*>", content)
        if not application_open_match:
            print("ERREUR : balise <application> introuvable.", file=sys.stderr)
            sys.exit(1)
        insert_at = application_open_match.end()
        content = content[:insert_at] + "\n" + FILE_PROVIDER_BLOCK + content[insert_at:]
        provider_added = True
    else:
        provider_added = False

    MANIFEST_PATH.write_text(content, encoding="utf-8")
    print("AndroidManifest.xml mis à jour :")
    print(f"  - label : {APP_LABEL}")
    print(f"  - permissions ajoutées : {len(to_add)}")
    print(f"  - FileProvider ajouté : {provider_added}")


def write_provider_paths() -> None:
    PROVIDER_PATHS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROVIDER_PATHS_PATH.write_text(PROVIDER_PATHS_XML, encoding="utf-8")
    print(f"{PROVIDER_PATHS_PATH} créé.")


def append_launcher_icons_config() -> None:
    if not PUBSPEC_PATH.exists():
        print(f"ERREUR : {PUBSPEC_PATH} introuvable.", file=sys.stderr)
        sys.exit(1)

    content = PUBSPEC_PATH.read_text(encoding="utf-8")
    if "flutter_launcher_icons:" in content:
        print("pubspec.yaml : configuration flutter_launcher_icons déjà présente.")
        return

    icon_config = (
        "\n"
        "flutter_launcher_icons:\n"
        "  android: true\n"
        "  ios: false\n"
        '  image_path: "assets/icon/icon.png"\n'
        '  adaptive_icon_background: "#FFFFFF"\n'
        '  adaptive_icon_foreground: "assets/icon/icon_foreground.png"\n'
        "  min_sdk_android: 21\n"
    )
    PUBSPEC_PATH.write_text(content.rstrip("\n") + "\n" + icon_config, encoding="utf-8")
    print("pubspec.yaml : configuration flutter_launcher_icons ajoutée.")


def patch_agp_version() -> None:
    settings_path = next((p for p in SETTINGS_GRADLE_CANDIDATES if p.exists()), None)
    if settings_path is None:
        print(
            "ERREUR : aucun android/settings.gradle(.kts) introuvable.",
            file=sys.stderr,
        )
        sys.exit(1)

    content = settings_path.read_text(encoding="utf-8")
    original = content

    # Couvre à la fois la syntaxe Groovy :
    #   id "com.android.application" version "X.Y.Z" apply false
    # et la syntaxe Kotlin DSL :
    #   id("com.android.application") version "X.Y.Z" apply false
    content = re.sub(
        r'(com\.android\.application["\']\)?\s+version\s+["\'])[^"\']+(["\'])',
        rf"\g<1>{AGP_VERSION}\g<2>",
        content,
    )

    if content == original:
        print(
            "AVERTISSEMENT : aucune ligne de version AGP trouvée dans "
            f"{settings_path} — rien à modifier (le fichier a peut-être "
            "une structure différente de celle attendue).",
        )
        return

    settings_path.write_text(content, encoding="utf-8")
    print(f"{settings_path} mis à jour : AGP épinglé à {AGP_VERSION}")


def main() -> None:
    patch_manifest()
    write_provider_paths()
    append_launcher_icons_config()
    patch_agp_version()


if __name__ == "__main__":
    main()
