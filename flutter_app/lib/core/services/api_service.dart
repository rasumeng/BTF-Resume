/// Service for communicating with Flask backend
import 'dart:io';
import 'package:dio/dio.dart';
import 'package:logger/logger.dart';
import '../../config/app_constants.dart';
import '../models/resume_model.dart';

/// Retry interceptor for handling transient network failures
class RetryInterceptor extends Interceptor {
  final Dio dio;
  static const int maxRetry = 3;

  RetryInterceptor(this.dio);

  @override
  Future<void> onError(DioException err, ErrorInterceptorHandler handler) async {
    if (_shouldRetry(err) && err.requestOptions.extra['retryCount'] != null && err.requestOptions.extra['retryCount'] < maxRetry) {
      final retryCount = ((err.requestOptions.extra['retryCount'] ?? 0) as int) + 1;
      err.requestOptions.extra['retryCount'] = retryCount;

      // Exponential backoff: 100ms, 200ms, 400ms
      await Future.delayed(Duration(milliseconds: (100 * retryCount).toInt()));

      try {
        final response = await dio.request<dynamic>(
          err.requestOptions.path,
          data: err.requestOptions.data,
          queryParameters: err.requestOptions.queryParameters,
          options: Options(
            method: err.requestOptions.method,
            headers: err.requestOptions.headers,
            contentType: err.requestOptions.contentType,
          ),
        );
        return handler.resolve(response);
      } catch (e) {
        return handler.next(err);
      }
    }
    return handler.next(err);
  }

  bool _shouldRetry(DioException error) {
    // Retry on connection errors, timeouts, but NOT on 404s
    return error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout ||
        error.type == DioExceptionType.unknown ||
        (error.response?.statusCode ?? 0) >= 500; // Retry on 5xx errors
  }
}

class ApiService {
  static final ApiService _instance = ApiService._internal();
  late Dio _dio;
  final logger = Logger();

  /// Cache for parsed resumes to avoid re-parsing
  /// Maps resume filename to parsed JSON data
  Map<String, Map<String, dynamic>> _parsedResumeCache = {};

  factory ApiService() {
    return _instance;
  }

  ApiService._internal() {
    _initializeDio();
  }

  void _initializeDio() {
    _dio = Dio(
      BaseOptions(
        baseUrl: AppConstants.flaskApiBase,
        connectTimeout: Duration(
          milliseconds: AppConstants.connectionTimeout,
        ),
        receiveTimeout: Duration(
          milliseconds: AppConstants.receiveTimeout,
        ),
        contentType: 'application/json',
        validateStatus: (status) {
          // Accept 2xx and 4xx responses without throwing
          // 5xx will still throw (server errors)
          return status != null && status < 500;
        },
      ),
    );

    // Add logging interceptor
    _dio.interceptors.add(
      LogInterceptor(
        requestBody: true,
        responseBody: true,
        logPrint: (obj) => logger.i(obj),
      ),
    );

    // Add retry interceptor for network failures
    _dio.interceptors.add(RetryInterceptor(_dio));
  }

  /// Check if backend is healthy and running
  Future<bool> checkHealth() async {
    try {
      final response = await _dio.get('/health');
      final data = response.data as Map<String, dynamic>;
      logger.i('✓ Backend health check passed');
      return data['status'] == 'healthy';
    } catch (e) {
      logger.w('✗ Backend health check failed: $e');
      return false;
    }
  }

  /// List all resumes
  Future<List<ResumeFile>> listResumes() async {
    try {
      final response = await _dio.get('/list-resumes');
      final data = response.data as Map<String, dynamic>;

      if (data['success'] != true) {
        throw Exception(data['error'] ?? 'Failed to list resumes');
      }

      final resumes = (data['resumes'] as List)
          .map((r) => ResumeFile.fromJson(r as Map<String, dynamic>))
          .toList();

      logger.i('✓ Listed ${resumes.length} resumes');
      return resumes;
    } catch (e) {
      logger.e('✗ Error listing resumes: $e');
      rethrow;
    }
  }

  /// Get resume content
  Future<ResumeContent> getResume(String filename) async {
    try {
      final response = await _dio.get(
        '/get-resume',
        queryParameters: {'filename': filename},
      );
      final data = response.data as Map<String, dynamic>;

      if (data['success'] != true) {
        throw Exception(data['error'] ?? 'Failed to get resume');
      }

      logger.i('✓ Loaded resume: $filename');
      return ResumeContent(
        filename: filename,
        content: data['content'] as String,
      );
    } catch (e) {
      logger.e('✗ Error getting resume: $e');
      rethrow;
    }
  }

  /// Update resume content
  Future<void> updateResume(String filename, String content) async {
    try {
      final response = await _dio.post(
        '/update-resume',
        data: {
          'filename': filename,
          'content': content,
        },
      );
      final data = response.data as Map<String, dynamic>;

      if (data['success'] != true) {
        throw Exception(data['error'] ?? 'Failed to update resume');
      }

      logger.i('✓ Updated resume: $filename');
    } catch (e) {
      logger.e('✗ Error updating resume: $e');
      rethrow;
    }
  }

  /// Delete resume
  Future<void> deleteResume(String filename) async {
    try {
      final response = await _dio.delete(
        '/delete-resume',
        queryParameters: {'filename': filename},
      );
      final data = response.data as Map<String, dynamic>;

      if (data['success'] != true) {
        throw Exception(data['error'] ?? 'Failed to delete resume');
      }

      logger.i('✓ Deleted resume: $filename');
    } catch (e) {
      logger.e('✗ Error deleting resume: $e');
      rethrow;
    }
  }

  /// Polish resume bullets
  Future<List<String>> polishBullets(
    List<String> bullets, {
    String intensity = 'medium',
  }) async {
    try {
      // Ensure backend is ready before attempting to polish
      final isHealthy = await _waitForBackend(maxAttempts: 3);
      if (!isHealthy) {
        throw Exception(
          'Backend is not responding. Please ensure the Flask backend is running on localhost:5000'
        );
      }

      final response = await _dio.post(
        '/polish-bullets',
        data: {
          'bullets': bullets,
          'intensity': intensity,
        },
      );

      // Check for HTTP errors
      if (response.statusCode! >= 400) {
        logger.e('✗ HTTP ${response.statusCode}: ${response.statusMessage}');
        final errorMsg = (response.data as Map<String, dynamic>?)?['error'];
        throw Exception(errorMsg ?? 'Failed to polish bullets (HTTP ${response.statusCode})');
      }

      final data = response.data as Map<String, dynamic>;

      if (data['success'] != true) {
        throw Exception(data['error'] ?? 'Failed to polish bullets');
      }

      final polished = (data['bullets'] as List).cast<String>();
      logger.i('✓ Polished ${polished.length} bullets');
      return polished;
    } catch (e) {
      logger.e('✗ Error polishing bullets: $e');
      rethrow;
    }
  }

  /// Extract text from a PDF file
  Future<String> extractPdfText(File pdfFile) async {
    try {
      if (!pdfFile.existsSync()) {
        throw Exception('PDF file not found: ${pdfFile.path}');
      }

      final fileName = pdfFile.path.split(Platform.pathSeparator).last;
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(
          pdfFile.path,
          filename: fileName,
        ),
      });

      final response = await _dio.post(
        '/extract-pdf-text',
        data: formData,
      );

      // Check for HTTP errors
      if (response.statusCode == 404) {
        logger.e('✗ /extract-pdf-text endpoint not found (404)');
        throw Exception('Extract PDF text endpoint not found. Ensure backend is properly configured.');
      }

      if (response.statusCode! >= 400) {
        logger.e('✗ HTTP ${response.statusCode}: ${response.statusMessage}');
        final errorMsg = (response.data as Map<String, dynamic>?)?['error'];
        throw Exception(errorMsg ?? 'Failed to extract PDF text (HTTP ${response.statusCode})');
      }

      final data = response.data as Map<String, dynamic>;

      if (data['success'] != true) {
        throw Exception(data['error'] ?? 'Failed to extract PDF text');
      }

      final extractedText = data['text'] as String;
      logger.i('✓ Extracted text from PDF: $fileName (${extractedText.length} chars)');
      return extractedText;
    } catch (e) {
      logger.e('✗ Error extracting PDF text: $e');
      rethrow;
    }
  }

  /// Parse resume and cache the structured data for reuse
  /// This should be called after extracting PDF text
  Future<Map<String, dynamic>> parseAndCacheResume(
    String resumeText, {
    String? filename,
  }) async {
    try {
      logger.i('📄 Parsing and caching resume structure...');

      final response = await _dio.post(
        '/parse-resume',
        data: {
          'resume_text': resumeText,
          'filename': filename,
        },
      );

      if (response.statusCode == 404) {
        throw Exception('Parse endpoint not found');
      }

      if (response.statusCode! >= 400) {
        final errorMsg = (response.data as Map<String, dynamic>?)?['error'];
        throw Exception(errorMsg ?? 'Failed to parse resume');
      }

      final data = response.data as Map<String, dynamic>;

      if (data['success'] != true) {
        throw Exception(data['error'] ?? 'Failed to parse resume');
      }

      final parsedResume = data['parsed_resume'] as Map<String, dynamic>;
      
      // Cache locally for fast access
      if (filename != null) {
        _parsedResumeCache[filename] = parsedResume;
        logger.i('✅ Parsed and cached resume: $filename');
      }

      return parsedResume;
    } catch (e) {
      logger.e('✗ Error parsing and caching resume: $e');
      rethrow;
    }
  }

  /// Get cached parsed resume data
  Map<String, dynamic>? getCachedResume(String filename) {
    final cached = _parsedResumeCache[filename];
    if (cached != null) {
      logger.i('📦 Using cached resume data for: $filename');
    }
    return cached;
  }

  /// Clear resume cache
  void clearResumeCache(String? filename) {
    if (filename != null) {
      _parsedResumeCache.remove(filename);
      logger.i('🗑️  Cleared cache for: $filename');
    } else {
      _parsedResumeCache.clear();
      logger.i('🗑️  Cleared all resume cache');
    }
  }

  /// Polish entire resume
  Future<String> polishResume(
    String resumeText, {
    String intensity = 'medium',
  }) async {
    try {
      // Ensure backend is ready before attempting to polish
      final isHealthy = await _waitForBackend(maxAttempts: 3);
      if (!isHealthy) {
        throw Exception(
          'Backend is not responding. Please ensure the Flask backend is running on localhost:5000'
        );
      }

      final response = await _dio.post(
        '/polish-resume',
        data: {
          'resume_text': resumeText,
          'intensity': intensity,
        },
      );

      // Check for HTTP errors
      if (response.statusCode == 404) {
        logger.e('✗ /polish-resume endpoint not found (404)');
        logger.e('Available backend URL: ${AppConstants.flaskApiBase}');
        throw Exception(
          'Polish resume endpoint not found. Ensure backend is properly configured.'
        );
      }

      if (response.statusCode! >= 400) {
        logger.e('✗ HTTP ${response.statusCode}: ${response.statusMessage}');
        final errorMsg = (response.data as Map<String, dynamic>?)?['error'];
        throw Exception(errorMsg ?? 'Failed to polish resume (HTTP ${response.statusCode})');
      }

      final data = response.data as Map<String, dynamic>;

      if (data['success'] != true) {
        throw Exception(data['error'] ?? 'Failed to polish resume');
      }

      logger.i('✓ Polished resume');
      return data['polished_resume'] as String;
    } catch (e) {
      logger.e('✗ Error polishing resume: $e');
      rethrow;
    }
  }

  /// Get specific changes made during resume polishing
  Future<List<String>> getPolishChanges(
    String originalResume,
    String polishedResume,
  ) async {
    try {
      final response = await _dio.post(
        '/get-polish-changes',
        data: {
          'original_resume': originalResume,
          'polished_resume': polishedResume,
        },
      );

      if (response.statusCode! >= 400) {
        logger.w('⚠️  Failed to get polish changes: HTTP ${response.statusCode}');
        // Return generic fallback
        return [
          'Resume content optimized for clarity',
          'Action verbs strengthened throughout',
          'Content formatted for better impact',
        ];
      }

      final data = response.data as Map<String, dynamic>;

      if (data['success'] != true) {
        logger.w('⚠️  Backend returned success=false for polish changes');
        return [
          'Resume content optimized for clarity',
          'Action verbs strengthened throughout',
        ];
      }

      final changes = (data['changes'] as List?)?.cast<String>() ?? [];
      logger.i('✓ Retrieved ${changes.length} polish changes');
      return changes.isNotEmpty
          ? changes
          : [
              'Resume content optimized',
              'Formatting improved for ATS compatibility',
            ];
    } catch (e) {
      logger.w('⚠️  Error getting polish changes: $e');
      // Return graceful fallback - don't break UX
      return [
        'Resume enhanced with AI improvements',
        'Content optimized for clarity',
      ];
    }
  }

  /// Wait for backend to be healthy with retries
  Future<bool> _waitForBackend({int maxAttempts = 5}) async {
    for (int i = 0; i < maxAttempts; i++) {
      try {
        final response = await _dio.get(
          '/health',
          options: Options(
            validateStatus: (status) => status == 200,
            sendTimeout: const Duration(milliseconds: 5000),
            receiveTimeout: const Duration(milliseconds: 5000),
          ),
        );

        if (response.statusCode == 200) {
          logger.i('✓ Backend is ready after $i attempts');
          return true;
        }
      } catch (e) {
        logger.w('⚠️  Backend health check attempt ${i + 1}/$maxAttempts failed');
        if (i < maxAttempts - 1) {
          await Future.delayed(Duration(milliseconds: 500 * (i + 1)));
        }
      }
    }

    logger.e('✗ Backend failed to respond after $maxAttempts attempts');
    return false;
  }

  /// Tailor resume to job description with comprehensive analysis
  Future<Map<String, dynamic>> tailorResume(
    String resumeText,
    String jobDescription, {
    String intensity = 'medium',
  }) async {
    try {
      // Ensure backend is ready before attempting to tailor
      final isHealthy = await _waitForBackend(maxAttempts: 3);
      if (!isHealthy) {
        throw Exception(
          'Backend is not responding. Please ensure the Flask backend is running on localhost:5000'
        );
      }

      final response = await _dio.post(
        '/tailor-resume',
        data: {
          'resume_text': resumeText,
          'job_description': jobDescription,
          'intensity': intensity,
        },
      );

      // Check for HTTP errors
      if (response.statusCode! >= 400) {
        logger.e('✗ HTTP ${response.statusCode}: ${response.statusMessage}');
        final errorMsg = (response.data as Map<String, dynamic>?)?['error'];
        throw Exception(errorMsg ?? 'Failed to tailor resume (HTTP ${response.statusCode})');
      }

      final data = response.data as Map<String, dynamic>;

      if (data['success'] != true) {
        throw Exception(data['error'] ?? 'Failed to tailor resume');
      }

      logger.i('✓ Tailored resume with analysis');
      // Return full response including analysis data
      return {
        'tailored_resume': data['tailored_resume'] as String? ?? '',
        'overall_confidence': data['overall_confidence'] as int? ?? 0,
        'category_scores': (data['category_scores'] as List?)?.map((e) => e as Map<String, dynamic>).toList() ?? [],
        'matches': (data['matches'] as List?)?.map((e) => e as Map<String, dynamic>).toList() ?? [],
        'gaps': data['gaps'] as Map<String, dynamic>? ?? {'missing_skills': [], 'missing_keywords': [], 'suggestions': []},
        'changes_summary': data['changes_summary'] as String? ?? '',
      };
    } catch (e) {
      logger.e('✗ Error tailoring resume: $e');
      rethrow;
    }
  }

  /// Analyze how well resume fits a job description (without tailoring)
  Future<Map<String, dynamic>> analyzeFit(
    String resumeText,
    String jobDescription,
  ) async {
    try {
      // Ensure backend is ready before attempting to analyze
      final isHealthy = await _waitForBackend(maxAttempts: 3);
      if (!isHealthy) {
        throw Exception(
          'Backend is not responding. Please ensure the Flask backend is running on localhost:5000'
        );
      }

      final response = await _dio.post(
        '/analyze-fit',
        data: {
          'resume_text': resumeText,
          'job_description': jobDescription,
        },
      );

      // Check for HTTP errors
      if (response.statusCode! >= 400) {
        logger.e('✗ HTTP ${response.statusCode}: ${response.statusMessage}');
        final errorMsg = (response.data as Map<String, dynamic>?)?['error'];
        throw Exception(errorMsg ?? 'Failed to analyze fit (HTTP ${response.statusCode})');
      }

      final data = response.data as Map<String, dynamic>;

      if (data['success'] != true) {
        throw Exception(data['error'] ?? 'Failed to analyze fit');
      }

      logger.i('✓ Analyzed fit');
      // Return analysis data without tailored_resume
      return {
        'overall_confidence': data['overall_confidence'] as int? ?? 0,
        'category_scores': (data['category_scores'] as List?)?.map((e) => e as Map<String, dynamic>).toList() ?? [],
        'matches': (data['matches'] as List?)?.map((e) => e as Map<String, dynamic>).toList() ?? [],
        'gaps': data['gaps'] as Map<String, dynamic>? ?? {'missing_skills': [], 'missing_keywords': [], 'suggestions': []},
      };
    } catch (e) {
      logger.e('✗ Error analyzing fit: $e');
      rethrow;
    }
  }

  /// Grade a resume and get feedback
  Future<GradeResponse> gradeResume(String resumeOrFilename) async {
    try {
      // Ensure backend is ready before attempting to grade
      final isHealthy = await _waitForBackend(maxAttempts: 3);
      if (!isHealthy) {
        return GradeResponse(
          success: false,
          error: 'Backend is not responding. Please ensure the Flask backend is running on localhost:5000',
        );
      }

      // Determine if it's a filename or actual text
      final isFilename = resumeOrFilename.endsWith('.pdf') || 
                        resumeOrFilename.endsWith('.txt') ||
                        (!resumeOrFilename.contains('\n') && resumeOrFilename.length < 500);
      
      // Send as filename in query param (more reliable than JSON body for special chars)
      final requestData = isFilename 
          ? {'filename': resumeOrFilename}
          : {'resume_text': resumeOrFilename};
      
      final response = await _dio.post(
        '/grade-resume',
        data: requestData,
      );

      // Check for HTTP errors
      if (response.statusCode! >= 400) {
        logger.e('✗ HTTP ${response.statusCode}: ${response.statusMessage}');
        final errorMsg = (response.data as Map<String, dynamic>?)?['error'];
        return GradeResponse(
          success: false,
          error: errorMsg ?? 'Failed to grade resume (HTTP ${response.statusCode})',
        );
      }

      final data = response.data as Map<String, dynamic>;
      
      if (data['success'] != true) {
        return GradeResponse(
          success: false,
          error: data['error'] ?? 'Failed to grade resume',
        );
      }

      final gradeResponse = GradeResponse.fromJson(data);
      logger.i('✓ Resume graded: ${gradeResponse.grade?.score}/100');
      return gradeResponse;
    } catch (e) {
      logger.e('✗ Error grading resume: $e');
      return GradeResponse(
        success: false,
        error: 'Error grading resume: $e',
      );
    }
  }

  /// Parse resume to PDF format
  Future<Map<String, dynamic>> parseResume(String resumeText) async {
    try {
      // Ensure backend is ready before attempting to parse
      final isHealthy = await _waitForBackend(maxAttempts: 3);
      if (!isHealthy) {
        throw Exception(
          'Backend is not responding. Please ensure the Flask backend is running on localhost:5000'
        );
      }

      final response = await _dio.post(
        '/parse-resume',
        data: {
          'resume_text': resumeText,
        },
      );

      // Check for HTTP errors
      if (response.statusCode! >= 400) {
        logger.e('✗ HTTP ${response.statusCode}: ${response.statusMessage}');
        final errorMsg = (response.data as Map<String, dynamic>?)?['error'];
        throw Exception(errorMsg ?? 'Failed to parse resume (HTTP ${response.statusCode})');
      }

      final data = response.data as Map<String, dynamic>;

      if (data['success'] != true) {
        throw Exception(data['error'] ?? 'Failed to parse resume');
      }

      logger.i('✓ Parsed resume');
      return data['parsed_resume'] as Map<String, dynamic>;
    } catch (e) {
      logger.e('✗ Error parsing resume: $e');
      rethrow;
    }
  }

  /// Save resume as PDF
  Future<String> savePdf(
    String filename,
    Map<String, dynamic> resumeData,
  ) async {
    try {
      final response = await _dio.post(
        '/save-resume-pdf',
        data: {
          'filename': filename,
          'resume_text': resumeData,
        },
      );
      final data = response.data as Map<String, dynamic>;

      if (data['success'] != true) {
        throw Exception(data['error'] ?? 'Failed to save PDF');
      }

      logger.i('✓ Saved PDF: ${data['filename']}');
      return data['filename'] as String;
    } catch (e) {
      logger.e('✗ Error saving PDF: $e');
      rethrow;
    }
  }

  /// Save plain text as PDF (for polished/tailored resumes)
  Future<Map<String, dynamic>> saveTextPdf(String filename, String textContent) async {
    try {
      final response = await _dio.post(
        '/save-text-pdf',
        data: {
          'filename': filename,
          'text_content': textContent,
        },
      );
      final data = response.data as Map<String, dynamic>;

      if (data['success'] != true) {
        throw Exception(data['error'] ?? 'Failed to save text PDF');
      }

      logger.i('✓ Saved text PDF: ${data['filename']} at ${data['path']}');
      return data; // Return full response with success, filename, and path
    } catch (e) {
      logger.e('✗ Error saving text PDF: $e');
      rethrow;
    }
  }

  /// Submit user feedback to Vercel API
  Future<Map<String, dynamic>> submitFeedback({
    required String type,
    required int rating,
    required String message,
    String? name,
    bool isAnonymous = false,
    String? email,
  }) async {
    try {
      // Determine the name to send
      final String submitName = isAnonymous 
          ? 'Anonymous' 
          : (name?.isNotEmpty == true ? name! : 'Anonymous');
      
      // Send to Vercel API instead of Flask backend
      final response = await _dio.post(
        '${AppConstants.vercelApiBase}/reviews',
        data: {
          'type': type,
          'rating': rating,
          'message': message,
          'email': email,
          'name': submitName,
        },
      );
      
      final data = response.data as Map<String, dynamic>;

      if (data['success'] != true) {
        throw Exception(data['error'] ?? 'Failed to submit feedback');
      }

      logger.i('✓ Feedback submitted to Vercel: ${data['review']['id']}');
      return data as Map<String, dynamic>;
    } catch (e) {
      logger.e('✗ Error submitting feedback: $e');
      rethrow;
    }
  }
}
