export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const token = process.env.NEXT_PUBLIC_SCHOLARMIND_API_TOKEN;
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(token ? { "X-API-Key": token } : {}), ...(init?.headers ?? {}) },
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json() as Promise<T>;
}

export async function sse<T>(path: string, payload: unknown): Promise<T> {
  const token = process.env.NEXT_PUBLIC_SCHOLARMIND_API_TOKEN;
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(token ? { "X-API-Key": token } : {}) },
    body: JSON.stringify(payload),
  });
  if (!response.ok || !response.body) throw new Error(await response.text());
  const text = await response.text();
  const match = [...text.matchAll(/event: result\ndata: (.+)/g)].at(-1);
  if (!match) throw new Error("No result event returned by ScholarMind API");
  return JSON.parse(match[1]) as T;
}

export async function upload<T>(path: string, form: FormData): Promise<T> {
  const token = process.env.NEXT_PUBLIC_SCHOLARMIND_API_TOKEN;
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: token ? { "X-API-Key": token } : undefined,
    body: form,
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json() as Promise<T>;
}
