import { matchPath } from 'react-router-dom'
import type { PageContext, PageView } from './types'

const VIEWS: Record<string, PageView> = {
  '/': 'home',
  '/products': 'products',
  '/about': 'about',
  '/login': 'login',
  '/register': 'register',
}

/**
 * What the chat tells the server about the page the shopper is on. On a product page that is
 * the product id; the server looks the product up itself, so nothing else is sent about it.
 */
export function pageContextFor(pathname: string): PageContext {
  const product = matchPath('/products/:productId', pathname)
  if (product?.params.productId) {
    return { view: 'product', path: pathname, product_id: product.params.productId }
  }
  return { view: VIEWS[pathname] ?? 'other', path: pathname }
}
