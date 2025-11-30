// Główna aplikacja frontendowa
let currentUserId = null;
let refreshInterval = null;
let isAdmin = false; // v0.6: stan logowania administratora
let adminSettingsMeta = null; // meta (domyślne wartości, zakresy) do panelu ustawień

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

// ===== ADMIN v0.6: logowanie i panel ustawień =====

function closeAdminModal() {
    const modal = document.getElementById('admin-modal');
    if (modal) {
        modal.remove();
    }
}

function showAdminLoginModal() {
    closeAdminModal();
    const modal = document.createElement('div');
    modal.id = 'admin-modal';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Logowanie administratora</h3>
                <button class="modal-close" onclick="closeAdminModal()">&times;</button>
            </div>
            <div class="modal-body">
                <p>Podaj dane logowania administratora, aby uzyskać dostęp do zaawansowanych ustawień.</p>
                <div class="form-group">
                    <label for="admin-username">Login:</label>
                    <input id="admin-username" type="text" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #ccc;">
                </div>
                <div class="form-group">
                    <label for="admin-password">Hasło:</label>
                    <input id="admin-password" type="password" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #ccc;">
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeAdminModal()">Anuluj</button>
                <button class="btn btn-primary" id="admin-login-confirm-btn">Zaloguj</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    const confirmBtn = document.getElementById('admin-login-confirm-btn');
    confirmBtn.addEventListener('click', async () => {
        const username = document.getElementById('admin-username').value;
        const password = document.getElementById('admin-password').value;
        try {
            const response = await fetch('/api/admin/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await response.json();
            if (response.ok && data.success) {
                isAdmin = true;
                window.localStorage.setItem('scenarzysta_is_admin', 'true');
                updateAdminUI();
                closeAdminModal();
                showToast('Zalogowano jako administrator', 'success');
            } else {
                showToast(data.error || 'Nieprawidłowe dane logowania', 'error');
            }
        } catch (err) {
            console.error('Błąd logowania admina:', err);
            showToast('Nie udało się zalogować jako admin', 'error');
        }
    });
}

async function handleAdminLogout() {
    try {
        await fetch('/api/admin/logout', { method: 'POST' });
    } catch (err) {
        console.error('Błąd wylogowania admina:', err);
    }
    isAdmin = false;
    window.localStorage.removeItem('scenarzysta_is_admin');
    updateAdminUI();
    showToast('Wylogowano administratora', 'info');
}

function buildSettingsField(id, label, description, min, max, value) {
    return `
        <div class="form-group">
            <label for="${id}">${label}</label>
            <input id="${id}" type="number" step="any" value="${value}" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #ccc;">
            <p class="hint">${description} Zakres: ${min} – ${max}.</p>
        </div>
    `;
}

function buildPromptField(id, label, description, value) {
    return `
        <div class="form-group">
            <label for="${id}">${label}</label>
            <p class="hint">${description}</p>
            <textarea id="${id}" rows="12" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #ccc;">${value || ''}</textarea>
        </div>
    `;
}

async function showAdminSettingsModal() {
    if (!isAdmin) {
        showToast('Zaloguj się jako admin, aby otworzyć ustawienia', 'warning');
        return;
    }
    try {
        const response = await fetch('/api/admin/settings');
        const data = await response.json();
        if (!response.ok) {
            showToast(data.error || 'Błąd pobierania ustawień', 'error');
            return;
        }
        adminSettingsMeta = {
            defaults: data.defaults || {},
            ranges: data.ranges || {},
            promptDefaults: data.prompt_defaults || {}
        };
        const s = data.settings || {};
        const p = data.prompts || {};
        closeAdminModal();
        const modal = document.createElement('div');
        modal.id = 'admin-modal';
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content admin-settings-modal">
                <div class="modal-header">
                    <h3>Ustawienia systemu (admin)</h3>
                    <button class="modal-close" onclick="closeAdminModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <p>Zmiany parametrów modelu i promptów obowiązują dopiero po użyciu opcji <strong>Restartuj system</strong>.</p>
                    <h4>Parametry modelu Ollama</h4>
                    ${buildSettingsField('setting-temperature', 'Temperatura', 'Kontroluje kreatywność odpowiedzi (niższa = bardziej zachowawcza, wyższa = bardziej kreatywna).', adminSettingsMeta.ranges.temperature.min, adminSettingsMeta.ranges.temperature.max, s.temperature)}
                    ${buildSettingsField('setting-top-p', 'Top P', 'Filtr próbkowania nucleus – zakres prawdopodobieństwa rozważanych tokenów.', adminSettingsMeta.ranges.top_p.min, adminSettingsMeta.ranges.top_p.max, s.top_p)}
                    ${buildSettingsField('setting-top-k', 'Top K', 'Liczba kandydatów tokenów branych pod uwagę przy generowaniu.', adminSettingsMeta.ranges.top_k.min, adminSettingsMeta.ranges.top_k.max, s.top_k)}
                    ${buildSettingsField('setting-max-tokens', 'Max tokens (num_predict)', 'Maksymalna liczba tokenów generowanej odpowiedzi.', adminSettingsMeta.ranges.max_tokens.min, adminSettingsMeta.ranges.max_tokens.max, s.max_tokens)}
                    ${buildSettingsField('setting-context-length', 'Długość kontekstu (num_ctx)', 'Maksymalna liczba tokenów w kontekście (im więcej, tym większe zużycie pamięci).', adminSettingsMeta.ranges.context_length.min, adminSettingsMeta.ranges.context_length.max, s.context_length)}
                    ${buildSettingsField('setting-segment-chunk-words', 'Długość segmentu (słowa)', 'Liczba słów w jednym fragmencie podczas segmentacji dokumentu.', adminSettingsMeta.ranges.segment_chunk_words.min, adminSettingsMeta.ranges.segment_chunk_words.max, s.segment_chunk_words)}
                    <h4 style="margin-top: 15px;">Prompty</h4>
                    ${buildPromptField('prompt-segmentation', 'Prompt segmentacji', 'Określa, jak AI ma wyodrębniać funkcjonalności z dokumentu.', p.segmentation)}
                    ${buildPromptField('prompt-paths', 'Prompt ścieżek testowych', 'Definiuje sposób generowania ścieżek testowych.', p.paths)}
                    ${buildPromptField('prompt-scenario', 'Prompt scenariuszy manualnych', 'Definiuje szczegółowe scenariusze testowe.', p.scenario)}
                    ${buildPromptField('prompt-images', 'Prompt opisów obrazów', 'Kontroluje sposób opisu grafik w dokumentacji.', p.images)}
                    ${buildPromptField('prompt-automation', 'Prompt automatyzacji', 'Definiuje generowanie testów automatycznych.', p.automation)}
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" id="admin-defaults-btn">Przywróć domyślne</button>
                    <button class="btn btn-primary" id="admin-save-settings-btn">Zapisz ustawienia</button>
                    <button class="btn btn-danger" id="admin-restart-system-btn">Restartuj system</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        document.getElementById('admin-defaults-btn').addEventListener('click', applyAdminDefaultsToForm);
        document.getElementById('admin-save-settings-btn').addEventListener('click', saveAdminSettingsFromForm);
        document.getElementById('admin-restart-system-btn').addEventListener('click', showAdminRestartConfirm);
    } catch (err) {
        console.error('Błąd pobierania ustawień admina:', err);
        showToast('Nie udało się pobrać ustawień systemu', 'error');
    }
}

function applyAdminDefaultsToForm() {
    if (!adminSettingsMeta || !adminSettingsMeta.defaults) return;
    const d = adminSettingsMeta.defaults;
    const map = {
        temperature: 'setting-temperature',
        top_p: 'setting-top-p',
        top_k: 'setting-top-k',
        max_tokens: 'setting-max-tokens',
        context_length: 'setting-context-length',
        segment_chunk_words: 'setting-segment-chunk-words'
    };
    Object.keys(map).forEach(key => {
        const el = document.getElementById(map[key]);
        if (el && d[key] !== undefined) {
            el.value = d[key];
        }
    });
    const pd = adminSettingsMeta.promptDefaults || null;
    if (pd) {
        const promptMap = {
            segmentation: 'prompt-segmentation',
            paths: 'prompt-paths',
            scenario: 'prompt-scenario',
            images: 'prompt-images',
            automation: 'prompt-automation'
        };
        Object.keys(promptMap).forEach(key => {
            const el = document.getElementById(promptMap[key]);
            if (el && typeof pd[key] === 'string') {
                el.value = pd[key];
            }
        });
    }
    showToast('Przywrócono domyślne wartości (pamiętaj o zapisaniu zmian).', 'info');
}

async function saveAdminSettingsFromForm() {
    if (!adminSettingsMeta) return;
    const ranges = adminSettingsMeta.ranges || {};
    const getVal = (id) => {
        const el = document.getElementById(id);
        return el ? el.value : '';
    };
    const settings = {
        temperature: parseFloat(getVal('setting-temperature')),
        top_p: parseFloat(getVal('setting-top-p')),
        top_k: parseInt(getVal('setting-top-k') || '0', 10),
        max_tokens: parseInt(getVal('setting-max-tokens') || '0', 10),
        context_length: parseInt(getVal('setting-context-length') || '0', 10),
        segment_chunk_words: parseInt(getVal('setting-segment-chunk-words') || '0', 10)
    };
    // Prosta walidacja po stronie klienta (zakresy)
    for (const key of Object.keys(settings)) {
        if (!ranges[key]) continue;
        const v = settings[key];
        if (isNaN(v) || v < ranges[key].min || v > ranges[key].max) {
            showToast(`Wartość ${key} musi być w zakresie ${ranges[key].min}–${ranges[key].max}`, 'warning');
            return;
        }
    }
    const prompts = {
        segmentation: (document.getElementById('prompt-segmentation') || {}).value || '',
        paths: (document.getElementById('prompt-paths') || {}).value || '',
        scenario: (document.getElementById('prompt-scenario') || {}).value || '',
        images: (document.getElementById('prompt-images') || {}).value || '',
        automation: (document.getElementById('prompt-automation') || {}).value || ''
    };
    try {
        const response = await fetch('/api/admin/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ settings, prompts })
        });
        const data = await response.json();
        if (response.ok && data.success) {
            showToast('Ustawienia zapisane. Zostaną zastosowane po restarcie systemu.', 'success');
        } else {
            const msg = data.errors ? JSON.stringify(data.errors) : (data.error || 'Błąd zapisu ustawień');
            showToast(msg, 'error');
        }
    } catch (err) {
        console.error('Błąd zapisu ustawień admina:', err);
        showToast('Nie udało się zapisać ustawień systemu', 'error');
    }
}

function showAdminRestartConfirm() {
    // Drugi modal z potwierdzeniem restartu
    const existing = document.getElementById('admin-restart-modal');
    if (existing) existing.remove();
    const modal = document.createElement('div');
    modal.id = 'admin-restart-modal';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Restart systemu</h3>
                <button class="modal-close" onclick="document.getElementById('admin-restart-modal').remove()">&times;</button>
            </div>
            <div class="modal-body">
                <p>Po restarcie systemu nowe ustawienia zostaną wczytane.</p>
                <p class="modal-warning">Aktualnie przetwarzane zadania zostaną przerwane i <strong>nie zostaną automatycznie wznowione</strong>. Będziesz mógł/mogła uruchomić je ponownie ręcznie z poziomu kolejki.</p>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="document.getElementById('admin-restart-modal').remove()">Anuluj</button>
                <button class="btn btn-danger" id="admin-restart-confirm-btn">TAK, restartuj system</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    document.getElementById('admin-restart-confirm-btn').addEventListener('click', async () => {
        try {
            const response = await fetch('/api/admin/restart', { method: 'POST' });
            const data = await response.json();
            if (response.ok && data.success) {
                showToast('System zrestartowany. Nowe ustawienia są aktywne.', 'success');
                refreshQueueStatus();
            } else {
                showToast(data.error || 'Błąd restartu systemu', 'error');
            }
        } catch (err) {
            console.error('Błąd restartu systemu:', err);
            showToast('Nie udało się zrestartować systemu', 'error');
        } finally {
            const m = document.getElementById('admin-restart-modal');
            if (m) m.remove();
            closeAdminModal();
        }
    });
}

// Inicjalizacja panelu administratora v0.6
function initAdminUI() {
    isAdmin = window.localStorage.getItem('scenarzysta_is_admin') === 'true';
    updateAdminUI();
    const loginBtn = document.getElementById('admin-login-btn');
    const logoutBtn = document.getElementById('admin-logout-btn');
    const settingsBtn = document.getElementById('admin-settings-btn');
    if (loginBtn) {
        loginBtn.addEventListener('click', showAdminLoginModal);
    }
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleAdminLogout);
    }
    if (settingsBtn) {
        settingsBtn.addEventListener('click', showAdminSettingsModal);
    }
}

function updateAdminUI() {
    const loginBtn = document.getElementById('admin-login-btn');
    const logoutBtn = document.getElementById('admin-logout-btn');
    const settingsBtn = document.getElementById('admin-settings-btn');
    const statusLabel = document.getElementById('admin-status');
    if (!loginBtn || !logoutBtn || !settingsBtn || !statusLabel) return;
    if (isAdmin) {
        loginBtn.style.display = 'none';
        logoutBtn.style.display = 'inline-block';
        settingsBtn.style.display = 'inline-block';
        statusLabel.style.display = 'inline-block';
    } else {
        loginBtn.style.display = 'inline-block';
        logoutBtn.style.display = 'none';
        settingsBtn.style.display = 'none';
        statusLabel.style.display = 'none';
    }
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
    initAdminUI();
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
    
    // Toggle dla sekcji "Dodaj swój opis"
    const descToggle = document.getElementById('custom-description-toggle');
    if (descToggle) {
        descToggle.addEventListener('change', (e) => {
            const section = document.getElementById('custom-description-section');
            section.style.display = e.target.checked ? 'block' : 'none';
        });
    }
    
    // Toggle dla sekcji "Dodaj swój przykład"
    const exampleToggle = document.getElementById('custom-example-toggle');
    if (exampleToggle) {
        exampleToggle.addEventListener('change', (e) => {
            const section = document.getElementById('custom-example-section');
            section.style.display = e.target.checked ? 'block' : 'none';
        });
    }
    
    // Toggle dla sekcji "Szablon testów automatycznych"
    const automationToggle = document.getElementById('automation-toggle');
    if (automationToggle) {
        automationToggle.addEventListener('change', (e) => {
            const section = document.getElementById('automation-section');
            section.style.display = e.target.checked ? 'block' : 'none';
        });
    }
    
    // Toggle dla podopcji "Wczytaj plik ze scenariuszami"
    const automationExcelToggle = document.getElementById('automation-excel-toggle');
    if (automationExcelToggle) {
        automationExcelToggle.addEventListener('change', (e) => {
            const upload = document.getElementById('automation-excel-upload');
            const fileLabel = document.querySelector('.file-label-text');
            const fileSection = document.querySelector('.file-input-wrapper');
            const customDescToggle = document.getElementById('custom-description-toggle');
            const customDescSection = document.getElementById('custom-description-section');
            const customExampleToggle = document.getElementById('custom-example-toggle');
            const customExampleSection = document.getElementById('custom-example-section');
            const correlateToggle = document.getElementById('correlate-documents');
            upload.style.display = e.target.checked ? 'block' : 'none';
            
            // Zmień etykietę głównego inputu w trybie Excel
            if (e.target.checked) {
                fileLabel.textContent = 'Plik dokumentacji (opcjonalny w trybie Excel)';
                fileSection.classList.add('optional-mode');

                // Tryb Excel: wyłącz opcje zależne od generowania scenariuszy z dokumentacji
                if (customDescToggle) {
                    customDescToggle.checked = false;
                    customDescToggle.disabled = true;
                    if (customDescSection) {
                        customDescSection.style.display = 'none';
                    }
                }
                if (customExampleToggle) {
                    customExampleToggle.checked = false;
                    customExampleToggle.disabled = true;
                    if (customExampleSection) {
                        customExampleSection.style.display = 'none';
                    }
                }
                if (correlateToggle) {
                    correlateToggle.checked = false;
                    correlateToggle.disabled = true;
                }

                showToast('Tryb Excel: scenariusze nie będą generowane z dokumentacji. Opcje opisu, przykładu i korelacji zostały wyłączone.', 'info', 8000);
            } else {
                fileLabel.textContent = 'Wybierz pliki (docx, pdf, xlsx, txt)';
                fileSection.classList.remove('optional-mode');

                // Powrót z trybu Excel: odblokuj checkboxy (bez zmiany zawartości pól)
                if (customDescToggle) {
                    customDescToggle.disabled = false;
                }
                if (customExampleToggle) {
                    customExampleToggle.disabled = false;
                }
                if (correlateToggle) {
                    correlateToggle.disabled = false;
                }
            }
        });
    }
    
    // Toggle dla podopcji "Użyj własnego promptu"
    const automationCustomToggle = document.getElementById('automation-custom-toggle');
    if (automationCustomToggle) {
        automationCustomToggle.addEventListener('change', (e) => {
            const section = document.getElementById('automation-custom-section');
            section.style.display = e.target.checked ? 'block' : 'none';
        });
    }
}

// Obsługa przesyłania pliku
async function handleFileUpload(e) {
    e.preventDefault();
    
    const fileInput = document.getElementById('file-input');
    const files = fileInput.files;
    const correlateDocuments = document.getElementById('correlate-documents')?.checked || false;
    
    // Nowe opcje v0.2
    const customDescEnabled = document.getElementById('custom-description-toggle')?.checked || false;
    const customPathsDesc = customDescEnabled ? document.getElementById('custom-paths-desc')?.value || '' : '';
    const customScenariosDesc = customDescEnabled ? document.getElementById('custom-scenarios-desc')?.value || '' : '';
    
    const customExampleEnabled = document.getElementById('custom-example-toggle')?.checked || false;
    const exampleFile = document.getElementById('example-file')?.files?.[0] || null;
    
    // Nowe opcje v0.4 - Automatyzacja
    const automationEnabled = document.getElementById('automation-toggle')?.checked || false;
    const automationExcelToggleChecked = document.getElementById('automation-excel-toggle')?.checked || false;
    const automationExcelInput = document.getElementById('automation-excel-file');
    const automationExcelFile = automationExcelInput?.files?.[0] || null;
    const automationExcelEnabled = automationEnabled && automationExcelToggleChecked;
    const automationCustomEnabled = automationEnabled && document.getElementById('automation-custom-toggle')?.checked || false;
    const automationCustomPrompt = automationCustomEnabled ? document.getElementById('automation-custom-prompt')?.value || '' : '';
    const automationCustomFiles = automationCustomEnabled ? document.getElementById('automation-custom-files')?.files || [] : [];
    
    // v0.5: Rozszerzona walidacja formularza
    const hasDocumentationFiles = files && files.length > 0;
    const isExcelMode = automationEnabled && automationExcelEnabled && automationExcelFile;
    
    // 1. Walidacja podstawowa: musi być przynajmniej jedno źródło danych
    if (!hasDocumentationFiles && !isExcelMode) {
        showToast('Wybierz co najmniej jeden plik dokumentacji lub wgraj Excel ze scenariuszami w trybie automatyzacji', 'warning');
        return;
    }
    
    // 2. Walidacja trybu Excel: musi być plik Excel jeśli tryb jest aktywny
    if (automationExcelEnabled && !automationExcelFile) {
        showToast('W trybie Excel musisz wgrać plik ze scenariuszami', 'warning');
        return;
    }
    
    // 3. Opcjonalne ostrzeżenie: puste pola przy włączonym opisie wymagań
    if (customDescEnabled && !customPathsDesc && !customScenariosDesc) {
        console.warn('[WALIDACJA] Checkbox "Dodaj opis wymagań" jest zaznaczony, ale oba pola są puste');
        // Nie blokujemy - to tylko hint dla AI
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
        // W trybie Excel bez dokumentacji - jedno zadanie z plikiem Excel
        const filesToProcess = (isExcelMode && (!files || files.length === 0)) 
            ? [{ name: automationExcelFile.name, isExcelOnly: true }] 
            : Array.from(files);
        
        for (let i = 0; i < filesToProcess.length; i++) {
            const fileInfo = filesToProcess[i];
            const isExcelOnlyMode = fileInfo.isExcelOnly === true;
            uploadBtn.textContent = `Przesyłanie ${i + 1}/${filesToProcess.length}...`;
            
            const formData = new FormData();
            
            if (isExcelOnlyMode) {
                // W trybie tylko Excel - użyj pliku Excel jako głównego
                formData.append('file', automationExcelFile);
            } else {
                formData.append('file', files[i]);
            }
            
            formData.append('user_id', currentUserId);
            formData.append('correlate_documents', correlateDocuments.toString());
            
            // Nowe opcje v0.2
            formData.append('custom_paths_description', customPathsDesc);
            formData.append('custom_scenarios_description', customScenariosDesc);
            if (exampleFile) {
                formData.append('example_file', exampleFile);
            }
            
            // Nowe opcje v0.4 - Automatyzacja
            formData.append('generate_automation', automationEnabled.toString());
            formData.append('automation_excel_mode', (automationExcelEnabled || isExcelOnlyMode).toString());
            if (automationExcelFile) {
                formData.append('automation_excel_file', automationExcelFile);
            }
            formData.append('automation_custom_prompt', automationCustomPrompt);
            for (let j = 0; j < automationCustomFiles.length; j++) {
                formData.append('automation_custom_files', automationCustomFiles[j]);
            }
            
            const response = await fetch('/api/tasks', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                successCount++;
            } else {
                failCount++;
                const fileName = isExcelOnlyMode ? automationExcelFile.name : files[i].name;
                console.error(`Błąd przesyłania ${fileName}: ${data.error}`);
            }
        }
        
        // Podsumowanie
        const correlateInfo = correlateDocuments ? ' (z korelacją)' : '';
        const customInfo = (customPathsDesc || customScenariosDesc) ? ' (z opisem użytkownika)' : '';
        const automationInfo = automationEnabled ? (isExcelMode ? ' (automatyzacja z Excel)' : ' (z automatyzacją)') : '';
        
        if (failCount === 0) {
            showToast(`Przesłano ${successCount} plik(ów) pomyślnie${correlateInfo}${customInfo}${automationInfo}!`, 'success');
        } else {
            showToast(`Przesłano ${successCount} plik(ów), ${failCount} błędów.`, 'warning');
        }
        
        // Reset formularza
        fileInput.value = '';
        document.querySelector('.file-label-text').textContent = 'Wybierz pliki (docx, pdf, xlsx, txt)';
        document.getElementById('selected-files').innerHTML = '';
        if (document.getElementById('correlate-documents')) {
            document.getElementById('correlate-documents').checked = false;
        }
        // Reset opcjonalnych sekcji
        if (document.getElementById('custom-description-toggle')) {
            document.getElementById('custom-description-toggle').checked = false;
            document.getElementById('custom-description-section').style.display = 'none';
            document.getElementById('custom-paths-desc').value = '';
            document.getElementById('custom-scenarios-desc').value = '';
        }
        if (document.getElementById('custom-example-toggle')) {
            document.getElementById('custom-example-toggle').checked = false;
            document.getElementById('custom-example-section').style.display = 'none';
            document.getElementById('example-file').value = '';
        }
        // Reset sekcji automatyzacji
        if (document.getElementById('automation-toggle')) {
            document.getElementById('automation-toggle').checked = false;
            document.getElementById('automation-section').style.display = 'none';
            if (document.getElementById('automation-excel-toggle')) {
                document.getElementById('automation-excel-toggle').checked = false;
                document.getElementById('automation-excel-upload').style.display = 'none';
                document.getElementById('automation-excel-file').value = '';
                // Przywróć etykietę głównego inputu
                document.querySelector('.file-label-text').textContent = 'Wybierz pliki (docx, pdf, xlsx, txt)';
                document.querySelector('.file-input-wrapper').classList.remove('optional-mode');
            }
            if (document.getElementById('automation-custom-toggle')) {
                document.getElementById('automation-custom-toggle').checked = false;
                document.getElementById('automation-custom-section').style.display = 'none';
                document.getElementById('automation-custom-prompt').value = '';
                document.getElementById('automation-custom-files').value = '';
            }
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
            
            // Przycisk pobierania testów automatycznych
            const automationBtn = document.getElementById(`automation-btn-${task.task_id}`);
            if (automationBtn) {
                automationBtn.addEventListener('click', () => downloadAutomationTests(task.task_id));
            }
        }
        
        // Przycisk zatrzymania
        if (task.status === 'processing') {
            const stopBtn = document.getElementById(`stop-btn-${task.task_id}`);
            if (stopBtn) {
                stopBtn.addEventListener('click', () => showStopConfirmation(task.task_id, task.filename));
            }
            // Przycisk pobierania bieżących scenariuszy
            const currentExcelBtn = document.getElementById(`current-excel-btn-${task.task_id}`);
            if (currentExcelBtn) {
                currentExcelBtn.addEventListener('click', () => downloadCurrentExcel(task.task_id));
            }
            // Przycisk pobierania dotychczasowych testów automatycznych
            const currentAutomationBtn = document.getElementById(`current-automation-btn-${task.task_id}`);
            if (currentAutomationBtn) {
                currentAutomationBtn.addEventListener('click', () => downloadCurrentAutomationTests(task.task_id));
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
        const stageIndex = typeof task.current_stage === 'number' ? task.current_stage : 0;
        const totalStages = task.total_stages || 0;
        const stageInfo = totalStages > 0 ? ` (Etap ${stageIndex + 1}/${totalStages})` : '';
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
    if (task.status === 'processing' || task.status === 'stopped') {
        if (task.status === 'processing') {
            actions.push(`<button class="btn btn-warning" id="stop-btn-${task.task_id}">Zatrzymaj</button>`);
        }
        // Przycisk pobierania bieżących scenariuszy (etap >= 3, nie w trybie Excel)
        if (!task.automation_excel_mode && task.current_stage >= 3) {
            actions.push(`<button class="btn btn-info" id="current-excel-btn-${task.task_id}">Pobierz scenariusze manualne (dotychczasowe)</button>`);
        }
        // Przycisk pobierania dotychczasowych testów automatycznych (etap 4+)
        if (task.generate_automation && task.current_stage >= 4 && task.progress > 15) {
            actions.push(`<button class="btn btn-primary" id="current-automation-btn-${task.task_id}">Pobierz testy (dotychczasowe)</button>`);
        }
    }
    // Przycisk restartu dla zatrzymanych/błędnych/anulowanych
    if (task.can_restart) {
        actions.push(`<button class="btn btn-primary" id="restart-btn-${task.task_id}">Uruchom ponownie</button>`);
        actions.push(`<button class="btn btn-danger" id="remove-btn-${task.task_id}">Usuń z kolejki</button>`);
    }
    if (task.status === 'completed' && task.result_path) {
        actions.push(`<button class="btn btn-success" id="download-btn-${task.task_id}">Pobierz scenariusze manualne</button>`);
        actions.push(`<button class="btn btn-info" id="artifacts-btn-${task.task_id}">Wszystkie artefakty</button>`);
        // Przycisk pobierania testów automatycznych
        if (task.generate_automation && task.automation_result_path) {
            actions.push(`<button class="btn btn-primary" id="automation-btn-${task.task_id}">Pobierz testy automatyczne</button>`);
        }
    }
    
    // Znaczniki opcji
    let optionBadges = [];
    if (task.correlate_documents) {
        optionBadges.push('<span class="option-tag experimental">Korelacja dok.</span>');
    }
    if (task.generate_automation) {
        if (task.automation_excel_mode) {
            optionBadges.push('<span class="option-tag automation-excel">Automatyzacja (Excel)</span>');
        } else {
            optionBadges.push('<span class="option-tag automation">Automatyzacja</span>');
        }
    }
    const optionsInfo = optionBadges.length > 0 ? `
        <div class="task-options">${optionBadges.join('')}</div>
    ` : '';
    
    return `
        <div class="task-card">
            <div class="task-header">
                <div class="task-title">${task.filename}</div>
                <span class="task-status ${statusClass}">${statusText}</span>
            </div>
            <div class="task-info">
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
            
            // Przycisk pobierania testów automatycznych
            const automationArtifact = entry.artifacts ? entry.artifacts.find(a => a.type === 'zip' && a.filename.includes('automation')) : null;
            if (automationArtifact) {
                const automationBtn = document.getElementById(`history-automation-btn-${entry.task_id}`);
                if (automationBtn) {
                    automationBtn.addEventListener('click', () => downloadHistoryArtifact(entry.task_id, automationArtifact.filename));
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
    
    // Znajdź pliki w artefaktach
    const excelArtifact = entry.artifacts ? entry.artifacts.find(a => a.type === 'xlsx') : null;
    const automationArtifact = entry.artifacts ? entry.artifacts.find(a => a.type === 'zip' && a.filename.includes('automation')) : null;
    
    const actions = [];
    // Przycisk pobierania scenariuszy manualnych (Excel, jeśli jest)
    if (excelArtifact) {
        actions.push(`<button class="btn btn-success btn-sm" id="history-excel-btn-${entry.task_id}">Pobierz scenariusze manualne</button>`);
    }
    // Przycisk pobierania testów automatycznych (jeśli jest ZIP z automatyzacją)
    if (automationArtifact) {
        actions.push(`<button class="btn btn-primary btn-sm" id="history-automation-btn-${entry.task_id}">Pobierz testy automatyczne</button>`);
    }
    if (entry.has_source) {
        actions.push(`<button class="btn btn-secondary btn-sm" id="history-source-btn-${entry.task_id}">Plik zrodlowy</button>`);
    }
    if (artifactsCount > 0) {
        actions.push(`<button class="btn btn-info btn-sm" id="history-artifacts-btn-${entry.task_id}">Artefakty (${artifactsCount})</button>`);
    }
    
    // Znaczniki opcji (historia) - wszystkie ustawione checkboxy
    let historyBadges = [];
    if (entry.correlate_documents) {
        historyBadges.push('<span class="option-tag experimental">Korelacja dok.</span>');
    }
    if (entry.custom_description) {
        historyBadges.push('<span class="option-tag">Wlasny opis</span>');
    }
    if (entry.custom_example) {
        historyBadges.push('<span class="option-tag">Przyklad</span>');
    }
    if (entry.generate_automation) {
        if (entry.automation_excel_mode) {
            historyBadges.push('<span class="option-tag automation-excel">Automatyzacja (Excel)</span>');
        } else {
            historyBadges.push('<span class="option-tag automation">Automatyzacja</span>');
        }
    }
    const optionsInfo = historyBadges.length > 0 ? `
        <div class="task-options history-options">${historyBadges.join('')}</div>
    ` : '';
    
    return `
        <div class="history-card">
            <div class="history-header">
                <div class="history-title">${entry.filename}</div>
                <span class="task-status ${statusClass}">${statusText}</span>
            </div>
            <div class="history-info">
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
                <div class="download-all-section">
                    <button class="btn btn-primary" onclick="downloadAllArtifacts('${taskId}')">
                        Pobierz wszystko (ZIP)
                    </button>
                </div>
                <p>Lub pobierz pojedyncze pliki:</p>
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

// Pobieranie bieżącego excela w trakcie przetwarzania
function downloadCurrentExcel(taskId) {
    window.location.href = `/api/tasks/${taskId}/current-excel`;
}

// Pobieranie wszystkich artefaktów jako ZIP
function downloadAllArtifacts(taskId) {
    window.location.href = `/api/history/${taskId}/artifacts-zip`;
}

// Pobieranie artefaktu z historii
function downloadHistoryArtifact(taskId, filename) {
    window.location.href = `/api/history/${taskId}/artifacts/${filename}`;
}

// Pobieranie testów automatycznych (ZIP)
function downloadAutomationTests(taskId) {
    window.location.href = `/api/tasks/${taskId}/automation-zip`;
}

// Pobieranie dotychczasowych testów automatycznych (w trakcie przetwarzania)
function downloadCurrentAutomationTests(taskId) {
    window.location.href = `/api/tasks/${taskId}/automation-current-zip`;
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
