const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

async function request<T>(path: string, options: { method?: string; body?: unknown; token?: string } = {}): Promise<T> {
  const { method = 'GET', body, token } = options;
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  
  const res = await fetch(`${API_BASE}${path}`, { method, headers, body: body ? JSON.stringify(body) : undefined });
  if (!res.ok) throw new Error(`API Error ${res.status}`);
  return res.json();
}

export const authApi = {
  sendOtp: (phone: string) => request<{ otp: string }>('/auth/send-otp', { method: 'POST', body: { phone } }),
  verifyOtp: (phone: string, otp: string) => request<{ access_token: string }>('/auth/verify-otp', { method: 'POST', body: { phone, otp } }),
  authorityLogin: (email: string, password: string) => request<{ access_token: string }>('/auth/authority/login', { method: 'POST', body: { email, password } }),
};

export const feedApi = {
  list: () => request<unknown[]>('/feed/'),
  trending: () => request<unknown[]>('/feed/trending'),
  search: (q: string) => request<unknown[]>(`/feed/search?q=${encodeURIComponent(q)}`),
  nearby: (lat: number, lng: number, radius = 1000) => request<unknown[]>(`/feed/nearby?lat=${lat}&lng=${lng}&radius_meters=${radius}`),
  forYou: (token: string) => request<unknown[]>('/feed/for-you', { token }),
};

export const issuesApi = {
  get: (id: string) => request<unknown>(`/issues/${id}`),
  create: (data: unknown, token: string) => request<unknown>('/issues', { method: 'POST', body: data, token }),
  getTimeline: (id: string) => request<unknown[]>(`/issues/${id}/timeline`),
  getComments: (id: string) => request<unknown[]>(`/issues/${id}/comments`),
  addComment: (id: string, message_text: string, token: string) => request<unknown>(`/issues/${id}/comments`, { method: 'POST', body: { message_text }, token }),
  support: (id: string, token: string) => request<unknown>(`/issues/${id}/support`, { method: 'POST', token }),
  confirm: (id: string, token: string) => request<unknown>(`/issues/${id}/confirm`, { method: 'POST', token }),
  dispute: (id: string, token: string) => request<unknown>(`/issues/${id}/dispute`, { method: 'POST', token }),
  getMediaUrl: (id: string, token: string) => request<unknown>(`/issues/${id}/media/upload-url?media_type=complaint_photo&content_type=image/jpeg`, { method: 'POST', token }),
  generateNarrative: (id: string) => request<unknown>(`/issues/${id}/narrative`, { method: 'POST' }),
};

export const geoApi = {
  getCities: () => request<unknown[]>('/geo/cities'),
  getCityWards: (id: string) => request<unknown[]>(`/geo/cities/${id}/wards`),
};

export const meApi = {
  getIssues: (token: string) => request<unknown[]>('/me/issues', { token }),
  getComments: (token: string) => request<unknown[]>('/me/comments', { token }),
  getSupports: (token: string) => request<unknown[]>('/me/supports', { token }),
};

export const authorityApi = {
  getMe: (token: string) => request<unknown>('/authority/me', { token }),
  getDashboard: (token: string) => request<unknown>('/authority/dashboard', { token }),
  acknowledge: (id: string, token: string) => request<unknown>(`/issues/${id}/acknowledge`, { method: 'POST', token }),
  visit: (id: string, token: string) => request<unknown>(`/issues/${id}/visit`, { method: 'POST', token }),
  startWork: (id: string, token: string) => request<unknown>(`/issues/${id}/start-work`, { method: 'POST', token }),
  resolve: (id: string, token: string) => request<unknown>(`/issues/${id}/resolve`, { method: 'POST', token }),
};

export const chatApi = {
  ask: (issueId: string, question: string, token: string) => request<unknown>(`/chat/issue/${issueId}`, { method: 'POST', body: { question }, token }),
};