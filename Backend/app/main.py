from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.data.player_service import PlayerService
from app.model.team_balance import TeamBalanceOptimizer
from typing import Dict, List
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

player_service = PlayerService()
team_balance_optimizer = TeamBalanceOptimizer()

@app.get("/api/search-player")
async def search_player(name: str):
    """Search for players by name"""
    logger.info(f"Searching for player: {name}")
    try:
        results = await player_service.search_player(name)
        if not results:
            raise HTTPException(status_code=404, detail="No players found")
        return results
    except Exception as e:
        logger.error(f"Error in search_player: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/player/{player_id}")
async def get_player_details(player_id: str):
    """Get detailed information for a specific player"""
    logger.info(f"Getting details for player ID: {player_id}")
    try:
        details = await player_service.get_player_details(player_id)
        if not details:
            raise HTTPException(status_code=404, detail="Player not found")
        return details
    except Exception as e:
        logger.error(f"Error in get_player_details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Error handling
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return {"detail": "Internal server error"}, 500

# Keep your existing routes below this line
# ... (your other routes for team analysis, etc.)

@app.post("/api/analyze-team-balance")
async def analyze_team_balance(team_data: List[dict]):
    """Analyze team balance and provide recommendations"""
    try:
        logger.info("Analyzing team balance")
        
        # Convert team data to DataFrame
        df = pd.DataFrame(team_data)
        
        # Add required columns if they don't exist
        if 'Age' not in df.columns and 'info' in df.columns:
            df['Age'] = df['info'].apply(lambda x: x.get('age', 0) if x else 0)
        
        if 'Position' not in df.columns and 'info' in df.columns:
            df['Position'] = df['info'].apply(lambda x: x.get('position', '') if x else '')
        
        # Ensure required columns exist
        required_columns = ['Name', 'Age', 'Position']
        for col in required_columns:
            if col not in df.columns:
                df[col] = ''
        
        # Convert Age to numeric
        df['Age'] = pd.to_numeric(df['Age'], errors='coerce')
        
        # Perform analysis
        analysis_results = team_balance_optimizer.analyze_squad_balance(df)
        
        return {
            "analysis": analysis_results,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error in team balance analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))