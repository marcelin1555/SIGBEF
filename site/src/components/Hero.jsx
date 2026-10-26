import { VERSAO } from '../versao'
import { LINKS } from '../config'

export default function Hero() {
  return (
    <section id="inicio" className="bg-gradient-to-br from-dark to-primary text-white pt-16 pb-20 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="grid md:grid-cols-[1fr_1.2fr] gap-12 items-center">

          <div>
            <div className="flex flex-wrap gap-2 mb-6">
              {['Gratuito', 'Funciona sem internet', 'Código aberto', `v${VERSAO}`].map(b => (
                <span key={b} className="bg-white/15 text-white text-xs font-semibold px-3 py-1 rounded-full">{b}</span>
              ))}
            </div>

            <h1 className="text-4xl sm:text-5xl font-bold leading-tight mb-5">
              Sistema de biblioteca para a escola que{' '}
              <span className="text-ambar-claro">não pode pagar por um.</span>
            </h1>

            <p className="text-lg text-blue-100 mb-8 leading-relaxed">
              Cadastro do acervo, empréstimos, autoatendimento e aplicativo do aluno.
              Roda no computador que a escola já tem, sem servidor e sem mensalidade.
            </p>

            <div className="flex flex-col sm:flex-row gap-3">
              <a href={LINKS.download} target="_blank" rel="noopener noreferrer"
                className="bg-ambar text-dark font-bold px-7 py-3.5 rounded-xl text-base hover:bg-ambar-claro active:scale-[0.98] transition shadow-lg text-center">
                Baixar grátis
              </a>
              <a href="#veja-funcionando"
                className="border-2 border-white/60 text-white font-semibold px-7 py-3.5 rounded-xl text-base hover:bg-white/10 active:scale-[0.98] transition text-center">
                Ver o sistema
              </a>
            </div>

            <p className="mt-5 text-blue-100 text-sm">
              Feito por estudantes do CEFE, escola pública de Jardim do Seridó/RN.
            </p>
          </div>

          {/* Tela real do sistema, com o acervo da biblioteca do CEFE */}
          <figure className="rounded-xl overflow-hidden shadow-2xl ring-1 ring-white/20 bg-white">
            <div className="bg-fundo px-4 py-2 flex items-center gap-2 border-b border-gray-200" aria-hidden="true">
              <span className="w-2.5 h-2.5 rounded-full bg-red-400" />
              <span className="w-2.5 h-2.5 rounded-full bg-yellow-400" />
              <span className="w-2.5 h-2.5 rounded-full bg-green-400" />
              <span className="ml-2 text-gray-400 text-[11px]">{`SIGBEF v${VERSAO} · Livros e exemplares`}</span>
            </div>
            <img src="/telas/acervo.webp" width="1540" height="845" fetchPriority="high"
              alt="Tela de livros e exemplares do SIGBEF com o acervo real da biblioteca do CEFE"
              className="w-full h-auto" />
          </figure>
        </div>
      </div>
    </section>
  )
}
