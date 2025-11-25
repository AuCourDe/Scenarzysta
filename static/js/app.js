// Główna aplikacja frontendowa
let currentUserId = null;
let refreshInterval = null;

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
    
    // Ukryj po 3-5 sekundach
    const duration = 3000 + Math.random() * 2000; // 3-5 sekund
    setTimeout(() => {
        messageEl.classList.remove('show');
    }, duration);
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
        alert('Nie udało się utworzyć użytkownika');
    }
}

// Konfiguracja event listenerów
function setupEventListeners() {
    // Przesyłanie pliku
    document.getElementById('upload-form').addEventListener('submit', handleFileUpload);
    
    // Nowy użytkownik
    document.getElementById('new-user-btn').addEventListener('click', createNewUser);
    
    // Przełącznik trybu
    document.getElementById('theme-toggle').addEventListener('change', toggleTheme);
    
    // Zmiana pliku
    document.getElementById('file-input').addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            document.querySelector('.file-label-text').textContent = file.name;
        }
    });
}

// Obsługa przesyłania pliku
async function handleFileUpload(e) {
    e.preventDefault();
    
    const fileInput = document.getElementById('file-input');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Wybierz plik');
        return;
    }
    
    if (!currentUserId) {
        alert('Brak użytkownika. Tworzenie nowego...');
        await createNewUser();
    }
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', currentUserId);
    
    const uploadBtn = document.getElementById('upload-btn');
    uploadBtn.disabled = true;
    uploadBtn.textContent = 'Przesyłanie...';
    
    try {
        const response = await fetch('/api/tasks', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert(`Dokument przesłany pomyślnie! ID zadania: ${data.task_id}`);
            fileInput.value = '';
            document.querySelector('.file-label-text').textContent = 'Wybierz plik .docx';
            refreshQueueStatus();
        } else {
            alert(`Błąd: ${data.error}`);
        }
    } catch (error) {
        console.error('Błąd podczas przesyłania:', error);
        alert('Nie udało się przesłać pliku');
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.textContent = 'Prześlij i przetwórz';
    }
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
    
    // Lista zadań
    const tasksList = document.getElementById('tasks-list');
    
    if (!queueData.tasks || queueData.tasks.length === 0) {
        tasksList.innerHTML = '<p class="no-tasks">Brak zadań w kolejce</p>';
        return;
    }
    
    tasksList.innerHTML = queueData.tasks.map(task => createTaskCard(task)).join('');
    
    // Dodaj event listenery dla przycisków
    queueData.tasks.forEach(task => {
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
        'cancelled': 'Anulowane'
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
    
    const timeEstimate = task.estimated_time_remaining !== null && task.estimated_time_remaining !== undefined
        ? `
            <div class="time-estimate">
                <strong>Szacowany czas do zakończenia:</strong> ${formatTime(task.estimated_time_remaining)}
            </div>
        `
        : '';
    
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
    if (task.status === 'pending') {
        actions.push(`<button class="btn btn-danger" id="cancel-btn-${task.task_id}">Anuluj</button>`);
    }
    if (task.status === 'completed' && task.result_path) {
        actions.push(`<button class="btn btn-success" id="download-btn-${task.task_id}">Pobierz wyniki</button>`);
    }
    
    return `
        <div class="task-card">
            <div class="task-header">
                <div class="task-title">${task.filename}</div>
                <span class="task-status ${statusClass}">${statusText}</span>
            </div>
            <div class="task-info">
                <div class="task-info-item">
                    <div class="task-info-label">Użytkownik</div>
                    <div class="task-info-value">${task.user_id ? task.user_id.substring(0, 8) + '...' : '-'}</div>
                </div>
                <div class="task-info-item">
                    <div class="task-info-label">ID zadania</div>
                    <div class="task-info-value">${task.task_id.substring(0, 8)}...</div>
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
            alert('Zadanie anulowane');
            refreshQueueStatus();
        } else {
            alert(`Błąd: ${data.error}`);
        }
    } catch (error) {
        console.error('Błąd podczas anulowania zadania:', error);
        alert('Nie udało się anulować zadania');
    }
}

// Pobieranie wyników
function downloadResults(taskId) {
    window.location.href = `/api/tasks/${taskId}/download`;
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
