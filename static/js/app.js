// Główna aplikacja frontendowa
let currentUserId = null;
let refreshInterval = null;

// Toast notifications
function showToast(message, type = 'info', duration = 10000) {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    const icons = {
        success: '✓',
        error: '✗',
        info: 'ℹ',
        warning: '⚠'
    };
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span class="toast-icon">${icons[type] || icons.info}</span><span>${message}</span>`;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Komunikaty humorystyczne dla trybu jasnego (nietoperz/księżyc)
const lightModeMessages = [
    "Założ okulary przeciwsłoneczne",
    "Słońce świeci jasno!",
    "Czas na kawę w świetle dnia",
    "Włącz tryb dzienny",
    "Światło dzienne aktywowane",
    "Ochrona przed słońcem włączona",
    "Jasny jak słońce",
    "Dzień dobry, światło!",
    "Przygotuj się na blask",
    "Słoneczny tryb aktywny"
];

// Komunikaty humorystyczne dla trybu ciemnego (słońce/okulary)
const darkModeMessages = [
    "Zapal świeczkę, będzie nocny klimat",
    "Noc zapada...",
    "Czas na nocną sesję",
    "Włącz tryb nocny",
    "Ciemność zapada",
    "Nocne marki, łączcie się!",
    "Księżyc świeci jasno",
    "Dobranoc, światło!",
    "Przygotuj się na ciemność",
    "Nocny tryb aktywny"
];

// Inicjalizacja
document.addEventListener('DOMContentLoaded', () => {
    // Inicjalizuj tryb z localStorage
    initTheme();
    
    // Spróbuj odtworzyć istniejącego użytkownika z localStorage,
    // żeby po odświeżeniu strony nie znikała lista zadań.
    const storedUserId = window.localStorage.getItem('scenarzysta_user_id');
    if (storedUserId) {
        currentUserId = storedUserId;
        const userLabel = document.getElementById('current-user-id');
        if (userLabel) {
            userLabel.textContent = currentUserId.substring(0, 8) + '...';
        }
    } else {
        // Jeśli nie ma jeszcze użytkownika – utwórz nowego
        createNewUser();
    }
    setupEventListeners();
    startQueueRefresh();
});

// Inicjalizacja trybu
function initTheme() {
    const savedTheme = localStorage.getItem('theme');
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;
    
    if (savedTheme === 'dark') {
        body.classList.add('dark-mode');
        themeToggle.checked = true;
        updateThemeIcon(true);
    } else {
        body.classList.remove('dark-mode');
        themeToggle.checked = false;
        updateThemeIcon(false);
    }
}

// Aktualizacja ikony w przełączniku
function updateThemeIcon(isDark) {
    const icon = document.querySelector('.theme-toggle-icon');
    if (isDark) {
        // Tryb ciemny - słońce lub okulary
        const darkIcons = ['☀️', '🕶️', '🌞'];
        icon.textContent = darkIcons[Math.floor(Math.random() * darkIcons.length)];
    } else {
        // Tryb jasny - nietoperz lub księżyc
        const lightIcons = ['🦇', '🌙', '🦉'];
        icon.textContent = lightIcons[Math.floor(Math.random() * lightIcons.length)];
    }
}

// Przełączanie trybu
function toggleTheme() {
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;
    const isDark = themeToggle.checked;
    
    if (isDark) {
        body.classList.add('dark-mode');
        localStorage.setItem('theme', 'dark');
        updateThemeIcon(true);
        showThemeMessage(darkModeMessages);
    } else {
        body.classList.remove('dark-mode');
        localStorage.setItem('theme', 'light');
        updateThemeIcon(false);
        showThemeMessage(lightModeMessages);
    }
}

// Wyświetlanie humorystycznego komunikatu
function showThemeMessage(messages) {
    const messageEl = document.getElementById('theme-message');
    const randomMessage = messages[Math.floor(Math.random() * messages.length)];
    
    messageEl.textContent = randomMessage;
    messageEl.classList.add('show');
    
    // Ukryj po 5 sekundach
    setTimeout(() => {
        messageEl.classList.remove('show');
    }, 5000);
}

// Utworzenie nowego użytkownika
async function createNewUser() {
    try {
        const response = await fetch('/api/user/create', {
            method: 'POST'
        });
        const data = await response.json();
        currentUserId = data.user_id;
        // Zapamiętaj użytkownika w localStorage, aby odświeżenie strony nie tworzyło nowego
        window.localStorage.setItem('scenarzysta_user_id', currentUserId);
        document.getElementById('current-user-id').textContent = currentUserId.substring(0, 8) + '...';
    } catch (error) {
        console.error('Błąd podczas tworzenia użytkownika:', error);
        showToast('Nie udało się utworzyć użytkownika', 'error');
    }
}

// Konfiguracja event listenerów
function setupEventListeners() {
    // Przesyłanie pliku
    document.getElementById('upload-form').addEventListener('submit', handleFileUpload);
    
    // Przełącznik trybu
    document.getElementById('theme-toggle').addEventListener('change', toggleTheme);
    
    // Zmiana pliku
    document.getElementById('file-input').addEventListener('change', (e) => {
        const files = e.target.files;
        if (files && files.length > 0) {
            if (files.length === 1) {
                document.querySelector('.file-label-text').textContent = files[0].name;
            } else {
                document.querySelector('.file-label-text').textContent = `Wybrano ${files.length} plików`;
            }
            updateSelectedFiles();
        }
    });
}

// Obsługa przesyłania pliku
async function handleFileUpload(e) {
    e.preventDefault();
    
    const fileInput = document.getElementById('file-input');
    const files = fileInput.files;
    const analyzeImages = document.getElementById('analyze-images').checked;
    const correlateDocuments = document.getElementById('correlate-documents')?.checked || false;
    
    if (!files || files.length === 0) {
        showToast('Wybierz co najmniej jeden plik', 'warning');
        return;
    }
    
    if (!currentUserId) {
        showToast('Brak użytkownika. Tworzenie nowego...', 'info', 3000);
        await createNewUser();
    }
    
    const uploadBtn = document.getElementById('upload-btn');
    uploadBtn.disabled = true;
    uploadBtn.textContent = 'Przesyłanie...';
    
    let successCount = 0;
    let failCount = 0;
    
    try {
        // Prześlij każdy plik osobno
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            uploadBtn.textContent = `Przesyłanie ${i + 1}/${files.length}...`;
            
            const formData = new FormData();
            formData.append('file', file);
            formData.append('user_id', currentUserId);
            formData.append('analyze_images', analyzeImages.toString());
            formData.append('correlate_documents', correlateDocuments.toString());
            
            const response = await fetch('/api/tasks', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                successCount++;
            } else {
                failCount++;
                console.error(`Błąd przesyłania ${file.name}: ${data.error}`);
            }
        }
        
        // Podsumowanie
        const imageInfo = analyzeImages ? ' (z analizą obrazów)' : '';
        const correlateInfo = correlateDocuments ? ' (z korelacją)' : '';
        
        if (failCount === 0) {
            showToast(`Przesłano ${successCount} plik(ów) pomyślnie${imageInfo}${correlateInfo}!`, 'success');
        } else {
            showToast(`Przesłano ${successCount} plik(ów), ${failCount} błędów.`, 'warning');
        }
        
        // Reset formularza
        fileInput.value = '';
        document.querySelector('.file-label-text').textContent = 'Wybierz pliki (docx, pdf, xlsx, txt)';
        document.getElementById('selected-files').innerHTML = '';
        document.getElementById('analyze-images').checked = false;
        if (document.getElementById('correlate-documents')) {
            document.getElementById('correlate-documents').checked = false;
        }
        refreshQueueStatus();
        
    } catch (error) {
        console.error('Błąd podczas przesyłania:', error);
        showToast('Nie udało się przesłać plików', 'error');
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.textContent = 'Prześlij i przetwórz';
    }
}

// Wyświetlanie wybranych plików
function updateSelectedFiles() {
    const fileInput = document.getElementById('file-input');
    const selectedFilesDiv = document.getElementById('selected-files');
    
    if (!fileInput.files || fileInput.files.length === 0) {
        selectedFilesDiv.innerHTML = '';
        return;
    }
    
    let html = '';
    for (const file of fileInput.files) {
        const ext = file.name.split('.').pop().toLowerCase();
        html += `<span class="selected-file"><span class="file-ext">${ext}</span>${file.name}</span>`;
    }
    selectedFilesDiv.innerHTML = html;
}

// Odświeżanie statusu kolejki
async function refreshQueueStatus() {
    if (!currentUserId) return;
    
    try {
        const response = await fetch(`/api/queue/status?user_id=${currentUserId}`);
        const data = await response.json();
        
        updateQueueDisplay(data);
    } catch (error) {
        console.error('Błąd podczas odświeżania kolejki:', error);
    }
}

// Aktualizacja wyświetlania kolejki
function updateQueueDisplay(queueData) {
    // Statystyki
    document.getElementById('pending-count').textContent = queueData.pending_tasks || 0;
    document.getElementById('processing-count').textContent = queueData.processing_tasks || 0;
    
    // Szacowany czas oczekiwania
    const waitTime = queueData.user_wait_time;
    if (waitTime !== null && waitTime !== undefined) {
        document.getElementById('wait-time').textContent = formatTime(waitTime);
    } else {
        document.getElementById('wait-time').textContent = '-';
    }
    
    // Lista zadań - filtruj zakończone (te są w historii)
    const tasksList = document.getElementById('tasks-list');
    
    // Pokaż tylko: pending, processing, stopped (możliwy restart)
    // Zakończone (completed, failed, cancelled) są w historii
    const activeTasks = (queueData.tasks || []).filter(task => 
        ['pending', 'processing', 'stopped'].includes(task.status)
    );
    
    if (activeTasks.length === 0) {
        tasksList.innerHTML = '<p class="no-tasks">Brak aktywnych zadań w kolejce</p>';
        return;
    }
    
    tasksList.innerHTML = activeTasks.map(task => createTaskCard(task)).join('');
    
    // Dodaj event listenery dla przycisków
    activeTasks.forEach(task => {
        if (task.status === 'pending') {
            const cancelBtn = document.getElementById(`cancel-btn-${task.task_id}`);
            if (cancelBtn) {
                cancelBtn.addEventListener('click', () => cancelTask(task.task_id));
            }
        }
        
        if (task.status === 'completed' && task.result_path) {
            const downloadBtn = document.getElementById(`download-btn-${task.task_id}`);
            if (downloadBtn) {
                downloadBtn.addEventListener('click', () => downloadResults(task.task_id));
            }
            
            const artifactsBtn = document.getElementById(`artifacts-btn-${task.task_id}`);
            if (artifactsBtn) {
                artifactsBtn.addEventListener('click', () => showArtifacts(task.task_id));
            }
        }
        
        // Przycisk zatrzymania
        if (task.status === 'processing') {
            const stopBtn = document.getElementById(`stop-btn-${task.task_id}`);
            if (stopBtn) {
                stopBtn.addEventListener('click', () => showStopConfirmation(task.task_id, task.filename));
            }
        }
        
        // Przycisk restartu
        if (task.can_restart) {
            const restartBtn = document.getElementById(`restart-btn-${task.task_id}`);
            if (restartBtn) {
                restartBtn.addEventListener('click', () => restartTask(task.task_id));
            }
            const removeBtn = document.getElementById(`remove-btn-${task.task_id}`);
            if (removeBtn) {
                removeBtn.addEventListener('click', () => removeFromQueue(task.task_id));
            }
        }

        const sourceBtn = document.getElementById(`download-source-btn-${task.task_id}`);
        if (sourceBtn) {
            sourceBtn.addEventListener('click', () => downloadSource(task.task_id));
        }
    });
}

// Tworzenie karty zadania
function createTaskCard(task) {
    const statusClass = task.status.toLowerCase();
    const statusText = {
        'pending': 'Oczekuje',
        'processing': 'Przetwarzanie',
        'completed': 'Zakończone',
        'failed': 'Błąd',
        'cancelled': 'Anulowane',
        'stopped': 'Zatrzymane'
    }[task.status] || task.status;
    
    const progressBar = task.status === 'processing' || task.status === 'completed'
        ? `
            <div class="task-progress">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${task.progress || 0}%"></div>
                </div>
                <div class="progress-text">${Math.round(task.progress || 0)}%</div>
            </div>
        `
        : '';
    
    // Informacja o etapie i czasie
    let timeEstimate = '';
    if (task.status === 'processing') {
        const stageInfo = task.current_stage > 0 ? ` (Etap ${task.current_stage}/${task.total_stages})` : '';
        const etaText = task.estimated_time_remaining !== null && task.estimated_time_remaining !== undefined
            ? formatTime(task.estimated_time_remaining)
            : 'obliczanie...';
        timeEstimate = `
            <div class="time-estimate">
                <strong>Szacowany czas do zakończenia${stageInfo}:</strong> ${etaText}
            </div>
        `;
    } else if (task.estimated_time_remaining !== null && task.estimated_time_remaining !== undefined && task.status === 'pending') {
        timeEstimate = `
            <div class="time-estimate">
                <strong>Szacowany czas:</strong> ${formatTime(task.estimated_time_remaining)}
            </div>
        `;
    }
    
    const positionInfo = task.position_in_queue
        ? `<div class="task-info-item">
            <div class="task-info-label">Pozycja w kolejce</div>
            <div class="task-info-value">#${task.position_in_queue}</div>
        </div>`
        : '';
    
    const errorMessage = task.error_message
        ? `<div class="error-message">Błąd: ${task.error_message}</div>`
        : '';
    
    const actions = [];
    // Przyciski zatrzymania i anulowania
    if (task.status === 'pending') {
        actions.push(`<button class="btn btn-danger" id="cancel-btn-${task.task_id}">Anuluj</button>`);
    }
    if (task.status === 'processing') {
        actions.push(`<button class="btn btn-warning" id="stop-btn-${task.task_id}">Zatrzymaj</button>`);
    }
    // Przycisk restartu dla zatrzymanych/błędnych/anulowanych
    if (task.can_restart) {
        actions.push(`<button class="btn btn-primary" id="restart-btn-${task.task_id}">Uruchom ponownie</button>`);
        actions.push(`<button class="btn btn-danger" id="remove-btn-${task.task_id}">Usuń z kolejki</button>`);
    }
    if (task.status === 'completed' && task.result_path) {
        actions.push(`<button class="btn btn-success" id="download-btn-${task.task_id}">Pobierz Excel</button>`);
        actions.push(`<button class="btn btn-info" id="artifacts-btn-${task.task_id}">Wszystkie artefakty</button>`);
    }
    
    // Checkboxy opcji (zablokowane)
    const optionsInfo = `
        <div class="task-options">
            <label class="option-badge ${task.analyze_images ? 'active' : 'inactive'}">
                <input type="checkbox" ${task.analyze_images ? 'checked' : ''} disabled>
                <span>Analiza obrazów</span>
            </label>
            <label class="option-badge experimental ${task.correlate_documents ? 'active' : 'inactive'}">
                <input type="checkbox" ${task.correlate_documents ? 'checked' : ''} disabled>
                <span>Korelacja dok.</span>
            </label>
        </div>
    `;
    
    return `
        <div class="task-card">
            <div class="task-header">
                <div class="task-title">${task.filename}</div>
                <span class="task-status ${statusClass}">${statusText}</span>
            </div>
            <div class="task-info">
                <div class="task-info-item">
                    <div class="task-info-label">Użytkownik</div>
                    <div class="task-info-value task-id-value" title="${task.user_id || '-'}">${task.user_id ? task.user_id.substring(0, 16) : '-'}</div>
                </div>
                <div class="task-info-item">
                    <div class="task-info-label">ID zadania</div>
                    <div class="task-info-value task-id-value" title="${task.task_id}">${task.task_id.substring(0, 16)}</div>
                </div>
                <div class="task-info-item">
                    <div class="task-info-label">Utworzono</div>
                    <div class="task-info-value">${formatDateTime(task.created_at)}</div>
                </div>
                ${positionInfo}
                ${task.started_at ? `
                    <div class="task-info-item">
                        <div class="task-info-label">Rozpoczęto</div>
                        <div class="task-info-value">${formatDateTime(task.started_at)}</div>
                    </div>
                ` : ''}
                ${task.completed_at ? `
                    <div class="task-info-item">
                        <div class="task-info-label">Zakończono</div>
                        <div class="task-info-value">${formatDateTime(task.completed_at)}</div>
                    </div>
                ` : ''}
                ${task.result_filename ? `
                    <div class="task-info-item">
                        <div class="task-info-label">Plik wynikowy</div>
                        <div class="task-info-value">${task.result_filename}</div>
                    </div>
                ` : ''}
            </div>
            ${optionsInfo}
            ${progressBar}
            ${timeEstimate}
            ${errorMessage}
            ${(() => {
                actions.push(`<button class="btn btn-secondary task-source-btn" id="download-source-btn-${task.task_id}">Pobierz oryginał</button>`);
                return actions.length > 0 ? `<div class="task-actions">${actions.join('')}</div>` : '';
            })()}
        </div>
    `;
}

// Anulowanie zadania
async function cancelTask(taskId) {
    if (!confirm('Czy na pewno chcesz anulować to zadanie?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/tasks/${taskId}/cancel`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('Zadanie anulowane', 'success');
            refreshQueueStatus();
        } else {
            showToast(`Błąd: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Błąd podczas anulowania zadania:', error);
        showToast('Nie udało się anulować zadania', 'error');
    }
}

// Pokazanie modalu potwierdzenia zatrzymania
function showStopConfirmation(taskId, filename) {
    // Usuń poprzedni modal jeśli istnieje
    const existingModal = document.getElementById('stop-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    const modal = document.createElement('div');
    modal.id = 'stop-modal';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Zatrzymaj proces</h3>
                <button class="modal-close" onclick="closeStopModal()">&times;</button>
            </div>
            <div class="modal-body">
                <p>Czy potwierdzasz zatrzymanie operacji?</p>
                <p class="modal-filename"><strong>${filename}</strong></p>
                <p class="modal-warning">Po zatrzymaniu możesz uruchomić zadanie ponownie.</p>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeStopModal()">NIE</button>
                <button class="btn btn-danger" onclick="confirmStopTask('${taskId}')">TAK - Zatrzymaj</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

// Zamknięcie modalu zatrzymania
function closeStopModal() {
    const modal = document.getElementById('stop-modal');
    if (modal) {
        modal.remove();
    }
}

// Potwierdzenie zatrzymania
async function confirmStopTask(taskId) {
    closeStopModal();
    
    try {
        const response = await fetch(`/api/tasks/${taskId}/stop`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showToast('Zadanie zatrzymane. Możesz je uruchomić ponownie.', 'warning');
            refreshQueueStatus();
        } else {
            showToast(`Błąd: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Błąd podczas zatrzymywania zadania:', error);
        showToast('Nie udało się zatrzymać zadania', 'error');
    }
}

// Restart zadania
async function restartTask(taskId) {
    try {
        const response = await fetch(`/api/tasks/${taskId}/restart`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showToast('Zadanie uruchomione ponownie i dodane na koniec kolejki', 'success');
            refreshQueueStatus();
        } else {
            showToast(`Błąd: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Błąd podczas restartowania zadania:', error);
        showToast('Nie udało się uruchomić zadania ponownie', 'error');
    }
}

// Usuwanie z kolejki (przeniesienie do historii jako błąd)
async function removeFromQueue(taskId) {
    try {
        const response = await fetch(`/api/tasks/${taskId}/remove`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showToast('Zadanie usunięte z kolejki i przeniesione do historii', 'success');
            refreshQueueStatus();
            refreshHistory();
        } else {
            showToast(`Błąd: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Błąd podczas usuwania z kolejki:', error);
        showToast('Nie udało się usunąć zadania', 'error');
    }
}

// Pobieranie wyników
function downloadResults(taskId) {
    window.location.href = `/api/tasks/${taskId}/download`;
}

// Pokazanie listy artefaktów
async function showArtifacts(taskId) {
    try {
        const response = await fetch(`/api/tasks/${taskId}/artifacts`);
        const data = await response.json();
        
        if (!response.ok) {
            showToast(`Błąd: ${data.error}`, 'error');
            return;
        }
        
        if (data.artifacts.length === 0) {
            showToast('Brak dostępnych artefaktów dla tego zadania.', 'warning');
            return;
        }
        
        // Stwórz modal z listą artefaktów
        const artifactsList = data.artifacts.map(artifact => {
            const sizeKB = (artifact.size / 1024).toFixed(1);
            return `
                <div class="artifact-item">
                    <div class="artifact-info">
                        <strong>Etap ${artifact.stage}: ${artifact.name}</strong>
                        <span class="artifact-size">(${sizeKB} KB, ${artifact.type.toUpperCase()})</span>
                    </div>
                    <button class="btn btn-success btn-sm" onclick="downloadArtifact('${taskId}', '${artifact.filename}')">
                        Pobierz
                    </button>
                </div>
            `;
        }).join('');
        
        // Usuń poprzedni modal jeśli istnieje
        const existingModal = document.getElementById('artifacts-modal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Stwórz nowy modal
        const modal = document.createElement('div');
        modal.id = 'artifacts-modal';
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Artefakty zadania</h3>
                    <button class="modal-close" onclick="closeArtifactsModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <p>Dostępne pliki z każdego etapu przetwarzania:</p>
                    <div class="artifacts-list">
                        ${artifactsList}
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeArtifactsModal()">Zamknij</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
    } catch (error) {
        console.error('Błąd podczas pobierania artefaktów:', error);
        showToast('Nie udało się pobrać listy artefaktów', 'error');
    }
}

// Pobieranie pojedynczego artefaktu
function downloadArtifact(taskId, filename) {
    window.location.href = `/api/tasks/${taskId}/artifacts/${filename}`;
}

// Zamknięcie modalu artefaktów
function closeArtifactsModal() {
    const modal = document.getElementById('artifacts-modal');
    if (modal) {
        modal.remove();
    }
}

// Formatowanie czasu
function formatTime(seconds) {
    if (seconds === null || seconds === undefined) return '-';
    
    if (seconds < 60) {
        return `${Math.round(seconds)}s`;
    } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        const secs = Math.round(seconds % 60);
        return `${minutes}m ${secs}s`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    }
}

// Formatowanie daty i czasu
function formatDateTime(isoString) {
    if (!isoString) return '-';
    const date = new Date(isoString);
    return date.toLocaleString('pl-PL', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Rozpoczęcie automatycznego odświeżania
function startQueueRefresh() {
    refreshQueueStatus(); // Odśwież od razu
    refreshInterval = setInterval(refreshQueueStatus, 2000); // Co 2 sekundy
}

// Zatrzymanie automatycznego odświeżania (gdy strona jest ukryta)
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        if (refreshInterval) {
            clearInterval(refreshInterval);
            refreshInterval = null;
        }
    } else {
        if (!refreshInterval) {
            startQueueRefresh();
        }
    }
});

// ==================== HISTORIA ZADAŃ ====================

// Pobieranie historii zadań
async function refreshHistory() {
    try {
        const response = await fetch('/api/history?limit=50');
        const data = await response.json();
        
        if (!response.ok) {
            console.error('Błąd pobierania historii:', data.error);
            return;
        }
        
        // Aktualizuj statystyki
        document.getElementById('history-total').textContent = data.statistics.total_tasks;
        document.getElementById('history-completed').textContent = data.statistics.completed;
        document.getElementById('history-failed').textContent = data.statistics.failed;
        
        // Aktualizuj listę
        const historyList = document.getElementById('history-list');
        
        if (data.entries.length === 0) {
            historyList.innerHTML = '<p class="no-history">Brak przetworzonych plików</p>';
            return;
        }
        
        historyList.innerHTML = data.entries.map(entry => createHistoryCard(entry)).join('');
        
        // Dodaj event listenery dla przycisków
        data.entries.forEach(entry => {
            // Przycisk pobierania Excel
            const excelArtifact = entry.artifacts ? entry.artifacts.find(a => a.type === 'xlsx') : null;
            if (excelArtifact) {
                const excelBtn = document.getElementById(`history-excel-btn-${entry.task_id}`);
                if (excelBtn) {
                    excelBtn.addEventListener('click', () => downloadHistoryArtifact(entry.task_id, excelArtifact.filename));
                }
            }
            
            // Przycisk pobrania źródła
            if (entry.has_source) {
                const sourceBtn = document.getElementById(`history-source-btn-${entry.task_id}`);
                if (sourceBtn) {
                    sourceBtn.addEventListener('click', () => downloadHistorySource(entry.task_id));
                }
            }
            
            // Przycisk artefaktów
            if (entry.artifacts && entry.artifacts.length > 0) {
                const artifactsBtn = document.getElementById(`history-artifacts-btn-${entry.task_id}`);
                if (artifactsBtn) {
                    artifactsBtn.addEventListener('click', () => showHistoryArtifacts(entry.task_id, entry.artifacts));
                }
            }
        });
        
    } catch (error) {
        console.error('Błąd podczas pobierania historii:', error);
    }
}

// Tworzenie karty historii
function createHistoryCard(entry) {
    const statusClass = entry.status === 'completed' ? 'completed' : 'failed';
    const statusText = entry.status === 'completed' ? 'Ukończone' : 'Błąd';
    
    const errorMessage = entry.error_message
        ? `<div class="error-message">Błąd: ${entry.error_message}</div>`
        : '';
    
    const artifactsCount = entry.artifacts ? entry.artifacts.length : 0;
    const totalSize = entry.artifacts 
        ? entry.artifacts.reduce((sum, a) => sum + (a.size || 0), 0)
        : 0;
    const sizeKB = (totalSize / 1024).toFixed(1);
    
    // Znajdź plik Excel w artefaktach
    const excelArtifact = entry.artifacts ? entry.artifacts.find(a => a.type === 'xlsx') : null;
    
    const actions = [];
    // Przycisk pobierania Excel (jeśli jest)
    if (excelArtifact) {
        actions.push(`<button class="btn btn-success btn-sm" id="history-excel-btn-${entry.task_id}">Pobierz Excel</button>`);
    }
    if (entry.has_source) {
        actions.push(`<button class="btn btn-secondary btn-sm" id="history-source-btn-${entry.task_id}">Źródło</button>`);
    }
    if (artifactsCount > 0) {
        actions.push(`<button class="btn btn-info btn-sm" id="history-artifacts-btn-${entry.task_id}">Artefakty (${artifactsCount})</button>`);
    }
    
    // Checkboxy opcji (zablokowane)
    const optionsInfo = `
        <div class="task-options history-options">
            <label class="option-badge ${entry.analyze_images ? 'active' : 'inactive'}">
                <input type="checkbox" ${entry.analyze_images ? 'checked' : ''} disabled>
                <span>Analiza obrazów</span>
            </label>
            <label class="option-badge experimental ${entry.correlate_documents ? 'active' : 'inactive'}">
                <input type="checkbox" ${entry.correlate_documents ? 'checked' : ''} disabled>
                <span>Korelacja dok.</span>
            </label>
        </div>
    `;
    
    return `
        <div class="history-card">
            <div class="history-header">
                <div class="history-title">${entry.filename}</div>
                <span class="task-status ${statusClass}">${statusText}</span>
            </div>
            <div class="history-info">
                <div class="history-info-item">
                    <span class="history-label">Użytkownik:</span>
                    <span class="history-value task-id-value" title="${entry.user_id || '-'}">${entry.user_id || '-'}</span>
                </div>
                <div class="history-info-item">
                    <span class="history-label">ID zadania:</span>
                    <span class="history-value task-id-value" title="${entry.task_id}">${entry.task_id.substring(0, 16)}</span>
                </div>
                <div class="history-info-item">
                    <span class="history-label">Zakończono:</span>
                    <span class="history-value">${formatDateTime(entry.completed_at)}</span>
                </div>
                <div class="history-info-item">
                    <span class="history-label">Wygasa:</span>
                    <span class="history-value">${formatDateTime(entry.expires_at)}</span>
                </div>
                <div class="history-info-item">
                    <span class="history-label">Rozmiar:</span>
                    <span class="history-value">${sizeKB} KB</span>
                </div>
            </div>
            ${optionsInfo}
            ${errorMessage}
            ${actions.length > 0 ? `<div class="history-actions">${actions.join('')}</div>` : ''}
        </div>
    `;
}

// Pobieranie pliku źródłowego z historii
function downloadHistorySource(taskId) {
    window.location.href = `/api/history/${taskId}/source`;
}

// Pokazanie artefaktów z historii
function showHistoryArtifacts(taskId, artifacts) {
    const artifactsList = artifacts.map(artifact => {
        const sizeKB = (artifact.size / 1024).toFixed(1);
        return `
            <div class="artifact-item">
                <div class="artifact-info">
                    <strong>Etap ${artifact.stage}: ${artifact.name}</strong>
                    <span class="artifact-size">(${sizeKB} KB, ${artifact.type.toUpperCase()})</span>
                </div>
                <button class="btn btn-success btn-sm" onclick="downloadHistoryArtifact('${taskId}', '${artifact.filename}')">
                    Pobierz
                </button>
            </div>
        `;
    }).join('');
    
    // Usuń poprzedni modal jeśli istnieje
    const existingModal = document.getElementById('artifacts-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Stwórz nowy modal
    const modal = document.createElement('div');
    modal.id = 'artifacts-modal';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Artefakty zadania</h3>
                <button class="modal-close" onclick="closeArtifactsModal()">&times;</button>
            </div>
            <div class="modal-body">
                <p>Dostępne pliki z każdego etapu przetwarzania:</p>
                <div class="artifacts-list">
                    ${artifactsList}
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeArtifactsModal()">Zamknij</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

// Pobieranie artefaktu z historii
function downloadHistoryArtifact(taskId, filename) {
    window.location.href = `/api/history/${taskId}/artifacts/${filename}`;
}

// Odświeżanie historii co 30 sekund
let historyRefreshInterval = null;

function startHistoryRefresh() {
    refreshHistory(); // Odśwież od razu
    historyRefreshInterval = setInterval(refreshHistory, 30000); // Co 30 sekund
}

// Inicjalizacja historii przy starcie
document.addEventListener('DOMContentLoaded', () => {
    startHistoryRefresh();
});
