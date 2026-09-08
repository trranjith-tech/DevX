// DevX Console — vanilla JS client for the DevX backend prototype.
// No build step: open index.html via a static server and it talks
// straight to the FastAPI backend over fetch().

const DEPLOYED_API_BASE = 'https://devx-3rqa.onrender.com';
const savedApiBase = localStorage.getItem('devx_api_base');

const state = {
  apiBase: savedApiBase && !/^https?:\/\/(127\.0\.0\.1|localhost):8000\/?$/i.test(savedApiBase)
    ? savedApiBase.replace(/\/$/, '')
    : DEPLOYED_API_BASE,
  token: localStorage.getItem('devx_token') || null,
  user: null,
  sessions: [],          // [{session_id, app_name, device_model, status, ...}]
  activeSessionId: null,
  activeTab: 'dashboard',
  latestMetrics: {},     // session_id -> last metric row, for the signal strip
};

// ---------- tiny fetch helper ----------

async function api(path, { method = 'GET', body, auth = true } = {}) {
  const headers = {};
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (auth && state.token) headers['Authorization'] = `Bearer ${state.token}`;

  const res = await fetch(`${state.apiBase}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  let payload;
  try {
    payload = await res.json();
  } catch {
    throw new Error(`Request to ${path} returned a non-JSON response (${res.status})`);
  }

  if (!res.ok || payload.success === false) {
    throw new Error(payload.message || `Request failed (${res.status})`);
  }
  return payload.data;
}

function toast(message, isError = false) {
  const el = document.getElementById('toast');
  el.textContent = message;
  el.className = 'toast show' + (isError ? ' error' : '');
  clearTimeout(toast._t);
  toast._t = setTimeout(() => { el.className = 'toast'; }, 3200);
}

// ---------- auth ----------

const authLoggedOut = document.getElementById('auth-logged-out');
const authLoggedIn = document.getElementById('auth-logged-in');

function setAuthedUI() {
  const loggedIn = Boolean(state.token && state.user);
  authLoggedOut.classList.toggle('hidden', loggedIn);
  authLoggedIn.classList.toggle('hidden', !loggedIn);
  document.getElementById('new-session-btn').disabled = !loggedIn;
  document.getElementById('session-start-cta').disabled = !loggedIn;

  if (loggedIn) {
    document.getElementById('identity-name').textContent = state.user.name;
    document.getElementById('identity-email').textContent = state.user.email;
    document.getElementById('identity-avatar').textContent = state.user.name.slice(0, 1).toUpperCase();
    document.getElementById('welcome-name').textContent = state.user.name.split(' ')[0];
  }
}

async function checkApiConnection() {
  const indicator = document.getElementById('api-indicator');
  const status = document.getElementById('api-status');
  try {
    await api('/health', { auth: false });
    indicator.className = 'connection-dot online';
    status.textContent = 'Connected to FastAPI';
  } catch {
    indicator.className = 'connection-dot offline';
    status.textContent = 'Backend unavailable';
  }
}

document.querySelectorAll('.mini-tab').forEach((btn) => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.mini-tab').forEach((b) => b.classList.remove('active'));
    btn.classList.add('active');
    const mode = btn.dataset.authmode;
    document.getElementById('login-form').classList.toggle('hidden', mode !== 'login');
    document.getElementById('register-form').classList.toggle('hidden', mode !== 'register');
  });
});

document.getElementById('register-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    await api('/api/auth/register', {
      auth: false,
      method: 'POST',
      body: { name: fd.get('name'), email: fd.get('email'), password: fd.get('password') },
    });
    toast('Account created — log in below.');
    document.querySelector('[data-authmode="login"]').click();
    e.target.reset();
  } catch (err) {
    toast(err.message, true);
  }
});

document.getElementById('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    const data = await api('/api/auth/login', {
      auth: false,
      method: 'POST',
      body: { email: fd.get('email'), password: fd.get('password') },
    });
    state.token = data.access_token;
    localStorage.setItem('devx_token', state.token);
    state.user = await api('/api/auth/profile');
    setAuthedUI();
    toast(`Welcome back, ${state.user.name}.`);
    await loadSessions();
  } catch (err) {
    toast(err.message, true);
  }
});

document.getElementById('logout-btn').addEventListener('click', () => {
  state.token = null;
  state.user = null;
  state.sessions = [];
  state.activeSessionId = null;
  localStorage.removeItem('devx_token');
  setAuthedUI();
  renderSessionList();
  renderSessionHeader();
  renderDashboard();
  renderSessionPage();
});

// try to resume a session on load
(async function resume() {
  document.getElementById('api-base').value = state.apiBase;
  checkApiConnection();
  renderDashboard();
  renderSessionPage();
  if (state.token) {
    try {
      state.user = await api('/api/auth/profile');
      setAuthedUI();
      await loadSessions();
    } catch {
      state.token = null;
      localStorage.removeItem('devx_token');
      setAuthedUI();
    }
  }
})();

document.getElementById('api-base').addEventListener('change', (e) => {
  state.apiBase = e.target.value.trim().replace(/\/$/, '');
  localStorage.setItem('devx_api_base', state.apiBase);
  toast(`API base set to ${state.apiBase}`);
  checkApiConnection();
});

// ---------- sessions ----------

// The backend has no "list my sessions" endpoint (by design, per the API
// spec) — sessions started in this browser tab are tracked client-side so
// you can switch between them. Reload the page and start a fresh one, or
// paste a known session_id straight into a request if you need to resume
// an old one.

async function loadSessions() {
  renderSessionList();
}

async function startSession() {
  const app_name = prompt('App name', 'Instagram');
  if (!app_name) return;
  const device_model = prompt('Device model', 'iQOO 13') || 'iQOO 13';
  const android_version = prompt('Android version', '15') || '15';

  try {
    const session = await api('/api/session/start', {
      method: 'POST',
      body: { app_name, device_model, android_version },
    });
    state.sessions.unshift(session);
    state.activeSessionId = session.session_id;
    renderSessionList();
    renderSessionHeader();
    toast(`Session started for ${app_name}.`);
    renderDashboard();
    renderSessionPage();
  } catch (err) {
    toast(err.message, true);
  }
}

document.getElementById('new-session-btn').addEventListener('click', startSession);
document.getElementById('session-start-cta').addEventListener('click', startSession);

function renderSessionList() {
  const el = document.getElementById('session-list');
  if (!state.token) {
    el.innerHTML = '<div class="empty-hint">Log in to see sessions</div>';
    return;
  }
  if (state.sessions.length === 0) {
    el.innerHTML = '<div class="empty-hint">No sessions yet in this tab — start one above.</div>';
    return;
  }
  el.innerHTML = '';
  state.sessions.forEach((s) => {
    const div = document.createElement('div');
    div.className = 'session-item' + (s.session_id === state.activeSessionId ? ' active' : '');
    div.innerHTML = `
      <div class="session-item-name">${escapeHtml(s.app_name)}</div>
      <div class="session-item-meta">
        <span class="status-dot status-${s.status}"></span>
        <span>${s.device_model}</span>
        <span>${s.status}</span>
      </div>`;
    div.addEventListener('click', () => {
      state.activeSessionId = s.session_id;
      renderSessionList();
      renderSessionHeader();
      refreshActiveTab();
    });
    el.appendChild(div);
  });
}

function activeSession() {
  return state.sessions.find((s) => s.session_id === state.activeSessionId) || null;
}

function renderSessionHeader() {
  const el = document.getElementById('session-header');
  const s = activeSession();
  if (!s) {
    el.innerHTML = '<div class="session-header-empty">Select or start a test session to begin recording data.</div>';
    document.getElementById('header-session-status').textContent = 'No active session';
    return;
  }

  const m = state.latestMetrics[s.session_id];
  el.innerHTML = `
    <div class="session-header-active">
      <div class="session-title">
        <div class="session-title-app">${escapeHtml(s.app_name)}</div>
        <div class="session-title-meta">${s.device_model} · Android ${s.android_version} · ${s.session_id.slice(0, 8)}</div>
      </div>
      <div class="signal-strip" id="signal-strip">${signalStripHtml(m)}</div>
      <div class="session-actions">
        ${s.status === 'STARTED' ? '<button id="end-session-btn" class="danger">End session</button>' : `<span class="status-dot status-${s.status}"></span> <span style="color:var(--text-dim);font-size:12px">${s.status}</span>`}
      </div>
    </div>`;
  document.getElementById('header-session-status').textContent = `${s.app_name} · ${s.status}`;

  const endBtn = document.getElementById('end-session-btn');
  if (endBtn) {
    endBtn.addEventListener('click', async () => {
      try {
        const updated = await api('/api/session/end', {
          method: 'PUT',
          body: { session_id: s.session_id, status: 'COMPLETED' },
        });
        const idx = state.sessions.findIndex((x) => x.session_id === s.session_id);
        state.sessions[idx] = updated;
        renderSessionList();
        renderSessionHeader();
        renderDashboard();
        renderSessionPage();
        toast('Session ended.');
      } catch (err) {
        toast(err.message, true);
      }
    });
  }
}

function signalStripHtml(m) {
  const rows = [
    ['fps', 'FPS', m ? m.fps : null, 120],
    ['cpu', 'CPU', m ? m.cpu_usage : null, 100],
    ['mem', 'MEM', m ? m.memory_usage : null, 100],
    ['temp', 'TEMP', m ? m.temperature : null, 60],
  ];
  return rows.map(([key, label, value, max]) => {
    const pct = value === null ? 0 : Math.min(100, (value / max) * 100);
    return `
      <div class="signal">
        <span class="signal-label">${label}</span>
        <span class="signal-value">${value === null ? '—' : value}</span>
        <div class="signal-bar"><div class="signal-bar-fill" style="width:${pct}%"></div></div>
      </div>`;
  }).join('');
}

// ---------- navigation ----------

document.querySelectorAll('[data-tab]').forEach((btn) => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav-item').forEach((b) => b.classList.toggle('active', b.dataset.tab === btn.dataset.tab));
    document.querySelectorAll('.page').forEach((p) => p.classList.add('hidden'));
    state.activeTab = btn.dataset.tab;
    const title = btn.textContent.trim();
    document.getElementById('page-title').textContent = title;
    document.getElementById(`panel-${state.activeTab}`).classList.remove('hidden');
    refreshActiveTab();
  });
});

function refreshActiveTab() {
  const s = activeSession();
  if (state.activeTab === 'dashboard') { renderDashboard(); return; }
  if (state.activeTab === 'session') { renderSessionPage(); return; }
  if (!s) return;
  if (state.activeTab === 'metrics') loadMetrics(s.session_id);
  if (state.activeTab === 'interactions') loadInteractions(s.session_id);
  if (state.activeTab === 'screenshots') loadScreenshots(s.session_id);
  if (state.activeTab === 'ai') loadReports(s.session_id);
  if (state.activeTab === 'replay') { /* explicit load button */ }
}

function renderDashboard() {
  const s = activeSession();
  const card = document.getElementById('dashboard-session-card');
  const recent = document.getElementById('recent-sessions');
  if (s) {
    card.querySelector('h2').textContent = `${s.app_name} test session`;
    card.querySelector('p').textContent = `${s.device_model} · Android ${s.android_version} · ${s.session_id.slice(0, 8)}`;
    card.querySelector('.live-label').innerHTML = `<i></i> ${s.status === 'STARTED' ? 'SESSION ACTIVE' : 'SESSION COMPLETE'}`;
    recent.innerHTML = state.sessions.map((session) => `<button class="recent-session ${session.session_id === state.activeSessionId ? 'selected' : ''}" data-session-id="${session.session_id}"><span class="status-dot status-${session.status}"></span><span><strong>${escapeHtml(session.app_name)}</strong><small>${session.device_model}</small></span><b>${session.status}</b></button>`).join('');
    recent.querySelectorAll('[data-session-id]').forEach((item) => item.addEventListener('click', () => { state.activeSessionId = item.dataset.sessionId; renderSessionList(); renderSessionHeader(); refreshActiveTab(); }));
    loadDashboardMetrics(s.session_id);
  } else {
    recent.innerHTML = '<div class="empty-state compact"><span>◉</span><p>No sessions yet.</p></div>';
    ['fps', 'cpu', 'memory', 'battery', 'temperature', 'drops'].forEach((key) => { document.getElementById(`kpi-${key}`).textContent = '—'; });
  }
}

async function loadDashboardMetrics(sessionId) {
  try {
    const rows = await api(`/api/metrics/session/${sessionId}`);
    const latest = rows[rows.length - 1];
    if (!latest) return;
    state.latestMetrics[sessionId] = latest;
    const values = { fps: latest.fps, cpu: `${latest.cpu_usage}%`, memory: `${latest.memory_usage}%`, battery: `${latest.battery_usage}%`, temperature: `${latest.temperature}°`, drops: latest.frame_drops };
    Object.entries(values).forEach(([key, value]) => { document.getElementById(`kpi-${key}`).textContent = value; });
    document.getElementById('dashboard-updated').textContent = `Updated ${formatTime(latest.recorded_at)}`;
    document.getElementById('performance-chart').innerHTML = rows.slice(-12).map((row) => `<div class="chart-column" title="FPS ${row.fps} · CPU ${row.cpu_usage}%"><div class="chart-bars"><i style="height:${Math.min(100, row.fps / 1.2)}%"></i><b style="height:${row.cpu_usage}%"></b></div><small>${formatTime(row.recorded_at)}</small></div>`).join('');
  } catch (err) { toast(err.message, true); }
}

function renderSessionPage() {
  const s = activeSession();
  const card = document.getElementById('session-detail-card');
  if (!s) { card.innerHTML = '<div class="empty-state"><span>◉</span><h3>No session selected</h3><p>Start a test session to unlock recording controls and live telemetry.</p></div>'; return; }
  card.innerHTML = `<div class="session-detail-top"><div><span class="live-label"><i></i> ${s.status}</span><h2>${escapeHtml(s.app_name)}</h2><p>${escapeHtml(s.device_model)} · Android ${escapeHtml(s.android_version)}</p></div><span class="session-id">${escapeHtml(s.session_id)}</span></div><div class="detail-grid"><div><span>STARTED</span><strong>${formatDateTime(s.start_time)}</strong></div><div><span>ENDED</span><strong>${s.end_time ? formatDateTime(s.end_time) : 'In progress'}</strong></div><div><span>STATUS</span><strong class="status-text">${s.status}</strong></div></div>${s.status === 'STARTED' ? '<button id="session-end-cta" class="danger-btn">End session</button>' : ''}`;
  const end = document.getElementById('session-end-cta');
  if (end) end.addEventListener('click', () => document.getElementById('end-session-btn')?.click());
}

function requireSession() {
  const s = activeSession();
  if (!s) {
    toast('Select or start a session first.', true);
    return null;
  }
  return s;
}

// ---------- metrics ----------

document.getElementById('metric-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const s = requireSession();
  if (!s) return;
  const fd = new FormData(e.target);
  try {
    const metric = await api('/api/metrics', {
      method: 'POST',
      body: {
        session_id: s.session_id,
        fps: Number(fd.get('fps')),
        memory_usage: Number(fd.get('memory_usage')),
        battery_usage: Number(fd.get('battery_usage')),
        cpu_usage: Number(fd.get('cpu_usage')),
        temperature: Number(fd.get('temperature')),
        frame_drops: Number(fd.get('frame_drops')),
      },
    });
    state.latestMetrics[s.session_id] = metric;
    renderSessionHeader();
    await loadMetrics(s.session_id, true);
    toast('Metric recorded.');
  } catch (err) {
    toast(err.message, true);
  }
});

async function loadMetrics(sessionId, flashLast = false) {
  try {
    const rows = await api(`/api/metrics/session/${sessionId}`);
    const tbody = document.querySelector('#metrics-table tbody');
    tbody.innerHTML = rows.map((m) => `
      <tr>
        <td>${formatTime(m.recorded_at)}</td>
        <td>${m.fps}</td><td>${m.cpu_usage}</td><td>${m.memory_usage}</td>
        <td>${m.temperature}</td><td>${m.battery_usage}</td><td>${m.frame_drops}</td>
      </tr>`).join('') || '<tr><td colspan="7" style="color:var(--text-faint)">No metrics yet.</td></tr>';
    if (flashLast && tbody.lastElementChild) {
      [...tbody.lastElementChild.children].forEach((td) => td.classList.add('flash'));
    }
    if (rows.length) state.latestMetrics[sessionId] = rows[rows.length - 1];
  } catch (err) {
    toast(err.message, true);
  }
}

// ---------- interactions ----------

document.getElementById('interaction-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const s = requireSession();
  if (!s) return;
  const fd = new FormData(e.target);
  let actionData = {};
  try {
    actionData = fd.get('action_data') ? JSON.parse(fd.get('action_data')) : {};
  } catch {
    toast('Action data must be valid JSON.', true);
    return;
  }
  try {
    await api('/api/interactions', {
      method: 'POST',
      body: {
        session_id: s.session_id,
        action_type: fd.get('action_type'),
        screen_name: fd.get('screen_name'),
        action_data: actionData,
      },
    });
    await loadInteractions(s.session_id);
    toast('Interaction recorded.');
  } catch (err) {
    toast(err.message, true);
  }
});

async function loadInteractions(sessionId) {
  try {
    const rows = await api(`/api/interactions/session/${sessionId}`);
    const tbody = document.querySelector('#interactions-table tbody');
    tbody.innerHTML = rows.map((i) => `
      <tr>
        <td>${i.sequence_number}</td><td>${i.action_type}</td><td>${escapeHtml(i.screen_name)}</td>
        <td>${formatTime(i.timestamp)}</td><td>${escapeHtml(JSON.stringify(i.action_data))}</td>
      </tr>`).join('') || '<tr><td colspan="5" style="color:var(--text-faint)">No interactions yet.</td></tr>';
  } catch (err) {
    toast(err.message, true);
  }
}

// ---------- screenshots ----------

document.getElementById('screenshot-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const s = requireSession();
  if (!s) return;
  const fd = new FormData(e.target);
  try {
    await api('/api/screenshots', {
      method: 'POST',
      body: {
        session_id: s.session_id,
        screen_name: fd.get('screen_name'),
        file_name: fd.get('file_name'),
        storage_path: fd.get('storage_path'),
        width: Number(fd.get('width')),
        height: Number(fd.get('height')),
        metadata: {},
      },
    });
    await loadScreenshots(s.session_id);
    toast('Screenshot metadata recorded.');
  } catch (err) {
    toast(err.message, true);
  }
});

async function loadScreenshots(sessionId) {
  try {
    const rows = await api(`/api/screenshots/session/${sessionId}`);
    const tbody = document.querySelector('#screenshots-table tbody');
    tbody.innerHTML = rows.map((s) => `
      <tr>
        <td>${formatTime(s.timestamp)}</td><td>${escapeHtml(s.screen_name)}</td>
        <td>${escapeHtml(s.file_name)}</td><td>${s.width}×${s.height}</td>
      </tr>`).join('') || '<tr><td colspan="4" style="color:var(--text-faint)">No screenshots yet.</td></tr>';
  } catch (err) {
    toast(err.message, true);
  }
}

// ---------- AI reports ----------

document.getElementById('run-ai-btn').addEventListener('click', async () => {
  const s = requireSession();
  if (!s) return;
  try {
    const result = await api('/api/ai/analyze', { method: 'POST', body: { session_id: s.session_id } });
    renderReports(result.reports);
    toast(`Analysis complete — ${result.reports.length} finding(s).`);
  } catch (err) {
    toast(err.message, true);
  }
});

async function loadReports(sessionId) {
  try {
    const result = await api(`/api/ai/report/${sessionId}`);
    renderReports(result.reports);
  } catch (err) {
    toast(err.message, true);
  }
}

function renderReports(reports) {
  const el = document.getElementById('report-list');
  if (!reports.length) {
    el.innerHTML = '<div class="empty-hint">No reports yet — run an analysis.</div>';
    return;
  }
  el.innerHTML = reports.map((r) => `
    <div class="report-card sev-${r.severity}">
      <div class="report-top">
        <span class="report-issue">${r.issue_type}</span>
        <span class="report-sev">${r.severity}</span>
      </div>
      <div class="report-cause">${escapeHtml(r.root_cause)}</div>
      <div class="report-explain">${escapeHtml(r.explanation)}</div>
      <div class="report-fix"><strong>Suggested fix —</strong> ${escapeHtml(r.suggested_fix)}</div>
      <div class="report-confidence">confidence ${(r.confidence_score * 100).toFixed(0)}%</div>
    </div>`).join('');
}

// ---------- replay ----------

document.getElementById('load-replay-btn').addEventListener('click', async () => {
  const s = requireSession();
  if (!s) return;
  try {
    const result = await api(`/api/replay/${s.session_id}`);
    const el = document.getElementById('replay-list');
    el.innerHTML = result.actions.map((a) => `
      <li>
        <span class="replay-seq">#${a.sequence_number}</span>
        <span class="replay-type">${a.action_type}</span>
        <span class="replay-screen">${escapeHtml(a.screen_name)}</span>
        <span class="replay-time">${formatTime(a.timestamp)} · ${escapeHtml(JSON.stringify(a.action_data))}</span>
      </li>`).join('') || '<li style="color:var(--text-faint)">No interactions recorded for this session.</li>';
    toast(`Replay loaded — ${result.total_actions} action(s).`);
  } catch (err) {
    toast(err.message, true);
  }
});

// ---------- helpers ----------

function formatTime(iso) {
  try {
    return new Date(iso).toLocaleTimeString();
  } catch {
    return iso;
  }
}

function formatDateTime(iso) {
  try { return new Date(iso).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }); }
  catch { return iso; }
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
