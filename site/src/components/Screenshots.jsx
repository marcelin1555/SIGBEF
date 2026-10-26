const telas = [
  {
    src: '/screenshot-painel.webp', largura: 1600, altura: 825,
    alt: 'Painel do SIGBEF com as estatísticas do acervo do CEFE (2.867 títulos, 4.728 exemplares, 4.696 disponíveis), empréstimos, atrasos e os livros mais emprestados',
    legenda: 'Painel da bibliotecária: acervo, empréstimos e atrasos numa tela só.',
  },
  {
    src: '/telas/autoatendimento.webp', largura: 1040, altura: 720,
    alt: 'Terminal de autoatendimento do SIGBEF com os botões Pegar emprestado, Devolver e Meus empréstimos',
    legenda: 'Autoatendimento: o aluno pega e devolve o livro sozinho.',
  },
]

export default function Screenshots() {
  return (
    <section id="veja-funcionando" className="py-20 px-4 bg-gray-50 scroll-mt-16">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <p className="text-primary text-sm font-semibold uppercase tracking-widest mb-3">Veja funcionando</p>
          <h2 className="text-3xl sm:text-4xl font-bold text-dark mb-3">Telas reais do sistema</h2>
          <p className="text-gray-500 text-lg">Capturadas no computador da biblioteca do CEFE, sem montagem.</p>
        </div>

        <div className="grid lg:grid-cols-[1.55fr_1fr] gap-6 items-start">
          {telas.map(t => (
            <figure key={t.src}>
              <div className="rounded-2xl overflow-hidden shadow-xl border border-gray-200 bg-white">
                <img src={t.src} width={t.largura} height={t.altura} loading="lazy" alt={t.alt} className="w-full h-auto" />
              </div>
              <figcaption className="text-gray-500 text-sm mt-3 text-center">{t.legenda}</figcaption>
            </figure>
          ))}
        </div>
      </div>
    </section>
  )
}
