import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging
from pathlib import Path
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from .team_balance import TeamBalanceOptimizer
from .performance_predictor import PerformancePredictor
from .roster_analyzer import RosterAnalyzer

class RecommendationEngine:
    def __init__(self):
        self._setup_logging()
        self.team_balance = TeamBalanceOptimizer()
        self.performance_predictor = PerformancePredictor()
        self.roster_analyzer = RosterAnalyzer()
        self.scaler = StandardScaler()
        
        # We don't need to load the model directly as we're using RosterAnalyzer
        # which already has the model loaded
        
        # Features for similarity and prediction
        self.similarity_features = [
            'Age', 'Career_Games', 'Career_Goals', 'Career_Assists',
            'Career_Minutes', 'Current_Value', 'Peak_Value'
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
        self.logger = logging.getLogger(__name__)

    def get_recommendations(self, 
                          team_data: pd.DataFrame, 
                          available_players: pd.DataFrame,
                          num_recommendations: int = 5) -> Dict:
        """Get player recommendations based on team needs and similar profiles"""
        try:
            # Get career phase predictions using RosterAnalyzer
            team_phases = self.roster_analyzer.analyze_team(team_data)
            available_phases = self.roster_analyzer.analyze_team(available_players)
            
            # Add predicted phases to dataframes
            team_data['Predicted_Phase'] = team_phases['Career_Phase']
            available_players['Predicted_Phase'] = available_phases['Career_Phase']
            
            # Analyze team balance
            balance_analysis = self.team_balance.analyze_squad_balance(team_data)
            
            # Get team requirements
            requirements = self._analyze_team_requirements(balance_analysis)
            
            # Filter available players based on requirements
            filtered_players = self._filter_candidates(available_players, requirements)
            
            # Get recommendations for each requirement
            recommendations = {}
            for req_type, req_details in requirements.items():
                candidates = self._get_candidates(
                    team_data,
                    filtered_players,
                    req_details,
                    num_recommendations
                )
                recommendations[req_type] = self._rank_candidates(candidates, req_details)
            
            return {
                'requirements': requirements,
                'recommendations': recommendations
            }
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {str(e)}")
            raise

    def _predict_career_phases(self, players: pd.DataFrame) -> pd.Series:
        """Use gradient boosting model to predict career phases"""
        try:
            # Prepare features for prediction
            features = players[self.similarity_features].copy()
            
            # Make predictions using the model
            predictions = self.model.predict(features)
            
            return pd.Series(predictions, index=players.index)
            
        except Exception as e:
            self.logger.error(f"Error predicting career phases: {str(e)}")
            raise

    def _get_candidates(self, 
                       team_data: pd.DataFrame, 
                       available_players: pd.DataFrame,
                       requirement: Dict,
                       num_recommendations: int) -> pd.DataFrame:
        """Get candidate players based on similarity and career phase predictions"""
        try:
            print(f"\nGetting candidates for {requirement['type']}...")
            
            if available_players.empty:
                return pd.DataFrame()
            
            # Prepare data for similarity calculation
            team_features = team_data[self.similarity_features]
            candidate_features = available_players[self.similarity_features]
            
            print(f"Team features shape: {team_features.shape}")
            print(f"Candidate features shape: {candidate_features.shape}")
            
            # Scale features
            scaled_features = self.scaler.fit_transform(
                pd.concat([team_features, candidate_features])
            )
            
            # Calculate similarity
            team_scaled = scaled_features[:len(team_features)]
            candidates_scaled = scaled_features[len(team_features):]
            
            similarities = cosine_similarity(candidates_scaled, team_scaled)
            
            # Get average similarity for each candidate
            avg_similarities = similarities.mean(axis=1)
            
            # Add similarity scores to candidates
            candidates = available_players.copy()
            candidates['similarity_score'] = avg_similarities
            
            # Sort by similarity and return top candidates
            return candidates.nlargest(num_recommendations, 'similarity_score')
            
        except Exception as e:
            self.logger.error(f"Error getting candidates: {str(e)}")
            raise

    def _analyze_team_requirements(self, balance_analysis: Dict) -> Dict:
        """Analyze team requirements based on balance analysis"""
        requirements = {}
        
        # Get total players
        total_players = balance_analysis['squad_metrics']['total_players']
        
        print(f"\nAnalyzing requirements for {total_players} players...")
        print("Balance analysis:", balance_analysis)
        
        # Squad size requirements
        squad_status = balance_analysis['squad_metrics']['squad_size_status']
        if 'need' in squad_status.lower():
            requirements['squad_size'] = {
                'type': 'squad_size',
                'priority': 'high',
                'details': squad_status
            }
        
        # Age group requirements
        for age_group, gap in balance_analysis['age_analysis']['gaps'].items():
            if gap > 0.05:  # Need more players in this age group (5% threshold)
                requirements[f'age_{age_group}'] = {
                    'type': 'age_group',
                    'group': age_group,
                    'priority': 'high' if gap > 0.15 else 'medium',
                    'gap': gap,
                    'required_count': int(np.ceil(gap * total_players))
                }
                print(f"Added requirement for {age_group}: gap={gap}, count={int(np.ceil(gap * total_players))}")
        
        # Phase requirements
        for phase, gap in balance_analysis['phase_analysis']['gaps'].items():
            if gap > 0.05:  # Need more players in this phase (5% threshold)
                requirements[f'phase_{phase}'] = {
                    'type': 'career_phase',
                    'phase': phase,
                    'priority': 'high' if gap > 0.15 else 'medium',
                    'gap': gap,
                    'required_count': int(np.ceil(gap * total_players))
                }
                print(f"Added requirement for {phase}: gap={gap}, count={int(np.ceil(gap * total_players))}")
        
        print(f"Found {len(requirements)} requirements")
        return requirements

    def _filter_candidates(self, players: pd.DataFrame, requirements: Dict) -> pd.DataFrame:
        """Filter candidate players based on requirements"""
        if not requirements:  # If no requirements, return all players
            return players
        
        filtered = players.copy()
        
        # Debug print
        print(f"\nFiltering {len(filtered)} candidates...")
        print("Requirements:", requirements)
        
        # Create separate masks for each requirement type
        age_masks = []
        phase_masks = []
        
        for req_type, req_details in requirements.items():
            if req_details['type'] == 'age_group':
                age_mask = self._get_age_group_mask(filtered, req_details['group'])
                age_masks.append(age_mask)
                print(f"Age group {req_details['group']}: {age_mask.sum()} matches")
                
            elif req_details['type'] == 'career_phase':
                phase_mask = filtered['Predicted_Phase'] == req_details['phase']
                phase_masks.append(phase_mask)
                print(f"Career phase {req_details['phase']}: {phase_mask.sum()} matches")
        
        # Combine masks within each category using OR
        final_mask = pd.Series(True, index=filtered.index)
        
        if age_masks:
            age_mask = np.logical_or.reduce(age_masks)
            final_mask &= age_mask
            print(f"After age filtering: {final_mask.sum()} candidates")
            
        if phase_masks:
            phase_mask = np.logical_or.reduce(phase_masks)
            final_mask &= phase_mask
            print(f"After phase filtering: {final_mask.sum()} candidates")
        
        filtered = filtered[final_mask]
        
        # If no candidates match all criteria, return top 5 by similarity
        if len(filtered) == 0:
            print("No exact matches found, returning all candidates for ranking")
            return players
        
        print(f"Final filtered candidates: {len(filtered)}")
        return filtered

    def _get_age_group_mask(self, players: pd.DataFrame, age_group: str) -> pd.Series:
        """Get boolean mask for age group filtering"""
        if age_group == 'u21':
            return players['Age'] < 21
        elif age_group == '21_25':
            return (players['Age'] >= 21) & (players['Age'] <= 25)
        elif age_group == '26_29':
            return (players['Age'] >= 26) & (players['Age'] <= 29)
        elif age_group == '30_plus':
            return players['Age'] >= 30
        return pd.Series(True, index=players.index)

    def _rank_candidates(self, candidates: pd.DataFrame, requirement: Dict) -> List[Dict]:
        """Rank and format candidate recommendations"""
        if candidates.empty:
            return []
        
        ranked_candidates = []
        
        for _, player in candidates.iterrows():
            try:
                # Create single player DataFrame while preserving index
                player_df = pd.DataFrame([player.to_dict()])
                
                # Get performance predictions
                predictions = self.performance_predictor.predict_performance(player_df)
                
                # Calculate fit score based on requirement type
                if requirement['type'] == 'age_group':
                    fit_score = self._calculate_age_group_fit(player, requirement)
                elif requirement['type'] == 'career_phase':
                    fit_score = self._calculate_phase_fit(predictions, requirement)
                else:
                    fit_score = 0.5  # Default score for other requirement types
                
                ranked_candidates.append({
                    'player_id': player.name,
                    'name': player['Name'],
                    'age': player['Age'],
                    'current_value': player['Current_Value'],
                    'similarity_score': float(player['similarity_score']),
                    'fit_score': fit_score,
                    'predicted_phase': predictions.get('career_trajectory', {}).get('current_phase', 'Unknown'),
                    'performance_predictions': predictions,
                    'requirement_match': requirement
                })
                
            except Exception as e:
                self.logger.error(f"Error ranking candidate {player['Name']}: {str(e)}")
                continue
        
        # Sort by combined score (similarity * fit)
        ranked_candidates.sort(
            key=lambda x: x['similarity_score'] * x['fit_score'], 
            reverse=True
        )
        
        return ranked_candidates

    def _calculate_age_group_fit(self, player: pd.Series, requirement: Dict) -> float:
        """Calculate how well player fits age group requirement"""
        age = player['Age']
        
        if requirement['group'] == 'u21':
            return 1.0 if age < 21 else 0.0
        elif requirement['group'] == '21_25':
            return 1.0 if 21 <= age <= 25 else 0.0
        elif requirement['group'] == '26_29':
            return 1.0 if 26 <= age <= 29 else 0.0
        elif requirement['group'] == '30_plus':
            return 1.0 if age >= 30 else 0.0
        
        return 0.0

    def _calculate_phase_fit(self, predictions: Dict, requirement: Dict) -> float:
        """Calculate how well player fits career phase requirement"""
        try:
            current_phase = predictions.get('career_trajectory', {}).get('current_phase')
            next_phase = predictions.get('career_trajectory', {}).get('next_phase')
            years_to_next = predictions.get('career_trajectory', {}).get('years_to_next_phase', 0)
            
            if not current_phase:  # If phase prediction failed
                return 0.0
            
            if current_phase == requirement['phase']:
                return 1.0
            elif next_phase == requirement['phase'] and years_to_next <= 1:
                return 0.8
            elif next_phase == requirement['phase']:
                return 0.6
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating phase fit: {str(e)}")
            return 0.0
