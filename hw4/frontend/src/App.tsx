import { Route, Routes } from 'react-router-dom'
import Navbar from './components/Navbar'
import ChatWidget from './components/ChatWidget'
import ChatResults from './components/ChatResults'
import Backdrop from './components/Backdrop'
import Footer from './components/Footer'
import Ticker from './components/Ticker'
import Home from './pages/Home'
import Products from './pages/Products'
import ProductDetail from './pages/ProductDetail'
import About from './pages/About'
import AuthPage from './pages/AuthPage'

export default function App() {
  return (
    <>
      <Backdrop />
      <Navbar />
      <Ticker />
      <main className="page">
        <ChatResults />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<Products />} />
          <Route path="/products/:productId" element={<ProductDetail />} />
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<AuthPage mode="login" />} />
          <Route path="/register" element={<AuthPage mode="register" />} />
          <Route path="*" element={<p className="status">Page not found.</p>} />
        </Routes>
      </main>
      <Footer />
      <ChatWidget />
    </>
  )
}
