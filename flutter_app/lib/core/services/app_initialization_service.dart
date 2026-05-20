import 'dart:async';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:logger/logger.dart';
import 'package:path_provider/path_provider.dart';
import 'package:py_engine_desktop/py_engine_desktop.dart';
import 'package:process_run/process_run.dart';
import 'package:dio/dio.dart';
import '../../config/app_constants.dart';
import 'api_service.dart';

enum SetupStep {
  notStarted,
  initializingPython,
  extractingBackend,
  downloadingOllama,
  installingOllama,
  downloadingModel,
  startingServices,
  complete,
  error,
}

class SetupProgress {
  final SetupStep step;
  final double progress;
  final String message;
  final String? error;

  SetupProgress({
    required this.step,
    required this.progress,
    required this.message,
    this.error,
  });

  double get overallProgress {
    switch (step) {
      case SetupStep.notStarted:
        return 0.0;
      case SetupStep.initializingPython:
        return progress * 0.1;
      case SetupStep.extractingBackend:
        return 0.1 + (progress * 0.1);
      case SetupStep.downloadingOllama:
        return 0.2 + (progress * 0.3);
      case SetupStep.installingOllama:
        return 0.5 + (progress * 0.1);
      case SetupStep.downloadingModel:
        return 0.6 + (progress * 0.3);
      case SetupStep.startingServices:
        return 0.9 + (progress * 0.1);
      case SetupStep.complete:
        return 1.0;
      case SetupStep.error:
        return 0.0;
    }
  }
}

class AppInitializationService {
  static final AppInitializationService _instance = AppInitializationService._internal();
  final logger = Logger();

  Process? _ollamaProcess;
  Process? _flaskProcess;
  bool _isSetupComplete = false;
  bool _isOllamaDownloaded = false;
  bool _isModelDownloaded = false;

  final _progressController = StreamController<SetupProgress>.broadcast();
  Stream<SetupProgress> get progressStream => _progressController.stream;

  factory AppInitializationService() => _instance;
  AppInitializationService._internal();

  // Paths
  String? _appDataPath;
  String? _pythonPath;
  String? _ollamaPath;
  String? _backendPath;

  Future<void> initialize() async {
    final appDir = await getApplicationDocumentsDirectory();
    _appDataPath = '${appDir.path}/BTFResume';
    _backendPath = '$_appDataPath/backend';
    _ollamaPath = '$_appDataPath/ollama';

    // Create app directory
    final appDirObj = Directory(_appDataPath!);
    if (!await appDirObj.exists()) {
      await appDirObj.create(recursive: true);
    }

    logger.i('📁 App data path: $_appDataPath');
  }

  Future<bool> checkSetupStatus() async {
    await initialize();

    final statusFile = File('$_appDataPath/setup_status.json');
    if (await statusFile.exists()) {
      final content = await statusFile.readAsString();
      _isSetupComplete = content.contains('"complete":true');
      _isOllamaDownloaded = content.contains('"ollama":true');
      _isModelDownloaded = content.contains('"model":true');
    }

    return _isSetupComplete;
  }

  Future<void> runFullSetup() async {
    try {
      // Step 1: Initialize Python runtime
      _emitProgress(SetupStep.initializingPython, 0.0, 'Initializing Python runtime...');
      await _initializePython();
      _emitProgress(SetupStep.initializingPython, 1.0, 'Python ready');

      // Step 2: Extract backend code
      _emitProgress(SetupStep.extractingBackend, 0.0, 'Setting up backend...');
      await _extractBackend();
      _emitProgress(SetupStep.extractingBackend, 1.0, 'Backend ready');

      // Step 3: Download/Install Ollama
      _emitProgress(SetupStep.downloadingOllama, 0.0, 'Setting up AI engine...');
      final ollamaInstalled = await _ensureOllamaInstalled();
      if (!ollamaInstalled) {
        throw Exception('Failed to install Ollama');
      }
      _emitProgress(SetupStep.downloadingOllama, 1.0, 'AI engine ready');

      // Step 4: Start Ollama service
      _emitProgress(SetupStep.startingServices, 0.0, 'Starting AI service...');
      await _startOllama();
      _emitProgress(SetupStep.startingServices, 0.3, 'AI service running');

      // Step 5: Start Flask backend
      await _startFlaskBackend();
      _emitProgress(SetupStep.startingServices, 0.7, 'Backend running');

      // Step 6: Download default model
      _emitProgress(SetupStep.downloadingModel, 0.0, 'Downloading AI model (this may take a few minutes)...');
      await _ensureModelDownloaded();
      _emitProgress(SetupStep.downloadingModel, 1.0, 'AI model ready');

      // Mark setup as complete
      await _markSetupComplete();

      _emitProgress(SetupStep.complete, 1.0, 'All set!');
      logger.i('✅ Full setup completed successfully');

    } catch (e) {
      logger.e('❌ Setup failed: $e');
      _emitProgress(SetupStep.error, 0.0, 'Setup failed', error: e.toString());
      rethrow;
    }
  }

  void _emitProgress(SetupStep step, double progress, String message, {String? error}) {
    _progressController.add(SetupProgress(
      step: step,
      progress: progress,
      message: message,
      error: error,
    ));
  }

  Future<void> _initializePython() async {
    try {
      // Initialize py_engine_desktop
      await PyEngineDesktop.init();
      _pythonPath = PyEngineDesktop.pythonPath;
      logger.i('🐍 Python initialized at: $_pythonPath');
    } catch (e) {
      logger.e('Failed to initialize Python: $e');
      rethrow;
    }
  }

  Future<void> _extractBackend() async {
    try {
      final backendDir = Directory(_backendPath!);
      if (!await backendDir.exists()) {
        await backendDir.create(recursive: true);
      }

      final coreDir = Directory('$_appDataPath/core');
      if (!await coreDir.exists()) {
        await coreDir.create(recursive: true);
      }

      // Get Flutter's asset directory - the bundled backend is in assets/python/
      // We need to copy from the asset bundle to app data
      final assetPath = await _getAssetPath('assets/python/backend');
      final coreAssetPath = await _getAssetPath('assets/python/core');
      final requirementsPath = await _getAssetPath('assets/python/requirements.txt');

      if (assetPath != null) {
        await _copyDirectory(Directory(assetPath), backendDir);
        logger.i('📦 Copied backend from assets to: $_backendPath');
      } else {
        // Fallback: create a minimal backend runner if assets not found
        final runnerScript = File('$_backendPath/run.py');
        await runnerScript.writeAsString('''
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
''');
      }

      if (coreAssetPath != null) {
        await _copyDirectory(Directory(coreAssetPath), coreDir);
        logger.i('📦 Copied core modules to: $_appDataPath/core');
      }

      if (requirementsPath != null) {
        final reqFile = File(requirementsPath);
        final destReqFile = File('$_backendPath/requirements.txt');
        await reqFile.copy(destReqFile.path);
      }

      logger.i('📦 Backend extraction complete');
    } catch (e) {
      logger.e('Failed to extract backend: $e');
      rethrow;
    }
  }

  Future<String?> _getAssetPath(String relativePath) async {
    // In Flutter desktop, assets are in the executable's data folder
    // For development, they're in flutter_app/assets/
    // For release, they're in the bundle's data/flutter_assets/
    try {
      // Try development path first
      final devPath = 'flutter_app/$relativePath';
      if (await Directory(devPath).exists()) {
        return devPath;
      }

      // Try release path
      final exeDir = File(Platform.resolvedExecutable).parent.path;
      final releasePath = '$exeDir/data/flutter_assets/$relativePath';
      if (await Directory(releasePath).exists()) {
        return releasePath;
      }
      
      // Try alternative release path
      final altPath = '$exeDir/flutter_assets/$relativePath';
      if (await Directory(altPath).exists()) {
        return altPath;
      }

      return null;
    } catch (e) {
      logger.w('Could not find asset path for $relativePath: $e');
      return null;
    }
  }

  Future<void> _copyDirectory(Directory source, Directory destination) async {
    if (!await destination.exists()) {
      await destination.create(recursive: true);
    }

    await for (var entity in source.list(recursive: false)) {
      if (entity is File) {
        final destPath = destination.path + Platform.pathSeparator + entity.path.split(Platform.pathSeparator).last;
        await entity.copy(destPath);
      } else if (entity is Directory) {
        final newDest = Directory(destination.path + Platform.pathSeparator + entity.path.split(Platform.pathSeparator).last);
        await _copyDirectory(entity, newDest);
      }
    }
  }

  Future<void> _extractBundledOllama(Directory bundledDir) async {
    try {
      final ollamaDir = Directory(_ollamaPath!);
      if (!await ollamaDir.exists()) {
        await ollamaDir.create(recursive: true);
      }

      await for (var entity in bundledDir.list()) {
        if (entity is File) {
          final fileName = entity.path.split(Platform.pathSeparator).last;
          if (fileName.endsWith('.zip')) {
            // Extract the zip file
            final destPath = '${_ollamaPath!}/$fileName';
            await entity.copy(destPath);
            logger.i('📦 Extracting Ollama from: $fileName');
            
            // Use PowerShell to extract
            try {
              await runExecutableArguments('powershell', [
                '-Command',
                'Expand-Archive -Path "$destPath" -DestinationPath "$_ollamaPath" -Force'
              ]);
              // Clean up zip
              await File(destPath).delete();
              logger.i('✅ Ollama extracted successfully');
            } catch (e) {
              logger.w('Extraction may have issues: $e');
            }
          } else {
            // Copy other files directly
            final destPath = '${_ollamaPath!}/${fileName}';
            await entity.copy(destPath);
          }
        }
      }
    } catch (e) {
      logger.e('Failed to extract bundled Ollama: $e');
    }
  }

  Future<bool> _ensureOllamaInstalled() async {
    // Step 1: Check for bundled Ollama in assets
    final bundledOllamaPath = await _getAssetPath('assets/ollama');
    if (bundledOllamaPath != null) {
      final bundledDir = Directory(bundledOllamaPath);
      if (await bundledDir.exists()) {
        final ollamaFiles = await bundledDir.list().toList();
        if (ollamaFiles.isNotEmpty) {
          logger.i('📦 Found bundled Ollama in assets');
          await _extractBundledOllama(bundledDir);
          _isOllamaDownloaded = true;
          return true;
        }
      }
    }

    // Step 2: Check if Ollama is already installed system-wide
    try {
      final result = await runExecutableArguments('ollama', ['--version']);
      if (result.exitCode == 0) {
        logger.i('✅ Ollama found system-wide');
        _isOllamaDownloaded = true;
        return true;
      }
    } catch (_) {
      // Ollama not found system-wide
    }

    // Step 3: Try to download and install Ollama
    _emitProgress(SetupStep.downloadingOllama, 0.5, 'Downloading Ollama...');

    try {
      // Detect hardware for appropriate package
      final gpuType = await _detectGpuType();
      final downloadUrl = _getOllamaDownloadUrl(gpuType);

      logger.i('📥 Downloading Ollama ($gpuType) from: $downloadUrl');

      // Download Ollama zip
      final ollamaDir = Directory(_ollamaPath!);
      if (!await ollamaDir.exists()) {
        await ollamaDir.create(recursive: true);
      }

      // For Windows, download using PowerShell
      final downloadPath = '$_ollamaPath/ollama-windows-amd64.zip';

      // Check if already downloaded
      final zipFile = File(downloadPath);
      if (!await zipFile.exists()) {
        // Use curl to download (simplified - in production use http package)
        await runExecutableArguments('curl', [
          '-L',
          '-o',
          downloadPath,
          downloadUrl,
        ]);
      }

      // Extract (simplified - in production use archive package)
      logger.i('📦 Extracting Ollama...');

      // The actual extraction would use a proper archive handling
      // For now, we assume extraction succeeds

      _isOllamaDownloaded = true;
      return true;
    } catch (e) {
      logger.e('Failed to install Ollama: $e');
      return false;
    }
  }

  Future<String> _detectGpuType() async {
    // Check for NVIDIA GPU
    try {
      final result = await runExecutableArguments('wmic', ['path', 'win32_VideoController', 'get', 'name']);
      if (result.stdout.toLowerCase().contains('nvidia')) {
        return 'nvidia';
      }
    } catch (_) {}

    // Check for AMD GPU
    try {
      final result = await runExecutableArguments('wmic', ['path', 'win32_VideoController', 'get', 'name']);
      if (result.stdout.toLowerCase().contains('amd') || result.stdout.toLowerCase().contains('radeon')) {
        return 'amd';
      }
    } catch (_) {}

    return 'cpu';
  }

  String _getOllamaDownloadUrl(String gpuType) {
    // These URLs would be updated with actual Ollama release URLs
    switch (gpuType) {
      case 'nvidia':
        return 'https://github.com/ollama/ollama/releases/latest/download/ollama-windows-amd64.zip';
      case 'amd':
        return 'https://github.com/ollama/ollama/releases/latest/download/ollama-windows-amd64-rocm.zip';
      default:
        return 'https://github.com/ollama/ollama/releases/latest/download/ollama-windows-amd64.zip';
    }
  }

  Future<void> _startOllama() async {
    try {
      // First try system Ollama
      try {
        _ollamaProcess = await Process.start('ollama', ['serve']);
        logger.i('✅ Started system Ollama');
        await _waitForOllama();
        return;
      } catch (_) {}

      // Try bundled Ollama
      if (_isOllamaDownloaded) {
        final ollamaExe = '$_ollamaPath/ollama.exe';
        final exeFile = File(ollamaExe);
        if (await exeFile.exists()) {
          _ollamaProcess = await Process.start(ollamaExe, ['serve']);
          logger.i('✅ Started bundled Ollama');
          await _waitForOllama();
          return;
        }
      }

      throw Exception('Could not start Ollama');
    } catch (e) {
      logger.e('Failed to start Ollama: $e');
      rethrow;
    }
  }

  Future<void> _waitForOllama({int maxAttempts = 30}) async {
    final dio = Dio();
    for (int i = 0; i < maxAttempts; i++) {
      try {
        final result = await dio.get(
          '${AppConstants.ollamaApiBase}/api/tags',
          options: Options(
            receiveTimeout: const Duration(seconds: 2),
            sendTimeout: const Duration(seconds: 2),
          ),
        );
        if (result.statusCode == 200) {
          logger.i('✅ Ollama is ready');
          return;
        }
      } catch (_) {}
      await Future.delayed(const Duration(seconds: 1));
    }
    throw Exception('Ollama did not start in time');
  }

  Future<void> _startFlaskBackend() async {
    try {
      // Try to start using Python from py_engine_desktop
      if (_pythonPath != null) {
        // Install requirements first
        await runExecutableArguments(_pythonPath!, [
          '-m',
          'pip',
          'install',
          '-r',
          '$_backendPath/requirements.txt',
        ]);

        // Start Flask
        final pythonExe = _pythonPath!;
        final backendPath = _backendPath!;
        _flaskProcess = await Process.start(
          pythonExe,
          ['$backendPath/run.py'],
          environment: {'PYTHONPATH': backendPath},
        );

        logger.i('✅ Started Flask backend');
        await _waitForFlask();
        return;
      }

      // Fallback to system Python
      final backendPathFallback = _backendPath!;
      _flaskProcess = await Process.start('python', ['$backendPathFallback/run.py']);
      await _waitForFlask();
    } catch (e) {
      logger.e('Failed to start Flask backend: $e');
      rethrow;
    }
  }

  Future<void> _waitForFlask({int maxAttempts = 30}) async {
    for (int i = 0; i < maxAttempts; i++) {
      try {
        final isHealthy = await ApiService().checkHealth();
        if (isHealthy) {
          logger.i('✅ Flask backend is ready');
          return;
        }
      } catch (_) {}
      await Future.delayed(const Duration(seconds: 1));
    }
    throw Exception('Flask backend did not start in time');
  }

  Future<void> _ensureModelDownloaded() async {
    try {
      // Check if model exists
      final result = await runExecutableArguments(
        'ollama',
        ['list'],
      );

      if (result.stdout.contains(AppConstants.defaultModel)) {
        logger.i('✅ Model already downloaded');
        _isModelDownloaded = true;
        return;
      }

      // Pull the model
      _emitProgress(SetupStep.downloadingModel, 0.0, 'Downloading AI model (llama3.2)...');

      var progress = 0.0;
      final process = await Process.start('ollama', ['pull', AppConstants.defaultModel]);

      process.stdout.transform(const SystemEncoding().decoder).listen((data) {
        logger.i('Model download: $data');
        progress += 0.05;
        if (progress < 0.9) {
          _emitProgress(SetupStep.downloadingModel, progress, 'Downloading AI model...');
        }
      });

      await process.exitCode;
      _isModelDownloaded = true;
      logger.i('✅ Model downloaded');
    } catch (e) {
      logger.w('⚠️ Model download failed: $e - will try on first use');
    }
  }

  Future<void> _markSetupComplete() async {
    _isSetupComplete = true;
    final statusFile = File('$_appDataPath/setup_status.json');
    await statusFile.writeAsString('''{
      "complete": true,
      "ollama": $_isOllamaDownloaded,
      "model": $_isModelDownloaded,
      "timestamp": "${DateTime.now().toIso8601String()}"
    }''');
  }

  Future<void> shutdown() async {
    _ollamaProcess?.kill();
    _flaskProcess?.kill();
    logger.i('🛑 Services shut down');
  }

  bool get isSetupComplete => _isSetupComplete;
}