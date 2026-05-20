import 'dart:async';
import 'package:flutter/material.dart';
import 'package:logger/logger.dart';
import '../../../../config/colors.dart';
import '../../../../config/typography.dart';
import '../../../../core/services/app_initialization_service.dart';

class SetupScreen extends StatefulWidget {
  final VoidCallback onComplete;

  const SetupScreen({
    Key? key,
    required this.onComplete,
  }) : super(key: key);

  @override
  State<SetupScreen> createState() => _SetupScreenState();
}

class _SetupScreenState extends State<SetupScreen> {
  final logger = Logger();
  final _initService = AppInitializationService();

  SetupStep _currentStep = SetupStep.notStarted;
  double _progress = 0.0;
  String _message = 'Preparing...';
  String? _error;
  StreamSubscription? _progressSubscription;

  @override
  void initState() {
    super.initState();
    _startSetup();
  }

  @override
  void dispose() {
    _progressSubscription?.cancel();
    super.dispose();
  }

  Future<void> _startSetup() async {
    _progressSubscription = _initService.progressStream.listen((progress) {
      setState(() {
        _currentStep = progress.step;
        _progress = progress.overallProgress;
        _message = progress.message;
        _error = progress.error;
      });
    });

    try {
      await _initService.runFullSetup();
      widget.onComplete();
    } catch (e) {
      setState(() {
        _error = e.toString();
      });
    }
  }

  String get _stepTitle {
    switch (_currentStep) {
      case SetupStep.notStarted:
        return 'Getting Ready';
      case SetupStep.initializingPython:
        return 'Setting Up Python';
      case SetupStep.extractingBackend:
        return 'Preparing Backend';
      case SetupStep.downloadingOllama:
        return 'Downloading AI Engine';
      case SetupStep.installingOllama:
        return 'Installing AI Engine';
      case SetupStep.downloadingModel:
        return 'Downloading AI Model';
      case SetupStep.startingServices:
        return 'Starting Services';
      case SetupStep.complete:
        return 'All Set!';
      case SetupStep.error:
        return 'Setup Failed';
    }
  }

  String get _stepDescription {
    switch (_currentStep) {
      case SetupStep.notStarted:
        return 'Preparing your resume assistant...';
      case SetupStep.initializingPython:
        return 'Setting up the Python runtime for AI processing';
      case SetupStep.extractingBackend:
        return 'Extracting backend services...';
      case SetupStep.downloadingOllama:
        return 'Downloading the Ollama AI engine (~500MB)';
      case SetupStep.installingOllama:
        return 'Installing Ollama on your system...';
      case SetupStep.downloadingModel:
        return 'Downloading the AI model. This may take a few minutes...';
      case SetupStep.startingServices:
        return 'Starting the AI and backend services...';
      case SetupStep.complete:
        return 'Your resume assistant is ready!';
      case SetupStep.error:
        return 'Something went wrong during setup.';
    }
  }

  IconData get _stepIcon {
    switch (_currentStep) {
      case SetupStep.notStarted:
        return Icons.settings;
      case SetupStep.initializingPython:
        return Icons.code;
      case SetupStep.extractingBackend:
        return Icons.archive;
      case SetupStep.downloadingOllama:
        return Icons.download;
      case SetupStep.installingOllama:
        return Icons.build;
      case SetupStep.downloadingModel:
        return Icons.model_training;
      case SetupStep.startingServices:
        return Icons.play_arrow;
      case SetupStep.complete:
        return Icons.check_circle;
      case SetupStep.error:
        return Icons.error;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.darkPrimary,
      body: Center(
        child: Container(
          width: 500,
          padding: const EdgeInsets.all(40),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Logo
              Image.asset(
                'assets/icons/BTR-Logo.png',
                width: 120,
                height: 120,
                fit: BoxFit.contain,
              ),
              const SizedBox(height: 24),

              // Title
              Text(
                'Beyond The Resume',
                style: AppTypography.headingPageTitle.copyWith(
                  color: AppColors.cream,
                  fontSize: 28,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'AI-Powered Resume Helper',
                style: AppTypography.bodyLarge.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
              const SizedBox(height: 48),

              // Setup card
              Container(
                padding: const EdgeInsets.all(32),
                decoration: BoxDecoration(
                  color: AppColors.dark2,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: AppColors.gold.withOpacity(0.3),
                    width: 1,
                  ),
                ),
                child: Column(
                  children: [
                    // Icon
                    Container(
                      width: 64,
                      height: 64,
                      decoration: BoxDecoration(
                        color: _currentStep == SetupStep.error
                            ? AppColors.errorRed.withOpacity(0.2)
                            : AppColors.gold.withOpacity(0.2),
                        shape: BoxShape.circle,
                      ),
                      child: Icon(
                        _stepIcon,
                        color: _currentStep == SetupStep.error
                            ? AppColors.errorRed
                            : AppColors.gold,
                        size: 32,
                      ),
                    ),
                    const SizedBox(height: 24),

                    // Step title
                    Text(
                      _stepTitle,
                      style: AppTypography.headingSectionTitle.copyWith(
                        color: AppColors.cream,
                      ),
                    ),
                    const SizedBox(height: 8),

                    // Step description
                    Text(
                      _stepDescription,
                      style: AppTypography.bodyLarge.copyWith(
                        color: AppColors.textSecondary,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 24),

                    // Progress bar
                    if (_currentStep != SetupStep.error &&
                        _currentStep != SetupStep.complete)
                      Column(
                        children: [
                          ClipRRect(
                            borderRadius: BorderRadius.circular(4),
                            child: LinearProgressIndicator(
                              value: _progress,
                              backgroundColor: AppColors.darkPrimary,
                              valueColor: AlwaysStoppedAnimation<Color>(
                                AppColors.gold,
                              ),
                              minHeight: 8,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            '${(_progress * 100).toInt()}%',
                            style: AppTypography.bodySmall.copyWith(
                              color: AppColors.gold,
                            ),
                          ),
                        ],
                      ),

                    // Error message
                    if (_error != null) ...[
                      const SizedBox(height: 16),
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: AppColors.errorRed.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Row(
                          children: [
                            Icon(
                              Icons.warning_amber,
                              color: AppColors.errorRed,
                              size: 20,
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                _error!,
                                style: AppTypography.bodySmall.copyWith(
                                  color: AppColors.errorRed,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _startSetup,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.gold,
                          foregroundColor: AppColors.darkPrimary,
                          padding: const EdgeInsets.symmetric(
                            horizontal: 32,
                            vertical: 12,
                          ),
                        ),
                        child: const Text('Retry'),
                      ),
                    ],
                  ],
                ),
              ),

              const SizedBox(height: 24),

              // System info
              Text(
                'First-time setup is required to enable AI features',
                style: AppTypography.bodySmall.copyWith(
                  color: AppColors.textSecondary.withOpacity(0.5),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}