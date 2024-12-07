import pandas as pd
from typing import Dict, List
import logging
from pathlib import Path
import asyncio
from datetime import datetime
from .data_collector import DataCollector

class DataIntegrator:
    def __init__(self):
        self._setup_logging()
        self.collector = DataCollector()
        self.cache_dir = Path('app/data/cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _setup_logging(self):
        log_dir = Path('app/logs')
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            filename=log_dir / 'data_integrator.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    async def get_integrated_player_data(self, player_ids: Dict[str, str]) -> Dict:
        """Get integrated player data from all sources"""
        try:
            # Check cache first
            cache_key = f"{player_ids['transfermarkt']}_{player_ids['fbref']}"
            cached_data = self._check_cache(cache_key)
            if cached_data:
                return cached_data
            
            # Collect data from all sources
            transfermarkt_data = await self.collector.get_player_data(
                player_ids['transfermarkt'], 'transfermarkt'
            )
            fbref_data = await self.collector.get_player_data(
                player_ids['fbref'], 'fbref'
            )
            
            # Integrate data
            integrated_data = {
                # Basic info from Transfermarkt
                'name': transfermarkt_data.get('name'),
                'age': transfermarkt_data.get('age'),
                'nationality': transfermarkt_data.get('nationality'),
                'position': transfermarkt_data.get('position'),
                'foot': transfermarkt_data.get('foot'),
                'height': transfermarkt_data.get('height'),
                'current_club': transfermarkt_data.get('current_club'),
                'contract_until': transfermarkt_data.get('contract_until'),
                
                # Performance data combining both sources
                'performance': {
                    'matches': {
                        'total': transfermarkt_data.get('statistics', {}).get('matches'),
                        'fbref': fbref_data.get('matches')
                    },
                    'goals': {
                        'total': transfermarkt_data.get('statistics', {}).get('goals'),
                        'fbref': fbref_data.get('goals')
                    },
                    'assists': {
                        'total': transfermarkt_data.get('statistics', {}).get('assists'),
                        'fbref': fbref_data.get('assists')
                    },
                    'advanced_stats': {
                        'shots': fbref_data.get('shots'),
                        'shots_on_target': fbref_data.get('shots_on_target'),
                        'goals_per_90': fbref_data.get('goals_per_90'),
                        'assists_per_90': fbref_data.get('assists_per_90'),
                        'goals_assists_per_90': fbref_data.get('goals_assists_per_90'),
                        'xg': fbref_data.get('xg'),
                        'npxg': fbref_data.get('npxg'),
                        'xa': fbref_data.get('xa')
                    }
                },
                
                # Market value data from Transfermarkt
                'market_value': {
                    'current': transfermarkt_data.get('current_value'),
                    'history': transfermarkt_data.get('market_value_history', [])
                }
            }
            
            # Cache the integrated data
            self._cache_data(cache_key, integrated_data)
            
            return integrated_data
            
        except Exception as e:
            self.logger.error(f"Error integrating data for player IDs {player_ids}: {str(e)}")
            raise

    def _check_cache(self, cache_key: str) -> Dict:
        """Check if we have recent cached data"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                data = pd.read_json(cache_file)
                cache_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                
                # Return cached data if less than 24 hours old
                if (datetime.now() - cache_time).days < 1:
                    return data.to_dict('records')[0]
            except Exception as e:
                self.logger.error(f"Error reading cache: {str(e)}")
        return None

    def _cache_data(self, cache_key: str, data: Dict):
        """Cache player data"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            pd.DataFrame([data]).to_json(cache_file)
        except Exception as e:
            self.logger.error(f"Error caching data: {str(e)}")