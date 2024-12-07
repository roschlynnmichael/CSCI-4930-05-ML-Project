from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import pandas as pd
from pathlib import Path
from app.model.roster_analyzer import RosterAnalyzer, FeatureEngineering
from app.data.data_collector import DataCollector
from app.data.data_integrator import DataIntegrator
from app.model.performance_predictor import PerformancePredictor

app = FastAPI()

# Initialize components
analyzer = RosterAnalyzer()
collector = DataCollector(use_mock_data=False)  # Set to False for real API data
integrator = DataIntegrator()
predictor = PerformancePredictor()

class Player(BaseModel):
    Name: str
    Age: float
    Career_Minutes: float
    Career_Games: float
    Career_Goals: float
    Career_Assists: float
    Career_Yellows: float
    Career_Reds: float
    Current_Value: float
    Peak_Value: float
    Squad_Size: int

class TeamAnalysis(BaseModel):
    team_name: str
    players: List[Player]

class PlayerIds(BaseModel):
    transfermarkt: str
    fbref: str

@app.post("/analyze-team")
async def analyze_team(team: TeamAnalysis):
    try:
        # Convert input data to DataFrame
        team_data = pd.DataFrame([player.dict() for player in team.players])
        
        # Analyze team using your model
        results = analyzer.analyze_team(team_data)
        
        # Convert results to dictionary for JSON response
        analysis_results = {
            "team_name": team.team_name,
            "analysis": results.to_dict(orient='records'),
            "phase_distribution": results['Career_Phase'].value_counts().to_dict()
        }
        
        return analysis_results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/player/{transfermarkt_id}")
async def get_player_data(transfermarkt_id: str, fbref_id: str):
    """Get integrated player data from multiple sources"""
    try:
        player_ids = {
            'transfermarkt': transfermarkt_id,
            'fbref': fbref_id
        }
        
        integrated_data = await integrator.get_integrated_player_data(player_ids)
        return integrated_data
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict-performance")
async def predict_performance(player: Player):
    """Predict player's future performance"""
    try:
        # Convert player data to DataFrame
        player_data = pd.DataFrame([player.dict()])
        
        # Get performance predictions
        predictions = predictor.predict_performance(player_data)
        return predictions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/player-stats/{player_id}")
async def get_player_stats(player_id: str, source: str):
    """Get player statistics from a specific source"""
    try:
        data = await collector.get_player_data(player_id, source)
        if not data:
            raise HTTPException(status_code=404, detail=f"Player not found in {source}")
        return data
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}