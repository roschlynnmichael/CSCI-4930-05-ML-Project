// Team Balance Analyzer JavaScript

const BACKEND_URL = 'http://127.0.0.1:8000';

let selectedPlayers = [];
let ageChart = null;
let phaseChart = null;

document.addEventListener('DOMContentLoaded', function() {
    const playerSearch = document.getElementById('playerSearch');
    const analyzeButton = document.getElementById('analyzeTeam');

    // Player search functionality
    playerSearch.addEventListener('input', debounce(searchPlayers, 300));
    
    // Analyze team button
    analyzeButton.addEventListener('click', analyzeTeam);
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
        playerDiv.className = 'glass-card p-3 hover:scale-[1.02] transition-all duration-300';
        playerDiv.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    <img src="${player.image_url}" class="w-10 h-10 rounded-full object-cover" alt="${player.name}">
                    <span class="font-medium text-gray-800">${player.name}</span>
                </div>
                <button onclick="addPlayer('${player.id}')" 
                        class="px-3 py-1 bg-gradient-to-r from-indigo-600 to-emerald-600 text-white rounded-lg hover:from-indigo-700 hover:to-emerald-700 transition-all duration-300">
                    Add
                </button>
            </div>
        `;
        resultsDiv.appendChild(playerDiv);
    });
}

async function addPlayer(playerId) {
    try {
        const response = await fetch(`${BACKEND_URL}/api/player/${playerId}`);
        const playerData = await response.json();
        
        if (!selectedPlayers.find(p => p.id === playerData.id)) {
            selectedPlayers.push(playerData);
            updateSelectedPlayersList();
        }
    } catch (error) {
        console.error('Error adding player:', error);
    }
}

function updateSelectedPlayersList() {
    const selectedPlayersDiv = document.getElementById('selectedPlayers');
    selectedPlayersDiv.innerHTML = '';

    selectedPlayers.forEach(player => {
        const playerDiv = document.createElement('div');
        playerDiv.className = 'glass-card p-3 hover:scale-[1.02] transition-all duration-300';
        playerDiv.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    <img src="${player.image_url}" class="w-10 h-10 rounded-full object-cover" alt="${player.name}">
                    <span class="font-medium text-gray-800">${player.name}</span>
                </div>
                <button onclick="removePlayer('${player.id}')" 
                        class="px-3 py-1 bg-gradient-to-r from-red-600 to-red-700 text-white rounded-lg hover:from-red-700 hover:to-red-800 transition-all duration-300">
                    Remove
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
        alert('Please select players for analysis');
        return;
    }

    try {
        const response = await fetch(`${BACKEND_URL}/api/analyze-team-balance`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(selectedPlayers)
        });

        const analysis = await response.json();
        displayAnalysis(analysis);
    } catch (error) {
        console.error('Error analyzing team:', error);
        alert('Error analyzing team balance');
    }
}

function displayAnalysis(data) {
    if (!data || !data.analysis) {
        console.error('Invalid analysis data received');
        return;
    }
    
    const analysis = data.analysis;
    document.getElementById('analysisResults').style.display = 'block';
    
    // Display squad metrics
    displaySquadMetrics(analysis.squad_metrics);
    
    // Display balance scores
    displayBalanceScores(analysis.balance_scores);
    
    // Display distributions
    displayDistributionCharts(analysis);
    
    // Display recommendations
    displayRecommendations(analysis.recommendations);
}

// ... (continue with display helper functions)
function displaySquadMetrics(metrics) {
    const metricsDiv = document.getElementById('squadMetrics');
    metricsDiv.innerHTML = `
        <div class="space-y-3">
            ${Object.entries(metrics).map(([key, value]) => `
                <div class="glass-card p-4 hover:scale-[1.02] transition-all duration-300">
                    <div class="flex justify-between items-center">
                        <span class="text-gray-600">${formatMetricLabel(key)}</span>
                        <span class="font-semibold ${getMetricValueClass(key, value)}">${value}</span>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

function displayBalanceScores(scores) {
    const scoresDiv = document.getElementById('balanceScores');
    scoresDiv.innerHTML = `
        <div class="space-y-4">
            ${Object.entries(scores).map(([key, value]) => `
                <div class="glass-card p-4">
                    <div class="flex justify-between items-center mb-2">
                        <span class="text-gray-600">${formatScoreLabel(key)}</span>
                        <span class="font-semibold">${(value * 100).toFixed(1)}%</span>
                    </div>
                    <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div class="h-full ${getProgressBarClass(value)} transition-all duration-500"
                             style="width: ${value * 100}%"></div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

function displayDistributionCharts(analysis) {
    // Age Distribution Chart
    const ageCtx = document.getElementById('ageChart').getContext('2d');
    if (ageChart) ageChart.destroy();
    
    ageChart = new Chart(ageCtx, {
        type: 'bar',
        data: {
            labels: ['U21', '21-25', '26-29', '30+'],
            datasets: [{
                label: 'Current',
                data: Object.values(analysis.age_analysis.current),
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }, {
                label: 'Ideal',
                data: Object.values(analysis.age_analysis.gaps).map((gap, i) => 
                    Object.values(analysis.age_analysis.current)[i] + gap),
                type: 'line',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 2,
                fill: false
            }]
        },
        options: getChartOptions('Age Distribution')
    });

    // Phase Distribution Chart
    const phaseCtx = document.getElementById('phaseChart').getContext('2d');
    if (phaseChart) phaseChart.destroy();
    
    phaseChart = new Chart(phaseCtx, {
        type: 'bar',
        data: {
            labels: ['Breakthrough', 'Development', 'Peak', 'Twilight'],
            datasets: [{
                label: 'Current',
                data: Object.values(analysis.phase_analysis.current),
                backgroundColor: 'rgba(75, 192, 192, 0.5)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }, {
                label: 'Ideal',
                data: Object.values(analysis.phase_analysis.gaps).map((gap, i) => 
                    Object.values(analysis.phase_analysis.current)[i] + gap),
                type: 'line',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 2,
                fill: false
            }]
        },
        options: getChartOptions('Career Phase Distribution')
    });
}

function displayRecommendations(recommendations) {
    const recsDiv = document.getElementById('recommendations');
    if (recommendations.length === 0) {
        recsDiv.innerHTML = `
            <div class="glass-card p-4 bg-emerald-50">
                <div class="flex items-center text-emerald-700">
                    <svg class="h-5 w-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                    </svg>
                    No immediate actions required
                </div>
            </div>
        `;
        return;
    }

    recsDiv.innerHTML = `
        <div class="space-y-3">
            ${recommendations.map(rec => `
                <div class="glass-card p-4 hover:scale-[1.02] transition-all duration-300">
                    <div class="flex items-start">
                        <svg class="h-5 w-5 mr-3 text-indigo-600 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
                        </svg>
                        <span class="text-gray-700">${rec}</span>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

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

