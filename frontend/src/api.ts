import { getLocale } from "./i18n/locale";
import { tNow } from "./i18n/messages";

export class ApiError extends Error {
  status: number;
  code: string | null;

  constructor(status: number, message: string, code: string | null = null) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

type FieldError = { loc?: unknown[]; msg?: string };

function messageFrom(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (detail && typeof detail === "object" && "message" in detail) {
    const message = (detail as { message?: unknown }).message;
    if (typeof message === "string") return message;
  }
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
  if (!response.ok) {
    const code = typeof data?.detail?.code === "string" ? data.detail.code : null;
    if (
      response.status === 428 &&
      code === "privacy_acceptance_required" &&
      typeof window !== "undefined"
    ) {
      window.dispatchEvent(new Event("privacy-acceptance-required"));
    }
    throw new ApiError(response.status, messageFrom(data?.detail), code);
  }
  return data as T;
}
