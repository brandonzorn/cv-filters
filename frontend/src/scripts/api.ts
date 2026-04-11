import axios from "axios";
import type { ImageResponse } from "./models";

const API_BASE = "http://localhost:8000";

const api = axios.create({
    baseURL: API_BASE,
});

export async function getImages(signal?: AbortSignal): Promise<ImageResponse[]> {
    const response = await api.get<ImageResponse[]>("/images/", { signal });

    if (response.status !== 200) {
        throw new Error(`API getImages error: HTTP ${response.status}`);
    }
    return response.data.map(img => ({
        ...img,
        original_url: img.original_url.startsWith('http')
            ? img.original_url
            : `${API_BASE}${img.original_url}`,
        processed_url: img.processed_url.startsWith('http')
            ? img.processed_url
            : `${API_BASE}${img.processed_url}`
    }));
}

export async function postImage(file: File, filterType: string) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('filter_type', filterType);

    const response = await api.post("/images/upload", formData);
    if (response.status !== 201) {
        throw new Error(`API postImage error: HTTP ${response.status}`);
    }
}

export async function getApiStatus(): Promise<string> {
    const response = await api.get("/");
     if (response.status !== 200) {
        throw new Error(`API getApiStatus error: HTTP ${response.status}`);
    }
    return response.data.status;
}