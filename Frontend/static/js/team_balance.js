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
        
        console.log('Player info object:', playerData.info);
        console.log('Date of birth/age:', playerData.info?.['date_of_birth/age']);
        
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
    try {
        const selectedPlayers = Array.from(document.querySelectorAll('#selectedPlayers .player-card'))
            .map(card => ({
                'Full name': card.querySelector('.player-name').textContent,
                'Date of birth/Age': card.dataset.age || '',
                // Add other relevant fields
            }));

        if (selectedPlayers.length === 0) {
            alert('Please select players to analyze');
            return;
        }

        const response = await fetch('http://127.0.0.1:8000/api/analyze-team-balance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(selectedPlayers)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const analysis = await response.json();
        displayAnalysis(analysis);
    } catch (error) {
        console.error('Error analyzing team:', error);
        alert('Error analyzing team. Please try again.');
    }
}

function extractAgeFromString(dateString) {
    if (!dateString) return null;
    // Match pattern like "Jun 24, 1987 (37)"
    const ageMatch = dateString.match(/\((\d+)\)/);
    return ageMatch ? parseInt(ageMatch[1]) : null;
}

function displayAnalysis(data) {
    if (!data || !data.analysis) {
        console.error('Invalid analysis data received');
        return;
    }
    
    const analysis = data.analysis;
    document.getElementById('analysisResults').style.display = 'block';
    
    // Extract ages from the date_of_birth/age string in info object
    const ages = selectedPlayers.map(player => {
        console.log('Processing player:', player.name);
        const dobString = player.info?.['date_of_birth/age'];
        console.log('Date of birth string found:', dobString);
        
        // Try to extract age from the string
        const age = extractAgeFromString(dobString);
        console.log('Extracted age:', age);
        return age;
    });
    
    console.log('All extracted ages:', ages);
    
    // Filter out any null values and calculate metrics
    const validAges = ages.filter(age => age !== null);
    const averageAge = validAges.length 
        ? (validAges.reduce((a, b) => a + b, 0) / validAges.length).toFixed(1) 
        : 0;
    const ageSpread = validAges.length 
        ? (Math.max(...validAges) - Math.min(...validAges)).toFixed(1) 
        : 0;

    console.log('Valid ages:', validAges);
    console.log('Average age:', averageAge);
    console.log('Age spread:', ageSpread);

    // Update the analysis with calculated age metrics
    analysis.squad_metrics = {
        ...analysis.squad_metrics,
        average_age: averageAge,
        age_spread: ageSpread
    };
    
    displaySquadMetrics(analysis.squad_metrics);
    displayBalanceScores(analysis.balance_scores);
    displayDistributionCharts(analysis);
    displayRecommendations(analysis.recommendations);
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

