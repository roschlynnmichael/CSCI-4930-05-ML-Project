import requests
import random
import json
from datetime import datetime
from pathlib import Path
import pandas as pd
import sys

# Add the parent directory to system path to import from app
sys.path.append(str(Path(__file__).parent.parent))
from app.model.roster_analyzer import RosterAnalyzer
from app.model.feedback_system import FeedbackSystem

def generate_test_team():
    team_data = {
        "team_name": "Test FC",
        "players": []
    }
    
    # Common names for variety
    first_names = ["Alex", "James", "Mohamed", "Juan", "Carlos", "Kevin", "Robert", "Thomas", 
                  "David", "Lucas", "Marco", "Paulo", "Luis", "Andreas", "Christian"]
    last_names = ["Smith", "Silva", "Mueller", "Garcia", "Rodriguez", "Martinez", "Johnson",
                 "Williams", "Brown", "Jones", "Wilson", "Taylor", "Davies", "Evans"]
    
    for i in range(50):
        # Generate realistic player data
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        age = round(random.uniform(17, 35), 1)  # Ages from 17 to 35
        
        # Career stats based on age
        career_years = max(1, int(age - 17))  # Years playing professionally
        games_per_year = random.randint(20, 40)  # Games played per year
        career_games = career_years * games_per_year
        
        # Minutes based on games (60-90 minutes per game)
        minutes_per_game = random.randint(60, 90)
        career_minutes = career_games * minutes_per_game
        
        # Goals and assists (adjusted for position/role)
        scoring_rate = random.uniform(0.1, 0.5)  # Goals per game
        career_goals = int(career_games * scoring_rate)
        career_assists = int(career_goals * random.uniform(0.5, 1.5))
        
        # Cards
        yellow_rate = random.uniform(0.1, 0.3)  # Yellows per game
        career_yellows = int(career_games * yellow_rate)
        career_reds = int(career_yellows * 0.1)  # Reds are ~10% of yellows
        
        # Value in millions (€)
        peak_value = random.uniform(1, 50) * 1000000
        current_value = peak_value * random.uniform(0.5, 1.2)
        
        player = {
            "Name": name,
            "Age": age,
            "Career_Minutes": career_minutes,
            "Career_Games": career_games,
            "Career_Goals": career_goals,
            "Career_Assists": career_assists,
            "Career_Yellows": career_yellows,
            "Career_Reds": career_reds,
            "Current_Value": current_value,
            "Peak_Value": peak_value,
            "Squad_Size": 50  # Total squad size
        }
        
        team_data["players"].append(player)
    
    return team_data

def test_feedback_system():
    """Test the feedback system with generated data"""
    # Initialize systems
    analyzer = RosterAnalyzer()
    feedback_system = FeedbackSystem()
    
    # Generate and analyze test team
    test_team = generate_test_team()
    team_data = pd.DataFrame(test_team['players'])
    
    print("\nTesting Feedback System:")
    print("------------------------")
    
    # 1. Test Phase Prediction Feedback
    print("\n1. Testing Phase Prediction Feedback:")
    results = analyzer.analyze_team(team_data)
    
    # Record feedback for first 5 players
    for _, player in results.head().iterrows():
        # Simulate actual phase (randomly different from prediction 20% of the time)
        phases = ['breakthrough', 'development', 'peak', 'twilight']
        actual_phase = player['Career_Phase']
        if random.random() < 0.2:  # 20% chance of different outcome
            phases.remove(actual_phase)
            actual_phase = random.choice(phases)
            
        success = feedback_system.record_phase_prediction_feedback(
            player_id=player['Name'],
            predicted_phase=player['Career_Phase'],
            actual_phase=actual_phase,
            performance_metrics={
                'games_played': player['Games_Played'],
                'goals_per_game': player['Goals_per_Game'],
                'minutes_per_game': player['Minutes_per_Game']
            }
        )
        print(f"Recorded feedback for {player['Name']}: {'Success' if success else 'Failed'}")
    
    # 2. Test Recommendation Feedback
    print("\n2. Testing Recommendation Feedback:")
    recommendation_types = ['transfer', 'development', 'rotation']
    
    for i in range(3):  # Test 3 different recommendations
        recommendation_id = f"REC_{datetime.now().strftime('%Y%m%d')}_{i}"
        player = results.iloc[i]
        
        # Simulate actual outcome
        actual_outcome = {
            'player_id': player['Name'],
            'type': random.choice(recommendation_types),
            'performance_improvement': random.uniform(0.8, 1.2),
            'team_impact': random.uniform(0.7, 1.3),
            'financial_outcome': random.uniform(0.9, 1.1)
        }
        
        success = feedback_system.record_recommendation_feedback(
            recommendation_id=recommendation_id,
            player_id=player['Name'],
            recommendation_type=actual_outcome['type'],
            actual_outcome=actual_outcome,
            success_metrics={
                'performance_improvement': 1.0,
                'team_impact': 1.0,
                'financial_outcome': 1.0
            }
        )
        print(f"Recorded recommendation feedback {recommendation_id}: {'Success' if success else 'Failed'}")
    
    # 3. Analyze Feedback Trends
    print("\n3. Testing Feedback Analysis:")
    trends = feedback_system.analyze_feedback_trends()
    print("Feedback Trends Analysis:")
    for key, value in trends.items():
        print(f"{key}: {value}")
    
    # 4. Get Feedback Summary
    print("\n4. Testing Feedback Summary:")
    summary = feedback_system.get_feedback_summary()
    print("Feedback Summary:")
    for key, value in summary.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    # Your existing test team generation and output
    test_team = generate_test_team()
    
    print("Sample of generated players:")
    for player in test_team["players"][:5]:
        print("\nPlayer:", player["Name"])
        print(f"Age: {player['Age']}")
        print(f"Games: {player['Career_Games']}")
        print(f"Goals: {player['Career_Goals']}")
        print(f"Value: €{player['Current_Value']:,.2f}")
    
    # Save to file for reference
    with open('test_team_data.json', 'w') as f:
        json.dump(test_team, f, indent=4)
    
    # Run feedback system tests
    print("\nStarting Feedback System Tests...")
    test_feedback_system()