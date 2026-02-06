const API_URL = "http://127.0.0.1:8000/predict";

const form = document.getElementById('studentForm');
const welcomeMessage = document.getElementById('welcomeMessage');
const loading = document.getElementById('loading');
const results = document.getElementById('results');
const suggestionsList = document.getElementById('suggestionsList');

const pedraStyles = {
    "Quartzo": { color: "#ef4444", icon: "🛑" },
    "Ágata": { color: "#f97316", icon: "⚠️" },
    "Ametista": { color: "#a855f7", icon: "🔮" },
    "Topázio": { color: "#3b82f6", icon: "💎" }
};

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // UI State
    welcomeMessage.classList.add('hidden');
    results.classList.add('hidden');
    loading.classList.remove('hidden');
    
    // Coletar dados
    const payload = {
        IAN: parseFloat(document.getElementById('ian').value),
        IDA: parseFloat(document.getElementById('ida').value),
        IEG: parseFloat(document.getElementById('ieg').value),
        IAA: parseFloat(document.getElementById('iaa').value),
        IPS: parseFloat(document.getElementById('ips').value),
        IPP: parseFloat(document.getElementById('ipp').value),
        IPV: parseFloat(document.getElementById('ipv').value),
        FASE: parseFloat(document.getElementById('fase').value),
        DEFA: parseFloat(document.getElementById('defa').value)
    };

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error('Erro na API');

        const data = await response.json();
        renderResults(data);
        
    } catch (error) {
        alert("Erro ao conectar com o servidor: " + error.message);
        console.error(error);
    } finally {
        loading.classList.add('hidden');
    }
});

function renderResults(data) {
    results.classList.remove('hidden');
    
    const pedra = data.pedra_conceito || "Desconhecido";
    const style = pedraStyles[pedra] || { color: "gray", icon: "❓" };
    
    // Atualizar Card
    const card = document.getElementById('pedraCard');
    const icon = document.getElementById('pedraIcon');
    const name = document.getElementById('pedraNome');
    const conf = document.getElementById('pedraConfianca');
    
    card.style.borderTop = `8px solid ${style.color}`;
    icon.textContent = style.icon;
    name.textContent = pedra;
    name.style.color = style.color;
    conf.textContent = `Confiança: ${(data.confidence * 100).toFixed(1)}%`;
    
    // Sugestões
    suggestionsList.innerHTML = '';
    if (data.sugestoes_pedagogicas && data.sugestoes_pedagogicas.length > 0) {
        data.sugestoes_pedagogicas.forEach(item => {
            const div = document.createElement('div');
            div.className = 'suggestion-item';
            div.innerHTML = `<strong>${item.perfil}</strong> ${item.acao}`;
            suggestionsList.appendChild(div);
        });
    } else {
        suggestionsList.innerHTML = '<p>Nenhuma intervenção crítica identificada.</p>';
    }
}
