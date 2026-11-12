import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("cityfix_access");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  if (config.data instanceof FormData) {
    delete config.headers["Content-Type"];
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = localStorage.getItem("cityfix_refresh");
      if (refresh) {
        try {
          const { data } = await axios.post(`${baseURL}/auth/refresh/`, { refresh });
          localStorage.setItem("cityfix_access", data.access);
          original.headers.Authorization = `Bearer ${data.access}`;
          return api(original);
        } catch {
          localStorage.removeItem("cityfix_access");
          localStorage.removeItem("cityfix_refresh");
          localStorage.removeItem("cityfix_user");
        }
      }
    }
    return Promise.reject(error);
  }
);
