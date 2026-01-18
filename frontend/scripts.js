const API_BASE = "/api";
let currentUser = null;
let marketChart = null;
let globalStocks = [];
let globalHoldings = [];

// Helper for notifications (can be expanded later)
function monitor(msg, color = 'white') {
    console.log(`%c[System] ${msg}`, `color: ${color}`);
}

// --- AUTHENTICATION ---

function toggleAuth(mode) {
    if (mode === 'register') {
        document.getElementById('login-form').classList.add('hidden');
        document.getElementById('register-form').classList.remove('hidden');
    } else {
        document.getElementById('login-form').classList.remove('hidden');
        document.getElementById('register-form').classList.add('hidden');
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-pass').value;

    try {
        const res = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();

        if (data.status === 'success') {
            setUser(data);
        } else {
            alert(data.message);
        }
    } catch (err) {
        console.error(err);
        alert("Login failed");
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const name = document.getElementById('reg-name').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-pass').value;

    // Password Validation
    // Min 8 chars, 1 Uppercase, 1 Lowercase, 1 Number
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d\w\W]{8,}$/;

    if (!passwordRegex.test(password)) {
        alert("Password must be at least 8 characters long and contain:\n- One Uppercase Letter\n- One Lowercase Letter\n- One Number");
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password })
        });
        const data = await res.json();
        if (data.status === 'success') {
            alert("Registration successful! Please sign in.");
            toggleAuth('login');
        } else {
            alert(data.message);
        }
    } catch (err) {
        alert("Registration failed");
    }
}

function updateCashDisplay(amount) {
    if (amount !== undefined && amount !== null) {
        const fmt = `₹${parseFloat(amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}`;

        // Update Dashboard KPI
        const kpiCash = document.getElementById('kpi-cash');
        if (kpiCash) kpiCash.innerText = fmt;

        // Update Portfolio Card
        const portCash = document.getElementById('port-cash');
        if (portCash) portCash.innerText = fmt;
    }
}

async function fetchLatestUserData() {
    if (!currentUser) return;
    try {
        const res = await fetch(`${API_BASE}/user/${currentUser.user_id}`);
        if (res.ok) {
            const data = await res.json();
            currentUser.cash_balance = data.cash_balance;
            currentUser.email = data.email; // Sync email
            currentUser.name = data.name;   // Sync name
            localStorage.setItem('stock_user', JSON.stringify(currentUser));

            // Refresh UI Elements
            updateCashDisplay(data.cash_balance);
            const ddName = document.getElementById('user-name-display');
            if (ddName) ddName.innerText = data.name;
            const ddEmail = document.getElementById('user-email-display');
            if (ddEmail) ddEmail.innerText = data.email;

            // Update Avatar Initial
            const initialEl = document.getElementById('user-initial');
            if (initialEl && data.name) initialEl.innerText = data.name.charAt(0).toUpperCase();

            const initialElDropdown = document.getElementById('user-initial-dropdown');
            if (initialElDropdown && data.name) initialElDropdown.innerText = data.name.charAt(0).toUpperCase();
        }
    } catch (e) { console.error("Sync user data failed", e); }
}

function setUser(userData) {
    currentUser = userData;
    localStorage.setItem('stock_user', JSON.stringify(userData));

    // Update UI
    const authOverlay = document.getElementById('auth-overlay');
    if (authOverlay) authOverlay.style.display = 'none';

    const mainLayout = document.getElementById('main-layout');
    if (mainLayout) mainLayout.style.display = 'flex';

    initializeUI();

    const initialEl = document.getElementById('user-initial');
    if (initialEl) initialEl.innerText = userData.name.charAt(0).toUpperCase();

    // Update Dropdown Info
    const ddName = document.getElementById('user-name-display');
    if (ddName) ddName.innerText = userData.name;

    const ddEmail = document.getElementById('user-email-display');
    if (ddEmail) ddEmail.innerText = userData.email;

    const initialElDropdown = document.getElementById('user-initial-dropdown');
    if (initialElDropdown) initialElDropdown.innerText = userData.name.charAt(0).toUpperCase();

    // Update Cash Balance
    updateCashDisplay(userData.cash_balance);

    // Load Data
    loadPortfolio();
    initChart();

    // Start Auto-Refresh Service (delayed to prioritize initial load)
    setTimeout(refreshMarket, 2000);
    setInterval(refreshMarket, 60000);
}

function initializeUI() {
    // Set dynamic date
    const dateEl = document.getElementById('current-date');
    if (dateEl) {
        const options = { year: 'numeric', month: 'long', day: 'numeric' };
        dateEl.innerText = new Date().toLocaleDateString(undefined, options);
    }
}

function logout() {
    currentUser = null;
    localStorage.removeItem('stock_user');
    window.location.reload();
}

function checkSession() {
    const saved = localStorage.getItem('stock_user');
    if (saved) {
        setUser(JSON.parse(saved));
    }
}

// Redundant loadAIInsightsPage removed.

// --- PORTFOLIO & DATA ---

async function loadPortfolio() {
    if (!currentUser) return;

    try {
        const res = await fetch(`${API_BASE}/portfolio/${currentUser.user_id}`);
        globalHoldings = await res.json();
        const holdings = globalHoldings;

        const tbody = document.getElementById('portfolio-body');
        if (!tbody) return; // Exit if not on dashboard
        tbody.innerHTML = '';
        let totalVal = 0;
        let totalCost = 0;

        holdings.forEach(item => {
            const currentVal = item.total_quantity * item.current_price;
            const costBasis = item.total_quantity * item.avg_buy_price;
            const pl = currentVal - costBasis;
            const plPct = (pl / costBasis) * 100;

            totalVal += currentVal;
            totalCost += costBasis;

            const row = tbody.insertRow();
            row.innerHTML = `
                <td style="font-weight: 600; color: var(--text-primary);">${item.symbol}</td>
                <td>${item.total_quantity}</td>
                <td>₹${item.avg_buy_price.toFixed(2)}</td>
                <td>₹${item.current_price.toFixed(2)}</td>
                <td class="${pl >= 0 ? 'positive' : 'negative'}">
                    ${pl >= 0 ? '+' : ''}${plPct.toFixed(2)}%
                    <span style="font-size:0.8em; color: var(--text-muted);">(₹${pl.toFixed(2)})</span>
                </td>
            `;
        });

        // Update KPIs
        document.getElementById('kpi-value').innerText = `₹${totalVal.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
        const totalPL = totalVal - totalCost;
        const totalPLPct = totalCost > 0 ? (totalPL / totalCost) * 100 : 0;

        const plEl = document.getElementById('kpi-pl');
        plEl.innerText = `${totalPL >= 0 ? '+' : ''}₹${totalPL.toFixed(2)}`;
        plEl.className = `kpi-value ${totalPL >= 0 ? 'positive' : 'negative'}`;

        const plPctEl = document.getElementById('kpi-pl-percent');
        plPctEl.innerText = `${totalPLPct.toFixed(2)}%`;
        plPctEl.className = `kpi-sub ${totalPL >= 0 ? 'positive' : 'negative'}`;

        // Sync User
        fetchLatestUserData();

    } catch (err) {
        console.error("Failed to load portfolio", err);
    }
}

// DROPDOWN LOGIC
function toggleProfileMenu() {
    const menu = document.getElementById('profile-menu');
    options = menu.classList.contains('show');

    // Close others if needed (not implemented here)
    if (options) {
        menu.classList.remove('show');
    } else {
        menu.classList.add('show');
    }
}

// Close dropdown when clicking outside
window.addEventListener('click', (e) => {
    const menu = document.getElementById('profile-menu');
    const profileBtn = document.querySelector('.user-profile');

    if (menu && menu.classList.contains('show')) {
        if (!menu.contains(e.target) && !profileBtn.contains(e.target)) {
            menu.classList.remove('show');
        }
    }
});

function prefillTrade(symbol, id, price) {
    document.getElementById('stock_id').value = id; // Ideally use ID, but user might want symbol lookup later
    document.getElementById('price').value = price;
    // Highlight
    document.getElementById('stock_id').focus();
    calculateTotal(); // Trigger calc
}

// Auto-Calculate Total
function calculateTotal() {
    const qtyInput = document.getElementById('qty');
    const priceInput = document.getElementById('price');
    if (!qtyInput || !priceInput) return;

    const qty = parseFloat(qtyInput.value) || 0;
    const price = parseFloat(priceInput.value) || 0;
    const total = qty * price;
    document.getElementById('est-total').innerText = `₹${total.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
}

// Add listeners
const qtyInput = document.getElementById('qty');
const priceInput = document.getElementById('price');
if (qtyInput) qtyInput.addEventListener('input', calculateTotal);
if (priceInput) priceInput.addEventListener('input', calculateTotal);

async function refreshMarket() {
    monitor("Auto-syncing market data...", "#58a6ff");
    try {
        const res = await fetch(`${API_BASE}/market/refresh`, { method: 'POST' });
        const result = await res.json();
        if (result.status === 'success') {
            console.log(`Market Updated: ${result.updated} tickers synced.`);
            // Determine active page logic
            if (document.getElementById('portfolio-body')) {
                loadPortfolio();
            }
            if (document.getElementById('detailed-holdings-body')) {
                loadPortfolioPage();
            }
            if (document.getElementById('tax-body')) {
                loadTaxReport();
            }
        }
    } catch (err) {
        console.error("Auto-sync failed", err);
    }
}

// --- PORTFOLIO PAGE LOGIC ---

async function loadPortfolioPage() {
    if (!currentUser) return;

    // 1. Load Holdings for Detailed Table & Chart
    try {
        const res = await fetch(`${API_BASE}/portfolio/${currentUser.user_id}`);
        const holdings = await res.json();
        const stockPrices = {}; // Map for easy access

        const tbody = document.getElementById('detailed-holdings-body');
        if (tbody) {
            tbody.innerHTML = '';
            let totalEquity = 0;
            let totalCostBasis = 0;
            const labels = [];
            const dataPoints = [];
            const colors = [];

            holdings.forEach((item, index) => {
                const marketVal = item.total_quantity * item.current_price;
                const costBasis = item.total_quantity * item.avg_buy_price;
                const pl = marketVal - costBasis;

                totalEquity += marketVal;
                totalCostBasis += costBasis;

                // Chart Data
                if (marketVal > 0) {
                    labels.push(item.symbol);
                    dataPoints.push(marketVal);
                    // Generate Color
                    const hue = (index * 137.5) % 360;
                    colors.push(`hsl(${hue}, 70%, 60%)`);
                }

                const row = tbody.insertRow();
                row.innerHTML = `
                    <td style="font-weight: 600;">${item.symbol}</td>
                    <td>${item.total_quantity}</td>
                    <td>₹${item.avg_buy_price.toFixed(2)}</td>
                    <td>₹${item.current_price.toFixed(2)}</td>
                    <td>₹${marketVal.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                    <td class="${pl >= 0 ? 'positive' : 'negative'}">₹${pl.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                `;
            });

            // Update Summary Cards
            const portEquity = document.getElementById('port-equity');
            if (portEquity) portEquity.innerText = `₹${totalEquity.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;

            const portCash = document.getElementById('port-cash');
            if (portCash) portCash.innerText = `₹${parseFloat(currentUser.cash_balance).toLocaleString(undefined, { minimumFractionDigits: 2 })}`;

            const totalPL = totalEquity - totalCostBasis;
            const plElement = document.getElementById('port-pl');
            if (plElement) {
                plElement.innerText = `${totalPL >= 0 ? '+' : ''}₹${totalPL.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
                plElement.className = `kpi-value ${totalPL >= 0 ? 'positive' : 'negative'}`;
            }

            // Render Chart
            renderAllocationChart(labels, dataPoints, colors);
        }

    } catch (err) { console.error(err); }

    // 2. Load Transactions
    loadTransactions();
}

async function loadTransactions() {
    try {
        const res = await fetch(`${API_BASE}/transactions/${currentUser.user_id}`);
        const txns = await res.json();

        const tbody = document.getElementById('txn-history-body');
        if (tbody) {
            tbody.innerHTML = '';
            txns.forEach(t => {
                const row = tbody.insertRow();
                const isBuy = t.txn_type === 'BUY';
                row.innerHTML = `
                    <td style="color:var(--text-muted); font-size:0.85em;">${t.txn_date.split(' ')[0]}</td>
                    <td class="${isBuy ? 'positive' : 'negative'}" style="font-weight:600;">${t.txn_type}</td>
                    <td style="font-weight:600;">${t.symbol}</td>
                    <td>${t.quantity}</td>
                    <td>₹${t.price.toFixed(2)}</td>
                `;
            });
        }
    } catch (err) { console.error(err); }
}

async function loadTaxReport() {
    if (!currentUser) return;
    try {
        const res = await fetch(`${API_BASE}/tax_report/${currentUser.user_id}`);
        const data = await res.json();
        const details = data.details;
        const summary = data.summary;

        // Update Summary Cards
        const liability = summary.tax_liability;
        document.getElementById('tax-stcg').innerText = `₹${summary.short_term_gain.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
        document.getElementById('tax-ltcg').innerText = `₹${summary.long_term_gain.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
        document.getElementById('tax-liability').innerText = `₹${liability.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;

        // Populate Table
        const tbody = document.getElementById('tax-body');
        if (tbody) {
            tbody.innerHTML = '';
            details.forEach(item => {
                const gain = item.total_gain;
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td style="font-weight: 600;">${item.symbol}</td>
                    <td><span class="badge ${item.term === 'LONG' ? 'badge-success' : 'badge-warning'}">${item.term}</span></td>
                    <td>${item.quantity}</td>
                    <td>${item.buy_date}</td>
                    <td>${item.sell_date}</td>
                    <td>₹${item.buy_price.toFixed(2)}</td>
                    <td>₹${item.sell_price.toFixed(2)}</td>
                    <td class="${gain >= 0 ? 'positive' : 'negative'}">₹${gain.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                `;
            });
        }

    } catch (err) { console.error(err); }
}

let allocChartInstance = null;
function renderAllocationChart(labels, data, colors) {
    const ctx = document.getElementById('allocationChart').getContext('2d');

    if (allocChartInstance) {
        allocChartInstance.destroy();
    }

    allocChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { color: '#a0a0a0' }
                }
            }
        }
    });
}

// --- TRADING ---

function setTradeMode(type) {
    const btnBuy = document.getElementById('btn-buy');
    const btnSell = document.getElementById('btn-sell');
    const submitBtn = document.getElementById('txn-submit');
    const typeInput = document.getElementById('txn-type');

    typeInput.value = type;

    if (type === 'BUY') {
        btnBuy.classList.add('active', 'buy');
        btnSell.classList.remove('active', 'sell');
        submitBtn.innerText = "Execute Buy Order";
        submitBtn.style.backgroundColor = "var(--accent-success)";
    } else {
        btnSell.classList.add('active', 'sell');
        btnBuy.classList.remove('active', 'buy');
        submitBtn.innerText = "Execute Sell Order";
        submitBtn.style.backgroundColor = "var(--accent-danger)";
    }

    // Refresh dropdown based on mode
    updateStockDropdownOptions();
}

function updateStockDropdownOptions() {
    const selector = document.getElementById('stock_id');
    const typeInput = document.getElementById('txn-type');
    if (!selector || !typeInput) return;

    const mode = typeInput.value;
    const stocksToDisplay = (mode === 'SELL') ? globalHoldings : globalStocks;

    selector.innerHTML = '<option value="" disabled selected>Choose a stock...</option>';

    if (stocksToDisplay.length === 0 && mode === 'SELL') {
        const opt = document.createElement('option');
        opt.disabled = true;
        opt.innerText = "No holdings available to sell";
        selector.appendChild(opt);
        return;
    }

    stocksToDisplay.forEach(stock => {
        const opt = document.createElement('option');
        opt.value = stock.stock_id;
        opt.dataset.price = stock.current_price;
        opt.innerText = `${stock.symbol} - ₹${stock.current_price.toFixed(2)}`;
        selector.appendChild(opt);
    });
}



const txnForm = document.getElementById('txnForm');
if (txnForm) {
    txnForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!currentUser) return;

        const type = document.getElementById('txn-type').value;
        const endpoint = type === 'BUY' ? '/buy' : '/sell';

        const data = {
            user_id: currentUser.user_id,
            stock_id: parseInt(document.getElementById('stock_id').value),
            quantity: parseInt(document.getElementById('qty').value),
            price: parseFloat(document.getElementById('price').value)
        };

        try {
            const res = await fetch(API_BASE + endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await res.json();

            if (res.ok) {
                alert(`${type} Order Executed Successfully`);
                loadPortfolio();
                // Reset form partly
                document.getElementById('qty').value = '';
                document.getElementById('price').value = '';
            } else {
                alert(`Error: ${result.message}`);
            }
        } catch (err) {
            alert("Transaction Failed: Network Error");
        }
    });
}

// --- CHART (Mock Data) ---
function initChart() {
    const canvas = document.getElementById('mainChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    // Gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(59, 130, 246, 0.5)'); // Blue
    gradient.addColorStop(1, 'rgba(59, 130, 246, 0.0)');

    marketChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['9:30', '10:00', '10:30', '11:00', '11:30', '12:00', '12:30'],
            datasets: [{
                label: 'Portfolio Value',
                data: [10000, 10200, 10150, 10400, 10350, 10800, 10950],
                borderColor: '#3b82f6',
                backgroundColor: gradient,
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#71717a' }
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#71717a' }
                }
            }
        }
    });
}

// --- MARKET EXPLORER PAGE ---


async function loadStockDropdown() {
    const selector = document.getElementById('stock_id');
    if (!selector) return; // Not on dashboard

    try {
        if (globalStocks.length === 0) {
            const res = await fetch(`${API_BASE}/stocks`);
            globalStocks = await res.json(); // Update global cache
        }

        updateStockDropdownOptions();

        // Add Change Listener for Auto-Price (only once)
        if (!selector.dataset.listener) {
            selector.addEventListener('change', (e) => {
                const selectedOpt = selector.options[selector.selectedIndex];
                if (!selectedOpt || selectedOpt.disabled) return;

                const price = parseFloat(selectedOpt.dataset.price);
                const priceInput = document.getElementById('price');
                if (priceInput) {
                    priceInput.value = price;
                    calculateTotal();
                }
            });
            selector.dataset.listener = "true";
        }

        console.log("Stock Dropdown Loaded");
        // Only check trade intent AFTER stocks are loaded
        checkTradeIntent();

    } catch (err) {
        console.error("Failed to load stock dropdown", err);
    }
}

async function loadMarketPage() {
    try {
        const res = await fetch(`${API_BASE}/stocks`);
        globalStocks = await res.json();

        renderStocks(globalStocks);

        // Check for URL Search Params
        const urlParams = new URLSearchParams(window.location.search);
        const queryParam = urlParams.get('q');

        const sectorSelect = document.getElementById('sector-filter');
        const searchInput = document.getElementById('market-search');

        if (queryParam && searchInput) {
            searchInput.value = queryParam;
            filterMarket('All', queryParam);
        }

        // Filters
        if (sectorSelect) {
            sectorSelect.addEventListener('change', (e) => filterMarket(e.target.value, searchInput ? searchInput.value : ''));
        }
        if (searchInput) {
            searchInput.addEventListener('input', (e) => filterMarket(sectorSelect ? sectorSelect.value : 'All', e.target.value));
        }

    } catch (err) {
        console.error("Failed to load market explorer", err);
    }
}

// Redirect to market with search query
function handleGlobalSearch(e) {
    if (e.key === 'Enter') {
        const query = e.target.value.trim();
        if (query) {
            window.location.href = `market.html?q=${encodeURIComponent(query)}`;
        }
    }
}

function filterMarket(sector, searchText) {
    if (!globalStocks || globalStocks.length === 0) return;

    // Fallback if args not provided (from HTML onchange)
    const activeSector = sector || document.getElementById('sector-filter')?.value || 'ALL';
    const activeSearch = searchText !== undefined ? searchText : (document.getElementById('market-search')?.value || '');

    const term = activeSearch.toLowerCase();
    const filtered = globalStocks.filter(stock => {
        const matchesSector = activeSector === 'ALL' || stock.sector === activeSector;
        const matchesSearch = stock.symbol.toLowerCase().includes(term) ||
            (stock.name && stock.name.toLowerCase().includes(term));
        return matchesSector && matchesSearch;
    });
    renderStocks(filtered);
}

function renderStocks(stocks) {
    const grid = document.getElementById('market-grid');
    if (!grid) return;

    if (stocks.length === 0) {
        grid.innerHTML = '<div class="loading-state">No stocks found matching filters.</div>';
        return;
    }

    grid.innerHTML = '';
    stocks.forEach(stock => {
        const card = document.createElement('div');
        card.className = 'stock-card';
        // Assume random change for demo visualization if not present
        const change = (Math.random() * 5 - 2).toFixed(2);
        const isPos = change >= 0;

        card.innerHTML = `
            <div class="stock-header">
                <div>
                    <div class="stock-symbol">${stock.symbol}</div>
                    <div class="stock-name">${stock.name || 'Company Name'}</div>
                </div>
                <div class="stock-sector">${stock.sector || 'N/A'}</div>
            </div>
            
            <div style="margin: 12px 0; color: ${isPos ? 'var(--accent-success)' : 'var(--accent-danger)'}; font-weight: 500;">
                <i class="fas ${isPos ? 'fa-arrow-up' : 'fa-arrow-down'}"></i> ${Math.abs(change)}%
            </div>

            <div class="stock-price">₹${stock.current_price.toFixed(2)}</div>
            
            <div class="trade-overlay">
                <button class="btn-trade buy" onclick="quickBuyRedirect('${stock.symbol}', ${stock.stock_id}, ${stock.current_price})">
                    Buy ${stock.symbol}
                </button>
            </div>
        `;
        grid.appendChild(card);
    });

    // Update count
    const countEl = document.getElementById('stock-count');
    if (countEl) countEl.innerText = stocks.length;
}

function quickBuyRedirect(symbol, id, price) {
    console.log("Setting Trade Intent:", { symbol, id, price });
    // Redirect to index with params to prefill
    localStorage.setItem('trade_intent', JSON.stringify({ symbol, id, price, mode: 'BUY' }));
    window.location.href = 'index.html';
}

// Check for trade intent on index load
function checkTradeIntent() {
    const intent = localStorage.getItem('trade_intent');
    console.log("Checking Trade Intent:", intent);
    const form = document.getElementById('txnForm');

    if (intent && form) {
        try {
            const data = JSON.parse(intent);
            console.log("Processing Intent Data:", data);

            // 1. Set Mode FIRST (crucial because it resets dropdown)
            setTradeMode(data.mode);

            // 2. Set Stock after a micro-delay to let UI update
            setTimeout(() => {
                const stockIdInput = document.getElementById('stock_id');
                if (stockIdInput) {
                    stockIdInput.value = data.id;
                    console.log("Set Stock ID:", data.id);
                    stockIdInput.dispatchEvent(new Event('change'));
                }

                const priceInput = document.getElementById('price');
                if (data.price && priceInput) {
                    priceInput.value = data.price;
                    console.log("Set Price:", data.price);
                }

                if (stockIdInput) stockIdInput.focus();
                calculateTotal(); // Update total calculation
            }, 50);

            // Clear intent
            localStorage.removeItem('trade_intent');
            monitor(`Quick Trade Prefilled: ${data.symbol}`, "#10b981");
        } catch (e) {
            console.error("Error processing trade intent:", e);
        }
    } else {
        console.log("No intent or form not found. Form present:", !!form);
    }
}


// --- NEWS PORTAL ---
async function loadNews() {
    const container = document.getElementById('news-container');
    if (!container) return;

    container.innerHTML = `
        <div class="fx-card" style="grid-column: 1 / -1; text-align: center; color: var(--text-muted); padding: 80px 40px;">
            <i class="fas fa-spinner fa-spin" style="font-size: 2.5rem; margin-bottom: 24px; color: var(--primary-purple);"></i>
            <p style="font-size: 1.1rem;">Fetching latest financial news...</p>
        </div>
    `;

    try {
        const res = await fetch(`${API_BASE}/news`);
        const newsItems = await res.json();

        container.innerHTML = '';
        if (newsItems.length === 0) {
            container.innerHTML = '<p style="text-align: center; grid-column: 1/-1;">No news available at the moment.</p>';
            return;
        }

        newsItems.forEach(item => {
            const card = document.createElement('div');
            card.className = 'news-card';

            let iconClass = 'fa-newspaper';
            const cat = (item.category || '').toLowerCase();
            if (cat.includes('tech')) iconClass = 'fa-microchip';
            else if (cat.includes('eco')) iconClass = 'fa-chart-line';
            else if (cat.includes('crypto')) iconClass = 'fa-bitcoin-sign';
            else if (cat.includes('auto')) iconClass = 'fa-car';

            card.innerHTML = `
                <div class="news-image-placeholder">
                    <i class="fas ${iconClass}"></i>
                </div>
                <div class="news-content">
                    <div class="news-meta">
                        <span class="news-source"><i class="far fa-newspaper"></i> ${item.source}</span>
                        <span class="news-time">${item.time || 'Today'}</span>
                    </div>
                    <h3 class="news-title">${item.title}</h3>
                    <p class="news-summary">${item.summary || 'No summary available.'}</p>
                    <a href="#" class="read-more">Read Full Story <i class="fas fa-arrow-right"></i></a>
                </div>
            `;
            container.appendChild(card);
        });
    } catch (err) {
        console.error("Failed to load news", err);
        container.innerHTML = '<p style="text-align: center; color: var(--accent-danger); grid-column: 1/-1;">Failed to load news. Please try again later.</p>';
    }
}

// --- AI INSIGHTS ---
async function loadRecommendations() {
    const container = document.getElementById('ai-recommendations');
    if (!container || !currentUser) return;

    container.innerHTML = `
        <div class="fx-card" style="text-align: center; color: var(--text-muted); padding: 80px 40px;">
            <i class="fas fa-sparkles fa-spin" style="font-size: 2.5rem; margin-bottom: 24px; color: var(--primary-purple);"></i>
            <p style="font-size: 1.1rem;">Generating smart insights for your portfolio...</p>
        </div>
    `;

    try {
        const res = await fetch(`${API_BASE}/recommendations/${currentUser.user_id}`);
        const data = await res.json();

        // UI Transition
        const loader = document.getElementById('ai-loading');
        const content = document.getElementById('ai-content');
        if (loader) loader.style.display = 'none';
        if (content) content.style.display = 'block';

        container.innerHTML = '';

        // Split data into cards
        const recs = [
            { label: 'Primary Recommendation', value: data.suggested_stock || 'Balanced Growth', rationale: data.reason || 'Your portfolio is currently being optimized for long-term growth.' },
            { label: 'Suggested Sector', value: data.sector || 'Diversified', rationale: 'This sector currently offers the best risk-adjusted momentum for your profile.' },
            { label: 'Investment Action', value: data.action || 'Hold', rationale: `Recommended action based on portfolio concentration and market trends.` }
        ];

        recs.forEach(rec => {
            const card = document.createElement('div');
            card.className = 'recommendation-card';
            card.innerHTML = `
                <div class="rec-label">${rec.label}</div>
                <div class="rec-value">${rec.value}</div>
                <div class="rec-rationale">${rec.rationale}</div>
            `;
            container.appendChild(card);
        });

    } catch (err) {
        console.error("Failed to load recommendations", err);
        const loader = document.getElementById('ai-loading');
        const content = document.getElementById('ai-content');
        if (loader) loader.style.display = 'none';
        if (content) content.style.display = 'block';
        container.innerHTML = `<p style="text-align: center; color: var(--accent-danger); padding: 40px;">Failed to load AI insights: ${err.message}</p>`;
    }
}

// --- DB VISUALIZER ---
async function loadTableList() {
    const container = document.getElementById('table-tabs');
    if (!container) return;

    try {
        const adminToken = localStorage.getItem('finnex_admin_token');
        const res = await fetch(`${API_BASE}/admin/tables`, {
            headers: { 'Authorization': adminToken }
        });
        const tables = await res.json();

        container.innerHTML = '';
        tables.forEach((table, index) => {
            const chip = document.createElement('div');
            chip.className = 'table-chip';
            chip.innerText = table;
            chip.onclick = () => {
                document.querySelectorAll('.table-chip').forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                loadTableData(table);
            };
            container.appendChild(chip);

            // Load first table by default
            if (index === 0) chip.click();
        });
    } catch (err) {
        container.innerHTML = '<div class="table-chip">Error loading tables</div>';
    }
}

async function loadTableData(tableName) {
    const thead = document.getElementById('db-thead');
    const tbody = document.getElementById('db-tbody');
    if (!thead || !tbody) return;

    tbody.innerHTML = '<tr><td colspan="100%" style="text-align: center; padding: 40px;"><i class="fas fa-spinner fa-spin"></i> Fetching records...</td></tr>';

    try {
        const adminToken = localStorage.getItem('finnex_admin_token');
        const res = await fetch(`${API_BASE}/admin/table/${tableName}`, {
            headers: { 'Authorization': adminToken }
        });
        const data = await res.json();

        if (data.length === 0) {
            thead.innerHTML = '';
            tbody.innerHTML = '<tr><td colspan="100%" style="text-align: center; padding: 40px; color: var(--text-muted);">This relation is currently empty.</td></tr>';
            return;
        }

        // Generate Headers
        const cols = Object.keys(data[0]);
        thead.innerHTML = `<tr>${cols.map(col => `<th>${col}</th>`).join('')}</tr>`;

        // Generate Body
        tbody.innerHTML = data.map(row => `
            <tr>
                ${cols.map(col => {
            const val = row[col];
            if (val === null) return '<td style="color: var(--text-muted); opacity: 0.5;">null</td>';
            return `<td>${val}</td>`;
        }).join('')}
            </tr>
        `).join('');

        monitor(`Visualized: ${tableName} (${data.length} rows)`, "#primary-purple");
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="100%" style="text-align: center; color: var(--accent-danger);">Failed to fetch data: ${err.message}</td></tr>`;
    }
}


// --- INITIALIZATION ---
const loginForm = document.getElementById('login-form');
if (loginForm) loginForm.addEventListener('submit', handleLogin);

const registerForm = document.getElementById('register-form');
if (registerForm) registerForm.addEventListener('submit', handleRegister);
window.onload = () => {
    checkSession();

    // Global Search Listener
    const globalSearch = document.querySelector('.search-input');
    if (globalSearch) {
        globalSearch.addEventListener('keypress', handleGlobalSearch);
    }

    // Set Date on all pages
    const dateSpan = document.getElementById('current-date');
    if (dateSpan) {
        const now = new Date();
        const options = { year: 'numeric', month: 'long', day: 'numeric' };
        dateSpan.innerText = now.toLocaleDateString('en-US', options);
    }

    // Page Specific Initializations
    if (document.getElementById('market-grid')) loadMarketPage();
    if (document.getElementById('detailed-holdings-body')) loadPortfolioPage();
    if (document.getElementById('tax-body')) loadTaxReport();
    if (document.getElementById('news-container')) loadNews();
    if (document.getElementById('ai-recommendations')) loadRecommendations();
    if (document.getElementById('table-tabs')) loadTableList();

    loadStockDropdown();

    // 30-min Auto Refresh
    setInterval(async () => {
        try {
            const res = await fetch(`${API_BASE}/market/refresh`, { method: 'POST' });
            if (res.ok) {
                if (document.getElementById('market-grid')) loadMarketPage();
                if (document.getElementById('detailed-holdings-body')) loadPortfolioPage();
                if (document.getElementById('portfolio-body')) loadPortfolio();
            }
        } catch (e) { }
    }, 1800000);
};