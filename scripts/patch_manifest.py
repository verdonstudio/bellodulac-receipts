#!/usr/bin/env python3
"""
Ajustements post-scaffold appliqués juste après `flutter create`, avant
`flutter build apk` (voir le workflow GitHub Actions) :

1. Ajoute les permissions nécessaires (Internet, Caméra, Stockage) et le nom
   affiché de l'application dans AndroidManifest.xml.
2. Épingle la version de l'Android Gradle Plugin (AGP) à 8.11.1. Nécessaire
   car flutter_inappwebview n'est pas encore compatible avec AGP 9+ (erreur
   de build "getDefaultProguardFile('proguard-android.txt') is no longer
   supported" / nouvelle DSL AGP 9), alors que Flutter exige lui-même au
   moins AGP 8.11.1. 8.11.1 est le point précis qui satisfait les deux
   contraintes à la date d'écriture de ce script.
"""
import re
import sys
from pathlib import Path

MANIFEST_PATH = Path("android/app/src/main/AndroidManifest.xml")
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


def patch_manifest() -> None:
    if not MANIFEST_PATH.exists():
        print(f"ERREUR : {MANIFEST_PATH} introuvable.", file=sys.stderr)
        sys.exit(1)

    content = MANIFEST_PATH.read_text(encoding="utf-8")

    manifest_open_match = re.search(r"<manifest[^>]*>", content)
    if not manifest_open_match:
        print("ERREUR : balise <manifest> introuvable.", file=sys.stderr)
        sys.exit(1)

    insert_at = manifest_open_match.end()
    to_add = [p for p in PERMISSIONS if p.split('"')[1] not in content]
    if to_add:
        block = "\n" + "\n".join(to_add)
        content = content[:insert_at] + block + content[insert_at:]

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
    patch_agp_version()


if __name__ == "__main__":
    main()
