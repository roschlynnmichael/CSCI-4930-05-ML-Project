from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.data.player_service import PlayerService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

player_service = PlayerService()

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