import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_inappwebview/flutter_inappwebview.dart';
import 'package:permission_handler/permission_handler.dart';

/// URL de l'application web à afficher. Pour changer d'adresse plus tard,
/// il suffit de modifier cette ligne et de relancer le build (voir README).
const String kUrl = 'https://bellodulac-receipts.netlify.app/';

const Color kBrandColor = Color(0xFF0F6E6A);

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
                InAppWebView(
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
              if (!_hasError && _progress < 1.0)
                LinearProgressIndicator(
                  value: _progress,
                  minHeight: 3,
                  backgroundColor: Colors.white24,
                  color: Colors.white,
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
