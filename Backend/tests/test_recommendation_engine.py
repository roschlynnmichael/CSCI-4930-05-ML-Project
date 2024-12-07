import pandas as pd
from pathlib import Path
import sys

# Add the parent directory to system path
sys.path.append(str(Path(__file__).parent.parent))

from app.model.recommendation_engine import RecommendationEngine

def create_test_data():
    """Create realistic test data with clear imbalances"""
    # Create test team data with imbalances
    team_data = pd.DataFrame({
        'Name': ['Player1', 'Player2', 'Player3', 'Player4'],
        'Age': [19, 19, 27, 28],  # Lacking in 21-25 and 30+ age groups
        'Career_Games': [50, 55, 200, 210],
        'Career_Minutes': [4500, 4950, 18000, 18900],
        'Career_Goals': [15, 16, 60, 63],
        'Career_Assists': [10, 11, 40, 42],
        'Career_Yellows': [5, 5, 20, 21],
        'Career_Reds': [0, 0, 2, 2],
        'Current_Value': [2000000, 2200000, 10000000, 10500000],
        'Peak_Value': [5000000, 5500000, 15000000, 15750000],
        'Squad_Size': [25, 25, 25, 25],
        'Minutes_per_Game': [90, 90, 90, 90],
        'Goals_per_Game': [0.3, 0.29, 0.3, 0.3],
        'Assists_per_Game': [0.2, 0.2, 0.2, 0.2],
        'Goal_to_Assist_Ratio': [1.5, 1.45, 1.5, 1.5],
        'Minutes_per_Goal': [300, 309, 300, 300],
        'Card_Rate': [0.1, 0.09, 0.1, 0.1],
        'Goal_Involvement': [0.5, 0.49, 0.5, 0.5],
        'Minutes_Share': [0.25, 0.25, 0.25, 0.25],
        'Value_Growth': [0.2, 0.2, 0.1, 0.1],
        'Value_Stability': [0.9, 0.9, 0.9, 0.9],
        'Value_to_Squad_Ratio': [0.1, 0.11, 0.5, 0.52],
        'Playing_Time_Share': [0.25, 0.25, 0.25, 0.25]
    })
    
    # Create test available players with diverse profiles
    available_players = pd.DataFrame({
        'Name': ['Available1', 'Available2', 'Available3', 'Available4', 'Available5'],
        'Age': [20, 23, 25, 28, 32],  # Different age groups
        'Career_Games': [60, 110, 180, 250, 320],
        'Career_Minutes': [5400, 9900, 16200, 22500, 28800],
        'Career_Goals': [18, 33, 54, 75, 96],
        'Career_Assists': [12, 22, 36, 50, 64],
        'Career_Yellows': [6, 11, 18, 25, 32],
        'Career_Reds': [0, 1, 2, 2, 3],
        'Current_Value': [2500000, 5500000, 9000000, 11000000, 7000000],
        'Peak_Value': [6000000, 13000000, 14000000, 16000000, 18000000],
        'Squad_Size': [25, 25, 25, 25, 25],
        'Minutes_per_Game': [90, 90, 90, 90, 90],
        'Goals_per_Game': [0.3, 0.3, 0.3, 0.3, 0.3],
        'Assists_per_Game': [0.2, 0.2, 0.2, 0.2, 0.2],
        'Goal_to_Assist_Ratio': [1.5, 1.5, 1.5, 1.5, 1.5],
        'Minutes_per_Goal': [300, 300, 300, 300, 300],
        'Card_Rate': [0.1, 0.1, 0.1, 0.1, 0.1],
        'Goal_Involvement': [0.5, 0.5, 0.5, 0.5, 0.5],
        'Minutes_Share': [0.2, 0.2, 0.2, 0.2, 0.2],
        'Value_Growth': [0.2, 0.15, 0.1, 0.1, 0.05],
        'Value_Stability': [0.9, 0.9, 0.9, 0.9, 0.9],
        'Value_to_Squad_Ratio': [0.1, 0.22, 0.36, 0.44, 0.28],
        'Playing_Time_Share': [0.2, 0.2, 0.2, 0.2, 0.2]
    })
    
    return team_data, available_players

def test_recommendation_engine():
    # Get test data
    team_data, available_players = create_test_data()
    
    try:
        # Initialize recommendation engine
        print("\nInitializing recommendation engine...")
        engine = RecommendationEngine()
        
        # Get recommendations
        print("Generating recommendations...")
        recommendations = engine.get_recommendations(team_data, available_players)
        
        # Print results
        print("\nTeam Requirements:")
        print("------------------")
        for req_type, details in recommendations['requirements'].items():
            print(f"\n{req_type}:")
            for key, value in details.items():
                print(f"{key}: {value}")
        
        print("\nRecommendations:")
        print("----------------")
        for req_type, candidates in recommendations['recommendations'].items():
            print(f"\nFor {req_type}:")
            for i, candidate in enumerate(candidates, 1):
                print(f"\n{i}. {candidate['name']}")
                print(f"   Age: {candidate['age']}")
                print(f"   Value: €{candidate['current_value']:,}")
                print(f"   Similarity Score: {candidate['similarity_score']:.2f}")
                print(f"   Fit Score: {candidate['fit_score']:.2f}")
                print(f"   Predicted Phase: {candidate.get('performance_predictions', {}).get('career_trajectory', {}).get('current_phase', 'N/A')}")
                
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        raise

if __name__ == "__main__":
    test_recommendation_engine() 