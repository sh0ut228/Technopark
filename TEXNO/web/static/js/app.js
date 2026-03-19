// Состояние приложения
const state = {
    token: localStorage.getItem('adminToken'),
    currentPage: 'dashboard',
    links: [],
    users: [],
    charts: {}
};

const API_BASE = '/api/admin';

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
    setupEventListeners();
});

function checkAuth() {
    if (!state.token) {
        showLoginModal();
    } else {
        loadPage('dashboard');
    }
}

function setupEventListeners() {
    // Навигация
    document.querySelectorAll('.nav-link[data-page]').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = e.target.closest('a').dataset.page;
            setActiveNavLink(e.target);
            loadPage(page);
        });
    });

    // Обновление
    document.getElementById('refreshBtn')?.addEventListener('click', () => {
        loadPage(state.currentPage);
    });

    // Выход
    document.getElementById('logoutBtn')?.addEventListener('click', (e) => {
        e.preventDefault();
        logout();
    });

    // Экспорт
    document.getElementById('exportCSV')?.addEventListener('click', exportToCSV);
    document.getElementById('exportJSON')?.addEventListener('click', exportToJSON);
}

function setActiveNavLink(element) {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    element.closest('a').classList.add('active');
}

function showLoginModal() {
    const modal = new bootstrap.Modal(document.getElementById('loginModal'));
    modal.show();

    document.getElementById('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const token = document.getElementById('token').value;
        
        try {
            const response = await fetch(`${API_BASE}/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token })
            });

            if (response.ok) {
                state.token = token;
                localStorage.setItem('adminToken', token);
                modal.hide();
                loadPage('dashboard');
                showNotification('Успешный вход!', 'success');
            } else {
                showNotification('Неверный токен', 'error');
            }
        } catch (error) {
            showNotification('Ошибка подключения', 'error');
        }
    });
}

function logout() {
    state.token = null;
    localStorage.removeItem('adminToken');
    showLoginModal();
}

async function loadPage(page) {
    state.currentPage = page;
    document.getElementById('page-title').textContent = getPageTitle(page);
    
    const content = document.getElementById('content-area');
    content.innerHTML = '<div class="text-center mt-5"><div class="spinner-border"></div><p>Загрузка...</p></div>';
    
    try {
        switch(page) {
            case 'dashboard':
                await loadDashboard();
                break;
            case 'links':
                await loadLinks();
                break;
            case 'users':
                await loadUsers();
                break;
            case 'stats':
                await loadStats();
                break;
            case 'settings':
                await loadSettings();
                break;
        }
    } catch (error) {
        content.innerHTML = `<div class="alert alert-danger">Ошибка: ${error.message}</div>`;
    }
}

async function loadDashboard() {
    const template = document.getElementById('dashboard-template').innerHTML;
    document.getElementById('content-area').innerHTML = template;
    
    try {
        const [links, userStats, clickStats] = await Promise.all([
            apiCall('/links'),
            apiCall('/users/stats'),
            apiCall('/stats/clicks')
        ]);
        
        state.links = links;
        
        document.getElementById('totalLinks').textContent = links.length;
        document.getElementById('totalUsers').textContent = userStats.total_users || 0;
        document.getElementById('totalClicks').textContent = clickStats.total || 0;
        document.getElementById('activeToday').textContent = userStats.active_today || 0;
        
        // Топ ссылок
        const topLinks = clickStats.top_5 || [];
        const tbody = document.getElementById('topLinksTable');
        
        if (topLinks.length) {
            tbody.innerHTML = topLinks.map(link => {
                const percent = clickStats.total ? Math.round(link.clicks / clickStats.total * 100) : 0;
                return `
                    <tr>
                        <td>${link.name}</td>
                        <td>${link.clicks}</td>
                        <td>${percent}%</td>
                    </tr>
                `;
            }).join('');
        }
        
        // График
        createCategoryChart(clickStats.by_category || {});
        
    } catch (error) {
        console.error('Dashboard error:', error);
    }
}

function createCategoryChart(data) {
    const ctx = document.getElementById('categoryChart').getContext('2d');
    
    if (state.charts.category) {
        state.charts.category.destroy();
    }
    
    state.charts.category = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Финансы', 'Развитие', 'Инфраструктура'],
            datasets: [{
                data: [data.finance || 0, data.development || 0, data.infrastructure || 0],
                backgroundColor: ['#4361ee', '#f72585', '#4cc9f0']
            }]
        }
    });
}

async function loadLinks() {
    const template = document.getElementById('links-template').innerHTML;
    document.getElementById('content-area').innerHTML = template;
    
    try {
        const links = await apiCall('/links');
        state.links = links;
        
        document.getElementById('links-count').textContent = links.length;
        
        $('#linksTable').DataTable({
            data: links,
            columns: [
                { data: 'code' },
                { data: 'name' },
                { 
                    data: 'url',
                    render: (url) => `<a href="${url}" target="_blank">${truncate(url, 40)}</a>`
                },
                { 
                    data: 'category',
                    render: (cat) => `<span class="badge badge-category badge-${cat}">${getCategoryName(cat)}</span>`
                },
                { data: 'clicks', default: 0 },
                {
                    data: null,
                    render: (data) => `
                        <button class="btn btn-sm btn-outline-primary btn-action" onclick="editLink('${data.code}')">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger btn-action" onclick="showDeleteModal('${data.code}', '${data.name}')">
                            <i class="bi bi-trash"></i>
                        </button>
                    `
                }
            ],
            language: { url: '//cdn.datatables.net/plug-ins/1.11.5/i18n/ru.json' }
        });
    } catch (error) {
        console.error('Links error:', error);
    }
}

async function loadUsers() {
    const template = document.getElementById('users-template').innerHTML;
    document.getElementById('content-area').innerHTML = template;
    
    try {
        const users = await apiCall('/users');
        state.users = users;
        
        $('#usersTable').DataTable({
            data: users,
            columns: [
                { data: 'user_id' },
                { data: 'username', defaultContent: '-' },
                { 
                    data: null,
                    render: (data) => `${data.first_name || ''} ${data.last_name || ''}`.trim() || '-'
                },
                { 
                    data: 'first_seen',
                    render: (date) => new Date(date).toLocaleString()
                },
                { 
                    data: 'last_seen',
                    render: (date) => new Date(date).toLocaleString()
                },
                { data: 'interactions_count' }
            ],
            language: { url: '//cdn.datatables.net/plug-ins/1.11.5/i18n/ru.json' }
        });
    } catch (error) {
        console.error('Users error:', error);
    }
}

async function loadStats() {
    const template = document.getElementById('stats-template').innerHTML;
    document.getElementById('content-area').innerHTML = template;
    
    try {
        const stats = await apiCall('/stats/clicks');
        
        const ctx = document.getElementById('statsChart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Финансы', 'Развитие', 'Инфраструктура'],
                datasets: [{
                    label: 'Переходы',
                    data: [stats.by_category.finance, stats.by_category.development, stats.by_category.infrastructure],
                    backgroundColor: ['#4361ee', '#f72585', '#4cc9f0']
                }]
            }
        });
    } catch (error) {
        console.error('Stats error:', error);
    }
}

async function loadSettings() {
    const template = document.getElementById('settings-template').innerHTML;
    document.getElementById('content-area').innerHTML = template;
    
    try {
        const settings = await apiCall('/settings');
        
        document.getElementById('welcomeMessage').value = settings.welcome_message || '';
        document.getElementById('botName').value = settings.bot_name || '';
        
        document.getElementById('settingsForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            await saveSettings();
        });
    } catch (error) {
        console.error('Settings error:', error);
    }
}

async function saveSettings() {
    const settings = {
        welcome_message: document.getElementById('welcomeMessage').value,
        bot_name: document.getElementById('botName').value
    };
    
    try {
        await apiCall('/settings', {
            method: 'POST',
            body: JSON.stringify(settings)
        });
        showNotification('Настройки сохранены', 'success');
    } catch (error) {
        showNotification('Ошибка сохранения', 'error');
    }
}

function showAddLinkModal() {
    document.getElementById('linkModalTitle').textContent = 'Добавить ссылку';
    document.getElementById('linkForm').reset();
    document.getElementById('linkId').value = '';
    new bootstrap.Modal(document.getElementById('linkModal')).show();
}

function editLink(code) {
    const link = state.links.find(l => l.code === code);
    if (!link) return;
    
    document.getElementById('linkModalTitle').textContent = 'Редактировать ссылку';
    document.getElementById('linkCode').value = link.code;
    document.getElementById('menuCode').value = link.menu_code;
    document.getElementById('linkName').value = link.name;
    document.getElementById('linkUrl').value = link.url;
    document.getElementById('linkCategory').value = link.category || 'finance';
    document.getElementById('parentCategory').value = link.parent_category || '1';
    
    new bootstrap.Modal(document.getElementById('linkModal')).show();
}

async function saveLink() {
    const linkData = {
        code: document.getElementById('linkCode').value,
        menu_code: document.getElementById('menuCode').value,
        name: document.getElementById('linkName').value,
        url: document.getElementById('linkUrl').value,
        category: document.getElementById('linkCategory').value,
        parent_category: document.getElementById('parentCategory').value
    };
    
    try {
        await apiCall('/links', {
            method: 'POST',
            body: JSON.stringify(linkData)
        });
        
        bootstrap.Modal.getInstance(document.getElementById('linkModal')).hide();
        loadLinks();
        showNotification('Ссылка сохранена', 'success');
    } catch (error) {
        showNotification('Ошибка сохранения', 'error');
    }
}

function showDeleteModal(code, name) {
    document.getElementById('deleteLinkName').textContent = name;
    window.currentDeleteCode = code;
    new bootstrap.Modal(document.getElementById('deleteModal')).show();
}

async function confirmDelete() {
    if (!window.currentDeleteCode) return;
    
    try {
        await apiCall(`/links/${window.currentDeleteCode}`, { method: 'DELETE' });
        bootstrap.Modal.getInstance(document.getElementById('deleteModal')).hide();
        loadLinks();
        showNotification('Ссылка удалена', 'success');
    } catch (error) {
        showNotification('Ошибка удаления', 'error');
    }
}

async function apiCall(endpoint, options = {}) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers: {
            'Authorization': `Bearer ${state.token}`,
            'Content-Type': 'application/json',
            ...options.headers
        }
    });
    
    if (response.status === 401) {
        logout();
        throw new Error('Сессия истекла');
    }
    
    if (!response.ok) {
        throw new Error(await response.text());
    }
    
    return response.json();
}

function getPageTitle(page) {
    const titles = {
        dashboard: 'Дашборд',
        links: 'Ссылки',
        users: 'Пользователи',
        stats: 'Статистика',
        settings: 'Настройки'
    };
    return titles[page] || page;
}

function getCategoryName(cat) {
    const names = {
        finance: 'Финансы',
        development: 'Развитие',
        infrastructure: 'Инфраструктура'
    };
    return names[cat] || cat;
}

function truncate(str, length) {
    return str.length > length ? str.substr(0, length) + '...' : str;
}

function showNotification(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `position-fixed bottom-0 end-0 p-3`;
    toast.style.zIndex = '9999';
    toast.innerHTML = `
        <div class="toast show align-items-center text-white bg-${type === 'error' ? 'danger' : 'success'} border-0">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function exportToCSV() {
    if (!state.links.length) return;
    
    const csv = [
        ['Код', 'Название', 'URL', 'Категория', 'Переходов'].join(','),
        ...state.links.map(l => `${l.code},"${l.name}",${l.url},${l.category},${l.clicks || 0}`)
    ].join('\n');
    
    downloadFile('links.csv', csv);
}

function exportToJSON() {
    if (!state.links.length) return;
    downloadFile('links.json', JSON.stringify(state.links, null, 2));
}

function downloadFile(filename, content) {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
}