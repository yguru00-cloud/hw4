import type { ChatHistoryMessage, ChatReply, ChatTurn, PageContext, Product, User } from './types'

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`Request failed (${res.status})`)
  return res.json() as Promise<T>
}

export const fetchProducts = () => getJson<Product[]>('/api/products')

export const fetchProduct = (id: string) =>
  getJson<Product>(`/api/products/${encodeURIComponent(id)}`)


// FastAPI returns `detail` as a string for HTTP errors and as a list of
// { msg } objects for validation errors.
async function errorMessage(res: Response): Promise<string> {
  try {
    const { detail } = await res.json()
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail) && detail.length > 0) {
      return String(detail[0].msg).replace(/^Value error, /, '')
    }
  } catch {
    // fall through to the generic message
  }
  return `Request failed (${res.status})`
}

async function postJson<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await errorMessage(res))
  return res.json() as Promise<T>
}

export interface RegisterInput {
  first_name: string
  last_name: string
  email: string
  password: string
}

export const registerUser = (input: RegisterInput) => postJson<User>('/api/register', input)

export const loginUser = (email: string, password: string) =>
  postJson<User>('/api/login', { email, password })

/** The logged-in user according to the server (from the session cookie), or null. */
export const fetchMe = () => getJson<User | null>('/api/me')

export async function logoutUser(): Promise<void> {
  await fetch('/api/logout', { method: 'POST' })
}

/** The logged-in customer's saved conversation. Fails with 401 for guests. */
export const fetchChatHistory = () => getJson<ChatHistoryMessage[]>('/api/chat/history')

export const sendChatMessage = (message: string, history: ChatTurn[], page: PageContext) =>
  postJson<ChatReply>('/api/chat', { message, history, page })
