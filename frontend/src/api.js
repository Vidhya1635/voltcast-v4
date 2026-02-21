import axios from 'axios';

const getBaseUrl = () => {
    // If we have a hardcoded production API URL, use it
    const prodUrl = 'https://voltcast-backend.onrender.com'; // Change this after deploying to Render

    if (import.meta.env.PROD) return prodUrl;

    const isTunnel = window.location.hostname.includes('localtunnel.me') || window.location.hostname.includes('loca.lt');
    return isTunnel ? 'https://empty-plants-judge.loca.lt' : `http://${window.location.hostname}:5000`;
};

const api = axios.create({
    baseURL: getBaseUrl()
});

export default api;
