// Board management
const Board = {
    editingTask: null,

    async init() {
        await this.load();
        this.initSortable();
        this.initAddTask();
        this.initModal();
    },

    async load() {
        const board = await API.get('/api/board');
        this.renderColumn('todo', board.todo);
        this.renderColumn('doing', board.doing);
        this.renderColumn('done', board.done);
    },

    renderColumn(status, tasks) {
        const col = document.getElementById(`col-${status}`);
        if (!tasks.length) {
            col.innerHTML = '';
            return;
        }
        col.innerHTML = tasks.map(task => `
            <div class="task-card" data-id="${task.id}">
                <div class="task-card-title">${this.escapeHtml(task.title)}</div>
                ${task.tags.length ? `<div class="task-card-tags">${Tags.renderChips(task.tags)}</div>` : ''}
            </div>
        `).join('');

        col.querySelectorAll('.task-card').forEach(card => {
            card.addEventListener('dblclick', () => {
                this.openModal(parseInt(card.dataset.id));
            });
        });
    },

    initSortable() {
        ['todo', 'doing', 'done'].forEach(status => {
            const el = document.getElementById(`col-${status}`);
            if (typeof Sortable !== 'undefined') {
                Sortable.create(el, {
                    group: 'board',
                    animation: 150,
                    ghostClass: 'sortable-ghost',
                    onEnd: (evt) => {
                        const targetStatus = evt.to.id.replace('col-', '');
                        const ids = Array.from(evt.to.children).map(c => parseInt(c.dataset.id));
                        API.post('/api/tasks/reorder', { status: targetStatus, ordered_ids: ids });
                        Tags.load();
                    }
                });
            }
        });
    },

    initAddTask() {
        document.querySelectorAll('.add-task-input').forEach(input => {
            input.addEventListener('keydown', async (e) => {
                if (e.key === 'Enter' && input.value.trim()) {
                    const { body, tags } = Tags.parseInline(input.value.trim());
                    await API.post('/api/tasks', {
                        title: body,
                        status: input.dataset.status,
                        tags: tags
                    });
                    input.value = '';
                    await this.load();
                    Tags.load();
                }
            });
        });
    },

    initModal() {
        document.getElementById('modal-cancel').addEventListener('click', () => this.closeModal());
        document.getElementById('modal-save').addEventListener('click', () => this.saveModal());
        document.getElementById('modal-delete').addEventListener('click', () => this.deleteFromModal());
        document.getElementById('task-modal').addEventListener('click', (e) => {
            if (e.target === document.getElementById('task-modal')) this.closeModal();
        });
    },

    async openModal(taskId) {
        const task = await API.get(`/api/board`);
        let found = null;
        for (const col of ['todo', 'doing', 'done']) {
            found = task[col].find(t => t.id === taskId);
            if (found) break;
        }
        if (!found) return;

        this.editingTask = found;
        document.getElementById('modal-task-title').value = found.title;
        document.getElementById('modal-task-desc').value = found.description || '';
        document.getElementById('modal-task-tags').value = found.tags.map(t => t.name).join(', ');
        document.getElementById('task-modal').hidden = false;
    },

    closeModal() {
        document.getElementById('task-modal').hidden = true;
        this.editingTask = null;
    },

    async saveModal() {
        if (!this.editingTask) return;
        const title = document.getElementById('modal-task-title').value.trim();
        if (!title) return;

        const tagsStr = document.getElementById('modal-task-tags').value;
        const tags = tagsStr ? tagsStr.split(',').map(t => t.trim()).filter(Boolean) : [];

        await API.patch(`/api/tasks/${this.editingTask.id}`, {
            title: title,
            description: document.getElementById('modal-task-desc').value.trim() || null,
            tags: tags
        });

        this.closeModal();
        await this.load();
        Tags.load();
    },

    async deleteFromModal() {
        if (!this.editingTask) return;
        await API.del(`/api/tasks/${this.editingTask.id}`);
        this.closeModal();
        await this.load();
        Tags.load();
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

document.addEventListener('DOMContentLoaded', () => Board.init());
