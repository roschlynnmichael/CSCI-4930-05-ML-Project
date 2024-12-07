import pandas as pd
import numpy as np
from pathlib import Path
import joblib
from typing import Dict, List, Union
import logging
from sklearn.preprocessing import StandardScaler
from .roster_analyzer import RosterAnalyzer

class PerformancePredictor:
    def __init__(self):
        self._setup_logging()
        self.model_dir = Path(r"D:\Projects\Machine Learning Applications for Soccer\model_creation\Backend\app\model")
        self.roster_analyzer = RosterAnalyzer()
        self.career_phase_model = self._load_model("career_phase_model.joblib")
        self.scaler = StandardScaler()
        
    def _setup_logging(self):
        """Setup logging for performance predictor"""
        log_dir = Path('app/logs')
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            filename=log_dir / 'performance_predictor.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _load_model(self, model_name: str):
        """Load the trained model"""
        try:
            model_path = self.model_dir / model_name
            return joblib.load(model_path)
        except Exception as e:
            self.logger.error(f"Error loading model {model_name}: {str(e)}")
            raise

    def predict_performance(self, player_data: pd.DataFrame) -> Dict:
        """
        Predict future performance metrics for a player
        """
        try:
            # Get current career phase
            current_phase = self.roster_analyzer.analyze_team(player_data)['Career_Phase'].iloc[0]
            
            # Calculate performance metrics
            metrics = {
                'current_metrics': self._calculate_current_metrics(player_data),
                'predicted_metrics': self._predict_future_metrics(player_data),
                'career_trajectory': self._predict_career_trajectory(player_data, current_phase),
                'peak_prediction': self._predict_peak_performance(player_data),
                'value_projection': self._project_value_progression(player_data)
            }
            
            return metrics
        
        except Exception as e:
            self.logger.error(f"Error in performance prediction: {str(e)}")
            raise

    def _calculate_current_metrics(self, player_data: pd.DataFrame) -> Dict:
        """Calculate current performance metrics"""
        return {
            'games_per_season': player_data['Career_Games'].iloc[0] / max(1, (player_data['Age'].iloc[0] - 17)),
            'goals_per_game': player_data['Career_Goals'].iloc[0] / max(1, player_data['Career_Games'].iloc[0]),
            'assists_per_game': player_data['Career_Assists'].iloc[0] / max(1, player_data['Career_Games'].iloc[0]),
            'minutes_per_game': player_data['Career_Minutes'].iloc[0] / max(1, player_data['Career_Games'].iloc[0]),
            'cards_per_game': (player_data['Career_Yellows'].iloc[0] + player_data['Career_Reds'].iloc[0]) / 
                             max(1, player_data['Career_Games'].iloc[0])
        }

    def _predict_future_metrics(self, player_data: pd.DataFrame) -> Dict:
        """Predict future performance metrics"""
        age = player_data['Age'].iloc[0]
        current_metrics = self._calculate_current_metrics(player_data)
        
        # Refined age-based performance multipliers
        age_multipliers = {
            'breakthrough': 1.3,   # 30% improvement potential
            'development': 1.15,   # 15% improvement potential
            'peak': 1.05,         # 5% improvement potential
            'twilight': 0.9      # 10% decline
        }
        
        # Get current phase using age-based validation
        if age <= 20:
            current_phase = 'breakthrough'
        elif age <= 24:
            current_phase = 'development'
        elif age <= 29:
            current_phase = 'peak'
        else:
            current_phase = 'twilight'
        
        # Apply multiplier based on career phase
        multiplier = age_multipliers.get(current_phase, 1.0)
        
        return {
            'next_season': {
                metric: value * multiplier 
                for metric, value in current_metrics.items()
            },
            'peak_potential': {
                metric: value * 1.5  # 50% improvement potential at peak
                for metric, value in current_metrics.items()
            }
        }

    def _predict_career_trajectory(self, player_data: pd.DataFrame, current_phase: str) -> Dict:
        """Predict career trajectory and phase transitions"""
        age = player_data['Age'].iloc[0]
        
        # Define phase based on age
        if age <= 20:
            current_phase = 'breakthrough'
            next_phase = 'development'
            years_to_next = 21 - age
        elif age <= 24:
            current_phase = 'development'
            next_phase = 'peak'
            years_to_next = 25 - age
        elif age <= 29:
            current_phase = 'peak'
            next_phase = 'twilight'
            years_to_next = 30 - age
        else:
            current_phase = 'twilight'
            next_phase = 'retirement'
            years_to_next = 35 - age
        
        return {
            'current_phase': current_phase,
            'next_phase': next_phase,
            'years_to_next_phase': years_to_next,
            'development_potential': self._calculate_development_potential(player_data),
            'expected_peak_age': self._predict_peak_age(player_data)
        }

    def _predict_peak_performance(self, player_data: pd.DataFrame) -> Dict:
        """Predict peak performance metrics"""
        current_metrics = self._calculate_current_metrics(player_data)
        age = player_data['Age'].iloc[0]
        peak_age = self._predict_peak_age(player_data)
        
        # Calculate potential improvement factor
        years_to_peak = max(0, peak_age - age)
        improvement_factor = 1 + (years_to_peak * 0.1)  # 10% improvement per year until peak
        
        return {
            'peak_age': peak_age,
            'years_to_peak': years_to_peak,
            'peak_metrics': {
                metric: value * improvement_factor
                for metric, value in current_metrics.items()
            }
        }

    def _predict_peak_age(self, player_data: pd.DataFrame) -> float:
        """Predict player's peak performance age"""
        # Base peak age on position and current trajectory
        base_peak_age = 27  # Default peak age
        
        # Adjust based on current performance trajectory
        current_metrics = self._calculate_current_metrics(player_data)
        performance_level = current_metrics['goals_per_game'] + current_metrics['assists_per_game']
        
        # Early bloomer (high performance at young age) might peak earlier
        age = player_data['Age'].iloc[0]
        if age < 23 and performance_level > 0.5:
            base_peak_age -= 1
        
        return base_peak_age

    def _calculate_development_potential(self, player_data: pd.DataFrame) -> float:
        """Calculate player's development potential (0-1 scale)"""
        age = player_data['Age'].iloc[0]
        current_metrics = self._calculate_current_metrics(player_data)
        
        # Base potential on age (younger = more potential)
        age_factor = max(0, 1 - (age - 17) / 15)  # Decreases with age
        
        # Current performance level
        performance_level = min(1, (current_metrics['goals_per_game'] + 
                                  current_metrics['assists_per_game']) / 1.5)
        
        # Combine factors (weight age more heavily for young players)
        potential = (age_factor * 0.7) + (performance_level * 0.3)
        return min(1, max(0, potential))

    def _project_value_progression(self, player_data: pd.DataFrame) -> Dict:
        """Project player value progression"""
        current_value = player_data['Current_Value'].iloc[0]
        peak_value = player_data['Peak_Value'].iloc[0]
        age = player_data['Age'].iloc[0]
        peak_age = self._predict_peak_age(player_data)
        
        # Calculate value projections
        years_to_peak = max(0, peak_age - age)
        annual_growth_rate = (peak_value / current_value) ** (1 / max(1, years_to_peak)) if years_to_peak > 0 else 1
        
        value_projection = {
            'current_value': current_value,
            'peak_value': peak_value,
            'years_to_peak_value': years_to_peak,
            'annual_growth_rate': annual_growth_rate - 1,  # Convert to percentage
            'projected_values': {}
        }
        
        # Project values for next 5 years
        for year in range(5):
            projected_year = age + year
            if projected_year < peak_age:
                # Growing phase
                value_projection['projected_values'][projected_year] = current_value * (annual_growth_rate ** year)
            else:
                # Decline phase (15% annual decline after peak)
                years_past_peak = projected_year - peak_age
                value_projection['projected_values'][projected_year] = peak_value * (0.85 ** years_past_peak)
        
        return value_projection