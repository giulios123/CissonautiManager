import { getLocale } from "./i18n/locale";
import { tNow } from "./i18n/messages";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

type FieldError = { loc?: unknown[]; msg?: string };

function messageFrom(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return (detail as FieldError[])
      .map((e) => e.msg?.replace(/^Value error, /, ""))
      .filter(Boolean)
      .join(". ");
  }
  return tNow("common.somethingWrong");
}

export async function api<T>(
  path: string,
  init: RequestInit & { json?: unknown } = {},
): Promise<T> {
  const { json, headers, ...rest } = init;
  const response = await fetch(path, {
    credentials: "same-origin",
    ...rest,
    headers: {
      "Accept-Language": getLocale(),
      ...(json !== undefined ? { "Content-Type": "application/json" } : {}),
      ...headers,
    },
    body: json !== undefined ? JSON.stringify(json) : rest.body,
  });
  if (response.status === 204) return undefined as T;
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(response.status, messageFrom(data?.detail));
  return data as T;
}
