import sys
from pathlib import Path
import pandas as pd

# Add Backend directory to system path
current_dir = Path(__file__).parent.parent
sys.path.append(str(current_dir))

from app.model.team_balance import TeamBalanceOptimizer
from app.model.roster_analyzer import RosterAnalyzer

def test_team_balance():
    # Create test data with clear age groups
    test_team = pd.DataFrame({
        'Name': [f'Player{i}' for i in range(1, 21)],  # 20 players
        'Age': [
            # Breakthrough (4 players)
            18, 19, 19, 20,
            # Development (6 players)
            21, 22, 22, 23, 23, 24,
            # Peak (7 players)
            25, 26, 26, 27, 27, 28, 29,
            # Twilight (3 players)
            31, 32, 33
        ],
        'Career_Games': [
            # Breakthrough
            20, 25, 30, 35,
            # Development
            50, 60, 65, 70, 75, 80,
            # Peak
            120, 140, 150, 160, 170, 180, 190,
            # Twilight
            250, 280, 300
        ]
    })
    
    # Add other required columns based on Career_Games
    test_team['Career_Minutes'] = test_team['Career_Games'] * 85
    test_team['Career_Goals'] = (test_team['Career_Games'] * 0.3).astype(int)
    test_team['Career_Assists'] = (test_team['Career_Games'] * 0.2).astype(int)
    test_team['Career_Yellows'] = (test_team['Career_Games'] * 0.1).astype(int)
    test_team['Career_Reds'] = (test_team['Career_Games'] * 0.01).astype(int)
    test_team['Current_Value'] = test_team['Career_Games'] * 100000
    test_team['Peak_Value'] = test_team['Current_Value'] * 1.5
    test_team['Squad_Size'] = len(test_team)
    
    try:
        # Initialize optimizer
        print("Initializing TeamBalanceOptimizer...")
        optimizer = TeamBalanceOptimizer()
        
        # Get analysis
        print("Analyzing squad balance...")
        analysis = optimizer.analyze_squad_balance(test_team)
        
        # Print results
        print("\nSquad Metrics:")
        print(analysis['squad_metrics'])
        
        print("\nAge Distribution Analysis:")
        print("Current Distribution:")
        for age_group, value in analysis['age_analysis']['current'].items():
            print(f"{age_group}: {value:.1%}")
        print("\nGaps:")
        for age_group, gap in analysis['age_analysis']['gaps'].items():
            print(f"{age_group}: {gap:+.1%}")
        
        print("\nPhase Distribution Analysis:")
        print("Current Distribution:")
        for phase, value in analysis['phase_analysis']['current'].items():
            print(f"{phase}: {value:.1%}")
        print("\nGaps:")
        for phase, gap in analysis['phase_analysis']['gaps'].items():
            print(f"{phase}: {gap:+.1%}")
        
        print("\nBalance Scores:")
        for metric, score in analysis['balance_scores'].items():
            print(f"{metric}: {score:.2f}")
        
        print("\nRecommendations:")
        for rec in analysis['recommendations']:
            print(f"- {rec}")
            
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        raise

if __name__ == "__main__":
    test_team_balance() 