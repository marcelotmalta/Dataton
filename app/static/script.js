/* ============================================
   STUDENT PERFORMANCE PREDICTION - MAIN SCRIPT
   ============================================ */

/* ============================================
   Utility Functions
   ============================================ */

/**
 * Updates the displayed value for a slider input
 * @param {string} id - The ID of the slider element
 * @param {string|number} val - The current value to display
 */
function updateVal(id, val) {
    document.getElementById('val_' + id).innerText = val;
}

let selectedStudentName = null;

/**
 * Converts value to number when possible
 * @param {any} value
 * @returns {number|null}
 */
function toFiniteNumber(value) {
    const num = Number(value);
    return Number.isFinite(num) ? num : null;
}

/**
 * Updates helper text with currently loaded student
 * @param {Object|null} student
 * @param {boolean} autoLoaded
 */
function updateLoadedStudentInfo(student, autoLoaded = false) {
    const infoEl = document.getElementById('loadedStudentInfo');
    if (!infoEl) return;

    if (!student) {
        infoEl.innerText = 'Nenhum aluno carregado no simulador.';
        return;
    }

    const nome = student.NOME || 'Aluno';
    const ano = toFiniteNumber(student.ANO);
    const fase = toFiniteNumber(student.FASE);

    const anoFase = [];
    if (ano !== null) anoFase.push(`Ano ${ano}`);
    if (fase !== null) anoFase.push(`Fase ${Math.round(fase)}`);

    const origem = autoLoaded ? 'preenchidos automaticamente' : 'carregados';
    const sufixoAnoFase = anoFase.length ? ` (${anoFase.join(', ')})` : '';

    infoEl.innerText =
        `${nome}: dados ${origem}${sufixoAnoFase}. ` +
        'Você pode ajustar os valores no simulador antes de prever.';
}

/**
 * Sorts student history by recency (ANO desc, FASE desc)
 * @param {Array<Object>} historico
 * @returns {Array<Object>}
 */
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

/**
 * Marks one history item as selected in the student list
 * @param {HTMLElement} selectedItem
 * @param {HTMLElement} list
 */
function selectHistoryItem(selectedItem, list) {
    list.querySelectorAll('.student-item.selected').forEach(item => {
        item.classList.remove('selected');
    });
    selectedItem.classList.add('selected');
}

/* ============================================
   Student Search Functions
   ============================================ */

/**
 * Searches for students by name and displays their historical data
 * Makes an API call to /students/{name} endpoint
 */
async function searchStudent() {
    const name = document.getElementById('studentName').value.trim();
    const list = document.getElementById('studentList');
    list.style.display = 'none';
    list.innerHTML = '';

    if (!name) return;

    try {
        const response = await fetch(`/students/${encodeURIComponent(name)}`);
        if (!response.ok) throw new Error('Aluno não encontrado');

        const data = await response.json(); // data contains {nome: "...", historico: [...]}
        const historico = Array.isArray(data.historico) ? data.historico : [];
        if (!historico.length) throw new Error('Aluno sem histórico disponível');
        const historicoOrdenado = sortHistoricoByRecency(historico);

        list.style.display = 'block';

        // Preencher automaticamente com o registro mais recente
        const registroMaisRecente = { NOME: data.nome, ...historicoOrdenado[0] };
        fillForm(registroMaisRecente);
        updateLoadedStudentInfo(registroMaisRecente, true);

        // Exibir histórico para permitir troca de ano/fase mantendo edição livre dos campos
        historicoOrdenado.forEach((registro, idx) => {
            const li = document.createElement('li');
            li.className = 'student-item';
            li.innerText = `${data.nome} - Ano: ${registro.ANO} (Fase: ${registro.FASE})`;

            li.onclick = () => {
                const studentToFill = { NOME: data.nome, ...registro };
                selectHistoryItem(li, list);
                fillForm(studentToFill);
                updateLoadedStudentInfo(studentToFill, false);
            };

            if (idx === 0) {
                li.classList.add('selected');
            }

            list.appendChild(li);
        });
    } catch (error) {
        selectedStudentName = null;
        updateLoadedStudentInfo(null);
        alert(error.message);
    }
}

/**
 * Fills the prediction form with student data
 * @param {Object} student - Student data object with uppercase keys from API
 */
function fillForm(student) {
    const fields = ['IAN', 'IDA', 'IEG', 'IAA', 'IPS', 'IPP', 'IPV', 'FASE', 'DEFA'];

    fields.forEach(field => {
        const el = document.getElementById(field);
        if (!el) return;

        const parsedValue = toFiniteNumber(student[field]);
        if (parsedValue === null) {
            if (field === 'DEFA') {
                el.value = 0;
            }
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
   Prediction Functions
   ============================================ */

/**
 * Submits prediction request to the API and displays results
 * Collects all form data and sends POST request to /predict endpoint
 */
async function predict() {
    const fields = ['IAN', 'IDA', 'IEG', 'IAA', 'IPS', 'IPP', 'IPV', 'FASE', 'DEFA'];
    const data = {};

    // Collect all form field values
    fields.forEach(field => {
        data[field] = parseFloat(document.getElementById(field).value);
    });
    if (selectedStudentName) {
        data.NOME = selectedStudentName;
    }

    try {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });

        if (!response.ok) throw new Error('Erro na previsão');

        const result = await response.json();

        // Display results section
        document.getElementById('result').style.display = 'block';

        // Display prediction
        document.getElementById('predictionBadge').innerText = result.prediction;
        document.getElementById('actionText').innerText = result.acao_sugerida || '--';

        // Display risk assessment
        displayRiskAssessment(result);

        // Display suggested messages
        displaySuggestedMessages(result);

        // Display probabilities
        displayProbabilities(result.probabilities);

        // Scroll to result section
        document.getElementById('result').scrollIntoView({ behavior: 'smooth' });

    } catch (error) {
        alert('Erro ao realizar previsão: ' + error.message);
    }
}

/**
 * Displays risk assessment information
 * @param {Object} result - API response object
 */
function displayRiskAssessment(result) {
    // Display risk score
    if (result.risk_score !== undefined && result.risk_score !== null) {
        const score = Number(result.risk_score);
        document.getElementById('riskScore').innerText =
            Number.isFinite(score) ? score.toFixed(3) : '--';
    } else {
        document.getElementById('riskScore').innerText = '--';
    }

    // Display risk tier with color coding
    if (result.risk_tier) {
        const riskTierElement = document.getElementById('riskTier');
        riskTierElement.innerText = result.risk_tier;

        // Color code based on risk tier
        const riskColors = {
            'Baixo': '#4caf50',
            'Médio': '#ff9800',
            'Moderado': '#ff9800',
            'Alto': '#f44336',
            'Crítico': '#d32f2f'
        };
        riskTierElement.style.color = riskColors[result.risk_tier] || '#333';
    } else {
        document.getElementById('riskTier').innerText = '--';
    }
}

/**
 * Displays suggested messages for family and professor
 * @param {Object} result - API response object
 */
function displaySuggestedMessages(result) {
    if (result.suggested_messages) {
        document.getElementById('messageFamily').innerText =
            result.suggested_messages.family || 'Nenhuma mensagem disponível';
        document.getElementById('messageProfessor').innerText =
            result.suggested_messages.professor || 'Nenhuma mensagem disponível';
    } else {
        document.getElementById('messageFamily').innerText = '--';
        document.getElementById('messageProfessor').innerText = '--';
    }
}

/**
 * Displays prediction probabilities as a list
 * @param {Object} probabilities - Object containing class probabilities
 */
function displayProbabilities(probabilities) {
    const probList = document.getElementById('probList');
    probList.innerHTML = '';

    for (const [key, value] of Object.entries(probabilities)) {
        const li = document.createElement('li');
        li.innerText = `${key}: ${(value * 100).toFixed(1)}%`;
        probList.appendChild(li);
    }
}
