const API_BASE = '';

export async function apiFetch(path, options = {}) {
  const token = localStorage.getItem('access_token');
  const headers = { ...options.headers };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  // Try refresh if token expired
  if (res.status === 401 && token) {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      const refreshRes = await fetch(`${API_BASE}/api/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (refreshRes.ok) {
        const data = await refreshRes.json();
        localStorage.setItem('access_token', data.access_token);
        headers['Authorization'] = `Bearer ${data.access_token}`;
        res = await fetch(`${API_BASE}${path}`, { ...options, headers });
      } else {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    } else {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
  }

  return res;
}
