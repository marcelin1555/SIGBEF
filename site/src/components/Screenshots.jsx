export default function Screenshots() {
  return (
    <section className="py-20 px-4 bg-gray-50">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <p className="text-[#2E75B6] text-sm font-semibold uppercase tracking-widest mb-3">Veja funcionando</p>
          <h2 className="text-3xl sm:text-4xl font-bold text-[#1F4E79] mb-3">Captura de tela real</h2>
          <p className="text-gray-500 text-lg">O painel do administrador rodando de verdade, sem maquiagem.</p>
        </div>

        <div className="rounded-2xl overflow-hidden shadow-xl border border-gray-200 bg-white">
          <img
            src="/screenshot-painel.svg"
            alt="Painel administrativo do SIGBEF mostrando estatísticas do acervo (11 títulos, 32 exemplares, 24 disponíveis), empréstimos abertos, atrasos, usuários ativos e o ranking dos livros mais emprestados"
            className="w-full h-auto"
          />
        </div>
      </div>
    </section>
  )
}
