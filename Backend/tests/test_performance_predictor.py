import pandas as pd
from pathlib import Path
import sys

# Add the parent directory to system path
sys.path.append(str(Path(__file__).parent.parent))

from app.model.performance_predictor import PerformancePredictor

def test_performance_predictor():
    # Create test player data
    test_player = pd.DataFrame({
        'Name': ['Test Player'],
        'Age': [22],
        'Career_Games': [80],
        'Career_Minutes': [6800],
        'Career_Goals': [25],
        'Career_Assists': [15],
        'Career_Yellows': [8],
        'Career_Reds': [1],
        'Current_Value': [5000000],
        'Peak_Value': [15000000],
        'Squad_Size': [25]
    })
    
    # Initialize predictor
    predictor = PerformancePredictor()
    
    try:
        # Get predictions
        predictions = predictor.predict_performance(test_player)
        
        # Print results
        print("\nPerformance Predictions for Test Player:")
        print("----------------------------------------")
        
        print("\n1. Current Metrics:")
        for metric, value in predictions['current_metrics'].items():
            print(f"{metric}: {value:.2f}")
        
        print("\n2. Future Metrics:")
        print("\nNext Season:")
        for metric, value in predictions['predicted_metrics']['next_season'].items():
            print(f"{metric}: {value:.2f}")
        
        print("\nPeak Potential:")
        for metric, value in predictions['predicted_metrics']['peak_potential'].items():
            print(f"{metric}: {value:.2f}")
        
        print("\n3. Career Trajectory:")
        trajectory = predictions['career_trajectory']
        print(f"Current Phase: {trajectory['current_phase']}")
        print(f"Next Phase: {trajectory['next_phase']}")
        print(f"Years to Next Phase: {trajectory['years_to_next_phase']:.1f}")
        print(f"Development Potential: {trajectory['development_potential']:.2f}")
        print(f"Expected Peak Age: {trajectory['expected_peak_age']}")
        
        print("\n4. Peak Performance Prediction:")
        peak = predictions['peak_prediction']
        print(f"Peak Age: {peak['peak_age']}")
        print(f"Years to Peak: {peak['years_to_peak']:.1f}")
        print("\nPeak Metrics:")
        for metric, value in peak['peak_metrics'].items():
            print(f"{metric}: {value:.2f}")
        
        print("\n5. Value Projection:")
        value = predictions['value_projection']
        print(f"Current Value: €{value['current_value']:,.2f}")
        print(f"Peak Value: €{value['peak_value']:,.2f}")
        print(f"Years to Peak Value: {value['years_to_peak_value']:.1f}")
        print(f"Annual Growth Rate: {value['annual_growth_rate']*100:.1f}%")
        print("\nProjected Values:")
        for age, projected_value in value['projected_values'].items():
            print(f"Age {age}: €{projected_value:,.2f}")
            
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        raise

if __name__ == "__main__":
    test_performance_predictor()