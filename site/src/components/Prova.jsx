const metricas = [
  { valor: '+1.000', label: 'livros cadastrados' },
  { valor: '4', label: 'perfis de usuário' },
  { valor: '5 min', label: 'para instalar' },
  { valor: '100%', label: 'offline' },
]

export default function Prova() {
  return (
    <section className="py-20 px-4 bg-white">
      <div className="max-w-4xl mx-auto">
        <div className="bg-[#1F4E79] text-white rounded-3xl p-8 sm:p-12 mb-12 text-center">
          <p className="text-2xl sm:text-3xl font-bold leading-snug mb-2">
            Esse não é um protótipo.
          </p>
          <p className="text-blue-200 text-lg sm:text-xl">
            É um sistema completo, com instalador, rodando neste momento na biblioteca do CEFE.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {metricas.map((m) => (
            <div key={m.label} className="text-center bg-gray-50 rounded-2xl p-6 border border-gray-100">
              <div className="text-3xl font-bold text-[#2E75B6] mb-1">{m.valor}</div>
              <div className="text-gray-500 text-sm">{m.label}</div>
            </div>
          ))}
        </div>

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
