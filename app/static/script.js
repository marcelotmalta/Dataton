/* =============================================
   PAINEL PEDAGÓGICO — Script Principal
   ============================================= */

// State
let currentStudent = null;
let analysisData = null;
let pendingTrajectory = null;

/* =============================================
   Background Particles
   ============================================= */
(function initParticles() {
    const container = document.getElementById('bgParticles');
    if (!container) return;
    for (let i = 0; i < 12; i++) {
        const p = document.createElement('div');
        p.className = 'particle';
        const size = Math.random() * 120 + 40;
        p.style.width = size + 'px';
        p.style.height = size + 'px';
        p.style.left = Math.random() * 100 + '%';
        p.style.top = Math.random() * 100 + '%';
        p.style.animationDelay = (Math.random() * 10) + 's';
        p.style.animationDuration = (15 + Math.random() * 15) + 's';
        container.appendChild(p);
    }
})();

/* =============================================
   API Health Check
   ============================================= */
(async function checkHealth() {
    try {
        const r = await fetch('/health');
        if (!r.ok) throw new Error();
    } catch {
        const el = document.getElementById('apiStatus');
        if (el) {
            el.innerHTML = '<span class="status-dot" style="background:var(--danger)"></span><span>API Offline</span>';
            el.style.color = 'var(--danger)';
            el.style.background = 'rgba(248,113,113,0.1)';
            el.style.borderColor = 'rgba(248,113,113,0.2)';
        }
    }
})();

/* =============================================
   Utility Functions
   ============================================= */
function updateSlider(id) {
    const el = document.getElementById(id);
    const valEl = document.getElementById('val_' + id);
    if (el && valEl) valEl.innerText = el.value;
}

function show(id) { document.getElementById(id)?.classList.remove('hidden'); }
function hide(id) { document.getElementById(id)?.classList.add('hidden'); }

function safeNum(v, decimals = 1) {
    if (v === null || v === undefined || isNaN(v)) return '—';
    return Number(v).toFixed(decimals);
}

/* =============================================
   Tab Navigation
   ============================================= */
function switchTab(tabId, btn) {
    // Deactivate all
    document.querySelectorAll('#profileSection .tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('#profileSection .tab-content').forEach(tc => tc.classList.remove('active'));

    // Activate selected
    btn.classList.add('active');
    document.getElementById(tabId)?.classList.add('active');

    // Draw chart when trajectory tab becomes visible
    if (tabId === 'tabTrajectory' && pendingTrajectory) {
        requestAnimationFrame(() => drawTrajectoryChart(pendingTrajectory));
    }
}

/* =============================================
   Student Search
   ============================================= */
async function searchStudent() {
    const name = document.getElementById('studentName').value.trim();
    if (!name) return;

    const results = document.getElementById('searchResults');
    results.innerHTML = '<div style="padding:16px;text-align:center"><div class="spinner"></div></div>';
    show('searchResults');

    try {
        const response = await fetch(`/students/${encodeURIComponent(name)}`);
        if (!response.ok) throw new Error('Aluno não encontrado');
        const data = await response.json();

        results.innerHTML = '';

        if (!data.historico || data.historico.length === 0) {
            results.innerHTML = '<div style="padding:16px;color:var(--text-muted)">Nenhum registro encontrado.</div>';
            return;
        }

        // Group years
        const anos = data.historico.map(r => r.ANO).join(', ');
        const item = document.createElement('div');
        item.className = 'search-result-item';
        item.innerHTML = `
            <div>
                <strong>${data.nome}</strong>
                <div class="search-result-meta">${data.historico.length} registro(s) — Anos: ${anos}</div>
            </div>
            <span style="color:var(--accent)">→</span>
        `;
        item.onclick = () => selectStudent(data);
        results.appendChild(item);

    } catch (error) {
        results.innerHTML = `<div style="padding:16px;color:var(--danger)">${error.message}</div>`;
    }
}

/* =============================================
   Student Selection — Load Profile
   ============================================= */
async function selectStudent(data) {
    currentStudent = data;
    hide('searchResults');

    // Show sections
    show('profileSection');
    show('evaluationSection');
    document.getElementById('btnSimulate').style.display = 'inline-flex';

    // Set profile header
    const latest = data.historico[data.historico.length - 1];
    document.getElementById('profileName').innerText = data.nome;
    document.getElementById('profilePhase').innerText = `Fase ${latest.FASE || '—'}`;

    // Fill history table
    fillHistoryTable(data.historico);

    // Fill form with latest data
    fillForm(latest);

    // Load deep analysis
    loadDeepAnalysis(data.nome);

    // Scroll to profile
    document.getElementById('profileSection').scrollIntoView({ behavior: 'smooth' });
}

/* =============================================
   History Table
   ============================================= */
function fillHistoryTable(historico) {
    const tbody = document.getElementById('historyBody');
    tbody.innerHTML = '';

    historico.forEach((r, idx) => {
        const tr = document.createElement('tr');
        tr.className = idx === historico.length - 1 ? 'selected' : '';
        tr.innerHTML = `
            <td>${r.ANO || '—'}</td>
            <td>${r.FASE || '—'}</td>
            <td>${safeNum(r.INDE)}</td>
            <td>${safeNum(r.IDA)}</td>
            <td>${safeNum(r.IEG)}</td>
            <td>${safeNum(r.IPS)}</td>
            <td>${safeNum(r.IPV)}</td>
            <td>${r.DEFA ?? '—'}</td>
        `;
        tr.style.cursor = 'pointer';
        tr.onclick = () => {
            fillForm(r);
            tbody.querySelectorAll('tr').forEach(t => t.classList.remove('selected'));
            tr.classList.add('selected');
        };
        tbody.appendChild(tr);
    });
}

/* =============================================
   Fill Form
   ============================================= */
function fillForm(record) {
    const fields = ['IAN', 'IDA', 'IEG', 'IAA', 'IPS', 'IPP', 'IPV', 'FASE', 'DEFA'];
    fields.forEach(f => {
        const el = document.getElementById(f);
        if (el && record[f] !== undefined && record[f] !== null) {
            el.value = record[f];
            if (f !== 'DEFA') updateSlider(f);
        }
    });
}

/* =============================================
   Deep Analysis (Trajectory + Diagnostic)
   ============================================= */
async function loadDeepAnalysis(name) {
    try {
        const response = await fetch(`/students/${encodeURIComponent(name)}/analysis`);
        if (!response.ok) throw new Error('Análise indisponível');
        analysisData = await response.json();

        renderTrajectory(analysisData.trajetoria);
        renderIpvIda(analysisData.cruzamento_ipv_ida);
        renderDiagnostics(analysisData.diagnosticos, analysisData.resumo);

    } catch (err) {
        document.getElementById('trajectorySummary').innerHTML =
            `<p class="placeholder-text">${err.message}</p>`;
        document.getElementById('diagnosticContent').innerHTML =
            `<p class="placeholder-text">${err.message}</p>`;
    }
}

/* =============================================
   Render Trajectory
   ============================================= */
function renderTrajectory(traj) {
    const summary = document.getElementById('trajectorySummary');

    if (!traj) {
        summary.innerHTML = '<p class="placeholder-text">Trajetória indisponível.</p>';
        return;
    }

    const trendIcons = {
        'ascendente': '📈',
        'estável': '➡️',
        'descendente': '📉',
        'insuficiente': 'ℹ️'
    };
    const trendColors = {
        'ascendente': 'var(--success)',
        'estável': 'var(--info)',
        'descendente': 'var(--danger)',
        'insuficiente': 'var(--text-muted)'
    };

    summary.innerHTML = `
        <div class="traj-stat">
            <div class="label">Tendência</div>
            <div class="value" style="color:${trendColors[traj.tendencia] || 'inherit'}">
                ${trendIcons[traj.tendencia] || ''} ${traj.tendencia || '—'}
            </div>
        </div>
        <div class="traj-stat">
            <div class="label">Inclinação</div>
            <div class="value">${safeNum(traj.inclinacao, 4)}</div>
        </div>
        <div class="traj-stat">
            <div class="label">Registros</div>
            <div class="value">${traj.num_registros || '—'}</div>
        </div>
    `;

    // Store for deferred drawing (canvas may be in a hidden tab)
    pendingTrajectory = traj;

    // Draw immediately if trajectory tab is currently visible
    if (document.getElementById('tabTrajectory')?.classList.contains('active')) {
        requestAnimationFrame(() => drawTrajectoryChart(traj));
    }
}

/* =============================================
   Canvas Chart for INDE Trajectory
   ============================================= */
function drawTrajectoryChart(traj) {
    const canvas = document.getElementById('trajectoryChart');
    if (!canvas || !traj.anos || traj.anos.length < 2) return;

    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = 280 * dpr;
    canvas.style.width = rect.width + 'px';
    canvas.style.height = '280px';
    ctx.scale(dpr, dpr);

    const W = rect.width;
    const H = 280;
    const pad = { top: 30, right: 30, bottom: 40, left: 50 };
    const chartW = W - pad.left - pad.right;
    const chartH = H - pad.top - pad.bottom;

    const values = traj.inde_values.filter(v => v !== null);
    const years = traj.anos;
    const minV = Math.floor(Math.min(...values) - 0.5);
    const maxV = Math.ceil(Math.max(...values) + 0.5);

    function xPos(i) { return pad.left + (i / (years.length - 1)) * chartW; }
    function yPos(v) { return pad.top + chartH - ((v - minV) / (maxV - minV)) * chartH; }

    // Clear
    ctx.clearRect(0, 0, W, H);

    // Grid lines
    ctx.strokeStyle = 'rgba(255,255,255,0.06)';
    ctx.lineWidth = 1;
    const steps = 5;
    for (let i = 0; i <= steps; i++) {
        const v = minV + (maxV - minV) * (i / steps);
        const y = yPos(v);
        ctx.beginPath();
        ctx.moveTo(pad.left, y);
        ctx.lineTo(W - pad.right, y);
        ctx.stroke();

        ctx.fillStyle = 'rgba(255,255,255,0.3)';
        ctx.font = '11px Inter, sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(v.toFixed(1), pad.left - 8, y + 4);
    }

    // Year labels
    ctx.textAlign = 'center';
    ctx.fillStyle = 'rgba(255,255,255,0.4)';
    years.forEach((year, i) => {
        ctx.fillText('20' + year, xPos(i), H - pad.bottom + 20);
    });

    // Area fill
    const gradient = ctx.createLinearGradient(0, pad.top, 0, H - pad.bottom);
    gradient.addColorStop(0, 'rgba(124, 92, 252, 0.25)');
    gradient.addColorStop(1, 'rgba(124, 92, 252, 0.02)');

    ctx.beginPath();
    ctx.moveTo(xPos(0), yPos(values[0]));
    for (let i = 1; i < values.length; i++) {
        ctx.lineTo(xPos(i), yPos(values[i]));
    }
    ctx.lineTo(xPos(values.length - 1), H - pad.bottom);
    ctx.lineTo(xPos(0), H - pad.bottom);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // Line
    ctx.beginPath();
    ctx.moveTo(xPos(0), yPos(values[0]));
    for (let i = 1; i < values.length; i++) {
        ctx.lineTo(xPos(i), yPos(values[i]));
    }
    ctx.strokeStyle = '#7c5cfc';
    ctx.lineWidth = 2.5;
    ctx.lineJoin = 'round';
    ctx.stroke();

    // Points
    values.forEach((v, i) => {
        ctx.beginPath();
        ctx.arc(xPos(i), yPos(v), 5, 0, Math.PI * 2);
        ctx.fillStyle = '#7c5cfc';
        ctx.fill();
        ctx.strokeStyle = '#1e1b3a';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Value labels
        ctx.fillStyle = 'rgba(255,255,255,0.7)';
        ctx.font = 'bold 12px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(v.toFixed(1), xPos(i), yPos(v) - 12);
    });

    // Title
    ctx.fillStyle = 'rgba(255,255,255,0.35)';
    ctx.font = '12px Inter, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('Evolução do INDE', pad.left, 16);
}

/* =============================================
   Render IPV × IDA Crossover
   ============================================= */
function renderIpvIda(cross) {
    const el = document.getElementById('ipvIdaContent');
    if (!cross || !cross.analise_disponivel) {
        el.innerHTML = '<span class="placeholder-text">Dados insuficientes para cruzamento.</span>';
        return;
    }

    const typeLabels = {
        'técnica': { icon: '📘', color: 'var(--info)' },
        'maturidade': { icon: '📙', color: 'var(--warning)' },
        'combinada': { icon: '📕', color: 'var(--danger)' },
        'nenhuma': { icon: '✅', color: 'var(--success)' },
        'atípica': { icon: '❓', color: 'var(--text-muted)' }
    };

    const t = typeLabels[cross.tipo_queda] || typeLabels['atípica'];
    el.innerHTML = `
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
            <span style="font-size:1.3rem">${t.icon}</span>
            <strong style="color:${t.color};font-size:1rem;">Tipo: ${cross.tipo_queda || '—'}</strong>
        </div>
        <p style="color:var(--text-secondary);font-size:0.88rem;line-height:1.6;">${cross.descricao || ''}</p>
    `;
}

/* =============================================
   Render Diagnostics
   ============================================= */
function renderDiagnostics(diagnosticos, resumo) {
    const container = document.getElementById('diagnosticContent');
    const summaryEl = document.getElementById('diagnosticSummary');

    if (!diagnosticos || diagnosticos.length === 0) {
        container.innerHTML = '<div class="diagnostic-clean">✅ Nenhum diagnóstico de risco identificado.</div>';
        summaryEl.innerHTML = resumo || '';
        return;
    }

    const typeLabels = {
        'academico': '📘 Gargalo Acadêmico',
        'desengajamento': '📙 Risco de Desengajamento',
        'psicossocial': '📕 Vulnerabilidade Psicossocial'
    };

    container.innerHTML = diagnosticos.map((d, idx) => `
        <div class="diagnostic-card ${d.gravidade || ''}" style="animation-delay:${idx * 0.1}s">
            <div class="diag-header">
                <span class="diag-type">${typeLabels[d.tipo] || d.tipo}</span>
                <span class="severity-badge ${d.gravidade || ''}">${d.gravidade || '—'}</span>
            </div>
            <div style="font-size:0.84rem;color:var(--text-secondary);margin-bottom:6px;">
                Indicadores: ${(d.indicadores_afetados || []).join(', ')}
            </div>
            <ul class="intervention-list">
                ${(d.intervencoes || []).map(i => `<li>${i}</li>`).join('')}
            </ul>
        </div>
    `).join('');

    summaryEl.innerHTML = resumo || '';
}

/* =============================================
   Prediction
   ============================================= */
async function submitPrediction() {
    const fields = ['IAN', 'IDA', 'IEG', 'IAA', 'IPS', 'IPP', 'IPV', 'FASE', 'DEFA'];
    const data = {};
    fields.forEach(f => {
        data[f] = parseFloat(document.getElementById(f).value);
    });

    // Add student name if available
    if (currentStudent) {
        data.NOME = currentStudent.nome;
    }

    try {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });

        if (!response.ok) throw new Error('Erro na previsão');
        const result = await response.json();

        show('resultSection');
        renderPredictionResult(result);
        document.getElementById('resultSection').scrollIntoView({ behavior: 'smooth' });

    } catch (error) {
        alert('Erro ao realizar previsão: ' + error.message);
    }
}

/* =============================================
   Render Prediction Result
   ============================================= */
function renderPredictionResult(result) {
    // Badge
    const badge = document.getElementById('predictionBadge');
    badge.innerText = result.prediction || '—';

    // Badge color based on prediction
    const badgeColors = {
        'quartzo': 'var(--danger)',
        'ágata': 'var(--warning)',
        'ametista': 'var(--info)',
        'topázio': 'var(--success)'
    };
    const predLower = (result.prediction || '').toLowerCase();
    badge.style.background = badgeColors[predLower] || 'var(--accent)';

    // Risk
    const riskScore = document.getElementById('riskScore');
    riskScore.innerText = result.risk_score !== null ? safeNum(result.risk_score, 3) : '—';

    const riskTier = document.getElementById('riskTier');
    riskTier.innerText = result.risk_tier || '—';
    const tierColors = {
        'Baixo': 'var(--success)',
        'Médio': 'var(--warning)',
        'Alto': 'var(--danger)',
        'Crítico': 'var(--danger-deep)'
    };
    riskTier.style.color = tierColors[result.risk_tier] || 'inherit';

    // Action
    document.getElementById('actionText').innerText = result.acao_sugerida || '—';

    // Messages
    if (result.suggested_messages) {
        document.getElementById('messageFamily').innerText =
            result.suggested_messages.family || 'Nenhuma mensagem disponível';
        document.getElementById('messageProfessor').innerText =
            result.suggested_messages.professor || 'Nenhuma mensagem disponível';
    }

    // Probabilities
    renderProbabilities(result.probabilities);
}

/* =============================================
   Render Probabilities as Bars
   ============================================= */
function renderProbabilities(probs) {
    const container = document.getElementById('probBars');
    if (!probs) { container.innerHTML = '—'; return; }

    container.innerHTML = Object.entries(probs)
        .sort(([, a], [, b]) => b - a)
        .map(([label, val]) => {
            const pct = (val * 100).toFixed(1);
            return `
                <div class="prob-row">
                    <span class="prob-label">${label}</span>
                    <div class="prob-bar-bg">
                        <div class="prob-bar-fill" style="width:${pct}%"></div>
                    </div>
                    <span class="prob-pct">${pct}%</span>
                </div>
            `;
        }).join('');
}

/* =============================================
   Simulation
   ============================================= */
async function runSimulation() {
    if (!currentStudent) {
        alert('Selecione um aluno antes de simular.');
        return;
    }

    const fields = ['IAN', 'IDA', 'IEG', 'IAA', 'IPS', 'IPP', 'IPV'];
    const changes = {};

    // Compare current slider values with the latest historical record
    const latest = currentStudent.historico[currentStudent.historico.length - 1];
    fields.forEach(f => {
        const currentVal = parseFloat(document.getElementById(f).value);
        const originalVal = parseFloat(latest[f]);
        if (!isNaN(currentVal) && !isNaN(originalVal) && Math.abs(currentVal - originalVal) > 0.01) {
            changes[f] = currentVal;
        }
    });

    if (Object.keys(changes).length === 0) {
        alert('Ajuste pelo menos um indicador para simular um cenário diferente.');
        return;
    }

    try {
        const response = await fetch('/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                NOME: currentStudent.nome,
                changes: changes
            }),
        });

        if (!response.ok) throw new Error('Erro na simulação');
        const result = await response.json();

        show('simulationSection');
        renderSimulation(result);
        document.getElementById('simulationSection').scrollIntoView({ behavior: 'smooth' });

    } catch (error) {
        alert('Erro ao simular: ' + error.message);
    }
}

/* =============================================
   Render Simulation Result
   ============================================= */
function renderSimulation(result) {
    const comp = document.getElementById('simulationComparison');

    comp.innerHTML = `
        <div class="sim-side">
            <span class="label">Original</span>
            <div class="sim-value">${result.original_prediction || '—'}</div>
            <div style="margin-top:6px;font-size:0.8rem;color:var(--text-muted)">
                Risco: ${safeNum(result.original_risk, 3)}
            </div>
        </div>
        <div class="sim-arrow">→</div>
        <div class="sim-side">
            <span class="label">Simulado</span>
            <div class="sim-value" style="color:var(--accent-hover)">${result.simulated_prediction || '—'}</div>
            <div style="margin-top:6px;font-size:0.8rem;color:var(--text-muted)">
                Risco: ${safeNum(result.simulated_risk, 3)}
            </div>
        </div>
    `;

    const impactEl = document.getElementById('simulationImpact');
    impactEl.innerText = result.impacto || '—';

    // Color impact box
    if (result.delta_risk !== null && result.delta_risk < -0.01) {
        impactEl.style.background = 'rgba(52, 211, 153, 0.1)';
        impactEl.style.borderColor = 'rgba(52, 211, 153, 0.2)';
        impactEl.style.color = 'var(--success)';
    } else if (result.delta_risk !== null && result.delta_risk > 0.01) {
        impactEl.style.background = 'rgba(248,113,113,0.1)';
        impactEl.style.borderColor = 'rgba(248,113,113,0.2)';
        impactEl.style.color = 'var(--danger)';
    } else {
        impactEl.style.background = '';
        impactEl.style.borderColor = '';
        impactEl.style.color = '';
    }
}
