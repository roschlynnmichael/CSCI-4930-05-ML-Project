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
    try {
        document.getElementById('loadingOverlay').classList.remove('hidden');
        
        const response = await fetch(`${BACKEND_URL}/api/analyze-team-balance`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(selectedPlayers)
        });
        
        const analysis = await response.json();
        
        // Update the balance display
        updateAnalysisDisplay(analysis);
        
        // Your existing chart updates...
        updateCharts(analysis);
        
    } catch (error) {
        console.error('Error analyzing team:', error);
    } finally {
        document.getElementById('loadingOverlay').classList.add('hidden');
    }
}

function extractAgeFromString(dateString) {
    if (!dateString) return null;
    // Match pattern like "Jun 24, 1987 (37)"
    const ageMatch = dateString.match(/\((\d+)\)/);
    return ageMatch ? parseInt(ageMatch[1]) : null;
}

function updateAnalysisDisplay(analysis) {
    // Update squad metrics
    document.getElementById('averageAge').textContent = analysis.squad_metrics.average_age;
    document.getElementById('squadSize').textContent = analysis.squad_metrics.total_players;

    // Update balance scores and progress bars
    const scores = {
        'overall': analysis.balance_scores.overall_balance,
        'age': analysis.balance_scores.age_balance,
        'phase': analysis.balance_scores.phase_balance
    };

    Object.entries(scores).forEach(([key, value]) => {
        const percentage = Math.round(value * 100);
        document.getElementById(`${key}BalanceScore`).textContent = `${percentage}%`;
        document.getElementById(`${key}BalanceBar`).style.width = `${percentage}%`;
    });

    // Update recommendations
    const recommendationsDiv = document.getElementById('recommendations');
    recommendationsDiv.innerHTML = analysis.recommendations
        .map(rec => `<div class="flex items-center space-x-2">
                        <span class="text-indigo-600">•</span>
                        <span>${rec}</span>
                     </div>`)
        .join('');

    // Create/Update charts
    createDistributionCharts(analysis);
}

function createDistributionCharts(analysis) {
    // Age Distribution Chart
    const ageCtx = document.getElementById('ageDistributionChart').getContext('2d');
    new Chart(ageCtx, {
        type: 'bar',
        data: {
            labels: ['U21', '21-25', '26-29', '30+'],
            datasets: [{
                label: 'Current',
                data: Object.values(analysis.age_analysis.current),
                backgroundColor: 'rgba(99, 102, 241, 0.5)',
                borderColor: 'rgb(99, 102, 241)',
                borderWidth: 1
            }, {
                label: 'Ideal',
                data: Object.values(analysis.age_analysis.ideal),
                type: 'line',
                borderColor: 'rgb(16, 185, 129)',
                borderWidth: 2,
                fill: false
            }]
        },
        options: getChartOptions('Age Distribution')
    });

    // Phase Distribution Chart
    const phaseCtx = document.getElementById('phaseDistributionChart').getContext('2d');
    new Chart(phaseCtx, {
        type: 'bar',
        data: {
            labels: ['Breakthrough', 'Development', 'Peak', 'Twilight'],
            datasets: [{
                label: 'Current',
                data: Object.values(analysis.phase_analysis.current),
                backgroundColor: 'rgba(99, 102, 241, 0.5)',
                borderColor: 'rgb(99, 102, 241)',
                borderWidth: 1
            }, {
                label: 'Ideal',
                data: Object.values(analysis.phase_analysis.ideal),
                type: 'line',
                borderColor: 'rgb(16, 185, 129)',
                borderWidth: 2,
                fill: false
            }]
        },
        options: getChartOptions('Career Phase Distribution')
    });
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

function getChartOptions(title) {
    return {
        responsive: true,
        plugins: {
            legend: {
                position: 'top',
                labels: {
                    font: {
                        family: "'Inter', sans-serif",
                        size: 12
                    },
                    padding: 20
                }
            },
            title: {
                display: true,
                text: title,
                font: {
                    family: "'Inter', sans-serif",
                    size: 16,
                    weight: 'bold'
                },
                padding: {
                    bottom: 20
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)'
                },
                ticks: {
                    font: {
                        family: "'Inter', sans-serif"
                    }
                }
            },
            x: {
                grid: {
                    display: false
                },
                ticks: {
                    font: {
                        family: "'Inter', sans-serif"
                    }
                }
            }
        }
    };
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

function updateBalanceDisplay(analysis) {
    // Update overall balance score
    const overallScore = Math.round(analysis.balance_scores.overall_balance * 100);
    const circumference = 2 * Math.PI * 32; // r=32
    const offset = circumference - (analysis.balance_scores.overall_balance * circumference);
    
    const circle = document.getElementById('overallBalanceCircle');
    const text = document.getElementById('overallBalanceText');
    
    circle.style.strokeDasharray = `${circumference} ${circumference}`;
    circle.style.strokeDashoffset = offset;
    text.textContent = `${overallScore}%`;

    // Update age distribution percentages
    const ageDistribution = analysis.age_analysis.current;
    document.getElementById('u21Percentage').textContent = `${Math.round(ageDistribution.u21 * 100)}%`;
    document.getElementById('age21_25Percentage').textContent = `${Math.round(ageDistribution['21_25'] * 100)}%`;
    document.getElementById('age26_29Percentage').textContent = `${Math.round(ageDistribution['26_29'] * 100)}%`;
    document.getElementById('age30PlusPercentage').textContent = `${Math.round(ageDistribution['30_plus'] * 100)}%`;

    // Update career phase percentages
    const phaseDistribution = analysis.phase_analysis.current;
    document.getElementById('breakthroughPercentage').textContent = `${Math.round(phaseDistribution.breakthrough * 100)}%`;
    document.getElementById('developmentPercentage').textContent = `${Math.round(phaseDistribution.development * 100)}%`;
    document.getElementById('peakPercentage').textContent = `${Math.round(phaseDistribution.peak * 100)}%`;
    document.getElementById('twilightPercentage').textContent = `${Math.round(phaseDistribution.twilight * 100)}%`;

    // Update recommendations
    const recommendationsDiv = document.getElementById('balanceRecommendations');
    recommendationsDiv.innerHTML = analysis.recommendations
        .map(rec => `<div class="mb-1">• ${rec}</div>`)
        .join('');
}