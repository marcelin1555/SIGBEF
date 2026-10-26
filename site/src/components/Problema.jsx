import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faMoneyBillWave, faServer, faTableColumns } from '@fortawesome/free-solid-svg-icons'

const dores = [
  {
    icon: faMoneyBillWave, cor: 'text-red-500', bgCor: 'bg-red-50',
    titulo: 'Os sistemas profissionais são pagos',
    texto: 'Pergamum e Sophia têm preço sob consulta. Um contrato de licença do Pergamum custou R$ 27.200 a uma universidade federal em 2017.',
  },
  {
    icon: faServer, cor: 'text-orange-500', bgCor: 'bg-orange-50',
    titulo: 'O gratuito pede servidor',
    texto: 'O Biblivre é livre, mas roda num servidor com Java, Tomcat e PostgreSQL, que a maioria das escolas públicas não tem quem instale e mantenha.',
  },
  {
    icon: faTableColumns, cor: 'text-yellow-600', bgCor: 'bg-yellow-50',
    titulo: 'Planilha não controla empréstimo',
    texto: 'Na biblioteca do CEFE, o acervo ficava numa planilha desde 2015. Sem aviso de atraso, sem fila de espera e sem saber onde cada exemplar estava.',
  },
]

export default function Problema() {
  return (
    <section className="py-20 px-4 bg-gray-50">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-dark mb-4">
            Só 31% das escolas públicas brasileiras têm biblioteca.
          </h2>
          <p className="text-gray-500 text-lg max-w-2xl mx-auto">
            E as que têm, muitas vezes, não conseguem pagar por um sistema para cuidar dela.
          </p>
          <p className="text-gray-400 text-xs mt-3">Fonte: Atricon (2024), com dados do Censo Escolar 2022.</p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {dores.map((d) => (
            <div key={d.titulo} className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
              <div className={`w-12 h-12 rounded-xl ${d.bgCor} flex items-center justify-center mb-4`}>
                <FontAwesomeIcon icon={d.icon} className={`text-xl ${d.cor}`} />
              </div>
              <h3 className="font-bold text-gray-800 text-lg mb-2">{d.titulo}</h3>
              <p className="text-gray-500 text-sm leading-relaxed">{d.texto}</p>
            </div>
          ))}
        </div>

        <p className="text-center mt-10 text-xl font-semibold text-primary">
          O SIGBEF é gratuito, roda sem servidor e controla cada exemplar.
        </p>
      </div>
    </section>
  )
}
