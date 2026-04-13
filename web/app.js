// Task Manager Application
(function() {
    'use strict';

    // Constants
    const STORAGE_KEY = 'taskManagerTasks';
    const DEFAULT_PRIORITY_COLORS = {
        high: '#dc3545',
        medium: '#fd7e14',
        low: '#28a745'
    };

    // State
    let tasks = [];
    let currentFilter = {
        start: null,
        end: null
    };
    let selectedTaskId = null;
    let draggedTaskId = null;

    // DOM Elements
    const elements = {
        filterStart: document.getElementById('filter-start'),
        filterEnd: document.getElementById('filter-end'),
        clearFilterBtn: document.getElementById('clear-filter'),
        kanbanBoard: document.querySelector('.kanban-board'),
        addTaskBtn: document.getElementById('add-task-btn'),
        addTaskModal: document.getElementById('add-task-modal'),
        addTaskForm: document.getElementById('add-task-form'),
        taskNameInput: document.getElementById('task-name'),
        taskDescriptionInput: document.getElementById('task-description'),
        taskDeadlineInput: document.getElementById('task-deadline'),
        taskPrioritySelect: document.getElementById('task-priority'),
        cancelAddBtn: document.getElementById('cancel-add'),
        taskDetailModal: document.getElementById('task-detail-modal'),
        taskDetailContent: document.getElementById('task-detail-content'),
        editTaskBtn: document.getElementById('edit-task-btn'),
        deleteTaskBtn: document.getElementById('delete-task-btn'),
        closeDetailBtn: document.getElementById('close-detail'),
        editTaskModal: document.getElementById('edit-task-modal'),
        editTaskForm: document.getElementById('edit-task-form'),
        editTaskNameInput: document.getElementById('edit-task-name'),
        editTaskDescriptionInput: document.getElementById('edit-task-description'),
        editTaskDeadlineInput: document.getElementById('edit-task-deadline'),
        editTaskPrioritySelect: document.getElementById('edit-task-priority'),
        cancelEditBtn: document.getElementById('cancel-edit'),
        noTasksMessage: document.getElementById('no-tasks-message'),
        warningBanner: document.getElementById('warning-banner')
    };

    // Initialize Application
    function init() {
        checkLocalStorage();
        loadTasks();
        setDefaultFilter();
        renderTasks();
        bindEvents();
    }

    // Check localStorage availability
    function checkLocalStorage() {
        try {
            localStorage.setItem('test', 'test');
            localStorage.removeItem('test');
            elements.warningBanner.classList.add('hidden');
        } catch (e) {
            elements.warningBanner.classList.remove('hidden');
        }
    }

    // Set default date filter (current week ±3 days)
    function setDefaultFilter() {
        const today = new Date();
        const threeDaysAgo = new Date(today);
        threeDaysAgo.setDate(today.getDate() - 3);
        const threeDaysLater = new Date(today);
        threeDaysLater.setDate(today.getDate() + 3);

        elements.filterStart.value = formatDate(threeDaysAgo);
        elements.filterEnd.value = formatDate(threeDaysLater);

        currentFilter.start = threeDaysAgo;
        currentFilter.end = threeDaysLater;
    }

    // Format date for input fields
    function formatDate(date) {
        return date.toISOString().split('T')[0];
    }

    // Format date for display
    function formatDisplayDate(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    // Load tasks from localStorage
    function loadTasks() {
        try {
            const stored = localStorage.getItem(STORAGE_KEY);
            tasks = stored ? JSON.parse(stored) : [];
        } catch (e) {
            console.error('Failed to load tasks:', e);
            tasks = [];
        }
    }

    // Save tasks to localStorage
    function saveTasks() {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
        } catch (e) {
            console.error('Failed to save tasks:', e);
        }
    }

    // Generate unique ID
    function generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    // Create new task
    function createTask(name, description, deadline, priority) {
        const task = {
            id: generateId(),
            name: name,
            description: description || '',
            deadline: deadline || null,
            status: 'pending',
            priority: priority,
            created_at: new Date().toISOString(),
            started_at: null,
            completed_at: null,
            color: DEFAULT_PRIORITY_COLORS[priority]
        };
        tasks.push(task);
        saveTasks();
        renderTasks();
        return task;
    }

    // Update task
    function updateTask(id, updates) {
        const index = tasks.findIndex(t => t.id === id);
        if (index !== -1) {
            tasks[index] = { ...tasks[index], ...updates };
            saveTasks();
            renderTasks();
        }
    }

    // Delete task
    function deleteTask(id) {
        tasks = tasks.filter(t => t.id !== id);
        saveTasks();
        renderTasks();
    }

    // Get filtered tasks
    function getFilteredTasks() {
        if (!currentFilter.start || !currentFilter.end) {
            return tasks;
        }

        const startDate = new Date(currentFilter.start);
        startDate.setHours(0, 0, 0, 0);
        const endDate = new Date(currentFilter.end);
        endDate.setHours(23, 59, 59, 999);

        return tasks.filter(task => {
            const createdDate = new Date(task.created_at);
            return createdDate >= startDate && createdDate <= endDate;
        });
    }

    // Render tasks to columns
    function renderTasks() {
        const filteredTasks = getFilteredTasks();

        // Clear all columns
        document.querySelectorAll('.tasks-container').forEach(container => {
            container.innerHTML = '';
        });

        if (filteredTasks.length === 0) {
            elements.noTasksMessage.classList.remove('hidden');
        } else {
            elements.noTasksMessage.classList.add('hidden');
        }

        // Group tasks by status
        filteredTasks.forEach(task => {
            const container = document.querySelector(`.tasks-container[data-status="${task.status}"]`);
            if (container) {
                container.appendChild(createTaskCard(task));
            }
        });
    }

    // Create task card element
    function createTaskCard(task) {
        const card = document.createElement('div');
        card.className = `task-card priority-${task.priority}`;
        if (task.deadline && new Date(task.deadline) < new Date() && task.status !== 'done') {
            card.classList.add('overdue');
        }
        card.draggable = true;
        card.dataset.taskId = task.id;

        const descriptionPreview = task.description ? `<div class="task-description">${escapeHtml(task.description.substring(0, 50))}${task.description.length > 50 ? '...' : ''}</div>` : '';
        const deadlinePreview = task.deadline ? `<div class="task-deadline">Deadline: ${task.deadline}</div>` : '';

        card.innerHTML = `
            <div class="task-name">${escapeHtml(task.name)}</div>
            ${descriptionPreview}
            ${deadlinePreview}
            <div class="task-date">${formatDisplayDate(task.created_at)}</div>
        `;

        // Drag events
        card.addEventListener('dragstart', handleDragStart);
        card.addEventListener('dragend', handleDragEnd);

        // Click to view details
        card.addEventListener('click', () => showTaskDetails(task));

        return card;
    }

    // Escape HTML to prevent XSS
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Drag and Drop Handlers
    function handleDragStart(e) {
        draggedTaskId = e.target.dataset.taskId;
        e.target.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
    }

    function handleDragEnd(e) {
        e.target.classList.remove('dragging');
        draggedTaskId = null;
        document.querySelectorAll('.column').forEach(col => {
            col.classList.remove('drag-over');
        });
    }

    function handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    }

    function handleDragEnter(e) {
        e.preventDefault();
        const column = e.target.closest('.column');
        if (column) {
            column.classList.add('drag-over');
        }
    }

    function handleDragLeave(e) {
        const column = e.target.closest('.column');
        if (column && !column.contains(e.relatedTarget)) {
            column.classList.remove('drag-over');
        }
    }

    function handleDrop(e) {
        e.preventDefault();
        const column = e.target.closest('.column');
        if (!column || !draggedTaskId) return;

        const newStatus = column.dataset.status;
        const task = tasks.find(t => t.id === draggedTaskId);
        if (!task || task.status === newStatus) return;

        const updates = { status: newStatus };

        // Set started_at when moving to processing
        if (newStatus === 'processing' && !task.started_at) {
            updates.started_at = new Date().toISOString();
        }

        // Set completed_at when moving to done
        if (newStatus === 'done' && !task.completed_at) {
            updates.completed_at = new Date().toISOString();
        }

        updateTask(draggedTaskId, updates);
    }

    // Show task details modal
    function showTaskDetails(task) {
        selectedTaskId = task.id;
        const descriptionHtml = task.description ? `<p><strong>Description:</strong></p><p class="task-description-text">${escapeHtml(task.description)}</p>` : '';
        const deadlineHtml = task.deadline ? `<p><strong>Deadline:</strong> ${task.deadline}</p>` : '';
        elements.taskDetailContent.innerHTML = `
            <p><strong>Name:</strong> ${escapeHtml(task.name)}</p>
            ${descriptionHtml}
            ${deadlineHtml}
            <p><strong>Priority:</strong> <span class="priority-${task.priority}">${task.priority.charAt(0).toUpperCase() + task.priority.slice(1)}</span></p>
            <p><strong>Status:</strong> ${task.status.charAt(0).toUpperCase() + task.status.slice(1)}</p>
            <p><strong>Created:</strong> ${formatDisplayDate(task.created_at)}</p>
            <p><strong>Started:</strong> ${formatDisplayDate(task.started_at)}</p>
            <p><strong>Completed:</strong> ${formatDisplayDate(task.completed_at)}</p>
        `;
        elements.taskDetailModal.classList.remove('hidden');
    }

    // Show add task modal
    function showAddTaskModal() {
        elements.taskNameInput.value = '';
        elements.taskDescriptionInput.value = '';
        elements.taskDeadlineInput.value = '';
        elements.taskPrioritySelect.value = 'medium';
        elements.addTaskModal.classList.remove('hidden');
        elements.taskNameInput.focus();
    }

    // Hide add task modal
    function hideAddTaskModal() {
        elements.addTaskModal.classList.add('hidden');
    }

    // Show edit task modal
    function showEditTaskModal() {
        const task = tasks.find(t => t.id === selectedTaskId);
        if (!task) return;

        elements.editTaskNameInput.value = task.name;
        elements.editTaskDescriptionInput.value = task.description || '';
        elements.editTaskDeadlineInput.value = task.deadline || '';
        elements.editTaskPrioritySelect.value = task.priority;
        elements.editTaskModal.classList.remove('hidden');
        elements.editTaskNameInput.focus();
    }

    // Hide edit task modal
    function hideEditTaskModal() {
        elements.editTaskModal.classList.add('hidden');
    }

    // Apply filter
    function applyFilter() {
        const startValue = elements.filterStart.value;
        const endValue = elements.filterEnd.value;

        currentFilter.start = startValue ? new Date(startValue) : null;
        currentFilter.end = endValue ? new Date(endValue) : null;

        renderTasks();
    }

    // Clear filter
    function clearFilter() {
        elements.filterStart.value = '';
        elements.filterEnd.value = '';
        currentFilter.start = null;
        currentFilter.end = null;
        renderTasks();
    }

    // Bind events
    function bindEvents() {
        // Add task button
        elements.addTaskBtn.addEventListener('click', showAddTaskModal);

        // Add task form
        elements.addTaskForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const name = elements.taskNameInput.value.trim();
            const description = elements.taskDescriptionInput.value.trim();
            const deadline = elements.taskDeadlineInput.value;
            const priority = elements.taskPrioritySelect.value;
            if (name) {
                createTask(name, description, deadline, priority);
                hideAddTaskModal();
            }
        });

        // Cancel add
        elements.cancelAddBtn.addEventListener('click', hideAddTaskModal);

        // Close detail modal
        elements.closeDetailBtn.addEventListener('click', () => {
            elements.taskDetailModal.classList.add('hidden');
        });

        // Edit task
        elements.editTaskBtn.addEventListener('click', () => {
            elements.taskDetailModal.classList.add('hidden');
            showEditTaskModal();
        });

        // Edit task form
        elements.editTaskForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const name = elements.editTaskNameInput.value.trim();
            const description = elements.editTaskDescriptionInput.value.trim();
            const deadline = elements.editTaskDeadlineInput.value;
            const priority = elements.editTaskPrioritySelect.value;
            if (name && selectedTaskId) {
                updateTask(selectedTaskId, {
                    name: name,
                    description: description,
                    deadline: deadline || null,
                    priority: priority,
                    color: DEFAULT_PRIORITY_COLORS[priority]
                });
                hideEditTaskModal();
                // Re-show details with updated info
                const task = tasks.find(t => t.id === selectedTaskId);
                if (task) showTaskDetails(task);
            }
        });

        // Cancel edit
        elements.cancelEditBtn.addEventListener('click', hideEditTaskModal);

        // Delete task
        elements.deleteTaskBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to delete this task?')) {
                deleteTask(selectedTaskId);
                elements.taskDetailModal.classList.add('hidden');
            }
        });

        // Filter controls
        elements.filterStart.addEventListener('change', applyFilter);
        elements.filterEnd.addEventListener('change', applyFilter);
        elements.clearFilterBtn.addEventListener('click', clearFilter);

        // Drag and drop for columns
        document.querySelectorAll('.column').forEach(column => {
            column.addEventListener('dragover', handleDragOver);
            column.addEventListener('dragenter', handleDragEnter);
            column.addEventListener('dragleave', handleDragLeave);
            column.addEventListener('drop', handleDrop);
        });

        // Close modals on outside click
        [elements.addTaskModal, elements.taskDetailModal, elements.editTaskModal].forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.add('hidden');
                }
            });
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                elements.addTaskModal.classList.add('hidden');
                elements.taskDetailModal.classList.add('hidden');
                elements.editTaskModal.classList.add('hidden');
            }
        });
    }

    // Start the app
    document.addEventListener('DOMContentLoaded', init);
})();