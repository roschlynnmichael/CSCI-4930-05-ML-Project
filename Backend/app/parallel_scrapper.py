import aiohttp
import asyncio
from bs4 import BeautifulSoup
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class ParallelPlayerScraper:
    def __init__(self):
        self.base_transfermarkt_url = "https://www.transfermarkt.com"
        self.apify_api_key = "apify_api_DtfxEWl7hpHvuuw7UB0LJck4iFgsNu1dNorP"
        self.cache = {}
        self.session = None
    
    async def get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def scrape_players_parallel(self, player_ids: list) -> Dict[str, Dict]:
        """Scrape multiple players in parallel"""
        async with aiohttp.ClientSession() as session:
            self.session = session
            tasks = [self.scrape_player(player_id) for player_id in player_ids]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Create a dictionary mapping player_id to their data
            player_data = {}
            for player_id, result in zip(player_ids, results):
                if isinstance(result, Exception):
                    logger.error(f"Error scraping player {player_id}: {str(result)}")
                    player_data[player_id] = {"error": str(result)}
                else:
                    player_data[player_id] = result
                    
            return player_data

    async def scrape_player(self, player_id: str) -> Optional[Dict]:
        """Scrape a single player's data"""
        try:
            if player_id in self.cache:
                return self.cache[player_id]

            url = f"{self.base_transfermarkt_url}/player/profil/spieler/{player_id}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }

            session = await self.get_session()
            async with session.get(url, headers=headers) as response:
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')

                # Extract basic info
                player_data = {
                    'id': player_id,
                    'status': 'success',
                    'progress': 100
                }

                # Get player name and image
                header = soup.select_one('div.data-header__profile-container')
                player_data['name'] = header.select_one('h1').text.strip() if header else 'Unknown'
                image_element = soup.select_one('img.data-header__profile-image')
                player_data['image_url'] = image_element['src'] if image_element else None

                # Get basic info
                info_table = soup.select_one('table.info-table')
                if info_table:
                    for row in info_table.select('tr'):
                        label = row.select_one('th')
                        value = row.select_one('td')
                        if label and value:
                            key = label.text.strip()
                            player_data[key] = value.text.strip()

                self.cache[player_id] = player_data
                return player_data

        except Exception as e:
            logger.error(f"Error scraping player {player_id}: {str(e)}")
            return {
                'id': player_id,
                'status': 'error',
                'error': str(e),
                'progress': 0
            }

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None