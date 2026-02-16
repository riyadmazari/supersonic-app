const API_URL = '';
// DOM Elements
const authScreen = document.getElementById('auth-screen');
const dashboardScreen = document.getElementById('dashboard-screen');
const authForm = document.getElementById('auth-form');
const authTabs = document.querySelectorAll('.auth-tab');
const projectList = document.getElementById('project-list');
const projectView = document.getElementById('project-view');
const emptyState = document.getElementById('empty-state');
const tasksContainer = document.getElementById('tasks-container');
const modalProject = document.getElementById('modal-project');
const modalTask = document.getElementById('modal-task');
const modalTaskEdit = document.getElementById('modal-task-edit');
const modalImport = document.getElementById('modal-import');
const fileUploadArea = document.getElementById('file-upload-area');
const importFileInput = document.getElementById('import-file');
const selectedFilename = document.getElementById('selected-filename');
const chatContainer = document.getElementById('ai-chat-container');
const toggleChatBtn = document.getElementById('toggle-chat-panel');
const closeChatBtn = document.getElementById('close-chat');
const chatMessages = document.getElementById('chat-messages');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const addTaskBottomBtn = document.getElementById('add-task-bottom-btn');

// State
let isLoginMode = true;
let token = localStorage.getItem('token');
let currentUser = null;
let currentProject = null;
let selectedFile = null;

// Toast Notification System
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const iconMap = {
        success: 'checkmark-circle',
        error: 'alert-circle',
        info: 'information-circle'
    };

    toast.innerHTML = `
        <ion-icon name="${iconMap[type]}" class="toast-icon"></ion-icon>
        <div class="toast-message">${message}</div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('removing');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Error Handler
async function handleApiCall(fn, successMessage = null) {
    try {
        const result = await fn();
        if (successMessage) {
            showToast(successMessage, 'success');
        }
        return result;
    } catch (error) {
        console.error('API Error:', error);
        showToast(error.message || 'An error occurred', 'error');
        throw error;
    }
}

// Init
document.addEventListener('DOMContentLoaded', () => {
    if (token) {
        checkAuth();
    } else {
        showAuth();
    }
});

// Auth Logic
authTabs.forEach(tab => {
    tab.addEventListener('click', () => {
        authTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        isLoginMode = tab.dataset.tab === 'login';
        document.getElementById('full-name-field').classList.toggle('hidden', isLoginMode);
        document.getElementById('auth-submit-btn').textContent = isLoginMode ? 'Login' : 'Register';
    });
});

authForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const fullName = document.getElementById('full-name').value;
    const errorMsg = document.getElementById('auth-error');

    try {
        let endpoint = isLoginMode ? '/auth/login' : '/auth/register';

        let body;
        if (isLoginMode) {
            body = JSON.stringify({ username, password });
        } else {
            body = JSON.stringify({ username, password, full_name: fullName });
        }

        const headers = { 'Content-Type': 'application/json' };

        const res = await fetch(`${API_URL}${endpoint}`, {
            method: 'POST',
            headers,
            body
        });

        if (!res.ok) throw new Error('Auth failed');

        const data = await res.json();

        if (isLoginMode) {
            token = data.access_token;
            localStorage.setItem('token', token);
            checkAuth();
        } else {
            // Auto login after register
            alert('Registration successful! Please login.');
            authTabs[0].click();
        }
    } catch (err) {
        errorMsg.textContent = err.message;
        errorMsg.classList.remove('hidden');
    }
});

document.getElementById('logout-btn').addEventListener('click', () => {
    localStorage.removeItem('token');
    location.reload();
});

async function checkAuth() {
    try {
        const res = await fetch(`${API_URL}/auth/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Invalid token');
        currentUser = await res.json();
        showDashboard();
    } catch (err) {
        localStorage.removeItem('token');
        showAuth();
    }
}

function showAuth() {
    authScreen.classList.remove('hidden');
    dashboardScreen.classList.add('hidden');
    document.getElementById('navbar').classList.add('hidden');
}

function showDashboard() {
    authScreen.classList.add('hidden');
    dashboardScreen.classList.remove('hidden');
    document.getElementById('navbar').classList.remove('hidden');
    document.getElementById('user-name').textContent = currentUser.full_name || currentUser.username;
    loadProjects();
}

// Project Logic
async function loadProjects() {
    const res = await fetch(`${API_URL}/projects?skip=0&limit=100`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    const projects = await res.json();
    renderProjectList(projects);
}

function renderProjectList(projects) {
    projectList.innerHTML = '';
    if (projects.length === 0) {
        projectList.innerHTML = '<div style="color: var(--text-secondary); padding: 1rem; text-align: center;">No projects yet</div>';
        return;
    }
    projects.forEach(p => {
        const div = document.createElement('div');
        div.className = 'project-item';
        if (currentProject && currentProject.id === p.id) {
            div.classList.add('active');
        }
        div.innerHTML = `
            <span class="project-name">${p.name || p.title}</span>
            <button class="btn btn-secondary btn-sm text-danger project-delete-btn" onclick="deleteProject(event, '${p.id}')">
                <ion-icon name="trash-outline"></ion-icon>
            </button>
        `;
        div.onclick = () => loadProjectDetails(p.id);
        projectList.appendChild(div);
    });
}

async function deleteProject(event, id) {
    event.stopPropagation();
    if (!confirm('Are you sure you want to delete this project and all its tasks?')) return;

    try {
        const res = await fetch(`${API_URL}/projects/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!res.ok) throw new Error('Failed to delete project');

        showToast('Project deleted successfully', 'success');

        if (currentProject && currentProject.id === id) {
            currentProject = null;
            projectView.classList.add('hidden');
            emptyState.classList.remove('hidden');
        }

        loadProjects();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function loadProjectDetails(id) {
    const res = await fetch(`${API_URL}/projects/${id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    currentProject = await res.json();
    renderProjectView();
    loadTasks(id);
}

function renderProjectView() {
    emptyState.classList.add('hidden');
    projectView.classList.remove('hidden');
    document.getElementById('project-title').textContent = currentProject.name || currentProject.title;
    document.getElementById('project-desc').textContent = currentProject.description || 'No description';

    // AI section and Chat
    document.getElementById('ai-section').classList.add('hidden');

    // Reset Chat for new project
    chatContainer.classList.add('hidden');
    chatMessages.innerHTML = `
        <div class="message assistant">
            Hello! I'm your AI project assistant for <strong>${currentProject.name || currentProject.title}</strong>. 
            Ask me anything about these tasks.
        </div>
    `;

    // Ensure tasks the grid is visible
    document.getElementById('tasks-section').classList.remove('hidden');
}

// Task Logic
async function loadTasks(projectId) {
    const res = await fetch(`${API_URL}/projects/${projectId}/tasks`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    const tasks = await res.json();
    renderTasks(tasks);
}

function renderTasks(tasks) {
    tasksContainer.innerHTML = '';
    const emptyTasksState = document.getElementById('empty-tasks');

    if (tasks.length === 0) {
        tasksContainer.classList.add('hidden');
        emptyTasksState.classList.remove('hidden');
        return;
    }

    tasksContainer.classList.remove('hidden');
    emptyTasksState.classList.add('hidden');

    tasks.forEach(t => {
        const div = document.createElement('div');
        div.className = 'task-card';
        div.innerHTML = `
            <div class="task-info">
                <h4>${t.title}</h4>
                <div class="task-meta">
                    <span class="status-badge status-${t.status.toLowerCase().replace(' ', '-').replace('_', '-')}">${t.status.replace('_', ' ')}</span>
                    <span class="priority-badge priority-${t.priority.toLowerCase()}">${t.priority}</span>
                </div>
            </div>
            <div class="flex-row" style="gap: 0.5rem">
                <button class="btn btn-secondary btn-sm" onclick="openEditTaskModal('${t.id}')">
                    <ion-icon name="create-outline"></ion-icon>
                </button>
                <button class="btn btn-secondary btn-sm text-danger" onclick="deleteTask('${t.id}')">
                    <ion-icon name="trash"></ion-icon>
                </button>
            </div>
        `;
        tasksContainer.appendChild(div);
    });

    if (addTaskBottomBtn) {
        addTaskBottomBtn.classList.remove('hidden');
    }
}

async function deleteTask(id) {
    if (!confirm('Delete task?')) return;
    await fetch(`${API_URL}/tasks/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
    });
    loadTasks(currentProject.id);
}

// Open modals
document.getElementById('new-project-btn').addEventListener('click', () => {
    modalProject.classList.add('open');
    setTimeout(() => document.getElementById('new-proj-name').focus(), 100);
});

document.getElementById('new-task-btn').addEventListener('click', () => {
    modalTask.classList.add('open');
    setTimeout(() => document.getElementById('new-task-title').focus(), 100);
});

// Close modals
document.querySelectorAll('.close-modal').forEach(btn => {
    btn.addEventListener('click', (e) => {
        e.preventDefault();
        modalProject.classList.remove('open');
        modalTask.classList.remove('open');
        modalImport.classList.remove('open');
        modalTaskEdit.classList.remove('open');
    });
});

document.getElementById('import-project-btn').addEventListener('click', () => {
    modalImport.classList.add('open');
    selectedFile = null;
    importFileInput.value = '';
    selectedFilename.textContent = '';
});

// File upload area click
fileUploadArea.addEventListener('click', () => {
    importFileInput.click();
});

// File selection
importFileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        selectedFile = e.target.files[0];
        selectedFilename.textContent = `Selected: ${selectedFile.name}`;
    }
});

// Drag and drop
fileUploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    fileUploadArea.classList.add('dragover');
});

fileUploadArea.addEventListener('dragleave', () => {
    fileUploadArea.classList.remove('dragover');
});

fileUploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    fileUploadArea.classList.remove('dragover');

    if (e.dataTransfer.files.length > 0) {
        selectedFile = e.dataTransfer.files[0];
        selectedFilename.textContent = `Selected: ${selectedFile.name}`;
        // Update the input element
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(selectedFile);
        importFileInput.files = dataTransfer.files;
    }
});

// Import form submission
document.getElementById('import-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!selectedFile) {
        showToast('Please select a file to import', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        const res = await fetch(`${API_URL}/projects/import`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });

        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.detail || 'Failed to import project');
        }

        const project = await res.json();
        showToast(`Project "${project.name}" imported successfully with tasks!`, 'success');
        modalImport.classList.remove('open');
        loadProjects();
    } catch (error) {
        showToast(error.message || 'Failed to import project', 'error');
    }
});

// Create Project
document.getElementById('project-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('new-proj-name').value;
    const description = document.getElementById('new-proj-desc').value;

    try {
        const res = await fetch(`${API_URL}/projects`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ name, description })
        });

        if (!res.ok) throw new Error('Failed to create project');

        showToast('Project created successfully!', 'success');
        modalProject.classList.remove('open');
        e.target.reset();
        loadProjects();
    } catch (error) {
        showToast(error.message || 'Failed to create project', 'error');
    }
});

// Create Task
document.getElementById('task-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = document.getElementById('new-task-title').value;
    const priority = document.getElementById('new-task-priority').value;
    const status = document.getElementById('new-task-status').value;

    try {
        const res = await fetch(`${API_URL}/projects/${currentProject.id}/tasks`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                title, priority, status,
                description: "" // Schema might require this
            })
        });

        if (!res.ok) throw new Error('Failed to create task');

        showToast('Task created successfully!', 'success');
        modalTask.classList.remove('open');
        e.target.reset();
        loadTasks(currentProject.id);
    } catch (error) {
        showToast(error.message || 'Failed to create task', 'error');
    }
});

// AI Summary
const aiSummaryBtn = document.getElementById('ai-summary-btn');
if (aiSummaryBtn) {
    aiSummaryBtn.addEventListener('click', async () => {
        if (!currentProject) return;

        const aiSection = document.getElementById('ai-section');
        const aiResult = document.getElementById('ai-content');

        aiResult.innerHTML = '<div class="spinner"></div> Analyzing project...';
        aiSection.classList.remove('hidden');

        try {
            const res = await fetch(`${API_URL}/ai/summary`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ project_id: currentProject.id })
            });

            if (!res.ok) throw new Error('Failed to generate summary');

            const data = await res.json();
            const formattedResult = formatAIResponse(data.result);
            aiResult.innerHTML = formattedResult;
        } catch (error) {
            aiResult.innerHTML = `<span style="color: var(--danger);">Error: ${error.message}</span>`;
        }
    });
}

// AI Suggestions
const aiSuggestionsBtn = document.getElementById('ai-suggestions-btn');
if (aiSuggestionsBtn) {
    aiSuggestionsBtn.addEventListener('click', async () => {
        if (!currentProject) return;

        const aiSection = document.getElementById('ai-section');
        const aiResult = document.getElementById('ai-content');

        aiResult.innerHTML = '<div class="spinner"></div> Generating suggestions...';
        aiSection.classList.remove('hidden');

        try {
            const res = await fetch(`${API_URL}/ai/suggestions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ project_id: currentProject.id })
            });

            if (!res.ok) throw new Error('Failed to generate suggestions');

            const data = await res.json();
            const formattedResult = formatAIResponse(data.result);
            aiResult.innerHTML = formattedResult;
        } catch (error) {
            aiResult.innerHTML = `<span style="color: var(--danger);">Error: ${error.message}</span>`;
        }
    });
}

// Helper function to format AI responses
function formatAIResponse(text) {
    return text
        .split('\n')
        .map(line => {
            // Headings
            if (line.startsWith('# ')) {
                return `<h2 style="margin-top: 1rem; margin-bottom: 0.5rem; color: var(--accent-primary);">${line.substring(2)}</h2>`;
            }
            if (line.startsWith('## ')) {
                return `<h3 style="margin-top: 0.8rem; margin-bottom: 0.4rem; font-size: 1.1rem;">${line.substring(3)}</h3>`;
            }
            // Bold text
            if (line.includes('**')) {
                line = line.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
            }
            // List items
            if (line.startsWith('- ')) {
                return `<div style="margin-left: 1rem; margin-bottom: 0.3rem;">• ${line.substring(2)}</div>`;
            }
            // Numbered lists
            if (/^\d+\.\s/.test(line)) {
                return `<div style="margin-bottom: 0.5rem; font-weight: 600;">${line}</div>`;
            }
            // Regular paragraphs
            if (line.trim()) {
                return `<p style="margin-bottom: 0.5rem;">${line}</p>`;
            }
            // Empty lines
            return '<br style="line-height: 0.5;">';
        })
        .join('');
}
// Task Editing logic
async function openEditTaskModal(taskId) {
    try {
        const res = await fetch(`${API_URL}/tasks/${taskId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to fetch task details');
        const task = await res.json();

        document.getElementById('edit-task-id').value = task.id;
        document.getElementById('edit-task-title').value = task.title;
        document.getElementById('edit-task-priority').value = task.priority;
        document.getElementById('edit-task-status').value = task.status;
        document.getElementById('edit-task-assignee').value = task.assignee || '';

        document.getElementById('modal-task-edit').classList.add('open');
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function updateTask(e) {
    if (e) e.preventDefault();
    const taskId = document.getElementById('edit-task-id').value;
    const title = document.getElementById('edit-task-title').value;
    const priority = document.getElementById('edit-task-priority').value;
    const status = document.getElementById('edit-task-status').value;
    const assignee = document.getElementById('edit-task-assignee').value;

    const body = {
        title,
        priority,
        status,
        assignee: assignee || null
    };

    try {
        const res = await fetch(`${API_URL}/tasks/${taskId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(body)
        });

        if (!res.ok) throw new Error('Failed to update task');

        showToast('Task updated successfully', 'success');
        document.getElementById('modal-task-edit').classList.remove('open');
        loadProjectDetails(currentProject.id);
    } catch (error) {
        showToast(error.message, 'error');
    }
}

if (addTaskBottomBtn) {
    addTaskBottomBtn.addEventListener('click', () => {
        modalTask.classList.add('open');
    });
}

document.getElementById('task-edit-form').addEventListener('submit', updateTask);

toggleChatBtn.addEventListener('click', () => {
    chatContainer.classList.toggle('hidden');

    if (!chatContainer.classList.contains('hidden')) {
        chatInput.focus();
    }
});

closeChatBtn.addEventListener('click', () => {
    chatContainer.classList.add('hidden');
});

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const message = chatInput.value.trim();
    if (!message || !currentProject) return;

    // Add user message to UI
    appendMessage(message, 'user');
    chatInput.value = '';

    try {
        const res = await fetch(`${API_URL}/ai/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                project_id: currentProject.id,
                message: message
            })
        });

        if (!res.ok) throw new Error('Failed to get AI response');
        const data = await res.json();
        appendMessage(data.result, 'assistant');
    } catch (error) {
        appendMessage('Sorry, I encountered an error processing your request.', 'assistant');
    }
});

function appendMessage(text, sender) {
    const div = document.createElement('div');
    div.className = `message ${sender}`;
    if (sender === 'assistant') {
        div.innerHTML = formatAIResponse(text);
    } else {
        div.innerText = text;
    }
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

