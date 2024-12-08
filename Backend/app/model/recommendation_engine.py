import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
from pathlib import Path
from sklearn.preprocessing import StandardScaler
import json

logger = logging.getLogger(__name__)

class RecommendationEngine:
    def __init__(self):
        """Initialize the recommendation engine"""
        self._setup_logging()
        self.scaler = StandardScaler()
        
        # Define career phases and ideal distributions
        self.career_phases = {
            'breakthrough': {'age_range': (17, 20), 'ideal_pct': 0.20},
            'development': {'age_range': (21, 24), 'ideal_pct': 0.30},
            'peak': {'age_range': (25, 29), 'ideal_pct': 0.35},
            'twilight': {'age_range': (30, 40), 'ideal_pct': 0.15}
        }
        
        # Age distribution targets
        self.age_distribution = {
            'u21': {'ideal_pct': 0.15},
            '21_25': {'ideal_pct': 0.35},
            '26_29': {'ideal_pct': 0.35},
            '30_plus': {'ideal_pct': 0.15}
        }

    def _setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path('app/logs')
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            filename=log_dir / 'recommendation_engine.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def load_player_data(self) -> Dict:
        """Load player data from player service cache"""
        try:
            from app.data.player_service import PlayerService
            player_service = PlayerService()
            data = player_service.get_all_players()
            logger.info(f"Loaded {len(data)} players from cache")
            return data
        except Exception as e:
            logger.error(f"Error loading player data: {str(e)}")
            return {}

    def get_recommendations(self, squad_ids: List[str]) -> Dict:
        """Get recommendations based on squad analysis"""
        try:
            # Load data and validate squad
            all_players = self.load_player_data()
            squad_players = [all_players.get(id) for id in squad_ids if id in all_players]
            
            if not squad_players:
                logger.warning("No valid squad players found")
                return self._empty_response()

            # Calculate current distributions
            current_age_dist = self._calculate_age_distribution(squad_players)
            current_phase_dist = self._calculate_phase_distribution(squad_players)
            
            # Identify needs
            needs = self._identify_needs(current_phase_dist)
            
            # Get recommendations
            recommendations = {}
            for phase in needs:
                candidates = self._get_phase_candidates(all_players, squad_ids, phase)
                recommendations[phase] = candidates[:3]  # Top 3 recommendations per phase

            return {
                "squad_analysis": {
                    "age_analysis": {
                        "current": current_age_dist,
                        "ideal": {k: v['ideal_pct'] for k, v in self.age_distribution.items()}
                    },
                    "phase_analysis": {
                        "current": current_phase_dist,
                        "ideal": {k: v['ideal_pct'] for k, v in self.career_phases.items()}
                    }
                },
                "identified_needs": needs,
                "recommendations": recommendations
            }

        except Exception as e:
            logger.error(f"Error in get_recommendations: {str(e)}")
            return self._empty_response()

    def _calculate_age_distribution(self, squad_players: List[Dict]) -> Dict[str, float]:
        """Calculate age distribution percentages"""
        try:
            total_players = len(squad_players)
            if total_players == 0:
                return {k: 0.0 for k in self.age_distribution.keys()}

            # Initialize counters for each age group
            age_counts = {
                'u21': 0,
                '21_25': 0,
                '26_29': 0,
                '30_plus': 0
            }

            # Count players in each age group
            for player in squad_players:
                age = self._extract_age(player.get('Date of birth/Age', '0'))
                if age < 21:
                    age_counts['u21'] += 1
                elif 21 <= age <= 25:
                    age_counts['21_25'] += 1
                elif 26 <= age <= 29:
                    age_counts['26_29'] += 1
                else:  # age >= 30
                    age_counts['30_plus'] += 1

            # Calculate percentages
            distribution = {
                group: count / total_players 
                for group, count in age_counts.items()
            }

            logger.info(f"Age distribution calculated: {distribution}")
            return distribution

        except Exception as e:
            logger.error(f"Error calculating age distribution: {str(e)}")
            return {k: 0.0 for k in self.age_distribution.keys()}

    def _calculate_phase_distribution(self, players: List[Dict]) -> Dict[str, float]:
        """Calculate current phase distribution"""
        total = len(players)
        if not total:
            return {k: 0.0 for k in self.career_phases.keys()}
            
        distribution = {phase: 0 for phase in self.career_phases}
        
        for player in players:
            age = self._extract_age(player['Date of birth/Age'])
            phase = self._get_player_phase(age)
            if phase:
                distribution[phase] += 1
                
        return {k: v/total for k, v in distribution.items()}

    def _identify_needs(self, current_dist: Dict[str, float]) -> List[str]:
        """Identify phases that need strengthening"""
        needs = []
        for phase, data in self.career_phases.items():
            if current_dist[phase] < data['ideal_pct'] - 0.1:  # 10% threshold
                needs.append(phase)
        return needs

    def _get_phase_candidates(self, all_players: Dict, squad_ids: List[str], target_phase: str) -> List[Dict]:
        """Get candidate players for a specific phase"""
        try:
            candidates = []
            min_age, max_age = self.career_phases[target_phase]['age_range']
        
            for pid, player in all_players.items():
                if pid not in squad_ids:  # Don't recommend players already in squad
                    try:
                        age = self._extract_age(player.get('Date of birth/Age', '0'))
                        if min_age <= age <= max_age:
                            similarity_score = self._calculate_similarity(player)
                            candidates.append({
                                'id': pid,
                                'Full_name': player.get('Full name', 'Unknown'),
                                'Position': player.get('Position', 'Unknown'),
                                'Date of birth/Age': player.get('Date of birth/Age', 'Unknown'),
                                'Market value': player.get('Market value', 'N/A'),
                                'image_url': player.get('image_url', ''),
                                'similarity_score': similarity_score
                            })
                    except Exception as e:
                        logger.error(f"Error processing player {pid}: {str(e)}")
                        continue
        
        # Sort by similarity score and return top candidates
            sorted_candidates = sorted(candidates, key=lambda x: x['similarity_score'], reverse=True)
            return sorted_candidates[:5]  # Return top 5 candidates per phase
        
        except Exception as e:
            logger.error(f"Error in _get_phase_candidates: {str(e)}")
            return []

    def _extract_age(self, age_string: str) -> int:
        """Extract age from string format like '1995-01-01 (28)'"""
        try:
            # Extract age from parentheses
            age = int(age_string.split('(')[1].replace(')', ''))
            return age
        except Exception as e:
            logger.error(f"Error extracting age from {age_string}: {str(e)}")
            return 0

    def _get_player_phase(self, age: int) -> Optional[str]:
        """Determine player's career phase based on age"""
        for phase, data in self.career_phases.items():
            min_age, max_age = data['age_range']
            if min_age <= age <= max_age:
                return phase
        return None

    def _calculate_similarity(self, player: Dict) -> float:
        """Calculate similarity score based on player stats"""
        try:
            # Extract career stats
            stats = player.get('careerStats', [{}])[0]
        
            # Get base stats with defaults
            appearances = float(stats.get('Appearances', 0))
            minutes = float(stats.get('Minutes played', 0))
            goals = float(stats.get('Goals', 0))
            assists = float(stats.get('Assists', 0))
            
            # Calculate normalized scores
            appearance_score = min(1.0, appearances / 38)  # Full season
            minutes_score = min(1.0, minutes / 3420)  # 90 mins * 38 games
            goals_score = min(1.0, goals / 20)  # Assuming 20 goals is excellent
            assists_score = min(1.0, assists / 15)  # Assuming 15 assists is excellent
            
            # Weighted average
            total_score = (
                appearance_score * 0.3 +
                minutes_score * 0.3 +
                goals_score * 0.2 +
                assists_score * 0.2
            )
        
            # Ensure score is between 0.6 and 0.95
            return max(0.6, min(0.95, total_score))
        
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            return 0.6

    def _empty_response(self) -> Dict:
        """Return empty response structure"""
        return {
            "squad_analysis": {
                "age_analysis": {
                    "current": {k: 0.0 for k in self.age_distribution.keys()},
                    "ideal": {k: v['ideal_pct'] for k, v in self.age_distribution.items()}
                },
                "phase_analysis": {
                    "current": {k: 0.0 for k in self.career_phases.keys()},
                    "ideal": {k: v['ideal_pct'] for k, v in self.career_phases.items()}
                }
            },
            "identified_needs": [],
            "recommendations": {}
        }