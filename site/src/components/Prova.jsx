const provas = [
  {
    titulo: '15 mil exemplares',
    texto: 'testados em produção, sem engasgar',
    icone: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253',
  },
  {
    titulo: 'Trava contra duplicidade',
    texto: 'nenhum empréstimo duplo passa batido',
    icone: 'M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z',
  },
  {
    titulo: '100% aberto',
    texto: 'código, manual e documentação, sem letra miúda',
    icone: 'M8 9l-3 3 3 3m8-6l3 3-3 3M13 5l-2 14',
  },
]

export default function Prova() {
  return (
    <section className="py-20 px-4 bg-white">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-10">
          <span className="inline-block text-xs font-bold tracking-[0.2em] text-[#2E75B6] uppercase mb-3">
            Em produção
          </span>
          <h2 className="text-2xl sm:text-4xl font-bold text-gray-900 leading-snug">
            Não é uma demonstração.
          </h2>
          <p className="text-gray-500 text-lg mt-2">
            É uso real, todo dia, pela bibliotecária do CEFE.
          </p>
        </div>

        <div className="bg-gradient-to-br from-[#1F4E79] to-[#2E75B6] text-white rounded-3xl p-8 sm:p-12 mb-8 flex flex-col sm:flex-row items-center justify-center gap-5 sm:gap-10 text-center">
          <div>
            <div className="text-xs uppercase tracking-wider text-blue-200 mb-1">achar um livro, antes</div>
            <div className="text-3xl sm:text-4xl font-bold text-blue-200/50 line-through decoration-2">minutos</div>
          </div>
          <svg className="w-7 h-7 text-yellow-300 rotate-90 sm:rotate-0 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
          </svg>
          <div>
            <div className="text-xs uppercase tracking-wider text-blue-200 mb-1">achar um livro, agora</div>
            <div className="text-3xl sm:text-4xl font-bold text-yellow-300">segundos</div>
          </div>
        </div>

        <div className="grid sm:grid-cols-3 gap-4 mb-8">
          {provas.map((p) => (
            <div key={p.titulo} className="flex items-start gap-3 bg-gray-50 rounded-xl p-5 border border-gray-100">
              <svg className="w-5 h-5 text-[#2E75B6] shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={p.icone} />
              </svg>
              <div>
                <div className="font-bold text-gray-900 text-sm">{p.titulo}</div>
                <div className="text-gray-500 text-sm">{p.texto}</div>
              </div>
            </div>
          ))}
        </div>

        <p className="text-center text-gray-500 text-sm mb-10">
          Na versão <span className="font-semibold text-gray-700">1.4.0</span> (jul/2026): importação de
          acervo por planilha, etiquetas em massa e cartão de biblioteca do aluno.
        </p>

        <figure className="bg-blue-50 border-l-4 border-[#2E75B6] rounded-xl p-6 sm:p-8">
          <blockquote className="text-gray-700 text-lg sm:text-xl italic leading-relaxed mb-4">
            "Antes eu levava 15 minutos pra achar um livro. Agora levo 5 segundos."
          </blockquote>
          <figcaption className="text-[#1F4E79] font-semibold">
            Jaqueline Dantas, bibliotecária do CEFE
          </figcaption>
        </figure>
      </div>
    </section>
  )
}
