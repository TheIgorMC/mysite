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
let parsedCSVData = null;

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

// ==================== CSV PARSING UTILITIES ====================

/**
 * Detect CSV delimiter by analyzing the first few lines
 */
function detectDelimiter(text) {
    const lines = text.trim().split('\n').slice(0, 3);
    const delimiters = [',', '\t', ';', '|'];
    const counts = {};
    
    delimiters.forEach(delim => {
        const lineCounts = lines.map(line => (line.match(new RegExp(`\\${delim}`, 'g')) || []).length);
        // Check if delimiter appears consistently
        const avgCount = lineCounts.reduce((a, b) => a + b, 0) / lineCounts.length;
        const consistent = lineCounts.every(count => Math.abs(count - avgCount) <= 1);
        counts[delim] = consistent ? avgCount : 0;
    });
    
    // Return delimiter with highest consistent count
    const detected = Object.entries(counts).sort((a, b) => b[1] - a[1])[0][0];
    console.log('[CSV] Detected delimiter:', detected === '\t' ? 'TAB' : detected, 'Counts:', counts);
    return detected;
}

/**
 * Parse CSV text with auto-delimiter detection
 * Handles quoted fields properly
 */
function parseCSV(text) {
    const delimiter = detectDelimiter(text);
    const lines = text.trim().split('\n');
    
    // Parse line respecting quotes
    function parseLine(line) {
        const result = [];
        let current = '';
        let inQuotes = false;
        
        for (let i = 0; i < line.length; i++) {
            const char = line[i];
            const nextChar = line[i + 1];
            
            if (char === '"') {
                if (inQuotes && nextChar === '"') {
                    // Escaped quote
                    current += '"';
                    i++;
                } else {
                    // Toggle quote mode
                    inQuotes = !inQuotes;
                }
            } else if (char === delimiter && !inQuotes) {
                // End of field
                result.push(current.trim());
                current = '';
            } else {
                current += char;
            }
        }
        result.push(current.trim());
        return result;
    }
    
    const headers = parseLine(lines[0]).map(h => h.replace(/^["']|["']$/g, '').trim());
    const rows = [];
    
    for (let i = 1; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue;
        
        const values = parseLine(line);
        const row = {};
        headers.forEach((header, idx) => {
            row[header] = values[idx] || '';
        });
        rows.push(row);
    }
    
    console.log('[CSV] Parsed:', rows.length, 'rows with headers:', headers);
    return { headers, rows };
}

/**
 * Map CSV row to component lookup
 * Returns { manufacturer_code, supplier_code, qty } or null if invalid
 */
function mapBOMRow(row) {
    // Find manufacturer part column (case-insensitive)
    const mfrPartKey = Object.keys(row).find(k => 
        k.toLowerCase().includes('manufacturer') && k.toLowerCase().includes('part')
    );
    
    // Find supplier part column
    const supplierPartKey = Object.keys(row).find(k => 
        k.toLowerCase().includes('supplier') && k.toLowerCase().includes('part')
    );
    
    // Find quantity column
    const qtyKey = Object.keys(row).find(k => 
        k.toLowerCase() === 'quantity' || k.toLowerCase() === 'qty'
    );
    
    // Find designator column
    const designatorKey = Object.keys(row).find(k => 
        k.toLowerCase() === 'designator' || k.toLowerCase() === 'designators' || 
        k.toLowerCase() === 'reference' || k.toLowerCase() === 'ref'
    );
    
    if (!qtyKey) {
        console.warn('[CSV] Missing quantity column in row:', row);
        return null;
    }
    
    const manufacturer_code = row[mfrPartKey]?.trim() || '';
    const supplier_code = row[supplierPartKey]?.trim() || '';
    const qty = parseInt(row[qtyKey]);
    const designators = row[designatorKey]?.trim() || ''; // Preserve designators as-is (may contain commas)
    
    // Only reject if qty is invalid - allow empty codes (will go to manual mapping)
    if (isNaN(qty) || qty <= 0) {
        console.warn('[CSV] Invalid quantity in row:', row);
        return null;
    }
    
    return { 
        manufacturer_code, 
        supplier_code,
        qty,
        designators, // Add designators field
        // Store all row data for manual mapping
        _rawRow: row
    };
}

// ==================== END CSV UTILITIES ====================

// ==================== MANUAL MAPPING ====================

let unmappedComponents = [];
let manualMappings = {};
let resolveManualMapping = null;

let ignoredComponents = new Set();

function showManualMappingModal(notFoundItems, alreadyMapped) {
    return new Promise((resolve) => {
        unmappedComponents = notFoundItems;
        manualMappings = {};
        ignoredComponents = new Set();
        resolveManualMapping = resolve;
        
        // Reset filter to unmapped
        const filterDropdown = document.getElementById('mapping-filter');
        if (filterDropdown) {
            filterDropdown.value = 'unmapped';
            // Add event listener for filter changes
            filterDropdown.onchange = filterManualMappings;
        }
        
        renderManualMappingList();
        updateMappingStats();
        
        document.getElementById('manual-mapping-modal').classList.remove('hidden');
        document.getElementById('manual-mapping-modal').classList.add('flex');
    });
}

function renderManualMappingList() {
    const list = document.getElementById('manual-mapping-list');
    const filter = document.getElementById('mapping-filter')?.value || 'all';
    
    const filteredItems = unmappedComponents.filter((item, idx) => {
        const isMapped = manualMappings[idx] !== undefined;
        const isIgnored = ignoredComponents.has(idx);
        
        if (filter === 'unmapped') return !isMapped && !isIgnored;
        if (filter === 'mapped') return isMapped;
        if (filter === 'ignored') return isIgnored;
        return true; // 'all'
    });
    
    if (filteredItems.length === 0) {
        list.innerHTML = '<div class="text-center py-8 text-gray-500 dark:text-gray-400">No components match the current filter</div>';
        return;
    }
    
    list.innerHTML = unmappedComponents.map((item, idx) => {
        const isMapped = manualMappings[idx] !== undefined;
        const isIgnored = ignoredComponents.has(idx);
        
        // Apply filter
        if (filter === 'unmapped' && (isMapped || isIgnored)) return '';
        if (filter === 'mapped' && !isMapped) return '';
        if (filter === 'ignored' && !isIgnored) return '';
        
        const mfrCode = item.manufacturer_code || '-';
        const supplierCode = item.supplier_code || '-';
        const qty = item.qty;
        
        // Get a sample of other data from raw row
        const otherData = Object.entries(item._rawRow)
            .filter(([k]) => !k.toLowerCase().includes('quantity') && !k.toLowerCase().includes('qty'))
            .slice(0, 3)
            .map(([k, v]) => `${k}: ${v}`)
            .join(', ');
        
        const statusBadge = isIgnored 
            ? '<span class="px-2 py-1 text-xs bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded">Ignored</span>'
            : isMapped 
            ? '<span class="px-2 py-1 text-xs bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 rounded">Mapped</span>'
            : '<span class="px-2 py-1 text-xs bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-300 rounded">Unmapped</span>';
        
        // Show "Create New" button for unmapped/non-ignored items
        const createNewBtn = (!isMapped && !isIgnored) ? `
            <button onclick="openBOMQuickAdd(${idx})" 
                    class="px-2 py-1 text-xs bg-green-600 hover:bg-green-700 text-white rounded whitespace-nowrap"
                    title="Create new component in database">
                <i class="fas fa-plus mr-1"></i>New
            </button>
        ` : '';
        
        return `
            <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4" data-mapping-idx="${idx}">
                <div class="grid grid-cols-12 gap-3 items-center">
                    <div class="col-span-5">
                        <div class="flex items-center justify-between mb-1">
                            <p class="text-sm font-medium text-gray-900 dark:text-gray-100">Component Info</p>
                            ${statusBadge}
                        </div>
                        <p class="text-xs text-gray-600 dark:text-gray-400">MFR: <span class="font-mono">${mfrCode}</span></p>
                        <p class="text-xs text-gray-600 dark:text-gray-400">Supplier: <span class="font-mono">${supplierCode}</span></p>
                        <p class="text-xs text-gray-500 dark:text-gray-500 mt-1">${otherData}</p>
                    </div>
                    <div class="col-span-1 text-center">
                        <i class="fas fa-arrow-right text-gray-400"></i>
                    </div>
                    <div class="col-span-4">
                        <select id="manual-map-${idx}" 
                                class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                                onchange="updateManualMapping(${idx}, this.value)"
                                ${isIgnored ? 'disabled' : ''}>
                            <option value="">-- Select Component --</option>
                            <option value="IGNORE" class="text-gray-500">🚫 Ignore this component</option>
                            ${allComponents.map(comp => {
                                const label = `${comp.manufacturer_code || comp.seller_code || 'ID:' + comp.id} - ${comp.value || ''} ${comp.package || ''} (${comp.product_type || ''})`;
                                const selected = manualMappings[idx] === comp.id ? 'selected' : '';
                                return `<option value="${comp.id}" ${selected}>${label}</option>`;
                            }).join('')}
                        </select>
                    </div>
                    <div class="col-span-2 text-right flex items-center justify-end space-x-2">
                        <span class="text-sm font-medium text-gray-600 dark:text-gray-400">×${qty}</span>
                        ${createNewBtn}
                        ${isIgnored ? `
                            <button onclick="unignoreComponent(${idx})" 
                                    class="px-2 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded"
                                    title="Unignore">
                                <i class="fas fa-undo"></i>
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }).filter(html => html).join('');
    
    updateMappingStats();
}

function filterManualMappings() {
    renderManualMappingList();
}

function updateMappingStats() {
    let mappedCount = 0;
    let ignoredCount = 0;
    let unmappedCount = 0;
    
    unmappedComponents.forEach((item, idx) => {
        if (ignoredComponents.has(idx)) {
            ignoredCount++;
        } else if (manualMappings[idx]) {
            mappedCount++;
        } else {
            unmappedCount++;
        }
    });
    
    const statsEl = document.getElementById('mapping-stats');
    if (statsEl) {
        statsEl.innerHTML = `
            <span class="text-green-600 dark:text-green-400">${mappedCount} mapped</span> · 
            <span class="text-orange-600 dark:text-orange-400">${unmappedCount} unmapped</span> · 
            <span class="text-gray-600 dark:text-gray-400">${ignoredCount} ignored</span>
        `;
    }
    
    const mappedCountEl = document.getElementById('mapped-count');
    if (mappedCountEl) {
        mappedCountEl.textContent = mappedCount;
    }
}

function unignoreComponent(idx) {
    ignoredComponents.delete(idx);
    renderManualMappingList();
}

function closeManualMappingModal() {
    document.getElementById('manual-mapping-modal').classList.add('hidden');
    document.getElementById('manual-mapping-modal').classList.remove('flex');
    // Don't resolve here - let skip/apply do it
}

function updateManualMapping(idx, componentId) {
    if (componentId === 'IGNORE') {
        // Mark as ignored
        ignoredComponents.add(idx);
        delete manualMappings[idx]; // Remove any existing mapping
        renderManualMappingList(); // Re-render to show ignored state
    } else if (componentId) {
        manualMappings[idx] = parseInt(componentId);
        updateMappingStats();
    } else {
        delete manualMappings[idx];
        updateMappingStats();
    }
}

function skipUnmappedComponents() {
    const ignoredCount = ignoredComponents.size;
    const mappedCount = Object.keys(manualMappings).length;
    console.log(`[Manual Mapping] Skipping unmapped. Ignored: ${ignoredCount}, Mapped: ${mappedCount}, Auto-mapped: ${window._tempBomItems?.length || 0}`);
    closeManualMappingModal();
    if (resolveManualMapping) {
        resolveManualMapping(true);
        resolveManualMapping = null;
    }
}

function applyManualMappings() {
    const mappedCount = Object.keys(manualMappings).length;
    const ignoredCount = ignoredComponents.size;
    console.log(`[Manual Mapping] Applying ${mappedCount} manual mappings, ignoring ${ignoredCount} components`);
    
    // Add manually mapped items (skip ignored ones)
    Object.entries(manualMappings).forEach(([idx, componentId]) => {
        const idxNum = parseInt(idx);
        if (ignoredComponents.has(idxNum)) {
            console.log('[Manual Mapping] Skipping ignored component at index', idxNum);
            return; // Skip ignored components
        }
        
        const item = unmappedComponents[idxNum];
        // Store for upload handler
        if (window._tempBomItems) {
            const bomItem = {
                component_id: componentId,
                qty: item.qty
            };
            // Include designators if present
            if (item.designators) {
                bomItem.designators = item.designators;
            }
            window._tempBomItems.push(bomItem);
        }
    });
    console.log('[Manual Mapping] Total items after mapping:', window._tempBomItems?.length || 0);
    
    closeManualMappingModal();
    if (resolveManualMapping) {
        resolveManualMapping(true);
        resolveManualMapping = null;
    }
}

// ==================== BOM QUICK ADD COMPONENT ====================

function openBOMQuickAdd(unmappedIdx) {
    const item = unmappedComponents[unmappedIdx];
    const raw = item._rawRow || {};
    
    document.getElementById('bom-qa-unmapped-index').value = unmappedIdx;
    
    // Pre-fill from mapped fields
    document.getElementById('bom-qa-manufacturer-code').value = item.manufacturer_code || '';
    document.getElementById('bom-qa-supplier-code').value = item.supplier_code || '';
    
    // Try to extract additional fields from raw CSV row (case-insensitive lookup)
    const rawLower = {};
    Object.entries(raw).forEach(([k, v]) => { rawLower[k.toLowerCase().trim()] = v; });
    
    // Manufacturer
    const manufacturer = rawLower['manufacturer'] || rawLower['mfr'] || rawLower['mfg'] || '';
    document.getElementById('bom-qa-manufacturer').value = manufacturer;
    
    // Supplier name
    const supplier = rawLower['supplier'] || rawLower['seller'] || rawLower['vendor'] || rawLower['distributor'] || '';
    document.getElementById('bom-qa-supplier').value = supplier;
    
    // Package / Footprint
    const pkg = rawLower['package'] || rawLower['footprint'] || rawLower['case/package'] || rawLower['case'] || '';
    document.getElementById('bom-qa-package').value = pkg;
    
    // SMD footprint (separate from package in some BOMs)
    const footprint = rawLower['smd footprint'] || rawLower['smd_footprint'] || rawLower['footprint'] || '';
    document.getElementById('bom-qa-footprint').value = footprint;
    
    // Value
    const value = rawLower['value'] || rawLower['comment'] || rawLower['description'] || '';
    document.getElementById('bom-qa-value').value = value;
    
    // Product type / Category - try to guess from Description or Comment
    const typeGuess = rawLower['product_type'] || rawLower['type'] || rawLower['category'] || '';
    document.getElementById('bom-qa-type').value = typeGuess;
    
    // Description
    const description = rawLower['description'] || rawLower['desc'] || rawLower['comment'] || '';
    document.getElementById('bom-qa-description').value = description;
    
    // Price
    const priceStr = rawLower['unit price'] || rawLower['unit price(\u20ac)'] || rawLower['price'] || rawLower['unit_price'] || '0';
    document.getElementById('bom-qa-price').value = parseFloat(priceStr) || 0;
    
    // Stock qty defaults to 0
    document.getElementById('bom-qa-qty-stock').value = 0;
    
    // Show raw data preview
    const rawPreview = Object.entries(raw)
        .filter(([k, v]) => v && v.toString().trim())
        .map(([k, v]) => `<span class="text-gray-500">${k}:</span> ${v}`)
        .join(' &middot; ');
    document.getElementById('bom-qa-raw-data').innerHTML = rawPreview || 'No raw data available';
    
    // Open modal
    document.getElementById('bom-quick-add-modal').classList.remove('hidden');
    document.getElementById('bom-quick-add-modal').classList.add('flex');
    
    // Reset price info
    document.getElementById('bom-qa-price-info').classList.add('hidden');
    
    // Auto-fetch price if supplier code looks like LCSC
    const supplierCode = document.getElementById('bom-qa-supplier-code').value.trim();
    const supplierName = document.getElementById('bom-qa-supplier').value.trim().toUpperCase();
    if (supplierCode && (supplierCode.match(/^C\d+$/i) || supplierName.includes('LCSC'))) {
        fetchBOMQuickAddPrice();
    }
}

function closeBOMQuickAdd() {
    document.getElementById('bom-quick-add-modal').classList.add('hidden');
    document.getElementById('bom-quick-add-modal').classList.remove('flex');
}

async function fetchBOMQuickAddPrice() {
    const supplierCode = document.getElementById('bom-qa-supplier-code').value.trim();
    const btn = document.getElementById('bom-qa-fetch-price-btn');
    const priceInfo = document.getElementById('bom-qa-price-info');
    
    if (!supplierCode) {
        showToast('No supplier code to look up', 'error');
        return;
    }
    
    // Normalize code - ensure starts with C for LCSC
    let code = supplierCode;
    if (!code.match(/^C\d+$/i)) {
        showToast('Price fetch only supported for LCSC codes (C...)', 'info');
        return;
    }
    
    // Show loading state
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i>...';
    priceInfo.classList.add('hidden');
    
    try {
        const response = await fetch(`${ELECTRONICS_API_BASE}/fetch-lcsc-price?code=${encodeURIComponent(code)}`);
        const data = await response.json();
        
        if (response.ok && data.unit_price) {
            document.getElementById('bom-qa-price').value = data.unit_price;
            
            // Show price tiers info
            if (data.price_tiers && data.price_tiers.length > 1) {
                const tiersText = data.price_tiers.map((p, i) => `\u20ac${p}`).join(' / ');
                priceInfo.textContent = `Price tiers: ${tiersText}`;
                priceInfo.classList.remove('hidden');
            }
            
            showToast(`Price fetched: \u20ac${data.unit_price}`, 'success');
        } else {
            showToast(data.error || 'Could not fetch price', 'error');
        }
    } catch (error) {
        console.error('[LCSC Price] Error:', error);
        showToast('Failed to fetch price', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-sync-alt mr-1"></i>Fetch';
    }
}

async function saveBOMQuickAddComponent() {
    const unmappedIdx = parseInt(document.getElementById('bom-qa-unmapped-index').value);
    
    const packageValue = document.getElementById('bom-qa-package').value.trim();
    const truncatedPackage = packageValue.length > 50 ? packageValue.substring(0, 50) : packageValue;
    const manufacturerCode = document.getElementById('bom-qa-manufacturer-code').value.trim();
    const typeValue = document.getElementById('bom-qa-type').value.trim();
    
    // Validate required fields
    if (!typeValue || !truncatedPackage || !manufacturerCode) {
        showToast('Please fill in Type, Package, and Manufacturer Code', 'error');
        return;
    }
    
    const componentData = {
        seller: document.getElementById('bom-qa-supplier').value.trim(),
        seller_code: document.getElementById('bom-qa-supplier-code').value.trim(),
        manufacturer: document.getElementById('bom-qa-manufacturer').value.trim(),
        manufacturer_code: manufacturerCode,
        smd_footprint: document.getElementById('bom-qa-footprint').value.trim(),
        package: truncatedPackage,
        product_type: typeValue,
        value: document.getElementById('bom-qa-value').value.trim() || manufacturerCode,
        price: parseFloat(document.getElementById('bom-qa-price').value) || 0,
        qty_left: parseInt(document.getElementById('bom-qa-qty-stock').value) || 0
    };
    
    console.log('[BOM Quick Add] Creating component:', componentData);
    
    try {
        const response = await fetch(`${ELECTRONICS_API_BASE}/components`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(componentData)
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const errorMsg = errorData.detail || `HTTP ${response.status}`;
            throw new Error(errorMsg);
        }
        
        const newComponent = await response.json();
        console.log('[BOM Quick Add] Created component ID:', newComponent.id);
        
        // Add to allComponents so it appears in dropdowns
        allComponents.push({
            id: newComponent.id,
            ...componentData
        });
        
        // Auto-map this unmapped item to the new component
        manualMappings[unmappedIdx] = newComponent.id;
        
        closeBOMQuickAdd();
        showToast(`Component created (ID: ${newComponent.id}) and mapped`, 'success');
        
        // Re-render mapping list to show updated status
        renderManualMappingList();
        
    } catch (error) {
        console.error('[BOM Quick Add] Error:', error);
        showToast('Failed to create component: ' + error.message, 'error');
    }
}

// ==================== END MANUAL MAPPING ====================

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Electronics] Page loaded');
    console.log('[Electronics] Storage URL:', window.ELECTRONICS_STORAGE_URL);
    console.log('[Electronics] API Base:', window.ELECTRONICS_API_BASE);
    
    // Load autocomplete data
    loadAutocompleteData();
    
    // ALWAYS load components and boards on page load (needed for BOM editor and jobs)
    console.log('[Electronics] Pre-loading all components and boards...');
    loadComponents();
    loadBoards();
    
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

// Load Autocomplete Data
async function loadAutocompleteData() {
    console.log('[Electronics] Loading autocomplete data...');
    
    try {
        // Fetch component types
        const typesResponse = await fetch(`${ELECTRONICS_API_BASE}/components/types`);
        if (typesResponse.ok) {
            const types = await typesResponse.json();
            console.log('[Electronics] Loaded component types:', types.length);
            
            // Populate all component-types-list datalists (main form + quick-add)
            document.querySelectorAll('#component-types-list').forEach(datalist => {
                datalist.innerHTML = types.map(type => `<option value="${type}">`).join('');
            });
        } else {
            console.error('[Electronics] Failed to load component types:', typesResponse.status);
        }
        
        // Fetch component packages
        const packagesResponse = await fetch(`${ELECTRONICS_API_BASE}/components/packages`);
        if (packagesResponse.ok) {
            const packages = await packagesResponse.json();
            console.log('[Electronics] Loaded component packages:', packages.length);
            
            // Populate all component-packages-list datalists (main form + quick-add)
            document.querySelectorAll('#component-packages-list').forEach(datalist => {
                datalist.innerHTML = packages.map(pkg => `<option value="${pkg}">`).join('');
            });
        } else {
            console.error('[Electronics] Failed to load component packages:', packagesResponse.status);
        }
        
    } catch (error) {
        console.error('[Electronics] Error loading autocomplete data:', error);
    }
}

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
    
    // Load data for the active tab (only if not already loaded)
    console.log('[Electronics] Checking data for:', tabName);
    switch(tabName) {
        case 'components':
            if (allComponents.length === 0) {
                console.log('[Electronics] Components not loaded, loading now');
                loadComponents();
            } else {
                renderComponentsTable(allComponents);
            }
            break;
        case 'boards':
            if (allBoards.length === 0) {
                console.log('[Electronics] Boards not loaded, loading now');
                loadBoards();
            } else {
                renderBoardsGrid(allBoards);
            }
            break;
        case 'pnp':
            loadPnPFiles();
            break;
        case 'jobs':
            loadJobs();
            break;
        case 'orders':
            // Order importer tab - no initial load needed
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
        // Try to load in batches to avoid 500 errors with large datasets
        let allData = [];
        let offset = 0;
        const batchSize = 500;  // Smaller batch size to avoid backend issues
        let hasMore = true;
        
        while (hasMore && offset < 10000) {  // Max 10000 items total
            const url = `${ELECTRONICS_API_BASE}/components?limit=${batchSize}&offset=${offset}`;
            console.log(`[Components] Fetching from: ${url} (batch ${Math.floor(offset/batchSize) + 1})`);
            
            const response = await fetch(url);
            console.log('[Components] Response status:', response.status);
            
            if (!response.ok) {
                // If we get an error, try without offset parameter (backend might not support it)
                if (offset === 0) {
                    console.log('[Components] Offset not supported, trying simple limit...');
                    const simpleUrl = `${ELECTRONICS_API_BASE}/components?limit=1000`;
                    const simpleResponse = await fetch(simpleUrl);
                    
                    if (!simpleResponse.ok) {
                        const errorText = await simpleResponse.text();
                        console.error('[Components] Error response:', errorText);
                        throw new Error(`HTTP ${simpleResponse.status}: ${errorText}`);
                    }
                    
                    const data = await simpleResponse.json();
                    allComponents = Array.isArray(data) ? data : [];
                    console.log(`[Components] Loaded ${allComponents.length} components (fallback mode)`);
                    renderComponentsTable();
                    return;
                }
                
                // For subsequent batches, just stop and use what we have
                console.log(`[Components] Stopping at ${allData.length} components due to error`);
                break;
            }
            
            const data = await response.json();
            const count = Array.isArray(data) ? data.length : 0;
            console.log(`[Components] Received ${count} items in this batch`);
            
            if (count === 0) {
                hasMore = false;
            } else {
                allData = allData.concat(data);
                offset += batchSize;
                
                // If we got fewer than requested, we've reached the end
                if (count < batchSize) {
                    hasMore = false;
                }
            }
        }
        
        allComponents = allData;
        console.log(`[Components] Total components loaded: ${allComponents.length}`);
        
        renderComponentsTable(allComponents);
    } catch (error) {
        console.error('[Components] Error loading:', error);
        showToast('Failed to load components: ' + error.message, 'error');
        
        // Show error in table
        const tbody = document.getElementById('components-table-body');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9" class="px-4 py-8 text-center text-red-600 dark:text-red-400">
                        <i class="fas fa-exclamation-triangle text-2xl mb-2"></i>
                        <p>Error: ${error.message}</p>
                    </td>
                </tr>
            `;
        }
    }
}

function searchComponents() {
    const search = document.getElementById('component-search').value.toLowerCase();
    const type = document.getElementById('component-type-filter').value;
    const pkg = document.getElementById('component-package-filter').value;
    
    console.log('[Search] Filtering locally:', { search, type, pkg, total: allComponents.length });
    
    // Filter the already-loaded allComponents array locally
    let filtered = allComponents;
    
    if (search) {
        filtered = filtered.filter(comp => {
            return (
                (comp.manufacturer && comp.manufacturer.toLowerCase().includes(search)) ||
                (comp.manufacturer_code && comp.manufacturer_code.toLowerCase().includes(search)) ||
                (comp.value && comp.value.toLowerCase().includes(search)) ||
                (comp.package && comp.package.toLowerCase().includes(search)) ||
                (comp.product_type && comp.product_type.toLowerCase().includes(search)) ||
                (comp.seller && comp.seller.toLowerCase().includes(search)) ||
                (comp.seller_code && comp.seller_code.toLowerCase().includes(search)) ||
                (comp.smd_footprint && comp.smd_footprint.toLowerCase().includes(search))
            );
        });
    }
    
    if (type) {
        filtered = filtered.filter(comp => comp.product_type === type);
    }
    
    if (pkg) {
        filtered = filtered.filter(comp => comp.package === pkg);
    }
    
    console.log('[Search] Filtered to:', filtered.length, 'components');
    renderComponentsTable(filtered);
}

function renderComponentsTable(components) {
    const tbody = document.getElementById('components-table-body');
    
    if (components.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                    No components found
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = components.map(comp => {
        // Debug first component to see actual field names from API
        if (comp.id === components[0].id) {
            console.log('[Component Render] Sample component fields:', {
                id: comp.id,
                seller: comp.seller,
                seller_code: comp.seller_code,
                allFields: Object.keys(comp)
            });
        }
        
        return `
        <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
            <td class="px-3 py-3 text-sm text-gray-900 dark:text-gray-100">${comp.product_type || '-'}</td>
            <td class="px-3 py-3 text-sm font-medium text-gray-900 dark:text-gray-100">${comp.value || '-'}</td>
            <td class="px-3 py-3 text-sm text-gray-700 dark:text-gray-300 font-mono text-xs" title="${comp.manufacturer_code || ''}">${comp.manufacturer_code || '-'}</td>
            <td class="px-3 py-3 text-sm text-gray-700 dark:text-gray-300">${comp.package || '-'}</td>
            <td class="px-3 py-3 text-sm text-gray-700 dark:text-gray-300">${comp.manufacturer || '-'}</td>
            <td class="px-3 py-3 text-sm text-gray-700 dark:text-gray-300">
                <div class="max-w-xs">
                    <div class="font-medium">${comp.seller || '-'}</div>
                    <div class="text-xs text-gray-500 truncate" title="${comp.seller_code || ''}">${comp.seller_code || '-'}</div>
                </div>
            </td>
            <td class="px-3 py-3 text-sm">
                ${getStockBadge(comp.qty_left !== undefined ? comp.qty_left : (comp.stock_qty !== undefined ? comp.stock_qty : 0))}
            </td>
            <td class="px-3 py-3 text-sm text-gray-700 dark:text-gray-300">
                €${(parseFloat(comp.price) || parseFloat(comp.unit_price) || 0).toFixed(4)}
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
        
        // Load jobs first if not already loaded (needed for production count)
        if (allJobs.length === 0) {
            try {
                const jobsResponse = await fetch(`${ELECTRONICS_API_BASE}/jobs?limit=1000`);
                if (jobsResponse.ok) {
                    const jobsData = await jobsResponse.json();
                    allJobs = Array.isArray(jobsData) ? jobsData : [];
                }
            } catch (error) {
                console.log('[Boards] Could not load jobs for production count:', error);
            }
        }
        
        // Load BOM for each board to get accurate component counts and production stats
        await Promise.all(allBoards.map(async (board) => {
            try {
                const bomResponse = await fetch(`${ELECTRONICS_API_BASE}/boards/${board.id}/bom`);
                if (bomResponse.ok) {
                    const bom = await bomResponse.json();
                    board.bom_count = Array.isArray(bom) ? bom.length : 0;
                } else {
                    board.bom_count = 0;
                }
            } catch (error) {
                console.error(`Error loading BOM for board ${board.id}:`, error);
                board.bom_count = 0;
            }
            
            // Calculate production count from completed jobs
            board.produced_count = allJobs.filter(job => 
                job.board_id === board.id && job.status === 'completed'
            ).reduce((sum, job) => sum + (job.quantity || 0), 0);
        }));
        
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
    
    // Debug first board to see actual structure
    if (boards.length > 0) {
        console.log('[Boards Render] Sample board fields:', Object.keys(boards[0]), boards[0]);
    }
    
    grid.innerHTML = boards.map(board => {
        // Handle both 'board_name' and 'name' fields
        const boardName = board.name || board.board_name || `Board #${board.id}`;
        const version = board.version || 'v1.0';
        const variant = board.variant || '';
        const description = board.description || '';
        const bomCount = board.bom_count || 0;
        const filesCount = board.files_count || 0;
        
        return `
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4 hover:shadow-lg transition cursor-pointer"
             onclick="viewBoardDetails(${board.id})">
            <div class="flex items-start justify-between mb-3">
                <div>
                    <h4 class="text-lg font-semibold text-gray-900 dark:text-white">${boardName}</h4>
                    <p class="text-sm text-gray-600 dark:text-gray-400">V${version} - ID${board.id}</p>
                </div>
                <i class="fas fa-microchip text-blue-500 text-2xl"></i>
            </div>
            ${description ? `<p class="text-sm text-gray-700 dark:text-gray-300 mb-3">${description}</p>` : ''}
            <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                <span><i class="fas fa-list mr-1"></i>${bomCount} components</span>
                <span><i class="fas fa-industry mr-1"></i>${board.produced_count || 0} produced</span>
            </div>
        </div>
    `;
    }).join('');
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
    
    // Transform board_name to name for API compatibility
    const apiData = {
        name: data.board_name,
        version: data.version,
        variant: data.variant || '',
        description: data.description || ''
    };
    
    try {
        const response = await fetch(`${ELECTRONICS_API_BASE}/boards`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(apiData)
        });
        
        if (response.ok) {
            showToast('Board created successfully', 'success');
            closeAddBoardModal();
            loadBoards();
        } else {
            const error = await response.json();
            console.error('Board creation error:', error);
            throw new Error(error.detail || 'Failed to create board');
        }
    } catch (error) {
        console.error('Error creating board:', error);
        showToast('Failed to create board: ' + error.message, 'error');
    }
});

async function viewBoardDetails(boardId) {
    currentBoardId = boardId;
    const board = allBoards.find(b => b.id === boardId);
    if (!board) return;
    
    // Handle both 'board_name' and 'name' fields
    const boardName = board.name || board.board_name || 'Unnamed Board';
    const version = board.version || 'v1.0';
    const variant = board.variant || '';
    
    document.getElementById('board-detail-name').textContent = boardName;
    document.getElementById('board-detail-version').textContent = `${version}${variant ? ` - ${variant}` : ''}`;
    
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
    const tbody = document.getElementById('board-bom-table');
    
    // Show loading state
    tbody.innerHTML = '<tr><td colspan="8" class="px-4 py-8 text-center text-gray-500"><i class="fas fa-spinner fa-spin mr-2"></i>Loading BOM...</td></tr>';
    
    try {
        const response = await fetch(`${ELECTRONICS_API_BASE}/boards/${boardId}/bom`);
        const data = await response.json();
        
        console.log('[BOM] Loaded BOM data:', data);
        
        // Check for error in response
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Handle both {bom: [...]} and direct array responses
        const bomItems = Array.isArray(data) ? data : (data.bom || []);
        
        if (bomItems.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="px-4 py-8 text-center text-gray-500">No BOM data</td></tr>';
            return;
        }
        
        tbody.innerHTML = bomItems.map(item => `
            <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
                <td class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">${item.component_id}</td>
                <td class="px-4 py-3 text-sm font-mono text-gray-900 dark:text-gray-100">${item.designators || '-'}</td>
                <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">${item.product_type || '-'}</td>
                <td class="px-4 py-3 text-sm text-gray-600 dark:text-gray-400 font-mono">${item.seller_code || '-'}</td>
                <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-gray-100">${item.value || '-'}</td>
                <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">${item.package || '-'}</td>
                <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">${item.qty}</td>
                <td class="px-4 py-3 text-sm">${item.component_id ? getStockBadge(item.qty_left) : '<span class="text-xs text-gray-400">Not linked</span>'}</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading BOM:', error);
        tbody.innerHTML = '<tr><td colspan="8" class="px-4 py-8 text-center text-red-500">Error loading BOM</td></tr>';
    }
}

async function loadBoardFiles(boardId) {
    try {
        const response = await fetch(`${ELECTRONICS_API_BASE}/files?board_id=${boardId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        console.log('[Board Files] API response:', data);
        
        const container = document.getElementById('board-files-list');
        
        // Handle both array response and {files: [...]} response
        const filesList = Array.isArray(data) ? data : (data.files || []);
        
        if (filesList.length === 0) {
            container.innerHTML = '<p class="text-center text-gray-500 py-8">No files registered</p>';
            return;
        }
        
        container.innerHTML = filesList.map(file => `
            <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    <i class="fas ${getFileIcon(file.file_type)} text-2xl text-gray-600 dark:text-gray-400"></i>
                    <div>
                        <p class="text-sm font-medium text-gray-900 dark:text-gray-100">${file.display_name || file.filename || file.file_path}</p>
                        <p class="text-xs text-gray-500 dark:text-gray-400">${file.file_type}</p>
                    </div>
                </div>
                <div class="flex items-center space-x-2">
                    ${file.file_type === 'ibom' ? `
                        <button onclick="viewIBOMFromBoard('${file.file_path}')" 
                                class="px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white text-xs rounded">
                            <i class="fas fa-eye mr-1"></i>View
                        </button>
                    ` : file.file_type === 'bom_csv' ? `
                        <button onclick="loadBOMFromFile('${file.file_path}')" 
                                class="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-xs rounded">
                            <i class="fas fa-upload mr-1"></i>Load BOM
                        </button>
                        <a href="${ELECTRONICS_STORAGE_URL}/${file.file_path}" target="_blank"
                           class="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded">
                            <i class="fas fa-external-link-alt mr-1"></i>Open
                        </a>
                    ` : file.file_type === 'pnp_csv' ? `
                        <button onclick="loadPnPFromFile('${file.file_path}')" 
                                class="px-3 py-1 bg-orange-600 hover:bg-orange-700 text-white text-xs rounded">
                            <i class="fas fa-upload mr-1"></i>Load PnP
                        </button>
                        <a href="${ELECTRONICS_STORAGE_URL}/${file.file_path}" target="_blank"
                           class="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded">
                            <i class="fas fa-external-link-alt mr-1"></i>Open
                        </a>
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
        const container = document.getElementById('board-files-list');
        container.innerHTML = '<p class="text-center text-red-500 py-8">Error loading files</p>';
    }
}

function viewIBOMFromBoard(filePath) {
    // Close board details modal
    closeBoardDetailsModal();
    // Switch to Files tab
    switchTab('files');
    // Open iBOM viewer
    setTimeout(() => {
        openIBOMViewer(filePath);
    }, 100);
}

async function loadBOMFromFile(filePath) {
    try {
        // Use proxy endpoint to bypass CORS
        const response = await fetch(`${ELECTRONICS_API_BASE}/storage/fetch?path=${encodeURIComponent(filePath)}`);
        if (!response.ok) throw new Error('Failed to fetch BOM file');
        
        let headers, rows;
        
        // Check file extension
        const fileName = filePath.toLowerCase();
        const isExcel = fileName.endsWith('.xlsx') || fileName.endsWith('.xls');
        
        if (isExcel) {
            // Parse Excel file
            const arrayBuffer = await response.arrayBuffer();
            const workbook = XLSX.read(arrayBuffer, { type: 'array' });
            
            // Get first sheet
            const firstSheetName = workbook.SheetNames[0];
            const worksheet = workbook.Sheets[firstSheetName];
            
            // Convert to JSON
            const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1, defval: '' });
            
            if (jsonData.length < 2) {
                showToast('Excel file must have at least a header row and one data row', 'error');
                return;
            }
            
            // First row is headers
            headers = jsonData[0].map(h => String(h).trim());
            
            // Remaining rows are data
            rows = jsonData.slice(1).map(row => {
                const obj = {};
                headers.forEach((header, idx) => {
                    obj[header] = row[idx] != null ? String(row[idx]).trim() : '';
                });
                return obj;
            }).filter(row => Object.values(row).some(v => v));
            
            console.log('[Excel] Loaded', rows.length, 'rows from server file');
        } else {
            // Parse CSV
            const text = await response.text();
            const parsed = parseCSV(text);
            headers = parsed.headers;
            rows = parsed.rows;
        }
        
        const mapped = rows.map(mapBOMRow).filter(r => r !== null);
        
        if (mapped.length === 0) {
            showToast('No valid BOM data found in file', 'error');
            return;
        }
        
        parsedCSVData = mapped;
        
        // Open upload modal with pre-loaded data
        document.getElementById('upload-bom-board-id').value = currentBoardId;
        
        // Show preview
        const previewContainer = document.getElementById('bom-preview-container');
        const headerRow = document.getElementById('bom-preview-header');
        const bodyRows = document.getElementById('bom-preview-body');
        const stats = document.getElementById('bom-preview-stats');
        
        headerRow.innerHTML = headers.map(h => 
            `<th class="px-2 py-1 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">${h}</th>`
        ).join('');
        
        bodyRows.innerHTML = rows.slice(0, 5).map(row => {
            return '<tr class="text-xs">' + headers.map(h => 
                `<td class="px-2 py-1 text-gray-900 dark:text-gray-100">${row[h] || '-'}</td>`
            ).join('') + '</tr>';
        }).join('');
        
        stats.textContent = `Loaded ${mapped.length} valid components from registered file`;
        previewContainer.classList.remove('hidden');
        
        // Hide file upload input since we already loaded a file
        const fileInputContainer = document.querySelector('#upload-bom-form > div:first-of-type');
        const fileInput = document.getElementById('bom-csv-file');
        if (fileInputContainer) {
            fileInputContainer.style.display = 'none';
        }
        if (fileInput) {
            fileInput.removeAttribute('required'); // Remove required to prevent form validation error
        }
        
        // Change modal title to indicate we're loading from existing file
        const modalTitle = document.querySelector('#upload-bom-modal h3');
        if (modalTitle) {
            modalTitle.innerHTML = '<i class="fas fa-file-import text-blue-600 mr-2"></i>Load BOM from File';
        }
        
        // Open modal
        document.getElementById('upload-bom-modal').classList.remove('hidden');
        document.getElementById('upload-bom-modal').classList.add('flex');
        
        showToast(`Loaded ${mapped.length} components from file`, 'success');
        
    } catch (error) {
        console.error('[Load BOM] Error:', error);
        showToast('Failed to load BOM file: ' + error.message, 'error');
    }
}

async function loadPnPFromFile(filePath) {
    try {
        // Use proxy endpoint to bypass CORS
        const response = await fetch(`${ELECTRONICS_API_BASE}/storage/fetch?path=${encodeURIComponent(filePath)}`);
        if (!response.ok) throw new Error('Failed to fetch PnP file');
        
        const text = await response.text();
        
        // Open PnP upload modal and populate with data
        showUploadPnPModal();
        
        // Set to paste mode and fill textarea
        const pasteRadio = document.querySelector('input[name="pnp-upload-method"][value="paste"]');
        if (pasteRadio) {
            pasteRadio.checked = true;
            togglePnPUploadMethod();
        }
        
        document.getElementById('pnp-csv-data').value = text;
        
        // Auto-fill filename from path
        const filename = filePath.split('/').pop().replace(/\.[^/.]+$/, '');
        document.getElementById('pnp-filename').value = filename;
        
        // Set board ID to current board
        document.getElementById('upload-pnp-board-id').value = currentBoardId;
        
        showToast('Loaded PnP file data', 'success');
        
    } catch (error) {
        console.error('[Load PnP] Error:', error);
        showToast('Failed to load PnP file: ' + error.message, 'error');
    }
}

function uploadBOM() {
    document.getElementById('upload-bom-board-id').value = currentBoardId;
    parsedCSVData = null;
    document.getElementById('bom-preview-container').classList.add('hidden');
    document.getElementById('upload-bom-modal').classList.remove('hidden');
    document.getElementById('upload-bom-modal').classList.add('flex');
    
    // Add file change listener
    const fileInput = document.getElementById('bom-csv-file');
    if (fileInput && !fileInput.hasAttribute('data-listener')) {
        fileInput.setAttribute('data-listener', 'true');
        fileInput.addEventListener('change', handleBOMFileSelect);
    }
}

function closeUploadBOMModal() {
    document.getElementById('upload-bom-modal').classList.add('hidden');
    document.getElementById('upload-bom-modal').classList.remove('flex');
    document.getElementById('upload-bom-form').reset();
    document.getElementById('bom-preview-container').classList.add('hidden');
    parsedCSVData = null;
    
    // Reset file input visibility (in case it was hidden when loading from file)
    const fileInputContainer = document.querySelector('#upload-bom-form > div:first-of-type');
    const fileInput = document.getElementById('bom-csv-file');
    if (fileInputContainer) {
        fileInputContainer.style.display = '';
    }
    if (fileInput) {
        fileInput.setAttribute('required', ''); // Restore required attribute for normal uploads
    }
    
    // Reset modal title
    const modalTitle = document.querySelector('#upload-bom-modal h3');
    if (modalTitle) {
        modalTitle.innerHTML = '<i class="fas fa-upload text-blue-600 mr-2"></i>Upload BOM';
    }
}

async function handleBOMFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    try {
        let headers, rows;
        
        // Check file extension to determine parsing method
        const fileName = file.name.toLowerCase();
        const isExcel = fileName.endsWith('.xlsx') || fileName.endsWith('.xls');
        
        if (isExcel) {
            // Parse Excel file
            const data = await file.arrayBuffer();
            const workbook = XLSX.read(data, { type: 'array' });
            
            // Get first sheet
            const firstSheetName = workbook.SheetNames[0];
            const worksheet = workbook.Sheets[firstSheetName];
            
            // Convert to JSON (array of objects)
            const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1, defval: '' });
            
            if (jsonData.length < 2) {
                showToast('Excel file must have at least a header row and one data row', 'error');
                return;
            }
            
            // First row is headers
            headers = jsonData[0].map(h => String(h).trim());
            
            // Remaining rows are data - convert back to object format
            rows = jsonData.slice(1).map(row => {
                const obj = {};
                headers.forEach((header, idx) => {
                    obj[header] = row[idx] != null ? String(row[idx]).trim() : '';
                });
                return obj;
            }).filter(row => Object.values(row).some(v => v)); // Filter out completely empty rows
            
            console.log('[Excel] Parsed', rows.length, 'rows from', firstSheetName);
        } else {
            // Parse CSV file
            const text = await file.text();
            const parsed = parseCSV(text);
            headers = parsed.headers;
            rows = parsed.rows;
        }
        
        // Map rows to BOM format
        const mapped = rows.map(mapBOMRow).filter(r => r !== null);
        
        if (mapped.length === 0) {
            showToast('No valid BOM data found. Check file format.', 'error');
            return;
        }
        
        parsedCSVData = mapped;
        
        // Show preview
        const previewContainer = document.getElementById('bom-preview-container');
        const headerRow = document.getElementById('bom-preview-header');
        const bodyRows = document.getElementById('bom-preview-body');
        const stats = document.getElementById('bom-preview-stats');
        
        // Render header
        headerRow.innerHTML = headers.map(h => 
            `<th class="px-2 py-1 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">${h}</th>`
        ).join('');
        
        // Render first 5 rows
        bodyRows.innerHTML = rows.slice(0, 5).map(row => {
            return '<tr class="text-xs">' + headers.map(h => 
                `<td class="px-2 py-1 text-gray-900 dark:text-gray-100">${row[h] || '-'}</td>`
            ).join('') + '</tr>';
        }).join('');
        
        stats.textContent = `Detected ${mapped.length} valid components from ${rows.length} total rows`;
        previewContainer.classList.remove('hidden');
        
        console.log('[CSV] Preview ready:', mapped.length, 'components');
        
    } catch (error) {
        console.error('[CSV] Parse error:', error);
        showToast('Failed to parse CSV file: ' + error.message, 'error');
    }
}

// Edit BOM Modal
let currentBOMItems = [];

async function showEditBOMModal() {
    if (!currentBoardId) return;
    
    // Load current BOM
    try {
        const response = await fetch(`${ELECTRONICS_API_BASE}/boards/${currentBoardId}/bom`);
        const data = await response.json();
        // Handle both array and object responses
        currentBOMItems = Array.isArray(data) ? data : (data.bom || []);
        
        console.log('[Edit BOM] Loaded', currentBOMItems.length, 'items');
        
        // Clear search input
        const searchInput = document.getElementById('bom-component-search');
        if (searchInput) {
            searchInput.value = '';
        }
        
        // Setup search listeners if not already set
        setupBOMComponentSearch();
        
        renderEditBOMTable();
        
        document.getElementById('edit-bom-modal').classList.remove('hidden');
        document.getElementById('edit-bom-modal').classList.add('flex');
    } catch (error) {
        console.error('Error loading BOM for edit:', error);
        showToast('Failed to load BOM', 'error');
    }
}

let selectedBOMComponent = null;

function setupBOMComponentSearch() {
    const searchInput = document.getElementById('bom-component-search');
    const resultsDiv = document.getElementById('bom-component-results');
    
    if (!searchInput || searchInput.dataset.initialized) return;
    searchInput.dataset.initialized = 'true';
    
    let searchDebounce;
    
    searchInput.addEventListener('input', function() {
        clearTimeout(searchDebounce);
        const query = this.value.trim().toLowerCase();
        
        if (query.length < 2) {
            resultsDiv.classList.add('hidden');
            return;
        }
        
        searchDebounce = setTimeout(() => {
            // Search components
            const matches = allComponents.filter(comp => {
                const searchStr = `${comp.value || ''} ${comp.manufacturer_code || ''} ${comp.mpn || ''} ${comp.seller_code || ''} ${comp.product_type || ''} ${comp.package || ''}`.toLowerCase();
                return searchStr.includes(query);
            }).slice(0, 20); // Limit to 20 results
            
            if (matches.length === 0) {
                resultsDiv.innerHTML = '<div class="px-3 py-2 text-sm text-gray-500">No components found</div>';
                resultsDiv.classList.remove('hidden');
                return;
            }
            
            resultsDiv.innerHTML = matches.map(comp => {
                const label = `${comp.value || comp.manufacturer_code || 'Unknown'} - ${comp.package || ''} (${comp.product_type || ''})`;
                const sellerCode = comp.seller_code ? `<span class="text-xs text-gray-500 ml-2">${comp.seller_code}</span>` : '';
                return `
                    <div class="px-3 py-2 hover:bg-blue-50 dark:hover:bg-blue-900/20 cursor-pointer border-b border-gray-200 dark:border-gray-700 last:border-b-0" 
                         onclick="selectBOMComponent(${comp.id}, '${label.replace(/'/g, "\\'")}')">
                        <div class="text-sm text-gray-900 dark:text-gray-100">${label}</div>
                        <div class="text-xs text-gray-600 dark:text-gray-400">ID: ${comp.id}${sellerCode}</div>
                    </div>
                `;
            }).join('');
            
            resultsDiv.classList.remove('hidden');
        }, 300);
    });
    
    // Hide results when clicking outside
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !resultsDiv.contains(e.target)) {
            resultsDiv.classList.add('hidden');
        }
    });
}

function selectBOMComponent(componentId, label) {
    selectedBOMComponent = componentId;
    const searchInput = document.getElementById('bom-component-search');
    const resultsDiv = document.getElementById('bom-component-results');
    
    searchInput.value = label;
    resultsDiv.classList.add('hidden');
    
    // Auto-fill component ID field
    document.getElementById('bom-component-id').value = componentId;
    
    // Trigger component preview
    const event = new Event('input', { bubbles: true });
    document.getElementById('bom-component-id').dispatchEvent(event);
}

function closeEditBOMModal() {
    document.getElementById('edit-bom-modal').classList.add('hidden');
    document.getElementById('edit-bom-modal').classList.remove('flex');
    document.getElementById('add-bom-item-form').reset();
    currentBOMItems = [];
}

function renderEditBOMTable() {
    const tbody = document.getElementById('edit-bom-table');
    
    if (currentBOMItems.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="px-4 py-8 text-center text-gray-500">No components in BOM</td></tr>';
        return;
    }
    
    tbody.innerHTML = currentBOMItems.map((item, index) => `
        <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
            <td class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">${item.component_id}</td>
            <td class="px-4 py-3 text-sm font-mono">${item.designators || item.designator || '-'}</td>
            <td class="px-4 py-3 text-sm">${item.product_type || '-'}</td>
            <td class="px-4 py-3 text-sm font-medium">${item.value || '-'}</td>
            <td class="px-4 py-3 text-sm">${item.package || '-'}</td>
            <td class="px-4 py-3 text-sm">
                <input type="number" min="1" value="${item.quantity || item.qty || 1}" 
                       onchange="updateBOMQuantity(${index}, this.value)"
                       class="w-16 px-2 py-1 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                       title="Edit quantity">
            </td>
            <td class="px-4 py-3 text-sm text-right">
                <button onclick="removeBOMItem(${index})" 
                        class="text-red-600 hover:text-red-800 dark:text-red-400"
                        title="Remove">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

function removeBOMItem(index) {
    currentBOMItems.splice(index, 1);
    renderEditBOMTable();
}

function updateBOMQuantity(index, newQuantity) {
    const qty = parseInt(newQuantity);
    if (qty > 0) {
        currentBOMItems[index].quantity = qty;
        console.log(`[BOM] Updated quantity for item ${index} to ${qty}`);
    }
}

document.getElementById('add-bom-item-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Get component ID from either search selection or direct ID input
    let componentId = selectedBOMComponent || document.getElementById('bom-component-id').value;
    
    if (!componentId) {
        componentId = document.getElementById('bom-component-id').value;
    }
    
    const designators = document.getElementById('bom-designators').value.trim();
    const quantity = parseInt(document.getElementById('bom-quantity').value);
    
    if (!componentId) {
        showToast('Please select a component or enter a component ID', 'error');
        return;
    }
    
    // Get component data from allComponents array
    let component = allComponents.find(c => c.id === parseInt(componentId));
    
    if (!component) {
        console.error(`[BOM] Component ID ${componentId} not found in loaded components`);
        showToast('Component not found. Please make sure components are loaded and the ID is correct.', 'error');
        return;
    }
    
    console.log(`[BOM] Adding component ${componentId}:`, component.value, component.package);
    
    // Add to BOM items (designators now optional)
    currentBOMItems.push({
        component_id: parseInt(componentId),
        designators: designators || '-',
        quantity: quantity,
        product_type: component.product_type || component.category,
        value: component.value,
        package: component.package
    });
    
    renderEditBOMTable();
    
    // Reset form and hide preview
    document.getElementById('add-bom-item-form').reset();
    document.getElementById('bom-component-preview').classList.add('hidden');
    document.getElementById('bom-component-search').value = '';
    selectedBOMComponent = null;
    showToast('Component added to BOM', 'success');
    
    // Refocus on search field for quick consecutive entries
    document.getElementById('bom-component-search').focus();
});

// Auto-fill component details when ID is entered manually
let componentIdDebounceTimer;
document.getElementById('bom-component-id')?.addEventListener('input', function(e) {
    const componentId = e.target.value.trim();
    const previewDiv = document.getElementById('bom-component-preview');
    
    // Clear previous timer
    clearTimeout(componentIdDebounceTimer);
    
    if (!componentId) {
        // Hide preview if field is empty
        previewDiv.classList.add('hidden');
        return;
    }
    
    // Show loading state
    previewDiv.classList.remove('hidden');
    previewDiv.innerHTML = '<div class="text-gray-600 dark:text-gray-400"><i class="fas fa-spinner fa-spin mr-1"></i>Loading...</div>';
    
    // Debounce: wait 500ms after user stops typing
    componentIdDebounceTimer = setTimeout(() => {
        // Find component in already loaded allComponents array
        const component = allComponents.find(c => c.id === parseInt(componentId));
        
        if (!component) {
            previewDiv.innerHTML = '<div class="text-red-600 dark:text-red-400"><i class="fas fa-exclamation-circle mr-1"></i>Component not found</div>';
            return;
        }
        
        // Display component details
        const details = [
            component.seller_code ? `<strong>Seller:</strong> ${component.seller_code}` : null,
            component.manufacturer ? `<strong>Mfr:</strong> ${component.manufacturer}` : null,
            component.manufacturer_code ? `<strong>Mfr Code:</strong> ${component.manufacturer_code}` : null,
            component.value ? `<strong>Value:</strong> ${component.value}` : null,
            component.package ? `<strong>Package:</strong> ${component.package}` : null,
            component.product_type ? `<strong>Type:</strong> ${component.product_type}` : null
        ].filter(Boolean).join(' • ');
        
        previewDiv.innerHTML = `
            <div class="text-green-600 dark:text-green-400 mb-1">
                <i class="fas fa-check-circle mr-1"></i>Component found
            </div>
            <div class="text-gray-700 dark:text-gray-300 text-sm break-words">${details || 'No details available'}</div>
        `;
    }, 500);
});

async function saveBOM() {
    if (!currentBoardId) return;
    
    try {
        // Format data according to API spec: array of {component_id, qty, designators}
        const bomData = currentBOMItems.map(item => ({
            component_id: parseInt(item.component_id),
            qty: parseInt(item.quantity || item.qty) || 1,
            designators: item.designators || null
        }));
        
        console.log('[BOM] Saving BOM data:', JSON.stringify(bomData, null, 2));
        
        const response = await fetch(`${ELECTRONICS_API_BASE}/boards/${currentBoardId}/bom`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(bomData)
        });
        
        if (response.ok) {
            showToast('BOM saved successfully', 'success');
            closeEditBOMModal();
            loadBoardBOM(currentBoardId);
        } else {
            const error = await response.json();
            console.error('[BOM] Save failed:', response.status, error);
            
            // Show detailed error if validation failed
            if (error.detail && Array.isArray(error.detail)) {
                const errorMessages = error.detail.map(e => `${e.loc.join('.')}: ${e.msg}`).join(', ');
                throw new Error(`Validation error: ${errorMessages}`);
            }
            
            throw new Error(error.detail || error.error || 'Failed to save BOM');
        }
    } catch (error) {
        console.error('[BOM] Error saving:', error);
        showToast('Failed to save BOM: ' + error.message, 'error');
    }
}

document.getElementById('upload-bom-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    if (!parsedCSVData || parsedCSVData.length === 0) {
        showToast('Please select a valid CSV file first', 'error');
        return;
    }
    
    const boardId = document.getElementById('upload-bom-board-id').value;
    
    try {
        // Build component maps: manufacturer_code -> component_id AND seller_code -> component_id
        const mfrCodeMap = {};
        const sellerCodeMap = {};
        allComponents.forEach(comp => {
            if (comp.manufacturer_code) {
                mfrCodeMap[comp.manufacturer_code.toLowerCase()] = comp;
            }
            if (comp.seller_code) {
                sellerCodeMap[comp.seller_code.toLowerCase()] = comp;
            }
        });
        
        // Map CSV data to component IDs
        let bomItems = [];
        const notFound = [];
        
        for (const item of parsedCSVData) {
            let component = null;
            
            // Try manufacturer code first (if present)
            if (item.manufacturer_code) {
                component = mfrCodeMap[item.manufacturer_code.toLowerCase()];
                if (component) {
                    console.log('[BOM Match] Found by manufacturer_code:', item.manufacturer_code, '→', component.id);
                }
            }
            
            // Try supplier code if manufacturer code didn't match (or wasn't present)
            if (!component && item.supplier_code) {
                component = sellerCodeMap[item.supplier_code.toLowerCase()];
                if (component) {
                    console.log('[BOM Match] Found by supplier_code:', item.supplier_code, '→', component.id);
                }
            }
            
            if (!component) {
                console.log('[BOM No Match] manufacturer_code:', item.manufacturer_code || 'N/A', 'supplier_code:', item.supplier_code || 'N/A');
            }
            
            if (component) {
                const bomItem = {
                    component_id: component.id,
                    qty: item.qty
                };
                // Include designators if present
                if (item.designators) {
                    bomItem.designators = item.designators;
                }
                bomItems.push(bomItem);
            } else {
                notFound.push(item);
            }
        }
        
        // If some components not found, offer manual mapping
        if (notFound.length > 0) {
            console.log('[BOM Upload] Found', bomItems.length, 'auto-mapped,', notFound.length, 'unmapped');
            // Store bomItems in global scope for manual mapping
            window._tempBomItems = bomItems;
            const proceed = await showManualMappingModal(notFound, bomItems);
            
            // Restore from global (it will have manually mapped items added)
            // Clone the array to avoid reference issues
            const finalBomItems = [...window._tempBomItems];
            delete window._tempBomItems;
            
            console.log('[BOM Upload] After mapping - proceed:', proceed, 'items:', finalBomItems?.length);
            
            if (!proceed) return;
            
            // Replace bomItems with final list
            bomItems = finalBomItems;
        }
        
        console.log('[BOM Upload] Final count:', bomItems.length, 'components');
        
        if (bomItems.length === 0) {
            showToast('No components to upload', 'error');
            return;
        }
        
        // Deduplicate by component_id: merge quantities and designators
        const componentMap = new Map();
        for (const item of bomItems) {
            const key = item.component_id;
            if (componentMap.has(key)) {
                const existing = componentMap.get(key);
                // Sum quantities
                existing.qty += item.qty;
                // Merge designators
                if (item.designators) {
                    const existingDesignators = existing.designators ? existing.designators.split(',') : [];
                    const newDesignators = item.designators.split(',');
                    const allDesignators = [...new Set([...existingDesignators, ...newDesignators])];
                    existing.designators = allDesignators.join(',');
                }
            } else {
                componentMap.set(key, {...item});
            }
        }
        
        // Convert back to array
        bomItems = Array.from(componentMap.values());
        console.log('[BOM Upload] After deduplication:', bomItems.length, 'unique components');
        
        // Batch insert components - send all at once as array
        console.log('[BOM Upload] Inserting', bomItems.length, 'components to board', boardId);
        
        try {
            const response = await fetch(`${ELECTRONICS_API_BASE}/boards/${boardId}/bom`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(bomItems)
            });
            
            if (response.ok) {
                showToast(`BOM uploaded: ${bomItems.length} components added`, 'success');
                closeUploadBOMModal();
                loadBoardBOM(boardId);
            } else {
                const errorData = await response.json().catch(() => ({}));
                console.error('[BOM Upload] Failed:', errorData);
                throw new Error(errorData.error || errorData.detail || 'Failed to upload BOM');
            }
        } catch (error) {
            console.error('[BOM Upload] Error:', error);
            showToast('Failed to upload BOM: ' + error.message, 'error');
        }
        
    } catch (error) {
        console.error('[BOM Upload] Error:', error);
        showToast('Failed to upload BOM: ' + error.message, 'error');
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
            
            if (!response.ok) {
                // If jobs endpoint returns 500 or 404, show appropriate message
                if (response.status === 404) {
                    console.warn('[Jobs] Jobs endpoint not available');
                    const grid = document.getElementById('jobs-grid');
                    if (grid) {
                        grid.innerHTML = `
                            <div class="col-span-full text-center py-8">
                                <i class="fas fa-info-circle text-4xl text-blue-500 dark:text-blue-400 mb-3"></i>
                                <p class="text-gray-600 dark:text-gray-400 mb-2">Production jobs not yet available</p>
                                <p class="text-sm text-gray-500 dark:text-gray-500">The jobs API endpoint is not configured</p>
                            </div>
                        `;
                    }
                    allJobs = [];
                    return;
                } else if (response.status === 500) {
                    console.error('[Jobs] Server error loading jobs');
                    const grid = document.getElementById('jobs-grid');
                    if (grid) {
                        grid.innerHTML = `
                            <div class="col-span-full text-center py-8">
                                <i class="fas fa-exclamation-triangle text-4xl text-yellow-500 mb-3"></i>
                                <p class="text-gray-600 dark:text-gray-400 mb-2">Server error loading jobs</p>
                                <p class="text-sm text-gray-500 dark:text-gray-500">The jobs API endpoint returned an error</p>
                            </div>
                        `;
                    }
                    allJobs = [];
                    return;
                }
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            // Ensure it's an array
            if (!Array.isArray(data)) {
                console.error('[Jobs] Expected array, got:', typeof data, data);
                allJobs = [];
                break;
            }
            
            const count = data.length;
            
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
        allJobs = [];
        const grid = document.getElementById('jobs-grid');
        if (grid) {
            grid.innerHTML = `
                <div class="col-span-full text-center py-8">
                    <i class="fas fa-exclamation-triangle text-4xl text-red-500 mb-3"></i>
                    <p class="text-gray-600 dark:text-gray-400">Failed to load jobs</p>
                    <p class="text-sm text-gray-500 dark:text-gray-500">${error.message}</p>
                </div>
            `;
        }
    }
}

function renderJobsGrid(jobs) {
    const grid = document.getElementById('jobs-grid');
    
    if (!grid) {
        console.error('[Jobs] jobs-grid element not found');
        return;
    }
    
    if (!jobs || jobs.length === 0) {
        grid.innerHTML = '<div class="col-span-full text-center py-8"><p class="text-gray-500 dark:text-gray-400">No jobs found</p></div>';
        return;
    }
    
    grid.innerHTML = jobs.map(job => {
        // Find the board for this job
        const board = allBoards.find(b => b.id === job.board_id);
        const boardName = board ? `${board.name || board.board_name || 'Unnamed'} - ${board.version}` : `Board #${job.board_id}`;
        const jobTitle = `Job #${job.job_id || job.id}`;
        const status = job.status || 'created';
        const quantity = job.quantity || 1;
        const pnpJob = job.pnp_job || 0;
        const dueDate = job.due_date ? new Date(job.due_date).toLocaleDateString() : null;
        
        return `
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4 hover:shadow-lg transition cursor-pointer"
             onclick="viewJobDetails(${job.job_id || job.id})">
            <div class="flex items-start justify-between mb-3">
                <div>
                    <h4 class="text-lg font-semibold text-gray-900 dark:text-white">${jobTitle}</h4>
                    <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">${boardName}</p>
                    ${getStatusBadge(status)}
                </div>
                <i class="fas fa-industry text-blue-500 text-2xl"></i>
            </div>
            <div class="flex items-center gap-3 text-sm text-gray-700 dark:text-gray-300 mb-2">
                <span><i class="fas fa-layer-group mr-1"></i>Qty: ${quantity}</span>
                ${pnpJob > 0 ? `<span><i class="fas fa-robot mr-1"></i>PnP: ${pnpJob}</span>` : '<span><i class="fas fa-hand-paper mr-1"></i>Manual</span>'}
            </div>
            ${dueDate ? `<div class="text-xs text-gray-500 dark:text-gray-400">
                <span><i class="fas fa-calendar mr-1"></i>Due: ${dueDate}</span>
            </div>` : ''}
        </div>
    `;
    }).join('');
}

function getStatusBadge(status) {
    const statusColors = {
        created: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
        in_progress: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
        completed: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
        on_hold: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
    };
    const color = statusColors[status] || statusColors.created;
    const displayText = status.replace('_', ' ').charAt(0).toUpperCase() + status.replace('_', ' ').slice(1);
    return `<span class="px-2 py-1 text-xs font-semibold rounded-full ${color}">${displayText}</span>`;
}

function showCreateJobModal() {
    document.getElementById('create-job-modal').classList.remove('hidden');
    document.getElementById('create-job-modal').classList.add('flex');
    
    // Populate board select
    const select = document.getElementById('create-job-board-select');
    if (allBoards.length > 0) {
        select.innerHTML = '<option value="">Select a board...</option>' + 
            allBoards.map(board => 
                `<option value="${board.id}">${board.name || board.board_name || 'Unnamed'} v${board.version} - ${board.id}</option>`
            ).join('');
    } else {
        select.innerHTML = '<option value="">No boards available</option>';
    }
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
    
    // Convert to correct types
    const jobData = {
        board_id: parseInt(data.board_id),
        quantity: parseInt(data.quantity),
        pnp_job: parseInt(data.pnp_job) || 0,
        status: data.status || 'created'
    };
    
    // Add due_date only if provided
    if (data.due_date) {
        jobData.due_date = data.due_date;
    }
    
    try {
        const response = await fetch(`${ELECTRONICS_API_BASE}/jobs`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(jobData)
        });
        
        if (response.ok) {
            showToast('Job created successfully', 'success');
            closeCreateJobModal();
            loadJobs();
        } else {
            const errorData = await response.json().catch(() => ({}));
            const errorMsg = errorData.error || 'Failed to create job';
            console.error('[Job Create] Error:', errorMsg);
            showToast(errorMsg, 'error');
        }
    } catch (error) {
        console.error('[Job Create] Network error:', error);
        showToast(`Network error: ${error.message}`, 'error');
    }
});

async function viewJobDetails(jobId) {
    currentJobId = jobId;
    const job = allJobs.find(j => (j.job_id || j.id) === jobId);
    if (!job) {
        console.error('[Job Details] Job not found:', jobId);
        return;
    }
    
    // Find the board for this job
    const board = allBoards.find(b => b.id === job.board_id);
    const boardName = board ? `${board.name || board.board_name || 'Unnamed'} - ${board.version}` : `Board #${job.board_id}`;
    const jobTitle = `Job #${job.job_id || job.id} - ${boardName}`;
    const quantity = job.quantity || 1;
    const pnpJob = job.pnp_job || 0;
    
    document.getElementById('job-detail-name').textContent = jobTitle;
    const statusText = job.status.replace('_', ' ').charAt(0).toUpperCase() + job.status.replace('_', ' ').slice(1);
    document.getElementById('job-detail-status').textContent = statusText;
    document.getElementById('job-detail-status').className = `px-3 py-1 text-sm font-semibold rounded-full ${getStatusBadge(job.status).split('class="')[1].split('"')[0]}`;
    
    const dateInfo = [];
    if (job.due_date) {
        dateInfo.push(`Due: ${new Date(job.due_date).toLocaleDateString()}`);
    }
    dateInfo.push(`Qty: ${quantity}`);
    if (pnpJob > 0) {
        dateInfo.push(`PnP: ${pnpJob}`);
    }
    document.getElementById('job-detail-date').textContent = dateInfo.join(' • ');
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
        
        console.log('[Job Boards] API response:', data);
        
        const container = document.getElementById('job-boards-list');
        
        // Job data is in data.job, board info is in job.board_id
        const job = data.job || data;
        const board = allBoards.find(b => b.id === job.board_id);
        
        if (!board) {
            container.innerHTML = '<p class="col-span-full text-center text-gray-500 py-8">Board not found</p>';
            return;
        }
        
        container.innerHTML = `
            <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                <div class="flex items-center justify-between">
                    <div>
                        <h5 class="font-semibold text-gray-900 dark:text-white">${board.name || board.board_name || 'Unnamed'}</h5>
                        <p class="text-sm text-gray-600 dark:text-gray-400">v${board.version} - ID${board.id}</p>
                    </div>
                    <div class="text-right">
                        <p class="text-2xl font-bold text-blue-600">${job.quantity}</p>
                        <p class="text-xs text-gray-500">units</p>
                    </div>
                </div>
            </div>
        `;
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
        `<option value="${board.id}">${board.name || board.board_name || 'Unnamed'} v${board.version} - ${board.id}</option>`
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
        
        console.log('[Check Stock] API response:', data);
        
        document.getElementById('stock-check-results').classList.remove('hidden');
        
        // Calculate summary from ok/missing arrays
        const okCount = data.ok ? data.ok.length : 0;
        const missingCount = data.missing ? data.missing.length : 0;
        
        document.getElementById('stock-available-count').textContent = okCount;
        document.getElementById('stock-low-count').textContent = 0;
        document.getElementById('stock-missing-count').textContent = missingCount;
        
        const tbody = document.getElementById('stock-check-table');
        
        // Helper: enrich component data from allComponents cache
        function enrichComp(comp) {
            const cached = allComponents.find(c => c.id === comp.component_id);
            return {
                component_id: comp.component_id,
                seller_code: cached?.seller_code || comp.seller_code || '',
                product_type: cached?.product_type || comp.product_type || '',
                package: cached?.package || comp.package || '',
                value: cached?.value || comp.value || '',
                need: comp.need,
                have: comp.have
            };
        }
        
        function renderStockRow(comp, status) {
            const e = enrichComp(comp);
            const badge = status === 'ok'
                ? '<span class="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 text-xs font-semibold rounded">OK</span>'
                : '<span class="px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 text-xs font-semibold rounded">Missing</span>';
            return `
                <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td class="px-4 py-3 text-sm font-mono text-gray-900 dark:text-gray-100">${e.component_id}</td>
                    <td class="px-4 py-3 text-sm font-mono text-gray-700 dark:text-gray-300">${e.seller_code || '-'}</td>
                    <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">${e.product_type || '-'}</td>
                    <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">${e.package || '-'}</td>
                    <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-gray-100">${e.value || '-'}</td>
                    <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">${e.need}</td>
                    <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">${e.have}</td>
                    <td class="px-4 py-3 text-sm">${badge}</td>
                </tr>
            `;
        }
        
        const okRows = (data.ok || []).map(comp => renderStockRow(comp, 'ok'));
        const missingRows = (data.missing || []).map(comp => renderStockRow(comp, 'missing'));
        
        tbody.innerHTML = [...okRows, ...missingRows].join('');
        
        if (okCount === 0 && missingCount === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="px-4 py-8 text-center text-gray-500">No BOM data for this board</td></tr>';
        }
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
        // Fetch fresh stock check data
        const response = await fetch(`${ELECTRONICS_API_BASE}/jobs/${currentJobId}/check_stock`);
        const data = await response.json();
        
        const missing = data.missing || [];
        if (missing.length === 0) {
            showToast('No missing components to generate a shopping list for', 'info');
            return;
        }
        
        // Enrich with supplier info from allComponents and group by supplier
        const bySupplier = {};
        for (const comp of missing) {
            const cached = allComponents.find(c => c.id === comp.component_id);
            const seller = (cached?.seller || comp.seller || 'UNKNOWN').trim().toUpperCase();
            const sellerCode = cached?.seller_code || comp.seller_code || '';
            const mfrCode = cached?.manufacturer_code || comp.manufacturer_code || '';
            const need = comp.need - comp.have; // only the shortage
            
            if (!bySupplier[seller]) bySupplier[seller] = [];
            bySupplier[seller].push({
                supplier_code: sellerCode,
                manufacturer_code: mfrCode,
                quantity: need > 0 ? need : comp.need
            });
        }
        
        // Generate and download a CSV per supplier
        let fileCount = 0;
        for (const [supplier, items] of Object.entries(bySupplier)) {
            const csvLines = ['Supplier Code,Manufacturer Code,Quantity'];
            for (const item of items) {
                // Escape fields that might contain commas
                const sc = item.supplier_code.includes(',') ? `"${item.supplier_code}"` : item.supplier_code;
                const mc = item.manufacturer_code.includes(',') ? `"${item.manufacturer_code}"` : item.manufacturer_code;
                csvLines.push(`${sc},${mc},${item.quantity}`);
            }
            
            const csvContent = csvLines.join('\n');
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `${supplier}_BOM_JOB_${currentJobId}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            fileCount++;
        }
        
        showToast(`Downloaded ${fileCount} shopping list${fileCount > 1 ? 's' : ''} (${missing.length} components)`, 'success');
        
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
            
            if (!response.ok) {
                console.warn('[Files] Files endpoint returned error:', response.status);
                allFiles = [];
                const grid = document.getElementById('files-grid');
                if (grid) {
                    grid.innerHTML = `
                        <div class="col-span-full text-center py-8">
                            <i class="fas fa-info-circle text-4xl text-blue-500 dark:text-blue-400 mb-3"></i>
                            <p class="text-gray-600 dark:text-gray-400 mb-2">No files available</p>
                            <p class="text-sm text-gray-500 dark:text-gray-500">Upload files to see them here</p>
                        </div>
                    `;
                }
                return;
            }
            
            const data = await response.json();
            
            // Ensure data is an array
            if (!Array.isArray(data)) {
                console.error('[Files] Expected array, got:', typeof data);
                allFiles = [];
                break;
            }
            
            const count = data.length;
            console.log('[Files] Loaded:', count, 'files');
            
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
        
        console.log('[Files] Loaded files:', allFiles.length, 'Sample:', allFiles[0]);
        renderFilesGrid(allFiles);
        
        // Populate board filter if empty
        const boardSelect = document.getElementById('files-board-filter');
        if (boardSelect && allBoards.length > 0) {
            const currentValue = boardSelect.value;
            boardSelect.innerHTML = '<option value="">All Boards</option>' + 
                allBoards.map(board => {
                    const boardName = board.name || 'Unnamed';
                    const version = board.version || 'v1.0';
                    return `<option value="${board.id}">${boardName} - ${version}</option>`;
                }).join('');
            boardSelect.value = currentValue;
        }
    } catch (error) {
        console.error('[Files] Error in loadFiles:', error);
        console.error('[Files] Error stack:', error.stack);
        allFiles = [];
        const grid = document.getElementById('files-grid');
        if (grid) {
            grid.innerHTML = `
                <div class="col-span-full text-center py-8">
                    <i class="fas fa-exclamation-triangle text-4xl text-red-500 mb-3"></i>
                    <p class="text-gray-600 dark:text-gray-400">Failed to load files</p>
                    <p class="text-sm text-gray-500 dark:text-gray-500">${error.message}</p>
                </div>
            `;
        }
        showToast('Failed to load files: ' + error.message, 'error');
    }
}

function renderFilesGrid(files) {
    const grid = document.getElementById('files-grid');
    
    if (!grid) {
        console.error('[Files] files-grid element not found');
        return;
    }
    
    if (!files || files.length === 0) {
        grid.innerHTML = '<div class="col-span-full text-center py-8"><p class="text-gray-500 dark:text-gray-400">No files found</p></div>';
        return;
    }
    
    try {
        grid.innerHTML = files.map(file => {
            const fileType = file.file_type || 'unknown';
            const displayName = file.display_name || file.filename || file.file_path?.split('/').pop() || 'Unknown File';
            const boardName = file.board_name || file.board?.name || file.board?.board_name || 'No board';
            
            return `
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4 hover:shadow-lg transition cursor-pointer"
                 onclick="viewFileDetails(${file.id})">
                <div class="flex items-center justify-between mb-3">
                    <i class="fas ${getFileIcon(fileType)} text-4xl text-gray-600 dark:text-gray-400"></i>
                    ${fileType === 'ibom' ? '<span class="px-2 py-1 bg-purple-100 text-purple-800 text-xs font-semibold rounded">Interactive</span>' : ''}
                </div>
                <h4 class="text-sm font-semibold text-gray-900 dark:text-white mb-1 truncate" title="${displayName}">${displayName}</h4>
                <p class="text-xs text-gray-600 dark:text-gray-400 mb-2">${fileType}</p>
                <p class="text-xs text-gray-500 dark:text-gray-500 truncate" title="${boardName}">${boardName}</p>
            </div>
        `;
        }).join('');
    } catch (error) {
        console.error('[Files] Error rendering grid:', error);
        grid.innerHTML = `
            <div class="col-span-full text-center py-8">
                <i class="fas fa-exclamation-triangle text-4xl text-red-500 mb-3"></i>
                <p class="text-gray-600 dark:text-gray-400">Error displaying files</p>
                <p class="text-sm text-gray-500 dark:text-gray-500">${error.message}</p>
            </div>
        `;
    }
}

function getFileIcon(fileType) {
    const icons = {
        bom: 'fa-file-csv',
        bom_csv: 'fa-file-csv',
        bom_excel: 'fa-file-excel',
        pnp: 'fa-map-marker-alt',
        pnp_csv: 'fa-map-marker-alt',
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
        allBoards.map(board => `<option value="${board.id}">${board.name || 'Unnamed'} - ${board.version}</option>`).join('');
}

function closeRegisterFileModal() {
    document.getElementById('register-file-modal').classList.add('hidden');
    document.getElementById('register-file-modal').classList.remove('flex');
    document.getElementById('register-file-form').reset();
}

// ==================== AUTO-DETECT FILES ====================

let detectedFiles = [];

function showAutoDetectModal() {
    document.getElementById('auto-detect-modal').classList.remove('hidden');
    document.getElementById('auto-detect-modal').classList.add('flex');
    
    // Populate board select
    const select = document.getElementById('auto-detect-board');
    select.innerHTML = '<option value="">Select a board...</option>' + 
        allBoards.map(board => `<option value="${board.id}">${board.name || board.board_name || 'Unnamed'} - ${board.version}</option>`).join('');
    
    // Reset detection results
    document.getElementById('detected-files-container').classList.add('hidden');
    detectedFiles = [];
}

function closeAutoDetectModal() {
    document.getElementById('auto-detect-modal').classList.add('hidden');
    document.getElementById('auto-detect-modal').classList.remove('flex');
    document.getElementById('auto-detect-folder').value = '';
    document.getElementById('detected-files-container').classList.add('hidden');
    detectedFiles = [];
}

// Map frontend file types to API-compatible types
function mapFileTypeToAPI(fileType) {
    // API supports: bom_csv, bom_excel, pnp, gerber, schematic, pcb_layout, ibom, datasheet, documentation, firmware, cad
    // Most types pass through directly, but pnp_csv needs to be mapped to pnp
    const mapping = {
        'pnp_csv': 'pnp'
    };
    return mapping[fileType] || fileType;
}

function detectFileType(filename) {
    const lower = filename.toLowerCase();
    
    // BOM detection
    if (lower.startsWith('bom') && lower.endsWith('.csv')) {
        return 'bom_csv';
    }
    if (lower.startsWith('bom') && (lower.endsWith('.xlsx') || lower.endsWith('.xls'))) {
        return 'bom_excel';
    }
    
    // PnP detection
    if ((lower.startsWith('pnp') || lower.startsWith('pnp_')) && lower.endsWith('.csv')) {
        return 'pnp_csv';
    }
    
    // iBOM detection
    if (lower.includes('ibom') && lower.endsWith('.html')) {
        return 'ibom';
    }
    
    // Gerber detection
    if (lower.endsWith('.gbr') || lower.includes('gerber')) {
        return 'gerber';
    }
    
    // Schematic detection
    if (lower.includes('schematic') || lower.includes('sch')) {
        return 'schematic';
    }
    
    // PCB layout detection
    if (lower.includes('pcb') || lower.includes('layout')) {
        return 'pcb_layout';
    }
    
    // Datasheet detection
    if (lower.includes('datasheet') && lower.endsWith('.pdf')) {
        return 'datasheet';
    }
    
    // Documentation detection
    if (lower.endsWith('.pdf') || lower.endsWith('.md') || lower.endsWith('.txt')) {
        return 'documentation';
    }
    
    // Firmware detection
    if (lower.endsWith('.hex') || lower.endsWith('.bin') || lower.endsWith('.elf')) {
        return 'firmware';
    }
    
    // CAD detection
    if (lower.endsWith('.step') || lower.endsWith('.stl') || lower.endsWith('.stp')) {
        return 'cad';
    }
    
    return null; // Unknown type
}

async function scanFolder() {
    const boardId = document.getElementById('auto-detect-board').value;
    const folderPath = document.getElementById('auto-detect-folder').value.trim();
    
    if (!boardId) {
        showToast('Please select a board', 'error');
        return;
    }
    
    if (!folderPath) {
        showToast('Please enter a folder path', 'error');
        return;
    }
    
    // Show loading
    document.getElementById('scan-loading').classList.remove('hidden');
    document.getElementById('detected-files-container').classList.add('hidden');
    
    try {
        // Fetch directory listing via proxy to avoid CORS issues
        const response = await fetch(`${ELECTRONICS_API_BASE}/storage/list?path=${encodeURIComponent(folderPath)}`);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || 'Folder not found or inaccessible');
        }
        
        const data = await response.json();
        const files = data.files || [];
        
        detectedFiles = [];
        
        files.forEach(filename => {
            const fileType = detectFileType(filename);
            if (!fileType) return; // Skip unknown types
            
            detectedFiles.push({
                filename: filename,
                file_path: `${folderPath}/${filename}`,
                file_type: fileType,
                display_name: filename.replace(/\.[^/.]+$/, ''), // Remove extension
                selected: true,
                board_id: parseInt(boardId)
            });
        });
        
        if (detectedFiles.length === 0) {
            showToast('No recognizable files found in folder', 'warning');
            document.getElementById('scan-loading').classList.add('hidden');
            return;
        }
        
        renderDetectedFiles();
        document.getElementById('scan-loading').classList.add('hidden');
        document.getElementById('detected-files-container').classList.remove('hidden');
        showToast(`Found ${detectedFiles.length} files`, 'success');
        
    } catch (error) {
        console.error('[Auto-Detect] Error:', error);
        showToast('Failed to scan folder: ' + error.message, 'error');
        document.getElementById('scan-loading').classList.add('hidden');
    }
}

function renderDetectedFiles() {
    const tbody = document.getElementById('detected-files-table');
    
    tbody.innerHTML = detectedFiles.map((file, idx) => `
        <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
            <td class="px-4 py-3">
                <input type="checkbox" 
                       id="detect-check-${idx}" 
                       onchange="updateDetectedFileSelection(${idx}, this.checked)"
                       ${file.selected ? 'checked' : ''}
                       class="rounded text-blue-600 focus:ring-blue-500">
            </td>
            <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-gray-100 font-mono">
                ${file.filename}
            </td>
            <td class="px-4 py-3">
                <select id="detect-type-${idx}" 
                        onchange="updateDetectedFileType(${idx}, this.value)"
                        class="px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100">
                    <option value="bom_csv" ${file.file_type === 'bom_csv' ? 'selected' : ''}>BOM (CSV)</option>
                    <option value="bom_excel" ${file.file_type === 'bom_excel' ? 'selected' : ''}>BOM (Excel)</option>
                    <option value="pnp_csv" ${file.file_type === 'pnp_csv' ? 'selected' : ''}>Pick & Place (CSV)</option>
                    <option value="gerber" ${file.file_type === 'gerber' ? 'selected' : ''}>Gerber Files</option>
                    <option value="schematic" ${file.file_type === 'schematic' ? 'selected' : ''}>Schematic</option>
                    <option value="pcb_layout" ${file.file_type === 'pcb_layout' ? 'selected' : ''}>PCB Layout</option>
                    <option value="ibom" ${file.file_type === 'ibom' ? 'selected' : ''}>Interactive BOM</option>
                    <option value="datasheet" ${file.file_type === 'datasheet' ? 'selected' : ''}>Datasheet</option>
                    <option value="documentation" ${file.file_type === 'documentation' ? 'selected' : ''}>Documentation</option>
                    <option value="firmware" ${file.file_type === 'firmware' ? 'selected' : ''}>Firmware</option>
                    <option value="cad" ${file.file_type === 'cad' ? 'selected' : ''}>CAD Files</option>
                </select>
            </td>
            <td class="px-4 py-3">
                <input type="text" 
                       id="detect-name-${idx}"
                       value="${file.display_name}"
                       onchange="updateDetectedFileName(${idx}, this.value)"
                       class="px-2 py-1 text-sm w-full border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100">
            </td>
        </tr>
    `).join('');
    
    updateSelectedCount();
}

function updateDetectedFileSelection(idx, selected) {
    detectedFiles[idx].selected = selected;
    updateSelectedCount();
}

function updateDetectedFileType(idx, fileType) {
    detectedFiles[idx].file_type = fileType;
}

function updateDetectedFileName(idx, displayName) {
    detectedFiles[idx].display_name = displayName;
}

function toggleAllDetected(checked) {
    detectedFiles.forEach((file, idx) => {
        file.selected = checked;
        const checkbox = document.getElementById(`detect-check-${idx}`);
        if (checkbox) checkbox.checked = checked;
    });
    updateSelectedCount();
}

function updateSelectedCount() {
    const count = detectedFiles.filter(f => f.selected).length;
    document.getElementById('selected-count').textContent = count;
}

async function registerDetectedFiles() {
    const selectedFiles = detectedFiles.filter(f => f.selected);
    
    if (selectedFiles.length === 0) {
        showToast('No files selected', 'error');
        return;
    }
    
    let successCount = 0;
    let errorCount = 0;
    
    for (const file of selectedFiles) {
        try {
            const response = await fetch(`${ELECTRONICS_API_BASE}/files/register`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    board_id: file.board_id,
                    file_type: mapFileTypeToAPI(file.file_type),
                    file_path: file.file_path,
                    filename: file.filename,
                    display_name: file.display_name || file.filename
                })
            });
            
            if (response.ok) {
                successCount++;
            } else {
                errorCount++;
                console.error('[Auto-Detect] Failed to register:', file.filename);
            }
        } catch (error) {
            errorCount++;
            console.error('[Auto-Detect] Error registering:', error);
        }
    }
    
    if (successCount > 0) {
        showToast(`Registered ${successCount} file(s)${errorCount > 0 ? `, ${errorCount} failed` : ''}`, 
                 errorCount > 0 ? 'warning' : 'success');
        closeAutoDetectModal();
        loadFiles();
    } else {
        showToast('Failed to register files', 'error');
    }
}

// ==================== END AUTO-DETECT ====================

document.getElementById('register-file-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    
    // Validate board_id
    if (!data.board_id) {
        showToast('Please select a board', 'error');
        return;
    }
    
    // Extract filename from file_path
    const filePath = data.file_path || '';
    const filename = filePath.split('/').pop() || filePath;
    
    // Prepare data for API
    const apiData = {
        board_id: parseInt(data.board_id),
        file_type: mapFileTypeToAPI(data.file_type),
        filename: filename,
        file_path: filePath,
        display_name: data.display_name || filename,
        description: data.description || ''
    };
    
    console.log('[File Register] Original file_type:', data.file_type);
    console.log('[File Register] Mapped file_type:', mapFileTypeToAPI(data.file_type));
    console.log('[File Register] Sending data:', apiData);
    
    try {
        const response = await fetch(`${ELECTRONICS_API_BASE}/files/register`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(apiData)
        });
        
        if (response.ok) {
            showToast('File registered successfully', 'success');
            closeRegisterFileModal();
            loadFiles();
        } else {
            const error = await response.json().catch(() => ({}));
            console.error('[File Register] Error response:', error);
            throw new Error(error.error || error.detail || 'Failed to register file');
        }
    } catch (error) {
        console.error('Error registering file:', error);
        showToast('Failed to register file: ' + error.message, 'error');
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
        // Smart pagination to get all components
        let limit = 100;
        let allData = [];
        
        while (true) {
            const response = await fetch(`${ELECTRONICS_API_BASE}/components?limit=${limit}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            // API returns array directly
            if (!Array.isArray(data)) {
                console.error('[Stock] Expected array, got:', typeof data);
                break;
            }
            
            if (data.length < limit) {
                allData = data;
                break;
            }
            
            limit += 100;
            if (limit > 10000) {
                allData = data;
                break;
            }
        }
        
        allComponents = allData;
        
        // Calculate stats using correct field names
        const total = allComponents.length;
        const available = allComponents.filter(c => {
            const qty = c.qty_left !== undefined ? c.qty_left : c.stock_qty;
            return qty > 10;
        }).length;
        const low = allComponents.filter(c => {
            const qty = c.qty_left !== undefined ? c.qty_left : c.stock_qty;
            return qty > 0 && qty <= 10;
        }).length;
        const out = allComponents.filter(c => {
            const qty = c.qty_left !== undefined ? c.qty_left : c.stock_qty;
            return qty === 0;
        }).length;
        const totalValue = allComponents.reduce((sum, c) => {
            const qty = c.qty_left !== undefined ? c.qty_left : (c.stock_qty || 0);
            const price = c.price !== undefined ? c.price : (c.unit_price || 0);
            return sum + (qty * price);
        }, 0);
        
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
    
    // Apply filters with correct field names
    if (typeFilter) {
        filtered = filtered.filter(c => (c.product_type || c.category) === typeFilter);
    }
    if (statusFilter === 'available') {
        filtered = filtered.filter(c => {
            const qty = c.qty_left !== undefined ? c.qty_left : c.stock_qty;
            return qty > 10;
        });
    } else if (statusFilter === 'low') {
        filtered = filtered.filter(c => {
            const qty = c.qty_left !== undefined ? c.qty_left : c.stock_qty;
            return qty > 0 && qty <= 10;
        });
    } else if (statusFilter === 'out') {
        filtered = filtered.filter(c => {
            const qty = c.qty_left !== undefined ? c.qty_left : c.stock_qty;
            return qty === 0;
        });
    }
    
    // Apply sorting with correct field names
    if (sortFilter === 'qty_asc') {
        filtered.sort((a, b) => {
            const qtyA = a.qty_left !== undefined ? a.qty_left : a.stock_qty;
            const qtyB = b.qty_left !== undefined ? b.qty_left : b.stock_qty;
            return qtyA - qtyB;
        });
    } else if (sortFilter === 'qty_desc') {
        filtered.sort((a, b) => {
            const qtyA = a.qty_left !== undefined ? a.qty_left : a.stock_qty;
            const qtyB = b.qty_left !== undefined ? b.qty_left : b.stock_qty;
            return qtyB - qtyA;
        });
    } else if (sortFilter === 'value_desc') {
        filtered.sort((a, b) => {
            const qtyA = a.qty_left !== undefined ? a.qty_left : a.stock_qty;
            const priceA = a.price !== undefined ? a.price : a.unit_price || 0;
            const qtyB = b.qty_left !== undefined ? b.qty_left : b.stock_qty;
            const priceB = b.price !== undefined ? b.price : b.unit_price || 0;
            return (qtyB * priceB) - (qtyA * priceA);
        });
    } else if (sortFilter === 'type') {
        filtered.sort((a, b) => {
            const typeA = a.product_type || a.category || '';
            const typeB = b.product_type || b.category || '';
            return typeA.localeCompare(typeB);
        });
    }
    
    renderStockTable(filtered);
}

function renderStockTable(components) {
    const tbody = document.getElementById('stock-overview-table');
    
    if (components.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="px-4 py-8 text-center text-gray-500">No components found</td></tr>';
        return;
    }
    
    tbody.innerHTML = components.map(comp => {
        const qty = comp.qty_left !== undefined ? comp.qty_left : comp.stock_qty;
        const price = comp.price !== undefined ? comp.price : comp.unit_price || 0;
        const totalValue = qty * price;
        
        return `
        <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
            <td class="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">${comp.product_type || comp.category || '-'}</td>
            <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-gray-100">${comp.manufacturer_code || comp.mpn || comp.value || '-'}</td>
            <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">${comp.package || '-'}</td>
            <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">${comp.seller || comp.supplier || '-'}</td>
            <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300 font-mono text-xs">${comp.seller_code || comp.supplier_code || '-'}</td>
            <td class="px-4 py-3 text-sm">${getStockBadge(qty)}</td>
            <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">€${price.toFixed(4)}</td>
            <td class="px-4 py-3 text-sm font-semibold text-gray-900 dark:text-gray-100">€${totalValue.toFixed(2)}</td>
        </tr>
    `;
    }).join('');
}

async function exportStockReport() {
    try {
        // Create CSV
        const csv = ['Type,Value,Package,Supplier,Part#,Stock,Price,Total Value\n'];
        allComponents.forEach(comp => {
            const qty = comp.qty_left !== undefined ? comp.qty_left : comp.stock_qty;
            const price = comp.price !== undefined ? comp.price : comp.unit_price || 0;
            const totalValue = (qty * price).toFixed(2);
            csv.push(`${comp.product_type || comp.category || ''},${comp.manufacturer_code || comp.mpn || comp.value || ''},${comp.package || ''},${comp.seller || comp.supplier || ''},${comp.seller_code || comp.supplier_code || ''},${qty},${price},${totalValue}\n`);
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


// ===== ORDER IMPORTER =====

let currentOrderData = null;

async function processOrderFile() {
    const fileInput = document.getElementById('order-file-input');
    const supplierSelect = document.getElementById('order-supplier-select');
    const dateInput = document.getElementById('order-date-input');
    
    if (!fileInput.files || fileInput.files.length === 0) {
        showToast('Please select a file to import', 'error');
        return;
    }
    
    const file = fileInput.files[0];
    const filename = file.name;
    
    // Show processing status
    document.getElementById('order-processing-status').classList.remove('hidden');
    document.getElementById('order-results').classList.add('hidden');
    document.getElementById('order-status-text').textContent = 'Processing order file...';
    
    // Create FormData
    const formData = new FormData();
    formData.append('file', file);
    
    // Try to parse supplier and date from filename
    let supplier = supplierSelect.value;
    let orderDate = dateInput.value;
    
    if (!supplier || !orderDate) {
        // Parse from filename: SUPPLIER_DDMMYY
        const match = filename.match(/^(LCSC|MOUSER|lcsc|mouser)_(\d{6})/i);
        if (match) {
            supplier = match[1].toUpperCase();
            const dateStr = match[2]; // DDMMYY
            const day = dateStr.substring(0, 2);
            const month = dateStr.substring(2, 4);
            const year = '20' + dateStr.substring(4, 6);
            orderDate = `${year}-${month}-${day}`;
        }
    }
    
    if (!supplier) {
        showToast('Could not detect supplier. Please select manually.', 'error');
        document.getElementById('order-processing-status').classList.add('hidden');
        return;
    }
    
    if (!orderDate) {
        showToast('Could not detect order date. Please enter manually.', 'error');
        document.getElementById('order-processing-status').classList.add('hidden');
        return;
    }
    
    formData.append('supplier', supplier);
    formData.append('order_date', orderDate);
    
    try {
        const response = await fetch(`${ELECTRONICS_API_BASE}/orders/parse`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to process order file');
        }
        
        const result = await response.json();
        currentOrderData = result;
        
        displayOrderResults(result);
        
    } catch (error) {
        console.error('[Order Import] Error:', error);
        showToast('Failed to process order file: ' + error.message, 'error');
    } finally {
        document.getElementById('order-processing-status').classList.add('hidden');
    }
}

function displayOrderResults(data) {
    // Debug: Log the data to console
    console.log('[Order Import] Full data:', data);
    console.log('[Order Import] Matched items:', data.matched);
    console.log('[Order Import] Sample matched item:', data.matched[0]);
    
    // Show results section
    document.getElementById('order-results').classList.remove('hidden');
    
    // Display summary
    document.getElementById('result-supplier').textContent = data.supplier;
    document.getElementById('result-date').textContent = new Date(data.order_date).toLocaleDateString();
    document.getElementById('result-total').textContent = data.matched.length + data.unmatched.length;
    
    // Display matched components
    document.getElementById('matched-count').textContent = data.matched.length;
    const matchedBody = document.getElementById('matched-components-body');
    matchedBody.innerHTML = data.matched.map(item => {
        console.log(`[Order Import] Rendering item - Price: ${item.unit_price}, Total: ${item.total_price}`, item);
        return `
        <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
            <td class="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">${item.seller_code || '-'}</td>
            <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">${item.manufacturer || '-'}</td>
            <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">${item.manufacturer_code || '-'}</td>
            <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">${item.package || '-'}</td>
            <td class="px-4 py-3 text-sm text-right text-gray-900 dark:text-gray-100 font-medium">${item.quantity}</td>
            <td class="px-4 py-3 text-sm text-right text-gray-700 dark:text-gray-300">€${item.unit_price.toFixed(4)}</td>
            <td class="px-4 py-3 text-sm text-right font-semibold text-gray-900 dark:text-gray-100">€${item.total_price.toFixed(2)}</td>
        </tr>
    `;
    }).join('');
    
    // Display unmatched components
    if (data.unmatched.length > 0) {
        document.getElementById('unmatched-section').classList.remove('hidden');
        document.getElementById('unmatched-count').textContent = data.unmatched.length;
        const unmatchedBody = document.getElementById('unmatched-components-body');
        unmatchedBody.innerHTML = data.unmatched.map((item, index) => `
            <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
                <td class="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">${item.seller_code || '-'}</td>
                <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">${item.manufacturer || '-'}</td>
                <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">${item.manufacturer_code || '-'}</td>
                <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">${item.package || '-'}</td>
                <td class="px-4 py-3 text-sm text-right text-gray-900 dark:text-gray-100">${item.quantity}</td>
                <td class="px-4 py-3 text-sm text-right text-gray-700 dark:text-gray-300">€${item.unit_price.toFixed(4)}</td>
                <td class="px-4 py-3 text-sm text-center">
                    <button onclick="openQuickAddModal(${index})" 
                            class="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-medium transition">
                        <i class="fas fa-plus mr-1"></i>Add
                    </button>
                </td>
            </tr>
        `).join('');
    } else {
        document.getElementById('unmatched-section').classList.add('hidden');
    }
}

function openQuickAddModal(unmatchedIndex) {
    const item = currentOrderData.unmatched[unmatchedIndex];
    
    document.getElementById('quick-add-order-item-index').value = unmatchedIndex;
    document.getElementById('quick-add-supplier-code').value = item.seller_code || '';
    document.getElementById('quick-add-supplier').value = currentOrderData.supplier;
    document.getElementById('quick-add-manufacturer').value = item.manufacturer || '';
    document.getElementById('quick-add-manufacturer-code').value = item.manufacturer_code || '';
    document.getElementById('quick-add-package').value = item.package || '';
    document.getElementById('quick-add-price').value = item.unit_price || 0;
    document.getElementById('quick-add-quantity').value = item.quantity || 0;
    document.getElementById('quick-add-description').value = item.description || '';
    
    // Clear optional fields
    document.getElementById('quick-add-type').value = '';
    document.getElementById('quick-add-value').value = '';
    
    document.getElementById('quick-add-component-modal').classList.remove('hidden');
}

function closeQuickAddModal() {
    document.getElementById('quick-add-component-modal').classList.add('hidden');
}

async function saveQuickAddComponent() {
    const unmatchedIndex = parseInt(document.getElementById('quick-add-order-item-index').value);
    const orderItem = currentOrderData.unmatched[unmatchedIndex];
    
    // Get and truncate package field to max 50 chars
    const packageValue = document.getElementById('quick-add-package').value;
    const truncatedPackage = packageValue.length > 50 ? packageValue.substring(0, 50) : packageValue;
    
    const supplierValue = document.getElementById('quick-add-supplier').value;
    const supplierCodeValue = document.getElementById('quick-add-supplier-code').value;
    const manufacturerCode = document.getElementById('quick-add-manufacturer-code').value;
    const typeValue = document.getElementById('quick-add-type').value;
    
    // Match exact API schema
    const componentData = {
        seller: supplierValue,
        seller_code: supplierCodeValue,
        manufacturer: document.getElementById('quick-add-manufacturer').value,
        manufacturer_code: manufacturerCode,
        smd_footprint: "",  // Optional field - can be filled later
        package: truncatedPackage,
        product_type: typeValue,
        value: document.getElementById('quick-add-value').value || manufacturerCode,
        price: parseFloat(document.getElementById('quick-add-price').value) || 0,
        qty_left: parseInt(document.getElementById('quick-add-quantity').value) || 0
    };
    
    console.log('[Quick Add] Sending component data:', componentData);
    
    // Validate required fields
    if (!componentData.product_type || !componentData.package || !componentData.manufacturer_code) {
        showToast('Please fill in Type, Package, and Manufacturer Code', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${ELECTRONICS_API_BASE}/components`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(componentData)
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const errorMsg = errorData.detail || `HTTP ${response.status}`;
            throw new Error(errorMsg);
        }
        
        const newComponent = await response.json();
        
        // Move from unmatched to matched
        orderItem.component_id = newComponent.id;
        currentOrderData.matched.push(orderItem);
        currentOrderData.unmatched.splice(unmatchedIndex, 1);
        
        // Refresh display
        displayOrderResults(currentOrderData);
        
        closeQuickAddModal();
        showToast('Component added successfully', 'success');
        
    } catch (error) {
        console.error('[Quick Add] Error:', error);
        showToast('Failed to add component: ' + error.message, 'error');
    }
}

async function confirmImportOrder() {
    if (!currentOrderData || currentOrderData.matched.length === 0) {
        showToast('No matched components to import', 'error');
        return;
    }
    
    if (currentOrderData.unmatched.length > 0) {
        if (!confirm(`There are ${currentOrderData.unmatched.length} unmatched components. Import anyway?`)) {
            return;
        }
    }
    
    try {
        const response = await fetch(`${ELECTRONICS_API_BASE}/orders/import`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(currentOrderData)
        });
        
        if (!response.ok) {
            throw new Error('Failed to import order');
        }
        
        showToast('Order imported successfully!', 'success');
        cancelOrderImport();
        
        // Refresh components and stock
        if (currentTab === 'components') {
            loadComponents();
        } else if (currentTab === 'stock') {
            loadStockOverview();
        }
        
    } catch (error) {
        console.error('[Order Import] Error:', error);
        showToast('Failed to import order: ' + error.message, 'error');
    }
}

function cancelOrderImport() {
    document.getElementById('order-file-input').value = '';
    document.getElementById('order-supplier-select').value = '';
    document.getElementById('order-date-input').value = '';
    document.getElementById('order-results').classList.add('hidden');
    document.getElementById('order-processing-status').classList.add('hidden');
    currentOrderData = null;
}

// ===== PNP TAB =====

let allPnPFiles = [];
let currentPnPId = null;
let currentPnPData = null;

async function loadPnPFiles() {
    try {
        const boardFilter = document.getElementById('pnp-board-filter')?.value || '';
        
        let url = `${ELECTRONICS_API_BASE}/pnp`;
        if (boardFilter) url += `?board_id=${boardFilter}`;
        
        const response = await fetch(url);
        
        if (response.status === 404 || response.status === 500) {
            console.warn('[PnP] PnP endpoint not available or not implemented');
            const grid = document.getElementById('pnp-files-grid');
            if (grid) {
                grid.innerHTML = `
                    <div class="col-span-full text-center py-8">
                        <i class="fas fa-info-circle text-4xl text-blue-500 dark:text-blue-400 mb-3"></i>
                        <p class="text-gray-600 dark:text-gray-400 mb-2">PnP file management not yet available</p>
                        <p class="text-sm text-gray-500 dark:text-gray-500">The PnP API endpoint needs to be implemented</p>
                    </div>
                `;
            }
            allPnPFiles = [];
            return;
        }
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log('[PnP] Loaded files:', data.length);
        allPnPFiles = Array.isArray(data) ? data : [];
        renderPnPFilesGrid(allPnPFiles);
        
        // Populate board filter dropdown
        const boardSelect = document.getElementById('pnp-board-filter');
        const uploadBoardSelect = document.getElementById('upload-pnp-board-id');
        if (boardSelect && allBoards.length > 0) {
            const currentValue = boardSelect.value;
            boardSelect.innerHTML = '<option value="">All Boards</option>' +
                allBoards.map(board => `<option value="${board.id}">${board.name || board.board_name} - ${board.version}</option>`).join('');
            boardSelect.value = currentValue;
        }
        if (uploadBoardSelect && allBoards.length > 0) {
            uploadBoardSelect.innerHTML = '<option value="">Select board...</option>' +
                allBoards.map(board => `<option value="${board.id}">${board.name || board.board_name} - ${board.version}</option>`).join('');
        }
        
    } catch (error) {
        console.error('[PnP] Error loading:', error);
        const grid = document.getElementById('pnp-files-grid');
        if (grid) {
            grid.innerHTML = `
                <div class="col-span-full text-center py-8">
                    <i class="fas fa-exclamation-triangle text-4xl text-red-500 mb-3"></i>
                    <p class="text-gray-600 dark:text-gray-400">Failed to load PnP files</p>
                    <p class="text-sm text-gray-500 dark:text-gray-500">${error.message}</p>
                </div>
            `;
        }
    }
}

function renderPnPFilesGrid(files) {
    const grid = document.getElementById('pnp-files-grid');
    
    if (!grid) return;
    
    if (files.length === 0) {
        grid.innerHTML = `
            <div class="col-span-full text-center py-8">
                <i class="fas fa-robot text-4xl text-gray-400 mb-3"></i>
                <p class="text-gray-500 dark:text-gray-400">No PnP files found</p>
                <p class="text-sm text-gray-500 dark:text-gray-500 mt-2">Upload a pick and place CSV file to get started</p>
            </div>
        `;
        return;
    }
    
    grid.innerHTML = files.map(file => {
        const board = allBoards.find(b => b.id === file.board_id);
        const boardName = board ? (board.name || board.board_name) : `Board #${file.board_id}`;
        const componentCount = file.component_count || 0;
        const createdAt = file.created_at ? new Date(file.created_at).toLocaleDateString() : '';
        
        return `
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4 hover:shadow-lg transition cursor-pointer"
             onclick="viewPnPDetails(${file.id})">
            <div class="flex items-start justify-between mb-3">
                <div class="flex-1">
                    <h4 class="text-lg font-semibold text-gray-900 dark:text-white truncate">${file.filename || 'Unnamed PnP'}</h4>
                    <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">${boardName}</p>
                </div>
                <i class="fas fa-robot text-green-500 text-2xl"></i>
            </div>
            <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                <span><i class="fas fa-microchip mr-1"></i>${componentCount} components</span>
                ${createdAt ? `<span><i class="fas fa-calendar mr-1"></i>${createdAt}</span>` : ''}
            </div>
        </div>
        `;
    }).join('');
}

function showUploadPnPModal() {
    document.getElementById('upload-pnp-modal').classList.remove('hidden');
    document.getElementById('upload-pnp-modal').classList.add('flex');
    
    // Populate board dropdown
    const boardSelect = document.getElementById('upload-pnp-board-id');
    if (boardSelect && allBoards.length > 0) {
        boardSelect.innerHTML = '<option value="">Select board...</option>' +
            allBoards.map(board => `<option value="${board.id}">${board.name || board.board_name} - ${board.version}</option>`).join('');
    }
}

function closeUploadPnPModal() {
    document.getElementById('upload-pnp-modal').classList.add('hidden');
    document.getElementById('upload-pnp-modal').classList.remove('flex');
    document.getElementById('upload-pnp-form').reset();
}

function togglePnPUploadMethod() {
    const method = document.querySelector('input[name="pnp-upload-method"]:checked')?.value;
    const fileContainer = document.getElementById('pnp-file-upload-container');
    const pasteContainer = document.getElementById('pnp-paste-container');
    const fileInput = document.getElementById('pnp-csv-file');
    const textArea = document.getElementById('pnp-csv-data');
    
    if (method === 'file') {
        fileContainer.classList.remove('hidden');
        pasteContainer.classList.add('hidden');
        fileInput.required = true;
        textArea.required = false;
    } else {
        fileContainer.classList.add('hidden');
        pasteContainer.classList.remove('hidden');
        fileInput.required = false;
        textArea.required = true;
    }
}

document.getElementById('upload-pnp-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const boardId = document.getElementById('upload-pnp-board-id').value;
    let filename = document.getElementById('pnp-filename').value;
    const method = document.querySelector('input[name="pnp-upload-method"]:checked')?.value;
    
    if (!boardId) {
        showToast('Please select a board', 'error');
        return;
    }
    
    let csvData;
    
    try {
        if (method === 'file') {
            const fileInput = document.getElementById('pnp-csv-file');
            if (!fileInput.files || fileInput.files.length === 0) {
                showToast('Please select a CSV file', 'error');
                return;
            }
            csvData = await fileInput.files[0].text();
            
            // Auto-generate filename from uploaded file if not provided
            if (!filename) {
                filename = fileInput.files[0].name.replace(/\.[^/.]+$/, '');
            }
        } else {
            csvData = document.getElementById('pnp-csv-data').value;
            if (!csvData) {
                showToast('Please paste CSV data', 'error');
                return;
            }
            
            // If no filename provided in paste mode, use a default
            if (!filename) {
                filename = `PnP_Board${boardId}_${Date.now()}`;
            }
        }
        
        console.log('[PnP Upload] Uploading to board', boardId, 'with filename:', filename);
        
        // Parse and validate/map CSV columns
        const { headers, rows } = parseCSV(csvData);
        console.log('[PnP Upload] Parsed CSV with headers:', headers);
        
        // Map common column name variations to API-expected names
        const columnMapping = {
            'Designator': ['Designator', 'Ref', 'Reference', 'RefDes', 'Component'],
            'Mid X': ['Mid X', 'Center X', 'X', 'PosX', 'LocationX', 'Mid-X'],
            'Mid Y': ['Mid Y', 'Center Y', 'Y', 'PosY', 'LocationY', 'Mid-Y'],
            'Layer': ['Layer', 'Side', 'TB'],
            'Rotation': ['Rotation', 'Rot', 'Angle'],
            'Comment': ['Comment', 'Value', 'Description', 'Part'],
        };
        
        // Build header mapping
        const headerMap = {};
        for (const [apiName, variations] of Object.entries(columnMapping)) {
            const found = variations.find(v => headers.includes(v));
            if (found) {
                headerMap[found] = apiName;
            }
        }
        
        // Check for required columns
        const requiredColumns = ['Designator', 'Mid X', 'Mid Y', 'Layer'];
        const missingColumns = requiredColumns.filter(col => 
            !Object.values(headerMap).includes(col)
        );
        
        if (missingColumns.length > 0) {
            console.error('[PnP Upload] Missing required columns:', missingColumns);
            console.log('[PnP Upload] Available headers:', headers);
            console.log('[PnP Upload] Header mapping:', headerMap);
            throw new Error(`Missing required columns: ${missingColumns.join(', ')}. Available: ${headers.join(', ')}`);
        }
        
        // Rebuild CSV with mapped headers
        const mappedHeaders = headers.map(h => headerMap[h] || h);
        const mappedCsvLines = [mappedHeaders.join(',')];
        
        rows.forEach(row => {
            const mappedRow = headers.map(h => {
                let value = row[h] || '';
                // Quote if contains comma or quote
                if (value.includes(',') || value.includes('"')) {
                    value = `"${value.replace(/"/g, '""')}"`;
                }
                return value;
            });
            mappedCsvLines.push(mappedRow.join(','));
        });
        
        const mappedCsvData = mappedCsvLines.join('\n');
        console.log('[PnP Upload] Mapped', rows.length, 'rows with headers:', mappedHeaders);
        
        const response = await fetch(`${ELECTRONICS_API_BASE}/pnp`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                board_id: parseInt(boardId),
                filename: filename,
                csv_data: mappedCsvData
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log('[PnP Upload] Success:', result);
            showToast('PnP file uploaded successfully', 'success');
            closeUploadPnPModal();
            loadPnPFiles();
        } else {
            const error = await response.json().catch(() => ({}));
            console.error('[PnP Upload] Failed with status', response.status, ':', error);
            throw new Error(error.error || error.detail || 'Failed to upload PnP file');
        }
    } catch (error) {
        console.error('[PnP Upload] Error:', error);
        showToast('Failed to upload: ' + error.message, 'error');
    }
});

async function viewPnPDetails(pnpId) {
    currentPnPId = pnpId;
    
    try {
        const response = await fetch(`${ELECTRONICS_API_BASE}/pnp/${pnpId}`);
        
        if (!response.ok) {
            throw new Error('Failed to fetch PnP details');
        }
        
        const pnp = await response.json();
        currentPnPData = pnp;
        
        const board = allBoards.find(b => b.id === pnp.board_id);
        const boardName = board ? `${board.name || board.board_name} - ${board.version}` : `Board #${pnp.board_id}`;
        
        document.getElementById('pnp-detail-name').textContent = pnp.filename || 'PnP File';
        document.getElementById('pnp-detail-board').textContent = boardName;
        document.getElementById('current-pnp-id').value = pnpId;
        
        // Parse and display data
        const items = pnp.pnp_data || [];
        
        // Calculate statistics
        const total = items.length;
        const topLayer = items.filter(item => item.layer === 'T' || item.layer === 'Top').length;
        const bottomLayer = items.filter(item => item.layer === 'B' || item.layer === 'Bottom').length;
        const uniqueParts = new Set(items.map(item => item.device || item.comment)).size;
        
        document.getElementById('pnp-total-count').textContent = total;
        document.getElementById('pnp-top-count').textContent = topLayer;
        document.getElementById('pnp-bottom-count').textContent = bottomLayer;
        document.getElementById('pnp-unique-count').textContent = uniqueParts;
        
        // Render table
        const tbody = document.getElementById('pnp-data-table');
        tbody.innerHTML = items.map(item => `
            <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
                <td class="px-4 py-2 text-sm font-medium text-gray-900 dark:text-gray-100">${item.designator || '-'}</td>
                <td class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300">${item.mid_x || item.x || '-'}</td>
                <td class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300">${item.mid_y || item.y || '-'}</td>
                <td class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300">
                    <span class="px-2 py-1 rounded text-xs font-semibold ${item.layer === 'T' || item.layer === 'Top' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'}">
                        ${item.layer || '-'}
                    </span>
                </td>
                <td class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300">${item.rotation || '0'}°</td>
                <td class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300">${item.comment || '-'}</td>
                <td class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300">${item.device || '-'}</td>
            </tr>
        `).join('');
        
        document.getElementById('pnp-details-modal').classList.remove('hidden');
        document.getElementById('pnp-details-modal').classList.add('flex');
        
    } catch (error) {
        console.error('[PnP Details] Error:', error);
        showToast('Failed to load PnP details', 'error');
    }
}

function closePnPDetailsModal() {
    document.getElementById('pnp-details-modal').classList.add('hidden');
    document.getElementById('pnp-details-modal').classList.remove('flex');
    currentPnPId = null;
    currentPnPData = null;
}

async function exportPnPFile() {
    if (!currentPnPId || !currentPnPData) return;
    
    try {
        // Convert to CSV
        const items = currentPnPData.pnp_data || [];
        const headers = ['Designator', 'Mid X', 'Mid Y', 'Ref X', 'Ref Y', 'Pad X', 'Pad Y', 'Layer', 'Rotation', 'Comment', 'Device'];
        
        let csv = headers.join(',') + '\n';
        csv += items.map(item => [
            `"${item.designator || ''}"`,
            `"${item.mid_x || item.x || ''}"`,
            `"${item.mid_y || item.y || ''}"`,
            `"${item.ref_x || ''}"`,
            `"${item.ref_y || ''}"`,
            `"${item.pad_x || ''}"`,
            `"${item.pad_y || ''}"`,
            `"${item.layer || ''}"`,
            `"${item.rotation || '0'}"`,
            `"${item.comment || ''}"`,
            `"${item.device || ''}"`
        ].join(',')).join('\n');
        
        // Download
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${currentPnPData.filename || 'pnp'}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showToast('PnP file exported', 'success');
    } catch (error) {
        console.error('[PnP Export] Error:', error);
        showToast('Failed to export PnP file', 'error');
    }
}

async function deletePnPFile() {
    if (!currentPnPId) return;
    
    if (!confirm('Are you sure you want to delete this PnP file?')) return;
    
    try {
        const response = await fetch(`${ELECTRONICS_API_BASE}/pnp/${currentPnPId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('PnP file deleted', 'success');
            closePnPDetailsModal();
            loadPnPFiles();
        } else {
            throw new Error('Failed to delete PnP file');
        }
    } catch (error) {
        console.error('[PnP Delete] Error:', error);
        showToast('Failed to delete PnP file', 'error');
    }
}

// ===== OPENPNP EXPORT =====

let openPnPMappingData = [];

async function showOpenPnPExportModal() {
    if (!currentPnPId || !currentPnPData) {
        showToast('No PnP file selected', 'error');
        return;
    }
    
    const boardId = currentPnPData.board_id;
    
    try {
        // Fetch BOM for this board
        const bomResponse = await fetch(`${ELECTRONICS_API_BASE}/boards/${boardId}/bom`);
        if (!bomResponse.ok) throw new Error('Failed to fetch BOM');
        const bomData = await bomResponse.json();
        
        console.log('[OpenPnP] Loaded BOM with', bomData.length, 'entries');
        
        // Build designator -> component map from BOM
        const designatorMap = {};
        bomData.forEach(item => {
            if (item.designators) {
                // Split designators (could be comma-separated like "R1,R2,R3" or "R1, R2, R3")
                const designators = item.designators.split(',').map(d => d.trim()).filter(d => d.length > 0);
                designators.forEach(des => {
                    designatorMap[des] = {
                        component_id: item.component_id,
                        footprint: item.smd_footprint || '',
                        manufacturer_code: item.manufacturer_code || '',
                        value: item.value || ''
                    };
                });
            }
        });
        
        console.log('[OpenPnP] Built designator map with', Object.keys(designatorMap).length, 'entries');
        
        // Map PnP data with BOM
        const pnpItems = currentPnPData.pnp_data || [];
        openPnPMappingData = pnpItems.map(item => {
            const designator = item.designator || '';
            const bomMatch = designatorMap[designator];
            
            return {
                designator: designator,
                x: item.mid_x || item.x || '',
                y: item.mid_y || item.y || '',
                layer: item.layer || '',
                rotation: item.rotation || '0',
                component_id: bomMatch ? bomMatch.component_id : null,
                footprint: bomMatch ? bomMatch.footprint : '',
                manufacturer_code: bomMatch ? bomMatch.manufacturer_code : '',
                value: bomMatch ? bomMatch.value : '',
                status: bomMatch ? 'mapped' : 'unmapped',
                selected: bomMatch ? true : false, // Auto-select mapped, deselect unmapped
                _pnpData: item // Store original PnP data
            };
        });
        
        // Update statistics
        const mapped = openPnPMappingData.filter(i => i.status === 'mapped').length;
        const unmapped = openPnPMappingData.filter(i => i.status === 'unmapped').length;
        const selected = openPnPMappingData.filter(i => i.selected).length;
        
        document.getElementById('openpnp-mapped-count').textContent = mapped;
        document.getElementById('openpnp-unmapped-count').textContent = unmapped;
        document.getElementById('openpnp-selected-count').textContent = selected;
        document.getElementById('openpnp-download-count').textContent = selected;
        document.getElementById('openpnp-total-count').textContent = openPnPMappingData.length;
        
        // Show warning for unmapped designators
        if (unmapped > 0) {
            const unmappedDesignators = openPnPMappingData
                .filter(i => i.status === 'unmapped')
                .map(i => i.designator)
                .join(', ');
            document.getElementById('openpnp-unmapped-list').textContent = unmappedDesignators;
            document.getElementById('openpnp-unmapped-warning').classList.remove('hidden');
        } else {
            document.getElementById('openpnp-unmapped-warning').classList.add('hidden');
        }
        
        // Render mapping table
        renderOpenPnPMappingTable();
        
        // Show modal
        document.getElementById('openpnp-export-modal').classList.remove('hidden');
        document.getElementById('openpnp-export-modal').classList.add('flex');
        
    } catch (error) {
        console.error('[OpenPnP] Error:', error);
        showToast('Failed to prepare OpenPnP export: ' + error.message, 'error');
    }
}

function renderOpenPnPMappingTable() {
    const tbody = document.getElementById('openpnp-mapping-table');
    
    tbody.innerHTML = openPnPMappingData.map((item, idx) => {
        const statusBadge = item.status === 'mapped' 
            ? '<span class="px-2 py-1 text-xs bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 rounded">Mapped</span>'
            : '<span class="px-2 py-1 text-xs bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-300 rounded">Unmapped</span>';
        
        return `
            <tr class="text-sm ${item.status === 'unmapped' ? 'bg-orange-50 dark:bg-orange-900/10' : ''}">
                <td class="px-3 py-2 text-center">
                    <input type="checkbox" 
                           ${item.selected ? 'checked' : ''}
                           onchange="toggleOpenPnPComponent(${idx}, this.checked)"
                           class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500">
                </td>
                <td class="px-3 py-2 font-mono text-gray-900 dark:text-gray-100">${item.designator}</td>
                <td class="px-3 py-2 text-gray-600 dark:text-gray-400">${item.x}</td>
                <td class="px-3 py-2 text-gray-600 dark:text-gray-400">${item.y}</td>
                <td class="px-3 py-2 text-gray-600 dark:text-gray-400">${item.layer}</td>
                <td class="px-3 py-2 text-gray-600 dark:text-gray-400">${item.rotation}</td>
                <td class="px-3 py-2">
                    <input type="number" 
                           value="${item.component_id || ''}" 
                           onchange="updateOpenPnPMapping(${idx}, 'component_id', this.value)"
                           placeholder="Component ID"
                           class="w-24 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100">
                </td>
                <td class="px-3 py-2">
                    <input type="text" 
                           value="${item.footprint || ''}" 
                           onchange="updateOpenPnPMapping(${idx}, 'footprint', this.value)"
                           placeholder="Footprint"
                           class="w-32 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100">
                </td>
                <td class="px-3 py-2">${statusBadge}</td>
            </tr>
        `;
    }).join('');
}

function updateOpenPnPMapping(idx, field, value) {
    if (openPnPMappingData[idx]) {
        openPnPMappingData[idx][field] = value;
        
        // Update status based on component_id
        if (field === 'component_id') {
            openPnPMappingData[idx].status = value ? 'mapped' : 'unmapped';
            
            // Re-render to update status badge
            renderOpenPnPMappingTable();
            
            // Update statistics
            const mapped = openPnPMappingData.filter(i => i.status === 'mapped').length;
            const unmapped = openPnPMappingData.filter(i => i.status === 'unmapped').length;
            const selected = openPnPMappingData.filter(i => i.selected).length;
            document.getElementById('openpnp-mapped-count').textContent = mapped;
            document.getElementById('openpnp-unmapped-count').textContent = unmapped;
            document.getElementById('openpnp-selected-count').textContent = selected;
            document.getElementById('openpnp-download-count').textContent = selected;
        }
    }
}

function toggleOpenPnPComponent(idx, checked) {
    if (openPnPMappingData[idx]) {
        openPnPMappingData[idx].selected = checked;
        const selected = openPnPMappingData.filter(i => i.selected).length;
        document.getElementById('openpnp-selected-count').textContent = selected;
        document.getElementById('openpnp-download-count').textContent = selected;
    }
}

function toggleAllOpenPnPComponents(checked) {
    openPnPMappingData.forEach(item => item.selected = checked);
    renderOpenPnPMappingTable();
    const selected = openPnPMappingData.filter(i => i.selected).length;
    document.getElementById('openpnp-selected-count').textContent = selected;
    document.getElementById('openpnp-download-count').textContent = selected;
}

function selectAllOpenPnPComponents() {
    toggleAllOpenPnPComponents(true);
}

function deselectAllOpenPnPComponents() {
    toggleAllOpenPnPComponents(false);
}

function selectOnlyMappedOpenPnPComponents() {
    openPnPMappingData.forEach(item => {
        item.selected = item.status === 'mapped';
    });
    renderOpenPnPMappingTable();
    const selected = openPnPMappingData.filter(i => i.selected).length;
    document.getElementById('openpnp-selected-count').textContent = selected;
    document.getElementById('openpnp-download-count').textContent = selected;
}

function closeOpenPnPExportModal() {
    document.getElementById('openpnp-export-modal').classList.add('hidden');
    document.getElementById('openpnp-export-modal').classList.remove('flex');
    openPnPMappingData = [];
}

function downloadOpenPnPCSV() {
    try {
        // Filter only selected components
        const selectedComponents = openPnPMappingData.filter(item => item.selected);
        
        if (selectedComponents.length === 0) {
            showToast('No components selected for export', 'warning');
            return;
        }
        
        // OpenPnP CSV format according to https://github.com/openpnp/openpnp/wiki/Importing-Centroid-Data
        // Required columns: Designator, X, Y, Rotation, Side (or Layer)
        // Optional: Value (we use for component ID), Footprint, Comment
        
        const headers = ['Designator', 'X', 'Y', 'Rotation', 'Side', 'Value', 'Footprint', 'Comment'];
        
        const rows = selectedComponents.map(item => {
            // Clean coordinates - remove units if present
            const x = (item.x || '').replace(/[^0-9.-]/g, '');
            const y = (item.y || '').replace(/[^0-9.-]/g, '');
            
            // Normalize layer to Top/Bottom
            let side = item.layer || '';
            if (side.toUpperCase() === 'T') side = 'Top';
            else if (side.toUpperCase() === 'B') side = 'Bottom';
            else if (!side.match(/top|bottom/i)) side = 'Top'; // Default to Top
            
            return [
                item.designator || '',
                x,
                y,
                item.rotation || '0',
                side,
                item.component_id || '', // Component ID goes in Value field
                item.footprint || '',
                item.manufacturer_code || item.value || '' // Additional info in Comment
            ];
        });
        
        // Build CSV
        let csv = headers.join(',') + '\n';
        csv += rows.map(row => row.map(cell => {
            // Quote if contains comma or quote
            const str = String(cell);
            if (str.includes(',') || str.includes('"') || str.includes('\n')) {
                return `"${str.replace(/"/g, '""')}"`;
            }
            return str;
        }).join(',')).join('\n');
        
        // Download
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${currentPnPData.filename || 'pnp'}_OpenPnP.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        console.log('[OpenPnP] Exported', rows.length, 'selected components');
        showToast(`OpenPnP CSV exported: ${rows.length} selected components`, 'success');
        closeOpenPnPExportModal();
        
    } catch (error) {
        console.error('[OpenPnP Export] Error:', error);
        showToast('Failed to export OpenPnP CSV: ' + error.message, 'error');
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

