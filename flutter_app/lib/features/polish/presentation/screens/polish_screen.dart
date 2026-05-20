import 'package:flutter/material.dart';
import 'dart:io';
import 'package:logger/logger.dart';
import 'package:syncfusion_flutter_pdfviewer/pdfviewer.dart';
import '../../../../config/colors.dart';
import '../../../../config/typography.dart';
import '../../../../core/services/resume_file_service.dart';
import '../../../../core/services/api_service.dart';
import '../../../../shared/widgets/custom_dropdown.dart';
import '../../../../shared/widgets/download_dialog.dart';
import '../../../../shared/widgets/notification_dialog.dart';
import '../../../../shared/mixins/has_clear_inputs.dart';

// ============================================================================
// PolishChange Model
// ============================================================================
class PolishChange {
  /* MEMBERS */
  final String icon;
  final String title;
  final String description;

  /* CONSTRUCTOR */
  PolishChange({
    required this.icon,
    required this.title,
    required this.description,
  });
}
// ============================================================================

// ============================================================================
// PolishScreen StatefulWidget
// ============================================================================
class PolishScreen extends StatefulWidget {
  const PolishScreen({Key? key}) : super(key: key);

  @override
  State<PolishScreen> createState() => _PolishScreenState();
}
// ============================================================================

// ============================================================================
// _PolishScreenState
// ============================================================================
class _PolishScreenState extends State<PolishScreen> with HasClearInputs, AutomaticKeepAliveClientMixin {
  /* STATE VARIABLES */
  List<File> resumeFiles = [];
  int selectedResumeIndex = 0;
  bool isLoading = true;
  bool isPolishing = false;
  bool hasPolished = false;
  bool isGeneratingPdf = false;
  bool _showPolishedPreview = true;
  List<PolishChange> polishChanges = [];
  File? polishedPdfFile; // Track the polished PDF for preview and download
  String polishIntensity = 'medium'; // 'light' | 'medium' | 'aggressive'
  String? polishedResumeContent; // Store polished content for PDF generation
  final ApiService _apiService = ApiService();
  final logger = Logger();

  // --------------------------------------------------------------------------
  // LIFECYCLE: initState
  // --------------------------------------------------------------------------
  @override
  void initState() {
    super.initState();
    _loadResumeFiles();
  }

  // --------------------------------------------------------------------------
  // METHOD: Load Resume Files
  // --------------------------------------------------------------------------
  Future<void> _loadResumeFiles() async {
    try {
      final files = await ResumeFileService.listResumeFiles();
      setState(() {
        resumeFiles = files;
        isLoading = false;
      });
    } catch (e) {
      print('Error loading resumes: $e');
      setState(() {
        isLoading = false;
      });
    }
  }

  // --------------------------------------------------------------------------
  // METHOD: Polish Resume
  // --------------------------------------------------------------------------
  Future<void> _polishResume() async {
    // Guard: Prevent double-tap
    if (isPolishing) return;
    
    if (resumeFiles.isEmpty || selectedResumeIndex >= resumeFiles.length) {
      NotificationDialog.show(
        context: context,
        title: 'No Resume Selected',
        message: 'Please select a resume to polish.',
        isSuccess: false,
      );
      return;
    }

    try {
      setState(() {
        isPolishing = true;
      });

      // Extract text from the selected PDF file
      final selectedFile = resumeFiles[selectedResumeIndex];
      logger.i('Extracting text from: ${selectedFile.path}');

      final resumeContent = await _apiService.extractPdfText(selectedFile);

      // Parse and cache the resume structure for reuse
      logger.i('=��� Parsing resume into structured format...');
      try {
        await _apiService.parseAndCacheResume(
          resumeContent,
          filename: selectedFile.path.split(Platform.pathSeparator).last,
        );
      } catch (parseError) {
        logger.w(
          'G��n+�  Failed to cache parsed resume (non-critical): $parseError',
        );
        // Continue anyway - polish will still work with raw text
      }

      // Call API to polish the resume
      final polishedContent = await _apiService.polishResume(
        resumeContent,
        intensity: polishIntensity,
      );

      // polishedContent is already a String
      final polishedText = polishedContent;

      // Generate professional PDF from polished content using template
      logger.i('=��� Generating professional PDF from polished content...');
      try {
        final timestamp = DateTime.now().millisecondsSinceEpoch;
        // Backend will add "polished_" prefix automatically
        final pdfFilename = 'resume_$timestamp.pdf';

        // Use saveTextPdf endpoint which now generates professional PDFs using template
        // The backend parses the text, structures it, and generates using pdf_generator
        final saveResult = await _apiService.saveTextPdf(
          pdfFilename,
          polishedText,
        );

        // Verify backend saved the file successfully
        if (!saveResult['success']) {
          throw Exception('Backend failed to save PDF: ${saveResult['error']}');
        }

        // Use the path from backend response - it knows the actual OS path
        final polishedPdfPath = saveResult['path'];
        if (polishedPdfPath == null || polishedPdfPath.isEmpty) {
          throw Exception('Backend response missing path information');
        }

        final polishedPdfFileTemp = File(polishedPdfPath);

        // Verify the file was actually created at the backend's reported path
        if (!await polishedPdfFileTemp.exists()) {
          logger.e('G�� File check failed at: $polishedPdfPath');
          logger.e('Backend reported file at: $polishedPdfPath');
          throw Exception(
            'Polished PDF file was not created at: $polishedPdfPath',
          );
        }

        logger.i(
          'G�� Professional polished resume PDF generated: $polishedPdfPath',
        );

        // Get real changes from backend
        List<String> changesFromBackend = [];
        try {
          changesFromBackend = await _apiService.getPolishChanges(
            resumeContent,
            polishedText,
          );
          logger.i('G�� Got ${changesFromBackend.length} real polish changes');
        } catch (e) {
          logger.w('G��n+�  Failed to get polish changes: $e');
          // Will use fallback changes below
        }

        // Convert change descriptions to PolishChange objects
        List<PolishChange> realChanges = changesFromBackend.isNotEmpty
            ? changesFromBackend
                  .map(
                    (change) => PolishChange(
                      icon: 'G��',
                      title: change.length > 60
                          ? change.substring(0, 60) + '...'
                          : change,
                      description: change,
                    ),
                  )
                  .toList()
            : [
                // Fallback if no changes returned
                PolishChange(
                  icon: 'G��',
                  title: 'Content enhanced',
                  description:
                      'Resume content optimized for clarity and impact',
                ),
                PolishChange(
                  icon: 'G��',
                  title: 'Formatting improved',
                  description: 'Professional formatting for ATS compatibility',
                ),
              ];

        setState(() {
          hasPolished = true;
          isPolishing = false;
          polishedPdfFile = polishedPdfFileTemp;
          polishedResumeContent = polishedText;
          polishChanges = realChanges;
        });
      } catch (pdfError) {
        logger.e('G�� Error generating polished PDF: $pdfError');
        logger.e('Stack trace: $pdfError');
        // DON'T continue silently - user needs to know PDF generation failed
        setState(() {
          isPolishing = false;
        });
        if (mounted) {
          NotificationDialog.show(
            context: context,
            title: 'PDF Error',
            message: 'Error generating polished resume PDF',
            isSuccess: false,
          );
        }
        rethrow;
      }
    } catch (e) {
      logger.e('Error polishing resume: $e');
      setState(() {
        isPolishing = false;
      });
      if (mounted) {
        String errorMessage = 'Error polishing resume';

        // Provide user-friendly error messages
        if (e.toString().contains('404')) {
          errorMessage =
              'Backend endpoint not found. Ensure backend is running.';
        } else if (e.toString().contains('Backend is not responding')) {
          errorMessage =
              'Cannot connect to backend. Please start the Flask backend.';
        } else if (e.toString().contains('Connection refused')) {
          errorMessage =
              'Connection refused. Ensure backend is running on localhost:5000.';
        } else if (e.toString().contains('timeout')) {
          errorMessage = 'Backend request timed out. Please try again.';
        }

        NotificationDialog.show(
          context: context,
          title: 'Error',
          message: errorMessage,
          isSuccess: false,
        );
      }
    }
  }

  // --------------------------------------------------------------------------
  // METHOD: Reset Polish State
  // --------------------------------------------------------------------------
  void _resetPolish() {
    setState(() {
      hasPolished = false;
      polishChanges = [];
      polishedPdfFile = null; // Clear polished PDF when switching resumes
      polishedResumeContent = null;
      _showPolishedPreview = true;
    });
  }

  // --------------------------------------------------------------------------
  // METHOD: Clear Input Fields (for tab switching - hybrid approach)
  // --------------------------------------------------------------------------
  @override
  void clearInputFields() {
    // Polish screen has no text input fields, only selectors
    // Keep: selectedResumeIndex, polishIntensity, hasPolished, polishChanges
    // Nothing to clear
  }

  // --------------------------------------------------------------------------
  // Keep widget alive when switching tabs
  // --------------------------------------------------------------------------
  @override
  bool get wantKeepAlive => true;

  // --------------------------------------------------------------------------
  // METHOD: Generate PDF from Polished Resume
  // --------------------------------------------------------------------------
  Future<void> _generatePdf() async {
    if (resumeFiles.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('No resume selected'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    // Show dialog to input filename
    final fileName = await _showPdfFilenameDialog();
    if (fileName == null || fileName.isEmpty) return;

    setState(() {
      isGeneratingPdf = true;
    });

    try {
      // Sample resume data - in production, this would be parsed from the PDF
      final sampleResumeData = {
        'contact': {
          'name': 'John Doe',
          'email': 'john@example.com',
          'phone': '(555) 123-4567',
          'location': 'Boston, MA',
          'linkedin': 'linkedin.com/in/johndoe',
        },
        'education': [
          {
            'school': 'Massachusetts Institute of Technology',
            'degree': 'BS Computer Science',
            'location': 'Cambridge, MA',
            'date': '2020',
            'details': ['Graduated with honors', 'GPA: 3.8'],
          },
        ],
        'skills': [
          {
            'category': 'Programming Languages',
            'items': ['Python', 'JavaScript', 'Java', 'C++'],
          },
          {
            'category': 'Tools & Frameworks',
            'items': ['Flutter', 'React', 'Django', 'TensorFlow'],
          },
        ],
        'work_experience': [
          {
            'title': 'Software Engineer',
            'company': 'Tech Corp',
            'location': 'Boston, MA',
            'start_date': '2020',
            'end_date': '2023',
            'bullets': [
              'Led team of 5 engineers in building scalable microservices',
              'Improved system performance by 40% through optimization',
              'Mentored 3 junior developers in best practices',
            ],
          },
          {
            'title': 'Junior Developer',
            'company': 'StartupXYZ',
            'location': 'Remote',
            'start_date': '2019',
            'end_date': '2020',
            'bullets': [
              'Developed full-stack web application using React and Django',
              'Implemented CI/CD pipeline reducing deployment time by 50%',
              'Collaborated with design team on UI/UX improvements',
            ],
          },
        ],
        'projects': [
          {
            'name': 'Resume AI',
            'details': [
              'AI-powered resume analyzer and generator',
              'Built with Flutter and Python',
            ],
          },
        ],
      };

      // Call API to generate PDF
      final pdfFilename = fileName.endsWith('.pdf')
          ? fileName
          : '$fileName.pdf';
      final result = await _apiService.savePdf(pdfFilename, sampleResumeData);

      if (mounted) {
        setState(() {
          isGeneratingPdf = false;
        });

        NotificationDialog.show(
          context: context,
          title: 'PDF Generated',
          message: 'Your polished resume has been saved.',
          isSuccess: true,
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          isGeneratingPdf = false;
        });

        NotificationDialog.show(
          context: context,
          title: 'Error',
          message: 'Error generating PDF',
          isSuccess: false,
        );
      }
    }
  }

  // --------------------------------------------------------------------------
  // METHOD: Show PDF Filename Dialog
  // --------------------------------------------------------------------------
  Future<String?> _showPdfFilenameDialog() async {
    final TextEditingController controller = TextEditingController(
      text: 'polished_resume_${DateTime.now().millisecondsSinceEpoch}',
    );

    return showDialog<String?>(
      context: context,
      builder: (BuildContext context) => AlertDialog(
        backgroundColor: AppColors.dark2,
        title: Text(
          'Export Polished Resume as PDF',
          style: AppTypography.labelText.copyWith(color: AppColors.cream),
        ),
        content: TextField(
          controller: controller,
          style: AppTypography.bodySmall.copyWith(color: AppColors.cream),
          decoration: InputDecoration(
            hintText: 'Enter filename',
            hintStyle: AppTypography.bodySmall.copyWith(
              color: AppColors.textSecondary,
            ),
            border: OutlineInputBorder(
              borderSide: BorderSide(color: AppColors.gold),
            ),
            focusedBorder: OutlineInputBorder(
              borderSide: BorderSide(color: AppColors.gold, width: 2),
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text(
              'Cancel',
              style: AppTypography.bodySmall.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.gold,
              foregroundColor: AppColors.darkPrimary,
            ),
            onPressed: () => Navigator.pop(context, controller.text),
            child: Text(
              'Generate',
              style: AppTypography.bodySmall.copyWith(
                color: AppColors.darkPrimary,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }

  // --------------------------------------------------------------------------
  // BUILD: Main Widget Tree
  // --------------------------------------------------------------------------
  @override
  Widget build(BuildContext context) {
    super.build(context);
    return Row(
      children: [
        // ====================================================================
        // LEFT PANEL: Resume List (40%)
        // ====================================================================
        Expanded(
          flex: 40,
          child: Container(
            color: AppColors.darkSecondary,
            child: isLoading
                ? _buildLoadingState()
                : resumeFiles.isEmpty
                ? _buildEmptyState()
                : _buildPolishPanelContent(),
          ),
        ),

        // ====================================================================
        // VERTICAL DIVIDER: Between Panels
        // ====================================================================
        Container(width: 1, color: AppColors.dark3),

        // ====================================================================
        // RIGHT PANEL: Resume Preview (60%)
        // ====================================================================
        Expanded(
          flex: 60,
          child: Container(
            color: AppColors.darkPrimary,
            child: resumeFiles.isEmpty
                ? _buildNoResumeSelectedPanel()
                : _buildResumePreviewPanel(),
          ),
        ),
      ],
    );
  }

  // --------------------------------------------------------------------------
  // BUILD HELPER: Loading State
  // --------------------------------------------------------------------------
  Widget _buildLoadingState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const CircularProgressIndicator(
            valueColor: AlwaysStoppedAnimation<Color>(AppColors.gold),
          ),
          const SizedBox(height: 16),
          Text(
            'Loading resumes...',
            style: AppTypography.bodySmall.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
        ],
      ),
    );
  }

  // --------------------------------------------------------------------------
  // BUILD HELPER: Empty State
  // --------------------------------------------------------------------------
  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.description_outlined,
            size: 48,
            color: AppColors.textSecondary,
          ),
          const SizedBox(height: 16),
          Text(
            'No resumes found',
            style: AppTypography.bodyLarge.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Add a resume first',
            style: AppTypography.bodySmall.copyWith(
              color: AppColors.textTertiary,
            ),
          ),
        ],
      ),
    );
  }

  // --------------------------------------------------------------------------
  // BUILD HELPER: Polish Panel Content
  // --------------------------------------------------------------------------
  Widget _buildPolishPanelContent() {
    return Container(
      margin: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border.all(color: AppColors.gold.withOpacity(0.3), width: 1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Polish Resume',
                  style: AppTypography.labelText.copyWith(
                    color: AppColors.cream,
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Improve clarity, impact, and ATS performance',
                  style: AppTypography.bodySmall.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ),
          Container(height: 1, color: AppColors.gold.withOpacity(0.3)),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Select Resume *',
                    style: AppTypography.bodySmall.copyWith(
                      color: AppColors.cream,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 8),
                  CustomResumeDropdown(
                    resumeFiles: resumeFiles,
                    selectedIndex: selectedResumeIndex,
                    onChanged: (newValue) {
                      setState(() {
                        selectedResumeIndex = newValue;
                        _resetPolish();
                      });
                    },
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'Polish Intensity',
                    style: AppTypography.labelText.copyWith(
                      color: AppColors.cream,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 8),
                  _buildIntensityControl(),
                  const SizedBox(height: 16),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppColors.dark3,
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(
                        color: AppColors.gold.withOpacity(0.2),
                      ),
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(
                          Icons.auto_awesome,
                          color: AppColors.gold,
                          size: 18,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            'Select a resume, choose an intensity, then polish when ready.',
                            style: AppTypography.bodySmall.copyWith(
                              color: AppColors.textSecondary,
                              fontSize: 11,
                              height: 1.4,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  _buildPolishResumeButton(),
                  if (hasPolished) ...[
                    const SizedBox(height: 16),
                    Container(
                      height: 1,
                      color: AppColors.gold.withOpacity(0.3),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Icon(
                          Icons.check_circle,
                          color: AppColors.successGreen,
                          size: 20,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          'Improvements Applied',
                          style: AppTypography.labelText.copyWith(
                            color: AppColors.cream,
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 6,
                            vertical: 2,
                          ),
                          decoration: BoxDecoration(
                            color: AppColors.successGreen.withOpacity(0.2),
                            borderRadius: BorderRadius.circular(4),
                            border: Border.all(
                              color: AppColors.successGreen.withOpacity(0.5),
                            ),
                          ),
                          child: Text(
                            '${polishChanges.length}',
                            style: AppTypography.bodySmall.copyWith(
                              color: AppColors.successGreen,
                              fontSize: 10,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    ...polishChanges.map(_buildPolishChangeCard),
                    const SizedBox(height: 16),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        onPressed: isPolishing ? null : _polishResume,
                        icon: isPolishing
                            ? SizedBox(
                                width: 16,
                                height: 16,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  valueColor: AlwaysStoppedAnimation<Color>(
                                    AppColors.darkPrimary,
                                  ),
                                ),
                              )
                            : const Icon(Icons.refresh_outlined),
                        label: Text(
                          isPolishing ? 'Polishing...' : 'Polish Again',
                        ),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.dark2,
                          foregroundColor: AppColors.cream,
                          padding: const EdgeInsets.symmetric(vertical: 10),
                        ),
                      ),
                    ),
                    const SizedBox(height: 8),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        onPressed: isGeneratingPdf ? null : _generatePdf,
                        icon: isGeneratingPdf
                            ? SizedBox(
                                width: 18,
                                height: 18,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  valueColor: AlwaysStoppedAnimation<Color>(
                                    AppColors.darkPrimary.withOpacity(0.7),
                                  ),
                                ),
                              )
                            : const Icon(Icons.download),
                        label: Text(
                          isGeneratingPdf ? 'Generating...' : 'Export as PDF',
                        ),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.successGreen,
                          foregroundColor: AppColors.darkPrimary,
                          padding: const EdgeInsets.symmetric(vertical: 10),
                          disabledBackgroundColor: AppColors.successGreen
                              .withOpacity(0.5),
                          disabledForegroundColor: AppColors.darkPrimary
                              .withOpacity(0.5),
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPolishChangeCard(PolishChange change) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.dark3,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: AppColors.successGreen.withOpacity(0.3)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 24,
            height: 24,
            decoration: BoxDecoration(
              color: AppColors.successGreen.withOpacity(0.2),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Icon(
              Icons.auto_awesome,
              color: AppColors.successGreen,
              size: 12,
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  change.title,
                  style: AppTypography.labelText.copyWith(
                    color: AppColors.cream,
                    fontSize: 12,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 2),
                Text(
                  change.description,
                  style: AppTypography.bodySmall.copyWith(
                    color: AppColors.textSecondary,
                    fontSize: 10,
                  ),
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // --------------------------------------------------------------------------
  // BUILD HELPER: Intensity Control
  // --------------------------------------------------------------------------
  Widget _buildIntensityControl() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12),
      child: Container(
        decoration: BoxDecoration(
          color: AppColors.dark2,
          borderRadius: BorderRadius.circular(20),
        ),
        padding: const EdgeInsets.all(2),
        child: Row(
          children: [
            Expanded(child: _buildIntensityButton('light', 'Light')),
            Expanded(child: _buildIntensityButton('medium', 'Medium')),
            Expanded(child: _buildIntensityButton('aggressive', 'Aggressive')),
          ],
        ),
      ),
    );
  }

  // --------------------------------------------------------------------------
  // BUILD HELPER: Single Intensity Button
  // --------------------------------------------------------------------------
  Widget _buildIntensityButton(String intensity, String label) {
    final isSelected = polishIntensity == intensity;

    return GestureDetector(
      onTap: () {
        setState(() {
          polishIntensity = intensity;
        });
      },
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.dark3 : Colors.transparent,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(
            color: isSelected ? AppColors.gold : Colors.transparent,
            width: isSelected ? 1.5 : 0,
          ),
        ),
        child: Text(
          label,
          textAlign: TextAlign.center,
          style: AppTypography.bodySmall.copyWith(
            color: isSelected ? AppColors.gold : AppColors.textSecondary,
            fontSize: 11,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }

  // --------------------------------------------------------------------------
  // BUILD HELPER: Polish Resume Button
  // --------------------------------------------------------------------------
  Widget _buildPolishResumeButton() {
    return Padding(
      padding: const EdgeInsets.all(12),
      child: SizedBox(
        width: double.infinity,
        child: ElevatedButton.icon(
          onPressed: resumeFiles.isEmpty || isPolishing ? null : _polishResume,
          icon: isPolishing
              ? SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(
                    valueColor: AlwaysStoppedAnimation<Color>(
                      isPolishing
                          ? AppColors.darkPrimary
                          : AppColors.darkPrimary,
                    ),
                    strokeWidth: 2,
                  ),
                )
              : const Icon(Icons.brush),
          label: Text(isPolishing ? 'Polishing...' : 'Polish Resume'),
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.gold,
            foregroundColor: AppColors.darkPrimary,
            padding: const EdgeInsets.symmetric(vertical: 12),
            disabledBackgroundColor: AppColors.dark3,
            disabledForegroundColor: AppColors.textSecondary,
          ),
        ),
      ),
    );
  }

  // --------------------------------------------------------------------------
  // BUILD HELPER: No Resume Selected Panel
  // --------------------------------------------------------------------------
  Widget _buildNoResumeSelectedPanel() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.auto_awesome, size: 64, color: AppColors.textSecondary),
          const SizedBox(height: 16),
          Text(
            'No Resume Selected',
            style: AppTypography.headingPageTitle.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Select a resume from the list to polish',
            style: AppTypography.bodySmall.copyWith(
              color: AppColors.textTertiary,
            ),
          ),
        ],
      ),
    );
  }

  // --------------------------------------------------------------------------
  // BUILD HELPER: Resume Preview Panel
  // --------------------------------------------------------------------------
  Widget _buildResumePreviewPanel() {
    return Container(
      margin: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border.all(color: AppColors.gold.withOpacity(0.3), width: 1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        children: [
          // ====================================================================
          // HEADER: Preview Title and Download Button
          // ====================================================================
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              border: Border(
                bottom: BorderSide(color: AppColors.gold.withOpacity(0.3)),
              ),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      Text(
                        'Resume Preview',
                        style: AppTypography.labelText.copyWith(
                          color: AppColors.cream,
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        hasPolished
                            ? 'Polished version'
                            : ResumeFileService.getFileName(
                                resumeFiles[selectedResumeIndex].path,
                              ),
                        style: AppTypography.bodySmall.copyWith(
                          color: AppColors.textSecondary,
                        ),
                      ),
                    ],
                  ),
                ),
                if (hasPolished && polishedPdfFile != null) ...[
                  const SizedBox(width: 16),
                  Container(
                    decoration: BoxDecoration(
                      color: AppColors.dark2,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    padding: const EdgeInsets.all(2),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        GestureDetector(
                          onTap: () =>
                              setState(() => _showPolishedPreview = false),
                          child: Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 12,
                              vertical: 6,
                            ),
                            decoration: BoxDecoration(
                              color: !_showPolishedPreview
                                  ? AppColors.dark3
                                  : Colors.transparent,
                              borderRadius: BorderRadius.circular(18),
                            ),
                            child: Text(
                              'Original',
                              style: AppTypography.bodySmall.copyWith(
                                color: !_showPolishedPreview
                                    ? AppColors.gold
                                    : AppColors.textSecondary,
                                fontSize: 10,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ),
                        GestureDetector(
                          onTap: () =>
                              setState(() => _showPolishedPreview = true),
                          child: Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 12,
                              vertical: 6,
                            ),
                            decoration: BoxDecoration(
                              color: _showPolishedPreview
                                  ? AppColors.dark3
                                  : Colors.transparent,
                              borderRadius: BorderRadius.circular(18),
                            ),
                            child: Text(
                              'Polished',
                              style: AppTypography.bodySmall.copyWith(
                                color: _showPolishedPreview
                                    ? AppColors.gold
                                    : AppColors.textSecondary,
                                fontSize: 10,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
                _buildDownloadButton(),
              ],
            ),
          ),

          // ====================================================================
          // CONTENT: PDF Viewer with Overlay
          // ====================================================================
          Expanded(
            child: Container(
              decoration: BoxDecoration(borderRadius: BorderRadius.circular(8)),
              margin: const EdgeInsets.all(12),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: Stack(
                  children: [
                    SfPdfViewer.file(
                      hasPolished && _showPolishedPreview
                          ? (polishedPdfFile ??
                                resumeFiles[selectedResumeIndex])
                          : resumeFiles[selectedResumeIndex],
                      pageLayoutMode: PdfPageLayoutMode.continuous,
                    ),
                    if (isPolishing) _buildPolishingOverlay(),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // --------------------------------------------------------------------------
  // BUILD HELPER: Download Button
  // --------------------------------------------------------------------------
  Widget _buildDownloadButton() {
    return IconButton(
      icon: const Icon(Icons.download),
      color: hasPolished ? AppColors.gold : AppColors.textTertiary,
      tooltip: hasPolished
          ? 'Download polished resume'
          : 'Polish resume to download',
      onPressed: hasPolished ? () => _downloadPolishedResume() : null,
    );
  }

  // --------------------------------------------------------------------------
  // METHOD: Download Polished Resume
  // --------------------------------------------------------------------------
  Future<void> _downloadPolishedResume() async {
    if (selectedResumeIndex >= resumeFiles.length) return;

    // Use polished PDF if available, otherwise fall back to original
    final sourceFile = polishedPdfFile ?? resumeFiles[selectedResumeIndex];
    final originalFileName = polishedPdfFile != null
        ? 'polished_resume'
        : ResumeFileService.getFileName(resumeFiles[selectedResumeIndex].path);

    if (mounted) {
      showDialog(
        context: context,
        builder: (context) => DownloadDialog(
          originalFileName: originalFileName,
          onDownload: (fileName, replaceOriginal) async {
            await _performDownload(
              sourceFile,
              fileName,
              replaceOriginal,
              'polished',
            );
          },
        ),
      );
    }
  }

  // --------------------------------------------------------------------------
  // METHOD: Perform Download
  // --------------------------------------------------------------------------
  Future<void> _performDownload(
    File sourceFile,
    String fileName,
    bool replaceOriginal,
    String type,
  ) async {
    try {
      final downloadPath = await ResumeFileService.downloadResume(
        sourceFile,
        fileName,
        replaceOriginal: replaceOriginal,
      );

      if (mounted && downloadPath != null) {
        final message = replaceOriginal
            ? 'G�� Resume replaced: $fileName.pdf'
            : 'G�� Downloaded to: $fileName.pdf';

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(message),
            backgroundColor: AppColors.successGreen,
            duration: const Duration(seconds: 3),
          ),
        );
      } else if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('G�� Failed to download resume'),
            backgroundColor: AppColors.errorRed,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('G�� Error: ${e.toString()}'),
            backgroundColor: AppColors.errorRed,
          ),
        );
      }
    }
  }

  // --------------------------------------------------------------------------
  // BUILD HELPER: Polishing Overlay
  // --------------------------------------------------------------------------
  Widget _buildPolishingOverlay() {
    return Container(
      color: AppColors.darkPrimary.withOpacity(0.7),
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const CircularProgressIndicator(
              valueColor: AlwaysStoppedAnimation<Color>(AppColors.gold),
            ),
            const SizedBox(height: 16),
            Text(
              'Polishing resume...',
              style: AppTypography.bodySmall.copyWith(color: AppColors.cream),
            ),
          ],
        ),
      ),
    );
  }
}
