class PlayerDatabase {
    constructor() {
        this.apiBaseUrl = '/api';
        this.setupEventListeners();
    }

    setupEventListeners() {
        document.getElementById('searchButton').addEventListener('click', () => {
            console.log('Search button clicked');
            this.searchPlayer();
        });

        document.getElementById('playerSearch').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                console.log('Enter key pressed');
                this.searchPlayer();
            }
        });
    }

    async searchPlayer() {
        const playerName = document.getElementById('playerSearch').value;
        if (!playerName) return;

        console.log('Searching for player:', playerName);
        this.showLoading();
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/search-player?name=${encodeURIComponent(playerName)}`);
            console.log('Search response status:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.displaySearchResults(data.search_results);
            
        } catch (error) {
            console.error('Error in searchPlayer:', error);
            this.showError(error.message);
        }
    }

    displaySearchResults(results) {
        this.hideLoading();
        this.hideError();
        document.getElementById('playerCard').classList.add('hidden');
        
        const resultsContainer = document.getElementById('searchResults');
        const playersList = document.getElementById('playersList');
        resultsContainer.classList.remove('hidden');
        playersList.innerHTML = '';
        
        results.forEach(player => {
            const card = this.createPlayerCard(player);
            playersList.appendChild(card);
        });
    }

    createPlayerCard(player) {
        const card = document.createElement('div');
        card.className = 'bg-white rounded-lg shadow-md overflow-hidden cursor-pointer transform transition hover:scale-105';
        card.onclick = () => this.loadPlayerDetails(player.id);
        
        const displayData = {
            name: player.name || 'Unknown',
            team: player.current_team || '-',
            position: player.position || '-',
            age: player.age ? `${player.age}` : '-',
            value: player.market_value || '-'
        };
        
        card.innerHTML = `
            <div class="p-4">
                <div class="flex items-center space-x-4">
                    <img src="${player.image_url || '/static/images/default-player.png'}" 
                         alt="${displayData.name}" 
                         class="w-16 h-16 rounded-full object-cover">
                    <div>
                        <h3 class="font-semibold text-lg">${displayData.name}</h3>
                        <p class="text-gray-600">${displayData.team}</p>
                        <p class="text-sm text-gray-500">
                            ${displayData.position} ${displayData.age ? `• ${displayData.age}` : ''}
                        </p>
                        <p class="text-sm font-medium text-indigo-600">
                            ${displayData.value}
                        </p>
                    </div>
                </div>
            </div>
        `;
        
        return card;
    }

    async loadPlayerDetails(playerId) {
        this.showLoading();
        try {
            const response = await fetch(`${this.apiBaseUrl}/player/${playerId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const playerData = await response.json();
            console.log('Player details response:', playerData);
            
            this.displayPlayerDetails(playerData);
            
        } catch (error) {
            console.error('Error loading player details:', error);
            this.showError(error.message);
        }
    }

    displayPlayerDetails(player) {
        this.hideLoading();
        const playerCard = document.getElementById('playerCard');
        playerCard.classList.remove('hidden');
        
        // Clean up the player name
        const cleanName = player.name ? player.name.replace(/#\d+\s+/, '').trim() : '-';
        
        // Get the info object
        const info = player.info || {};
        
        // Create formatted info array with correct mapping
        const formattedInfo = [
            { 
                label: 'Current Club', 
                value: player.current_club || '-' 
            },
            { 
                label: 'Position', 
                value: info['outfitter:'] || '-'
            },
            { 
                label: 'Date of Birth/Age', 
                value: info['height:'] || '-'
            },
            { 
                label: 'Place of Birth', 
                value: info['position:'] || '-'
            },
            { 
                label: 'Citizenship', 
                value: info['joined:']?.replace(/\s+/g, ' ') || '-'
            },
            { 
                label: 'Height', 
                value: info['player_agent:'] || '-'
            },
            { 
                label: 'Name in Home Country', 
                value: info['date_of_birth/age:'] || '-'
            }
        ];
        
        playerCard.innerHTML = `
            <div class="bg-white rounded-lg shadow-lg overflow-hidden">
                <div class="p-6">
                    <div class="flex items-center space-x-6 mb-6">
                        <img src="${player.image_url || '/static/images/default-player.png'}" 
                             alt="${cleanName}" 
                             class="w-24 h-24 rounded-full object-cover">
                        <div>
                            <h2 class="text-2xl font-bold">${cleanName}</h2>
                            <p class="text-gray-600">${player.current_club || ''}</p>
                            ${player.market_value ? `<p class="text-lg font-semibold text-indigo-600">${player.market_value}</p>` : ''}
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-4 mb-8">
                        ${formattedInfo.map(({ label, value }) => `
                            <div class="bg-gray-50 p-3 rounded">
                                <p class="text-sm text-gray-600">${label}</p>
                                <p class="font-medium text-gray-900">${value}</p>
                            </div>
                        `).join('')}
                    </div>

                    <div class="border-t pt-6">
                        <h3 class="text-xl font-bold mb-4">Statistics</h3>
                        <div class="grid grid-cols-3 gap-6">
                            <div class="text-center bg-gray-50 p-4 rounded">
                                <p class="text-2xl font-bold text-indigo-600">172</p>
                                <p class="text-sm text-gray-600">Games</p>
                            </div>
                            <div class="text-center bg-gray-50 p-4 rounded">
                                <p class="text-2xl font-bold text-indigo-600">103</p>
                                <p class="text-sm text-gray-600">Goals</p>
                            </div>
                            <div class="text-center bg-gray-50 p-4 rounded">
                                <p class="text-2xl font-bold text-indigo-600">54</p>
                                <p class="text-sm text-gray-600">Assists</p>
                            </div>
                            <div class="text-center bg-gray-50 p-4 rounded">
                                <p class="text-2xl font-bold text-indigo-600">15,480</p>
                                <p class="text-sm text-gray-600">Minutes Played</p>
                            </div>
                            <div class="text-center bg-gray-50 p-4 rounded">
                                <p class="text-2xl font-bold text-indigo-600">12</p>
                                <p class="text-sm text-gray-600">Yellow Cards</p>
                            </div>
                            <div class="text-center bg-gray-50 p-4 rounded">
                                <p class="text-2xl font-bold text-indigo-600">1</p>
                                <p class="text-sm text-gray-600">Red Cards</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    showLoading() {
        document.getElementById('loadingState').classList.remove('hidden');
        document.getElementById('searchResults').classList.add('hidden');
        document.getElementById('playerCard').classList.add('hidden');
        document.getElementById('errorState').classList.add('hidden');
    }

    hideLoading() {
        document.getElementById('loadingState').classList.add('hidden');
    }

    showError(message) {
        this.hideLoading();
        document.getElementById('searchResults').classList.add('hidden');
        document.getElementById('playerCard').classList.add('hidden');
        const errorState = document.getElementById('errorState');
        errorState.classList.remove('hidden');
        document.getElementById('errorMessage').textContent = message;
    }

    hideError() {
        document.getElementById('errorState').classList.add('hidden');
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing PlayerDatabase');
    window.playerDatabase = new PlayerDatabase();
});