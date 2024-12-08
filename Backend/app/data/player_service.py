import requests
from bs4 import BeautifulSoup
import logging
from typing import Dict, Optional, List

class PlayerService:
    _instance = None
    _initialized = False
    _players_cache = {}  # Class-level cache

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PlayerService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not PlayerService._initialized:
            self.base_url = "https://www.transfermarkt.com"
            self.headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            self.logger = logging.getLogger(__name__)
            PlayerService._initialized = True

    async def search_player(self, name: str) -> Optional[Dict]:
        """
        Search for players using Transfermarkt website
        Returns list of players found
        """
        try:
            search_url = f"{self.base_url}/schnellsuche/ergebnis/schnellsuche?query={name}"
            self.logger.info(f"Searching player at: {search_url}")
            
            response = requests.get(search_url, headers=self.headers)
            if response.status_code != 200:
                self.logger.error(f"Search failed with status: {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            player_rows = soup.find_all('table', class_='items')[0].find_all('tr', class_=['odd', 'even']) if soup.find_all('table', class_='items') else []
            
            search_results = []
            for row in player_rows:
                player_link = row.find('td', class_='hauptlink').find('a')
                player_img = row.find('img', class_='bilderrahmen-fixed')
                player_info = row.find_all('td', class_='zentriert')
                
                if player_link:
                    player_id = player_link['href'].split('/')[-1]
                    search_results.append({
                        'id': player_id,
                        'name': player_link.text.strip(),
                        'image_url': player_img['src'] if player_img else None,
                        'position': player_info[1].text if len(player_info) > 1 else 'Unknown',
                        'age': player_info[2].text if len(player_info) > 2 else 'Unknown',
                        'nationality': player_info[3].find('img')['title'] if len(player_info) > 3 and player_info[3].find('img') else 'Unknown',
                        'current_team': row.find_all('td', class_='hauptlink')[1].text.strip() if len(row.find_all('td', class_='hauptlink')) > 1 else 'Unknown',
                        'market_value': row.find('td', class_='rechts hauptlink').text.strip() if row.find('td', class_='rechts hauptlink') else 'Unknown'
                    })
            
            return {'search_results': search_results[:5]}  # Limit to top 5 results

        except Exception as e:
            self.logger.error(f"Error in search_player: {str(e)}")
            raise

    async def get_player_details(self, player_id: str) -> Optional[Dict]:
        """Get detailed player information from their profile page"""
        try:
            # Check cache first
            if player_id in self._players_cache:
                self.logger.info(f"Returning cached data for player {player_id}")
                return self._players_cache[player_id]

            player_url = f"{self.base_url}/spieler/profil/spieler/{player_id}"
            self.logger.info(f"Fetching player details from: {player_url}")
            
            response = requests.get(player_url, headers=self.headers)
            if response.status_code != 200:
                self.logger.error(f"Failed to get player details. Status: {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Get player name
            name_element = soup.find('h1', class_='data-header__headline-wrapper')
            player_name = name_element.text.strip() if name_element else 'Unknown'

            # Get player image
            img_element = soup.find('img', class_='data-header__profile-image')
            image_url = img_element['src'] if img_element and 'src' in img_element.attrs else None

            # Get player position
            position_element = soup.find('li', class_='data-header__position')
            position = position_element.text.strip() if position_element else 'Unknown'

            # Get birth date and age
            info_table = soup.find('div', class_='info-table')
            birth_date = None
            age = None
            if info_table:
                birth_elements = info_table.find_all('span', class_='info-table__content')
                for element in birth_elements:
                    text = element.text.strip()
                    if '(' in text and ')' in text:  # Format: "Jan 1, 1990 (33)"
                        birth_date = text.split('(')[0].strip()
                        age = text.split('(')[1].replace(')', '').strip()
                        break

            # Get market value
            market_value_div = soup.find('div', class_='tm-player-market-value-development__current-value')
            market_value = market_value_div.text.strip() if market_value_div else 'Unknown'

            # Get statistics
            stats = {}
            stats_table = soup.find('div', class_='grid statistics-list')
            if stats_table:
                stat_items = stats_table.find_all('div', class_='grid__cell')
                for item in stat_items:
                    label = item.find('span', class_='label')
                    value = item.find('span', class_='value')
                    if label and value:
                        key = label.text.strip().lower()
                        if 'appearances' in key:
                            stats['appearances'] = value.text.strip()
                        elif 'goals' in key:
                            stats['goals'] = value.text.strip()
                        elif 'assists' in key:
                            stats['assists'] = value.text.strip()
                        elif 'minutes' in key:
                            stats['minutes'] = value.text.strip()

            # Create player data dictionary
            player_data = {
                'id': player_id,
                'Full name': player_name,
                'Date of birth/Age': f"{birth_date} ({age})" if birth_date and age else 'Unknown',
                'Position': position,
                'Market value': market_value,
                'image_url': image_url,
                'careerStats': [{
                    'Season': '2023/24',
                    'Appearances': stats.get('appearances', '0'),
                    'Goals': stats.get('goals', '0'),
                    'Assists': stats.get('assists', '0'),
                    'Minutes': stats.get('minutes', '0')
                }]
            }

            # Cache the player data
            self._players_cache[player_id] = player_data
            self.logger.info(f"Added player {player_id} to cache. Cache now contains {len(self._players_cache)} players")
            return player_data

        except Exception as e:
            self.logger.error(f"Error in get_player_details: {str(e)}")
            raise

    def _extract_stats(self, stats_table) -> Dict:
        """Extract player statistics from the stats table"""
        try:
            stats = {}
            if not stats_table:
                return stats

            stat_items = stats_table.find_all('div', class_='grid__cell')
            for item in stat_items:
                label = item.find('span', class_='label')
                value = item.find('span', class_='value')
                if label and value:
                    key = label.text.strip().lower().replace(' ', '_')
                    stats[key] = value.text.strip()
            return stats
        except Exception as e:
            self.logger.error(f"Error extracting stats: {str(e)}")
            return {}

    def get_all_players(self) -> Dict:
        """Get all available players from the cache"""
        try:
            self.logger.info(f"Players in cache: {list(self._players_cache.keys())}")
            return self._players_cache
        except Exception as e:
            self.logger.error(f"Error getting all players: {str(e)}")
            return {}