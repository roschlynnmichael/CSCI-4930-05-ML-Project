import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from app.model.feedback_system import FeedbackSystem
from typing import Dict

class FeatureEngineering:
    @staticmethod
    def safe_divide(a, b):
        result = np.divide(a, b, out=np.zeros_like(a, dtype=float), where=b!=0)
        return np.nan_to_num(result, 0)
    
    def create_performance_features(self, data, X):
        X['Minutes_per_Game'] = self.safe_divide(data['Career_Minutes'].values, 
                                               data['Career_Games'].values)
        X['Goals_per_Game'] = self.safe_divide(data['Career_Goals'].values, 
                                             data['Career_Games'].values)
        X['Assists_per_Game'] = self.safe_divide(data['Career_Assists'].values, 
                                               data['Career_Games'].values)
        
        X['Goal_to_Assist_Ratio'] = self.safe_divide(X['Goals_per_Game'], 
                                                    X['Assists_per_Game'])
        X['Minutes_per_Goal'] = self.safe_divide(X['Minutes_per_Game'], 
                                               X['Goals_per_Game'])
        return X
    
    def create_form_features(self, data, X):
        X['Card_Rate'] = self.safe_divide(
            data['Career_Yellows'].values + data['Career_Reds'].values * 3,
            data['Career_Games'].values
        )
        
        X['Goal_Involvement'] = X['Goals_per_Game'] + X['Assists_per_Game']
        X['Minutes_Share'] = self.safe_divide(data['Career_Minutes'].values,
                                            90 * data['Career_Games'].values)
        return X
    
    def create_development_features(self, data, X):
        X['Value_Growth'] = self.safe_divide(
            data['Current_Value'].values - data['Peak_Value'].values,
            data['Peak_Value'].values + 1
        )
        
        X['Value_Stability'] = self.safe_divide(
            data['Current_Value'].values,
            data['Peak_Value'].values + 1
        )
        return X
    
    def create_relative_features(self, data, X):
        X['Value_to_Squad_Ratio'] = self.safe_divide(
            data['Current_Value'].values,
            data['Squad_Size'].values * data['Peak_Value'].values.mean()
        )
        
        X['Playing_Time_Share'] = self.safe_divide(
            data['Career_Minutes'].values,
            data['Squad_Size'].values * data['Career_Games'].values * 90
        )
        return X
    
    def transform(self, data):
        """Transform the input data into features"""
        X = pd.DataFrame()
        X = self.create_performance_features(data, X)
        X = self.create_form_features(data, X)
        X = self.create_development_features(data, X)
        X = self.create_relative_features(data, X)
        return self.process_features(X)
    
    def process_features(self, X):
        for col in X.columns:
            if X[col].dtype in ['float64', 'float32']:
                percentile_99 = np.percentile(X[col], 99)
                percentile_1 = np.percentile(X[col], 1)
                X[col] = X[col].clip(percentile_1, percentile_99)
        
        X = X.replace([np.inf, -np.inf], np.nan)
        
        for col in X.columns:
            X[col] = X[col].fillna(X[col].median())
        
        return X

class RosterAnalyzer:
    def __init__(self):
        try:
            model_dir = Path(r"D:\Projects\Machine Learning Applications for Soccer\model_creation\Backend\app\model")
            self.model = joblib.load(model_dir / "career_phase_model.joblib")
            self.feature_engineering = FeatureEngineering()
            
            # Initialize and fit the scaler with the initial data
            self.scaler = StandardScaler()
            # We'll fit the scaler in the analyze_team method
            print("Models loaded successfully!")
            self.feedback_system = FeedbackSystem()
        except Exception as e:
            print(f"Error loading models: {str(e)}")
            raise

    def analyze_team(self, team_data):
        """Analyze a team's roster and provide insights"""
        try:
            # Prepare features using the feature engineering pipeline
            X = self.feature_engineering.transform(team_data)
            
            # Ensure X has the same columns as during training
            expected_columns = [
                'Minutes_per_Game', 'Goals_per_Game', 'Assists_per_Game',
                'Goal_to_Assist_Ratio', 'Minutes_per_Goal', 'Card_Rate',
                'Goal_Involvement', 'Minutes_Share', 'Value_Growth',
                'Value_Stability', 'Value_to_Squad_Ratio', 'Playing_Time_Share'
            ]
            
            # Reorder columns to match training data
            X = X[expected_columns]
            
            # Fit and transform the data with the scaler
            X_scaled = self.scaler.fit_transform(X)
            
            # Make predictions
            predictions = self.model.predict(X_scaled)
            probabilities = self.model.predict_proba(X_scaled)

            # Map predictions to career phases
            phase_mapping = {
                0: 'breakthrough',
                1: 'development',
                2: 'peak',
                3: 'twilight'
            }
            
            # Create results DataFrame with additional metrics
            results = pd.DataFrame({
                'Name': team_data['Name'],
                'Age': team_data['Age'],
                'Career_Phase': [phase_mapping[p] for p in predictions],
                'Confidence': [max(prob) for prob in probabilities],
                'Games_Played': team_data['Career_Games'],
                'Goals_per_Game': X['Goals_per_Game'],
                'Minutes_per_Game': X['Minutes_per_Game'],
                'Value_Growth': X['Value_Growth']
            })
            
            # Add phase recommendations
            results['Recommendation'] = results.apply(self._get_recommendation, axis=1)
            
            # Record predictions for future feedback
            for _, player in results.iterrows():
                self.feedback_system.record_phase_prediction_feedback(
                    player_id=player['Name'],  # Use actual ID in production
                    predicted_phase=player['Career_Phase'],
                    actual_phase=None,  # To be updated later
                    performance_metrics={
                        'games_played': player['Games_Played'],
                        'goals_per_game': player['Goals_per_Game'],
                        'minutes_per_game': player['Minutes_per_Game']
                    }
                )
            
            return results
            
        except Exception as e:
            print(f"Error in analyze_team: {str(e)}")
            print(f"Feature columns: {X.columns.tolist()}")
            raise

    def _get_recommendation(self, player):
        """Enhanced recommendations based on multiple metrics"""
        base_rec = ""
        training_rec = ""
        playing_time_rec = ""
        development_rec = ""
    
        if player['Career_Phase'] == 'breakthrough':
            if player['Games_Played'] < 10:
                base_rec = "High Priority Development Required"
                training_rec = "Focus on technical skills and physical development"
                playing_time_rec = "Regular youth team starts with occasional first team exposure"
                development_rec = "Regular performance assessments needed to track potential"
            elif player['Goals_per_Game'] > 0.5:
                base_rec = "Fast-Track Development Candidate"
                training_rec = "Accelerated tactical and technical training"
                playing_time_rec = "Regular first team substitute appearances"
                development_rec = "Consider fast-tracking to regular first team training"
            else:
                base_rec = "Standard Development Track"
                training_rec = "Balanced technical and physical training"
                playing_time_rec = "Rotation between youth and reserve teams"
                development_rec = "Monthly progress reviews with development coaches"
    
        elif player['Career_Phase'] == 'development':
            if player['Value_Growth'] > 0.2:
                base_rec = "Progressive Development"
                training_rec = "Advanced tactical and technical refinement"
                playing_time_rec = "Increased first team minutes with rotation"
                development_rec = "Consider for key team roles in coming seasons"
            else:
                base_rec = "Development Monitoring"
                training_rec = "Focus on specific skill improvements"
                playing_time_rec = "Consistent minutes in appropriate level matches"
                development_rec = "Regular feedback sessions with coaching staff"
    
        elif player['Career_Phase'] == 'peak':
            if player['Confidence'] > 0.8:
                base_rec = "Key Squad Member"
                training_rec = "Maintain peak performance and leadership skills"
                playing_time_rec = "Core first team player with managed workload"
                development_rec = "Leadership role in team tactics and mentoring"
            else:
                base_rec = "Performance Optimization"
                training_rec = "Focus on consistency and specific role requirements"
                playing_time_rec = "Regular playing time with strategic rotation"
                development_rec = "Regular performance reviews to maintain standards"
    
        else:  # twilight
            if player['Minutes_per_Game'] > 60:
                base_rec = "Veteran Management"
                training_rec = "Focus on recovery and conditioning"
                playing_time_rec = "Reduced minutes with strategic deployment"
                development_rec = "Transition planning and mentoring responsibilities"
            else:
                base_rec = "Experience Utilization"
                training_rec = "Maintain fitness levels while mentoring"
                playing_time_rec = "Selective use with focus on key matches"
                development_rec = "Active role in youth development and team leadership"
    
        return f"{base_rec}\n- Training: {training_rec}\n- Playing Time: {playing_time_rec}\n- Development: {development_rec}"

    def update_recommendation_feedback(
        self,
        recommendation_id: str,
        actual_outcome: Dict
    ):
        """Update feedback for a specific recommendation"""
        try:
            success_metrics = {
                'performance_improvement': 0.0,
                'team_impact': 0.0,
                'financial_outcome': 0.0
            }
            
            self.feedback_system.record_recommendation_feedback(
                recommendation_id=recommendation_id,
                player_id=actual_outcome.get('player_id'),
                recommendation_type=actual_outcome.get('type'),
                actual_outcome=actual_outcome,
                success_metrics=success_metrics
            )
            
        except Exception as e:
            self.logger.error(f"Error updating recommendation feedback: {str(e)}")

'''
def main():
    try:
        # Use the test_data DataFrame instead of loading from CSV
        data = test_data  # Use your existing test_data DataFrame
        print("Data loaded successfully!")
        print(f"Total players in database: {len(data)}")
        
        # Create sample team data with reset index
        sample_team = data.sample(n=25, random_state=42).reset_index(drop=True)
        print(f"Sample team size: {len(sample_team)}")
        
        # Initialize analyzer
        analyzer = RosterAnalyzer()
        
        # Analyze team
        print("\nAnalyzing team roster...")
        results = analyzer.analyze_team(sample_team)
        
        # Display results
        print("\nTeam Analysis Results:")
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        print(results.sort_values(['Career_Phase', 'Age']).to_string(index=False))
        
        # Display phase distribution
        print("\nCareer Phase Distribution:")
        phase_dist = results['Career_Phase'].value_counts()
        for phase, count in phase_dist.items():
            print(f"{phase}: {count} players ({count/len(results)*100:.1f}%)")
        
        # Create visualizations
        create_analysis_visualizations(results)
        
    except Exception as e:
        print(f"Error in analysis: {str(e)}")
        print(f"Sample team shape: {sample_team.shape}")
        raise

def create_analysis_visualizations(results):
    """Create comprehensive visualizations for the analysis"""
    #plt.style.use('seaborn')
    fig = plt.figure(figsize=(20, 10))
    
    # 1. Career Phase Distribution
    plt.subplot(2, 2, 1)
    sns.countplot(data=results, x='Career_Phase')
    plt.title('Career Phase Distribution')
    plt.xticks(rotation=45)
    
    # 2. Age Distribution by Phase
    plt.subplot(2, 2, 2)
    sns.boxplot(data=results, x='Career_Phase', y='Age')
    plt.title('Age Distribution by Career Phase')
    plt.xticks(rotation=45)
    
    # 3. Performance Metrics
    plt.subplot(2, 2, 3)
    sns.scatterplot(data=results, x='Age', y='Goals_per_Game', 
                   hue='Career_Phase', size='Confidence')
    plt.title('Performance by Age and Career Phase')
    
    # 4. Confidence Distribution
    plt.subplot(2, 2, 4)
    sns.histplot(data=results, x='Confidence', hue='Career_Phase')
    plt.title('Prediction Confidence by Career Phase')
    
    plt.tight_layout()
    plt.show()



if __name__ == "__main__":
    # Add this before running main()
    print("Test Data Info:")
    print(test_data.info())
    print("\nTest Data Sample:")
    print(test_data.head())
    # Verify test_data exists and has the required columns
    required_columns = [
        'Name', 'Age', 'Career_Minutes', 'Career_Games', 'Career_Goals',
        'Career_Assists', 'Career_Yellows', 'Career_Reds', 'Current_Value',
        'Peak_Value', 'Squad_Size'
    ]
    
    missing_columns = [col for col in required_columns if col not in test_data.columns]
    if missing_columns:
        print(f"Missing required columns: {missing_columns}")
        print(f"Available columns: {test_data.columns.tolist()}")
    else:
        main()
'''