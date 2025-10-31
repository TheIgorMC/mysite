// Electronics Admin Portal JavaScript
// Global state
let currentTab = 'components';
let currentJobId = null;
let currentBoardId = null;
let currentFileId = null;
let allComponents = [];
let allBoards = [];
let allJobs = [];
let allFiles = [];

// Check for required variables
if (typeof ELECTRONICS_STORAGE_URL === 'undefined') {
    console.error('[Electronics] ELECTRONICS_STORAGE_URL is not defined!');
}
if (typeof ELECTRONICS_API_BASE === 'undefined') {
    console.error('[Electronics] ELECTRONICS_API_BASE is not defined!');
}

console.log('[Electronics] Script loaded');
console.log('[Electronics] Storage URL:', typeof ELECTRONICS_STORAGE_URL !== 'undefined' ? ELECTRONICS_STORAGE_URL : 'UNDEFINED');
console.log('[Electronics] API Base:', typeof ELECTRONICS_API_BASE !== 'undefined' ? ELECTRONICS_API_BASE : 'UNDEFINED');

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Electronics] Page loaded');
    console.log('[Electronics] Storage URL:', window.ELECTRONICS_STORAGE_URL);
    console.log('[Electronics] API Base:', window.ELECTRONICS_API_BASE);
    
    // Add Enter key support for component search
    const componentSearchInput = document.getElementById('component-search');
    if (componentSearchInput) {
        componentSearchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                searchComponents();
            }
        });
    }
    
    // Load initial data based on active tab
    const activeTab = document.querySelector('.tab-button.active');
    if (activeTab) {
        console.log('[Electronics] Active tab:', activeTab.dataset.tab);
        switchTab(activeTab.dataset.tab);
    } else {
        console.log('[Electronics] No active tab found, defaulting to components');
        switchTab('components');
    }
});

// Tab Switching
function switchTab(tabName) {
    console.log('[Electronics] Switching to tab:', tabName);
    currentTab = tabName;
    
    // Update tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active', 'border-blue-600', 'text-blue-600');
            btn.classList.remove('border-transparent', 'text-gray-500');
        } else {
            btn.classList.remove('active', 'border-blue-600', 'text-blue-600');
            btn.classList.add('border-transparent', 'text-gray-500');
        }
    });
    
    // Update tab panels
    document.querySelectorAll('.tab-panel').forEach(panel => {
        const shouldShow = panel.id === `panel-${tabName}`;
        panel.classList.toggle('hidden', !shouldShow);
        if (shouldShow) {
            console.log('[Electronics] Showing panel:', panel.id);
        }
    });
    
    // Load data for the active tab
    console.log('[Electronics] Loading data for:', tabName);
    switch(tabName) {
        case 'components':
            loadComponents();
            break;
        case 'boards':
            loadBoards();
            break;
        case 'jobs':
            loadJobs();
            break;
        case 'files':
            loadFiles();
            break;
        case 'stock':
            loadStockOverview();
            break;
        default:
            console.error('[Electronics] Unknown tab:', tabName);
    }
}

// ===== COMPONENTS TAB =====

async function loadComponents() {
    console.log('[Components] Loading...');
    try {
        // Smart pagination - increase limit until we get less than requested
        let limit = 100;
        let lastCount = 0;
        
        while (true) {
            const url = `${ELECTRONICS_API_BASE}/components?limit=${limit}`;
            console.log(`[Components] Fetching from: ${url}`);
            
            const response = await fetch(url);
            console.log('[Components] Response status:', response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('[Components] Error response:', errorText);
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
            
            const data = await response.json();
            const count = Array.isArray(data) ? data.length : 0;
            console.log(`[Components] Received ${count} items (limit was ${limit})`);
            
            // API returns array directly
            if (count < limit) {
                // Got fewer than requested, this is all the data
                console.log('[Components] Total components loaded:', count);
                allComponents = data;
                break;
            }
            
            // Got exactly what we asked for, there might be more
            limit += 100;
            
            // Safety: don't loop forever
            if (limit > 10000) {
                console.warn('[Components] Safety limit reached at 10000');
                allComponents = data;
                break;
            }
        }
        
        renderComponentsTable(allComponents);
    } catch (error) {
        console.error('[Components] Error loading:', error);
        showToast('Failed to load components: ' + error.message, 'error');
        
        // Show error in table
        const tbody = document.getElementById('components-table-body');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="px-4 py-8 text-center text-red-600 dark:text-red-400">
                        <i class="fas fa-exclamation-triangle text-2xl mb-2"></i>
                        <p>Error: ${error.message}</p>
                    </td>
                </tr>
            `;
        }
    }
}

async function searchComponents() {
    const search = document.getElementById('component-search').value;
    const type = document.getElementById('component-type-filter').value;
    const pkg = document.getElementById('component-package-filter').value;
    
    try {
        let url = `${ELECTRONICS_API_BASE}/components/search?`;
        if (search) url += `q=${encodeURIComponent(search)}&`;
        if (type) url += `product_type=${encodeURIComponent(type)}&`;
        if (pkg) url += `package=${encodeURIComponent(pkg)}`;
        
        const response = await fetch(url);
        const data = await response.json();
        // API returns array directly
        allComponents = Array.isArray(data) ? data : [];
        renderComponentsTable(allComponents);
    } catch (error) {
        console.error('Error searching components:', error);
        showToast('Search failed', 'error');
    }
}

function renderComponentsTable(components) {
    const tbody = document.getElementById('components-table-body');
    
    if (components.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                    No components found
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = components.map(comp => {
        // Debug first component
        if (comp.id === components[0].id) {
            console.log('[Component Render] Sample component fields:', {
                id: comp.id,
                seller: comp.seller,
                seller_code: comp.seller_code,
                supplier: comp.supplier,
                supplier_code: comp.supplier_code,
                allFields: Object.keys(comp)
            });
        }
        
        return `
        <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
            <td class="px-3 py-3 text-sm text-gray-900 dark:text-gray-100">${comp.product_type || comp.category || '-'}</td>
            <td class="px-3 py-3 text-sm font-medium text-gray-900 dark:text-gray-100 max-w-xs truncate" title="${comp.manufacturer_code || comp.mpn || comp.value || '-'}">${comp.manufacturer_code || comp.mpn || comp.value || '-'}</td>
            <td class="px-3 py-3 text-sm text-gray-700 dark:text-gray-300">${comp.package || '-'}</td>
            <td class="px-3 py-3 text-sm text-gray-700 dark:text-gray-300">${comp.manufacturer || '-'}</td>
            <td class="px-3 py-3 text-sm text-gray-700 dark:text-gray-300">
                <div class="max-w-xs">
                    <div class="font-medium">${comp.seller || comp.supplier || '-'}</div>
                    <div class="text-xs text-gray-500 truncate" title="${comp.seller_code || comp.supplier_code || ''}">${comp.seller_code || comp.supplier_code || '-'}</div>
                </div>
            </td>
            <td class="px-3 py-3 text-sm">
                ${getStockBadge(comp.qty_left !== undefined ? comp.qty_left : comp.stock_qty)}
            </td>
            <td class="px-3 py-3 text-sm text-gray-700 dark:text-gray-300">
                €${(comp.price !== undefined ? comp.price : comp.unit_price || 0).toFixed(4)}
            </td>
            <td class="px-3 py-3 text-sm text-right whitespace-nowrap">
                <button onclick="editComponent(${comp.id})" 
                        class="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 mr-3"
                        title="Edit component">
                    <i class="fas fa-edit"></i>
                </button>
                <button onclick="deleteComponent(${comp.id})" 
                        class="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                        title="Delete component">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `;
    }).join('');
}

function getStockBadge(qty) {
    if (qty === 0) {
        return '<span class="px-2 py-1 bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 text-xs font-semibold rounded">Out</span>';
    } else if (qty <= 10) {
        return `<span class="px-2 py-1 bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 text-xs font-semibold rounded">${qty}</span>`;
    } else {
        return `<span class="px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 text-xs font-semibold rounded">${qty}</span>`;
    }
}

function showAddComponentModal() {
    document.getElementById('add-component-modal').classList.remove('hidden');
    document.getElementById('add-component-modal').classList.add('flex');
}

function closeAddComponentModal() {
    document.getElementById('add-component-modal').classList.add('hidden');
    document.getElementById('add-component-modal').classList.remove('flex');
    document.getElementById('add-component-form').reset();
}

document.getElementById('add-component-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    
    try {
        const response = await fetch(`${ELECTRONICS_API_BASE}/components`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showToast('Component added successfully', 'success');
            closeAddComponentModal();
            loadComponents();
        } else {
            throw new Error('Failed to add component');
        }
    } catch (error) {
        console.error('Error adding component:', error);
        showToast('Failed to add component', 'error');
    }
});

function editComponent(id) {
    const comp = allComponents.find(c => c.id == id);
    if (!comp) return;
    
    // Use correct field names from API
    const displayName = `${comp.product_type || comp.category || 'Component'} ${comp.manufacturer_code || comp.mpn || comp.value || ''} (${comp.package || 'N/A'})`;
    const currentQty = comp.qty_left !== undefined ? comp.qty_left : (comp.stock_qty || 0);
    const currentPrice = comp.price !== undefined ? comp.price : (comp.unit_price || 0);
    
    document.getElementById('edit-component-id').value = id;
    document.getElementById('edit-component-name').textContent = displayName;
    document.getElementById('edit-component-qty').value = currentQty;
    document.getElementById('edit-component-price').value = currentPrice;
    
    document.getElementById('edit-component-modal').classList.remove('hidden');
    document.getElementById('edit-component-modal').classList.add('flex');
}

function closeEditComponentModal() {
    document.getElementById('edit-component-modal').classList.add('hidden');
    document.getElementById('edit-component-modal').classList.remove('flex');
}

document.getElementById('edit-component-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const id = document.getElementById('edit-component-id').value;
    const qty = parseInt(document.getElementById('edit-component-qty').value);
    const price = parseFloat(document.getElementById('edit-component-price').value);
    
    try {
        const response = await fetch(`${ELECTRONICS_API_BASE}/components/${id}`, {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                qty_left: qty, 
                stock_qty: qty,
                price: price,
                unit_price: price
            })
        });
        
        if (response.ok) {
            showToast('Component updated successfully', 'success');
            closeEditComponentModal();
            loadComponents();
        } else {
            const errorText = await response.text();
            console.error('[Edit Component] Error:', errorText);
            throw new Error('Failed to update component');
        }
    } catch (error) {
        console.error('Error updating component:', error);
        showToast('Failed to update component', 'error');
    }
});

async function deleteComponent(id) {
    if (!confirm('Are you sure you want to delete this component?')) return;
    
    try {
        const response = await fetch(`${ELECTRONICS_API_BASE}/components/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('Component deleted successfully', 'success');
            loadComponents();
        } else {
            throw new Error('Failed to delete component');
        }
    } catch (error) {
        console.error('Error deleting component:', error);
        showToast('Failed to delete component', 'error');
    }
}

// ===== BOARDS TAB =====

async function loadBoards() {
    try {
        // Smart pagination - increase limit until we get less than requested
        let limit = 100;
        
        while (true) {
            const response = await fetch(`${ELECTRONICS_API_BASE}/boards?limit=${limit}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            // Ensure it's an array
            if (!Array.isArray(data)) {
                console.error('[Boards] Expected array, got:', typeof data);
                allBoards = [];
                break;
            }
            
            const count = data.length;
            
            // API returns array directly
            if (count < limit) {
                // Got all data
                allBoards = data;
                break;
            }
            
            // Might be more data
            limit += 100;
            if (limit > 10000) {
                allBoards = data;
                break;
            }
        }
        
        renderBoardsGrid(allBoards);
    } catch (error) {
        console.error('Error loading boards:', error);
        showToast('Failed to load boards', 'error');
    }
}

function renderBoardsGrid(boards) {
    const grid = document.getElementById('boards-grid');
    
    if (boards.length === 0) {
        grid.innerHTML = `
            <div class="col-span-full text-center py-8">
                <p class="text-gray-500 dark:text-gray-400">No boards found</p>
            </div>
        `;
        return;
    }
    
    grid.innerHTML = boards.map(board => `
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4 hover:shadow-lg transition cursor-pointer"
             onclick="viewBoardDetails(${board.id})">
            <div class="flex items-start justify-between mb-3">
                <div>
                    <h4 class="text-lg font-semibold text-gray-900 dark:text-white">${board.board_name}</h4>
                    <p class="text-sm text-gray-600 dark:text-gray-400">${board.version}${board.variant ? ` - ${board.variant}` : ''}</p>
                </div>
                <i class="fas fa-microchip text-blue-500 text-2xl"></i>
            </div>
            ${board.description ? `<p class="text-sm text-gray-700 dark:text-gray-300 mb-3">${board.description}</p>` : ''}
            <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                <span><i class="fas fa-list mr-1"></i>${board.bom_count || 0} components</span>
                <span><i class="fas fa-folder mr-1"></i>${board.files_count || 0} files</span>
            </div>
        </div>
    `).join('');
}

function showAddBoardModal() {
    document.getElementById('add-board-modal').classList.remove('hidden');
    document.getElementById('add-board-modal').classList.add('flex');
}

function closeAddBoardModal() {
    document.getElementById('add-board-modal').classList.add('hidden');
    document.getElementById('add-board-modal').classList.remove('flex');
    document.getElementById('add-board-form').reset();
}

document.getElementById('add-board-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    
    try {
        const response = await fetch(`${ELECTRONICS_API_BASE}/boards`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showToast('Board created successfully', 'success');
            closeAddBoardModal();
            loadBoards();
        } else {
            throw new Error('Failed to create board');
        }
    } catch (error) {
        console.error('Error creating board:', error);
        showToast('Failed to create board', 'error');
    }
});

async function viewBoardDetails(boardId) {
    currentBoardId = boardId;
    const board = allBoards.find(b => b.id === boardId);
    if (!board) return;
    
    document.getElementById('board-detail-name').textContent = board.board_name;
    document.getElementById('board-detail-version').textContent = `${board.version}${board.variant ? ` - ${board.variant}` : ''}`;
    
    document.getElementById('board-details-modal').classList.remove('hidden');
    document.getElementById('board-details-modal').classList.add('flex');
    
    switchBoardTab('bom');
}

function closeBoardDetailsModal() {
    document.getElementById('board-details-modal').classList.add('hidden');
    document.getElementById('board-details-modal').classList.remove('flex');
    currentBoardId = null;
}

function switchBoardTab(tabName) {
    // Update tabs
    document.querySelectorAll('.board-tab').forEach(tab => {
        if (tab.dataset.tab === tabName) {
            tab.classList.add('border-blue-600', 'text-blue-600');
            tab.classList.remove('border-transparent', 'text-gray-500');
        } else {
            tab.classList.remove('border-blue-600', 'text-blue-600');
            tab.classList.add('border-transparent', 'text-gray-500');
        }
    });
    
    // Show/hide content
    document.querySelectorAll('.board-tab-content').forEach(content => {
        content.classList.toggle('hidden', content.id !== `board-${tabName}-content`);
    });
    
    // Load data
    if (tabName === 'bom') {
        loadBoardBOM(currentBoardId);
    } else if (tabName === 'files') {
        loadBoardFiles(currentBoardId);
    }
}

async function loadBoardBOM(boardId) {
    try {
        const response = await fetch(`${ELECTRONICS_API_BASE}/boards/${boardId}/bom`);
        const data = await response.json();
        
        const tbody = document.getElementById('board-bom-table');
        if (!data.bom || data.bom.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="px-4 py-8 text-center text-gray-500">No BOM data</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.bom.map(item => `
            <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
                <td class="px-4 py-3 text-sm font-mono text-gray-900 dark:text-gray-100">${item.designator}</td>
                <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">${item.product_type}</td>
                <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-gray-100">${item.value}</td>
                <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">${item.package}</td>
                <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">${item.qty}</td>
                <td class="px-4 py-3 text-sm">${item.component_id ? getStockBadge(item.stock_qty || 0) : '<span class="text-xs text-gray-400">Not linked</span>'}</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading BOM:', error);
    }
}

async function loadBoardFiles(boardId) {
    try {
        const response = await fetch(`${ELECTRONICS_API_BASE}/files?board_id=${boardId}`);
        const data = await response.json();
        
        const container = document.getElementById('board-files-list');
        if (!data.files || data.files.length === 0) {
            container.innerHTML = '<p class="text-center text-gray-500 py-8">No files registered</p>';
            return;
        }
        
        container.innerHTML = data.files.map(file => `
            <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    <i class="fas ${getFileIcon(file.file_type)} text-2xl text-gray-600 dark:text-gray-400"></i>
                    <div>
                        <p class="text-sm font-medium text-gray-900 dark:text-gray-100">${file.display_name || file.file_path}</p>
                        <p class="text-xs text-gray-500 dark:text-gray-400">${file.file_type}</p>
                    </div>
                </div>
                <div class="flex items-center space-x-2">
                    ${file.file_type === 'ibom' ? `
                        <button onclick="openIBOMViewer('${file.file_path}')" 
                                class="px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white text-xs rounded">
                            <i class="fas fa-eye mr-1"></i>View
                        </button>
                    ` : `
                        <a href="${ELECTRONICS_STORAGE_URL}/${file.file_path}" target="_blank"
                           class="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded">
                            <i class="fas fa-external-link-alt mr-1"></i>Open
                        </a>
                    `}
                    <button onclick="deleteFile(${file.id})" 
                            class="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-xs rounded">
                            <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading files:', error);
    }
}

function uploadBOM() {
    document.getElementById('upload-bom-board-id').value = currentBoardId;
    document.getElementById('upload-bom-modal').classList.remove('hidden');
    document.getElementById('upload-bom-modal').classList.add('flex');
}

function closeUploadBOMModal() {
    document.getElementById('upload-bom-modal').classList.add('hidden');
    document.getElementById('upload-bom-modal').classList.remove('flex');
    document.getElementById('upload-bom-form').reset();
}

document.getElementById('upload-bom-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const boardId = document.getElementById('upload-bom-board-id').value;
    const csvData = document.getElementById('bom-csv-data').value;
    
    try {
        const response = await fetch(`${ELECTRONICS_API_BASE}/boards/${boardId}/bom/upload`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({bom_data: csvData})
        });
        
        if (response.ok) {
            showToast('BOM uploaded successfully', 'success');
            closeUploadBOMModal();
            loadBoardBOM(boardId);
        } else {
            throw new Error('Failed to upload BOM');
        }
    } catch (error) {
        console.error('Error uploading BOM:', error);
        showToast('Failed to upload BOM', 'error');
    }
});

async function exportBOM() {
    try {
        window.open(`${ELECTRONICS_API_BASE}/boards/${currentBoardId}/bom/export`, '_blank');
    } catch (error) {
        console.error('Error exporting BOM:', error);
        showToast('Failed to export BOM', 'error');
    }
}

// ===== JOBS TAB =====

async function loadJobs() {
    try {
        // Smart pagination - increase limit until we get less than requested
        let limit = 100;
        
        while (true) {
            const response = await fetch(`${ELECTRONICS_API_BASE}/jobs?limit=${limit}`);
            const data = await response.json();
            const count = Array.isArray(data) ? data.length : 0;
            
            // API returns array directly
            if (count < limit) {
                // Got all data
                allJobs = data;
                break;
            }
            
            // Might be more data
            limit += 100;
            if (limit > 10000) {
                allJobs = data;
                break;
            }
        }
        
        renderJobsGrid(allJobs);
    } catch (error) {
        console.error('Error loading jobs:', error);
        showToast('Failed to load jobs', 'error');
    }
}

function renderJobsGrid(jobs) {
    const grid = document.getElementById('jobs-grid');
    
    if (jobs.length === 0) {
        grid.innerHTML = '<div class="col-span-full text-center py-8"><p class="text-gray-500">No jobs found</p></div>';
        return;
    }
    
    grid.innerHTML = jobs.map(job => `
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4 hover:shadow-lg transition cursor-pointer"
             onclick="viewJobDetails(${job.id})">
            <div class="flex items-start justify-between mb-3">
                <div>
                    <h4 class="text-lg font-semibold text-gray-900 dark:text-white">${job.job_name}</h4>
                    ${getStatusBadge(job.status)}
                </div>
                <i class="fas fa-industry text-blue-500 text-2xl"></i>
            </div>
            ${job.notes ? `<p class="text-sm text-gray-700 dark:text-gray-300 mb-3">${job.notes}</p>` : ''}
            <div class="text-xs text-gray-500 dark:text-gray-400">
                <span><i class="fas fa-calendar mr-1"></i>${new Date(job.created_at).toLocaleDateString()}</span>
            </div>
        </div>
    `).join('');
}

function getStatusBadge(status) {
    const statusColors = {
        planning: 'bg-gray-100 text-gray-800',
        ready: 'bg-green-100 text-green-800',
        in_progress: 'bg-blue-100 text-blue-800',
        completed: 'bg-purple-100 text-purple-800',
        on_hold: 'bg-yellow-100 text-yellow-800'
    };
    const color = statusColors[status] || statusColors.planning;
    return `<span class="px-2 py-1 text-xs font-semibold rounded-full ${color}">${status.replace('_', ' ')}</span>`;
}

function showCreateJobModal() {
    document.getElementById('create-job-modal').classList.remove('hidden');
    document.getElementById('create-job-modal').classList.add('flex');
}

function closeCreateJobModal() {
    document.getElementById('create-job-modal').classList.add('hidden');
    document.getElementById('create-job-modal').classList.remove('flex');
    document.getElementById('create-job-form').reset();
}

document.getElementById('create-job-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    
    try {
        const response = await fetch(`${ELECTRONICS_API_BASE}/jobs`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showToast('Job created successfully', 'success');
            closeCreateJobModal();
            loadJobs();
        } else {
            throw new Error('Failed to create job');
        }
    } catch (error) {
        console.error('Error creating job:', error);
        showToast('Failed to create job', 'error');
    }
});

async function viewJobDetails(jobId) {
    currentJobId = jobId;
    const job = allJobs.find(j => j.id === jobId);
    if (!job) return;
    
    document.getElementById('job-detail-name').textContent = job.job_name;
    document.getElementById('job-detail-status').textContent = job.status.replace('_', ' ');
    document.getElementById('job-detail-status').className = `px-3 py-1 text-sm font-semibold rounded-full ${getStatusBadge(job.status).split('class="')[1].split('"')[0]}`;
    document.getElementById('job-detail-date').textContent = new Date(job.created_at).toLocaleString();
    document.getElementById('current-job-id').value = jobId;
    
    document.getElementById('job-details-modal').classList.remove('hidden');
    document.getElementById('job-details-modal').classList.add('flex');
    document.getElementById('stock-check-results').classList.add('hidden');
    
    await loadJobBoards(jobId);
}

function closeJobDetailsModal() {
    document.getElementById('job-details-modal').classList.add('hidden');
    document.getElementById('job-details-modal').classList.remove('flex');
    currentJobId = null;
}

async function loadJobBoards(jobId) {
    try {
        const response = await fetch(`${ELECTRONICS_API_BASE}/jobs/${jobId}`);
        const data = await response.json();
        
        const container = document.getElementById('job-boards-list');
        if (!data.job.boards || data.job.boards.length === 0) {
            container.innerHTML = '<p class="col-span-full text-center text-gray-500 py-8">No boards added to this job</p>';
            return;
        }
        
        container.innerHTML = data.job.boards.map(board => `
            <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                <div class="flex items-center justify-between">
                    <div>
                        <h5 class="font-semibold text-gray-900 dark:text-white">${board.board_name}</h5>
                        <p class="text-sm text-gray-600 dark:text-gray-400">${board.version}</p>
                    </div>
                    <div class="text-right">
                        <p class="text-2xl font-bold text-blue-600">${board.quantity}</p>
                        <p class="text-xs text-gray-500">units</p>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading job boards:', error);
    }
}

function showAddBoardToJobModal() {
    document.getElementById('add-board-job-id').value = currentJobId;
    document.getElementById('add-board-to-job-modal').classList.remove('hidden');
    document.getElementById('add-board-to-job-modal').classList.add('flex');
    
    // Populate board select
    const select = document.getElementById('board-select');
    select.innerHTML = allBoards.map(board => 
        `<option value="${board.id}">${board.board_name} - ${board.version}</option>`
    ).join('');
}

function closeAddBoardToJobModal() {
    document.getElementById('add-board-to-job-modal').classList.add('hidden');
    document.getElementById('add-board-to-job-modal').classList.remove('flex');
}

document.getElementById('add-board-to-job-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const jobId = document.getElementById('add-board-job-id').value;
    const boardId = document.getElementById('board-select').value;
    const quantity = parseInt(document.getElementById('board-quantity').value);
    
    try {
        const response = await fetch(`${ELECTRONICS_API_BASE}/jobs/${jobId}/boards`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({board_id: boardId, quantity})
        });
        
        if (response.ok) {
            showToast('Board added to job', 'success');
            closeAddBoardToJobModal();
            loadJobBoards(jobId);
        } else {
            throw new Error('Failed to add board');
        }
    } catch (error) {
        console.error('Error adding board to job:', error);
        showToast('Failed to add board', 'error');
    }
});

async function checkJobStock() {
    try {
        const response = await fetch(`${ELECTRONICS_API_BASE}/jobs/${currentJobId}/check_stock`);
        const data = await response.json();
        
        document.getElementById('stock-check-results').classList.remove('hidden');
        document.getElementById('stock-available-count').textContent = data.summary.available_components;
        document.getElementById('stock-low-count').textContent = data.summary.low_stock_components;
        document.getElementById('stock-missing-count').textContent = data.summary.missing_components;
        
        const tbody = document.getElementById('stock-check-table');
        tbody.innerHTML = data.component_details.map(comp => `
            <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
                <td class="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">
                    ${comp.product_type} ${comp.value} (${comp.package})
                </td>
                <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">${comp.required}</td>
                <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">${comp.available}</td>
                <td class="px-4 py-3 text-sm">
                    ${comp.status === 'available' ? 
                        '<span class="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">OK</span>' :
                      comp.status === 'low' ?
                        '<span class="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-semibold rounded">Low</span>' :
                        '<span class="px-2 py-1 bg-red-100 text-red-800 text-xs font-semibold rounded">Missing</span>'
                    }
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error checking stock:', error);
        showToast('Failed to check stock', 'error');
    }
}

async function reserveStock() {
    if (!confirm('Reserve stock for this job? This will deduct from available inventory.')) return;
    
    try {
        const response = await fetch(`${ELECTRONICS_API_BASE}/jobs/${currentJobId}/reserve_stock`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showToast('Stock reserved successfully', 'success');
            checkJobStock();
        } else {
            throw new Error('Failed to reserve stock');
        }
    } catch (error) {
        console.error('Error reserving stock:', error);
        showToast('Failed to reserve stock', 'error');
    }
}

async function generateMissingBOM() {
    try {
        window.open(`${ELECTRONICS_API_BASE}/jobs/${currentJobId}/missing_bom`, '_blank');
    } catch (error) {
        console.error('Error generating missing BOM:', error);
        showToast('Failed to generate shopping list', 'error');
    }
}

// ===== FILES TAB =====

async function loadFiles() {
    try {
        const boardFilter = document.getElementById('files-board-filter')?.value || '';
        const categoryFilter = document.getElementById('files-type-filter')?.value || '';
        
        // Smart pagination - increase limit until we get less than requested
        let limit = 100;
        
        while (true) {
            let url = `${ELECTRONICS_API_BASE}/files?limit=${limit}`;
            if (boardFilter) url += `&board_id=${boardFilter}`;
            if (categoryFilter) url += `&category=${categoryFilter}`;
            
            const response = await fetch(url);
            
            // If files endpoint doesn't exist (404), show message and stop
            if (response.status === 404) {
                console.warn('[Files] Files endpoint not available in API');
                const grid = document.getElementById('files-grid');
                if (grid) {
                    grid.innerHTML = `
                        <div class="col-span-full text-center py-8">
                            <i class="fas fa-info-circle text-4xl text-blue-500 dark:text-blue-400 mb-3"></i>
                            <p class="text-gray-600 dark:text-gray-400 mb-2">File management not yet available</p>
                            <p class="text-sm text-gray-500 dark:text-gray-500">The files API endpoint is not configured</p>
                        </div>
                    `;
                }
                return;
            }
            
            const data = await response.json();
            const count = Array.isArray(data) ? data.length : 0;
            
            // API returns array directly
            if (count < limit) {
                // Got all data
                allFiles = data;
                break;
            }
            
            // Might be more data
            limit += 100;
            if (limit > 10000) {
                allFiles = data;
                break;
            }
        }
        
        renderFilesGrid(allFiles);
        
        // Populate board filter if empty
        if (!document.getElementById('files-board-filter').innerHTML || document.getElementById('files-board-filter').innerHTML === '<option value="">All Boards</option>') {
            const boardSelect = document.getElementById('files-board-filter');
            boardSelect.innerHTML = '<option value="">All Boards</option>' + 
                allBoards.map(board => `<option value="${board.id}">${board.board_name} - ${board.version}</option>`).join('');
        }
    } catch (error) {
        console.error('Error loading files:', error);
        showToast('Failed to load files', 'error');
    }
}

function renderFilesGrid(files) {
    const grid = document.getElementById('files-grid');
    
    if (files.length === 0) {
        grid.innerHTML = '<div class="col-span-full text-center py-8"><p class="text-gray-500">No files found</p></div>';
        return;
    }
    
    grid.innerHTML = files.map(file => `
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4 hover:shadow-lg transition cursor-pointer"
             onclick="viewFileDetails(${file.id})">
            <div class="flex items-center justify-between mb-3">
                <i class="fas ${getFileIcon(file.file_type)} text-4xl text-gray-600 dark:text-gray-400"></i>
                ${file.file_type === 'ibom' ? '<span class="px-2 py-1 bg-purple-100 text-purple-800 text-xs font-semibold rounded">Interactive</span>' : ''}
            </div>
            <h4 class="text-sm font-semibold text-gray-900 dark:text-white mb-1 truncate">${file.display_name || file.file_path.split('/').pop()}</h4>
            <p class="text-xs text-gray-600 dark:text-gray-400 mb-2">${file.file_type}</p>
            <p class="text-xs text-gray-500 dark:text-gray-500 truncate">${file.board_name}</p>
        </div>
    `).join('');
}

function getFileIcon(fileType) {
    const icons = {
        bom: 'fa-file-csv',
        pnp: 'fa-map-marker-alt',
        gerber: 'fa-layer-group',
        schematic: 'fa-project-diagram',
        pcb_layout: 'fa-microchip',
        ibom: 'fa-table',
        datasheet: 'fa-file-pdf',
        documentation: 'fa-book',
        firmware: 'fa-code',
        cad: 'fa-cube'
    };
    return icons[fileType] || 'fa-file';
}

function showRegisterFileModal() {
    document.getElementById('register-file-modal').classList.remove('hidden');
    document.getElementById('register-file-modal').classList.add('flex');
    
    // Populate board select
    const select = document.getElementById('register-file-board');
    select.innerHTML = '<option value="">Select a board...</option>' + 
        allBoards.map(board => `<option value="${board.id}">${board.board_name} - ${board.version}</option>`).join('');
}

function closeRegisterFileModal() {
    document.getElementById('register-file-modal').classList.add('hidden');
    document.getElementById('register-file-modal').classList.remove('flex');
    document.getElementById('register-file-form').reset();
}

document.getElementById('register-file-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    
    try {
        const response = await fetch(`${ELECTRONICS_API_BASE}/files/register`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showToast('File registered successfully', 'success');
            closeRegisterFileModal();
            loadFiles();
        } else {
            throw new Error('Failed to register file');
        }
    } catch (error) {
        console.error('Error registering file:', error);
        showToast('Failed to register file', 'error');
    }
});

function viewFileDetails(fileId) {
    const file = allFiles.find(f => f.id === fileId);
    if (!file) return;
    
    currentFileId = fileId;
    
    const content = document.getElementById('file-details-content');
    content.innerHTML = `
        <div class="space-y-3">
            <div>
                <label class="text-sm font-medium text-gray-500 dark:text-gray-400">Board</label>
                <p class="text-gray-900 dark:text-gray-100">${file.board_name}</p>
            </div>
            <div>
                <label class="text-sm font-medium text-gray-500 dark:text-gray-400">File Type</label>
                <p class="text-gray-900 dark:text-gray-100">${file.file_type}</p>
            </div>
            <div>
                <label class="text-sm font-medium text-gray-500 dark:text-gray-400">File Path</label>
                <p class="text-gray-900 dark:text-gray-100 font-mono text-sm break-all">${file.file_path}</p>
            </div>
            ${file.display_name ? `
                <div>
                    <label class="text-sm font-medium text-gray-500 dark:text-gray-400">Display Name</label>
                    <p class="text-gray-900 dark:text-gray-100">${file.display_name}</p>
                </div>
            ` : ''}
            ${file.description ? `
                <div>
                    <label class="text-sm font-medium text-gray-500 dark:text-gray-400">Description</label>
                    <p class="text-gray-900 dark:text-gray-100">${file.description}</p>
                </div>
            ` : ''}
            <div>
                <label class="text-sm font-medium text-gray-500 dark:text-gray-400">Full URL</label>
                <p class="text-gray-900 dark:text-gray-100 font-mono text-xs break-all">${ELECTRONICS_STORAGE_URL}/${file.file_path}</p>
            </div>
        </div>
    `;
    
    const viewBtn = document.getElementById('file-view-btn');
    if (file.file_type === 'ibom') {
        viewBtn.onclick = () => openIBOMViewer(file.file_path);
        viewBtn.innerHTML = '<i class="fas fa-eye mr-2"></i>View Interactive BOM';
    } else {
        viewBtn.onclick = () => window.open(`${ELECTRONICS_STORAGE_URL}/${file.file_path}`, '_blank');
        viewBtn.innerHTML = '<i class="fas fa-external-link-alt mr-2"></i>Open File';
    }
    
    document.getElementById('file-details-modal').classList.remove('hidden');
    document.getElementById('file-details-modal').classList.add('flex');
}

function closeFileDetailsModal() {
    document.getElementById('file-details-modal').classList.add('hidden');
    document.getElementById('file-details-modal').classList.remove('flex');
    currentFileId = null;
}

function openIBOMViewer(filePath) {
    const iframe = document.getElementById('ibom-viewer-frame');
    iframe.src = `${ELECTRONICS_STORAGE_URL}/${filePath}`;
    document.getElementById('ibom-viewer-modal').classList.remove('hidden');
    document.getElementById('ibom-viewer-modal').classList.add('flex');
}

function closeIBOMViewer() {
    document.getElementById('ibom-viewer-modal').classList.add('hidden');
    document.getElementById('ibom-viewer-modal').classList.remove('flex');
    document.getElementById('ibom-viewer-frame').src = '';
}

async function confirmDeleteFile() {
    if (!confirm('Are you sure you want to delete this file registration?')) return;
    
    try {
        const response = await fetch(`${ELECTRONICS_API_BASE}/files/${currentFileId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('File deleted successfully', 'success');
            closeFileDetailsModal();
            loadFiles();
        } else {
            throw new Error('Failed to delete file');
        }
    } catch (error) {
        console.error('Error deleting file:', error);
        showToast('Failed to delete file', 'error');
    }
}

// ===== STOCK TAB =====

async function loadStockOverview() {
    try {
        const response = await fetch(`${ELECTRONICS_API_BASE}/components`);
        const data = await response.json();
        allComponents = data.components || [];
        
        // Calculate stats
        const total = allComponents.length;
        const available = allComponents.filter(c => c.qty_left > 10).length;
        const low = allComponents.filter(c => c.qty_left > 0 && c.qty_left <= 10).length;
        const out = allComponents.filter(c => c.qty_left === 0).length;
        const totalValue = allComponents.reduce((sum, c) => sum + (c.qty_left * (c.price || 0)), 0);
        
        document.getElementById('stock-total-components').textContent = total;
        document.getElementById('stock-available-components').textContent = available;
        document.getElementById('stock-low-components').textContent = low;
        document.getElementById('stock-out-components').textContent = out;
        document.getElementById('stock-total-value').textContent = `€${totalValue.toFixed(2)}`;
        
        filterStockOverview();
    } catch (error) {
        console.error('Error loading stock overview:', error);
        showToast('Failed to load stock overview', 'error');
    }
}

function filterStockOverview() {
    const typeFilter = document.getElementById('stock-type-filter').value;
    const statusFilter = document.getElementById('stock-status-filter').value;
    const sortFilter = document.getElementById('stock-sort-filter').value;
    
    let filtered = [...allComponents];
    
    // Apply filters
    if (typeFilter) {
        filtered = filtered.filter(c => c.product_type === typeFilter);
    }
    if (statusFilter === 'available') {
        filtered = filtered.filter(c => c.qty_left > 10);
    } else if (statusFilter === 'low') {
        filtered = filtered.filter(c => c.qty_left > 0 && c.qty_left <= 10);
    } else if (statusFilter === 'out') {
        filtered = filtered.filter(c => c.qty_left === 0);
    }
    
    // Apply sorting
    if (sortFilter === 'qty_asc') {
        filtered.sort((a, b) => a.qty_left - b.qty_left);
    } else if (sortFilter === 'qty_desc') {
        filtered.sort((a, b) => b.qty_left - a.qty_left);
    } else if (sortFilter === 'value_desc') {
        filtered.sort((a, b) => (b.qty_left * (b.price || 0)) - (a.qty_left * (a.price || 0)));
    } else if (sortFilter === 'type') {
        filtered.sort((a, b) => a.product_type.localeCompare(b.product_type));
    }
    
    renderStockTable(filtered);
}

function renderStockTable(components) {
    const tbody = document.getElementById('stock-overview-table');
    
    if (components.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="px-4 py-8 text-center text-gray-500">No components found</td></tr>';
        return;
    }
    
    tbody.innerHTML = components.map(comp => `
        <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
            <td class="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">${comp.product_type}</td>
            <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-gray-100">${comp.value}</td>
            <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">${comp.package}</td>
            <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">${comp.seller || '-'}</td>
            <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300 font-mono text-xs">${comp.seller_code || '-'}</td>
            <td class="px-4 py-3 text-sm">${getStockBadge(comp.qty_left)}</td>
            <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">€${(comp.price || 0).toFixed(4)}</td>
            <td class="px-4 py-3 text-sm font-semibold text-gray-900 dark:text-gray-100">€${(comp.qty_left * (comp.price || 0)).toFixed(2)}</td>
        </tr>
    `).join('');
}

async function exportStockReport() {
    try {
        // Create CSV
        const csv = ['Type,Value,Package,Supplier,Part#,Stock,Price,Total Value\n'];
        allComponents.forEach(comp => {
            csv.push(`${comp.product_type},${comp.value},${comp.package},${comp.seller || ''},${comp.seller_code || ''},${comp.qty_left},${comp.price || 0},${(comp.qty_left * (comp.price || 0)).toFixed(2)}\n`);
        });
        
        const blob = new Blob(csv, {type: 'text/csv'});
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `stock_report_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
        
        showToast('Stock report exported', 'success');
    } catch (error) {
        console.error('Error exporting stock report:', error);
        showToast('Failed to export report', 'error');
    }
}

// ===== UTILITIES =====

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    const bgColor = type === 'success' ? 'bg-green-600' : type === 'error' ? 'bg-red-600' : 'bg-blue-600';
    toast.className = `fixed bottom-4 right-4 ${bgColor} text-white px-6 py-3 rounded-lg shadow-lg z-50 transition-opacity`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
