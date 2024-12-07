# app/model/feedback_system.py
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, List, Union
import logging

class FeedbackSystem:
    def __init__(self, feedback_file: str = "feedback_data.json"):
        self.feedback_dir = Path("app/data/feedback")
        self.feedback_file = self.feedback_dir / feedback_file
        self.feedback_data = self._load_feedback_data()
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging for feedback system"""
        logging.basicConfig(
            filename=self.feedback_dir / 'feedback_system.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _load_feedback_data(self) -> Dict:
        """Load existing feedback data or create new structure"""
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
        
        if self.feedback_file.exists():
            try:
                with open(self.feedback_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                self.logger.error("Error loading feedback data, creating new structure")
                return self._create_new_feedback_structure()
        else:
            return self._create_new_feedback_structure()

    def _create_new_feedback_structure(self) -> Dict:
        """Create new feedback data structure"""
        return {
            "recommendations": {},
            "phase_predictions": {},
            "performance_predictions": {},
            "team_balance_suggestions": {},
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "total_feedback_entries": 0
            }
        }

    def record_recommendation_feedback(
        self,
        recommendation_id: str,
        player_id: str,
        recommendation_type: str,
        actual_outcome: Dict,
        success_metrics: Dict
    ) -> bool:
        """
        Record feedback for a specific recommendation
        
        Parameters:
        - recommendation_id: Unique identifier for the recommendation
        - player_id: Player's unique identifier
        - recommendation_type: Type of recommendation (transfer, development, etc.)
        - actual_outcome: Actual results after implementing recommendation
        - success_metrics: Metrics to evaluate success
        """
        try:
            feedback_entry = {
                "timestamp": datetime.now().isoformat(),
                "player_id": player_id,
                "recommendation_type": recommendation_type,
                "actual_outcome": actual_outcome,
                "success_metrics": success_metrics,
                "success_score": self._calculate_success_score(actual_outcome, success_metrics)
            }
            
            self.feedback_data["recommendations"][recommendation_id] = feedback_entry
            self._update_metadata()
            self._save_feedback_data()
            
            self.logger.info(f"Recorded feedback for recommendation {recommendation_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error recording feedback: {str(e)}")
            return False

    def record_phase_prediction_feedback(
        self,
        player_id: str,
        predicted_phase: str,
        actual_phase: str,
        performance_metrics: Dict
    ) -> bool:
        """Record feedback for career phase predictions"""
        try:
            feedback_entry = {
                "timestamp": datetime.now().isoformat(),
                "predicted_phase": predicted_phase,
                "actual_phase": actual_phase,
                "performance_metrics": performance_metrics,
                "prediction_accuracy": 1 if predicted_phase == actual_phase else 0
            }
            
            if player_id not in self.feedback_data["phase_predictions"]:
                self.feedback_data["phase_predictions"][player_id] = []
            
            self.feedback_data["phase_predictions"][player_id].append(feedback_entry)
            self._update_metadata()
            self._save_feedback_data()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error recording phase prediction feedback: {str(e)}")
            return False

    def analyze_feedback_trends(self) -> Dict:
        """Analyze feedback data to identify trends and areas for improvement"""
        try:
            analysis = {
                "recommendation_success_rate": self._calculate_recommendation_success_rate(),
                "phase_prediction_accuracy": self._calculate_phase_prediction_accuracy(),
                "common_failure_patterns": self._identify_failure_patterns(),
                "improvement_suggestions": self._generate_improvement_suggestions()
            }
            
            self.logger.info("Completed feedback trend analysis")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing feedback trends: {str(e)}")
            return {}

    def _calculate_success_score(self, actual_outcome: Dict, success_metrics: Dict) -> float:
        """Calculate success score based on actual outcomes and metrics"""
        try:
            weights = {
                "performance_improvement": 0.4,
                "team_impact": 0.3,
                "financial_outcome": 0.3
            }
            
            scores = {
                metric: self._compare_outcome_to_metric(
                    actual_outcome.get(metric, 0),
                    success_metrics.get(metric, 0)
                )
                for metric in weights.keys()
            }
            
            weighted_score = sum(scores[metric] * weight 
                               for metric, weight in weights.items())
            
            return round(weighted_score, 2)
            
        except Exception as e:
            self.logger.error(f"Error calculating success score: {str(e)}")
            return 0.0

    def _compare_outcome_to_metric(self, actual: float, expected: float) -> float:
        """Compare actual outcome to expected metric"""
        if expected == 0:
            return 1.0 if actual >= 0 else 0.0
        return min(max(actual / expected, 0.0), 1.0)

    def _update_metadata(self):
        """Update metadata for feedback data"""
        self.feedback_data["metadata"]["last_updated"] = datetime.now().isoformat()
        self.feedback_data["metadata"]["total_feedback_entries"] = sum(
            len(entries) if isinstance(entries, list) else 1
            for category in self.feedback_data.values()
            if isinstance(category, dict)
            for entries in category.values()
        )

    def _save_feedback_data(self):
        """Save feedback data to file"""
        try:
            with open(self.feedback_file, 'w') as f:
                json.dump(self.feedback_data, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving feedback data: {str(e)}")

    def get_feedback_summary(self) -> Dict:
        """Get summary of feedback data"""
        return {
            "total_entries": self.feedback_data["metadata"]["total_feedback_entries"],
            "last_updated": self.feedback_data["metadata"]["last_updated"],
            "recommendation_count": len(self.feedback_data["recommendations"]),
            "phase_prediction_count": sum(
                len(predictions) 
                for predictions in self.feedback_data["phase_predictions"].values()
            )
        }

    def _calculate_recommendation_success_rate(self) -> float:
        """Calculate success rate of recommendations"""
        if not self.feedback_data["recommendations"]:
            return 0.0
        
        success_scores = [rec["success_score"] 
                         for rec in self.feedback_data["recommendations"].values()]
        return sum(success_scores) / len(success_scores)

    def _calculate_phase_prediction_accuracy(self) -> float:
        """Calculate accuracy of phase predictions"""
        if not self.feedback_data["phase_predictions"]:
            return 0.0
        
        accuracies = []
        for predictions in self.feedback_data["phase_predictions"].values():
            accuracies.extend([pred["prediction_accuracy"] for pred in predictions])
        
        return sum(accuracies) / len(accuracies) if accuracies else 0.0

    def _identify_failure_patterns(self) -> Dict:
        """Identify common patterns in unsuccessful predictions/recommendations"""
        patterns = {
            "phase_mismatches": {},
            "low_performing_recommendations": []
        }
        
        # Analyze phase prediction failures
        for player_id, predictions in self.feedback_data["phase_predictions"].items():
            for pred in predictions:
                if pred["prediction_accuracy"] == 0:
                    mismatch = f"{pred['predicted_phase']} -> {pred['actual_phase']}"
                    patterns["phase_mismatches"][mismatch] = patterns["phase_mismatches"].get(mismatch, 0) + 1
        
        # Analyze low-performing recommendations
        for rec_id, rec in self.feedback_data["recommendations"].items():
            if rec["success_score"] < 0.5:
                patterns["low_performing_recommendations"].append({
                    "type": rec["recommendation_type"],
                    "score": rec["success_score"]
                })
        
        return patterns

    def _generate_improvement_suggestions(self) -> List[str]:
        """Generate suggestions for model improvement based on feedback"""
        suggestions = []
        
        # Analyze phase prediction accuracy
        phase_accuracy = self._calculate_phase_prediction_accuracy()
        if phase_accuracy < 0.8:
            suggestions.append("Consider retraining phase prediction model with recent data")
        
        # Analyze recommendation success
        rec_success = self._calculate_recommendation_success_rate()
        if rec_success < 0.7:
            suggestions.append("Review recommendation criteria and thresholds")
        
        # Add more specific suggestions based on failure patterns
        patterns = self._identify_failure_patterns()
        if patterns["phase_mismatches"]:
            most_common_mismatch = max(patterns["phase_mismatches"].items(), key=lambda x: x[1])
            suggestions.append(f"Focus on improving {most_common_mismatch[0]} phase predictions")
        
        return suggestions