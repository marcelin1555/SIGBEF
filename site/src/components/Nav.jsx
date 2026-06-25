import { useState } from 'react'
import { NavLink, Link } from 'react-router-dom'

const links = [
  { to: '/funcionalidades', label: 'Funcionalidades' },
  { to: '/download', label: 'Como instalar' },
  { to: '/planos', label: 'Planos' },
  { to: '/equipe', label: 'Equipe' },
]

export default function Nav() {
  const [open, setOpen] = useState(false)

  return (
    <nav className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 flex items-center justify-between h-16">
        <Link to="/" className="flex items-center gap-2" onClick={() => setOpen(false)}>
          <img src="/SIGBEF/logo.png" alt="SIGBEF" className="h-8 w-8 rounded" />
          <span className="font-bold text-xl text-[#1F4E79]">SIGBEF</span>
        </Link>

        <div className="hidden md:flex items-center gap-6 text-sm font-medium">
          {links.map(({ to, label }) => (
            <NavLink key={to} to={to}
              className={({ isActive }) =>
                isActive
                  ? 'text-[#2E75B6] font-semibold'
                  : 'text-gray-600 hover:text-[#2E75B6] transition-colors'
              }>
              {label}
            </NavLink>
          ))}
          <a href="https://github.com/marcelin1555/SIGBEF/releases" target="_blank" rel="noopener noreferrer"
            className="bg-[#2E75B6] text-white px-4 py-2 rounded-lg hover:bg-[#1F4E79] transition-colors">
            Baixar agora
          </a>
        </div>

        <button type="button" className="md:hidden p-2 rounded text-gray-600"
          onClick={() => setOpen(o => !o)} aria-label="Menu">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            {open
              ? <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              : <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />}
          </svg>
        </button>
      </div>

      <div className={`md:hidden overflow-hidden transition-all duration-300 ease-in-out ${open ? 'max-h-72' : 'max-h-0'}`}>
        <div className="border-t border-gray-100 bg-white px-4 py-3 flex flex-col gap-1">
          {links.map(({ to, label }) => (
            <NavLink key={to} to={to} onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `px-2 py-2 rounded-lg text-sm font-medium ${isActive ? 'bg-blue-50 text-[#2E75B6] font-semibold' : 'text-gray-700 hover:bg-gray-50'}`
              }>
              {label}
            </NavLink>
          ))}
          <a href="https://github.com/marcelin1555/SIGBEF/releases" target="_blank" rel="noopener noreferrer"
            className="mt-2 bg-[#2E75B6] text-white px-4 py-2.5 rounded-lg text-center text-sm font-bold">
            Baixar agora
          </a>
        </div>
      </div>
    </nav>
  )
}
