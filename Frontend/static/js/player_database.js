class PlayerDatabase {
    constructor() {
        this.apiBaseUrl = '/api';
        this.setupEventListeners();
        this.selectedPlayerCard = null;
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
        document.getElementById('playerCard')?.classList.add('hidden');
        
        const resultsContainer = document.getElementById('searchResults');
        const playersList = document.getElementById('playersList');
        if (!resultsContainer || !playersList) return;

        console.log('Search results:', results); // Debug log

        resultsContainer.classList.remove('hidden');
        playersList.innerHTML = '';
        
        results.forEach(player => {
            console.log('Processing player:', player); // Debug log
            const card = this.createPlayerCard(player);
            playersList.appendChild(card);
        });
    }

    createPlayerCard(player) {
        const card = document.createElement('div');
        card.className = 'bg-white rounded-lg shadow-md overflow-hidden cursor-pointer transform transition hover:scale-105';
        card.onclick = () => {
            // Store just name and image_url
            this.selectedPlayerCard = {
                name: player.name,
                image_url: player.image_url?.replace('/small/', '/big/')
            };
            this.loadPlayerDetails(player.id);
        };
        
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

    addToSquad(player) {
        const selectedPlayersDiv = document.getElementById('selectedPlayers');
        if (!selectedPlayersDiv) return;

        // Create selected player card
        const card = document.createElement('div');
        card.className = 'selected-player-card bg-white rounded-lg shadow p-4 mb-2';
        
        card.innerHTML = `
            <div class="flex justify-between items-center">
                <span class="player-name font-semibold">${player.name || 'Unknown'}</span>
                <button class="remove-from-squad text-red-500 hover:text-red-700">×</button>
            </div>
            <div class="text-sm text-gray-600 player-age">Age: ${player.age}</div>
        `;

        // Add event listener for removal
        card.querySelector('.remove-from-squad').addEventListener('click', () => {
            card.remove();
        });

        selectedPlayersDiv.appendChild(card);
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
        
        // Use the stored name and image_url
        const name = this.selectedPlayerCard?.name || player['Full name'] || 'Unknown';
        const imageUrl = this.selectedPlayerCard?.image_url || player.image_url || '/static/images/default-player.png';
        
        // Get all career stats and info
        const careerStats = player.careerStats || [];
        const mostRecentStats = careerStats[0] || {}; // Get most recent stats
        
        playerCard.innerHTML = `
            <div class="bg-white rounded-lg shadow-lg overflow-hidden">
                <div class="p-6">
                    <div class="flex items-center space-x-6 mb-6">
                        <img src="${imageUrl}" 
                             alt="${name}" 
                             class="w-24 h-24 rounded-full object-cover">
                        <div>
                            <h2 class="text-2xl font-bold">${name}</h2>
                            <p class="text-gray-600">${player['Current club'] || ''}</p>
                            <p class="text-lg font-semibold text-indigo-600">${player['Market value'] || ''}</p>
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-4 mb-8">
                        ${[
                            { label: 'Position', value: player['Position'] },
                            { label: 'Age', value: player['Date of birth/Age'] },
                            { label: 'Height', value: player['Height'] },
                            { label: 'Citizenship', value: player['Citizenship'] },
                            { label: 'Current Club', value: player['Current club'] },
                            { label: 'Joined', value: player['Joined'] },
                            { label: 'Contract Until', value: player['Contract expires'] },
                            { label: 'Foot', value: player['Foot'] },
                            { label: 'Place of Birth', value: player['Place of birth'] },
                            { label: 'Player Agent', value: player['Player agent'] }
                        ].map(({ label, value }) => `
                            <div class="bg-gray-50 p-3 rounded">
                                <p class="text-sm text-gray-600">${label}</p>
                                <p class="font-medium text-gray-900">${value || '-'}</p>
                            </div>
                        `).join('')}
                    </div>

                    <div class="border-t pt-6">
                        <h3 class="text-xl font-bold mb-4">Current Season Statistics</h3>
                        <div class="grid grid-cols-4 gap-4">
                            <div class="bg-gray-50 p-4 rounded text-center">
                                <p class="text-2xl font-bold text-indigo-600">${mostRecentStats.Appearances || '0'}</p>
                                <p class="text-sm text-gray-600">Appearances</p>
                            </div>
                            <div class="bg-gray-50 p-4 rounded text-center">
                                <p class="text-2xl font-bold text-indigo-600">${mostRecentStats.Goals || '0'}</p>
                                <p class="text-sm text-gray-600">Goals</p>
                            </div>
                            <div class="bg-gray-50 p-4 rounded text-center">
                                <p class="text-2xl font-bold text-indigo-600">${mostRecentStats.Assists || '0'}</p>
                                <p class="text-sm text-gray-600">Assists</p>
                            </div>
                            <div class="bg-gray-50 p-4 rounded text-center">
                                <p class="text-2xl font-bold text-indigo-600">${mostRecentStats.Minutes || '0'}</p>
                                <p class="text-sm text-gray-600">Minutes Played</p>
                            </div>
                        </div>
                    </div>

                    <div class="border-t pt-6 mt-6">
                        <h3 class="text-xl font-bold mb-4">Career Statistics</h3>
                        <div class="overflow-x-auto">
                            <table class="min-w-full">
                                <thead>
                                    <tr class="bg-gray-50">
                                        <th class="px-4 py-2 text-left">Season</th>
                                        <th class="px-4 py-2 text-left">Club</th>
                                        <th class="px-4 py-2 text-left">Competition</th>
                                        <th class="px-4 py-2 text-center">Games</th>
                                        <th class="px-4 py-2 text-center">Goals</th>
                                        <th class="px-4 py-2 text-center">Assists</th>
                                        <th class="px-4 py-2 text-center">Minutes</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${careerStats.map(stat => `
                                        <tr class="border-t hover:bg-gray-50">
                                            <td class="px-4 py-2">${stat.Season || '-'}</td>
                                            <td class="px-4 py-2">${stat.Club || '-'}</td>
                                            <td class="px-4 py-2">${stat.Competition || '-'}</td>
                                            <td class="px-4 py-2 text-center">${stat.Appearances || '0'}</td>
                                            <td class="px-4 py-2 text-center">${stat.Goals || '0'}</td>
                                            <td class="px-4 py-2 text-center">${stat.Assists || '0'}</td>
                                            <td class="px-4 py-2 text-center">${stat.Minutes || '0'}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    ${player.transfers && player.transfers.length > 0 ? `
                        <div class="border-t pt-6 mt-6">
                            <h3 class="text-xl font-bold mb-4">Transfer History</h3>
                            <div class="space-y-4">
                                ${player.transfers.map(transfer => `
                                    <div class="bg-gray-50 p-4 rounded">
                                        <div class="flex justify-between items-center">
                                            <div>
                                                <p class="text-sm text-gray-600">${transfer.Season} - ${transfer.Date}</p>
                                                <p class="font-medium">${transfer.Left} → ${transfer.Joined}</p>
                                            </div>
                                            <div class="text-right">
                                                <p class="text-sm text-gray-600">Market Value: ${transfer.Market_Value || '-'}</p>
                                                <p class="font-semibold text-indigo-600">${transfer.Fee || '-'}</p>
                                            </div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
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

    _extractAge(dateString) {
        if (!dateString) return null;
        // Format: "Feb 5, 1985 (39)" -> extract 39
        const ageMatch = dateString.match(/\((\d+)\)/);
        return ageMatch ? ageMatch[1] : null;
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing PlayerDatabase');
    window.playerDatabase = new PlayerDatabase();
});