const API_BASE = '';
let authToken = localStorage.getItem('auth_token');

if (!authToken) {
    window.location.href = '/auth/discord';
}

async function api(endpoint, options = {}) {
    const response = await fetch(API_BASE + endpoint, {
        ...options,
        headers: {
            ...options.headers,
            'Authorization': `Bearer ${authToken}`
        }
    });
    
    if (response.status === 401) {
        localStorage.removeItem('auth_token');
        window.location.href = '/auth/discord';
        return;
    }
    
    return response.json();
}

async function loadAccounts() {
    const data = await api('/api/accounts');
    
    document.getElementById('total-accounts').textContent = data.total;
    document.getElementById('valid-accounts').textContent = data.valid_count;
    document.getElementById('invalid-accounts').textContent = data.invalid_count;
    
    const tbody = document.getElementById('accounts-body');
    tbody.innerHTML = '';
    
    data.accounts.forEach(acc => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${acc.id}</td>
            <td>${acc.username}</td>
            <td>
                <input type="text" value="${acc.description}" 
                       onchange="updateDescription(${acc.id}, this.value)"
                       placeholder="Добавить описание">
            </td>
            <td>
                <span class="status ${acc.is_valid ? 'valid' : 'invalid'}">
                    ${acc.is_valid ? '✅' : '❌'}
                </span>
            </td>
            <td>
                <button onclick="getCookie(${acc.id})">📋 Кука</button>
                <button onclick="deleteAccount(${acc.id})" class="danger">🗑️</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function uploadCookies(input) {
    const file = input.files[0];
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch('/api/accounts/bulk-cookies', {
        method: 'POST',
        headers: {'Authorization': `Bearer ${authToken}`},
        body: formData
    });
    
    const result = await response.json();
    alert(`✅ Успешно: ${result.success}\n❌ Ошибок: ${result.failed}`);
    loadAccounts();
}

async function uploadPasswords(input) {
    const file = input.files[0];
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch('/api/accounts/link-passwords', {
        method: 'POST',
        headers: {'Authorization': `Bearer ${authToken}`},
        body: formData
    });
    
    const result = await response.json();
    alert(`✅ Привязано: ${result.success}\n❌ Не найдено: ${result.failed}`);
    loadAccounts();
}

async function addSingleAccount() {
    const cookie = document.getElementById('single-cookie').value;
    const password = document.getElementById('single-password').value;
    const description = document.getElementById('single-desc').value;
    
    const formData = new FormData();
    formData.append('cookie', cookie);
    if (password) formData.append('password', password);
    formData.append('description', description);
    
    const response = await fetch('/api/accounts', {
        method: 'POST',
        headers: {'Authorization': `Bearer ${authToken}`},
        body: formData
    });
    
    if (response.ok) {
        alert('Аккаунт добавлен!');
        loadAccounts();
    } else {
        const err = await response.json();
        alert('Ошибка: ' + err.detail);
    }
}

async function deleteAccount(id) {
    if (!confirm('Удалить этот аккаунт?')) return;
    
    await api(`/api/accounts/${id}`, {method: 'DELETE'});
    loadAccounts();
}

async function updateDescription(id, desc) {
    await api(`/api/accounts/${id}/description?description=${encodeURIComponent(desc)}`, {
        method: 'PUT'
    });
}

async function getCookie(id) {
    const data = await api(`/api/accounts/${id}/cookie`);
    navigator.clipboard.writeText(data.cookie);
    alert('Кука скопирована в буфер!');
}

async function checkAllCookies() {
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = '⏳ Проверка...';
    
    await api('/api/accounts/check-all', {method: 'POST'});
    
    btn.disabled = false;
    btn.textContent = '🔄 Проверить все куки';
    loadAccounts();
}

function logout() {
    localStorage.removeItem('auth_token');
    window.location.href = '/auth/discord';
}

// Load on start
loadAccounts();