import json
from pathlib import Path
import logging
from typing import Dict, List, Optional
import asyncio

logger = logging.getLogger(__name__)

class JsonScraper:
    def __init__(self, player_scraper):
        """Initialize JsonScraper with a PlayerScraper instance"""
        self.player_scraper = player_scraper
        self.data_file = Path("app/data/players.json")
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.stored_data = self._load_existing_data()

    def _load_existing_data(self) -> Dict:
        """Load existing data from JSON file"""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading stored data: {str(e)}")
            return {}

    def _save_data(self):
        """Save data to JSON file"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.stored_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Successfully saved data for {len(self.stored_data)} players")
        except Exception as e:
            logger.error(f"Error saving data: {str(e)}")

    async def scrape_and_store(self, player_ids: List[str]) -> Dict:
        """Scrape player data and store in JSON"""
        try:
            new_players = 0
            updated_players = 0
            failed_players = []

            for player_id in player_ids:
                # Skip if player data exists and is recent (you could add timestamp checks here)
                if player_id in self.stored_data:
                    updated_players += 1
                    continue

                # Try Apify first
                player_data = await self.player_scraper.get_player_details_apify(player_id)
                if not player_data:
                    # Fallback to direct scraping if Apify fails
                    player_data = await self.player_scraper.get_player_details_direct(player_id)
                
                if player_data:
                    self.stored_data[player_id] = player_data
                    new_players += 1
                else:
                    failed_players.append(player_id)

                # Add small delay between requests
                await asyncio.sleep(1)
                    
            self._save_data()
            
            return {
                "status": "success",
                "new_players": new_players,
                "updated_players": updated_players,
                "failed_players": failed_players,
                "total_stored": len(self.stored_data)
            }
            
        except Exception as e:
            logger.error(f"Error in scrape_and_store: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "failed_players": player_ids
            }

    def get_stored_data(self) -> Dict:
        """Get all stored player data"""
        return self.stored_data

    def get_player_data(self, player_id: str) -> Optional[Dict]:
        """Get stored data for a specific player"""
        return self.stored_data.get(player_id)

    def get_players_by_ids(self, player_ids: List[str]) -> Dict:
        """Get stored data for multiple players"""
        return {
            pid: self.stored_data.get(pid)
            for pid in player_ids
            if pid in self.stored_data
        }

    def update_player_data(self, player_id: str, data: Dict) -> bool:
        """Update stored data for a specific player"""
        try:
            self.stored_data[player_id] = data
            self._save_data()
            return True
        except Exception as e:
            logger.error(f"Error updating player data: {str(e)}")
            return False

    def remove_player_data(self, player_id: str) -> bool:
        """Remove stored data for a specific player"""
        try:
            if player_id in self.stored_data:
                del self.stored_data[player_id]
                self._save_data()
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing player data: {str(e)}")
            return False