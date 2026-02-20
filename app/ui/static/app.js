async function fetchDashboard() {
  const resp = await fetch('/api/dashboard?timeframe=1h');
  return await resp.json();
}

function createMetrics(metrics) {
  return Object.entries(metrics)
    .map(([k, v]) => `<div class="metric"><strong>${k}</strong>: ${Number(v).toFixed(4)}</div>`)
    .join('');
}

function renderLogs(logs) {
  const tbody = document.querySelector('#logs-table tbody');
  tbody.innerHTML = logs.map((l) => `
    <tr>
      <td>${l.created_at}</td>
      <td>${l.asset}</td>
      <td>${l.signal_name}</td>
      <td>${l.direction}</td>
      <td>${Number(l.confidence).toFixed(2)}</td>
      <td class="danger">${Number(l.expected_drawdown).toFixed(2)}</td>
    </tr>
  `).join('');
}

function renderCurves(canvasId, series, color) {
  const ctx = document.getElementById(canvasId);
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: series.map((_, i) => i + 1),
      datasets: [{ data: series, borderColor: color, borderWidth: 1.7, pointRadius: 0 }],
    },
    options: { responsive: true, plugins: { legend: { display: false } }, scales: { x: { display: false } } },
  });
}

function renderAssets(data) {
  const dashboard = document.getElementById('dashboard');
  dashboard.innerHTML = data.assets.map((item, idx) => `
    <article class="card">
      <h2>${item.asset} <small>(${item.timeframe})</small></h2>
      <p>Regime: <strong>${item.regime.regime}</strong> (${item.regime.confidence}%)</p>
      <p>Suggested Direction: <strong>${item.decision.suggested_direction}</strong> | Confidence: ${item.decision.confidence}%</p>
      <p>${item.decision.uncertainty_note}</p>
      <div class="grid">
        <div>
          <h3>Signal Leaderboard</h3>
          <ol>
            ${item.signals.map((s) => `<li>${s.name} v${s.version} [${s.strategy_type}] - ${s.confidence_score}% (${s.direction})</li>`).join('')}
          </ol>
        </div>
        <div>
          <h3>Risk Metrics</h3>
          ${createMetrics(item.metrics)}
        </div>
      </div>
      <div class="grid">
        <div><h3>Equity Curve</h3><canvas id="eq-${idx}"></canvas></div>
        <div><h3>Drawdown Curve</h3><canvas id="dd-${idx}"></canvas></div>
      </div>
    </article>
  `).join('');

  data.assets.forEach((item, idx) => {
    renderCurves(`eq-${idx}`, item.curves.equity, '#4fa3ff');
    renderCurves(`dd-${idx}`, item.curves.drawdown, '#ff6b6b');
  });
  renderLogs(data.logs);
}

async function run() {
  const data = await fetchDashboard();
  renderAssets(data);
}

document.getElementById('refresh-btn').addEventListener('click', run);
document.getElementById('replay-btn').addEventListener('click', async () => {
  const date = document.getElementById('replay-date').value;
  if (!date) return;
  const iso = new Date(date).toISOString();
  const resp = await fetch(`/api/replay?asset=BTCUSDT&timeframe=1h&at=${encodeURIComponent(iso)}`);
  const replay = await resp.json();
  alert(`Replay ${replay.asset} @ ${replay.replay_timestamp}\nTop Signal: ${replay.signals[0].name}\nConfidence: ${replay.signals[0].confidence_score}`);
});

run();
