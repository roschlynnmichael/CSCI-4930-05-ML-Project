import requests
from bs4 import BeautifulSoup
import logging
import json
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestPlayerScraper:
    def __init__(self):
        self.base_transfermarkt_url = "https://www.transfermarkt.com"
        self.apify_api_key = "apify_api_DtfxEWl7hpHvuuw7UB0LJck4iFgsNu1dNorP"  # Replace with your Apify API key
        self.cache = {}
        
    def get_player_details_apify(self, player_id: str):
        """Get player details using Apify's Transfermarkt scraper"""
        try:
            # Start Apify actor run
            actor_call_url = "https://api.apify.com/v2/acts/curious_coder~transfermarkt/runs"
            headers = {
                "Authorization": f"Bearer {self.apify_api_key}"
            }
            payload = {
                "startUrls": [{
                    "url": f"https://www.transfermarkt.com/lionel-messi/profil/spieler/{player_id}"
                }]
            }
            
            # Start the actor
            response = requests.post(actor_call_url, json=payload, headers=headers)
            response.raise_for_status()
            run_id = response.json()["data"]["id"]
            logger.info(f"Started Apify actor run: {run_id}")
            
            # Wait for results
            while True:
                status_url = f"https://api.apify.com/v2/actor-runs/{run_id}"
                status_response = requests.get(status_url, headers=headers)
                status = status_response.json()["data"]["status"]
                
                if status == "SUCCEEDED":
                    break
                elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                    raise Exception(f"Actor run failed with status: {status}")
                
                time.sleep(2)  # Wait before checking again
            
            # Get the results
            dataset_id = status_response.json()["data"]["defaultDatasetId"]
            results_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
            results = requests.get(results_url, headers=headers).json()
            
            if results:
                return results[0]  # Return the first (and should be only) result
            return None
            
        except Exception as e:
            logger.error(f"Apify API error: {str(e)}")
            raise

    def get_player_details_direct(self, player_id: str):
        """Get player details directly from Transfermarkt"""
        try:
            url = f"{self.base_transfermarkt_url}/lionel-messi/profil/spieler/{player_id}"
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

            # Basic info
            info = {}
            
            # Get all info rows
            info_table = soup.select_one('table.info-table')
            if info_table:
                rows = info_table.select('tr')
                for row in rows:
                    label = row.select_one('th')
                    value = row.select_one('td')
                    if label and value:
                        key = label.text.strip()
                        info[key] = value.text.strip()

            # Get career stats
            career_stats = []
            stats_table = soup.select_one('div#yw1')  # Performance data table
            if stats_table:
                rows = stats_table.select('tbody tr')
                for row in rows:
                    cells = row.select('td')
                    if len(cells) >= 6:
                        stat = {
                            'Competition': cells[2].text.strip(),
                            'Appearances': cells[3].text.strip(),
                            'Goals': cells[4].text.strip(),
                            'Assists': cells[5].text.strip(),
                            'Minutes': cells[6].text.strip() if len(cells) > 6 else '0'
                        }
                        career_stats.append(stat)

            # Get transfers
            transfers = []
            transfer_table = soup.select_one('div#transferhistorie')
            if transfer_table:
                rows = transfer_table.select('tr.odd, tr.even')
                for row in rows:
                    cells = row.select('td')
                    if len(cells) >= 5:
                        transfer = {
                            'Season': cells[0].text.strip(),
                            'Date': cells[1].text.strip(),
                            'Left': cells[2].text.strip(),
                            'Joined': cells[3].text.strip(),
                            'MV': cells[4].text.strip(),
                            'Fee': cells[5].text.strip() if len(cells) > 5 else None
                        }
                        transfers.append(transfer)

            # Compile all data
            player_data = {
                'givenUrl': url,
                'id': player_id,
                'url': url,
                'type': 'player',
                **info,  # Include all info table data
                'transfers': transfers,
                'careerStats': career_stats
            }
            
            # Pretty print the results
            print("\nPlayer Details:")
            print(json.dumps(player_data, indent=2))
            
            return player_data
            
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            raise

def main():
    try:
        scraper = TestPlayerScraper()
        player_id = "28003"  # Messi's ID
        
        print("\nTesting Apify scraper...")
        apify_data = scraper.get_player_details_apify(player_id)
        print("\nApify Results:")
        print(json.dumps(apify_data, indent=2))
        
        print("\nTesting direct scraper...")
        direct_data = scraper.get_player_details_direct(player_id)
        print("\nDirect Scraping Results:")
        print(json.dumps(direct_data, indent=2))
        
    except Exception as e:
        print(f"\nError during testing: {str(e)}")

if __name__ == "__main__":
    main()