// API wrapper module
const API = {
    async get(url) {
        const res = await fetch(url);
        if (!res.ok) throw new Error((await res.json()).error || res.statusText);
        return res.json();
    },

    async post(url, data) {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const json = await res.json();
        if (!res.ok) throw new Error(json.error || res.statusText);
        return json;
    },

    async patch(url, data) {
        const res = await fetch(url, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const json = await res.json();
        if (!res.ok) throw new Error(json.error || res.statusText);
        return json;
    },

    async del(url) {
        const res = await fetch(url, { method: 'DELETE' });
        const json = await res.json();
        if (!res.ok) throw new Error(json.error || res.statusText);
        return json;
    }
};
