const Api = {
    async _fetch(url, options = {}) {
        const resp = await fetch(url, {
            headers: { 'Content-Type': 'application/json' },
            ...options,
        });
        if (!resp.ok) {
            throw new Error(`${resp.status}: ${await resp.text()}`);
        }
        return resp.json();
    },
};