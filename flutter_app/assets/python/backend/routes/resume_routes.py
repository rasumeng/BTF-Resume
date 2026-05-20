"""
Resume Routes - HTTP endpoints for resume operations.
Clean separation: routes handle HTTP, services handle business logic.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

from services.file_service import FileService
from services.llm import LLMService
from services.feedback_service import FeedbackService

# Create blueprint
resume_bp = Blueprint('resume', __name__)

# ─────────────────────────────────────────────────────────────
# FILE OPERATIONS
# ─────────────────────────────────────────────────────────────

@resume_bp.route('/list-resumes', methods=['GET'])
def list_resumes():
    """List all resumes in the folder."""
    result = FileService.list_resumes()
    status_code = 200 if result.get('success') else 500
    return jsonify(result), status_code

@resume_bp.route('/get-resume', methods=['GET'])
def get_resume():
    """Get resume content by filename."""
    filename = request.args.get('filename')
    
    if not filename:
        return jsonify({"success": False, "error": "filename required"}), 400
    
    result = FileService.get_resume(filename)
    status_code = 200 if result.get('success') else 500
    return jsonify(result), status_code

@resume_bp.route('/update-resume', methods=['POST'])
def update_resume():
    """Update an existing resume."""
    data = request.get_json()
    filename = data.get('filename')
    content = data.get('content')
    
    if not filename or content is None:
        return jsonify({"success": False, "error": "filename and content required"}), 400
    
    result = FileService.update_resume(filename, content)
    status_code = 200 if result.get('success') else 500
    return jsonify(result), status_code

@resume_bp.route('/save-resume-pdf', methods=['POST'])
def save_resume_pdf():
    """Generate and save a PDF resume."""
    try:
        logger.info("=" * 70)
        logger.info("ROUTE: save_resume_pdf called")
        logger.info("=" * 70)
        
        # Test import right here in the route
        logger.info("Testing imports in route handler...")
        try:
            from core.pdf import generate_pdf as test_pdf
            logger.info("✓ Successfully imported generate_pdf from core.pdf")
        except ImportError as ie:
            logger.error(f"✗ Failed to import from core.pdf: {ie}")
        
        data = request.get_json()
        filename = data.get('filename')
        resume_text = data.get('resume_text')
        
        if not filename or not resume_text:
            return jsonify({"success": False, "error": "filename and resume_text required"}), 400
        
        # Ensure .pdf extension
        if not filename.endswith('.pdf'):
            filename = filename.replace('.txt', '') + '.pdf'
        
        logger.info(f"save_resume_pdf: Calling FileService.save_resume_pdf({filename})")
        result = FileService.save_resume_pdf(filename, resume_text)
        status_code = 200 if result.get('success') else 500
        logger.info(f"save_resume_pdf result: {result}")
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"save_resume_pdf route handler exception: {e}", exc_info=True)
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }), 500

@resume_bp.route('/save-text-pdf', methods=['POST'])
def save_text_pdf():
    """Generate a simple PDF from plain text (for polished/tailored resumes)."""
    try:
        logger.info("save_text_pdf called")
        
        data = request.get_json()
        filename = data.get('filename')
        text_content = data.get('text_content')
        
        if not filename or not text_content:
            return jsonify({"success": False, "error": "filename and text_content required"}), 400
        
        # Ensure .pdf extension
        if not filename.endswith('.pdf'):
            filename = filename.replace('.txt', '') + '.pdf'
        
        result = FileService.save_text_pdf(filename, text_content)
        status_code = 200 if result.get('success') else 500
        logger.info(f"save_text_pdf result: {result}")
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"save_text_pdf route handler exception: {e}", exc_info=True)
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }), 500

@resume_bp.route('/delete-resume', methods=['DELETE'])
def delete_resume():
    """Delete a resume file."""
    from pathlib import Path
    from services.cache_service import CacheService
    
    filename = request.args.get('filename')
    
    if not filename:
        return jsonify({"success": False, "error": "filename required"}), 400
    
    # Invalidate the cached parsed data
    try:
        from config import get_resumes_dir
        resumes_dir = get_resumes_dir()
        resume_path = Path(resumes_dir) / filename
        CacheService.invalidate_cache(resume_path)
    except Exception as cache_err:
        logger.warning(f"⚠️  Failed to invalidate cache: {cache_err}")
    
    result = FileService.delete_resume(filename)
    status_code = 200 if result.get('success') else 500
    return jsonify(result), status_code

# ─────────────────────────────────────────────────────────────
# LLM OPERATIONS (AI processing)
# ─────────────────────────────────────────────────────────────

@resume_bp.route('/polish-bullets', methods=['POST'])
def polish_bullets():
    """
    Polish resume bullets.
    
    Request JSON:
    {
        "bullets": ["bullet 1", "bullet 2", ...],
        "intensity": "light|medium|heavy"
    }
    """
    data = request.get_json()
    bullets = data.get('bullets', [])
    intensity = data.get('intensity', 'medium')
    
    if not isinstance(bullets, list) or len(bullets) == 0:
        return jsonify({"success": False, "error": "bullets array required"}), 400
    
    result = LLMService.polish_bullets(bullets, intensity)
    status_code = 200 if result.get('success') else 500
    return jsonify(result), status_code

@resume_bp.route('/extract-pdf-text', methods=['POST'])
def extract_pdf_text():
    """
    Extract text from a PDF file.
    
    Request: multipart/form-data with 'file' field containing PDF
    Response: {"success": true, "text": "extracted resume text"}
    """
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "file field required"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "error": "no file selected"}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({"success": False, "error": "only PDF files allowed"}), 400
        
        # Extract text from PDF
        try:
            import PyPDF2
            import io
            
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
            extracted_text = ""
            
            for page in pdf_reader.pages:
                extracted_text += page.extract_text() + "\n"
            
            if not extracted_text.strip():
                return jsonify({"success": False, "error": "no text found in PDF"}), 400
            
            logger.info(f'✓ Extracted {len(extracted_text)} characters from PDF: {file.filename}')
            return jsonify({"success": True, "text": extracted_text.strip()}), 200
            
        except ImportError:
            # Fallback if PyPDF2 not installed, try pdfplumber
            try:
                import pdfplumber
                import io
                
                with pdfplumber.open(io.BytesIO(file.read())) as pdf:
                    extracted_text = ""
                    for page in pdf.pages:
                        extracted_text += page.extract_text() + "\n"
                
                if not extracted_text.strip():
                    return jsonify({"success": False, "error": "no text found in PDF"}), 400
                
                logger.info(f'✓ Extracted {len(extracted_text)} characters from PDF: {file.filename}')
                return jsonify({"success": True, "text": extracted_text.strip()}), 200
            except ImportError:
                return jsonify({"success": False, "error": "PDF extraction libraries not available"}), 500
    
    except Exception as e:
        logger.error(f'Error extracting PDF text: {e}')
        return jsonify({"success": False, "error": f"extraction error: {str(e)}"}), 500

@resume_bp.route('/polish-resume', methods=['POST'])
def polish_resume():
    """
    Polish an entire resume using AI.
    
    Request JSON:
    {
        "resume_text": "...",
        "intensity": "light|medium|aggressive"
    }
    """
    data = request.get_json()
    resume_text = data.get('resume_text', '')
    intensity = data.get('intensity', 'medium')
    
    if not resume_text or not isinstance(resume_text, str):
        return jsonify({"success": False, "error": "resume_text required"}), 400
    
    result = LLMService.polish_resume(resume_text, intensity)
    status_code = 200 if result.get('success') else 500
    return jsonify(result), status_code

@resume_bp.route('/get-polish-changes', methods=['POST'])
def get_polish_changes():
    """
    Get a summary of changes between original and polished resume.
    
    Request JSON:
    {
        "original_resume": "...",
        "polished_resume": "..."
    }
    """
    try:
        data = request.get_json()
        original_resume = data.get('original_resume')
        polished_resume = data.get('polished_resume')
        
        if not original_resume or not polished_resume:
            return jsonify({
                "success": False,
                "error": "original_resume and polished_resume required"
            }), 400
        
        result = LLMService.get_changes_summary(original_resume, polished_resume)
        status_code = 200 if result.get('success') else 500
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"✗ Exception in get_polish_changes: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@resume_bp.route('/tailor-resume', methods=['POST'])
def tailor_resume():
    """
    Tailor a resume to a job description with comprehensive analysis.
    
    Request JSON:
    {
        "resume_text": "...",
        "job_description": "...",
        "intensity": "light|medium|heavy" (optional, default: "medium")
    }
    """
    from services.job_tailor_service import JobTailorService
    from dataclasses import asdict
    
    data = request.get_json()
    resume_text = data.get('resume_text')
    job_description = data.get('job_description')
    intensity = data.get('intensity', 'medium')
    
    if not resume_text or not job_description:
        return jsonify({"success": False, "error": "resume_text and job_description required"}), 400
    
    try:
        # Use JobTailorService for comprehensive analysis with LLM
        tailor_result = JobTailorService.tailor_resume(resume_text, job_description, intensity)
        
        if not tailor_result:
            return jsonify({"success": False, "error": "Failed to tailor resume"}), 500
        
        # Convert dataclass to dict with nested conversions
        result_dict = {
            "success": True,
            "overall_confidence": tailor_result.overall_confidence,
            "category_scores": [asdict(cs) for cs in tailor_result.category_scores],
            "matches": [asdict(m) for m in tailor_result.matches],
            "gaps": {
                "missing_skills": tailor_result.gaps.missing_skills,
                "missing_keywords": tailor_result.gaps.missing_keywords,
                "suggestions": tailor_result.gaps.suggestions,
            },
            "tailored_resume": tailor_result.tailored_resume_text,
            "changes_summary": tailor_result.changes_summary,
        }
        
        logger.info(f"✓ Tailor result: confidence={tailor_result.overall_confidence}%, matches={len(tailor_result.matches)}")
        return jsonify(result_dict), 200
    
    except Exception as e:
        logger.error(f"✗ Error in tailor_resume route: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@resume_bp.route('/analyze-fit', methods=['POST'])
def analyze_fit():
    """
    Analyze how well a resume fits a job description without tailoring.
    Returns confidence score, category breakdown, and matches.
    
    Request JSON:
    {
        "resume_text": "...",
        "job_description": "..."
    }
    """
    from services.job_tailor_service import JobTailorService
    from dataclasses import asdict
    
    data = request.get_json()
    resume_text = data.get('resume_text')
    job_description = data.get('job_description')
    
    if not resume_text or not job_description:
        return jsonify({"success": False, "error": "resume_text and job_description required"}), 400
    
    try:
        # Use JobTailorService for analysis only (no tailoring)
        tailor_result = JobTailorService.tailor_resume(resume_text, job_description, intensity='light')
        
        if not tailor_result:
            return jsonify({"success": False, "error": "Failed to analyze fit"}), 500
        
        # Return just the analysis data, not the tailored resume
        result_dict = {
            "success": True,
            "overall_confidence": tailor_result.overall_confidence,
            "category_scores": [asdict(cs) for cs in tailor_result.category_scores],
            "matches": [asdict(m) for m in tailor_result.matches],
            "gaps": {
                "missing_skills": tailor_result.gaps.missing_skills,
                "missing_keywords": tailor_result.gaps.missing_keywords,
                "suggestions": tailor_result.gaps.suggestions,
            },
        }
        
        logger.info(f"✓ Fit analysis result: confidence={tailor_result.overall_confidence}%, matches={len(tailor_result.matches)}")
        return jsonify(result_dict), 200
    
    except Exception as e:
        logger.error(f"✗ Error in analyze_fit route: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@resume_bp.route('/grade-resume', methods=['POST'])
def grade_resume():
    """
    Grade a resume and provide feedback.
    
    Request JSON (option 1 - direct text):
    {
        "resume_text": "..."
    }
    
    Request JSON (option 2 - from filename):
    {
        "filename": "resume.pdf"
    }
    """
    import sys
    from pathlib import Path
    from services.cache_service import CacheService
    
    print("=== grade_resume route called ===", file=sys.stderr, flush=True)
    sys.stderr.flush()
    logger.warning("⚠️  grade_resume route called")
    try:
        data = request.get_json()
        resume_text = data.get('resume_text')
        filename = data.get('filename')
        
        # Get resume text either directly or from file
        if not resume_text and filename:
            # First check if we have cached parsed data
            from config import get_resumes_dir
            resumes_dir = get_resumes_dir()
            resume_path = Path(resumes_dir) / filename
            
            cached_parsed = CacheService.load_cached_resume(resume_path)
            if cached_parsed:
                # Reconstruct text from cached parsed data
                logger.info(f"📦 Using cached parsed data for grading: {filename}")
                resume_text = CacheService.extract_resume_text_from_cache(cached_parsed)
            
            # If no cache or cache load failed, extract from file
            if not resume_text:
                result = FileService.extract_resume_text(filename)
                if not result.get('success'):
                    return jsonify(result), 400
                resume_text = result.get('content')
                
                # Try to parse and cache for future use
                try:
                    parse_result = LLMService.parse_to_pdf_format(resume_text)
                    if parse_result.get('success'):
                        CacheService.save_parsed_resume(resume_path, parse_result.get('parsed_resume', {}))
                        logger.info(f"✅ Created cache during grading: {filename}")
                except Exception as parse_err:
                    logger.warning(f"⚠️  Failed to create cache during grading: {parse_err}")
        
        if not resume_text:
            return jsonify({
                "success": False, 
                "error": "resume_text or filename required"
            }), 400
        
        logger.warning("⚠️  Calling LLMService.grade_resume()")
        result = LLMService.grade_resume(resume_text)
        status_code = 200 if result.get('success') else 500
        return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"✗ Exception in grade_resume route: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@resume_bp.route('/parse-resume', methods=['POST'])
def parse_resume():
    """
    Parse resume text into structured PDF format.
    Automatically caches the parsed data for future operations.
    
    Request JSON:
    {
        "resume_text": "...",
        "filename": "resume.txt" (optional - for caching)
    }
    """
    data = request.get_json()
    resume_text = data.get('resume_text')
    filename = data.get('filename')
    
    if not resume_text:
        return jsonify({"success": False, "error": "resume_text required"}), 400
    
    result = LLMService.parse_to_pdf_format(resume_text)
    status_code = 200 if result.get('success') else 500
    
    # Cache the parsed data if filename provided
    if filename and result.get('success'):
        try:
            from pathlib import Path
            from config import get_resumes_dir
            from services.cache_service import CacheService
            
            parsed_data = result.get('parsed_resume', {})
            resumes_dir = get_resumes_dir()
            resume_path = Path(resumes_dir) / filename
            CacheService.save_parsed_resume(resume_path, parsed_data)
            logger.info(f"✅ Cached parsed resume: {filename}")
        except Exception as cache_err:
            logger.warning(f"⚠️  Failed to cache: {cache_err}")
    
    return jsonify(result), status_code

# ─────────────────────────────────────────────────────────────
# ALTERATION & VERSION MANAGEMENT
# ─────────────────────────────────────────────────────────────

@resume_bp.route('/save-altered-resume', methods=['POST'])
def save_altered_resume():
    """
    Save an altered (polished/tailored) resume with full version tracking.
    
    Implements complete workflow:
    1. Save as text (fallback format)
    2. Cache parsed JSON structure
    3. Generate professional PDF with metadata
    4. Track in version history
    5. Return comprehensive result
    
    Request JSON:
    {
        "original_filename": "resume.pdf",
        "altered_text": "...",
        "parsed_json": {...},  # Optional - pre-parsed structure
        "alteration_type": "polish|tailor",
        "intensity": "light|medium|heavy",  # For polish
        "job_description": "..."  # For tailor
    }
    """
    try:
        data = request.get_json()
        original_filename = data.get('original_filename')
        altered_text = data.get('altered_text')
        parsed_json = data.get('parsed_json')
        alteration_type = data.get('alteration_type', 'polish')
        intensity = data.get('intensity')
        job_description = data.get('job_description')
        
        # Validate inputs
        if not original_filename or not altered_text:
            return jsonify({
                "success": False,
                "error": "original_filename and altered_text required"
            }), 400
        
        logger.info(f"📝 Saving altered resume: {alteration_type} of {original_filename}")
        
        result = FileService.save_altered_resume(
            original_filename=original_filename,
            altered_text=altered_text,
            parsed_json=parsed_json,
            alteration_type=alteration_type,
            intensity=intensity,
            job_description=job_description
        )
        
        status_code = 200 if result.get('success') else 500
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"✗ Error saving altered resume: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }), 500

@resume_bp.route('/alteration-history', methods=['GET'])
def alteration_history():
    """
    Get the complete alteration history for a resume.
    
    Query parameters:
    - filename: Resume filename to retrieve history for
    
    Response:
    {
        "success": true,
        "filename": "resume.pdf",
        "total_alterations": 3,
        "created": "2026-04-19T10:00:00Z",
        "alterations": [
            {
                "id": "uuid",
                "type": "polish",
                "timestamp": "...",
                "intensity": "medium",
                "status": "saved",
                "text_file": "polished_medium_resume_...",
                "pdf_file": "polished_medium_resume_..."
            }
        ]
    }
    """
    try:
        filename = request.args.get('filename')
        
        if not filename:
            return jsonify({
                "success": False,
                "error": "filename query parameter required"
            }), 400
        
        result = FileService.get_alteration_history(filename)
        status_code = 200 if result.get('success') else 500
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"✗ Error retrieving alteration history: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@resume_bp.route('/alteration-stats', methods=['GET'])
def alteration_stats():
    """
    Get statistics about alterations for a resume.
    
    Query parameters:
    - filename: Resume filename to get stats for
    
    Response:
    {
        "success": true,
        "total_alterations": 5,
        "by_type": {
            "polish": 3,
            "tailor": 2
        },
        "latest_alteration": {
            "type": "tailor",
            "timestamp": "...",
            "status": "saved"
        }
    }
    """
    try:
        filename = request.args.get('filename')
        
        if not filename:
            return jsonify({
                "success": False,
                "error": "filename query parameter required"
            }), 400
        
        result = FileService.get_alteration_stats(filename)
        status_code = 200 if result.get('success') else 500
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"✗ Error retrieving alteration stats: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ─────────────────────────────────────────────────────────────
# FEEDBACK & FEATURE REQUESTS
# ─────────────────────────────────────────────────────────────

@resume_bp.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    """
    Submit user feedback or feature request.
    
    Request JSON:
    {
        "type": "bug_report|feature_request|general",
        "rating": 1-5,
        "message": "User feedback text",
        "email": "optional@email.com"
    }
    """
    data = request.get_json()
    feedback_type = data.get('type', 'general')
    rating = data.get('rating', 3)
    message = data.get('message', '')
    user_email = data.get('email', None)
    
    if not message:
        return jsonify({"success": False, "error": "Feedback message required"}), 400
    
    result = FeedbackService.submit_feedback(feedback_type, rating, message, user_email)
    status_code = 200 if result.get('success') else 400
    return jsonify(result), status_code

@resume_bp.route('/feedback-summary', methods=['GET'])
def feedback_summary():
    """Get summary of feedback received (for admin/owner)."""
    result = FeedbackService.get_feedback_summary()
    status_code = 200 if result.get('success') else 500
    return jsonify(result), status_code

# ─────────────────────────────────────────────────────────────
# RESPONSE SCHEMA
# ─────────────────────────────────────────────────────────────

"""
All responses follow this schema:

SUCCESS:
{
    "success": true,
    "data": {...},  # Operation-specific data
    "error": null,
    "timestamp": "2024-01-01T00:00:00Z"
}

ERROR:
{
    "success": false,
    "data": null,
    "error": "Error message",
    "timestamp": "2024-01-01T00:00:00Z"
}
"""

@resume_bp.before_request
def before_request():
    """Add timestamp to all responses."""
    request.start_time = datetime.utcnow()

@resume_bp.after_request
def after_request(response):
    """Add metadata to response."""
    if response.is_json:
        try:
            data = response.get_json()
            if isinstance(data, dict):
                if 'timestamp' not in data:
                    data['timestamp'] = datetime.utcnow().isoformat()
                response.set_data(json.dumps(data))
        except:
            pass
    return response
