export const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type JsonBody = Record<string, unknown> | null;

export async function fetchJson<T>(
  path: string,
  init?: {
    method?: "GET" | "POST" | "PUT";
    body?: JsonBody;
  }
): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method: init?.method ?? "GET",
    headers: {
      "Content-Type": "application/json"
    },
    body: init?.body ? JSON.stringify(init.body) : undefined
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;

    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      // Ignore JSON parse failures and keep the fallback message.
    }

    throw new Error(detail);
  }

  return (await response.json()) as T;
}
