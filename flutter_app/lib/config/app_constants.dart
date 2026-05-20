/// App-wide constants and configuration
class AppConstants {
  // API Configuration
  static const String flaskHost = 'localhost';
  static const int flaskPort = 5000;
  static const String flaskApiBase = 'http://$flaskHost:$flaskPort/api';
  
  // Vercel API (for feedback/reviews)
  static const String vercelApiBase = 'https://beyondtheframe.vercel.app/api';
  
  // Endpoints
  static const String healthEndpoint = '$flaskApiBase/health';
  static const String listResumesEndpoint = '$flaskApiBase/list-resumes';
  static const String getResumeEndpoint = '$flaskApiBase/get-resume';
  static const String updateResumeEndpoint = '$flaskApiBase/update-resume';
  static const String deleteResumeEndpoint = '$flaskApiBase/delete-resume';
  static const String saveResumePdfEndpoint = '$flaskApiBase/save-resume-pdf';
  static const String polishBulletsEndpoint = '$flaskApiBase/polish-bullets';
  static const String tailorResumeEndpoint = '$flaskApiBase/tailor-resume';
  static const String gradeResumeEndpoint = '$flaskApiBase/grade-resume';
  static const String parseResumeEndpoint = '$flaskApiBase/parse-resume';
  
  // Timeouts
  static const int connectionTimeout = 30000; // 30 seconds
  static const int receiveTimeout = 180000;   // 180 seconds (3 min) for LLM calls
  
  // Backend startup
  static const int backendStartupTimeout = 30000; // 30 seconds max wait
  static const int healthCheckRetryInterval = 500; // 500ms between checks
  
  // UI
  static const String appTitle = 'BTF Resume - AI Resume Helper';
  static const String appVersion = '1.0.0';
  
  // Embedded Runtime Paths
  static const String ollamaHost = 'localhost';
  static const int ollamaPort = 11434;
  static const String ollamaApiBase = 'http://$ollamaHost:$ollamaPort';
  
  // First-time setup
  static const String setupCompleteKey = 'setup_complete';
  static const String ollamaDownloadedKey = 'ollama_downloaded';
  static const String modelDownloadedKey = 'model_downloaded';
  
  // Model names
  static const String defaultModel = 'llama3.2'; // Default Ollama model
}
