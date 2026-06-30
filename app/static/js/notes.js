// Notes management
const Notes = {
    async init() {
        await this.load();
        this.initAddNote();
        this.initFilters();
        this.initExport();
    },

    async load() {
        const params = new URLSearchParams();
        const tagFilter = Tags.getFilterString();
        if (tagFilter) params.set('tags', tagFilter);

        const search = document.getElementById('note-search').value.trim();
        if (search) params.set('q', search);

        const from = document.getElementById('note-from').value;
        if (from) params.set('from', from);

        const to = document.getElementById('note-to').value;
        if (to) params.set('to', to);

        const url = '/api/notes' + (params.toString() ? '?' + params.toString() : '');
        const days = await API.get(url);
        this.render(days);
    },

    render(days) {
        const container = document.getElementById('notes-stream');
        if (!days.length) {
            container.innerHTML = '<p class="empty-state">No notes yet — write the first one.</p>';
            return;
        }

        container.innerHTML = days.map(day => `
            <div class="day-group">
                <h3 class="day-heading">${day.date}</h3>
                ${day.notes.map(note => this.renderNote(note)).join('')}
            </div>
        `).join('');

        container.querySelectorAll('.btn-delete-note').forEach(btn => {
            btn.addEventListener('click', async () => {
                await API.del(`/api/notes/${btn.dataset.id}`);
                await this.load();
                Tags.load();
            });
        });
    },

    renderNote(note) {
        const time = note.created_at.substring(11, 16);
        const tagsHtml = note.tags.length ? `<div class="note-tags">${Tags.renderChips(note.tags)}</div>` : '';
        return `
            <div class="note-entry" data-id="${note.id}">
                <span class="note-time">[${time}]</span>
                <div class="note-content">
                    <div class="note-body">${this.escapeHtml(note.body)}</div>
                    ${tagsHtml}
                </div>
                <div class="note-actions">
                    <button class="btn-sm danger btn-delete-note" data-id="${note.id}">×</button>
                </div>
            </div>
        `;
    },

    initAddNote() {
        document.getElementById('btn-add-note').addEventListener('click', async () => {
            const textarea = document.getElementById('note-body');
            const text = textarea.value.trim();
            if (!text) return;

            const { body, tags } = Tags.parseInline(text);
            await API.post('/api/notes', { body, tags });
            textarea.value = '';
            await this.load();
            Tags.load();
        });

        document.getElementById('note-body').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                document.getElementById('btn-add-note').click();
            }
        });
    },

    initFilters() {
        let debounce;
        document.getElementById('note-search').addEventListener('input', () => {
            clearTimeout(debounce);
            debounce = setTimeout(() => this.load(), 300);
        });
        document.getElementById('note-from').addEventListener('change', () => this.load());
        document.getElementById('note-to').addEventListener('change', () => this.load());
    },

    initExport() {
        document.getElementById('btn-export').addEventListener('click', () => {
            const params = new URLSearchParams();
            const tagFilter = Tags.getFilterString();
            if (tagFilter) params.set('tags', tagFilter);

            const search = document.getElementById('note-search').value.trim();
            if (search) params.set('q', search);

            const from = document.getElementById('note-from').value;
            if (from) params.set('from', from);

            const to = document.getElementById('note-to').value;
            if (to) params.set('to', to);

            params.set('format', 'txt');
            window.location.href = '/api/notes/export?' + params.toString();
        });
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Layout management
const Layout = {
    init() {
        const main = document.querySelector('.app-main');
        const tabs = document.querySelectorAll('.tab-btn');
        const toggle = document.getElementById('toggle-layout');

        // Check saved preference
        const pref = localStorage.getItem('miwork-layout');
        if (pref === 'tabs') {
            main.classList.add('tabbed');
            document.querySelector('.view-tabs').style.display = 'flex';
        }

        // Default to board active on narrow
        const boardPanel = document.getElementById('board-panel');
        const logPanel = document.getElementById('log-panel');
        boardPanel.classList.add('active');

        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                if (tab.dataset.view === 'board') {
                    boardPanel.classList.add('active');
                    logPanel.classList.remove('active');
                } else {
                    logPanel.classList.add('active');
                    boardPanel.classList.remove('active');
                }
            });
        });

        toggle.addEventListener('click', () => {
            if (main.classList.contains('tabbed') || main.classList.contains('force-tabs')) {
                main.classList.remove('tabbed', 'force-tabs');
                document.querySelector('.view-tabs').style.display = '';
                localStorage.removeItem('miwork-layout');
            } else {
                main.classList.add('force-tabs');
                document.querySelector('.view-tabs').style.display = 'flex';
                localStorage.setItem('miwork-layout', 'tabs');
            }
        });

        // Auto-tab on narrow
        const mq = window.matchMedia('(max-width: 960px)');
        const handleWidth = (e) => {
            if (e.matches && !main.classList.contains('force-tabs')) {
                main.classList.add('tabbed');
            } else if (!main.classList.contains('force-tabs')) {
                main.classList.remove('tabbed');
            }
        };
        mq.addListener(handleWidth);
        handleWidth(mq);
    }
};

document.addEventListener('DOMContentLoaded', () => {
    Layout.init();
    Notes.init();
    Tags.load();
});
