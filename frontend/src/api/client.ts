/**
 * API client for Where Is My Ferry? Spring Boot Backend.
 * Handles JWT access tokens, automatic headers, and RFC 7807 problem details parsing.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export interface ProblemDetails {
  type?: string;
  title?: string;
  status?: number;
  detail?: string;
  instance?: string;
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

let accessToken: string | null = localStorage.getItem('wimf_access_token');

export const setAccessToken = (token: string | null) => {
  accessToken = token;
  if (token) {
    localStorage.setItem('wimf_access_token', token);
  } else {
    localStorage.removeitem ? localStorage.removeItem('wimf_access_token') : null;
  }
};

export const getAccessToken = (): string | null => {
  return accessToken;
};

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = endpoint.startsWith('http') ? endpoint : `${BASE_URL}${endpoint}`;
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include', // for HttpOnly refresh cookie
  });

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

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}
