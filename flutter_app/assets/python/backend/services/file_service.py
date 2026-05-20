"""
File Service - Handles resume file operations.
Responsible for: listing, loading, saving, and deleting resumes.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

from config import get_resumes_dir, get_outputs_dir
from services.alteration_service import AlterationService, AlterationMetadata

class FileService:
    """Service for managing resume files."""
    
    @staticmethod
    def list_resumes():
        """
        List all resumes in the resumes folder.
        Returns list of files with metadata.
        """
        try:
            resumes_dir = get_resumes_dir()
            files = []
            
            # Get .txt and .pdf files (exclude .json metadata files)
            for file in resumes_dir.iterdir():
                if file.is_file() and not file.name.endswith('.json'):
                    files.append({
                        "name": file.name,
                        "path": str(file),
                        "size": file.stat().st_size,
                        "modified": file.stat().st_mtime,
                        "created": file.stat().st_ctime
                    })
            
            # Sort by modified time (newest first)
            files.sort(key=lambda x: x['modified'], reverse=True)
            
            logger.info(f"✓ Listed {len(files)} resumes")
            return {"success": True, "resumes": files}
        except Exception as e:
            logger.error(f"✗ Error listing resumes: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_resume(filename):
        """
        Load a resume file content.
        
        Args:
            filename: Name of the resume file
            
        Returns:
            File content as string
        """
        try:
            resumes_dir = get_resumes_dir()
            file_path = resumes_dir / filename
            
            # Security: Prevent path traversal
            if not file_path.parent == resumes_dir:
                raise ValueError("Invalid file path")
            
            if not file_path.exists():
                raise FileNotFoundError(f"Resume not found: {filename}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.info(f"✓ Loaded resume: {filename}")
            return {"success": True, "content": content, "filename": filename}
        except FileNotFoundError as e:
            logger.error(f"✗ File not found: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"✗ Error loading resume: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def save_resume_pdf(filename, resume_text):
        """
        Generate and save a PDF resume.
        
        Args:
            filename: Output filename (should end with .pdf)
            resume_text: Parsed resume text (JSON format from core logic)
            
        Returns:
            Path to saved PDF
        """
        try:
            import json
            logger.info(f"🚀 Starting PDF generation for {filename}")
            
            # Import inside method to avoid Flask module caching issues
            logger.info("Importing PDF generation modules...")
            from core.pdf import generate_pdf
            from core.resume_model import ResumData
            logger.info("✓ Imported generate_pdf and ResumData")
                
            outputs_dir = get_outputs_dir()
            output_path = outputs_dir / filename
            
            # Parse resume text if it's JSON
            if isinstance(resume_text, str):
                try:
                    resume_dict = json.loads(resume_text)
                except json.JSONDecodeError:
                    raise ValueError("Resume text must be valid JSON")
            else:
                resume_dict = resume_text
            
            logger.info("Converting to ResumData...")
            # Convert dict to ResumData object
            resume_data = ResumData.from_llm_json(resume_dict)
            logger.info("✓ Converted to ResumData")
            
            # Validate resume data
            is_valid, errors = resume_data.validate()
            if not is_valid:
                error_msg = "; ".join(errors)
                logger.error(f"✗ Resume validation failed: {error_msg}")
                return {"success": False, "error": f"Invalid resume data: {error_msg}"}
            
            logger.info("Generating PDF...")
            # Generate PDF
            success = generate_pdf(resume_data, str(output_path))
            logger.info(f"PDF generation success: {success}")
            
            if success:
                logger.info(f"✓ Generated PDF: {filename}")
                return {
                    "success": True,
                    "filename": filename,
                    "path": str(output_path)
                }
            else:
                return {"success": False, "error": "PDF generation failed"}
                
        except Exception as e:
            logger.error(f"✗ Error generating PDF: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def save_text_pdf(filename, text_content):
        """
        Generate a professional PDF from polished/tailored plain text using template.
        
        WORKFLOW:
        1. Parse plain text into structured JSON
        2. Build ResumData object from JSON
        3. Generate professional PDF using pdf_generator template
        4. Save to resumes/ directory (user storage, not temp storage)
        
        Args:
            filename: Output filename (should end with .pdf)
            text_content: Plain text resume content (from polishing/tailoring)
            
        Returns:
            {"success": true, "filename": ..., "path": ...} or error dict
        """
        try:
            logger.info(f"🚀 Starting polished resume PDF generation for {filename}")
            
            # Step 1: Parse plain text into structured JSON
            from backend.services.llm import LLMService
            parse_result = LLMService.parse_to_pdf_format(text_content)
            
            if not parse_result.get("success"):
                logger.error(f"Failed to parse polished resume: {parse_result.get('error')}")
                raise Exception(parse_result.get("error", "Failed to parse resume"))
            
            parsed_json = parse_result.get("parsed_resume", {})
            logger.info(f"✓ Parsed polished resume structure")
            logger.debug(f"Parsed JSON keys: {list(parsed_json.keys())}")
            
            # Step 2: Build ResumData from parsed JSON
            from core.resume_model import ResumData
            try:
                resume_data = ResumData.from_llm_json(parsed_json)
                logger.info(f"✓ Built ResumData object")
            except Exception as e:
                logger.error(f"Failed to build ResumData: {e}")
                logger.error(f"Parsed JSON was: {str(parsed_json)[:500]}")
                raise Exception(f"Failed to build resume structure: {e}")
            
            # Step 3: Generate professional PDF using template
            from core.pdf_generator import generate_pdf
            
            # Save to resumes/ directory (user storage) instead of outputs/ (temp)
            resumes_dir = get_resumes_dir()
            
            # Add "polished_" prefix to distinguish from originals
            polished_filename = f"polished_{filename}" if not filename.startswith("polished_") else filename
            output_path = resumes_dir / polished_filename
            
            # Create directory if it doesn't exist
            resumes_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Generating PDF to: {output_path}")
            
            # Generate PDF using professional template
            success = generate_pdf(resume_data, str(output_path))
            
            if not success:
                logger.error(f"PDF generation returned False")
                # Even if generate_pdf returns False, check if file was created
                if output_path.exists():
                    logger.warning(f"PDF was created despite False return")
                    success = True
                else:
                    raise Exception("PDF generation failed and file was not created")
            
            # Final verification
            if not output_path.exists():
                logger.error(f"PDF file does not exist at {output_path}")
                logger.error(f"Directory listing:")
                for item in resumes_dir.iterdir():
                    logger.error(f"  - {item}")
                raise Exception(f"PDF file not found at {output_path}")
            
            logger.info(f"✓ Generated professional polished resume PDF: {polished_filename}")
            
            return {
                "success": True,
                "filename": polished_filename,
                "path": str(output_path)
            }
            
        except Exception as e:
            logger.error(f"✗ Error generating polished resume PDF: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def update_resume(filename, content):
        """
        Update an existing resume file.
        
        Args:
            filename: Name of the resume file
            content: New content
            
        Returns:
            Confirmation
        """
        try:
            resumes_dir = get_resumes_dir()
            file_path = resumes_dir / filename
            
            # Security: Prevent path traversal
            if not file_path.parent == resumes_dir:
                raise ValueError("Invalid file path")
            
            if not file_path.exists():
                raise FileNotFoundError(f"Resume not found: {filename}")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"✓ Updated resume: {filename}")
            return {"success": True, "filename": filename}
        except Exception as e:
            logger.error(f"✗ Error updating resume: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def delete_resume(filename):
        """
        Delete a resume file.
        
        Args:
            filename: Name of the resume file
            
        Returns:
            Confirmation
        """
        try:
            resumes_dir = get_resumes_dir()
            file_path = resumes_dir / filename
            
            # Security: Prevent path traversal
            if not file_path.parent == resumes_dir:
                raise ValueError("Invalid file path")
            
            if not file_path.exists():
                raise FileNotFoundError(f"Resume not found: {filename}")
            
            os.remove(file_path)
            
            # Also delete associated JSON metadata if it exists
            json_path = file_path.with_suffix('.json')
            if json_path.exists():
                os.remove(json_path)
            
            logger.info(f"✓ Deleted resume: {filename}")
            return {"success": True, "deleted": filename}
        except Exception as e:
            logger.error(f"✗ Error deleting resume: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def extract_resume_text(filename):
        """
        Extract text from a resume file (PDF or TXT).
        Accepts either full path or just filename.
        Checks both resumes/ and flutter_app/resumes/ directories.
        
        Args:
            filename: Name of the resume file or full path
            
        Returns:
            Extracted text content
        """
        try:
            # Extract just the filename if a full path was provided
            import os
            if os.path.sep in filename or '/' in filename:
                filename = os.path.basename(filename)
            
            resumes_dir = get_resumes_dir()
            file_path = resumes_dir / filename
            
            # DEBUG: Log the exact path being searched
            logger.warning(f"🔍 DEBUG: Looking for resume...")
            logger.warning(f"   resumes_dir: {resumes_dir}")
            logger.warning(f"   filename: {filename}")
            logger.warning(f"   full file_path: {file_path}")
            logger.warning(f"   file_path exists: {file_path.exists()}")

            def _try_resolve_alternate_name(name: str) -> Optional[Path]:
                """Resolve common UI/generated filename variants to an existing file."""
                stem = Path(name).stem
                suffix = Path(name).suffix.lower()

                # Common naming variants seen in app flows.
                variants = {
                    stem,
                    stem.replace(" - AI", ""),
                    stem.replace("_AI", ""),
                    stem.replace(" AI", ""),
                }

                candidate_exts = [suffix] if suffix in {".pdf", ".txt"} else [".pdf", ".txt"]
                for variant in variants:
                    for ext in candidate_exts:
                        candidate = resumes_dir / f"{variant}{ext}"
                        if candidate.exists():
                            return candidate

                # Last resort: pick first close filename match.
                try:
                    files = [p for p in resumes_dir.iterdir() if p.is_file() and p.suffix.lower() in {".pdf", ".txt"}]
                    normalized = stem.lower().replace("- ai", "").strip()
                    for p in files:
                        p_norm = p.stem.lower().replace("- ai", "").strip()
                        if p_norm == normalized or p_norm.startswith(normalized) or normalized.startswith(p_norm):
                            return p
                except Exception:
                    pass

                return None
            
            # If not found in resumes/, check flutter_app/resumes/
            if not file_path.exists():
                resolved = _try_resolve_alternate_name(filename)
                if resolved is not None:
                    file_path = resolved
                    filename = resolved.name
                    logger.info(f"Resolved resume filename to existing file: {filename}")

            if not file_path.exists():
                flutter_resumes = Path.cwd() / "flutter_app" / "resumes" / filename
                logger.warning(f"🔍 DEBUG: Checking fallback path: {flutter_resumes}")
                logger.warning(f"   fallback exists: {flutter_resumes.exists()}")
                if flutter_resumes.exists():
                    file_path = flutter_resumes
                    logger.info(f"Found resume in flutter_app/resumes: {filename}")
            
            # Security: Prevent path traversal
            if not file_path.exists():
                raise FileNotFoundError(f"Resume not found: {filename}")
            
            # Handle PDF files
            if filename.lower().endswith('.pdf'):
                try:
                    import pdfplumber
                    with pdfplumber.open(file_path) as pdf:
                        text = ""
                        for page in pdf.pages:
                            text += page.extract_text() + "\n"
                    logger.info(f"✓ Extracted text from PDF: {filename}")
                    return {"success": True, "content": text.strip(), "filename": filename}
                except Exception as e:
                    logger.error(f"✗ Error extracting PDF text: {e}")
                    raise
            
            # Handle text files
            elif filename.lower().endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                logger.info(f"✓ Loaded text file: {filename}")
                return {"success": True, "content": content, "filename": filename}
            
            else:
                raise ValueError(f"Unsupported file type: {filename}")
        
        except Exception as e:
            logger.error(f"✗ Error extracting resume text: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def save_altered_resume(
        original_filename: str,
        altered_text: str,
        parsed_json: Optional[Dict] = None,
        alteration_type: str = 'polish',
        intensity: Optional[str] = None,
        job_description: Optional[str] = None
    ) -> Dict:
        """
        Save an altered resume (polished/tailored) with full version tracking.
        
        WORKFLOW:
        1. Save altered text as fallback format
        2. Cache parsed JSON structure
        3. Generate professional PDF with metadata
        4. Track alteration in version history
        5. Return all paths and metadata
        
        Args:
            original_filename: Original resume filename
            altered_text: The polished/tailored resume text
            parsed_json: Pre-parsed JSON structure (optional - to avoid re-parsing)
            alteration_type: 'polish' | 'tailor'
            intensity: For polish - 'light' | 'medium' | 'heavy'
            job_description: For tailor - the job description used
            
        Returns:
            {
                "success": bool,
                "text_file": str,      # Fallback text version
                "pdf_file": str,       # Generated PDF
                "pdf_path": str,       # Full path to PDF
                "preview_url": str,    # URL for preview (optional)
                "alteration_id": str,  # Unique ID for this alteration
                "history": dict        # Full alteration history
            }
        """
        try:
            logger.info(f"🚀 Starting full alteration workflow for {original_filename}")
            
            # Step 1: Save altered text as fallback
            text_filename = AlterationService.save_alteration_text(
                altered_text,
                alteration_type,
                original_filename,
                intensity
            )
            logger.info(f"✓ Step 1: Saved text fallback: {text_filename}")
            
            # Step 2: Parse and cache JSON structure (if not provided)
            if parsed_json is None:
                logger.info("Step 2: Parsing text into structured JSON...")
                from backend.services.llm import LLMService
                parse_result = LLMService.parse_to_pdf_format(altered_text)
                
                if not parse_result.get("success"):
                    logger.warning(f"⚠️  JSON parsing failed: {parse_result.get('error')}")
                    parsed_json = {}
                else:
                    parsed_json = parse_result.get("parsed_resume", {})
            
            # Cache the parsed structure
            AlterationService.cache_parsed_structure(parsed_json, text_filename)
            logger.info(f"✓ Step 2: Cached parsed structure")
            
            # Step 3: Build ResumData and generate PDF
            logger.info("Step 3: Building ResumData object...")
            from core.resume_model import ResumData
            from core.pdf import generate_pdf
            
            try:
                resume_data = ResumData.from_llm_json(parsed_json)
            except Exception as e:
                logger.error(f"Failed to build ResumData: {e}")
                raise Exception(f"Failed to build resume structure: {e}")
            
            # Validate resume data
            is_valid, errors = resume_data.validate()
            if not is_valid:
                error_msg = "; ".join(errors)
                logger.warning(f"⚠️  Resume validation warnings: {error_msg}")
                # Continue anyway - validation failures are non-critical
            
            # Generate PDF with metadata
            logger.info("Step 3: Generating professional PDF...")
            resumes_dir = get_resumes_dir()
            resumes_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate PDF filename matching text file
            pdf_filename = text_filename.replace('.txt', '.pdf')
            pdf_path = resumes_dir / pdf_filename
            
            # Create metadata for PDF
            pdf_metadata = {
                'title': f'Resume - {alteration_type.capitalize()}',
                'subject': f'{alteration_type.capitalize()} Resume Version',
                'alteration_type': alteration_type,
                'generation_timestamp': datetime.utcnow().isoformat(),
                'intensity': intensity,
            }
            
            success = generate_pdf(resume_data, str(pdf_path), metadata=pdf_metadata)
            
            if not success or not pdf_path.exists():
                logger.error("PDF generation failed")
                raise Exception("PDF generation failed and file was not created")
            
            logger.info(f"✓ Step 3: Generated PDF: {pdf_filename}")
            
            # Step 4: Track in version history
            logger.info("Step 4: Tracking in version history...")
            metadata = AlterationService.create_alteration_metadata(
                alteration_type=alteration_type,
                original_file=original_filename,
                intensity=intensity,
                job_description=job_description
            )
            metadata.output_text = text_filename
            metadata.output_pdf = pdf_filename
            metadata.parsed_json = parsed_json
            metadata.status = "saved"
            metadata.preview_available = True
            
            history = AlterationService.add_alteration_to_history(original_filename, metadata)
            logger.info(f"✓ Step 4: Added to version history (total alterations: {len(history.alterations)})")
            
            # Step 5: Return comprehensive result
            result = {
                "success": True,
                "text_file": text_filename,
                "pdf_file": pdf_filename,
                "pdf_path": str(pdf_path),
                "alteration_id": metadata.alteration_id,
                "alteration_type": alteration_type,
                "intensity": intensity,
                "status": "saved",
                "preview_available": True,
                "history_count": len(history.alterations)
            }
            
            logger.info(f"✅ Alteration workflow complete for {original_filename}")
            return result
            
        except Exception as e:
            logger.error(f"✗ Error in alteration workflow: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    @staticmethod
    def get_alteration_history(filename: str) -> Dict:
        """Get the version history for a resume."""
        try:
            history = AlterationService.load_history(filename)
            
            if not history:
                return {
                    "success": True,
                    "filename": filename,
                    "total_alterations": 0,
                    "alterations": []
                }
            
            return {
                "success": True,
                "filename": filename,
                "created": history.created_at,
                "total_alterations": len(history.alterations),
                "alterations": [
                    {
                        "id": alt.alteration_id,
                        "type": alt.alteration_type,
                        "timestamp": alt.timestamp,
                        "intensity": alt.intensity,
                        "status": alt.status,
                        "text_file": alt.output_text,
                        "pdf_file": alt.output_pdf,
                    }
                    for alt in history.alterations
                ]
            }
        except Exception as e:
            logger.error(f"✗ Error retrieving history: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_alteration_stats(filename: str) -> Dict:
        """Get statistics about alterations for a resume."""
        return AlterationService.get_alteration_stats(filename)
