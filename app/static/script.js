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

/* ============================================
   Student Search Functions
   ============================================ */

/**
 * Searches for students by name and displays their historical data
 * Makes an API call to /students/{name} endpoint
 */
async function searchStudent() {
    const name = document.getElementById('studentName').value;
    const list = document.getElementById('studentList');
    list.style.display = 'none';
    list.innerHTML = '';

    if (!name) return;

    try {
        const response = await fetch(`/students/${encodeURIComponent(name)}`);
        if (!response.ok) throw new Error('Aluno não encontrado');

        const data = await response.json(); // data contains {nome: "...", historico: [...]}

        list.style.display = 'block';

        // Iterate through the student's historical records
        data.historico.forEach(registro => {
            const li = document.createElement('li');
            li.className = 'student-item';
            // Display year and phase clearly
            li.innerText = `${data.nome} - Ano: ${registro.ANO} (Fase: ${registro.FASE})`;

            // On click, fill the form with this specific year's data
            li.onclick = () => {
                const studentToFill = { NOME: data.nome, ...registro };
                fillForm(studentToFill);
            };
            list.appendChild(li);
        });
    } catch (error) {
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
        if (student[field] !== undefined) {
            const el = document.getElementById(field);
            el.value = student[field];
            // Update slider display values (except for DEFA which is a number input)
            if (field !== 'DEFA') {
                updateVal(field, student[field]);
            }
        }
    });

    // Hide the student list after selection
    document.getElementById('studentList').style.display = 'none';
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
    if (result.risk_score !== undefined) {
        document.getElementById('riskScore').innerText = result.risk_score.toFixed(3);
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
