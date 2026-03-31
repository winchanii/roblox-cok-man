/**
 * Roblox Account Manager - Main JavaScript
 */

// Глобальные утилиты
const Utils = {
    // Получить токен из localStorage
    getToken() {
        return localStorage.getItem('token');
    },

    // Сохранить токен
    setToken(token) {
        localStorage.setItem('token', token);
    },

    // Удалить токен
    removeToken() {
        localStorage.removeItem('token');
        localStorage.removeItem('user_id');
    },

    // Проверить авторизацию
    isAuthenticated() {
        return !!this.getToken();
    },

    // Проверить срок действия токена
    isTokenExpired(token) {
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            return payload.exp * 1000 < Date.now();
        } catch (e) {
            return true;
        }
    },

    // Форматировать дату
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('ru-RU', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    // Форматировать относительное время
    timeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const seconds = Math.floor((now - date) / 1000);

        if (seconds < 60) return 'только что';
        if (seconds < 3600) return `${Math.floor(seconds / 60)} мин. назад`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)} ч. назад`;
        if (seconds < 604800) return `${Math.floor(seconds / 86400)} дн. назад`;
        return this.formatDate(dateString);
    },

    // Копировать в буфер
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (e) {
            // Fallback для старых браузеров
            const textarea = document.createElement('textarea');
            textarea.value = text;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            return true;
        }
    },

    // Показать уведомление
    showNotification(message, type = 'info') {
        const colors = {
            success: '#28a745',
            error: '#dc3545',
            warning: '#ffc107',
            info: '#17a2b8'
        };

        const notification = document.createElement('div');
        notification.className = 'alert alert-dismissible fade show';
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            background: ${colors[type]};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 1rem 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: slideIn 0.3s ease-out;
        `;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 0.3);
        }, 5000);
    },

    // Загрузить файл как текст
    readFileAsText(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsText(file);
        });
    },

    // Скачать файл
    downloadFile(content, filename, type = 'application/json') {
        const blob = new Blob([content], { type });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    },

    // API запрос
    async apiRequest(endpoint, options = {}) {
        const token = this.getToken();
        const defaultOptions = {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        };

        const response = await fetch(endpoint, { ...defaultOptions, ...options });

        if (!response.ok) {
            if (response.status === 401) {
                this.removeToken();
                window.location.href = '/login';
                throw new Error('Unauthorized');
            }
            const data = await response.json().catch(() => ({}));
            throw new Error(data.detail || `HTTP ${response.status}`);
        }

        return response.json();
    }
};

// API методы
const API = {
    // Получить все аккаунты
    async getAccounts() {
        return Utils.apiRequest('/api/accounts');
    },

    // Добавить аккаунт
    async addAccount(cookie, password = null, description = '') {
        const formData = new FormData();
        formData.append('cookie', cookie);
        if (password) formData.append('password', password);
        formData.append('description', description);

        const token = Utils.getToken();
        const response = await fetch('/api/accounts', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail);
        }

        return response.json();
    },

    // Удалить аккаунт
    async deleteAccount(id) {
        return Utils.apiRequest(`/api/accounts/${id}`, {
            method: 'DELETE'
        });
    },

    // Обновить описание
    async updateDescription(id, description, applyInRoblox = true) {
        return Utils.apiRequest(`/api/accounts/${id}/description?apply_in_roblox=${applyInRoblox}`, {
            method: 'PUT',
            body: JSON.stringify({ description })
        });
    },

    // Получить куку
    async getCookie(id) {
        return Utils.apiRequest(`/api/accounts/${id}/cookie`);
    },

    // Проверить все куки
    async checkAllCookies() {
        return Utils.apiRequest('/api/accounts/check-all', {
            method: 'POST'
        });
    },

    // Проверить одну куку
    async checkCookie(id) {
        return Utils.apiRequest(`/api/accounts/${id}/check`, {
            method: 'POST'
        });
    },

    // Загрузить куки из файла
    async uploadCookies(file) {
        const formData = new FormData();
        formData.append('file', file);

        const token = Utils.getToken();
        const response = await fetch('/api/accounts/bulk-cookies', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail);
        }

        return response.json();
    },

    // Привязать пароли
    async linkPasswords(file) {
        const formData = new FormData();
        formData.append('file', file);

        const token = Utils.getToken();
        const response = await fetch('/api/accounts/link-passwords', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail);
        }

        return response.json();
    },

    // Экспортировать аккаунты
    async exportAccounts() {
        return Utils.apiRequest('/api/accounts/export/with-passwords');
    },

    // Удалить все аккаунты
    async deleteAllAccounts() {
        return Utils.apiRequest('/api/accounts/all', {
            method: 'DELETE'
        });
    }
};

// Проверка авторизации при загрузке
document.addEventListener('DOMContentLoaded', () => {
    // Проверка токена для защищённых страниц
    const protectedPaths = ['/', '/accounts', '/dashboard'];
    const currentPath = window.location.pathname;

    if (protectedPaths.some(path => currentPath.startsWith(path))) {
        if (!Utils.isAuthenticated()) {
            window.location.href = '/login';
        }
    }
});

// CSS анимация для уведомлений
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);

// Экспорт глобальных объектов
window.Utils = Utils;
window.API = API;
