// SLA Calculator Application

const API_BASE = '';

// Tab Navigation
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        const tabName = item.dataset.tab;

        // Update active nav item
        document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
        item.classList.add('active');

        // Update active content
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        document.getElementById(`tab-${tabName}`).classList.add('active');
    });
});

// ===== Uptime Calculator =====
const uptimeSlider = document.getElementById('uptime-slider');
const uptimeInput = document.getElementById('uptime-input');

function syncUptimeInputs(value) {
    uptimeSlider.value = value;
    uptimeInput.value = value;
    calculateUptime();
}

uptimeSlider.addEventListener('input', (e) => syncUptimeInputs(e.target.value));
uptimeInput.addEventListener('input', (e) => syncUptimeInputs(e.target.value));

// Preset buttons
document.querySelectorAll('.preset-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        syncUptimeInputs(btn.dataset.value);
    });
});

async function calculateUptime() {
    const uptime = parseFloat(uptimeInput.value);

    try {
        const response = await fetch(`${API_BASE}/api/calculate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ uptime })
        });

        const data = await response.json();

        // Update result cards
        Object.keys(data.downtime).forEach(period => {
            const card = document.querySelector(`.result-card[data-period="${period}"]`);
            if (card) {
                card.querySelector('.downtime-value').textContent = data.downtime[period].formatted;
                card.querySelector('.downtime-compact').textContent = data.downtime[period].compact;
            }
        });

        // Update SLA badge
        const badge = document.getElementById('sla-badge');
        badge.querySelector('.badge-value').textContent = data.sla_level.name;
        badge.querySelector('.badge-value').style.background = data.sla_level.color;

    } catch (error) {
        console.error('Calculation error:', error);
    }
}

// Initial calculation
calculateUptime();

// ===== Compare SLA Levels =====
document.getElementById('compare-btn').addEventListener('click', async () => {
    const checkboxes = document.querySelectorAll('.sla-checkbox:checked');
    const levels = Array.from(checkboxes).map(cb => parseFloat(cb.value));

    try {
        const response = await fetch(`${API_BASE}/api/compare`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ levels })
        });

        const data = await response.json();

        const tbody = document.getElementById('compare-tbody');
        tbody.innerHTML = '';

        data.results.forEach(result => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><strong>${result.name}</strong></td>
                <td>${result.downtime.day.compact}</td>
                <td>${result.downtime.month.compact}</td>
                <td>${result.downtime.year.compact}</td>
            `;
            tbody.appendChild(row);
        });

    } catch (error) {
        console.error('Compare error:', error);
    }
});

// ===== Credit Calculator =====
document.getElementById('credit-calculate-btn').addEventListener('click', async () => {
    const slaLevel = parseFloat(document.getElementById('credit-sla').value);
    const actualUptime = parseFloat(document.getElementById('credit-actual').value);
    const monthlyFee = parseFloat(document.getElementById('credit-fee').value);

    try {
        const response = await fetch(`${API_BASE}/api/credit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sla_level: slaLevel,
                actual_uptime: actualUptime,
                monthly_fee: monthlyFee
            })
        });

        const data = await response.json();

        const statusEl = document.getElementById('credit-status');
        statusEl.textContent = data.status === '达标' ? '✓ SLA 达标' : '✗ SLA 未达标';
        statusEl.className = `credit-status ${data.status === '达标' ? 'success' : 'failure'}`;

        document.getElementById('credit-percent').textContent = `${data.credit_percentage}%`;
        document.getElementById('credit-money').textContent = `¥${data.credit_amount.toFixed(2)}`;
        document.getElementById('credit-message').textContent = data.message;

    } catch (error) {
        console.error('Credit calculation error:', error);
    }
});

// ===== Actual Uptime Calculator =====
const periodSelect = document.getElementById('actual-period');
const customMinutesGroup = document.getElementById('custom-minutes-group');

periodSelect.addEventListener('change', () => {
    customMinutesGroup.style.display = periodSelect.value === 'custom' ? 'block' : 'none';
});

document.getElementById('actual-calculate-btn').addEventListener('click', async () => {
    let totalMinutes;

    if (periodSelect.value === 'custom') {
        totalMinutes = parseFloat(document.getElementById('actual-total-minutes').value);
    } else {
        totalMinutes = parseFloat(periodSelect.value);
    }

    const downtimeMinutes = parseFloat(document.getElementById('actual-downtime').value);

    try {
        const response = await fetch(`${API_BASE}/api/actual-uptime`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                total_minutes: totalMinutes,
                downtime_minutes: downtimeMinutes
            })
        });

        const data = await response.json();

        document.getElementById('actual-uptime-pct').textContent = `${data.uptime_percentage.toFixed(4)}%`;
        document.getElementById('actual-downtime-str').textContent = data.downtime_formatted;
        document.getElementById('actual-closest-sla').textContent = data.closest_sla.name;

    } catch (error) {
        console.error('Actual uptime calculation error:', error);
    }
});

// ===== Reverse Calculator =====
document.getElementById('convert-time-btn').addEventListener('click', () => {
    const hours = parseFloat(document.getElementById('reverse-hours').value) || 0;
    const minutes = parseFloat(document.getElementById('reverse-minutes').value) || 0;

    const totalSeconds = (hours * 3600) + (minutes * 60);
    document.getElementById('reverse-seconds').value = totalSeconds;
});

document.getElementById('reverse-calculate-btn').addEventListener('click', async () => {
    const downtimeSeconds = parseFloat(document.getElementById('reverse-seconds').value) || 0;
    const period = document.getElementById('reverse-period').value;

    try {
        const response = await fetch(`${API_BASE}/api/reverse-calculate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                downtime_seconds: downtimeSeconds,
                period: period
            })
        });

        const data = await response.json();

        document.getElementById('reverse-uptime').textContent = `${data.required_uptime.toFixed(6)}%`;
        document.getElementById('reverse-sla').textContent = data.closest_sla.name;

    } catch (error) {
        console.error('Reverse calculation error:', error);
    }
});
