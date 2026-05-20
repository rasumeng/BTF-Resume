import 'package:flutter/material.dart';
import 'package:window_manager/window_manager.dart';
import 'package:flutter_desktop_updater/flutter_desktop_updater.dart';
import 'config/colors.dart';
import 'config/typography.dart';
import 'features/splash/presentation/splash_screen.dart';
import 'features/setup/presentation/screens/setup_screen.dart';
import 'features/resumes/presentation/screens/my_resumes_screen.dart';
import 'features/polish/presentation/screens/polish_screen.dart';
import 'features/tailor/presentation/screens/tailor_screen.dart';
import 'features/feedback/presentation/screens/feedback_screen.dart';
import 'shared/mixins/has_clear_inputs.dart';
import 'core/services/app_initialization_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Configure updater
  UpdateConfig().configure(
    updateJsonUrl: 'https://rasumeng.github.io/BT-Resume/releases/app-archive.json',
  );

  // Set minimum window size
  await windowManager.ensureInitialized();
  const windowOptions = WindowOptions(
    minimumSize: Size(1400, 850), // Minimum width x height
    size: Size(1600, 900),
  );
  windowManager.waitUntilReadyToShow(windowOptions, () async {
    await windowManager.show();
    await windowManager.focus();
  });

  runApp(const BTFResumeApp());
}

class BTFResumeApp extends StatelessWidget {
  const BTFResumeApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Beyond The Resume',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        primaryColor: AppColors.darkPrimary,
        scaffoldBackgroundColor: AppColors.darkPrimary,
        colorScheme: ColorScheme.dark(
          primary: AppColors.gold,
          secondary: AppColors.darkSecondary,
          surface: AppColors.dark2,
          error: AppColors.errorRed,
        ),
      ),
      home: const SetupWrapper(),
    );
  }
}

// ============================================================================
// SetupWrapper - Handles first-time setup before main app
// ============================================================================
class SetupWrapper extends StatefulWidget {
  const SetupWrapper({Key? key}) : super(key: key);

  @override
  State<SetupWrapper> createState() => _SetupWrapperState();
}

class _SetupWrapperState extends State<SetupWrapper> {
  bool _isSetupComplete = false;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _checkSetupStatus();
  }

  Future<void> _checkSetupStatus() async {
    final initService = AppInitializationService();
    final isComplete = await initService.checkSetupStatus();
    setState(() {
      _isSetupComplete = isComplete;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        backgroundColor: AppColors.darkPrimary,
        body: Center(
          child: CircularProgressIndicator(
            color: AppColors.gold,
          ),
        ),
      );
    }

    if (!_isSetupComplete) {
      return SetupScreen(
        onComplete: () {
          setState(() {
            _isSetupComplete = true;
          });
        },
      );
    }

    return const SplashWrapper();
  }
}

// ============================================================================
// SplashWrapper - Shows splash screen then transitions to home
// ============================================================================
class SplashWrapper extends StatefulWidget {
  const SplashWrapper({Key? key}) : super(key: key);

  @override
  State<SplashWrapper> createState() => _SplashWrapperState();
}

class _SplashWrapperState extends State<SplashWrapper> {
  bool _isReady = false;

  @override
  void initState() {
    super.initState();
    _checkForUpdates();
  }

  Future<void> _checkForUpdates() async {
    await UpdateManager().checkForUpdate();
  }

  @override
  Widget build(BuildContext context) {
    if (!_isReady) {
      return SplashScreen(
        onReady: () {
          setState(() {
            _isReady = true;
          });
        },
      );
    }

    return const HomeScreen();
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  int _previousTabIndex = 0;
  
  // Keys to access screen state
  final GlobalKey<State> _myResumesKey = GlobalKey();
  final GlobalKey<State> _polishKey = GlobalKey();
  final GlobalKey<State> _tailorKey = GlobalKey();
  final GlobalKey<State> _feedbackKey = GlobalKey();

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _tabController.addListener(_onTabChanged);
  }

  void _onTabChanged() {
    if (_tabController.indexIsChanging) return;
    
    final int fromIndex = _previousTabIndex;
    final int toIndex = _tabController.index;
    
    if (fromIndex != toIndex) {
      _clearInputsForTab(fromIndex);
      _previousTabIndex = toIndex;
    }
  }

  void _clearInputsForTab(int tabIndex) {
    switch (tabIndex) {
      case 0: // My Resumes
        break; // No input fields to clear
      case 1: // Polish
        try {
          final polishState = _polishKey.currentState;
          if (polishState != null) {
            (polishState as dynamic).clearInputFields();
          }
        } catch (_) {}
        break;
      case 2: // Tailor
        try {
          final tailorState = _tailorKey.currentState;
          if (tailorState != null) {
            (tailorState as dynamic).clearInputFields();
          }
        } catch (_) {}
        break;
      case 3: // Feedback
        try {
          final feedbackState = _feedbackKey.currentState;
          if (feedbackState != null) {
            (feedbackState as dynamic).clearInputFields();
          }
        } catch (_) {}
        break;
    }
  }

  @override
  void dispose() {
    _tabController.removeListener(_onTabChanged);
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.darkPrimary,
      appBar: AppBar(
        backgroundColor: AppColors.darkPrimary,
        elevation: 0,
        title: Row(
          children: [
            Image.asset(
              'assets/icons/BTR-Logo.png',
              width: 100,
              height: 100,
              fit: BoxFit.contain,
            ),
            const SizedBox(width: 16),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Save Time, Start Applying',
                  style: AppTypography.headingPageTitle.copyWith(
                    fontSize: 20,
                    color: AppColors.cream,
                  ),
                ),
                Text(
                  'All-in-One Resume Builder Powered by AI',
                  style: AppTypography.bodySmall.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ],
        ),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: '📄 MY RESUMES'),
            Tab(text: '✨ POLISH'),
            Tab(text: '🎯 TAILOR'),
            Tab(text: '⚡ FEEDBACK'),
          ],
          labelColor: AppColors.gold,
          unselectedLabelColor: AppColors.textSecondary,
          dividerColor: AppColors.gold,
          indicator: UnderlineTabIndicator(
            borderSide: BorderSide(
              color: AppColors.gold,
              width: 4,
            ),
          ),
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          // My Resumes Tab
          MyResumesScreen(key: _myResumesKey),
          // Polish Tab
          PolishScreen(key: _polishKey),
          // Tailor Tab
          TailorScreen(key: _tailorKey),
          // Experience Tab
          FeedbackScreen(key: _feedbackKey),
        ],
      ),
    );
  }

  Widget _buildPlaceholderTab(String title) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            title,
            style: AppTypography.headingPageTitle.copyWith(
              color: AppColors.cream,
            ),
          ),
          const SizedBox(height: 16),
          Text(
            'Ready to build',
            style: AppTypography.bodyLarge.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
        ],
      ),
    );
  }
}
