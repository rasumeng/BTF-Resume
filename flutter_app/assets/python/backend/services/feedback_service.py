"""
Feedback Service - Handles user feedback and feature requests.
Stores feedback in JSON files for easy access and review.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class FeedbackService:
    """Service for managing user feedback and feature requests."""
    
    @staticmethod
    def get_feedback_dir():
        """Get or create feedback directory."""
        feedback_dir = Path(__file__).parent.parent.parent / "feedback"
        feedback_dir.mkdir(exist_ok=True)
        return feedback_dir
    
    @staticmethod
    def submit_feedback(feedback_type, rating, message, user_email=None):
        """
        Submit user feedback.
        
        Args:
            feedback_type: "bug_report", "feature_request", or "general"
            rating: 1-5 star rating of the app
            message: User's feedback message
            user_email: Optional email for follow-up
            
        Returns:
            Dict with success status and feedback ID
        """
        try:
            # Validate inputs
            if not message or len(message.strip()) == 0:
                return {
                    "success": False,
                    "error": "Feedback message cannot be empty"
                }
            
            if not isinstance(rating, int) or rating < 1 or rating > 5:
                return {
                    "success": False,
                    "error": "Rating must be between 1 and 5"
                }
            
            if feedback_type not in ["bug_report", "feature_request", "general"]:
                return {
                    "success": False,
                    "error": "Invalid feedback type"
                }
            
            # Create feedback entry
            feedback_entry = {
                "id": datetime.utcnow().isoformat(),
                "type": feedback_type,
                "rating": rating,
                "message": message.strip(),
                "email": user_email if user_email and user_email.strip() else None,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "new"
            }
            
            # Save feedback to file
            feedback_dir = FeedbackService.get_feedback_dir()
            feedback_file = feedback_dir / "feedback.jsonl"
            
            # Append to feedback log (one JSON object per line)
            with open(feedback_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(feedback_entry) + "\n")
            
            logger.info(f"✓ Feedback received: {feedback_entry['id']}")
            
            return {
                "success": True,
                "data": {
                    "id": feedback_entry["id"],
                    "message": "Thank you for your feedback!"
                }
            }
            
        except Exception as e:
            logger.error(f"✗ Error submitting feedback: {e}")
            return {
                "success": False,
                "error": f"Failed to submit feedback: {str(e)}"
            }
    
    @staticmethod
    def get_feedback_summary():
        """
        Get summary of all feedback.
        
        Returns:
            Dict with feedback statistics
        """
        try:
            feedback_dir = FeedbackService.get_feedback_dir()
            feedback_file = feedback_dir / "feedback.jsonl"
            
            if not feedback_file.exists():
                return {
                    "success": True,
                    "data": {
                        "total": 0,
                        "by_type": {},
                        "average_rating": 0
                    }
                }
            
            feedback_list = []
            with open(feedback_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        feedback_list.append(json.loads(line))
            
            # Calculate statistics
            total = len(feedback_list)
            by_type = {}
            total_rating = 0
            
            for feedback in feedback_list:
                ftype = feedback.get('type', 'general')
                by_type[ftype] = by_type.get(ftype, 0) + 1
                total_rating += feedback.get('rating', 0)
            
            average_rating = total_rating / total if total > 0 else 0
            
            return {
                "success": True,
                "data": {
                    "total": total,
                    "by_type": by_type,
                    "average_rating": round(average_rating, 2),
                    "recent": feedback_list[-5:] if feedback_list else []
                }
            }
            
        except Exception as e:
            logger.error(f"✗ Error getting feedback summary: {e}")
            return {
                "success": False,
                "error": str(e)
            }
