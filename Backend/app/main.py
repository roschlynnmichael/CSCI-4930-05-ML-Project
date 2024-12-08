from fastapi import FastAPI, HTTPException
import requests
from bs4 import BeautifulSoup
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
    
def get_player_details(self, player_id: str):
    """Get detailed player statistics from Transfermarkt"""
    try:
        # Check cache first
        if player_id in self.cache:
            return self.cache[player_id]
            
        # Construct URL - handle both full URLs and IDs
        if player_id.startswith('http'):
            url = player_id
        else:
            url = f"{self.base_transfermarkt_url}/spieler/{player_id}"
            
        logger.info(f"Fetching player details from: {url}")
        
        # Make request with custom headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract basic info
        header_div = soup.find('div', {'class': 'data-header__profile-container'})
        info = {
            'name': header_div.find('h1').text.strip() if header_div and header_div.find('h1') else 'Unknown',
            'image_url': soup.find('img', {'class': 'data-header__profile-image'})['src'] if soup.find('img', {'class': 'data-header__profile-image'}) else None,
            'position': None,
            'age': None,
            'nationality': None,
            'current_team': None,
            'market_value': None
        }
        
        # Get detailed info from the info table
        info_table = soup.find('div', {'class': 'info-table'})
        if info_table:
            rows = info_table.find_all('tr')
            for row in rows:
                label = row.find('th')
                value = row.find('td')
                if label and value:
                    key = label.text.strip().lower()
                    if 'position' in key:
                        info['position'] = value.text.strip()
                    elif 'age' in key:
                        info['age'] = value.text.strip()
                    elif 'nationality' in key:
                        info['nationality'] = value.text.strip()
                    elif 'current club' in key:
                        info['current_team'] = value.text.strip()
        
        # Get market value
        market_value_div = soup.find('div', {'class': 'tm-player-market-value-development__current-value'})
        if market_value_div:
            info['market_value'] = market_value_div.text.strip()
        
        # Get performance data
        stats = {
            'appearances': '0',
            'goals': '0',
            'assists': '0',
            'minutes_played': '0'
        }
        
        performance_table = soup.find('div', {'class': 'performance-table'})
        if performance_table:
            current_season = performance_table.find('tr', {'class': ['odd', 'even']})
            if current_season:
                cells = current_season.find_all('td')
                if len(cells) >= 4:
                    stats['appearances'] = cells[3].text.strip()
                    stats['goals'] = cells[4].text.strip() if len(cells) > 4 else '0'
                    stats['assists'] = cells[5].text.strip() if len(cells) > 5 else '0'
        
        # Get transfer history
        transfers = []
        transfer_table = soup.find('div', {'id': 'transferhistorie'})
        if transfer_table:
            for row in transfer_table.find_all('tr', {'class': ['odd', 'even']}):
                cells = row.find_all('td')
                if len(cells) >= 5:
                    transfer = {
                        'date': cells[0].text.strip(),
                        'from': cells[1].text.strip(),
                        'to': cells[2].text.strip(),
                        'value': cells[3].text.strip()
                    }
                    transfers.append(transfer)
        
        # Compile all data
        player_data = {
            'info': info,
            'stats': stats,
            'transfers': transfers[:5]  # Last 5 transfers
        }
        
        # Cache the results
        self.cache[player_id] = player_data
        logger.info(f"Successfully fetched player data for ID: {player_id}")
        
        return player_data
        
    except requests.RequestException as e:
        logger.error(f"Request error fetching player {player_id}: {str(e)}")
        raise HTTPException(status_code=503, detail="Unable to fetch player data")
    except Exception as e:
        logger.error(f"Error processing player {player_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))