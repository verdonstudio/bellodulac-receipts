import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_inappwebview/flutter_inappwebview.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:url_launcher/url_launcher.dart';

/// URL de l'application web à afficher. Pour changer d'adresse plus tard,
/// il suffit de modifier cette ligne et de relancer le build (voir README).
const String kUrl = 'https://bellodulac-receipts.netlify.app/';

const Color kBrandColor = Color(0xFF0F6E6A);

/// Domaines dont les liens doivent ouvrir l'appli native correspondante
/// (si elle est installée) plutôt que de s'afficher dans notre webview.
const List<String> kExternalAppDomains = ['airbnb.', 'docs.google.com'];

void main() {
  runApp(const ReceiptsApp());
}

class ReceiptsApp extends StatelessWidget {
  const ReceiptsApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: "Reçus Airbnb",
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: kBrandColor,
      ),
      home: const WebViewScreen(),
    );
  }
}

class WebViewScreen extends StatefulWidget {
  const WebViewScreen({super.key});

  @override
  State<WebViewScreen> createState() => _WebViewScreenState();
}

class _WebViewScreenState extends State<WebViewScreen> {
  InAppWebViewController? _controller;
  double _progress = 0;
  bool _hasError = false;

  @override
  void initState() {
    super.initState();
    // Demande les permissions caméra/photos une fois au démarrage, pour que
    // la prise de photo depuis le formulaire fonctionne du premier coup.
    _requestPermissions();
    // Barre de statut opaque à la couleur de l'appli (au lieu de
    // transparente/edge-to-edge) : sur Android récent, une barre de statut
    // transparente peut se superposer au contenu de la webview et cacher sa
    // toute première ligne. En la rendant opaque, cette zone est clairement
    // réservée et ne recouvre jamais le contenu affiché en dessous.
    SystemChrome.setSystemUIOverlayStyle(
      const SystemUiOverlayStyle(
        statusBarColor: kBrandColor,
        statusBarIconBrightness: Brightness.light,
      ),
    );
  }

  Future<void> _requestPermissions() async {
    await [
      Permission.camera,
      Permission.photos,
      Permission.storage,
    ].request();
  }

  Future<void> _handleBack() async {
    if (_controller != null && await _controller!.canGoBack()) {
      await _controller!.goBack();
    }
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) async {
        if (didPop) return;
        if (_controller != null && await _controller!.canGoBack()) {
          await _controller!.goBack();
        } else {
          // Rien à dépiler dans la webview : on quitte vraiment l'appli.
          await SystemNavigator.pop();
        }
      },
      child: Scaffold(
        backgroundColor: kBrandColor,
        body: SafeArea(
          child: Stack(
            children: [
              if (_hasError)
                _ErrorView(onRetry: () {
                  setState(() => _hasError = false);
                  _controller?.reload();
                })
              else
                Positioned.fill(
                  // Positioned.fill (plutôt que de laisser le Stack deviner
                  // la taille) force la webview à occuper exactement
                  // l'espace laissé par SafeArea, sans jamais déborder sous
                  // la barre de statut.
                  child: InAppWebView(
                    initialUrlRequest: URLRequest(url: WebUri(kUrl)),
                    initialSettings: InAppWebViewSettings(
                      javaScriptEnabled: true,
                      domStorageEnabled: true,
                      databaseEnabled: true,
                      allowFileAccess: true,
                      allowContentAccess: true,
                      mediaPlaybackRequiresUserGesture: false,
                      supportZoom: false,
                      cacheEnabled: true,
                      useHybridComposition: true,
                    ),
                    onWebViewCreated: (controller) => _controller = controller,
                    shouldOverrideUrlLoading: (controller, navigationAction) async {
                      final uri = navigationAction.request.url;
                      // Le menu du site propose des liens (Airbnb, Google
                      // Sheets) destinés à ouvrir l'appli native
                      // correspondante plutôt que notre propre webview : on
                      // les détecte ici et on les fait gérer par le système
                      // Android, qui ouvrira l'appli installée, sinon un
                      // navigateur classique.
                      final host = uri?.host ?? '';
                      final isExternalApp =
                          uri != null && kExternalAppDomains.any(host.contains);
                      if (isExternalApp) {
                        final launched = await launchUrl(
                          Uri.parse(uri.toString()),
                          mode: LaunchMode.externalApplication,
                        );
                        if (launched) return NavigationActionPolicy.CANCEL;
                      }
                      return NavigationActionPolicy.ALLOW;
                    },
                    onProgressChanged: (controller, progress) {
                      setState(() => _progress = progress / 100);
                    },
                    onReceivedError: (controller, request, error) {
                      if (request.isForMainFrame ?? true) {
                        setState(() => _hasError = true);
                      }
                    },
                    onPermissionRequest: (controller, request) async {
                      return PermissionResponse(
                        resources: request.resources,
                        action: PermissionResponseAction.GRANT,
                      );
                    },
                  ),
                ),
              if (!_hasError && _progress < 1.0)
                Positioned(
                  top: 0,
                  left: 0,
                  right: 0,
                  child: LinearProgressIndicator(
                    value: _progress,
                    minHeight: 3,
                    backgroundColor: Colors.white24,
                    color: Colors.white,
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  final VoidCallback onRetry;
  const _ErrorView({required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.white,
      alignment: Alignment.center,
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.wifi_off, size: 48, color: kBrandColor),
          const SizedBox(height: 16),
          const Text(
            "Impossible de charger l'application.\nVérifiez votre connexion internet.",
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 20),
          ElevatedButton(
            onPressed: onRetry,
            style: ElevatedButton.styleFrom(backgroundColor: kBrandColor),
            child: const Text('Réessayer'),
          ),
        ],
      ),
    );
  }
}
