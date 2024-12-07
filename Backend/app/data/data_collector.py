import aiohttp
import asyncio
import logging
from pathlib import Path
from typing import Dict
from datetime import datetime
from bs4 import BeautifulSoup

class DataCollector:
    def __init__(self, use_mock_data: bool = True):
        self._setup_logging()
        self.use_mock_data = use_mock_data
        self.api_base_url = "https://transfermarkt-api.fly.dev"
        self.endpoints = {
            'player_info': '/player/{player_id}/info',
            'player_stats': '/player/{player_id}/stats',
            'player_market_value': '/player/{player_id}/market-value',
            'player_transfers': '/player/{player_id}/transfers'
        }
        
        # Mock data for testing
        self.mock_data = {
            'transfermarkt': {
                '418560': {  # Haaland
                    'name': 'Erling Haaland',
                    'age': 23,
                    'current_value': '€180.00m',
                    'nationality': 'Norway',
                    'position': 'Centre-Forward',
                    'foot': 'Left',
                    'height': '194cm',
                    'current_club': 'Manchester City',
                    'contract_until': '2027',
                    'statistics': {
                        'matches': 35,
                        'goals': 36,
                        'assists': 8
                    },
                    'market_value_history': [
                        {'date': '2024-01', 'value': '180000000'},
                        {'date': '2023-06', 'value': '170000000'},
                        {'date': '2023-01', 'value': '170000000'}
                    ]
                },
                '342229': {  # Mbappe
                    'name': 'Kylian Mbappé',
                    'age': 24,
                    'current_value': '€180.00m',
                    'nationality': 'France',
                    'position': 'Centre-Forward',
                    'foot': 'Right',
                    'height': '178cm',
                    'current_club': 'Paris Saint-Germain',
                    'contract_until': '2024',
                    'statistics': {
                        'matches': 34,
                        'goals': 29,
                        'assists': 6
                    }
                }
            },
            'fbref': {
                '1f44ac21': {  # Haaland
                    'matches': 35,
                    'goals': 36,
                    'assists': 8,
                    'shots': 124,
                    'shots_on_target': 64,
                    'goals_per_90': 1.03,
                    'assists_per_90': 0.23,
                    'goals_assists_per_90': 1.26,
                    'xg': 32.8,
                    'npxg': 29.4,
                    'xa': 7.2
                },
                '5eae500a': {  # Mbappe
                    'matches': 34,
                    'goals': 29,
                    'assists': 6,
                    'shots': 118,
                    'shots_on_target': 59,
                    'goals_per_90': 0.85,
                    'assists_per_90': 0.18,
                    'goals_assists_per_90': 1.03,
                    'xg': 27.4,
                    'npxg': 24.8,
                    'xa': 5.9
                }
            }
        }
        
    def _setup_logging(self):
        log_dir = Path('app/logs')
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            filename=log_dir / 'data_collector.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    async def get_player_data(self, player_id: str, source: str) -> Dict:
        """Get player data from specified source"""
        try:
            # Validate source
            if source not in ['transfermarkt', 'fbref']:
                raise ValueError(f"Invalid source: {source}. Must be one of: transfermarkt, fbref")
            
            if self.use_mock_data:
                return self.mock_data.get(source, {}).get(player_id, {})
            
            if source == 'transfermarkt':
                return await self._get_transfermarkt_api_data(player_id)
            elif source == 'fbref':
                return await self._get_fbref_data(player_id)
            
        except ValueError as e:
            self.logger.error(f"Invalid source or player ID: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error getting {source} data for player {player_id}: {str(e)}")
            return {}

    async def _get_transfermarkt_api_data(self, player_id: str) -> Dict:
        """Get player data from Transfermarkt API"""
        async with aiohttp.ClientSession() as session:
            try:
                # Get basic player info
                info_url = f"{self.api_base_url}{self.endpoints['player_info'].format(player_id=player_id)}"
                info_data = await self._fetch_api_data(session, info_url)
                
                # Get player stats
                stats_url = f"{self.api_base_url}{self.endpoints['player_stats'].format(player_id=player_id)}"
                stats_data = await self._fetch_api_data(session, stats_url)
                
                # Get market value history
                market_url = f"{self.api_base_url}{self.endpoints['player_market_value'].format(player_id=player_id)}"
                market_data = await self._fetch_api_data(session, market_url)
                
                # Combine all data
                combined_data = {
                    **info_data,
                    'statistics': stats_data,
                    'market_value_history': market_data
                }
                
                self.logger.info(f"Successfully retrieved data for player {player_id}")
                return combined_data
                
            except Exception as e:
                self.logger.error(f"Error fetching API data for player {player_id}: {str(e)}")
                return {}

    async def _fetch_api_data(self, session: aiohttp.ClientSession, url: str) -> Dict:
        """Fetch data from API endpoint with rate limiting"""
        try:
            await asyncio.sleep(1)  # Basic rate limiting
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.error(f"API request failed: {response.status} - {url}")
                    return {}
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {str(e)}")
            return {}

    async def _get_fbref_data(self, player_id: str) -> Dict:
        """Get player data from FBref"""
        if self.use_mock_data:
            return self.mock_data.get('fbref', {}).get(player_id, {})
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                # FBref URL format: https://fbref.com/en/players/{player_id}/
                url = f"{self.base_urls['fbref']}/{player_id}"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract standard stats
                        stats = {
                            'matches': self._safe_extract_fbref(soup, 'matches'),
                            'goals': self._safe_extract_fbref(soup, 'goals'),
                            'assists': self._safe_extract_fbref(soup, 'assists'),
                            'shots': self._safe_extract_fbref(soup, 'shots'),
                            'shots_on_target': self._safe_extract_fbref(soup, 'shots_on_target'),
                            'goals_per_90': self._safe_extract_fbref(soup, 'goals_per_90'),
                            'assists_per_90': self._safe_extract_fbref(soup, 'assists_per_90'),
                            'goals_assists_per_90': self._safe_extract_fbref(soup, 'goals_assists_per_90'),
                            'xg': self._safe_extract_fbref(soup, 'xg'),
                            'npxg': self._safe_extract_fbref(soup, 'npxg'),
                            'xa': self._safe_extract_fbref(soup, 'xa')
                        }
                        
                        return stats
                    else:
                        self.logger.error(f"Failed to get FBref data: {response.status}")
                        return {}
                    
            except Exception as e:
                self.logger.error(f"Error fetching FBref data for player {player_id}: {str(e)}")
                return {}

    def _safe_extract_fbref(self, soup: BeautifulSoup, stat_name: str) -> str:
        """Safely extract stats from FBref HTML"""
        try:
            # Find the stat in the stats table
            stat_element = soup.find('td', {'data-stat': stat_name})
            return stat_element.text.strip() if stat_element else ''
        except Exception as e:
            self.logger.error(f"Error extracting {stat_name} from FBref: {str(e)}")
            return ''