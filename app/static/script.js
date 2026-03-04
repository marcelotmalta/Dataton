/* ============================================
   STUDENT PERFORMANCE — MAIN SCRIPT
   ============================================ */

/* ---------- State ---------- */
let selectedStudentName = null;
let currentHistorico = [];
let historyChartInstance = null;
let resultChartInstance = null;

/* ---------- Indicator metadata ---------- */
const INDICATORS = ['IAN', 'IDA', 'IEG', 'IAA', 'IPS', 'IPP', 'IPV'];
const INDICATOR_COLORS = {
    IAN: { line: '#7c3aed', bg: 'rgba(124,58,237,0.15)' },
    IDA: { line: '#2dd4bf', bg: 'rgba(45,212,191,0.15)' },
    IEG: { line: '#f59e0b', bg: 'rgba(245,158,11,0.15)' },
    IAA: { line: '#ef4444', bg: 'rgba(239,68,68,0.15)' },
    IPS: { line: '#3b82f6', bg: 'rgba(59,130,246,0.15)' },
    IPP: { line: '#ec4899', bg: 'rgba(236,72,153,0.15)' },
    IPV: { line: '#10b981', bg: 'rgba(16,185,129,0.15)' },
};

const INDICATOR_LABELS = {
    IAN: 'Adequação de Nível',
    IDA: 'Desempenho Acadêmico',
    IEG: 'Engajamento',
    IAA: 'Autoavaliação',
    IPS: 'Psico-Social',
    IPP: 'Psicopedagógico',
    IPV: 'Ponto de Virada',
};

/* ============================================
   Utility Functions
   ============================================ */

function updateVal(id, val) {
    document.getElementById('val_' + id).innerText = val;
}

function toFiniteNumber(value) {
    const num = Number(value);
    return Number.isFinite(num) ? num : null;
}

function sortHistoricoByYear(historico) {
    return [...historico].sort((a, b) => {
        const anoA = toFiniteNumber(a?.ANO) ?? 0;
        const anoB = toFiniteNumber(b?.ANO) ?? 0;
        if (anoA !== anoB) return anoA - anoB;
        const faseA = toFiniteNumber(a?.FASE) ?? 0;
        const faseB = toFiniteNumber(b?.FASE) ?? 0;
        return faseA - faseB;
    });
}

function sortHistoricoByRecency(historico) {
    return [...historico].sort((a, b) => {
        const anoA = toFiniteNumber(a?.ANO) ?? -Infinity;
        const anoB = toFiniteNumber(b?.ANO) ?? -Infinity;
        if (anoA !== anoB) return anoB - anoA;
        const faseA = toFiniteNumber(a?.FASE) ?? -Infinity;
        const faseB = toFiniteNumber(b?.FASE) ?? -Infinity;
        return faseB - faseA;
    });
}

/* ============================================
   Chart Helpers
   ============================================ */

function getChartDefaults() {
    return {
        color: '#94a3b8',
        borderColor: 'rgba(255,255,255,0.06)',
        font: { family: "'Inter', sans-serif" },
    };
}

function buildLineChartData(historico, extraPoint) {
    const sorted = sortHistoricoByYear(historico);
    const labels = sorted.map(h => {
        const ano = toFiniteNumber(h.ANO);
        const fase = toFiniteNumber(h.FASE);
        if (ano !== null && fase !== null) return `${ano} (F${Math.round(fase)})`;
        if (ano !== null) return `${ano}`;
        return '?';
    });

    if (extraPoint) {
        labels.push('Nova Avaliação');
    }

    const datasets = INDICATORS.map(ind => {
        const data = sorted.map(h => toFiniteNumber(h[ind]));
        if (extraPoint) {
            data.push(toFiniteNumber(extraPoint[ind]));
        }
        return {
            label: ind,
            data: data,
            borderColor: INDICATOR_COLORS[ind].line,
            backgroundColor: INDICATOR_COLORS[ind].bg,
            borderWidth: 2.5,
            pointRadius: extraPoint ? [...sorted.map(() => 4), 7] : 4,
            pointBackgroundColor: INDICATOR_COLORS[ind].line,
            pointBorderColor: '#0f0f1a',
            pointBorderWidth: 2,
            pointHoverRadius: 7,
            tension: 0.35,
            fill: false,
        };
    });

    return { labels, datasets };
}

function createChartOptions(title) {
    const defaults = getChartDefaults();
    return {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
            legend: {
                position: 'top',
                labels: {
                    color: defaults.color,
                    font: { ...defaults.font, size: 11, weight: '500' },
                    usePointStyle: true,
                    pointStyle: 'circle',
                    padding: 14,
                },
            },
            title: {
                display: !!title,
                text: title || '',
                color: '#f1f5f9',
                font: { ...defaults.font, size: 14, weight: '600' },
                padding: { bottom: 14 },
            },
            tooltip: {
                backgroundColor: 'rgba(15,15,26,0.95)',
                titleColor: '#f1f5f9',
                bodyColor: '#94a3b8',
                borderColor: 'rgba(255,255,255,0.1)',
                borderWidth: 1,
                padding: 12,
                cornerRadius: 10,
                titleFont: { ...defaults.font, weight: '600' },
                bodyFont: { ...defaults.font },
            },
        },
        scales: {
            x: {
                grid: { color: defaults.borderColor },
                ticks: { color: defaults.color, font: { ...defaults.font, size: 11 } },
            },
            y: {
                min: 0,
                max: 10,
                grid: { color: defaults.borderColor },
                ticks: { color: defaults.color, font: { ...defaults.font, size: 11 }, stepSize: 2 },
            },
        },
    };
}

function renderChart(canvasId, historico, extraPoint, title) {
    const canvas = document.getElementById(canvasId);
    const ctx = canvas.getContext('2d');
    const chartData = buildLineChartData(historico, extraPoint);
    const options = createChartOptions(title);

    // Destroy existing chart on same canvas
    if (canvasId === 'historyChart' && historyChartInstance) {
        historyChartInstance.destroy();
        historyChartInstance = null;
    }
    if (canvasId === 'resultChart' && resultChartInstance) {
        resultChartInstance.destroy();
        resultChartInstance = null;
    }

    const chart = new Chart(ctx, {
        type: 'line',
        data: chartData,
        options: options,
    });

    if (canvasId === 'historyChart') historyChartInstance = chart;
    if (canvasId === 'resultChart') resultChartInstance = chart;

    return chart;
}

/* ============================================
   Form Functions
   ============================================ */

function fillForm(student) {
    const fields = ['IAN', 'IDA', 'IEG', 'IAA', 'IPS', 'IPP', 'IPV', 'FASE', 'DEFA'];

    fields.forEach(field => {
        const el = document.getElementById(field);
        if (!el) return;

        const parsedValue = toFiniteNumber(student[field]);
        if (parsedValue === null) {
            if (field === 'DEFA') el.value = 0;
            return;
        }

        if (field === 'FASE') {
            const fase = Math.round(parsedValue);
            el.value = fase;
            updateVal(field, fase);
            return;
        }

        el.value = parsedValue;
        if (field !== 'DEFA') {
            updateVal(field, parsedValue.toFixed(1));
        }
    });

    selectedStudentName = typeof student.NOME === 'string' ? student.NOME : null;
}

/* ============================================
   Student Search
   ============================================ */

async function searchStudent() {
    const name = document.getElementById('studentName').value.trim();
    if (!name) return;

    const searchBtn = document.getElementById('searchBtn');
    searchBtn.innerHTML = '<span class="spinner"></span>';
    searchBtn.disabled = true;

    const chipsEl = document.getElementById('studentChips');
    const infoBar = document.getElementById('studentInfoBar');
    chipsEl.innerHTML = '';
    infoBar.style.display = 'none';

    // Hide results when doing new search
    document.getElementById('resultsSection').classList.remove('visible');

    try {
        const response = await fetch(`/students/${encodeURIComponent(name)}`);
        if (!response.ok) throw new Error('Aluno não encontrado');

        const data = await response.json();
        const historico = Array.isArray(data.historico) ? data.historico : [];
        if (!historico.length) throw new Error('Aluno sem histórico disponível');

        currentHistorico = historico;
        const historicoDesc = sortHistoricoByRecency(historico);

        // Fill form with most recent record
        const registroRecente = { NOME: data.nome, ...historicoDesc[0] };
        fillForm(registroRecente);

        // Show info bar
        infoBar.style.display = 'block';
        infoBar.innerText = `${data.nome} — dados carregados (${historico.length} registro${historico.length > 1 ? 's' : ''}). Ajuste os sliders e clique em "Realizar Previsão".`;

        // Create year/phase chips
        historicoDesc.forEach((registro, idx) => {
            const chip = document.createElement('span');
            chip.className = 'student-chip' + (idx === 0 ? ' active' : '');
            chip.innerText = `${registro.ANO || '?'} (Fase ${registro.FASE || '?'})`;

            chip.onclick = () => {
                chipsEl.querySelectorAll('.student-chip').forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                fillForm({ NOME: data.nome, ...registro });
            };

            chipsEl.appendChild(chip);
        });

        // Show history chart
        document.getElementById('chartEmptyState').style.display = 'none';
        document.getElementById('historyChartContainer').style.display = 'block';
        renderChart('historyChart', historico, null, `Evolução de ${data.nome}`);

    } catch (error) {
        selectedStudentName = null;
        currentHistorico = [];
        infoBar.style.display = 'block';
        infoBar.innerText = `⚠️ ${error.message}`;

        document.getElementById('chartEmptyState').style.display = 'block';
        document.getElementById('historyChartContainer').style.display = 'none';
    } finally {
        searchBtn.innerHTML = 'Buscar';
        searchBtn.disabled = false;
    }
}

/* ============================================
   Prediction
   ============================================ */

async function predict() {
    const fields = ['IAN', 'IDA', 'IEG', 'IAA', 'IPS', 'IPP', 'IPV', 'FASE', 'DEFA'];
    const data = {};

    fields.forEach(field => {
        data[field] = parseFloat(document.getElementById(field).value);
    });
    if (selectedStudentName) {
        data.NOME = selectedStudentName;
    }

    const predictBtn = document.getElementById('predictBtn');
    predictBtn.innerHTML = '<span class="spinner"></span> Processando...';
    predictBtn.disabled = true;

    try {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });

        if (!response.ok) throw new Error('Erro na previsão');

        const result = await response.json();

        // Use historico from API response if available, otherwise fall back to local
        const historico = (Array.isArray(result.historico) && result.historico.length > 0)
            ? result.historico
            : currentHistorico;

        // Show results section
        const resultsSection = document.getElementById('resultsSection');
        resultsSection.classList.add('visible');

        // Render result chart with new evaluation point
        if (historico.length > 0) {
            document.getElementById('resultChartCard').style.display = 'block';
            renderChart('resultChart', historico, data, selectedStudentName ? `Evolução de ${selectedStudentName}` : 'Nova Avaliação');
        }

        // Update metric cards
        displayPredictionResult(result);
        displayRiskAssessment(result);
        displayActionBanner(result);
        displaySuggestedMessages(result);
        displayProbabilities(result.probabilities);

        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

    } catch (error) {
        alert('Erro ao realizar previsão: ' + error.message);
    } finally {
        predictBtn.innerHTML = '🚀 Realizar Previsão';
        predictBtn.disabled = false;
    }
}

/* ============================================
   Result Display Functions
   ============================================ */

function displayPredictionResult(result) {
    document.getElementById('predictionStone').innerText = result.prediction || '--';
}

function displayRiskAssessment(result) {
    // Risk score
    const scoreEl = document.getElementById('riskScoreValue');
    if (result.risk_score !== undefined && result.risk_score !== null) {
        const score = Number(result.risk_score);
        scoreEl.innerText = Number.isFinite(score) ? (score * 100).toFixed(1) + '%' : '--';
    } else {
        scoreEl.innerText = '--';
    }

    // Risk tier
    const tierEl = document.getElementById('riskTierValue');
    if (result.risk_tier) {
        tierEl.innerText = result.risk_tier;
        tierEl.className = 'metric-value';

        const tierMap = {
            'Baixo': 'risk-baixo',
            'Moderado': 'risk-moderado',
            'Alto': 'risk-alto',
            'Crítico': 'risk-critico',
        };
        tierEl.classList.add(tierMap[result.risk_tier] || '');
    } else {
        tierEl.innerText = '--';
    }

    // Action value
    document.getElementById('actionValue').innerText = result.acao_sugerida || '--';
}

function displayActionBanner(result) {
    const banner = document.getElementById('actionBanner');
    if (result.acao_sugerida) {
        banner.style.display = 'flex';
        document.getElementById('actionBannerText').innerText = result.acao_sugerida;
    } else {
        banner.style.display = 'none';
    }
}

function displaySuggestedMessages(result) {
    const cards = document.getElementById('actionCards');
    if (result.suggested_messages) {
        cards.style.display = 'grid';
        document.getElementById('messageFamily').innerText =
            result.suggested_messages.family || 'Nenhuma mensagem disponível';
        document.getElementById('messageProfessor').innerText =
            result.suggested_messages.professor || 'Nenhuma mensagem disponível';
    } else {
        cards.style.display = 'none';
    }
}

function displayProbabilities(probabilities) {
    const probList = document.getElementById('probList');
    probList.innerHTML = '';

    if (!probabilities) return;

    for (const [key, value] of Object.entries(probabilities)) {
        const li = document.createElement('li');
        const pct = (value * 100).toFixed(1);

        li.innerHTML = `
            <span style="color: var(--text-secondary);">${key}</span>
            <div class="prob-bar-wrapper">
                <div class="prob-bar">
                    <div class="prob-bar-fill" style="width: ${pct}%"></div>
                </div>
                <span class="prob-value">${pct}%</span>
            </div>
        `;
        probList.appendChild(li);
    }
}
