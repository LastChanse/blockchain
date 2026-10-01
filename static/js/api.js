const CryptoModule = {
    async generateKeyPair() {
        return window.crypto.subtle.generateKey(
            { name: 'RSA-OAEP', modulusLength: 2048,
              publicExponent: new Uint8Array([1, 0, 1]), hash: 'SHA-256' },
            true, ['encrypt', 'decrypt']
        );
    },

    async exportPublicKey(publicKey) {
        const exported = await window.crypto.subtle.exportKey('spki', publicKey);
        return btoa(String.fromCharCode(...new Uint8Array(exported)));
    },

    async storePrivateKey(username, privateKey) {
        const exported = await window.crypto.subtle.exportKey('pkcs8', privateKey);
        const b64 = btoa(String.fromCharCode(...new Uint8Array(exported)));
        localStorage.setItem(`privkey:${username}`, b64);
    },
};