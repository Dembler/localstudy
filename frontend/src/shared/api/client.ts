export type QueryValue = string | number | boolean | readonly (string | number | boolean)[]

export interface ApiRequestOptions {
  signal?: AbortSignal
}

interface RequestConfig extends ApiRequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE'
  query?: object
  body?: unknown
}

export interface ApiErrorPayload {
  code: string
  message: string
  details: unknown
  request_id: string | null
}

interface ApiErrorOptions {
  status: number
  code: string
  details?: unknown
  requestId?: string | null
  cause?: unknown
}

const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim()

export const API_BASE_URL = configuredApiBaseUrl
  ? configuredApiBaseUrl.replace(/\/$/, '')
  : '/api/v1'

const API_ROOT_URL = configuredApiBaseUrl
  ? configuredApiBaseUrl.replace(/\/api\/v1\/?$/, '').replace(/\/$/, '')
  : ''

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly details: unknown
  readonly requestId: string | null

  constructor(message: string, options: ApiErrorOptions) {
    super(message, { cause: options.cause })
    this.name = 'ApiError'
    this.status = options.status
    this.code = options.code
    this.details = options.details
    this.requestId = options.requestId ?? null
  }
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function readString(record: Record<string, unknown>, key: string): string | undefined {
  const value = record[key]
  return typeof value === 'string' && value.length > 0 ? value : undefined
}

function serializeQuery(query?: object): string {
  if (!query) return ''

  const searchParams = new URLSearchParams()

  for (const [key, rawValue] of Object.entries(query)) {
    if (rawValue === undefined || rawValue === null || rawValue === '') continue

    const values = Array.isArray(rawValue) ? rawValue : [rawValue]
    for (const value of values) {
      searchParams.append(key, String(value))
    }
  }

  const serialized = searchParams.toString()
  return serialized ? `?${serialized}` : ''
}

function unwrapSuccess<T>(payload: unknown): T {
  if (isRecord(payload)) {
    if (Object.hasOwn(payload, 'data')) return payload.data as T
    if (Object.hasOwn(payload, 'result')) return payload.result as T
  }

  return payload as T
}

function normalizeErrorPayload(payload: unknown, status: number): ApiErrorPayload {
  const root = isRecord(payload) ? payload : {}
  const nestedError = isRecord(root.error) ? root.error : root
  const detail = root.detail ?? nestedError.detail
  const detailRecord = isRecord(detail) ? detail : undefined
  const message =
    readString(nestedError, 'message') ??
    readString(root, 'message') ??
    (detailRecord ? readString(detailRecord, 'message') : undefined) ??
    (typeof detail === 'string' ? detail : undefined) ??
    `Запрос завершился с ошибкой ${status}`

  return {
    code:
      readString(nestedError, 'code') ??
      readString(root, 'code') ??
      (status === 422 ? 'VALIDATION_ERROR' : `HTTP_${status}`),
    message,
    details: nestedError.details ?? root.details ?? detail ?? null,
    request_id: readString(nestedError, 'request_id') ?? readString(root, 'request_id') ?? null,
  }
}

async function readResponse(response: Response): Promise<unknown> {
  if (response.status === 204) return undefined

  const text = await response.text()
  if (!text) return undefined

  try {
    return JSON.parse(text) as unknown
  } catch {
    return text
  }
}

async function request<T>(baseUrl: string, path: string, config: RequestConfig = {}): Promise<T> {
  const requestInit: RequestInit = {
    method: config.method ?? 'GET',
    headers: {
      Accept: 'application/json',
      ...(config.body === undefined ? {} : { 'Content-Type': 'application/json' }),
    },
  }

  if (config.signal) requestInit.signal = config.signal
  if (config.body !== undefined) requestInit.body = JSON.stringify(config.body)

  try {
    const response = await fetch(`${baseUrl}${path}${serializeQuery(config.query)}`, requestInit)
    const payload = await readResponse(response)

    if (!response.ok) {
      const error = normalizeErrorPayload(payload, response.status)
      throw new ApiError(error.message, {
        status: response.status,
        code: error.code,
        details: error.details,
        requestId: error.request_id,
      })
    }

    return unwrapSuccess<T>(payload)
  } catch (error) {
    if (error instanceof ApiError) throw error

    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError('Запрос отменён', {
        status: 0,
        code: 'REQUEST_ABORTED',
        cause: error,
      })
    }

    throw new ApiError('Не удалось загрузить данные. Проверьте подключение и попробуйте ещё раз', {
      status: 0,
      code: 'NETWORK_ERROR',
      cause: error,
    })
  }
}

export function apiRequest<T>(path: string, config?: RequestConfig): Promise<T> {
  return request<T>(API_BASE_URL, path, config)
}

export function rootRequest<T>(path: string, config?: RequestConfig): Promise<T> {
  return request<T>(API_ROOT_URL, path, config)
}
