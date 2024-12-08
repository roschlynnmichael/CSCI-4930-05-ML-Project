import pandas as pd
import numpy as np
from typing import Dict, List
import logging
from pathlib import Path
import json
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class RecommendationEngine:
    def __init__(self):
        self._setup_logging()
        self.scaler = StandardScaler()
        self.data_file = Path("app/data/players.json")
        
        # Define career phases
        self.career_phases = {
            'breakthrough': (16, 20),
            'development': (21, 24),
            'peak': (25, 29),
            'twilight': (30, 40)
        }
        
        # Ideal distribution percentages
        self.ideal_distribution = {
            'breakthrough': 15,  # 15% of squad
            'development': 30,   # 30% of squad
            'peak': 40,         # 40% of squad
            'twilight': 15      # 15% of squad
        }
        
        # Features for similarity calculation
        self.similarity_features = [
            'age', 'market_value', 'appearances', 'goals', 
            'assists', 'minutes_played'
        ]

    def _setup_logging(self):
        """Setup logging for recommendation engine"""
        log_dir = Path('app/logs')
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            filename=log_dir / 'recommendation_engine.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def load_player_data(self) -> Dict:
        """Load player data from JSON file"""
        try:
            if not self.data_file.exists():
                logger.error("Player data file not found")
                return {}
                
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading player data: {str(e)}")
            return {}

    def get_recommendations(self, squad_player_ids: List[str], num_recommendations: int = 3) -> Dict:
        """Get player recommendations based on squad needs"""
        try:
            # Load all player data
            all_player_data = self.load_player_data()
            if not all_player_data:
                return {"error": "No player data available"}

            # Split data into squad and available players
            squad_data = [all_player_data[pid] for pid in squad_player_ids if pid in all_player_data]
            available_players = [
                player for pid, player in all_player_data.items() 
                if pid not in squad_player_ids
            ]

            # Convert data to DataFrames
            squad_df = self._convert_to_dataframe(squad_data)
            available_df = self._convert_to_dataframe(available_players)
            
            # Analyze squad demographics
            demographics = self._analyze_squad_demographics(squad_df)
            
            # Identify squad needs
            needs = self._identify_squad_needs(demographics)
            
            # Get recommendations for each need
            recommendations = {}
            for phase in needs:
                candidates = self._get_candidates(
                    squad_df,
                    available_df,
                    phase,
                    num_recommendations
                )
                recommendations[phase] = self._rank_candidates(candidates, phase)
            
            return {
                'squad_analysis': demographics,
                'identified_needs': needs,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return {"error": str(e)}

    def _convert_to_dataframe(self, player_data: List[Dict]) -> pd.DataFrame:
        """Convert player data to DataFrame format"""
        processed_data = []
        
        for player in player_data:
            try:
                # Extract basic info
                player_info = {
                    'id': player.get('id'),
                    'name': player.get('Full name', 'Unknown'),
                    'age': self._extract_age(player),
                    'position': player.get('Position', ''),
                    'market_value': self._extract_market_value(player.get('Market value', '0')),
                }
                
                # Extract career stats
                career_stats = self._aggregate_career_stats(player.get('careerStats', []))
                player_info.update(career_stats)
                
                processed_data.append(player_info)
                
            except Exception as e:
                logger.error(f"Error processing player data: {str(e)}")
                continue
                
        return pd.DataFrame(processed_data)

    def _extract_age(self, player: Dict) -> int:
        """Extract age from player data"""
        try:
            if 'Date of birth/Age' in player:
                age_str = player['Date of birth/Age']
                if '(' in age_str and ')' in age_str:
                    return int(age_str.split('(')[1].split(')')[0])
            return 0
        except:
            return 0

    def _extract_market_value(self, value_str: str) -> float:
        """Extract market value as float"""
        try:
            value_str = value_str.replace('€', '').strip().lower()
            if 'm' in value_str:
                return float(value_str.replace('m', '')) * 1_000_000
            elif 'k' in value_str:
                return float(value_str.replace('k', '')) * 1_000
            return 0.0
        except:
            return 0.0

    def _aggregate_career_stats(self, career_stats: List[Dict]) -> Dict:
        """Aggregate career statistics"""
        total_stats = {
            'appearances': 0,
            'goals': 0,
            'assists': 0,
            'minutes_played': 0
        }
        
        for season in career_stats:
            try:
                total_stats['appearances'] += int(season.get('Appearances', '0').replace(',', ''))
                total_stats['goals'] += int(season.get('Goals', '0').replace(',', ''))
                total_stats['assists'] += int(season.get('Assists', '0').replace(',', ''))
                total_stats['minutes_played'] += int(season.get('Minutes', '0').replace(',', ''))
            except ValueError:
                continue
                
        return total_stats

    def _analyze_squad_demographics(self, squad_df: pd.DataFrame) -> Dict:
        """Analyze the age distribution of the squad"""
        demographics = {phase: [] for phase in self.career_phases.keys()}
        
        for _, player in squad_df.iterrows():
            age = player.get('age', 0)
            for phase, (min_age, max_age) in self.career_phases.items():
                if min_age <= age <= max_age:
                    demographics[phase].append({
                        'id': player.get('id'),
                        'name': player.get('name'),
                        'age': age,
                        'position': player.get('position')
                    })
                    break
        
        # Calculate phase distributions
        total_players = len(squad_df)
        distribution = {
            phase: {
                'count': len(players),
                'percentage': (len(players) / total_players * 100) if total_players > 0 else 0,
                'players': players
            }
            for phase, players in demographics.items()
        }
        
        return distribution

    def _identify_squad_needs(self, demographics: Dict) -> List[str]:
        """Identify which career phases need strengthening"""
        needs = []
        
        for phase, ideal_pct in self.ideal_distribution.items():
            current_pct = demographics[phase]['percentage']
            if current_pct < ideal_pct - 5:  # 5% tolerance
                needs.append(phase)
                
        return needs

    def _get_candidates(self, 
                       squad_df: pd.DataFrame, 
                       available_df: pd.DataFrame,
                       target_phase: str,
                       num_recommendations: int) -> pd.DataFrame:
        """Get candidate players for a specific career phase"""
        try:
            # Filter by age range
            min_age, max_age = self.career_phases[target_phase]
            candidates = available_df[
                (available_df['age'] >= min_age) & 
                (available_df['age'] <= max_age)
            ].copy()
            
            if candidates.empty:
                return pd.DataFrame()
            
            # Calculate similarity scores
            squad_features = squad_df[self.similarity_features]
            candidate_features = candidates[self.similarity_features]
            
            # Handle missing or invalid values
            squad_features = squad_features.fillna(0)
            candidate_features = candidate_features.fillna(0)
            
            # Scale features
            scaler = StandardScaler()
            scaled_features = scaler.fit_transform(
                pd.concat([squad_features, candidate_features])
            )
            
            # Calculate similarity
            squad_scaled = scaled_features[:len(squad_features)]
            candidates_scaled = scaled_features[len(squad_features):]
            
            # Calculate cosine similarity and normalize to [0,1] range
            similarities = cosine_similarity(candidates_scaled, squad_scaled)
            # Convert from [-1,1] to [0,1] range
            similarities = (similarities + 1) / 2
            
            candidates['similarity_score'] = similarities.mean(axis=1)
            
            return candidates.nlargest(num_recommendations, 'similarity_score')
            
        except Exception as e:
            logger.error(f"Error getting candidates: {str(e)}")
            return pd.DataFrame()

    def _rank_candidates(self, candidates: pd.DataFrame, target_phase: str) -> List[Dict]:
        """Format and rank candidate recommendations"""
        recommendations = []
        
        for _, player in candidates.iterrows():
            try:
                recommendations.append({
                    'id': player.get('id'),
                    'name': player.get('name'),
                    'age': player.get('age'),
                    'position': player.get('position', ''),
                    'market_value': player.get('market_value', 0),
                    'similarity_score': float(player.get('similarity_score', 0)),
                    'career_phase': target_phase,
                    'stats': {
                        'appearances': player.get('appearances', 0),
                        'goals': player.get('goals', 0),
                        'assists': player.get('assists', 0),
                        'minutes_played': player.get('minutes_played', 0)
                    }
                })
            except Exception as e:
                logger.error(f"Error formatting recommendation: {str(e)}")
                continue
        
        return sorted(recommendations, key=lambda x: x['similarity_score'], reverse=True)
