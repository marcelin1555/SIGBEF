import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { lazy, Suspense, useEffect } from 'react'
import Nav from './components/Nav'
import Footer from './components/Footer'
import BotaoWhatsApp from './components/BotaoWhatsApp'
import Home from './pages/Home'

// As páginas internas só são baixadas quando alguém abre cada uma,
// assim a página inicial carrega mais rápido.
const FuncionalidadesPage = lazy(() => import('./pages/FuncionalidadesPage'))
const DownloadPage = lazy(() => import('./pages/DownloadPage'))
const PlanosPage = lazy(() => import('./pages/PlanosPage'))
const EquipePage = lazy(() => import('./pages/EquipePage'))
const NovidadesPage = lazy(() => import('./pages/NovidadesPage'))
const EventosPage = lazy(() => import('./pages/EventosPage'))

const TITULO_PADRAO = 'SIGBEF — Biblioteca escolar gratuita, offline e código aberto'

// Título da aba e descrição de cada página (aparecem no Google e ao compartilhar o link).
const PAGINAS = {
  '/': { titulo: TITULO_PADRAO },
  '/funcionalidades': { titulo: 'Funcionalidades', descricao: 'O que o SIGBEF faz no computador da biblioteca, no terminal de autoatendimento e no celular do aluno.' },
  '/download': { titulo: 'Como instalar', descricao: 'Baixe e instale o SIGBEF de graça no Windows, Linux ou macOS, sem servidor e sem internet.' },
  '/planos': { titulo: 'Planos', descricao: 'O SIGBEF é gratuito. Implantação assistida e suporte mensal são opcionais.' },
  '/equipe': { titulo: 'Equipe', descricao: 'Estudantes do CEFE, escola pública de Jardim do Seridó/RN, que criaram o SIGBEF.' },
  '/eventos': { titulo: 'Eventos', descricao: 'Feiras, seminários e premiações em que o SIGBEF esteve.' },
  '/novidades': { titulo: 'Novidades', descricao: 'Tudo que mudou no SIGBEF, versão por versão.' },
}

function AoTrocarDePagina() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo(0, 0)
    const pagina = PAGINAS[pathname] || PAGINAS['/']
    document.title = pathname === '/' ? pagina.titulo : `${pagina.titulo} · SIGBEF`
    const meta = document.querySelector('meta[name="description"]')
    if (meta) {
      meta.dataset.padrao ??= meta.content
      meta.content = pagina.descricao || meta.dataset.padrao
    }
  }, [pathname])
  return null
}

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <a href="#conteudo"
        className="sr-only focus:not-sr-only focus:absolute focus:z-[60] focus:top-2 focus:left-2 focus:bg-white focus:text-dark focus:font-semibold focus:px-4 focus:py-2 focus:rounded-lg focus:shadow-lg">
        Pular para o conteúdo
      </a>
      <Nav />
      <AoTrocarDePagina />
      <main id="conteudo" className="flex-1">
        <Suspense fallback={<div className="min-h-[60vh]" aria-busy="true" />}>
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
        </Suspense>
      </main>
      <Footer />
      <BotaoWhatsApp />
    </div>
  )
}
