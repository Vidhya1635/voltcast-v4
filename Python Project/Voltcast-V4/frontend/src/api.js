import axios from 'axios';

const getBaseUrl = () => {
    // 💡 FOR MENTOR DEMO: If you use a tunnel, paste the link here
    const tunnelUrl = '';

    if (tunnelUrl) return tunnelUrl;

    // In dev mode, point explicitly to Flask; in prod build, use same-origin (relative)
    if (import.meta.env.DEV) {
        return 'http://localhost:5000';
    }
    return '';  // Same-origin: Flask serves both frontend & API
};

const api = axios.create({
    baseURL: getBaseUrl()
});

export default api;
