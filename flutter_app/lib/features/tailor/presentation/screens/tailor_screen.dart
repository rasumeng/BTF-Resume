import 'package:flutter/material.dart';
import 'dart:io';
import 'package:logger/logger.dart';
import 'package:syncfusion_flutter_pdfviewer/pdfviewer.dart';
import '../../../../config/colors.dart';
import '../../../../config/typography.dart';
import '../../../../core/services/resume_file_service.dart';
import '../../../../shared/widgets/custom_dropdown.dart';
import '../../../../shared/widgets/download_dialog.dart';
import '../../../../shared/widgets/notification_dialog.dart';
import '../../../../shared/mixins/has_clear_inputs.dart';
import '../controllers/tailor_controller.dart';
import '../models/tailor_models.dart';

// ============================================================================
// TailorScreen StatefulWidget
// ============================================================================
class TailorScreen extends StatefulWidget {
  const TailorScreen({Key? key}) : super(key: key);

  @override
  State<TailorScreen> createState() => _TailorScreenState();
}
// ============================================================================

// ============================================================================
// _TailorScreenState
// ============================================================================
class _TailorScreenState extends State<TailorScreen> with HasClearInputs, AutomaticKeepAliveClientMixin {
  /* STATE VARIABLES */
  List<File> resumeFiles = [];
  int selectedResumeIndex = 0;
  bool isLoading = true;
  bool isTailoring = false;
  bool hasTailored = false;
  bool isGeneratingPdf = false;
  bool hasSeenFit = false;
  bool userChoseToTailor = false;
  String tailorIntensity = 'medium'; // 'light' | 'medium' | 'heavy'
  File? tailoredPdfFile;
  bool showOriginalPdf = false;
  int overallConfidence = 0;
  List<CategoryScore> categoryScores = [];
  List<TailorMatch> tailorMatches = [];
  GapAnalysis? tailorGaps;
  String changesSummary = '';
  String originalResumeText = '';
  String tailoredResumeText = '';
  final TailorController _tailorController = TailorController();
  final logger = Logger();

  /* TEXT CONTROLLERS */
  final TextEditingController jobPositionController = TextEditingController();
  final TextEditingController jobCompanyController = TextEditingController();
  final TextEditingController jobDescriptionController =
      TextEditingController();

  // --------------------------------------------------------------------------
  // LIFECYCLE: initState
  // --------------------------------------------------------------------------
  @override
  void initState() {
    super.initState();
    _loadResumeFiles();
  }

  // --------------------------------------------------------------------------
  // LIFECYCLE: dispose
  // --------------------------------------------------------------------------
  @override
  void dispose() {
    jobPositionController.dispose();
    jobCompanyController.dispose();
    jobDescriptionController.dispose();
    super.dispose();
  }

  // --------------------------------------------------------------------------
  // METHOD: Load Resume Files
  // --------------------------------------------------------------------------
  Future<void> _loadResumeFiles() async {
    try {
      final files = await _tailorController.loadResumeFiles();
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
  // METHOD: Tailor Resume
  // --------------------------------------------------------------------------
  Future<void> _tailorResume() async {
    // Guard: Prevent double-tap
    if (isTailoring) return;
    
    if (jobDescriptionController.text.trim().isEmpty) {
      NotificationDialog.show(
        context: context,
        title: 'Missing Job Description',
        message: 'Please enter a job description to tailor your resume.',
        isSuccess: false,
      );
      return;
    }

    if (resumeFiles.isEmpty) {
      NotificationDialog.show(
        context: context,
        title: 'No Resume Selected',
        message: 'Please select a resume to tailor.',
        isSuccess: false,
      );
      return;
    }

    try {
      setState(() {
        isTailoring = true;
        tailoredPdfFile = null;
        showOriginalPdf = false;
      });

      // Get the selected resume file
      final resumeFile = resumeFiles[selectedResumeIndex];
      final fileName = ResumeFileService.getFileName(resumeFile.path);
      print('📋 Starting tailor for: $fileName');

      // Extract text from resume
      final resumeText = await _tailorController.extractResumeText(resumeFile);

      setState(() {
        originalResumeText = resumeText;
      });

      if (resumeText.isEmpty) {
        throw Exception('Resume text is empty');
      }

      print('✓ Extracted ${resumeText.length} characters from resume');
      print('🚀 Calling tailor API with LLM analysis...');

      final tailorResult = await _tailorController.tailorResume(
        resumeText: resumeText,
        jobDescription: jobDescriptionController.text,
        intensity: tailorIntensity,
      );

      print(
        '✓ Received tailored resume with analysis: ${tailorResult.tailoredResume.length} characters',
      );

      setState(() {
        hasTailored = true;
        isTailoring = false;
        tailoredResumeText = tailorResult.tailoredResume;
        overallConfidence = tailorResult.overallConfidence;
        categoryScores = tailorResult.categoryScores;
        tailorMatches = tailorResult.matches;
        tailorGaps = tailorResult.gaps;
        changesSummary = tailorResult.changesSummary;
      });

      // Generate tailored PDF for preview
      try {
        final timestamp = DateTime.now().millisecondsSinceEpoch;
        final pdfFilename = 'tailored_$timestamp.pdf';

        final saveResult = await _tailorController.saveTailoredTextPdf(
          filename: pdfFilename,
          tailoredResumeText: tailoredResumeText,
        );

        if (saveResult['success'] && saveResult['path'] != null) {
          final pdfFile = File(saveResult['path']);
          if (await pdfFile.exists()) {
            setState(() {
              tailoredPdfFile = pdfFile;
              showOriginalPdf = false;
            });
          }
        }
      } catch (e) {
        logger.w('⚠️  Failed to generate tailored PDF preview: $e');
      }

      if (mounted) {
        NotificationDialog.show(
          context: context,
          title: 'Success',
          message: 'Your resume has been tailored successfully!',
          isSuccess: true,
        );
      }
    } catch (e) {
      print('✗ Error tailoring resume: $e');
      setState(() {
        isTailoring = false;
      });
      if (mounted) {
        NotificationDialog.show(
          context: context,
          title: 'Error',
          message: 'Error tailoring resume. Please try again.',
          isSuccess: false,
        );
      }
    }
  }

  // --------------------------------------------------------------------------
  // METHOD: Reset Analysis (Back to empty state)
  // --------------------------------------------------------------------------
  void _resetAnalysis() {
    setState(() {
      hasSeenFit = false;
      userChoseToTailor = false;
      hasTailored = false;
      tailoredPdfFile = null;
      showOriginalPdf = false;
      tailorMatches = [];
      categoryScores = [];
      tailorGaps = null;
      overallConfidence = 0;
      changesSummary = '';
      jobPositionController.clear();
      jobCompanyController.clear();
      jobDescriptionController.clear();
    });
  }

  // --------------------------------------------------------------------------
  // METHOD: Clear Input Fields (for tab switching - hybrid approach)
  // --------------------------------------------------------------------------
  @override
  void clearInputFields() {
    setState(() {
      // Clear input fields but preserve results
      jobPositionController.clear();
      jobCompanyController.clear();
      jobDescriptionController.clear();
      // Keep: hasTailored, tailoredPdfFile, tailorMatches, categoryScores, etc.
    });
  }

  // --------------------------------------------------------------------------
  // Keep widget alive when switching tabs
  // --------------------------------------------------------------------------
  @override
  bool get wantKeepAlive => true;

  // --------------------------------------------------------------------------
  // METHOD: Analyze Fit (Show confidence without tailoring)
  // --------------------------------------------------------------------------
  Future<void> _analyzeFit() async {
    if (jobDescriptionController.text.trim().isEmpty) {
      NotificationDialog.show(
        context: context,
        title: 'Missing Job Description',
        message: 'Please enter a job description to analyze.',
        isSuccess: false,
      );
      return;
    }

    if (resumeFiles.isEmpty) {
      NotificationDialog.show(
        context: context,
        title: 'No Resume Selected',
        message: 'Please select a resume to analyze.',
        isSuccess: false,
      );
      return;
    }

    try {
      setState(() {
        isTailoring = true;
      });

      // Get the selected resume file
      final resumeFile = resumeFiles[selectedResumeIndex];
      final fileName = ResumeFileService.getFileName(resumeFile.path);
      print('📋 Starting fit analysis for: $fileName');

      // Extract text from resume
      final resumeText = await _tailorController.extractResumeText(resumeFile);

      if (resumeText.isEmpty) {
        throw Exception('Resume text is empty');
      }

      print('✓ Extracted ${resumeText.length} characters from resume');
      print('🚀 Calling fit analysis API with LLM...');

      final analysisResult = await _tailorController.analyzeFit(
        resumeText: resumeText,
        jobDescription: jobDescriptionController.text,
      );

      print(
        '✓ Received fit analysis: ${analysisResult.overallConfidence}% confidence',
      );

      setState(() {
        hasSeenFit = true;
        isTailoring = false;
        userChoseToTailor = false;
        overallConfidence = analysisResult.overallConfidence;
        categoryScores = analysisResult.categoryScores;
        tailorMatches = analysisResult.matches;
        tailorGaps = analysisResult.gaps;
      });

      if (mounted) {
        NotificationDialog.show(
          context: context,
          title: 'Analysis Complete',
          message: 'See your job fit analysis above.',
          isSuccess: true,
        );
      }
    } catch (e) {
      print('✗ Error analyzing fit: $e');
      setState(() {
        isTailoring = false;
      });
      if (mounted) {
        NotificationDialog.show(
          context: context,
          title: 'Error',
          message: 'Error analyzing fit. Please try again.',
          isSuccess: false,
        );
      }
    }
  }

  // --------------------------------------------------------------------------
  // METHOD: Generate PDF from Tailored Resume
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
      final result = await _tailorController.saveSamplePdf(fileName);

      if (mounted) {
        setState(() {
          isGeneratingPdf = false;
        });

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('PDF generated: $result'),
            backgroundColor: AppColors.successGreen,
            duration: const Duration(seconds: 3),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          isGeneratingPdf = false;
        });

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error generating PDF: $e'),
            backgroundColor: AppColors.errorRed,
          ),
        );
      }
    }
  }

  // --------------------------------------------------------------------------
  // METHOD: Show PDF Filename Dialog
  // --------------------------------------------------------------------------
  Future<String?> _showPdfFilenameDialog() async {
    final TextEditingController controller = TextEditingController(
      text: 'tailored_resume_${DateTime.now().millisecondsSinceEpoch}',
    );

    return showDialog<String?>(
      context: context,
      builder: (BuildContext context) => AlertDialog(
        backgroundColor: AppColors.dark2,
        title: Text(
          'Export Tailored Resume as PDF',
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
  // METHOD: Get File Size Text
  // --------------------------------------------------------------------------
  String _getFileSizeText(File file) {
    try {
      final bytes = file.lengthSync();
      if (bytes < 1024) {
        return '${bytes}B';
      } else if (bytes < 1024 * 1024) {
        return '${(bytes / 1024).toStringAsFixed(1)}KB';
      } else {
        return '${(bytes / (1024 * 1024)).toStringAsFixed(1)}MB';
      }
    } catch (e) {
      return 'Unknown';
    }
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
        // LEFT PANEL: Inputs & Results (40%)
        // ====================================================================
        Expanded(
          flex: 40,
          child: Container(
            color: AppColors.darkSecondary,
            child: isLoading
                ? _buildLoadingState()
                : resumeFiles.isEmpty
                ? _buildNoResumesPanel()
                : _buildLeftPanelContent(),
          ),
        ),

        // ====================================================================
        // VERTICAL DIVIDER: Between Panels
        // ====================================================================
        Container(width: 1, color: AppColors.dark2),

        // ====================================================================
        // RIGHT PANEL: Resume Preview (60%)
        // ====================================================================
        Expanded(
          flex: 60,
          child: Container(
            color: AppColors.darkPrimary,
            child: resumeFiles.isEmpty
                ? _buildNoResumesPreviewPanel()
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
    return Center(child: CircularProgressIndicator(color: AppColors.gold));
  }

  // --------------------------------------------------------------------------
  // BUILD HELPER: No Resumes Panel (Left)
  // --------------------------------------------------------------------------
  Widget _buildNoResumesPanel() {
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
  // BUILD HELPER: Left Panel Content (UNIFIED SECTION)
  // --------------------------------------------------------------------------
  Widget _buildLeftPanelContent() {
    return Container(
      margin: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border.all(color: AppColors.gold.withOpacity(0.3), width: 1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ==============================================================
          // HEADER
          // ==============================================================
          Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Job Tailor',
                  style: AppTypography.labelText.copyWith(
                    color: AppColors.cream,
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Select a resume and enter a job description to see your fit',
                  style: AppTypography.bodySmall.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ),
          // ==============================================================
          // DIVIDER
          // ==============================================================
          Container(height: 1, color: AppColors.gold.withOpacity(0.3)),
          // ==============================================================
          // CONTENT: Scrollable form
          // ==============================================================
          Expanded(
            child: SingleChildScrollView(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // ======================================================
                    // 1. RESUME SELECTOR (Dropdown)
                    // ======================================================
                    _buildResumeDropdown(),
                    const SizedBox(height: 16),
                    // ======================================================
                    // 2. JOB DETAILS INPUTS
                    // ======================================================
                    _buildJobInputFields(),
                    const SizedBox(height: 20),
                    // ======================================================
                    // 3. MATCH BREAKDOWN (Empty until user analyzes)
                    // ======================================================
                    if (!hasSeenFit)
                      _buildAnalyzeButton()
                    else ...[
                      _buildConfidenceGauge(),
                      const SizedBox(height: 16),
                      _buildCategoryScores(),
                      const SizedBox(height: 20),
                      // ======================================================
                      // 4. DECISION BUTTONS (Submit or Tailor)
                      // ======================================================
                      if (!userChoseToTailor)
                        _buildDecisionButtons()
                      else ...[
                        // ======================================================
                        // 5. INTENSITY CONTROL (if tailoring)
                        // ======================================================
                        _buildIntensityControl(),
                        const SizedBox(height: 16),
                        // ======================================================
                        // TAILOR BUTTON
                        // ======================================================
                        SizedBox(
                          width: double.infinity,
                          child: ElevatedButton.icon(
                            onPressed: isTailoring ? null : _tailorResume,
                            icon: isTailoring
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
                                : const Icon(Icons.edit_outlined),
                            label: Text(
                              isTailoring
                                  ? 'Tailoring...'
                                  : 'Generate Tailored Resume',
                            ),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppColors.gold,
                              foregroundColor: AppColors.darkPrimary,
                              disabledBackgroundColor: AppColors.dark3,
                              disabledForegroundColor: AppColors.textSecondary,
                              padding: const EdgeInsets.symmetric(vertical: 12),
                            ),
                          ),
                        ),
                        const SizedBox(height: 16),
                        // ======================================================
                        // RESULTS SECTION (if tailored)
                        // ======================================================
                        if (hasTailored) ...[
                          Divider(height: 1, color: AppColors.dark2),
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
                                'Top Matches',
                                style: AppTypography.labelText.copyWith(
                                  color: AppColors.cream,
                                  fontSize: 13,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          ListView.builder(
                            shrinkWrap: true,
                            physics: const NeverScrollableScrollPhysics(),
                            itemCount: tailorMatches.length,
                            itemBuilder: (context, index) =>
                                _buildTailorMatchItem(index),
                          ),
                          _buildGapAnalysis(),
                          const SizedBox(height: 16),
                          SizedBox(
                            width: double.infinity,
                            child: ElevatedButton.icon(
                              onPressed: _resetAnalysis,
                              icon: const Icon(Icons.refresh_outlined),
                              label: const Text('Try Different Job'),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: AppColors.dark2,
                                foregroundColor: AppColors.cream,
                                padding: const EdgeInsets.symmetric(
                                  vertical: 10,
                                ),
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
                                        valueColor:
                                            AlwaysStoppedAnimation<Color>(
                                              AppColors.darkPrimary.withOpacity(
                                                0.7,
                                              ),
                                            ),
                                      ),
                                    )
                                  : const Icon(Icons.download),
                              label: Text(
                                isGeneratingPdf
                                    ? 'Generating...'
                                    : 'Download Tailored Resume',
                              ),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: AppColors.successGreen,
                                foregroundColor: AppColors.darkPrimary,
                                padding: const EdgeInsets.symmetric(
                                  vertical: 10,
                                ),
                                disabledBackgroundColor: AppColors.successGreen
                                    .withOpacity(0.5),
                                disabledForegroundColor: AppColors.darkPrimary
                                    .withOpacity(0.5),
                              ),
                            ),
                          ),
                        ],
                      ],
                    ],
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
  // BUILD HELPER: Job Input Fields
  // --------------------------------------------------------------------------
  Widget _buildJobInputFields() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Position Input
        TextField(
          controller: jobPositionController,
          style: AppTypography.bodySmall.copyWith(color: AppColors.cream),
          decoration: InputDecoration(
            labelText: 'Job Position (Optional)',
            labelStyle: AppTypography.bodySmall.copyWith(
              color: AppColors.textSecondary,
              fontSize: 12,
            ),
            hintText: 'e.g. Senior Product Manager',
            hintStyle: AppTypography.bodySmall.copyWith(
              color: AppColors.textSecondary,
              fontSize: 11,
            ),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(6),
              borderSide: BorderSide(color: AppColors.dark2),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(6),
              borderSide: BorderSide(color: AppColors.gold, width: 2),
            ),
            filled: true,
            fillColor: AppColors.dark3,
            contentPadding: const EdgeInsets.symmetric(
              horizontal: 12,
              vertical: 10,
            ),
          ),
        ),
        const SizedBox(height: 12),
        // Company Input
        TextField(
          controller: jobCompanyController,
          style: AppTypography.bodySmall.copyWith(color: AppColors.cream),
          decoration: InputDecoration(
            labelText: 'Company (Optional)',
            labelStyle: AppTypography.bodySmall.copyWith(
              color: AppColors.textSecondary,
              fontSize: 12,
            ),
            hintText: 'e.g. TechCorp Inc',
            hintStyle: AppTypography.bodySmall.copyWith(
              color: AppColors.textSecondary,
              fontSize: 11,
            ),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(6),
              borderSide: BorderSide(color: AppColors.dark2),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(6),
              borderSide: BorderSide(color: AppColors.gold, width: 2),
            ),
            filled: true,
            fillColor: AppColors.dark3,
            contentPadding: const EdgeInsets.symmetric(
              horizontal: 12,
              vertical: 10,
            ),
          ),
        ),
        const SizedBox(height: 12),
        // Job Description Label
        Text(
          'Job Description *',
          style: AppTypography.bodySmall.copyWith(
            color: AppColors.cream,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 8),
        // Job Description Input
        Container(
          constraints: BoxConstraints(minHeight: 120, maxHeight: 150),
          child: TextField(
            controller: jobDescriptionController,
            maxLines: null,
            expands: true,
            textAlignVertical: TextAlignVertical.top,
            style: AppTypography.bodySmall.copyWith(
              color: AppColors.cream,
              height: 1.4,
            ),
            decoration: InputDecoration(
              hintText: 'Paste job description or posting here...',
              hintStyle: AppTypography.bodySmall.copyWith(
                color: AppColors.textSecondary,
                fontSize: 11,
              ),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(6),
                borderSide: BorderSide(color: AppColors.dark2),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(6),
                borderSide: BorderSide(color: AppColors.gold, width: 2),
              ),
              filled: true,
              fillColor: AppColors.dark3,
              contentPadding: const EdgeInsets.all(12),
            ),
          ),
        ),
      ],
    );
  }

  // --------------------------------------------------------------------------
  // BUILD HELPER: Resume Dropdown Selector
  // --------------------------------------------------------------------------
  Widget _buildResumeDropdown() {
    return Column(
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
              _resetAnalysis();
            });
          },
        ),
      ],
    );
  }

  // --------------------------------------------------------------------------
  // BUILD HELPER: Analyze Button (Before seeing fit)
  // --------------------------------------------------------------------------
  Widget _buildAnalyzeButton() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: AppColors.dark3,
            border: Border.all(color: AppColors.dark2),
            borderRadius: BorderRadius.circular(6),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(Icons.info_outline, color: AppColors.gold, size: 18),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Fill in the job details and analyze to see your fit',
                      style: AppTypography.bodySmall.copyWith(
                        color: AppColors.textSecondary,
                        fontSize: 11,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        SizedBox(
          width: double.infinity,
          child: ElevatedButton.icon(
            onPressed: isTailoring ? null : _analyzeFit,
            icon: isTailoring
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
                : const Icon(Icons.analytics_outlined),
            label: Text(isTailoring ? 'Analyzing...' : 'See How I Fit'),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.gold,
              foregroundColor: AppColors.darkPrimary,
              disabledBackgroundColor: AppColors.dark3,
              disabledForegroundColor: AppColors.textSecondary,
              padding: const EdgeInsets.symmetric(vertical: 12),
            ),
          ),
        ),
      ],
    );
  }

  // --------------------------------------------------------------------------
  // BUILD HELPER: Decision Buttons (After seeing fit)
  // --------------------------------------------------------------------------
  Widget _buildDecisionButtons() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'What would you like to do?',
          style: AppTypography.bodySmall.copyWith(
            color: AppColors.textSecondary,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 12),
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
              isGeneratingPdf ? 'Generating...' : 'Submit This Resume',
            ),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.successGreen,
              foregroundColor: AppColors.darkPrimary,
              padding: const EdgeInsets.symmetric(vertical: 12),
              disabledBackgroundColor: AppColors.successGreen.withOpacity(0.5),
              disabledForegroundColor: AppColors.darkPrimary.withOpacity(0.5),
            ),
          ),
        ),
        const SizedBox(height: 8),
        SizedBox(
          width: double.infinity,
          child: ElevatedButton.icon(
            onPressed: () {
              setState(() {
                userChoseToTailor = true;
                tailorIntensity = 'medium';
              });
            },
            icon: const Icon(Icons.tune),
            label: const Text('Tailor Resume'),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.dark2,
              foregroundColor: AppColors.cream,
              padding: const EdgeInsets.symmetric(vertical: 12),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildConfidenceGauge() {
    return Center(
      child: Column(
        children: [
          Stack(
            alignment: Alignment.center,
            children: [
              // Background circle
              SizedBox(
                width: 120,
                height: 120,
                child: CircularProgressIndicator(
                  value: overallConfidence / 100,
                  strokeWidth: 8,
                  backgroundColor: AppColors.dark3,
                  valueColor: AlwaysStoppedAnimation<Color>(
                    overallConfidence >= 85
                        ? AppColors.successGreen
                        : overallConfidence >= 70
                        ? AppColors.gold
                        : AppColors.warningOrange,
                  ),
                ),
              ),
              // Center text
              Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    '$overallConfidence%',
                    style: AppTypography.scoreDisplay.copyWith(
                      color: AppColors.gold,
                      fontSize: 28,
                    ),
                  ),
                  Text(
                    'Match',
                    style: AppTypography.bodySmall.copyWith(
                      color: AppColors.textSecondary,
                      fontSize: 10,
                    ),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            overallConfidence >= 85
                ? 'Excellent fit!'
                : overallConfidence >= 70
                ? 'Good match'
                : 'Needs work',
            style: AppTypography.bodySmall.copyWith(
              color: overallConfidence >= 85
                  ? AppColors.successGreen
                  : overallConfidence >= 70
                  ? AppColors.gold
                  : AppColors.warningOrange,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  // --------------------------------------------------------------------------
  // BUILD HELPER: Category Scores Breakdown
  // --------------------------------------------------------------------------
  Widget _buildCategoryScores() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Match Breakdown',
          style: AppTypography.labelText.copyWith(
            color: AppColors.cream,
            fontSize: 12,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 12),
        ...categoryScores.map((score) => _buildCategoryScoreItem(score)),
      ],
    );
  }

  // --------------------------------------------------------------------------
  // BUILD HELPER: Single Category Score Item
  // --------------------------------------------------------------------------
  Widget _buildCategoryScoreItem(CategoryScore score) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                score.category,
                style: AppTypography.bodySmall.copyWith(
                  color: AppColors.cream,
                  fontWeight: FontWeight.w500,
                ),
              ),
              Text(
                '${score.score}%',
                style: AppTypography.bodySmall.copyWith(
                  color: AppColors.gold,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: score.score / 100,
              minHeight: 6,
              backgroundColor: AppColors.dark3,
              valueColor: AlwaysStoppedAnimation<Color>(
                score.score >= 85
                    ? AppColors.successGreen
                    : score.score >= 70
                    ? AppColors.gold
                    : AppColors.warningOrange,
              ),
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
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Tailor Intensity',
          style: AppTypography.labelText.copyWith(
            color: AppColors.cream,
            fontSize: 12,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(child: _buildIntensityButton('light', 'Light')),
            const SizedBox(width: 8),
            Expanded(child: _buildIntensityButton('medium', 'Medium')),
            const SizedBox(width: 8),
            Expanded(child: _buildIntensityButton('heavy', 'Heavy')),
          ],
        ),
      ],
    );
  }

  // --------------------------------------------------------------------------
  // BUILD HELPER: Single Intensity Button
  // --------------------------------------------------------------------------
  Widget _buildIntensityButton(String intensity, String label) {
    final isSelected = tailorIntensity == intensity;
    return GestureDetector(
      onTap: () {
        setState(() {
          tailorIntensity = intensity;
        });
      },
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.dark3 : AppColors.dark2,
          border: Border.all(
            color: isSelected ? AppColors.gold : AppColors.dark3,
            width: isSelected ? 2 : 1,
          ),
          borderRadius: BorderRadius.circular(6),
        ),
        child: Text(
          label,
          textAlign: TextAlign.center,
          style: AppTypography.bodySmall.copyWith(
            color: isSelected ? AppColors.gold : AppColors.textSecondary,
            fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
            fontSize: 11,
          ),
        ),
      ),
    );
  }

  // --------------------------------------------------------------------------
  // BUILD HELPER: Gap Analysis Section
  // --------------------------------------------------------------------------
  Widget _buildGapAnalysis() {
    if (tailorGaps == null) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 16),
        Divider(height: 1, color: AppColors.gold.withOpacity(0.3)),
        const SizedBox(height: 16),
        Row(
          children: [
            Icon(
              Icons.lightbulb_outline,
              color: AppColors.warningOrange,
              size: 20,
            ),
            const SizedBox(width: 8),
            Text(
              'Opportunities to Improve',
              style: AppTypography.labelText.copyWith(
                color: AppColors.cream,
                fontSize: 13,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        // Missing Skills
        if (tailorGaps!.missingSkills.isNotEmpty)
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Missing Skills',
                style: AppTypography.bodySmall.copyWith(
                  color: AppColors.textSecondary,
                  fontWeight: FontWeight.w500,
                  fontSize: 11,
                ),
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: tailorGaps!.missingSkills.map((skill) {
                  return Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: AppColors.warningOrange.withOpacity(0.1),
                      border: Border.all(
                        color: AppColors.warningOrange.withOpacity(0.3),
                      ),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      skill,
                      style: AppTypography.bodySmall.copyWith(
                        color: AppColors.warningOrange,
                        fontSize: 10,
                      ),
                    ),
                  );
                }).toList(),
              ),
              const SizedBox(height: 12),
            ],
          ),
        // Suggestions
        if (tailorGaps!.suggestions.isNotEmpty)
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Suggestions',
                style: AppTypography.bodySmall.copyWith(
                  color: AppColors.textSecondary,
                  fontWeight: FontWeight.w500,
                  fontSize: 11,
                ),
              ),
              const SizedBox(height: 8),
              ...tailorGaps!.suggestions.map((suggestion) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '•',
                        style: AppTypography.bodySmall.copyWith(
                          color: AppColors.gold,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          suggestion,
                          style: AppTypography.bodySmall.copyWith(
                            color: AppColors.textSecondary,
                            fontSize: 10,
                            height: 1.4,
                          ),
                        ),
                      ),
                    ],
                  ),
                );
              }).toList(),
            ],
          ),
      ],
    );
  }

  // --------------------------------------------------------------------------
  // BUILD HELPER: Tailor Results
  // --------------------------------------------------------------------------
  Widget _buildTailorResults() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 24),
        Divider(height: 1, color: AppColors.dark2),
        const SizedBox(height: 20),
        // ======================================================
        // CONFIDENCE GAUGE
        // ======================================================
        _buildConfidenceGauge(),
        const SizedBox(height: 24),
        // ======================================================
        // CATEGORY SCORES
        // ======================================================
        _buildCategoryScores(),
        const SizedBox(height: 24),
        // ======================================================
        // INTENSITY CONTROL
        // ======================================================
        _buildIntensityControl(),
        const SizedBox(height: 24),
        // ======================================================
        // MATCHED KEYWORDS
        // ======================================================
        Row(
          children: [
            Icon(Icons.check_circle, color: AppColors.successGreen, size: 20),
            const SizedBox(width: 8),
            Text(
              'Top Matches',
              style: AppTypography.labelText.copyWith(
                color: AppColors.cream,
                fontSize: 13,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        ListView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: tailorMatches.length,
          itemBuilder: (context, index) => _buildTailorMatchItem(index),
        ),
        // ======================================================
        // GAP ANALYSIS
        // ======================================================
        _buildGapAnalysis(),
        const SizedBox(height: 24),
        // ======================================================
        // BEFORE/AFTER TOGGLE
        // ======================================================
        // ======================================================
        // BUTTONS
        // ======================================================
        SizedBox(
          width: double.infinity,
          child: ElevatedButton.icon(
            onPressed: _resetAnalysis,
            icon: const Icon(Icons.refresh_outlined),
            label: const Text('Try Again'),
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
            label: Text(isGeneratingPdf ? 'Generating...' : 'Export as PDF'),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.successGreen,
              foregroundColor: AppColors.darkPrimary,
              padding: const EdgeInsets.symmetric(vertical: 10),
              disabledBackgroundColor: AppColors.successGreen.withOpacity(0.5),
              disabledForegroundColor: AppColors.darkPrimary.withOpacity(0.5),
            ),
          ),
        ),
      ],
    );
  }

  // --------------------------------------------------------------------------
  // BUILD HELPER: Single Tailor Match Item
  // --------------------------------------------------------------------------
  Widget _buildTailorMatchItem(int index) {
    final match = tailorMatches[index];
    final isHighRelevance =
        int.parse(match.relevance.replaceAll('%', '')) >= 90;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.dark3,
        border: Border.all(
          color: isHighRelevance
              ? AppColors.gold.withOpacity(0.3)
              : AppColors.dark2,
        ),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      match.keyword,
                      style: AppTypography.labelText.copyWith(
                        color: AppColors.cream,
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      match.source,
                      style: AppTypography.bodySmall.copyWith(
                        color: AppColors.textSecondary,
                        fontSize: 9,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: isHighRelevance
                      ? AppColors.successGreen.withOpacity(0.2)
                      : AppColors.dark2,
                  border: Border.all(
                    color: isHighRelevance
                        ? AppColors.successGreen
                        : Colors.transparent,
                  ),
                  borderRadius: BorderRadius.circular(3),
                ),
                child: Text(
                  match.relevance,
                  style: AppTypography.bodySmall.copyWith(
                    color: isHighRelevance
                        ? AppColors.successGreen
                        : AppColors.textSecondary,
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // --------------------------------------------------------------------------
  // BUILD HELPER: No Resumes Preview Panel (Right)
  // --------------------------------------------------------------------------
  Widget _buildNoResumesPreviewPanel() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.file_copy_outlined,
            size: 64,
            color: AppColors.textSecondary,
          ),
          const SizedBox(height: 16),
          Text(
            'No resumes available',
            style: AppTypography.bodyLarge.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
        ],
      ),
    );
  }

  // --------------------------------------------------------------------------
  // BUILD HELPER: Resume Preview Panel (Right)
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
                        ResumeFileService.getFileName(
                          resumeFiles[selectedResumeIndex].path,
                        ),
                        style: AppTypography.bodySmall.copyWith(
                          color: AppColors.textSecondary,
                        ),
                      ),
                    ],
                  ),
                ),
                if (hasTailored) ...[
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
                          onTap: () => setState(() => showOriginalPdf = false),
                          child: Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 12,
                              vertical: 6,
                            ),
                            decoration: BoxDecoration(
                              color: !showOriginalPdf
                                  ? AppColors.dark3
                                  : Colors.transparent,
                              borderRadius: BorderRadius.circular(18),
                            ),
                            child: Text(
                              'Tailored',
                              style: AppTypography.bodySmall.copyWith(
                                color: !showOriginalPdf
                                    ? AppColors.gold
                                    : AppColors.textSecondary,
                                fontSize: 10,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ),
                        GestureDetector(
                          onTap: () => setState(() => showOriginalPdf = true),
                          child: Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 12,
                              vertical: 6,
                            ),
                            decoration: BoxDecoration(
                              color: showOriginalPdf
                                  ? AppColors.dark3
                                  : Colors.transparent,
                              borderRadius: BorderRadius.circular(18),
                            ),
                            child: Text(
                              'Original',
                              style: AppTypography.bodySmall.copyWith(
                                color: showOriginalPdf
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
                const SizedBox(width: 8),
                _buildDownloadButton(),
              ],
            ),
          ),

          // ====================================================================
          // CONTENT: PDF Viewer with Overlay
          // ====================================================================
          Expanded(
            child: Container(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: AppColors.dark3),
              ),
              margin: const EdgeInsets.all(12),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: Stack(
                  children: [
                    SfPdfViewer.file(
                      hasTailored && !showOriginalPdf
                          ? (tailoredPdfFile ??
                                resumeFiles[selectedResumeIndex])
                          : resumeFiles[selectedResumeIndex],
                      pageLayoutMode: PdfPageLayoutMode.continuous,
                    ),
                    if (isTailoring) _buildTailoringOverlay(),
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
      color: hasTailored ? AppColors.gold : AppColors.textTertiary,
      tooltip: hasTailored
          ? 'Download tailored resume'
          : 'Tailor resume to download',
      onPressed: hasTailored ? () => _downloadTailoredResume() : null,
    );
  }

  // --------------------------------------------------------------------------
  // METHOD: Download Tailored Resume
  // --------------------------------------------------------------------------
  Future<void> _downloadTailoredResume() async {
    if (tailoredResumeText.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('No tailored resume to download'),
          backgroundColor: AppColors.errorRed,
        ),
      );
      return;
    }

    if (selectedResumeIndex >= resumeFiles.length) return;

    final sourceFile = resumeFiles[selectedResumeIndex];
    final originalFileName = ResumeFileService.getFileName(sourceFile.path);

    if (mounted) {
      showDialog(
        context: context,
        builder: (context) => DownloadDialog(
          originalFileName: originalFileName,
          onDownload: (fileName, replaceOriginal) async {
            await _performDownloadTailored(fileName, replaceOriginal);
          },
        ),
      );
    }
  }

  // --------------------------------------------------------------------------
  // METHOD: Perform Tailored Download
  // --------------------------------------------------------------------------
  Future<void> _performDownloadTailored(
    String fileName,
    bool replaceOriginal,
  ) async {
    try {
      setState(() {
        isGeneratingPdf = true;
      });

      // Ensure filename ends with .pdf
      final pdfFilename = fileName.endsWith('.pdf')
          ? fileName
          : '$fileName.pdf';

      print('💾 Saving tailored resume as: $pdfFilename');

      // Call API to save as text PDF
      final result = await _tailorController.saveTailoredTextPdf(
        filename: pdfFilename,
        tailoredResumeText: tailoredResumeText,
      );

      if (mounted) {
        setState(() {
          isGeneratingPdf = false;
        });

        if (result['success'] == true) {
          final message = replaceOriginal
              ? '✓ Resume replaced: $pdfFilename'
              : '✓ Tailored resume saved: $pdfFilename';

          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(message),
              backgroundColor: AppColors.successGreen,
              duration: const Duration(seconds: 3),
            ),
          );
        } else {
          throw Exception(result['error'] ?? 'Failed to save tailored resume');
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          isGeneratingPdf = false;
        });

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('✗ Error: ${e.toString()}'),
            backgroundColor: AppColors.errorRed,
          ),
        );
      }
    }
  }

  // --------------------------------------------------------------------------
  // BUILD HELPER: Tailoring Overlay
  // --------------------------------------------------------------------------
  Widget _buildTailoringOverlay() {
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
              'Tailoring resume...',
              style: AppTypography.bodySmall.copyWith(color: AppColors.cream),
            ),
          ],
        ),
      ),
    );
  }
}
