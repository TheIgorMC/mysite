// Archery Analysis JavaScript

let selectedAthletes = [];
let resultsChart = null;

document.addEventListener('DOMContentLoaded', function() {
    // Load competition types and categories
    loadCompetitionTypes();
    loadCategories();
    
    // Set up event listeners
    document.getElementById('search-btn').addEventListener('click', searchAthletes);
    document.getElementById('athlete-search').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchAthletes();
        }
    });
    
    document.getElementById('analyze-btn').addEventListener('click', analyzeResults);
    
    // Category change listener
    document.getElementById('competition-category').addEventListener('change', onCategoryChange);
    
    // Initialize empty chart
    initializeChart();
});

async function loadCompetitionTypes() {
    try {
        const response = await fetch('/archery/api/competition_types');
        const types = await response.json();
        
        const select = document.getElementById('competition-type');
        types.forEach(type => {
            const option = document.createElement('option');
            option.value = type.id || type.name;
            option.textContent = type.name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading competition types:', error);
    }
}

async function loadCategories() {
    try {
        const response = await fetch('/archery/api/categories');
        const categories = await response.json();
        
        const select = document.getElementById('competition-category');
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category.id;
            option.textContent = category.name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

async function onCategoryChange() {
    const category = document.getElementById('competition-category').value;
    const typeSelect = document.getElementById('competition-type');
    
    // Clear current types
    typeSelect.innerHTML = '<option value="">All Types</option>';
    
    if (!category) {
        // Load all types if no category selected
        loadCompetitionTypes();
        return;
    }
    
    try {
        const response = await fetch(`/archery/api/category/${category}/types`);
        const types = await response.json();
        
        types.forEach(type => {
            const option = document.createElement('option');
            option.value = type.id;
            option.textContent = type.name;
            typeSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading types for category:', error);
    }
}

async function searchAthletes() {
    const searchInput = document.getElementById('athlete-search');
    const resultsDiv = document.getElementById('search-results');
    const query = searchInput.value.trim();
    
    if (query.length < 3) {
        resultsDiv.classList.add('hidden');
        return;
    }
    
    try {
        const response = await fetch(`/archery/api/search_athlete?name=${encodeURIComponent(query)}`);
        const athletes = await response.json();
        
        if (athletes.length === 0) {
            resultsDiv.innerHTML = '<p class="p-4 text-gray-500 dark:text-gray-400">No athletes found</p>';
        } else {
            resultsDiv.innerHTML = athletes.map(athlete => `
                <div class="p-3 hover:bg-gray-100 dark:hover:bg-gray-600 cursor-pointer border-b border-gray-200 dark:border-gray-600 last:border-b-0 text-gray-900 dark:text-white" 
                     onclick="selectAthlete('${athlete.id}', '${athlete.name}')">
                    <p class="font-semibold">${athlete.name}</p>
                    <p class="text-sm text-gray-600 dark:text-gray-400">ID: ${athlete.id}</p>
                </div>
            `).join('');
        }
        
        resultsDiv.classList.remove('hidden');
    } catch (error) {
        console.error('Error searching athletes:', error);
        resultsDiv.innerHTML = '<p class="p-4 text-red-500 dark:text-red-400">Error searching athletes</p>';
        resultsDiv.classList.remove('hidden');
    }
}

function selectAthlete(id, name) {
    // Check if already selected
    if (selectedAthletes.find(a => a.id === id)) {
        alert('Athlete already selected');
        return;
    }
    
    // Check max 5 athletes
    if (selectedAthletes.length >= 5) {
        alert('Maximum 5 athletes can be compared');
        return;
    }
    
    selectedAthletes.push({ id, name });
    updateSelectedAthletes();
    
    // Hide search results
    document.getElementById('search-results').classList.add('hidden');
    document.getElementById('athlete-search').value = '';
}

function updateSelectedAthletes() {
    const container = document.getElementById('selected-athletes');
    
    if (selectedAthletes.length === 0) {
        container.innerHTML = '<p class="text-gray-400 dark:text-gray-500 text-sm">Add athletes to compare</p>';
        return;
    }
    
    container.innerHTML = selectedAthletes.map((athlete, index) => `
        <div class="flex items-center justify-between bg-primary/10 dark:bg-primary/20 px-3 py-2 rounded">
            <span class="font-medium text-gray-900 dark:text-white">${athlete.name}</span>
            <button onclick="removeAthlete(${index})" 
                    class="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `).join('');
}

function removeAthlete(index) {
    selectedAthletes.splice(index, 1);
    updateSelectedAthletes();
}

async function analyzeResults() {
    if (selectedAthletes.length === 0) {
        alert('Please select at least one athlete');
        return;
    }
    
    const competitionType = document.getElementById('competition-type').value;
    const category = document.getElementById('competition-category').value;
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;
    const includeAverage = document.getElementById('include-average').checked;
    
    const chartCanvas = document.getElementById('results-chart');
    const chartContainer = chartCanvas.parentElement;
    
    try {
        showLoading(chartContainer);
        
        // Fetch results for all selected athletes
        const resultsPromises = selectedAthletes.map(athlete => 
            fetchAthleteResults(athlete.id, competitionType, category, startDate, endDate, includeAverage)
        );
        
        const allResults = await Promise.all(resultsPromises);
        
        // Restore canvas
        chartContainer.innerHTML = '<canvas id="results-chart"></canvas>';
        
        // Reinitialize chart after canvas recreation
        initializeChart();
        
        // Update chart with data
        updateChart(allResults, includeAverage);
        
        // Load statistics for first athlete
        if (selectedAthletes.length === 1) {
            loadStatistics(selectedAthletes[0].id);
        }
    } catch (error) {
        console.error('Error analyzing results:', error);
        showError(chartContainer, 'Error loading results. Please try again.');
    }
}

async function fetchAthleteResults(athleteId, competitionType, category, startDate, endDate, includeAverage) {
    let url = `/archery/api/athlete/${athleteId}/results?`;
    if (competitionType) url += `competition_type=${encodeURIComponent(competitionType)}&`;
    if (category) url += `category=${encodeURIComponent(category)}&`;
    if (startDate) url += `start_date=${startDate}&`;
    if (endDate) url += `end_date=${endDate}&`;
    if (includeAverage) url += `include_average=true&`;
    
    const response = await fetch(url);
    const data = await response.json();
    
    return {
        athleteId,
        athleteName: selectedAthletes.find(a => a.id === athleteId).name,
        results: data,
        includeAverage
    };
}

function initializeChart() {
    const ctx = document.getElementById('results-chart');
    
    // Detect dark mode
    const isDarkMode = document.documentElement.classList.contains('dark');
    const textColor = isDarkMode ? '#e5e7eb' : '#1f2937';
    const gridColor = isDarkMode ? '#374151' : '#d1d5db';
    const backgroundColor = isDarkMode ? 'transparent' : '#ffffff';
    
    resultsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: []
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            backgroundColor: backgroundColor,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: textColor,
                        font: {
                            size: 12
                        }
                    }
                },
                title: {
                    display: true,
                    text: 'Competition Results Over Time',
                    color: textColor,
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Score',
                        color: textColor,
                        font: {
                            weight: 'bold'
                        }
                    },
                    ticks: {
                        color: textColor
                    },
                    grid: {
                        color: gridColor,
                        drawBorder: true,
                        borderColor: gridColor
                    }
                },
                x: {
                    ticks: {
                        color: textColor
                    },
                    grid: {
                        color: gridColor,
                        drawBorder: true,
                        borderColor: gridColor
                    }
                }
            }
        }
    });
}

// Reinitialize chart when theme changes
document.addEventListener('DOMContentLoaded', function() {
    // Watch for theme changes
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.attributeName === 'class') {
                // Theme changed, reinitialize chart if it exists
                if (resultsChart) {
                    const hasData = resultsChart.data.datasets.length > 0;
                    const oldData = {
                        labels: resultsChart.data.labels,
                        datasets: resultsChart.data.datasets
                    };
                    
                    resultsChart.destroy();
                    initializeChart();
                    
                    if (hasData) {
                        resultsChart.data.labels = oldData.labels;
                        resultsChart.data.datasets = oldData.datasets;
                        resultsChart.update();
                    }
                }
            }
        });
    });
    
    observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['class']
    });
});

function updateChart(allResults, includeAverage = false) {
    // Subtle colors that work well in dark mode
    const isDarkMode = document.documentElement.classList.contains('dark');
    const colors = isDarkMode ? [
        'rgb(167, 139, 250)',  // light purple
        'rgb(251, 146, 60)',   // orange
        'rgb(96, 165, 250)',   // light blue
        'rgb(52, 211, 153)',   // emerald
        'rgb(251, 113, 133)'   // pink
    ] : [
        'rgb(124, 58, 237)',   // purple
        'rgb(249, 115, 22)',   // orange
        'rgb(59, 130, 246)',   // blue
        'rgb(16, 185, 129)',   // green
        'rgb(236, 72, 153)'    // pink
    ];
    
    const datasets = allResults.map((athleteData, index) => {
        const sortedResults = athleteData.results.sort((a, b) => 
            new Date(a.date) - new Date(b.date)
        );
        
        // Use average per arrow if checkbox is checked and data is available
        const dataPoints = includeAverage && sortedResults[0]?.average_per_arrow !== undefined
            ? sortedResults.map(r => r.average_per_arrow)
            : sortedResults.map(r => r.score);
        
        return {
            label: athleteData.athleteName,
            data: dataPoints,
            borderColor: colors[index % colors.length],
            backgroundColor: colors[index % colors.length] + '20',
            tension: 0.1,
            borderWidth: 2
        };
    });
    
    // Use dates from first athlete as labels
    const labels = allResults[0]?.results
        .sort((a, b) => new Date(a.date) - new Date(b.date))
        .map(r => new Date(r.date).toLocaleDateString('it-IT'));
    
    // Update Y-axis label based on what we're showing
    const yAxisLabel = includeAverage ? 'Average per Arrow' : 'Score';
    
    resultsChart.data.labels = labels;
    resultsChart.data.datasets = datasets;
    resultsChart.options.scales.y.title.text = yAxisLabel;
    resultsChart.update();
}

async function loadStatistics(athleteId) {
    try {
        const response = await fetch(`/archery/api/athlete/${athleteId}/statistics`);
        const stats = await response.json();
        
        const statsSection = document.getElementById('statistics-section');
        const statsGrid = document.getElementById('statistics-grid');
        
        statsGrid.innerHTML = `
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 class="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">Total Competitions</h3>
                <p class="text-4xl font-bold text-primary">${stats.total_competitions || 0}</p>
            </div>
            
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 class="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">Medals</h3>
                <div class="space-y-2">
                    <p class="text-lg"><span class="font-bold text-yellow-500">🥇</span> ${stats.gold_medals || 0}</p>
                    <p class="text-lg"><span class="font-bold text-gray-400">🥈</span> ${stats.silver_medals || 0}</p>
                    <p class="text-lg"><span class="font-bold text-orange-600">🥉</span> ${stats.bronze_medals || 0}</p>
                </div>
            </div>
            
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 class="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">Average Position</h3>
                <p class="text-4xl font-bold text-accent">${stats.avg_position ? stats.avg_position.toFixed(1) : 'N/A'}</p>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-2">Top ${stats.avg_percentile || 'N/A'}%</p>
            </div>
            
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 class="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">Best Score</h3>
                <p class="text-4xl font-bold text-primary">${stats.best_score || 'N/A'}</p>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-2">${stats.best_score_competition || ''}</p>
            </div>
        `;
        
        statsSection.classList.remove('hidden');
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}
