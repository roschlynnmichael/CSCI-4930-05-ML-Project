import pandas as pd
import numpy as np
from typing import Dict, List
import logging
from pathlib import Path

class TeamBalanceOptimizer:
    def __init__(self):
        self._setup_logging()
        
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

    def analyze_squad_balance(self, team_data: pd.DataFrame) -> Dict:
        """Main function to analyze squad balance"""
        try:
            # Prepare the data
            analysis_data = pd.DataFrame()
            
            # Extract name and age from scraped data
            analysis_data['Name'] = team_data.apply(lambda x: x.get('name', 'Unknown'), axis=1)
            analysis_data['Age'] = team_data.apply(lambda x: self._extract_age(x.get('Date of birth/Age', x.get('age', ''))), axis=1)
            
            # Determine career phase based on age
            analysis_data['Career_Phase'] = analysis_data['Age'].apply(self._determine_career_phase)
            
            # Calculate metrics
            squad_metrics = self._analyze_squad_metrics(analysis_data)
            age_analysis = self._analyze_age_distribution(analysis_data)
            phase_analysis = self._analyze_phase_distribution(analysis_data)
            balance_scores = self._calculate_balance_scores(analysis_data)
            
            # Generate recommendations
            recommendations = self._generate_recommendations({
                'squad_metrics': squad_metrics,
                'age_analysis': age_analysis,
                'phase_analysis': phase_analysis,
                'balance_scores': balance_scores
            })
            
            return {
                'squad_metrics': squad_metrics,
                'age_analysis': age_analysis,
                'phase_analysis': phase_analysis,
                'balance_scores': balance_scores,
                'recommendations': recommendations
            }
            
        except Exception as e:
            self.logger.error(f"Error in squad balance analysis: {str(e)}")
            raise

    def _analyze_squad_metrics(self, data: pd.DataFrame) -> Dict:
        """Calculate basic squad metrics"""
        total_players = len(data)
        average_age = data['Age'].mean()
        
        return {
            'total_players': total_players,
            'average_age': round(average_age, 1),
            'squad_size_status': self._evaluate_squad_size(total_players)
        }

    def _analyze_age_distribution(self, data: pd.DataFrame) -> Dict:
        """Analyze age distribution of the squad"""
        age_groups = {
            'u21': len(data[data['Age'] < 21]) / len(data),
            '21_25': len(data[(data['Age'] >= 21) & (data['Age'] <= 25)]) / len(data),
            '26_29': len(data[(data['Age'] >= 26) & (data['Age'] <= 29)]) / len(data),
            '30_plus': len(data[data['Age'] >= 30]) / len(data)
        }
        
        # Calculate balance score
        balance_score = self._calculate_distribution_score(
            age_groups, 
            self.ideal_composition['age_distribution']
        )
        
        # Calculate gaps
        gaps = {k: self.ideal_composition['age_distribution'][k] - v 
               for k, v in age_groups.items()}
        
        return {
            'current': age_groups,
            'ideal': self.ideal_composition['age_distribution'],
            'balance_score': balance_score,
            'gaps': gaps
        }

    def _analyze_phase_distribution(self, data: pd.DataFrame) -> Dict:
        """Analyze career phase distribution"""
        phase_counts = data['Career_Phase'].value_counts()
        total = len(data)
        
        phase_distribution = {
            'breakthrough': len(data[data['Career_Phase'] == 'breakthrough']) / total,
            'development': len(data[data['Career_Phase'] == 'development']) / total,
            'peak': len(data[data['Career_Phase'] == 'peak']) / total,
            'twilight': len(data[data['Career_Phase'] == 'twilight']) / total
        }
        
        balance_score = self._calculate_distribution_score(
            phase_distribution,
            self.ideal_composition['phase_distribution']
        )
        
        gaps = {k: self.ideal_composition['phase_distribution'][k] - v 
               for k, v in phase_distribution.items()}
        
        return {
            'current': phase_distribution,
            'ideal': self.ideal_composition['phase_distribution'],
            'balance_score': balance_score,
            'gaps': gaps
        }

    def _determine_career_phase(self, age: int) -> str:
        """Determine player's career phase based on age"""
        if age < 21:
            return 'breakthrough'
        elif age <= 24:
            return 'development'
        elif age <= 29:
            return 'peak'
        else:
            return 'twilight'

    def _calculate_balance_scores(self, data: pd.DataFrame) -> Dict:
        """Calculate overall balance scores"""
        age_analysis = self._analyze_age_distribution(data)
        phase_analysis = self._analyze_phase_distribution(data)
        
        return {
            'age_balance': age_analysis['balance_score'],
            'phase_balance': phase_analysis['balance_score'],
            'overall_balance': (age_analysis['balance_score'] + phase_analysis['balance_score']) / 2
        }

    def _calculate_distribution_score(self, current: Dict, ideal: Dict) -> float:
        """Calculate how well current distribution matches ideal"""
        differences = [abs(ideal[k] - current.get(k, 0)) for k in ideal]
        return 1 - sum(differences) / 2  # Convert to 0-1 score

    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate specific recommendations based on analysis"""
        recommendations = []
        
        # Squad size recommendations
        squad_size = analysis['squad_metrics']['total_players']
        if squad_size < self.ideal_composition['squad_size']['min']:
            recommendations.append(f"Need {self.ideal_composition['squad_size']['min'] - squad_size} more players")
        elif squad_size > self.ideal_composition['squad_size']['max']:
            recommendations.append(f"Squad too large by {squad_size - self.ideal_composition['squad_size']['max']} players")
        
        # Age balance recommendations
        for age_group, gap in analysis['age_analysis']['gaps'].items():
            if abs(gap) > 0.1:  # 10% threshold
                if gap > 0:
                    recommendations.append(f"Need more {age_group.replace('_', '-')} players (+{gap:.0%})")
                else:
                    recommendations.append(f"Reduce {age_group.replace('_', '-')} players ({gap:.0%})")
        
        return recommendations

    def _setup_logging(self):
        log_dir = Path('logs')
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            filename=log_dir / 'team_balance.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _extract_age(self, age_string: str) -> int:
        """Extract age from various string formats"""
        try:
            if not age_string:
                return 0
            
            # Handle "(age)" format
            if '(' in str(age_string):
                age = age_string.split('(')[1].replace(')', '')
                return int(age)
            
            # Handle direct number
            if str(age_string).isdigit():
                return int(age_string)
            
            return 0
        except Exception as e:
            self.logger.error(f"Error extracting age from {age_string}: {str(e)}")
            return 0

    def _evaluate_squad_size(self, total_players: int) -> str:
        """Evaluate if squad size is optimal"""
        if total_players < self.ideal_composition['squad_size']['min']:
            return 'understaffed'
        elif total_players > self.ideal_composition['squad_size']['max']:
            return 'overstaffed'
        elif total_players == self.ideal_composition['squad_size']['optimal']:
            return 'optimal'
        else:
            return 'acceptable'
