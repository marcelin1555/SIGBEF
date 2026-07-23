import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { useEffect } from 'react'
import Nav from './components/Nav'
import Footer from './components/Footer'
import BotaoWhatsApp from './components/BotaoWhatsApp'
import Home from './pages/Home'
import FuncionalidadesPage from './pages/FuncionalidadesPage'
import DownloadPage from './pages/DownloadPage'
import PlanosPage from './pages/PlanosPage'
import EquipePage from './pages/EquipePage'
import NovidadesPage from './pages/NovidadesPage'
import EventosPage from './pages/EventosPage'

function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => { window.scrollTo(0, 0) }, [pathname])
  return null
}

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <a href="#conteudo"
        className="sr-only focus:not-sr-only focus:absolute focus:z-[60] focus:top-2 focus:left-2 focus:bg-white focus:text-[#1F4E79] focus:font-semibold focus:px-4 focus:py-2 focus:rounded-lg focus:shadow-lg">
        Pular para o conteúdo
      </a>
      <Nav />
      <ScrollToTop />
      <main id="conteudo" className="flex-1">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/funcionalidades" element={<FuncionalidadesPage />} />
          <Route path="/download" element={<DownloadPage />} />
          <Route path="/planos" element={<PlanosPage />} />
          <Route path="/equipe" element={<EquipePage />} />
          <Route path="/novidades" element={<NovidadesPage />} />
          <Route path="/eventos" element={<EventosPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <Footer />
      <BotaoWhatsApp />
    </div>
  )
}
