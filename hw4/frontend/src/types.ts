export interface SizeStock {
  size: string
  quantity: number
}

export interface Product {
  product_id: string
  name: string
  garment_type: string
  description: string
  colors: string[]
  search_tags: string[]
  image_url: string
  price: number
  inventory: SizeStock[]
  total_stock: number
  stock_status: StockStatus
  /** The shop section, such as "Hoodies" or "T-Shirts". */
  category: string
}

export interface ProductCard {
  product_id: string
  name: string
  price: number
  image_url: string
  summary: string
  garment_type: string
  colors: string[]
  sizes_in_stock: string[]
  in_stock: boolean
  total_stock: number
  /** The size the shopper asked about; stock_status is for it. Null when no size was asked. */
  size: string | null
  size_stock: number | null
  stock_status: StockStatus
}

export type StockStatus = 'in_stock' | 'low_stock' | 'out_of_stock'

/** One column of the comparison table: a card plus the product's full description. */
export interface ComparedProduct extends ProductCard {
  details: string
}

export interface ChatTurn {
  role: 'user' | 'assistant'
  content: string
}

export type PageView = 'home' | 'products' | 'product' | 'about' | 'login' | 'register' | 'other'

/** Where the shopper is in the site; sent with every chat message. */
export interface PageContext {
  view: PageView
  path: string
  product_id?: string
}

/** A saved message loaded for a logged-in customer. */
export interface ChatHistoryMessage extends ChatTurn {
  products: ProductCard[]
  comparison: ComparedProduct[]
  created_at: string
}

export interface ChatReply {
  reply: string
  products: ProductCard[]
  comparison: ComparedProduct[]
}

export interface User {
  id: number
  first_name: string | null
  last_name: string | null
  email: string
}
