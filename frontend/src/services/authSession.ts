const ACCESS_TOKEN_KEY = 'auth_token';

let refreshPromise: Promise<string | null> | null = null;

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function clearAccessToken(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem('auth_user');
  localStorage.removeItem('patient_id');
}

export async function refreshAccessToken(baseUrl: string): Promise<string | null> {
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    try {
      const response = await fetch(`${baseUrl}/auth/refresh`, {
        method: 'POST',
        credentials: 'include',
        headers: { Accept: 'application/json' },
      });
      if (!response.ok) {
        clearAccessToken();
        return null;
      }

      const body = await response.json() as { access_token?: string };
      if (!body.access_token) {
        clearAccessToken();
        return null;
      }
      localStorage.setItem(ACCESS_TOKEN_KEY, body.access_token);
      return body.access_token;
    } catch {
      return null;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

export async function endSession(baseUrl: string): Promise<void> {
  clearAccessToken();
  if (!baseUrl) return;
  await fetch(`${baseUrl}/auth/logout`, {
    method: 'POST',
    credentials: 'include',
  }).catch(() => undefined);
}
