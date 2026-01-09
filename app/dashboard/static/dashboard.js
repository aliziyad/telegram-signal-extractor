// API Helper
const api = {
    async get(endpoint) {
        const response = await fetch(endpoint);
        if (!response.ok) throw new Error(`API error: ${response.statusText}`);
        return response.json();
    },
    async post(endpoint, data) {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error(`API error: ${response.statusText}`);
        return response.json();
    },
    async put(endpoint, data) {
        const response = await fetch(endpoint, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error(`API error: ${response.statusText}`);
        return response.json();
    },
    async delete(endpoint) {
        const response = await fetch(endpoint, { method: 'DELETE' });
        if (!response.ok) throw new Error(`API error: ${response.statusText}`);
        return response.json();
    }
};

// Navigation
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        const section = e.currentTarget.dataset.section;
        showSection(section);
    });
});

function showSection(sectionId) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
    
    // Show selected section
    document.getElementById(sectionId).classList.add('active');
    document.querySelector(`[data-section="${sectionId}"]`).classList.add('active');
    
    // Update title
    const titles = {
        'dashboard': 'Dashboard',
        'channels': 'Channel Management',
        'signals': 'Extracted Signals',
        'logs': 'System Logs',
        'errors': 'Parsing Errors'
    };
    document.getElementById('page-title').textContent = titles[sectionId];
    
    // Load section data
    if (sectionId === 'dashboard') loadDashboard();
    else if (sectionId === 'channels') loadChannels();
    else if (sectionId === 'signals') loadSignals();
    else if (sectionId === 'logs') loadLogs();
    else if (sectionId === 'errors') loadErrors();
}

// Dashboard
async function loadDashboard() {
    try {
        const data = await api.get('/api/stats');
        
        document.getElementById('total-signals').textContent = data.total_signals;
        document.getElementById('sent-signals').textContent = data.sent_signals;
        document.getElementById('pending-signals').textContent = data.pending_signals;
        document.getElementById('failed-signals').textContent = data.failed_signals;
        document.getElementById('active-channels').textContent = data.active_channels;
        document.getElementById('success-rate').textContent = data.success_rate + '%';
        document.getElementById('signals-24h').textContent = data.signals_24h;
        
        // Parsing methods
        const methodsList = data.parsing_methods.map(m => 
            `<div class="method-item"><span>${m.method}</span><span>${m.count}</span></div>`
        ).join('');
        document.getElementById('parsing-methods').innerHTML = methodsList;
        
        updateStatus('online');
    } catch (error) {
        console.error('Failed to load dashboard:', error);
        updateStatus('offline');
    }
}

// Channels
async function loadChannels() {
    try {
        const channels = await api.get('/api/channels');
        const tbody = document.getElementById('channels-tbody');
        
        if (channels.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center">No channels added yet</td></tr>';
            return;
        }
        
        tbody.innerHTML = channels.map(ch => `
            <tr>
                <td><strong>${ch.channel_name}</strong></td>
                <td><code>${ch.channel_id}</code></td>
                <td>${ch.total_signals}</td>
                <td><span class="status-badge sent">${ch.sent_signals}</span></td>
                <td><span class="status-badge pending">${ch.pending_signals}</span></td>
                <td><span class="status-badge failed">${ch.failed_signals}</span></td>
                <td>
                    <span class="status-badge ${ch.is_active ? 'active' : 'inactive'}">
                        ${ch.is_active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td>
                    <button class="btn" onclick="toggleChannel('${ch.channel_id}', ${!ch.is_active})">
                        ${ch.is_active ? '⏸️ Disable' : '▶️ Enable'}
                    </button>
                    <button class="btn btn-danger" onclick="deleteChannel('${ch.channel_id}')">🗑️ Delete</button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to load channels:', error);
    }
}

async function toggleChannel(channelId, activate) {
    try {
        await api.put(`/api/channels/${channelId}`, { is_active: activate });
        loadChannels();
    } catch (error) {
        alert('Failed to update channel: ' + error.message);
    }
}

async function deleteChannel(channelId) {
    if (!confirm('Are you sure you want to delete this channel?')) return;
    try {
        await api.delete(`/api/channels/${channelId}`);
        loadChannels();
    } catch (error) {
        alert('Failed to delete channel: ' + error.message);
    }
}

// Signals
let currentPage = 1;
let totalPages = 1;

async function loadSignals() {
    try {
        const status = document.getElementById('signal-filter').value;
        const params = new URLSearchParams({ page: currentPage, limit: 50 });
        if (status) params.append('status', status);
        
        const data = await api.get(`/api/signals?${params}`);
        const tbody = document.getElementById('signals-tbody');
        
        if (data.signals.length === 0) {
            tbody.innerHTML = '<tr><td colspan="10" class="text-center">No signals found</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.signals.map(signal => {
            const time = new Date(signal.extracted_at).toLocaleString();
            const direction = signal.direction === 'BUY' ? '📈 BUY' : '📉 SELL';
            const statusBadge = `<span class="status-badge ${signal.status}">${signal.status.toUpperCase()}</span>`;
            
            return `
                <tr>
                    <td><strong>${signal.symbol}</strong></td>
                    <td>${direction}</td>
                    <td>${signal.entry_price.toFixed(2)}</td>
                    <td>${signal.stop_loss ? signal.stop_loss.toFixed(2) : '-'}</td>
                    <td>${signal.take_profit_1 ? signal.take_profit_1.toFixed(2) : '-'}</td>
                    <td>${signal.take_profit_2 ? signal.take_profit_2.toFixed(2) : '-'}</td>
                    <td>${signal.take_profit_3 ? signal.take_profit_3.toFixed(2) : '-'}</td>
                    <td><span class="status-badge">${signal.parsing_method}</span></td>
                    <td>${statusBadge}</td>
                    <td><small>${time}</small></td>
                </tr>
            `;
        }).join('');
        
        totalPages = data.pages;
        document.getElementById('page-info').textContent = `Page ${currentPage} of ${totalPages}`;
        document.getElementById('prev-page').disabled = currentPage === 1;
        document.getElementById('next-page').disabled = currentPage === totalPages;
    } catch (error) {
        console.error('Failed to load signals:', error);
    }
}

document.getElementById('prev-page')?.addEventListener('click', () => {
    if (currentPage > 1) {
        currentPage--;
        loadSignals();
    }
});

document.getElementById('next-page')?.addEventListener('click', () => {
    if (currentPage < totalPages) {
        currentPage++;
        loadSignals();
    }
});

document.getElementById('signal-filter')?.addEventListener('change', () => {
    currentPage = 1;
    loadSignals();
});

// Logs
async function loadLogs() {
    try {
        const logs = await api.get('/api/logs?limit=100');
        const logsHtml = logs.map(log => {
            const time = new Date(log.created_at).toLocaleString();
            const icon = log.log_type === 'error' ? '❌' : log.log_type === 'warning' ? '⚠️' : 'ℹ️';
            
            return `
                <div class="log-entry ${log.log_type}">
                    <div><strong>${icon} ${log.message}</strong></div>
                    <div class="log-time">${time} • Channel: ${log.channel_id}</div>
                </div>
            `;
        }).join('');
        
        document.getElementById('logs-list').innerHTML = logsHtml || '<p class="text-center">No logs</p>';
    } catch (error) {
        console.error('Failed to load logs:', error);
    }
}

// Errors
async function loadErrors() {
    try {
        const errors = await api.get('/api/errors');
        const errorsHtml = errors.map(error => {
            const time = new Date(error.created_at).toLocaleString();
            
            return `
                <div class="error-entry">
                    <div><strong>⚠️ ${error.parsing_method}</strong> - ${error.channel_id}</div>
                    <div class="log-time">${time}</div>
                    <div style="margin-top: 8px; padding: 8px; background: #fff; border-radius: 4px;">
                        <strong>Error:</strong> ${error.error_message}
                        <br><br>
                        <strong>Message:</strong> ${error.raw_message}
                    </div>
                </div>
            `;
        }).join('');
        
        document.getElementById('errors-list').innerHTML = errorsHtml || '<p class="text-center">No parsing errors</p>';
    } catch (error) {
        console.error('Failed to load errors:', error);
    }
}

// Add Channel Modal
const modal = document.getElementById('channel-modal');
const addChannelBtn = document.getElementById('add-channel-btn');
const closeBtn = document.querySelector('.close');

addChannelBtn?.addEventListener('click', () => {
    modal.classList.add('show');
});

closeBtn?.addEventListener('click', () => {
    modal.classList.remove('show');
});

window.addEventListener('click', (e) => {
    if (e.target === modal) {
        modal.classList.remove('show');
    }
});

document.getElementById('add-channel-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    try {
        await api.post('/api/channels', {
            channel_id: document.getElementById('channel-id').value,
            channel_name: document.getElementById('channel-name').value,
            channel_username: document.getElementById('channel-username').value
        });
        
        modal.classList.remove('show');
        document.getElementById('add-channel-form').reset();
        loadChannels();
        alert('Channel added successfully!');
    } catch (error) {
        alert('Failed to add channel: ' + error.message);
    }
});

// Status
function updateStatus(status) {
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');
    
    if (status === 'online') {
        statusDot.classList.add('online');
        statusText.textContent = '🟢 Online';
    } else {
        statusDot.classList.remove('online');
        statusText.textContent = '🔴 Offline';
    }
}

// Auto-refresh
setInterval(() => {
    const activeSection = document.querySelector('.section.active').id;
    if (activeSection === 'dashboard') loadDashboard();
}, 5000);

// Initialize
showSection('dashboard');
loadDashboard();
