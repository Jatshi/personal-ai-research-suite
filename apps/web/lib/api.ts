export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

function reportError(message: string) {
  if (typeof window !== "undefined") window.dispatchEvent(new CustomEvent("scholarmind:toast", { detail: { kind: "error", message } }));
}

async function failure(response: Response): Promise<never> {
  const message = (await response.text()).slice(0, 500) || `Request failed (${response.status})`;
  reportError(message);
  throw new Error(message);
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const token = process.env.NEXT_PUBLIC_SCHOLARMIND_API_TOKEN;
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(token ? { "X-API-Key": token } : {}), ...(init?.headers ?? {}) },
  });
  if (!response.ok) return failure(response);
  return response.json() as Promise<T>;
}

export async function sse<T>(path: string, payload: unknown): Promise<T> {
  const token = process.env.NEXT_PUBLIC_SCHOLARMIND_API_TOKEN;
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(token ? { "X-API-Key": token } : {}) },
    body: JSON.stringify(payload),
  });
  if (!response.ok || !response.body) return failure(response);
  const text = await response.text();
  const match = [...text.matchAll(/event: result\ndata: (.+)/g)].at(-1);
  if (!match) { const message = "No result event returned by ScholarMind API"; reportError(message); throw new Error(message); }
  return JSON.parse(match[1]) as T;
}

export async function upload<T>(path: string, form: FormData): Promise<T> {
  const token = process.env.NEXT_PUBLIC_SCHOLARMIND_API_TOKEN;
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: token ? { "X-API-Key": token } : undefined,
    body: form,
  });
  if (!response.ok) return failure(response);
  return response.json() as Promise<T>;
}
