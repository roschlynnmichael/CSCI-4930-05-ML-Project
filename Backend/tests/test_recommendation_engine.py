import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

import pytest
import pandas as pd
import json
import logging
from app.model.recommendation_engine import RecommendationEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_test_data():
    """Create test data file"""
    test_data = {
        "123": {
            "id": "123",
            "Full name": "Test Player 1",
            "Date of birth/Age": "1995-01-01 (28)",
            "Position": "Forward",
            "Market value": "€15.00m",
            "careerStats": [
                {
                    "Season": "2022/23",
                    "Appearances": "34",
                    "Goals": "15",
                    "Assists": "7",
                    "Minutes": "2890"
                }
            ]
        },
        "456": {
            "id": "456",
            "Full name": "Test Player 2",
            "Date of birth/Age": "1999-01-01 (24)",
            "Position": "Midfielder",
            "Market value": "€25.00m",
            "careerStats": [
                {
                    "Season": "2022/23",
                    "Appearances": "30",
                    "Goals": "5",
                    "Assists": "12",
                    "Minutes": "2700"
                }
            ]
        },
        "789": {
            "id": "789",
            "Full name": "Test Player 3",
            "Date of birth/Age": "2003-01-01 (20)",
            "Position": "Defender",
            "Market value": "€8.00m",
            "careerStats": [
                {
                    "Season": "2022/23",
                    "Appearances": "20",
                    "Goals": "1",
                    "Assists": "2",
                    "Minutes": "1800"
                }
            ]
        },
        "101": {  # Adding an older player for twilight phase testing
            "id": "101",
            "Full name": "Test Player 4",
            "Date of birth/Age": "1990-01-01 (33)",
            "Position": "Midfielder",
            "Market value": "€5.00m",
            "careerStats": [
                {
                    "Season": "2022/23",
                    "Appearances": "25",
                    "Goals": "3",
                    "Assists": "4",
                    "Minutes": "2250"
                }
            ]
        }
    }
    
    test_file = Path("app/data/players.json")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, indent=2)
    
    return test_data

def test_recommendation_engine():
    """Test the recommendation engine"""
    print("\nInitializing recommendation engine...")
    engine = RecommendationEngine()
    
    # Setup test data
    test_data = setup_test_data()
    
    print("Generating recommendations...")
    # Test with a subset of players as the squad
    squad_ids = ["123", "456"]  # Test with 2 players
    recommendations = engine.get_recommendations(squad_ids)
    
    print("\nTeam Analysis:")
    print("------------------")
    try:
        # Check if recommendations were generated
        assert isinstance(recommendations, dict), "Recommendations should be a dictionary"
        
        # Check for required keys in the response
        assert "squad_analysis" in recommendations, "Missing squad analysis"
        assert "identified_needs" in recommendations, "Missing identified needs"
        assert "recommendations" in recommendations, "Missing recommendations"
        
        # Validate squad analysis
        squad_analysis = recommendations['squad_analysis']
        print("\nSquad Demographics:")
        total_percentage = 0
        for phase, data in squad_analysis.items():
            percentage = data['percentage']
            total_percentage += percentage
            print(f"{phase}: {data['count']} players ({percentage:.1f}%)")
            assert percentage >= 0, f"Negative percentage for {phase}"
            assert data['count'] >= 0, f"Negative count for {phase}"
            
        assert abs(total_percentage - 100.0) < 0.1, "Percentages should sum to 100%"
        
        # Validate identified needs
        print("\nIdentified Needs:")
        needs = recommendations['identified_needs']
        for need in needs:
            print(f"Need more players in {need} phase")
            assert need in engine.career_phases, f"Invalid phase: {need}"
        
        # Validate recommendations
        print("\nRecommendations:")
        for phase, candidates in recommendations['recommendations'].items():
            print(f"\nFor {phase} phase:")
            for candidate in candidates:
                score = candidate['similarity_score']
                print(f"- {candidate['name']} (Age: {candidate['age']}, "
                      f"Score: {score:.2f})")
                assert score >= 0, f"Negative similarity score for {candidate['name']}"
                assert score <= 1, f"Similarity score > 1 for {candidate['name']}"
                
                # Validate age matches phase
                min_age, max_age = engine.career_phases[phase]
                assert min_age <= candidate['age'] <= max_age, \
                    f"Player age {candidate['age']} outside {phase} phase range"
        
        print("\nAll tests passed successfully!")
        
    except AssertionError as e:
        print(f"Error during testing: {str(e)}")
        raise
    except KeyError as e:
        print(f"Error during testing: {str(e)}")
        print("Actual recommendation structure:", recommendations)
        raise
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise

if __name__ == "__main__":
    test_recommendation_engine() 