// Archery Analysis JavaScript

let selectedAthletes = [];
let resultsChart = null;
let currentTab = 'stats';

document.addEventListener('DOMContentLoaded', function() {
    // Load competition types and categories
    loadCompetitionTypes();
    loadCategories();
    
    // Set up event listeners for stats tab
    document.getElementById('search-btn').addEventListener('click', searchAthletes);
    document.getElementById('athlete-search').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchAthletes();
        }
    });
    
    document.getElementById('analyze-btn').addEventListener('click', analyzeResults);
    
    // Category change listener
    document.getElementById('competition-category').addEventListener('change', onCategoryChange);
    
    // Set up event listeners for results tab
    document.getElementById('search-btn-results').addEventListener('click', searchAthletesForResults);
    document.getElementById('athlete-search-results').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchAthletesForResults();
        }
    });
    document.getElementById('load-results-btn').addEventListener('click', loadPersonalResults);
    
    // Set up event listeners for rankings tab
    document.getElementById('load-ranking-btn').addEventListener('click', loadRankingData);
    loadRankings(); // Load available rankings
    
    // Initialize empty chart
    initializeChart();
});

// Tab switching
function switchTab(tab) {
    currentTab = tab;
    
    // Update tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active', 'border-primary', 'text-primary');
        btn.classList.add('border-transparent', 'text-gray-500', 'dark:text-gray-400');
    });
    document.getElementById(`tab-${tab}`).classList.add('active', 'border-primary', 'text-primary');
    document.getElementById(`tab-${tab}`).classList.remove('border-transparent', 'text-gray-500', 'dark:text-gray-400');
    
    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.add('hidden');
    });
    document.getElementById(`${tab}-content`).classList.remove('hidden');
}


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
    typeSelect.innerHTML = `<option value="">${t('archery.all_types')}</option>`;
    
    if (!category) {
        // Load all types if no category selected
        loadCompetitionTypes();
        return;
    }
    
    try {
        // Show loading in the select
        typeSelect.innerHTML = `<option value="">${t('common.loading')}</option>`;
        typeSelect.disabled = true;
        
        const response = await fetch(`/archery/api/category/${category}/types`);
        const types = await response.json();
        
        typeSelect.innerHTML = `<option value="">${t('archery.all_types')}</option>`;
        types.forEach(type => {
            const option = document.createElement('option');
            option.value = type.id;
            option.textContent = type.name;
            typeSelect.appendChild(option);
        });
        
        typeSelect.disabled = false;
    } catch (error) {
        console.error('Error loading types for category:', error);
        typeSelect.innerHTML = `<option value="">${t('errors.loading_types')}</option>`;
        setTimeout(() => {
            typeSelect.innerHTML = `<option value="">${t('archery.all_types')}</option>`;
            typeSelect.disabled = false;
        }, 2000);
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
        // Show loading state
        resultsDiv.innerHTML = `
            <div class="p-4 flex items-center justify-center">
                <div class="w-6 h-6 border-2 border-gray-300 dark:border-gray-600 border-t-primary rounded-full animate-spin mr-2"></div>
                <span class="text-gray-600 dark:text-gray-400 text-sm">${t('common.searching')}</span>
            </div>
        `;
        resultsDiv.classList.remove('hidden');
        
        const response = await fetch(`/archery/api/search_athlete?name=${encodeURIComponent(query)}`);
        const athletes = await response.json();
        
        if (athletes.length === 0) {
            resultsDiv.innerHTML = `<p class="p-4 text-gray-500 dark:text-gray-400">${t('messages.no_athletes_found')}</p>`;
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
        resultsDiv.innerHTML = `
            <div class="p-4 text-red-500 dark:text-red-400 flex items-center">
                <i class="fas fa-exclamation-circle mr-2"></i>
                <span>${t('errors.searching_athletes')}</span>
            </div>
        `;
        resultsDiv.classList.remove('hidden');
    }
}

function selectAthlete(id, name) {
    // Check if already selected
    if (selectedAthletes.find(a => a.id === id)) {
        showNotification(t('messages.athlete_already_selected'), 'warning');
        return;
    }
    
    // Check max 5 athletes
    if (selectedAthletes.length >= 5) {
        showNotification(t('messages.max_athletes'), 'warning');
        return;
    }
    
    selectedAthletes.push({ id, name });
    updateSelectedAthletes();
    
    // Hide search results
    document.getElementById('search-results').classList.add('hidden');
    document.getElementById('athlete-search').value = '';
    
    // If athletes were already analyzed, re-run analysis with new athlete
    if (resultsChart && resultsChart.data.datasets.length > 0) {
        analyzeResults();
    }
}

function updateSelectedAthletes() {
    const container = document.getElementById('selected-athletes');
    
    if (selectedAthletes.length === 0) {
        container.innerHTML = `<p class="text-gray-400 dark:text-gray-500 text-sm">${t('messages.add_athletes_to_compare')}</p>`;
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
    
    // If athletes were already analyzed, re-run analysis
    if (resultsChart && resultsChart.data.datasets.length > 0) {
        if (selectedAthletes.length > 0) {
            analyzeResults();
        } else {
            // Clear chart and stats if no athletes left
            resultsChart.data.labels = [];
            resultsChart.data.datasets = [];
            resultsChart.update();
            document.getElementById('statistics-section').classList.add('hidden');
            hideResetZoomButton();
        }
    }
}

async function analyzeResults() {
    if (selectedAthletes.length === 0) {
        showNotification(t('messages.select_at_least_one'), 'warning');
        return;
    }
    
    const competitionType = document.getElementById('competition-type').value;
    const category = document.getElementById('competition-category').value;
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;
    const includeAverage = document.getElementById('include-average').checked;
    
    const chartCanvas = document.getElementById('results-chart');
    const chartContainer = chartCanvas.parentElement;
    const statsSection = document.getElementById('statistics-section');
    const statsGrid = document.getElementById('statistics-grid');
    
    try {
        // Show loading for chart
        showLoading(chartContainer, t('messages.loading_competition_results'));
        
        // Show loading for statistics
        statsSection.classList.remove('hidden');
        showLoading(statsGrid, t('messages.loading_statistics'));
        
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
        
        // Load statistics - different behavior for single vs multiple athletes
        if (selectedAthletes.length === 1) {
            // Single athlete: show detailed statistics with career and filtered
            await loadStatistics(selectedAthletes[0].id, competitionType, category, startDate, endDate);
        } else {
            // Multiple athletes: show comparison statistics
            await loadComparisonStatistics(selectedAthletes, competitionType, category, startDate, endDate);
        }
    } catch (error) {
        console.error('Error analyzing results:', error);
        showError(chartContainer, `${t('errors.loading_results')}. ${t('common.please_try_again')}`);
        showError(statsGrid, `${t('errors.loading_statistics')}. ${t('common.please_try_again')}`);
    }
}

async function fetchAthleteResults(athleteId, competitionType, category, startDate, endDate, includeAverage) {
    // Call the Flask backend results endpoint. The backend will call the external API and return
    // a normalized array of result objects.
    let url = `/archery/api/athlete/${athleteId}/results?`;
    if (competitionType) url += `competition_type=${encodeURIComponent(competitionType)}&`;
    if (category) url += `category=${encodeURIComponent(category)}&`;
    if (startDate) url += `start_date=${startDate}&`;
    if (endDate) url += `end_date=${endDate}&`;
    if (includeAverage) url += `include_average=true&`;

    // Trim trailing separators
    url = url.replace(/[&?]+$/g, '');

    const response = await fetch(url);

    if (!response.ok) {
        // Try to extract JSON error or plain text for better debugging
        let details = '';
        try {
            details = JSON.stringify(await response.json());
        } catch (e) {
            try { details = await response.text(); } catch (e2) { details = '<unreadable response>'; }
        }
        console.error('Error fetching athlete results', response.status, details);
        throw new Error(`HTTP error ${response.status}: ${details}`);
    }

    // Ensure we parse JSON safely
    let data;
    try {
        data = await response.json();
    } catch (err) {
        console.error('Invalid JSON from results endpoint', err);
        const txt = await response.text().catch(() => '<no body>');
        console.error('Raw response:', txt.substring(0, 400));
        throw new Error('Invalid JSON in response from server');
    }

    // The backend returns either an array of results or an object with 'error'
    if (data && data.error) {
        const details = data.details ? `: ${data.details}` : '';
        throw new Error(`Server error: ${data.error}${details}`);
    }

    if (!Array.isArray(data)) {
        console.error('Unexpected payload for athlete results:', data);
        throw new Error('Unexpected response format from server');
    }

    return {
        athleteId,
        athleteName: (selectedAthletes.find(a => a.id === athleteId) || {}).name || 'Unknown',
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
                    text: t('archery.competition_results'),
                    color: textColor,
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                zoom: {
                    pan: {
                        enabled: true,
                        mode: 'xy',
                        modifierKey: 'ctrl',
                    },
                    zoom: {
                        wheel: {
                            enabled: true,
                            speed: 0.1
                        },
                        pinch: {
                            enabled: true
                        },
                        mode: 'xy',
                    },
                    limits: {
                        x: {min: 'original', max: 'original'},
                        y: {min: 'original', max: 'original'}
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: t('archery.score'),
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
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
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
    
    // Helper function to normalize date strings to YYYY-MM-DD format
    const normalizeDate = (dateStr) => {
        if (!dateStr) return null;
        
        try {
            // Handle various date formats: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, etc.
            let date;
            
            if (dateStr.includes('/')) {
                // Format like DD/MM/YYYY or MM/DD/YYYY
                const parts = dateStr.split('/');
                if (parts.length === 3) {
                    // Assume DD/MM/YYYY (Italian format)
                    date = new Date(parts[2], parts[1] - 1, parts[0]);
                }
            } else if (dateStr.includes('-')) {
                // Format like YYYY-MM-DD or DD-MM-YYYY
                const parts = dateStr.split('-');
                if (parts.length === 3) {
                    if (parts[0].length === 4) {
                        // YYYY-MM-DD format
                        date = new Date(dateStr);
                    } else {
                        // DD-MM-YYYY format
                        date = new Date(parts[2], parts[1] - 1, parts[0]);
                    }
                }
            } else {
                // Try to parse as-is
                date = new Date(dateStr);
            }
            
            // Validate date
            if (date && !isNaN(date.getTime())) {
                // Return as YYYY-MM-DD for consistent sorting
                const year = date.getFullYear();
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const day = String(date.getDate()).padStart(2, '0');
                return `${year}-${month}-${day}`;
            }
        } catch (e) {
            console.error('Error parsing date:', dateStr, e);
        }
        
        return null;
    };
    
    // Format date for display
    const formatDateForDisplay = (normalizedDate) => {
        if (!normalizedDate) return 'Invalid Date';
        const date = new Date(normalizedDate);
        return date.toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit', year: 'numeric' });
    };
    
    // Collect all unique dates from all athletes and sort them
    const allDates = new Set();
    allResults.forEach(athleteData => {
        athleteData.results.forEach(result => {
            const normalized = normalizeDate(result.date);
            if (normalized) {
                allDates.add(normalized);
            }
        });
    });
    
    // Sort all unique dates chronologically
    const sortedDates = Array.from(allDates).sort();
    
    // Create datasets with data points aligned to the common date axis
    const datasets = allResults.map((athleteData, index) => {
        // Create a map of date -> value for this athlete
        const athleteDateMap = new Map();
        athleteData.results.forEach(result => {
            const normalized = normalizeDate(result.date);
            if (normalized) {
                const value = includeAverage && result.average_per_arrow !== undefined
                    ? result.average_per_arrow
                    : result.score;
                athleteDateMap.set(normalized, value);
            }
        });
        
        // Create data array aligned with sortedDates (null for missing dates)
        const dataPoints = sortedDates.map(date => athleteDateMap.get(date) || null);
        
        return {
            label: athleteData.athleteName,
            data: dataPoints,
            borderColor: colors[index % colors.length],
            backgroundColor: colors[index % colors.length] + '20',
            tension: 0.1,
            borderWidth: 2,
            spanGaps: true // Connect line across null values
        };
    });
    
    // Format dates for display
    const labels = sortedDates.map(formatDateForDisplay);
    
    // Update Y-axis label based on what we're showing
    const yAxisLabel = includeAverage ? t('archery.average_per_arrow') : t('archery.score');
    
    resultsChart.data.labels = labels;
    resultsChart.data.datasets = datasets;
    resultsChart.options.scales.y.title.text = yAxisLabel;
    resultsChart.update();
    
    // Show reset zoom button when chart has data
    showResetZoomButton();
}

async function loadStatistics(athleteId, competitionType, category, startDate, endDate) {
    try {
        // Build URL with filters
        let url = `/archery/api/athlete/${athleteId}/statistics?`;
        if (competitionType) url += `competition_type=${encodeURIComponent(competitionType)}&`;
        if (category) url += `category=${encodeURIComponent(category)}&`;
        if (startDate) url += `start_date=${startDate}&`;
        if (endDate) url += `end_date=${endDate}&`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        const statsSection = document.getElementById('statistics-section');
        const statsGrid = document.getElementById('statistics-grid');
        
        const hasFilters = competitionType || category || startDate || endDate;
        const career = data.career;
        const filtered = data.filtered;
        
        // Helper function to create a stat card
        const createStatCard = (title, value, subtitle = '', type = 'career') => {
            const bgClass = type === 'filtered' ? 'bg-accent/10 dark:bg-accent/20 border-2 border-accent' : '';
            const badge = type === 'filtered' ? '<span class="text-xs bg-accent text-white px-2 py-1 rounded-full ml-2">Filtered</span>' : '';
            return `
                <div class="bg-white dark:bg-gray-800 ${bgClass} rounded-lg shadow-lg p-6">
                    <h3 class="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">
                        ${title}${badge}
                    </h3>
                    <p class="text-4xl font-bold text-primary">${value}</p>
                    ${subtitle ? `<p class="text-sm text-gray-500 dark:text-gray-400 mt-2">${subtitle}</p>` : ''}
                </div>
            `;
        };
        
        let careerHtml = `<div class="col-span-full mb-4"><h3 class="text-xl font-bold text-gray-900 dark:text-white">${t('archery.career_statistics')}</h3></div>`;
        
        // Career Statistics
        careerHtml += createStatCard(t('archery.total_competitions'), career.total_competitions || 0, '', 'career');
        
        careerHtml += createStatCard(t('archery.medals'), 
            `<div class="space-y-2">
                <p class="text-lg"><span class="font-bold text-yellow-500">🥇</span> ${career.gold_medals || 0}</p>
                <p class="text-lg"><span class="font-bold text-gray-400">🥈</span> ${career.silver_medals || 0}</p>
                <p class="text-lg"><span class="font-bold text-orange-600">🥉</span> ${career.bronze_medals || 0}</p>
            </div>`, '', 'career');
        
        careerHtml += createStatCard(t('archery.avg_position'), 
            career.avg_position ? career.avg_position.toFixed(1) : 'N/A',
            `${t('archery.top_percent')} ${career.avg_percentile || 'N/A'}%`, 'career');
        
        careerHtml += createStatCard(t('archery.best_score'), 
            career.best_score || 'N/A',
            career.best_score_competition || '', 'career');
        
        // Filtered Statistics (if filters are applied)
        let filteredHtml = '';
        if (hasFilters && filtered) {
            filteredHtml += `<div class="col-span-full mt-6 mb-4 border-t-2 border-gray-300 dark:border-gray-600 pt-4"><h3 class="text-xl font-bold text-accent dark:text-accent">${t('archery.filtered_statistics')}</h3></div>`;
            
            filteredHtml += createStatCard(t('archery.competitions_short'), filtered.total_competitions || 0, '', 'filtered');
            
            filteredHtml += createStatCard(t('archery.medals'),
                `<div class="space-y-2">
                    <p class="text-lg"><span class="font-bold text-yellow-500">🥇</span> ${filtered.gold_medals || 0}</p>
                    <p class="text-lg"><span class="font-bold text-gray-400">🥈</span> ${filtered.silver_medals || 0}</p>
                    <p class="text-lg"><span class="font-bold text-orange-600">🥉</span> ${filtered.bronze_medals || 0}</p>
                </div>`, '', 'filtered');
            
            filteredHtml += createStatCard(t('archery.avg_pos_short'),
                filtered.avg_position ? filtered.avg_position.toFixed(1) : 'N/A',
                `${t('archery.top_percent')} ${filtered.avg_percentile || 'N/A'}%`, 'filtered');
            
            filteredHtml += createStatCard(t('archery.best_score'),
                filtered.best_score || 'N/A',
                filtered.best_score_competition || '', 'filtered');
        }
        
        statsGrid.innerHTML = careerHtml + filteredHtml;
        statsSection.classList.remove('hidden');
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

async function loadComparisonStatistics(athletes, competitionType, category, startDate, endDate) {
    try {
        // Build URL with filters for each athlete
        const statsPromises = athletes.map(athlete => {
            let url = `/archery/api/athlete/${athlete.id}/statistics?`;
            if (competitionType) url += `competition_type=${encodeURIComponent(competitionType)}&`;
            if (category) url += `category=${encodeURIComponent(category)}&`;
            if (startDate) url += `start_date=${startDate}&`;
            if (endDate) url += `end_date=${endDate}&`;
            return fetch(url).then(r => r.json()).then(data => ({ ...data, athleteName: athlete.name }));
        });
        
        const allStats = await Promise.all(statsPromises);
        
        const statsSection = document.getElementById('statistics-section');
        const statsGrid = document.getElementById('statistics-grid');
        
        const hasFilters = competitionType || category || startDate || endDate;
        
        // Create comparison table
        let html = `
            <div class="col-span-full">
                <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-4">
                    ${hasFilters ? t('archery.filtered_comparison') : t('archery.career_comparison')}
                </h3>
                <div class="overflow-x-auto">
                    <table class="w-full text-sm text-left text-gray-700 dark:text-gray-300">
                        <thead class="text-xs uppercase bg-gray-200 dark:bg-gray-700">
                            <tr>
                                <th class="px-4 py-3">${t('archery.athlete')}</th>
                                <th class="px-4 py-3 text-center">${t('archery.competitions_short')}</th>
                                <th class="px-4 py-3 text-center">🥇</th>
                                <th class="px-4 py-3 text-center">🥈</th>
                                <th class="px-4 py-3 text-center">🥉</th>
                                <th class="px-4 py-3 text-center">${t('archery.avg_pos_short')}</th>
                                <th class="px-4 py-3 text-center">${t('archery.best_score')}</th>
                            </tr>
                        </thead>
                        <tbody>
        `;
        
        allStats.forEach((athleteStats, index) => {
            const stats = hasFilters && athleteStats.filtered ? athleteStats.filtered : athleteStats.career;
            const bgClass = index % 2 === 0 ? 'bg-white dark:bg-gray-800' : 'bg-gray-50 dark:bg-gray-750';
            
            html += `
                <tr class="${bgClass} border-b dark:border-gray-700">
                    <td class="px-4 py-3 font-semibold">${athleteStats.athleteName}</td>
                    <td class="px-4 py-3 text-center">${stats.total_competitions || 0}</td>
                    <td class="px-4 py-3 text-center text-yellow-500 font-bold">${stats.gold_medals || 0}</td>
                    <td class="px-4 py-3 text-center text-gray-400 font-bold">${stats.silver_medals || 0}</td>
                    <td class="px-4 py-3 text-center text-orange-600 font-bold">${stats.bronze_medals || 0}</td>
                    <td class="px-4 py-3 text-center">${stats.avg_position ? stats.avg_position.toFixed(1) : 'N/A'}</td>
                    <td class="px-4 py-3 text-center font-bold text-primary">${stats.best_score || 'N/A'}</td>
                </tr>
            `;
        });
        
        html += `
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        
        // Add individual highlight cards below table
        html += `<div class="col-span-full mt-6"><h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">${t('archery.individual_highlights')}</h4></div>`;
        
        allStats.forEach(athleteStats => {
            const stats = hasFilters && athleteStats.filtered ? athleteStats.filtered : athleteStats.career;
            html += `
                <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 border-l-4 border-primary">
                    <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">${athleteStats.athleteName}</h4>
                    <div class="space-y-2 text-sm">
                        <p class="text-gray-700 dark:text-gray-300">
                            <span class="font-semibold">${t('archery.best_score')}:</span> ${stats.best_score || 'N/A'}
                            ${stats.best_score_competition ? `<br><span class="text-xs text-gray-500">${stats.best_score_competition}</span>` : ''}
                        </p>
                        <p class="text-gray-700 dark:text-gray-300">
                            <span class="font-semibold">${t('archery.performance')}:</span> 
                            ${t('archery.top_percent')} ${stats.avg_percentile || 'N/A'}% (${t('archery.avg_pos_short')}: ${stats.avg_position ? stats.avg_position.toFixed(1) : 'N/A'})
                        </p>
                        <p class="text-gray-700 dark:text-gray-300">
                            <span class="font-semibold">${t('archery.podiums')}:</span> ${stats.top_finishes || 0} ${t('archery.out_of')} ${stats.recent_competitions_analyzed || 0} ${t('archery.recent')}
                        </p>
                    </div>
                </div>
            `;
        });
        
        statsGrid.innerHTML = html;
        statsSection.classList.remove('hidden');
    } catch (error) {
        console.error('Error loading comparison statistics:', error);
    }
}

// ===== PERSONAL RESULTS TAB FUNCTIONS =====

let selectedAthleteForResults = null;

async function searchAthletesForResults() {
    const searchTerm = document.getElementById('athlete-search-results').value.trim();
    const resultsDiv = document.getElementById('search-results-athlete');
    
    if (searchTerm.length < 2) {
        resultsDiv.classList.add('hidden');
        return;
    }
    
    try {
        const response = await fetch(`/archery/api/search_athlete?name=${encodeURIComponent(searchTerm)}`);
        const athletes = await response.json();
        
        resultsDiv.innerHTML = '';
        
        if (athletes.length === 0) {
            resultsDiv.innerHTML = '<div class="p-3 text-gray-500 dark:text-gray-400">No athletes found</div>';
        } else {
            athletes.forEach(athlete => {
                const div = document.createElement('div');
                div.className = 'p-3 hover:bg-gray-100 dark:hover:bg-gray-600 cursor-pointer border-b border-gray-200 dark:border-gray-600 last:border-0';
                div.textContent = `${athlete.name} (${athlete.id})`;
                div.onclick = () => selectAthleteForResults(athlete.id, athlete.name);
                resultsDiv.appendChild(div);
            });
        }
        
        resultsDiv.classList.remove('hidden');
    } catch (error) {
        console.error('Error searching athletes:', error);
        showNotification(t('messages.error_searching'), 'error');
    }
}

function selectAthleteForResults(id, name) {
    selectedAthleteForResults = { id, name };
    document.getElementById('athlete-code-input').value = id;
    document.getElementById('search-results-athlete').classList.add('hidden');
    document.getElementById('athlete-search-results').value = name;
}

async function loadPersonalResults() {
    const athleteCode = document.getElementById('athlete-code-input').value.trim();
    
    if (!athleteCode) {
        showNotification(t('messages.enter_athlete_code'), 'warning');
        return;
    }
    
    const tableContainer = document.getElementById('results-table-container');
    const loadingDiv = document.getElementById('results-loading');
    const emptyDiv = document.getElementById('results-empty');
    const tableBody = document.getElementById('results-table-body');
    
    // Show loading
    tableContainer.classList.add('hidden');
    emptyDiv.classList.add('hidden');
    loadingDiv.classList.remove('hidden');
    
    try {
        const response = await fetch(`/archery/api/athlete/${athleteCode}/results`);
        
        if (!response.ok) {
            throw new Error('Failed to load results');
        }
        
        const data = await response.json();
        
        // Hide loading
        loadingDiv.classList.add('hidden');
        
        if (!data.results || data.results.length === 0) {
            emptyDiv.classList.remove('hidden');
            return;
        }
        
        // Set athlete name
        document.getElementById('results-athlete-name').textContent = 
            `${t('archery.results_for')}: ${data.results[0].atleta || athleteCode}`;
        
        // Populate table
        tableBody.innerHTML = '';
        data.results.forEach(result => {
            const row = document.createElement('tr');
            row.className = 'hover:bg-gray-50 dark:hover:bg-gray-700';
            row.innerHTML = `
                <td class="px-4 py-3 text-gray-900 dark:text-white">${result.codice_gara || 'N/A'}</td>
                <td class="px-4 py-3 text-gray-900 dark:text-white">${result.nome_gara || 'N/A'}</td>
                <td class="px-4 py-3 text-gray-900 dark:text-white">${result.data_gara || 'N/A'}</td>
                <td class="px-4 py-3 text-gray-900 dark:text-white">${result.luogo_gara || 'N/A'}</td>
                <td class="px-4 py-3 text-gray-900 dark:text-white font-semibold">${result.punteggio || 'N/A'}</td>
                <td class="px-4 py-3 text-gray-900 dark:text-white font-semibold">${result.posizione || 'N/A'}</td>
            `;
            tableBody.appendChild(row);
        });
        
        tableContainer.classList.remove('hidden');
        
    } catch (error) {
        console.error('Error loading personal results:', error);
        loadingDiv.classList.add('hidden');
        showNotification(t('messages.error_loading_results'), 'error');
    }
}

// ===== RANKINGS TAB FUNCTIONS =====

async function loadRankings() {
    try {
        const response = await fetch('/archery/api/ranking');
        const rankings = await response.json();
        
        const select = document.getElementById('ranking-select');
        select.innerHTML = `<option value="">${t('archery.select_ranking')}</option>`;
        
        rankings.forEach(ranking => {
            const option = document.createElement('option');
            option.value = ranking.codice;
            option.textContent = `${ranking.descrizione} (${ranking.regione})`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading rankings:', error);
        showNotification(t('messages.error_loading_rankings'), 'error');
    }
}

async function loadRankingData() {
    const rankingCode = document.getElementById('ranking-select').value;
    const className = document.getElementById('ranking-class').value;
    const division = document.getElementById('ranking-division').value;
    
    if (!rankingCode || !className || !division) {
        showNotification(t('messages.select_all_ranking_fields'), 'warning');
        return;
    }
    
    const tableContainer = document.getElementById('ranking-table-container');
    const loadingDiv = document.getElementById('ranking-loading');
    const emptyDiv = document.getElementById('ranking-empty');
    const tableBody = document.getElementById('ranking-table-body');
    
    // Show loading
    tableContainer.classList.add('hidden');
    emptyDiv.classList.add('hidden');
    loadingDiv.classList.remove('hidden');
    
    try {
        const params = new URLSearchParams({
            code: rankingCode,
            class_name: className,
            division: division
        });
        
        const response = await fetch(`/archery/api/ranking/official?${params}`);
        
        if (!response.ok) {
            throw new Error('Failed to load ranking data');
        }
        
        const data = await response.json();
        
        // Hide loading
        loadingDiv.classList.add('hidden');
        
        if (!data || data.length === 0) {
            emptyDiv.classList.remove('hidden');
            return;
        }
        
        // Set ranking title
        const rankingSelect = document.getElementById('ranking-select');
        const rankingName = rankingSelect.options[rankingSelect.selectedIndex].text;
        document.getElementById('ranking-title').textContent = 
            `${rankingName} - ${className} - ${division}`;
        
        // Populate table
        tableBody.innerHTML = '';
        data.forEach(entry => {
            const row = document.createElement('tr');
            row.className = 'hover:bg-gray-50 dark:hover:bg-gray-700';
            
            // Highlight top 3
            let rankClass = '';
            if (entry.posizione === 1) rankClass = 'bg-yellow-100 dark:bg-yellow-900';
            else if (entry.posizione === 2) rankClass = 'bg-gray-100 dark:bg-gray-700';
            else if (entry.posizione === 3) rankClass = 'bg-orange-100 dark:bg-orange-900';
            
            row.className = `hover:bg-gray-50 dark:hover:bg-gray-700 ${rankClass}`;
            
            row.innerHTML = `
                <td class="px-4 py-3 text-gray-900 dark:text-white font-bold">${entry.posizione}</td>
                <td class="px-4 py-3 text-gray-900 dark:text-white">${entry.atleta || 'N/A'}</td>
                <td class="px-4 py-3 text-gray-900 dark:text-white">${entry.societa || 'N/A'}</td>
                <td class="px-4 py-3 text-gray-900 dark:text-white">${entry.punteggio1 || '-'}</td>
                <td class="px-4 py-3 text-gray-900 dark:text-white">${entry.punteggio2 || '-'}</td>
                <td class="px-4 py-3 text-gray-900 dark:text-white font-semibold">${entry.totale || 'N/A'}</td>
                <td class="px-4 py-3 text-gray-900 dark:text-white">${entry.data_qualificazione || 'N/A'}</td>
            `;
            tableBody.appendChild(row);
        });
        
        tableContainer.classList.remove('hidden');
        
    } catch (error) {
        console.error('Error loading ranking data:', error);
        loadingDiv.classList.add('hidden');
        showNotification(t('messages.error_loading_ranking_data'), 'error');
    }
}

// Reset chart zoom function
function resetChartZoom() {
    if (resultsChart) {
        resultsChart.resetZoom();
    }
}

// Show reset button when chart has data
function showResetZoomButton() {
    const resetBtn = document.getElementById('reset-zoom-btn');
    if (resetBtn && resultsChart && resultsChart.data.datasets.length > 0) {
        resetBtn.classList.remove('hidden');
    }
}

// Hide reset button when chart is empty
function hideResetZoomButton() {
    const resetBtn = document.getElementById('reset-zoom-btn');
    if (resetBtn) {
        resetBtn.classList.add('hidden');
    }
}
