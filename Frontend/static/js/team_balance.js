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
        playerDiv.className = 'player-result p-2 border-bottom';
        playerDiv.innerHTML = `
            <div class="d-flex align-items-center">
                <img src="${player.image_url}" class="mr-2" style="width: 30px; height: 30px;">
                <span>${player.name}</span>
                <button class="btn btn-sm btn-primary ml-auto" onclick="addPlayer('${player.id}')">Add</button>
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
        playerDiv.className = 'list-group-item d-flex justify-content-between align-items-center';
        playerDiv.innerHTML = `
            <div>
                <img src="${player.image_url}" style="width: 30px; height: 30px;">
                ${player.name}
            </div>
            <button class="btn btn-sm btn-danger" onclick="removePlayer('${player.id}')">Remove</button>
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
        <div class="list-group">
            <div class="list-group-item d-flex justify-content-between align-items-center">
                <span>Total Players</span>
                <span class="badge bg-primary rounded-pill">${metrics.total_players}</span>
            </div>
            <div class="list-group-item d-flex justify-content-between align-items-center">
                <span>Average Age</span>
                <span class="badge bg-primary rounded-pill">${metrics.average_age}</span>
            </div>
            <div class="list-group-item d-flex justify-content-between align-items-center">
                <span>Age Spread</span>
                <span class="badge bg-primary rounded-pill">${metrics.age_spread}</span>
            </div>
            <div class="list-group-item d-flex justify-content-between align-items-center">
                <span>Squad Size Status</span>
                <span class="badge ${getStatusBadgeClass(metrics.squad_size_status)}">${metrics.squad_size_status}</span>
            </div>
        </div>
    `;
}

function displayBalanceScores(scores) {
    const scoresDiv = document.getElementById('balanceScores');
    scoresDiv.innerHTML = `
        <div class="list-group">
            <div class="list-group-item">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <span>Age Balance</span>
                    <span>${(scores.age_balance * 100).toFixed(1)}%</span>
                </div>
                <div class="progress">
                    <div class="progress-bar ${getProgressBarClass(scores.age_balance)}" 
                         role="progressbar" 
                         style="width: ${scores.age_balance * 100}%">
                    </div>
                </div>
            </div>
            <div class="list-group-item">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <span>Phase Balance</span>
                    <span>${(scores.phase_balance * 100).toFixed(1)}%</span>
                </div>
                <div class="progress">
                    <div class="progress-bar ${getProgressBarClass(scores.phase_balance)}" 
                         role="progressbar" 
                         style="width: ${scores.phase_balance * 100}%">
                    </div>
                </div>
            </div>
            <div class="list-group-item">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <span>Overall Balance</span>
                    <span>${(scores.overall_balance * 100).toFixed(1)}%</span>
                </div>
                <div class="progress">
                    <div class="progress-bar ${getProgressBarClass(scores.overall_balance)}" 
                         role="progressbar" 
                         style="width: ${scores.overall_balance * 100}%">
                    </div>
                </div>
            </div>
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
        recsDiv.innerHTML = '<div class="alert alert-success">No immediate actions required.</div>';
        return;
    }

    recsDiv.innerHTML = `
        <ul class="list-group">
            ${recommendations.map(rec => `
                <li class="list-group-item">
                    <i class="fas fa-info-circle text-primary me-2"></i>
                    ${rec}
                </li>
            `).join('')}
        </ul>
    `;
}

// Helper functions
function getStatusBadgeClass(status) {
    if (status.includes('Optimal')) return 'bg-success';
    if (status.includes('too small')) return 'bg-warning';
    return 'bg-danger';
}

function getProgressBarClass(score) {
    if (score >= 0.8) return 'bg-success';
    if (score >= 0.6) return 'bg-warning';
    return 'bg-danger';
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
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                ticks: {
                    format: {
                        style: 'percent'
                    }
                }
            }
        }
    };
}

