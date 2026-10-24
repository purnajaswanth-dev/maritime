/**
 * API client for Where Is My Ferry?
 * Handles in-memory JWT access tokens, automatic silent refresh on 401 via HttpOnly cookie,
 * request queuing during token renewal, and RFC 7807 problem details parsing.
 */

const rawBase = import.meta.env.VITE_API_BASE_URL || '/api/v1';
const BASE_URL = rawBase.endsWith('/api/v1') ? rawBase : `${rawBase.replace(/\/$/, '')}/api/v1`;

export interface ProblemDetails {
  type?: string;
  title?: string;
  status?: number;
  detail?: string;
  instance?: string;
  errors?: Record<string, string[]>;
  [key: string]: unknown;
}

export class ApiError extends Error {
  status: number;
  problemDetails?: ProblemDetails;

  constructor(message: string, status: number, problemDetails?: ProblemDetails) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.problemDetails = problemDetails;
  }
}

// In-memory access token (not persisted in localStorage per security specification)
let memoryAccessToken: string | null = null;
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string | null) => void;
  reject: (err: any) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

export const setAccessToken = (token: string | null) => {
  memoryAccessToken = token;
};

export const getAccessToken = (): string | null => {
  return memoryAccessToken;
};

export const clearAuthSession = () => {
  memoryAccessToken = null;
};

/**
 * Attempts silent token refresh using the HttpOnly cookie.
 */
export async function refreshAuthToken(): Promise<string | null> {
  try {
    const response = await fetch(`${BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // passes HttpOnly refreshToken cookie
    });

    if (!response.ok) {
      clearAuthSession();
      return null;
    }

    const data = await response.json();
    if (data.accessToken) {
      setAccessToken(data.accessToken);
      return data.accessToken;
    }
    return null;
  } catch {
    clearAuthSession();
    return null;
  }
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const cleanEndpoint = endpoint.startsWith('/api/v1') ? endpoint.replace(/^\/api\/v1/, '') : endpoint;
  const url = endpoint.startsWith('http') ? endpoint : `${BASE_URL}${cleanEndpoint.startsWith('/') ? cleanEndpoint : `/${cleanEndpoint}`}`;
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (memoryAccessToken) {
    headers['Authorization'] = `Bearer ${memoryAccessToken}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include',
  });

  // Handle 401 Unauthorized with automatic refresh attempt
  const isAuthRoute = endpoint.includes('/auth/login') ||
                       endpoint.includes('/auth/register') ||
                       endpoint.includes('/auth/refresh') ||
                       endpoint.includes('/auth/forgot-password') ||
                       endpoint.includes('/auth/reset-password');

  if (response.status === 401 && !isAuthRoute) {
    if (isRefreshing) {
      return new Promise<string | null>((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      }).then((token) => {
        if (!token) {
          throw new ApiError('Session expired. Please log in again.', 401);
        }
        headers['Authorization'] = `Bearer ${token}`;
        return apiClient<T>(endpoint, { ...options, headers });
      });
    }

    isRefreshing = true;

    try {
      const newToken = await refreshAuthToken();
      isRefreshing = false;

      if (newToken) {
        processQueue(null, newToken);
        headers['Authorization'] = `Bearer ${newToken}`;
        return apiClient<T>(endpoint, { ...options, headers });
      } else {
        processQueue(new ApiError('Session expired. Please log in again.', 401), null);
        throw new ApiError('Session expired. Please log in again.', 401);
      }
    } catch (refreshErr) {
      isRefreshing = false;
      processQueue(refreshErr, null);
      throw refreshErr;
    }
  }

  if (!response.ok) {
    let errorData: ProblemDetails | undefined;
    try {
      errorData = await response.json();
    } catch {
      // not JSON
    }

    const message =
      errorData?.detail ||
      errorData?.title ||
      `HTTP Error ${response.status}: ${response.statusText}`;

    throw new ApiError(message, response.status, errorData);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

apiClient.get = function <T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  return apiClient<T>(endpoint, { ...options, method: 'GET' });
};

apiClient.post = function <T>(endpoint: string, body?: any, options: RequestInit = {}): Promise<T> {
  return apiClient<T>(endpoint, {
    ...options,
    method: 'POST',
    body: body !== undefined ? (typeof body === 'string' ? body : JSON.stringify(body)) : undefined,
  });
};

apiClient.put = function <T>(endpoint: string, body?: any, options: RequestInit = {}): Promise<T> {
  return apiClient<T>(endpoint, {
    ...options,
    method: 'PUT',
    body: body !== undefined ? (typeof body === 'string' ? body : JSON.stringify(body)) : undefined,
  });
};

apiClient.patch = function <T>(endpoint: string, body?: any, options: RequestInit = {}): Promise<T> {
  return apiClient<T>(endpoint, {
    ...options,
    method: 'PATCH',
    body: body !== undefined ? (typeof body === 'string' ? body : JSON.stringify(body)) : undefined,
  });
};

apiClient.delete = function <T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  return apiClient<T>(endpoint, { ...options, method: 'DELETE' });
};
