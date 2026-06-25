const emprestimos = [
  { titulo: 'Dom Casmurro', aluno: 'Ana Silva', venc: '28/06', atrasado: false },
  { titulo: 'O Cortiço', aluno: 'João P.', venc: '22/06', atrasado: true },
  { titulo: 'Iracema', aluno: 'Maria L.', venc: '30/06', atrasado: false },
  { titulo: 'Macunaíma', aluno: 'Pedro J.', venc: '02/07', atrasado: false },
]

function AppMockup() {
  return (
    <div className="rounded-xl overflow-hidden shadow-2xl border border-white/20 text-xs font-mono select-none">
      {/* titlebar */}
      <div className="bg-gray-800 px-4 py-2.5 flex items-center gap-2">
        <span className="w-3 h-3 rounded-full bg-red-500 opacity-80" />
        <span className="w-3 h-3 rounded-full bg-yellow-400 opacity-80" />
        <span className="w-3 h-3 rounded-full bg-green-500 opacity-80" />
        <span className="ml-3 text-gray-400 text-[11px]">SIGBEF v1.2.0 — Painel da Biblioteca</span>
      </div>

      {/* search */}
      <div className="bg-gray-900 px-4 py-2.5 border-b border-gray-700">
        <div className="bg-gray-800 rounded px-3 py-1.5 text-gray-500 flex items-center gap-2">
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <span>Pesquisar por título ou autor...</span>
        </div>
      </div>

      {/* stats */}
      <div className="bg-gray-900 grid grid-cols-3 border-b border-gray-700">
        <div className="px-4 py-3 border-r border-gray-700">
          <div className="text-yellow-400 font-bold text-base">1.247</div>
          <div className="text-gray-500">livros</div>
        </div>
        <div className="px-4 py-3 border-r border-gray-700">
          <div className="text-blue-400 font-bold text-base">43</div>
          <div className="text-gray-500">empréstimos</div>
        </div>
        <div className="px-4 py-3">
          <div className="text-red-400 font-bold text-base">3</div>
          <div className="text-gray-500">atrasados</div>
        </div>
      </div>

      {/* table header */}
      <div className="bg-gray-800 grid grid-cols-4 px-4 py-2 text-gray-500 text-[10px] uppercase tracking-wider">
        <span>Título</span><span>Aluno</span><span>Vencimento</span><span>Status</span>
      </div>

      {/* rows */}
      {emprestimos.map(({ titulo, aluno, venc, atrasado }, i) => (
        <div key={i} className={`grid grid-cols-4 px-4 py-2.5 border-t border-gray-800 ${i % 2 === 0 ? 'bg-gray-900' : 'bg-gray-850'}`}
          style={{ background: i % 2 === 0 ? '#111827' : '#0f172a' }}>
          <span className="text-blue-300 truncate pr-1">{titulo}</span>
          <span className="text-gray-300">{aluno}</span>
          <span className="text-gray-400">{venc}</span>
          <span className={atrasado ? 'text-red-400 font-semibold' : 'text-green-400'}>
            {atrasado ? '⚠ atrasado' : '✓ ok'}
          </span>
        </div>
      ))}
    </div>
  )
}

export default function Hero() {
  return (
    <section id="inicio" className="bg-gradient-to-br from-[#1F4E79] to-[#2E75B6] text-white py-20 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="grid md:grid-cols-2 gap-12 items-center">

          {/* left: copy */}
          <div>
            <div className="flex flex-wrap gap-2 mb-6">
              {['MIT', 'Offline', 'Windows', 'v1.2.0'].map(b => (
                <span key={b} className="bg-white/20 text-white text-xs font-semibold px-3 py-1 rounded-full">{b}</span>
              ))}
            </div>

            <h1 className="text-4xl sm:text-5xl font-bold leading-tight mb-5">
              Biblioteca digital pra escola que{' '}
              <span className="text-yellow-300">não tem como pagar uma.</span>
            </h1>

            <p className="text-lg text-blue-100 mb-8 leading-relaxed">
              Sistema completo de gestão de biblioteca escolar, gratuito, offline e
              código aberto. Instala em 5 minutos em qualquer PC com Windows.
            </p>

            <div className="flex flex-col sm:flex-row gap-3">
              <a href="https://github.com/marcelin1555/SIGBEF/releases" target="_blank" rel="noopener noreferrer"
                className="bg-yellow-400 text-[#1F4E79] font-bold px-7 py-3.5 rounded-xl text-base hover:bg-yellow-300 transition-colors shadow-lg text-center">
                Baixar grátis
              </a>
              <a href="https://github.com/marcelin1555/SIGBEF" target="_blank" rel="noopener noreferrer"
                className="border-2 border-white/60 text-white font-semibold px-7 py-3.5 rounded-xl text-base hover:bg-white/10 transition-colors text-center">
                Ver no GitHub
              </a>
            </div>

            <p className="mt-5 text-blue-200 text-sm">Gratuito para sempre, para qualquer escola pública.</p>
          </div>

          {/* right: app mockup */}
          <div className="hidden md:block">
            <AppMockup />
          </div>
        </div>
      </div>
    </section>
  )
}
