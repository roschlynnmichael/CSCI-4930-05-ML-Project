import pandas as pd
import numpy as np
from typing import Dict, List
import logging
from pathlib import Path
from .roster_analyzer import RosterAnalyzer

class TeamBalanceOptimizer:
    def __init__(self):
        self._setup_logging()
        self.roster_analyzer = RosterAnalyzer()
        
        # Define ideal team composition
        self.ideal_composition = {
            'squad_size': {
                'min': 20,
                'max': 28,
                'optimal': 24
            },
            'age_distribution': {
                'u21': 0.15,    # 15% under 21
                '21_25': 0.30,  # 30% development age
                '26_29': 0.35,  # 35% peak age
                '30_plus': 0.20 # 20% experienced
            },
            'phase_distribution': {
                'breakthrough': 0.20,
                'development': 0.30,
                'peak': 0.35,
                'twilight': 0.15
            }
        }

    def _setup_logging(self):
        log_dir = Path('app/logs')
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            filename=log_dir / 'team_balance.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def analyze_squad_balance(self, team_data: pd.DataFrame) -> Dict:
        """
        Main function to analyze squad balance
        """
        try:
            # Get career phase predictions using ML model
            ml_analysis = self.roster_analyzer.analyze_team(team_data)
            
            # Combine original data with ML predictions
            analysis_data = team_data.copy()
            
            # Convert ml_analysis to DataFrame if it's not already
            if isinstance(ml_analysis, dict):
                ml_analysis = pd.DataFrame(ml_analysis)
                
            # Ensure Career_Phase is properly assigned
            analysis_data['Career_Phase'] = ml_analysis['Career_Phase']
            
            # Validate and adjust phase predictions based on age
            analysis_data['Career_Phase'] = analysis_data.apply(
                lambda row: self._validate_career_phase(row['Age'], row['Career_Phase']), 
                axis=1
            )
            
            # Perform comprehensive analysis
            balance_analysis = {
                'squad_metrics': self._analyze_squad_metrics(analysis_data),
                'age_analysis': self._analyze_age_distribution(analysis_data),
                'phase_analysis': self._analyze_phase_distribution(analysis_data),
                'balance_scores': self._calculate_balance_scores(analysis_data),
            }
            
            # Generate recommendations
            balance_analysis['recommendations'] = self._generate_recommendations(balance_analysis)
            
            return balance_analysis
                
        except Exception as e:
            self.logger.error(f"Error in squad balance analysis: {str(e)}")
            raise

    def _validate_career_phase(self, age: float, predicted_phase: str) -> str:
        """Validate and adjust career phase based on age"""
        age_phase_mapping = {
            (17, 20): 'breakthrough',
            (21, 24): 'development',
            (25, 29): 'peak',
            (30, 40): 'twilight'
        }
        
        # Find expected phase based on age
        expected_phase = None
        for (min_age, max_age), phase in age_phase_mapping.items():
            if min_age <= age <= max_age:
                expected_phase = phase
                break
        
        # If prediction differs significantly from age expectation, use age-based phase
        if predicted_phase != expected_phase:
            self.logger.warning(
                f"Adjusting phase for player age {age}: {predicted_phase} -> {expected_phase}"
            )
            return expected_phase
        
        return predicted_phase

    def _analyze_squad_metrics(self, data: pd.DataFrame) -> Dict:
        """Analyze basic squad metrics"""
        return {
            'total_players': len(data),
            'average_age': round(data['Age'].mean(), 2),
            'age_spread': round(data['Age'].std(), 2),
            'squad_size_status': self._evaluate_squad_size(len(data))
        }

    def _analyze_age_distribution(self, data: pd.DataFrame) -> Dict:
        """Analyze age group distribution"""
        total_players = len(data)
        current_dist = {
            'u21': len(data[data['Age'] < 21]) / total_players,
            '21_25': len(data[(data['Age'] >= 21) & (data['Age'] < 26)]) / total_players,
            '26_29': len(data[(data['Age'] >= 26) & (data['Age'] < 30)]) / total_players,
            '30_plus': len(data[data['Age'] >= 30]) / total_players
        }
        
        gaps = {
            group: self.ideal_composition['age_distribution'][group] - current_dist[group]
            for group in current_dist
        }
        
        return {
            'current': current_dist,
            'gaps': gaps,
            'balance_score': self._calculate_distribution_score(current_dist, 
                                                             self.ideal_composition['age_distribution'])
        }

    def _analyze_phase_distribution(self, data: pd.DataFrame) -> Dict:
        """Analyze career phase distribution"""
        current_dist = data['Career_Phase'].value_counts(normalize=True).to_dict()
        
        # Ensure all phases are represented
        for phase in self.ideal_composition['phase_distribution']:
            if phase not in current_dist:
                current_dist[phase] = 0.0
        
        gaps = {
            phase: self.ideal_composition['phase_distribution'][phase] - current_dist.get(phase, 0)
            for phase in self.ideal_composition['phase_distribution']
        }
        
        return {
            'current': current_dist,
            'gaps': gaps,
            'balance_score': self._calculate_distribution_score(current_dist, 
                                                             self.ideal_composition['phase_distribution'])
        }

    def _calculate_balance_scores(self, data: pd.DataFrame) -> Dict:
        """Calculate overall balance scores"""
        return {
            'age_balance': self._analyze_age_distribution(data)['balance_score'],
            'phase_balance': self._analyze_phase_distribution(data)['balance_score'],
            'overall_balance': (self._analyze_age_distribution(data)['balance_score'] + 
                              self._analyze_phase_distribution(data)['balance_score']) / 2
        }

    def _calculate_distribution_score(self, current: Dict, ideal: Dict) -> float:
        """Calculate how well current distribution matches ideal"""
        differences = [abs(ideal[k] - current.get(k, 0)) for k in ideal]
        return 1 - sum(differences) / 2  # Convert to 0-1 score

    def _evaluate_squad_size(self, size: int) -> str:
        """Evaluate if squad size is optimal"""
        if size < self.ideal_composition['squad_size']['min']:
            return f"Squad too small (need {self.ideal_composition['squad_size']['min'] - size} more players)"
        elif size > self.ideal_composition['squad_size']['max']:
            return f"Squad too large (reduce by {size - self.ideal_composition['squad_size']['max']} players)"
        return "Optimal squad size"

    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate specific recommendations based on analysis"""
        recommendations = []
        
        # Squad size recommendations
        if analysis['squad_metrics']['squad_size_status'] != "Optimal squad size":
            recommendations.append(analysis['squad_metrics']['squad_size_status'])
        
        # Age balance recommendations
        for age_group, gap in analysis['age_analysis']['gaps'].items():
            if abs(gap) > 0.1:  # 10% threshold
                if gap > 0:
                    recommendations.append(f"Need more {age_group} players (deficit: {gap:.1%})")
                else:
                    recommendations.append(f"Reduce {age_group} players (excess: {-gap:.1%})")
        
        # Phase balance recommendations
        for phase, gap in analysis['phase_analysis']['gaps'].items():
            if abs(gap) > 0.1:  # 10% threshold
                if gap > 0:
                    recommendations.append(f"Need more {phase} phase players (deficit: {gap:.1%})")
                else:
                    recommendations.append(f"Reduce {phase} phase players (excess: {-gap:.1%})")
        
        return recommendations
    def get_priority_requirements(self, analysis_results: Dict) -> List[Dict]:
        """Get prioritized list of team requirements"""
        priorities = []
        gaps = analysis_results['balance_gaps']
        
        # Combine and prioritize gaps
        for category in ['age_groups', 'career_phases']:
            for group, gap in gaps[category].items():
                if abs(gap) > 0.1:  # 10% threshold
                    priorities.append({
                        'category': category,
                        'group': group,
                        'gap': gap,
                        'priority': 'High' if abs(gap) > 0.2 else 'Medium'
                    })
        
        # Sort by absolute gap size
        priorities.sort(key=lambda x: abs(x['gap']), reverse=True)
        return priorities
