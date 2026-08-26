name: Build APK

on:
  workflow_dispatch: {}
  push:
    branches: [ main ]
    paths:
      - 'app_src/**'
      - 'scripts/**'
      - 'assets/**'
      - '.github/workflows/build-apk.yml'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Recuperer le depot
        uses: actions/checkout@v4

      - name: Installer Flutter
        uses: subosito/flutter-action@v2
        with:
          channel: 'stable'

      - name: Creer le squelette Android natif
        run: flutter create --platforms=android --org com.bellodulac --project-name recus_airbnb .

      - name: Copier le code de l application
        run: cp -f app_src/main.dart lib/main.dart

      - name: Ajouter les dependances
        run: flutter pub add flutter_inappwebview permission_handler

      - name: Configurer les permissions et le nom de l appli
        run: python3 scripts/patch_manifest.py

      - name: Recuperer les paquets
        run: flutter pub get

      - name: Ajouter l icone de l application
        run: |
          flutter pub add --dev flutter_launcher_icons
          dart run flutter_launcher_icons

      - name: Construire l APK
        run: flutter build apk --release

      - name: Publier l APK comme artefact du build
        uses: actions/upload-artifact@v4
        with:
          name: recus-airbnb-apk
          path: build/app/outputs/flutter-apk/app-release.apk
          if-no-files-found: error
