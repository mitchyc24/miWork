// Tag management
const Tags = {
    activeTags: new Set(),

    async load() {
        const tags = await API.get('/api/tags');
        this.render(tags);
    },

    render(tags) {
        const container = document.getElementById('tag-filter');
        if (!tags.length) {
            container.innerHTML = '';
            return;
        }
        container.innerHTML = tags.map(tag => `
            <span class="tag-chip tag-chip-filter ${this.activeTags.has(tag.name) ? 'active' : ''}"
                  style="background:${tag.color}"
                  data-tag="${tag.name}">
                #${tag.name}<span class="tag-count">${tag.usage_count}</span>
            </span>
        `).join('');

        container.querySelectorAll('.tag-chip-filter').forEach(chip => {
            chip.addEventListener('click', () => {
                const name = chip.dataset.tag;
                if (this.activeTags.has(name)) {
                    this.activeTags.delete(name);
                    chip.classList.remove('active');
                } else {
                    this.activeTags.add(name);
                    chip.classList.add('active');
                }
                Notes.load();
            });
        });
    },

    getFilterString() {
        return this.activeTags.size ? Array.from(this.activeTags).join(',') : null;
    },

    renderChips(tags) {
        return tags.map(t =>
            `<span class="tag-chip" style="background:${t.color}">#${t.name}</span>`
        ).join('');
    },

    parseInline(text) {
        const tags = [];
        const body = text.replace(/#(\w[\w-]*)/g, (match, name) => {
            tags.push(name);
            return '';
        }).trim();
        return { body: body.length ? body : text, tags: tags.length ? tags : null };
    }
};
