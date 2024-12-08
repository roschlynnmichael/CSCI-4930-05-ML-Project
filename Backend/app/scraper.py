import requests
from bs4 import BeautifulSoup
import logging
import json
import time
import asyncio
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class PlayerScraper:
    def __init__(self):
        self.base_transfermarkt_url = "https://www.transfermarkt.com"
        self.apify_api_key = "apify_api_DtfxEWl7hpHvuuw7UB0LJck4iFgsNu1dNorP"  # Move this to environment variables
        self.cache = {}
        
    async def get_player_details_apify(self, player_id: str):
        """Get player details using Apify's Transfermarkt scraper"""
        try:
            # Check cache first
            if player_id in self.cache:
                logger.info(f"Returning cached data for player {player_id}")
                return self.cache[player_id]

            actor_call_url = "https://api.apify.com/v2/acts/curious_coder~transfermarkt/runs"
            headers = {
                "Authorization": f"Bearer {self.apify_api_key}"
            }
            payload = {
                "startUrls": [{
                    "url": f"https://www.transfermarkt.com/player/profil/spieler/{player_id}"
                }]
            }
            
            # Start the actor
            response = requests.post(actor_call_url, json=payload, headers=headers)
            response.raise_for_status()
            run_id = response.json()["data"]["id"]
            
            # Wait for results
            while True:
                status_url = f"https://api.apify.com/v2/actor-runs/{run_id}"
                status_response = requests.get(status_url, headers=headers)
                status = status_response.json()["data"]["status"]
                
                if status == "SUCCEEDED":
                    break
                elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                    raise Exception(f"Actor run failed with status: {status}")
                
                await asyncio.sleep(2)
            
            # Get results
            dataset_id = status_response.json()["data"]["defaultDatasetId"]
            results_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
            results = requests.get(results_url, headers=headers).json()
            
            if results:
                # Cache the results
                self.cache[player_id] = results[0]
                return results[0]
                
            return None
            
        except Exception as e:
            logger.error(f"Apify API error: {str(e)}")
            return None

    async def get_player_details_direct(self, player_id: str):
        """Get player details directly from Transfermarkt"""
        try:
            url = f"{self.base_transfermarkt_url}/player/profil/spieler/{player_id}"
            logger.info(f"Fetching player details from: {url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            logger.info("Successfully fetched and parsed page")

            # Get player name and image
            header = soup.select_one('div.data-header__profile-container')
            name = header.select_one('h1.data-header__headline-wrapper').text.strip() if header else 'Unknown'
            image_element = soup.select_one('img.data-header__profile-image')
            image_url = image_element['src'] if image_element else None

            # Basic info dictionary - now directly in the main object
            player_data = {
                'givenUrl': url,
                'id': player_id,
                'url': url,
                'type': 'player',
                'Full name': name,  # Add name directly to main object
                'image_url': image_url,  # Add image directly to main object
                'careerStats': [],
                'transfers': []
            }

            # Get all info rows
            info_table = soup.select_one('table.info-table')
            if info_table:
                rows = info_table.select('tr')
                for row in rows:
                    label = row.select_one('th')
                    value = row.select_one('td')
                    if label and value:
                        key = label.text.strip()
                        player_data[key] = value.text.strip()  # Add directly to main object

            # Get career stats with more detail
            career_stats = []
            stats_table = soup.select_one('div#yw1')  # Performance data table
            if stats_table:
                rows = stats_table.select('tbody tr')
                for row in rows:
                    cells = row.select('td')
                    if len(cells) >= 7:  # Make sure we have enough cells
                        stat = {
                            'Season': cells[0].text.strip(),
                            'Competition': cells[2].text.strip(),
                            'Club': cells[1].text.strip(),
                            'Appearances': cells[3].text.strip(),
                            'Goals': cells[4].text.strip(),
                            'Assists': cells[5].text.strip(),
                            'Minutes': cells[6].text.strip(),
                            'Yellow_Cards': cells[7].text.strip() if len(cells) > 7 else '0',
                            'Red_Cards': cells[8].text.strip() if len(cells) > 8 else '0',
                            'Minutes_per_Goal': cells[9].text.strip() if len(cells) > 9 else '-'
                        }
                        career_stats.append(stat)

            # Get market value
            market_value = soup.select_one('div.tm-player-market-value-development__current-value')
            if market_value:
                player_data['Market value'] = market_value.text.strip()

            # Get transfers with more detail
            transfers = []
            transfer_table = soup.select_one('div#transferhistorie')
            if transfer_table:
                rows = transfer_table.select('tr.odd, tr.even')
                for row in rows:
                    cells = row.select('td')
                    if len(cells) >= 6:
                        transfer = {
                            'Season': cells[0].text.strip(),
                            'Date': cells[1].text.strip(),
                            'Left': cells[2].text.strip(),
                            'Joined': cells[3].text.strip(),
                            'Market_Value': cells[4].text.strip(),
                            'Fee': cells[5].text.strip() if len(cells) > 5 else None
                        }
                        transfers.append(transfer)

            # Get additional stats if available
            additional_stats = {}
            stats_boxes = soup.select('div.data-header__details div.data-header__content--highlight')
            for box in stats_boxes:
                label = box.select_one('.data-header__label')
                value = box.select_one('.data-header__content')
                if label and value:
                    additional_stats[label.text.strip()] = value.text.strip()

            # Compile all data
            player_data['careerStats'] = career_stats
            player_data['transfers'] = transfers
            player_data['additionalStats'] = additional_stats

            logger.info(f"Successfully scraped data for player {name}")
            logger.info(f"Image URL: {image_url}")  # Add this log to verify image URL
            
            return player_data
            
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            raise