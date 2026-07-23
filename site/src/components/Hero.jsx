import { VERSAO } from '../versao'

const emprestimos = [
  { titulo: 'Dom Casmurro', aluno: 'Ana Silva', venc: '28/06', atrasado: false },
  { titulo: 'O Cortiço', aluno: 'João P.', venc: '22/06', atrasado: true },
  { titulo: 'Iracema', aluno: 'Maria L.', venc: '30/06', atrasado: false },
  { titulo: 'Macunaíma', aluno: 'Pedro J.', venc: '02/07', atrasado: false },
]

const menuLateral = ['Painel inicial', 'Livros e exemplares', 'Usuários', 'Empréstimos abertos']

function AppMockup() {
  return (
    <div aria-hidden="true" className="rounded-xl overflow-hidden shadow-2xl select-none bg-white flex text-[13px]">
      {/* sidebar */}
      <div className="w-[132px] shrink-0 bg-[#1F4E79] py-4 hidden sm:block">
        <div className="px-4 pb-3 mb-2 border-b border-white/15">
          <span className="text-white font-bold text-sm tracking-wide">SIGBEF</span>
        </div>
        {menuLateral.map((item, i) => (
          <div key={item}
            className={`px-4 py-2 text-[11px] leading-snug ${i === 0 ? 'bg-[#2E75B6] text-white font-semibold' : 'text-blue-100'}`}>
            {item}
          </div>
        ))}
      </div>

      {/* conteúdo */}
      <div className="flex-1 min-w-0">
        {/* titlebar */}
        <div className="bg-[#F5F7FA] px-4 py-2.5 flex items-center gap-2 border-b border-gray-200">
          <span className="w-2.5 h-2.5 rounded-full bg-red-400" />
          <span className="w-2.5 h-2.5 rounded-full bg-yellow-400" />
          <span className="w-2.5 h-2.5 rounded-full bg-green-400" />
          <span className="ml-2 text-gray-400 text-[11px]">{`SIGBEF v${VERSAO} · Painel da Biblioteca`}</span>
        </div>

        <div className="bg-white px-4 pt-3 pb-1">
          {/* search */}
          <div className="bg-[#F5F7FA] border border-gray-200 rounded-lg px-3 py-1.5 text-gray-400 flex items-center gap-2 mb-3">
            <svg className="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <span className="truncate">Pesquisar por título ou autor…</span>
          </div>

          {/* stats */}
          <div className="grid grid-cols-3 gap-2 mb-3">
            {[
              ['1.247', 'livros', 'text-[#1F4E79]'],
              ['43', 'empréstimos', 'text-[#2E75B6]'],
              ['3', 'atrasados', 'text-red-500'],
            ].map(([num, lab, cor]) => (
              <div key={lab} className="bg-[#F5F7FA] border border-gray-200 rounded-lg px-3 py-2">
                <div className={`font-bold text-base ${cor}`}>{num}</div>
                <div className="text-gray-400 text-[10px]">{lab}</div>
              </div>
            ))}
          </div>
        </div>

        {/* tabela */}
        <div className="bg-[#1F4E79] grid grid-cols-[2.1fr_1.4fr_0.9fr_1fr] gap-1 px-4 py-2 text-blue-100 text-[10px] uppercase tracking-wider font-semibold">
          <span>Título</span><span>Aluno</span><span>Venc.</span><span className="text-right">Status</span>
        </div>
        {emprestimos.map(({ titulo, aluno, venc, atrasado }, i) => (
          <div key={titulo} className={`grid grid-cols-[2.1fr_1.4fr_0.9fr_1fr] gap-1 px-4 py-2 items-center ${i % 2 === 1 ? 'bg-[#F8FAFC]' : 'bg-white'}`}>
            <span className="text-[#2E75B6] font-medium truncate pr-1">{titulo}</span>
            <span className="text-gray-600 truncate pr-1">{aluno}</span>
            <span className="text-gray-500">{venc}</span>
            <span className="text-right">
              {atrasado
                ? <span className="text-red-600 bg-red-50 rounded-full px-2 py-0.5 text-[10px] font-semibold whitespace-nowrap">atrasado</span>
                : <span className="text-emerald-600 bg-emerald-50 rounded-full px-2 py-0.5 text-[10px] font-semibold whitespace-nowrap">✓ ok</span>}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function Hero() {
  return (
    <section id="inicio" className="bg-gradient-to-br from-[#1F4E79] to-[#2E75B6] text-white py-20 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="grid md:grid-cols-[1fr_1.15fr] gap-12 items-center">

          {/* left: copy */}
          <div>
            <div className="flex flex-wrap gap-2 mb-6">
              {['MIT', 'Offline', 'Multiplataforma', `v${VERSAO}`].map(b => (
                <span key={b} className="bg-white/20 text-white text-xs font-semibold px-3 py-1 rounded-full">{b}</span>
              ))}
            </div>

            <h1 className="text-4xl sm:text-5xl font-bold leading-tight mb-5">
              Biblioteca digital pra escola que{' '}
              <span className="text-yellow-300">não tem como pagar uma.</span>
            </h1>

            <p className="text-lg text-blue-100 mb-8 leading-relaxed">
              Sistema completo de gestão de biblioteca escolar, gratuito, offline e
              código aberto. Instala em 5 minutos em Windows, Linux ou macOS.
            </p>

            <div className="flex flex-col sm:flex-row gap-3">
              <a href="https://github.com/marcelin1555/SIGBEF/releases" target="_blank" rel="noopener noreferrer"
                className="bg-yellow-400 text-[#1F4E79] font-bold px-7 py-3.5 rounded-xl text-base hover:bg-yellow-300 active:scale-[0.98] transition shadow-lg text-center">
                Baixar grátis
              </a>
              <a href="https://github.com/marcelin1555/SIGBEF" target="_blank" rel="noopener noreferrer"
                className="border-2 border-white/60 text-white font-semibold px-7 py-3.5 rounded-xl text-base hover:bg-white/10 active:scale-[0.98] transition text-center">
                Ver no GitHub
              </a>
            </div>

            <p className="mt-5 text-blue-100 text-sm">Gratuito para sempre, para qualquer escola pública.</p>
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
