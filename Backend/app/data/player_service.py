import requests
from bs4 import BeautifulSoup
import logging
from typing import Dict, Optional, List

class PlayerService:
    def __init__(self):
        self.base_url = "https://www.transfermarkt.com"
        self.logger = logging.getLogger(__name__)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

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
        """
        Get detailed player information from their profile page
        """
        try:
            player_url = f"{self.base_url}/spieler/profil/spieler/{player_id}"
            self.logger.info(f"Fetching player details from: {player_url}")
            
            response = requests.get(player_url, headers=self.headers)
            if response.status_code != 200:
                self.logger.error(f"Failed to get player details. Status: {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Get player info
            player_header = soup.find('div', class_='data-header__profile-container')
            player_info = soup.find('div', class_='info-table')
            market_value_div = soup.find('div', class_='tm-player-market-value-development__current-value')
            
            # Get player name
            name_element = soup.find('h1', class_='data-header__headline-wrapper')
            player_name = name_element.text.strip() if name_element else 'Unknown'

            # Get player image
            img_element = soup.find('img', class_='data-header__profile-image')
            image_url = img_element['src'] if img_element and 'src' in img_element.attrs else None

            # Get player details
            info_items = soup.find_all('span', class_='info-table__content')
            info_labels = soup.find_all('span', class_='info-table__content--regular')
            
            info_dict = {}
            for label, content in zip(info_labels, info_items):
                key = label.text.strip().lower().replace(' ', '_')
                value = content.text.strip()
                info_dict[key] = value

            # Get current club
            current_club_element = soup.find('span', class_='data-header__club')
            current_club = current_club_element.text.strip() if current_club_element else 'Unknown'

            # Get market value
            market_value = None
            if market_value_div:
                market_value = market_value_div.text.strip()

            # Get statistics
            stats_table = soup.find('div', class_='grid statistics-list')
            statistics = self._extract_stats(stats_table) if stats_table else {}

            return {
                'id': player_id,
                'name': player_name,
                'image_url': image_url,
                'current_club': current_club,
                'market_value': market_value,
                'info': info_dict,
                'statistics': statistics
            }

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