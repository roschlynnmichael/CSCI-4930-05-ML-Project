// Team Balance Analyzer JavaScript

const BACKEND_URL = 'http://127.0.0.1:8000';
const DEFAULT_PLAYER_IMAGE = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIGNsYXNzPSJmZWF0aGVyIGZlYXRoZXItdXNlciI+PHBhdGggZD0iTTIwIDIxdi0yYTQgNCAwIDAgMC00LTRINGE0IDQgMCAwIDAtNCA0djIiPjwvcGF0aD48Y2lyY2xlIGN4PSIxMiIgY3k9IjciIHI9IjQiPjwvY2lyY2xlPjwvc3ZnPg==';

let selectedPlayers = [];
let ageChart = null;
let phaseChart = null;
let scrapingProgress = new Map();

document.addEventListener('DOMContentLoaded', function() {
    const playerSearch = document.getElementById('playerSearch');
    const analyzeButton = document.getElementById('analyzeTeam');

    // Player search functionality
    playerSearch.addEventListener('input', debounce(searchPlayers, 300));
    
    // Analyze team button
    analyzeButton.addEventListener('click', analyzeTeam);

    // Add click outside handler
    document.addEventListener('click', function(event) {
        const searchResults = document.getElementById('playerResults');
        const searchInput = document.getElementById('playerSearch');
        
        if (!searchResults.contains(event.target) && !searchInput.contains(event.target)) {
            searchResults.innerHTML = '';
        }
    });
});

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

async function searchPlayers(event) {
    const searchTerm = event.target.value;
    if (searchTerm.length < 3) return;

    try {
        const response = await fetch(`${BACKEND_URL}/api/search-player?name=${searchTerm}`);
        const data = await response.json();
        displaySearchResults(data.search_results);
    } catch (error) {
        console.error('Error searching players:', error);
    }
}

function displaySearchResults(results) {
    const resultsDiv = document.getElementById('playerResults');
    resultsDiv.innerHTML = '';
    
    results.forEach(player => {
        const playerDiv = document.createElement('div');
        playerDiv.className = 'p-2 hover:bg-gray-100 cursor-pointer flex items-center space-x-3';
        
        const imageUrl = player.image_url || DEFAULT_PLAYER_IMAGE;
        
        playerDiv.innerHTML = `
            <img src="${imageUrl}" 
                 class="w-8 h-8 rounded-full object-cover bg-gray-100" 
                 alt="${player.name}"
                 onerror="this.src='${DEFAULT_PLAYER_IMAGE}'">
            <span>${player.name}</span>
        `;
        
        playerDiv.onclick = () => addPlayer(player.id, player.name, player.image_url);
        resultsDiv.appendChild(playerDiv);
    });
}

async function addPlayer(playerId, playerName, imageUrl) {
    try {
        // Hide search results
        document.getElementById('playerResults').innerHTML = '';
        document.getElementById('playerSearch').value = '';
        
        // Check if player already exists
        if (selectedPlayers.find(p => p.id === playerId)) {
            return;
        }

        // Create progress element first
        const playerDiv = document.createElement('div');
        playerDiv.id = `player-loading-${playerId}`;
        playerDiv.className = 'glass-card p-3 mb-2';
        playerDiv.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    <img src="${imageUrl || DEFAULT_PLAYER_IMAGE}" 
                         class="w-10 h-10 rounded-full object-cover bg-gray-100 animate-pulse" 
                         alt="${playerName}">
                    <span class="font-medium text-gray-800">${playerName}</span>
                </div>
                <div class="w-24">
                    <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div id="progress-${playerId}" 
                             class="h-full bg-gradient-to-r from-indigo-600 to-emerald-600 transition-all duration-300" 
                             style="width: 0%">
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.getElementById('selectedPlayers').appendChild(playerDiv);

        // Start progress updates
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress = Math.min(progress + 5, 90);
            updateProgress(playerId, progress);
        }, 100);

        // Fetch player data
        const response = await fetch(`${BACKEND_URL}/api/player/${playerId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const playerData = await response.json();
        
        // Clear interval and set progress to 100%
        clearInterval(progressInterval);
        updateProgress(playerId, 100);

        // Add to selected players with basic info
        selectedPlayers.push({
            id: playerId,
            name: playerName,
            image_url: imageUrl || DEFAULT_PLAYER_IMAGE,
            ...playerData
        });

        // Update display after short delay to show completion
        setTimeout(() => {
            updateSelectedPlayersList();
        }, 300);

    } catch (error) {
        console.error('Error adding player:', error);
        const progressBar = document.getElementById(`progress-${playerId}`);
        if (progressBar) {
            progressBar.classList.remove('from-indigo-600', 'to-emerald-600');
            progressBar.classList.add('bg-red-600');
        }
    }
}

function updateProgress(playerId, progress) {
    const progressBar = document.getElementById(`progress-${playerId}`);
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
    }
}

function updateSelectedPlayersList() {
    const selectedPlayersDiv = document.getElementById('selectedPlayers');
    selectedPlayersDiv.innerHTML = '';

    selectedPlayers.forEach(player => {
        const playerDiv = document.createElement('div');
        playerDiv.className = 'glass-card p-3 mb-2';
        
        playerDiv.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    <img src="${player.image_url || DEFAULT_PLAYER_IMAGE}" 
                         class="w-10 h-10 rounded-full object-cover bg-gray-100" 
                         alt="${player.name}"
                         onerror="this.src='${DEFAULT_PLAYER_IMAGE}'">
                    <span class="font-medium text-gray-800">${player.name}</span>
                </div>
                <button onclick="removePlayer('${player.id}')" 
                        class="text-red-500 hover:text-red-700">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        `;
        selectedPlayersDiv.appendChild(playerDiv);
    });
}

function removePlayer(playerId) {
    selectedPlayers = selectedPlayers.filter(p => p.id !== playerId);
    updateSelectedPlayersList();
}

async function analyzeTeam() {
    if (selectedPlayers.length === 0) {
        showError('Please add players to analyze');
        return;
    }

    document.getElementById('loadingOverlay').classList.remove('hidden');

    const playerIds = selectedPlayers.map(p => p.id);
    
    try {
        const response = await fetch(`${BACKEND_URL}/api/combined-analysis`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                players: selectedPlayers,
                player_ids: playerIds
            })
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();
        console.log('Analysis response:', data);

        // Check if we have valid data before updating UI
        if (data && data.squad_analysis) {
            updateSquadMetrics(data);
            updateBalanceScores(data);
            updateDistributionCharts(data);
            updateRecommendations(data);
            // Remove the displayPlayerRecommendations call since we removed that section
        } else {
            throw new Error('Invalid data structure received from server');
        }
    } catch (error) {
        console.error('Error analyzing team:', error);
        showError('Error analyzing team. Please try again later.');
    } finally {
        document.getElementById('loadingOverlay').classList.add('hidden');
    }
}

function calculateAgeBalance(players) {
    if (!players.length) return 0;
    
    const ages = players.map(player => extractAgeFromString(player['Date of birth/Age']) || 0);
    const avgAge = ages.reduce((a, b) => a + b, 0) / ages.length;
    
    // Ideal average age is around 26
    const ageDiff = Math.abs(avgAge - 26);
    return Math.max(0, 1 - (ageDiff / 10)); // Normalize to 0-1
}

function calculatePhaseBalance(current, ideal) {
    let totalDiff = 0;
    Object.keys(ideal).forEach(phase => {
        totalDiff += Math.abs((current[phase] || 0) - (ideal[phase] || 0));
    });
    return Math.max(0, 1 - totalDiff);
}

function extractAgeFromString(dateString) {
    if (!dateString) return null;
    const match = dateString.match(/\((\d+)\)/);
    return match ? parseInt(match[1]) : null;
}

function updateSquadMetrics(data) {
    const squadAnalysis = data.squad_analysis || {};
    const totalPlayers = selectedPlayers.length;
    const averageAge = selectedPlayers.reduce((sum, player) => {
        const age = extractAgeFromString(player['Date of birth/Age']) || 0;
        return sum + age;
    }, 0) / totalPlayers;

    document.getElementById('averageAge').textContent = averageAge.toFixed(1);
    document.getElementById('squadSize').textContent = totalPlayers;
}

function updateBalanceScores(data) {
    try {
        const phaseAnalysis = data.squad_analysis?.phase_analysis || {};
        const ageAnalysis = data.squad_analysis?.age_analysis || {};
        
        // Calculate phase balance
        const phaseBalance = calculateDistributionBalance(
            phaseAnalysis.current || {},
            phaseAnalysis.ideal || {}
        );
        
        // Calculate age balance
        const ageBalance = calculateDistributionBalance(
            ageAnalysis.current || {},
            ageAnalysis.ideal || {}
        );
        
        // Calculate overall balance (weighted average)
        const overallBalance = (phaseBalance * 0.6 + ageBalance * 0.4);
        
        // Update UI
        updateBalanceScore('overall', overallBalance);
        updateBalanceScore('age', ageBalance);
        updateBalanceScore('phase', phaseBalance);
        
    } catch (error) {
        console.error('Error updating balance scores:', error);
    }
}

function calculateDistributionBalance(current, ideal) {
    let totalDiff = 0;
    let count = 0;
    
    Object.keys(ideal).forEach(key => {
        const currentValue = current[key] || 0;
        const idealValue = ideal[key] || 0;
        totalDiff += Math.abs(currentValue - idealValue);
        count++;
    });
    
    // Normalize the difference to a 0-1 scale
    return Math.max(0, 1 - (totalDiff / 2));
}

function updateBalanceScore(type, score) {
    const scoreElement = document.getElementById(`${type}BalanceScore`);
    const barElement = document.getElementById(`${type}BalanceBar`);
    
    if (scoreElement && barElement) {
        const percentage = Math.round(score * 100);
        scoreElement.textContent = `${percentage}%`;
        barElement.style.width = `${percentage}%`;
        
        // Update bar color based on score
        barElement.className = `h-2.5 rounded-full ${getProgressBarClass(score)}`;
    }
}

function updateDistributionCharts(data) {
    const ageAnalysis = data.squad_analysis?.age_analysis || {};
    const phaseAnalysis = data.squad_analysis?.phase_analysis || {};
    
    // Age Distribution Chart
    const ageLabels = ['Under 21', '21-25', '26-29', '30+'];
    const ageKeys = ['u21', '21_25', '26_29', '30_plus'];
    
    const ageCurrentData = ageKeys.map(key => 
        (ageAnalysis.current?.[key] || 0) * 100
    );
    
    const ageIdealData = ageKeys.map(key => 
        (ageAnalysis.ideal?.[key] || 0) * 100
    );

    if (window.ageChart) {
        window.ageChart.destroy();
    }

    const ageCtx = document.getElementById('ageDistributionChart').getContext('2d');
    window.ageChart = new Chart(ageCtx, {
        type: 'bar',
        data: {
            labels: ageLabels,
            datasets: [
                {
                    label: 'Current Distribution',
                    data: ageCurrentData,
                    backgroundColor: 'rgba(99, 102, 241, 0.5)',
                    borderColor: 'rgb(99, 102, 241)',
                    borderWidth: 1
                },
                {
                    label: 'Ideal Distribution',
                    data: ageIdealData,
                    type: 'line',
                    borderColor: 'rgb(234, 88, 12)',
                    borderWidth: 2,
                    fill: false,
                    pointBackgroundColor: 'rgb(234, 88, 12)'
                }
            ]
        },
        options: getChartOptions('Age Distribution (%)')
    });

    // Career Phase Distribution Chart
    const phaseLabels = ['Breakthrough', 'Development', 'Peak', 'Twilight'];
    const phaseKeys = ['breakthrough', 'development', 'peak', 'twilight'];
    
    const phaseCurrentData = phaseKeys.map(key => 
        (phaseAnalysis.current?.[key] || 0) * 100
    );
    
    const phaseIdealData = phaseKeys.map(key => 
        (phaseAnalysis.ideal?.[key] || 0) * 100
    );

    if (window.phaseChart) {
        window.phaseChart.destroy();
    }

    const phaseCtx = document.getElementById('phaseDistributionChart').getContext('2d');
    window.phaseChart = new Chart(phaseCtx, {
        type: 'bar',
        data: {
            labels: phaseLabels,
            datasets: [
                {
                    label: 'Current Distribution',
                    data: phaseCurrentData,
                    backgroundColor: 'rgba(99, 102, 241, 0.5)',
                    borderColor: 'rgb(99, 102, 241)',
                    borderWidth: 1
                },
                {
                    label: 'Ideal Distribution',
                    data: phaseIdealData,
                    type: 'line',
                    borderColor: 'rgb(234, 88, 12)',
                    borderWidth: 2,
                    fill: false,
                    pointBackgroundColor: 'rgb(234, 88, 12)'
                }
            ]
        },
        options: getChartOptions('Career Phase Distribution (%)')
    });
}

function getChartOptions(title) {
    return {
        responsive: true,
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: true,
                text: title
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        return `${context.dataset.label}: ${context.parsed.y.toFixed(1)}%`;
                    }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                max: 100,
                ticks: {
                    callback: value => value + '%'
                }
            }
        }
    };
}

function updateRecommendations(data) {
    const recommendationsDiv = document.getElementById('recommendations');
    const squadAnalysis = data.squad_analysis || {};
    const needs = data.identified_needs || [];
    
    let recommendationsHTML = '<div class="space-y-4">';
    
    // Squad Size Recommendation
    const squadSize = selectedPlayers.length;
    recommendationsHTML += `
        <div class="recommendation-section">
            <h4 class="font-semibold text-lg mb-2">Squad Size Analysis</h4>
            <p>${getSquadSizeRecommendation(squadSize)}</p>
        </div>
    `;

    // Age Distribution Recommendation
    const ageAnalysis = squadAnalysis.age_analysis || {};
    recommendationsHTML += `
        <div class="recommendation-section">
            <h4 class="font-semibold text-lg mb-2">Age Distribution Analysis</h4>
            <p>${getAgeDistributionRecommendation(ageAnalysis)}</p>
        </div>
    `;

    // Career Phase Recommendations
    if (needs.length > 0) {
        recommendationsHTML += `
            <div class="recommendation-section">
                <h4 class="font-semibold text-lg mb-2">Career Phase Recommendations</h4>
                <p>Your squad needs strengthening in the following phases:</p>
                <ul class="list-disc pl-5 mt-2">
                    ${needs.map(phase => `
                        <li>${phase.charAt(0).toUpperCase() + phase.slice(1)} phase 
                            (${getPhaseRecommendation(phase)})</li>
                    `).join('')}
                </ul>
            </div>
        `;
    }

    recommendationsHTML += '</div>';
    recommendationsDiv.innerHTML = recommendationsHTML;
}

function getSquadSizeRecommendation(size) {
    if (size < 20) return "Your squad is understaffed. Consider adding more players to reach the ideal size of 22-25 players.";
    if (size > 25) return "Your squad might be too large. Consider streamlining it to 22-25 players for optimal management.";
    return "Your squad size is optimal.";
}

function getAgeDistributionRecommendation(analysis) {
    const current = analysis.current || {};
    const ideal = analysis.ideal || {};
    let recommendations = [];
    
    Object.entries(current).forEach(([group, value]) => {
        const diff = (value - (ideal[group] || 0));
        if (Math.abs(diff) > 0.1) {
            const groupName = group.replace('_', '-').toUpperCase();
            recommendations.push(
                diff > 0 
                    ? `Consider reducing ${groupName} players (currently ${(value * 100).toFixed(1)}% vs ideal ${(ideal[group] * 100).toFixed(1)}%)`
                    : `Need more ${groupName} players (currently ${(value * 100).toFixed(1)}% vs ideal ${(ideal[group] * 100).toFixed(1)}%)`
            );
        }
    });
    
    return recommendations.length > 0 
        ? recommendations.join('. ') + '.'
        : "Age distribution is well balanced.";
}

function getPhaseRecommendation(phase) {
    const recommendations = {
        'breakthrough': 'Focus on young talents with high potential',
        'development': 'Look for emerging players showing consistent growth',
        'peak': 'Target established players in their prime years',
        'twilight': 'Consider experienced players who can mentor younger squad members'
    };
    return recommendations[phase] || '';
}

function showError(message) {
    const recommendationsDiv = document.getElementById('recommendations');
    recommendationsDiv.innerHTML = `
        <div class="text-red-600">
            ${message}
        </div>
    `;
}

// Add event listener to analyze button
document.getElementById('analyzeTeam').addEventListener('click', analyzeTeam);

// Helper functions
function getMetricValueClass(key, value) {
    if (value.includes && value.includes('Optimal')) return 'text-emerald-600';
    if (key === 'squad_size_status' && value.includes('small')) return 'text-amber-600';
    return 'text-indigo-600';
}

function formatMetricLabel(key) {
    return key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
}

function formatScoreLabel(key) {
    return key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
}

function getProgressBarClass(score) {
    if (score >= 0.8) return 'bg-gradient-to-r from-emerald-500 to-emerald-600';
    if (score >= 0.6) return 'bg-gradient-to-r from-amber-500 to-amber-600';
    return 'bg-gradient-to-r from-red-500 to-red-600';
}

// Add this function to handle parallel scraping
async function addPlayersParallel(playerIds) {
    try {
        // Create progress elements for all players first
        playerIds.forEach(playerId => {
            const playerDiv = document.createElement('div');
            playerDiv.className = 'glass-card p-3 mb-2';
            playerDiv.innerHTML = `
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-3">
                        <div class="w-10 h-10 bg-gray-200 rounded-full animate-pulse"></div>
                        <span class="font-medium text-gray-800">Loading...</span>
                    </div>
                    <div class="w-24">
                        <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div id="progress-${playerId}" 
                                 class="h-full bg-gradient-to-r from-indigo-600 to-emerald-600 transition-all duration-300" 
                                 style="width: 0%">
                            </div>
                        </div>
                    </div>
                </div>
            `;
            document.getElementById('selectedPlayers').appendChild(playerDiv);
        });

        // Start parallel scraping
        const response = await fetch(`${BACKEND_URL}/api/parallel/players`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(playerIds)
        });

        const results = await response.json();

        // Process results and update UI
        Object.entries(results).forEach(([playerId, playerData]) => {
            const progressBar = document.getElementById(`progress-${playerId}`);
            if (playerData.status === 'success') {
                progressBar.style.width = '100%';
                if (!selectedPlayers.find(p => p.id === playerId)) {
                    selectedPlayers.push(playerData);
                }
            } else {
                progressBar.classList.remove('from-indigo-600', 'to-emerald-600');
                progressBar.classList.add('bg-red-600');
            }
        });

        updateSelectedPlayersList();

    } catch (error) {
        console.error('Error in parallel scraping:', error);
        playerIds.forEach(playerId => {
            const progressBar = document.getElementById(`progress-${playerId}`);
            if (progressBar) {
                progressBar.classList.remove('from-indigo-600', 'to-emerald-600');
                progressBar.classList.add('bg-red-600');
            }
        });
    }
}

// Add local storage functions
function savePlayerData(playerData) {
    const storedData = localStorage.getItem('selectedPlayersData') || '{}';
    const allPlayerData = JSON.parse(storedData);
    allPlayerData[playerData.id] = playerData;
    localStorage.setItem('selectedPlayersData', JSON.stringify(allPlayerData));
}

function loadStoredPlayerData() {
    const storedData = localStorage.getItem('selectedPlayersData');
    return storedData ? JSON.parse(storedData) : {};
}

function displayPlayerRecommendations(recommendations) {
    const container = document.getElementById('playerRecommendations');
    container.innerHTML = '';

    if (!recommendations || Object.keys(recommendations).length === 0) {
        container.innerHTML = '<div class="col-span-3 text-center text-gray-500">No recommendations available</div>';
        return;
    }

    Object.entries(recommendations).forEach(([phase, players]) => {
        // Create phase section
        const phaseSection = document.createElement('div');
        phaseSection.className = 'col-span-full mb-6';
        
        const phaseTitle = phase.charAt(0).toUpperCase() + phase.slice(1);
        phaseSection.innerHTML = `
            <h4 class="text-lg font-semibold mb-3">${phaseTitle} Phase Recommendations</h4>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                ${players.map(player => `
                    <div class="bg-white rounded-lg shadow p-4 hover:shadow-lg transition-shadow">
                        <div class="flex items-center space-x-3 mb-2">
                            <img src="${player.image_url || DEFAULT_PLAYER_IMAGE}" 
                                 class="w-12 h-12 rounded-full object-cover"
                                 alt="${player.Full_name}"
                                 onerror="this.src='${DEFAULT_PLAYER_IMAGE}'">
                            <div>
                                <h5 class="font-semibold">${player.Full_name}</h5>
                                <p class="text-sm text-gray-600">${player.Position}</p>
                            </div>
                        </div>
                        <div class="space-y-1">
                            <div class="flex justify-between text-sm">
                                <span>Match Score:</span>
                                <span class="font-medium text-indigo-600">
                                    ${(player.similarity_score * 100).toFixed(1)}%
                                </span>
                            </div>
                            <div class="flex justify-between text-sm">
                                <span>Age:</span>
                                <span>${player['Date of birth/Age']}</span>
                            </div>
                            <div class="flex justify-between text-sm">
                                <span>Market Value:</span>
                                <span>${player['Market value'] || 'N/A'}</span>
                            </div>
                        </div>
                        <button onclick="addPlayerToSquad('${player.id}')" 
                                class="mt-3 w-full bg-indigo-100 text-indigo-700 px-3 py-1 rounded-md hover:bg-indigo-200 transition-colors">
                            Add to Squad
                        </button>
                    </div>
                `).join('')}
            </div>
        `;
        container.appendChild(phaseSection);
    });
}

function addPlayerToSquad(playerId) {
    // Add logic to fetch player details and add to selected players
    fetch(`${BACKEND_URL}/api/player/${playerId}`)
        .then(response => response.json())
        .then(player => {
            if (!selectedPlayers.find(p => p.id === player.id)) {
                selectedPlayers.push(player);
                updateSelectedPlayersList();
                analyzeTeam(); // Re-analyze with new player
            }
        })
        .catch(error => console.error('Error adding player:', error));
}