// Główna logika aplikacji frontendowej

const API_BASE = '';

// Sprawdź status Ollama przy starcie
document.addEventListener('DOMContentLoaded', () => {
    checkOllamaStatus();
    
    // Obsługa wyboru pliku
    const fileInput = document.getElementById('file-input');
    const fileName = document.getElementById('file-name');
    const submitBtn = document.getElementById('submit-btn');
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            fileName.textContent = e.target.files[0].name;
            submitBtn.disabled = false;
        } else {
            fileName.textContent = 'Nie wybrano pliku';
            submitBtn.disabled = true;
        }
    });
    
    // Obsługa formularza
    const uploadForm = document.getElementById('upload-form');
    uploadForm.addEventListener('submit', handleFormSubmit);
});

// Sprawdź status Ollama
async function checkOllamaStatus() {
    const statusCard = document.getElementById('ollama-status');
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    
    try {
        const response = await fetch(`${API_BASE}/api/check-ollama`);
        const data = await response.json();
        
        if (data.connected) {
            statusIndicator.className = 'status-indicator connected';
            statusText.textContent = `Połączono z Ollama (Model: ${data.configured_model || 'N/A'})`;
        } else {
            statusIndicator.className = 'status-indicator disconnected';
            statusText.textContent = `Brak połączenia z Ollama. Upewnij się, że Ollama jest uruchomione.`;
        }
    } catch (error) {
        statusIndicator.className = 'status-indicator disconnected';
        statusText.textContent = `Błąd połączenia: ${error.message}`;
    }
}

// Obsługa przesyłania formularza
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const fileInput = document.getElementById('file-input');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoader = submitBtn.querySelector('.btn-loader');
    
    // Ukryj sekcje
    document.getElementById('results-section').style.display = 'none';
    document.getElementById('error-section').style.display = 'none';
    
    // Pokaż postęp
    document.getElementById('progress-section').style.display = 'block';
    updateProgress(0, 'Rozpoczynanie przetwarzania...');
    
    // Wyłącz przycisk
    submitBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline';
    
    try {
        const response = await fetch(`${API_BASE}/api/process-document`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Błąd przetwarzania');
        }
        
        const result = await response.json();
        
        // Sprawdzaj status zadania
        if (result.task_id) {
            pollTaskStatus(result.task_id);
        } else {
            // Bezpośredni wynik
            showResults(result);
        }
        
    } catch (error) {
        showError(error.message);
        submitBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
}

// Polling statusu zadania
async function pollTaskStatus(taskId) {
    const maxAttempts = 300; // 5 minut (1 sekunda * 300)
    let attempts = 0;
    
    const poll = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/task-status/${taskId}`);
            const status = await response.json();
            
            if (status.status === 'completed') {
                updateProgress(100, 'Przetwarzanie zakończone!');
                setTimeout(() => {
                    showResults(status);
                }, 1000);
                return;
            } else if (status.status === 'error') {
                throw new Error(status.error || 'Błąd przetwarzania');
            } else {
                updateProgress(status.progress || 0, status.message || 'Przetwarzanie...');
                attempts++;
                
                if (attempts < maxAttempts) {
                    setTimeout(poll, 1000);
                } else {
                    throw new Error('Przekroczono limit czasu oczekiwania');
                }
            }
        } catch (error) {
            showError(error.message);
        }
    };
    
    poll();
}

// Aktualizuj pasek postępu
function updateProgress(percent, message) {
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const progressMessage = document.getElementById('progress-message');
    
    progressBar.style.width = `${percent}%`;
    progressText.textContent = `${percent}%`;
    progressMessage.textContent = message;
}

// Pokaż wyniki
function showResults(result) {
    const resultsSection = document.getElementById('results-section');
    const statsDiv = document.getElementById('results-stats');
    const downloadBtn = document.getElementById('download-btn');
    const viewResultsBtn = document.getElementById('view-results-btn');
    const previewDiv = document.getElementById('test-cases-preview');
    
    // Ukryj postęp
    document.getElementById('progress-section').style.display = 'none';
    
    // Pokaż wyniki
    resultsSection.style.display = 'block';
    
    // Statystyki
    const stats = result.statistics || {};
    statsDiv.innerHTML = `
        <div class="stat-item">
            <div class="stat-value">${stats.text_chunks || 0}</div>
            <div class="stat-label">Fragmenty Tekstu</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">${stats.images || 0}</div>
            <div class="stat-label">Obrazy</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">${stats.batches || 0}</div>
            <div class="stat-label">Partie</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">${stats.test_cases || 0}</div>
            <div class="stat-label">Scenariusze Testowe</div>
        </div>
    `;
    
    // Przycisk pobierania
    if (result.excel_path) {
        const filename = result.excel_path.split('/').pop();
        downloadBtn.onclick = () => {
            window.location.href = `${API_BASE}/api/download/${filename}`;
        };
    }
    
    // Podgląd scenariuszy
    viewResultsBtn.onclick = () => {
        if (previewDiv.style.display === 'none') {
            previewDiv.style.display = 'block';
            const testCases = result.test_cases || [];
            previewDiv.innerHTML = testCases.map((tc, idx) => `
                <div class="test-case-item">
                    <h4>${idx + 1}. ${tc.scenario_name || 'Scenariusz testowy'}</h4>
                    <p><strong>ID:</strong> ${tc.test_case_id || 'N/A'}</p>
                    <p><strong>Krok:</strong> ${tc.step_action || 'N/A'}</p>
                    <p><strong>Wymaganie:</strong> ${tc.requirement || 'N/A'}</p>
                    <p><strong>Rezultat:</strong> ${tc.expected_result || 'N/A'}</p>
                </div>
            `).join('');
        } else {
            previewDiv.style.display = 'none';
        }
    };
    
    // Przywróć przycisk submit
    const submitBtn = document.getElementById('submit-btn');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoader = submitBtn.querySelector('.btn-loader');
    submitBtn.disabled = false;
    btnText.style.display = 'inline';
    btnLoader.style.display = 'none';
}

// Pokaż błąd
function showError(message) {
    const errorSection = document.getElementById('error-section');
    const errorCard = document.getElementById('error-card');
    
    errorCard.textContent = message;
    errorSection.style.display = 'block';
    
    // Ukryj postęp
    document.getElementById('progress-section').style.display = 'none';
}
