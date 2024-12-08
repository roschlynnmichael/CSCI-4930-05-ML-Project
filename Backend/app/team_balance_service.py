import json
from pathlib import Path
from typing import Dict, Optional, List
import logging
from datetime import datetime

class TeamBalanceService:
    def __init__(self):
        self.data_dir = Path('data/team_balance')
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.teams_file = self.data_dir / 'saved_teams.json'
        self.players_file = self.data_dir / 'team_players.json'
        self._setup_logging()
        self.load_data()

    def _setup_logging(self):
        """Setup logging for the service"""
        log_dir = Path('logs')
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            filename=log_dir / 'team_balance_service.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def load_data(self):
        """Load saved teams and players data"""
        try:
            if self.teams_file.exists():
                with open(self.teams_file, 'r', encoding='utf-8') as f:
                    self.saved_teams = json.load(f)
            else:
                self.saved_teams = {}

            if self.players_file.exists():
                with open(self.players_file, 'r', encoding='utf-8') as f:
                    self.players = json.load(f)
            else:
                self.players = {}

        except Exception as e:
            self.logger.error(f"Error loading data: {str(e)}")
            self.saved_teams = {}
            self.players = {}

    def save_data(self):
        """Save current data to files"""
        try:
            with open(self.teams_file, 'w', encoding='utf-8') as f:
                json.dump(self.saved_teams, f, indent=2, ensure_ascii=False)
            
            with open(self.players_file, 'w', encoding='utf-8') as f:
                json.dump(self.players, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"Error saving data: {str(e)}")
            raise

    def add_player(self, player_data: Dict) -> Optional[Dict]:
        """Add or update player data for team balance analysis"""
        try:
            player_id = str(player_data.get('id'))
            if not player_id:
                return None

            # Store only necessary data for team balance
            self.players[player_id] = {
                'id': player_id,
                'name': player_data.get('name', 'Unknown'),
                'image_url': player_data.get('image_url'),
                'age': player_data.get('age') or self._extract_age(player_data.get('Date of birth/Age', '')),
                'position': player_data.get('position', 'Unknown'),
                'market_value': player_data.get('market_value', 'Unknown'),
                'last_updated': datetime.now().isoformat()
            }
            
            self.save_data()
            return self.players[player_id]

        except Exception as e:
            self.logger.error(f"Error adding player {player_data.get('id')}: {str(e)}")
            return None

    def get_player(self, player_id: str) -> Optional[Dict]:
        """Get player data by ID"""
        return self.players.get(str(player_id))

    def save_team(self, team_name: str, player_ids: List[str]) -> bool:
        """Save a team composition for later analysis"""
        try:
            self.saved_teams[team_name] = {
                'player_ids': player_ids,
                'saved_at': datetime.now().isoformat()
            }
            self.save_data()
            return True
        except Exception as e:
            self.logger.error(f"Error saving team {team_name}: {str(e)}")
            return False

    def get_saved_team(self, team_name: str) -> Optional[List[Dict]]:
        """Get a saved team's player data"""
        try:
            team = self.saved_teams.get(team_name)
            if not team:
                return None

            return [
                self.players.get(str(player_id))
                for player_id in team['player_ids']
                if self.players.get(str(player_id))
            ]
        except Exception as e:
            self.logger.error(f"Error retrieving team {team_name}: {str(e)}")
            return None

    def _extract_age(self, age_string: str) -> Optional[int]:
        """Extract age from various string formats"""
        try:
            if not age_string:
                return None
            
            # Handle "(age)" format
            if '(' in str(age_string):
                age = age_string.split('(')[1].replace(')', '')
                return int(age)
            
            # Handle direct number
            if str(age_string).isdigit():
                return int(age_string)
            
            return None
        except Exception as e:
            self.logger.error(f"Error extracting age from {age_string}: {str(e)}")
            return None

    def list_saved_teams(self) -> Dict:
        """Get list of all saved teams"""
        return {
            name: {
                'saved_at': data['saved_at'],
                'player_count': len(data['player_ids'])
            }
            for name, data in self.saved_teams.items()
        }

    def delete_saved_team(self, team_name: str) -> bool:
        """Delete a saved team"""
        try:
            if team_name in self.saved_teams:
                del self.saved_teams[team_name]
                self.save_data()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting team {team_name}: {str(e)}")
            return False