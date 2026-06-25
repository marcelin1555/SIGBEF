import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faMoneyBillWave, faGlobe, faTableColumns } from '@fortawesome/free-solid-svg-icons'

const dores = [
  {
    icon: faMoneyBillWave, cor: 'text-red-500', bgCor: 'bg-red-50',
    titulo: 'Sistemas profissionais custam uma fortuna',
    texto: 'Pergamum e Sophia cobram entre R$ 8 mil e R$ 30 mil por ano, fora do alcance de qualquer escola pública sem orçamento de TI.',
  },
  {
    icon: faGlobe, cor: 'text-orange-500', bgCor: 'bg-orange-50',
    titulo: 'O gratuito existente exige internet',
    texto: 'O Biblivre é de código aberto, mas exige servidor dedicado, instalação complexa e conexão constante. A escola pública média não tem infraestrutura pra isso.',
  },
  {
    icon: faTableColumns, cor: 'text-yellow-600', bgCor: 'bg-yellow-50',
    titulo: 'Excel não é sistema de biblioteca',
    texto: 'Sem controle de atrasos, sem busca por autor, sem multi-usuário, sem relatórios. Uma planilha não consegue substituir um sistema de verdade.',
  },
]

export default function Problema() {
  return (
    <section className="py-20 px-4 bg-gray-50">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-[#1F4E79] mb-4">
            130 mil escolas públicas.<br />A maioria ainda usa Excel ou caderno.
          </h2>
          <p className="text-gray-500 text-lg">Por que isso ainda acontece em 2025?</p>
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

        <p className="text-center mt-10 text-xl font-semibold text-[#2E75B6]">
          O SIGBEF resolve os três.
        </p>
      </div>
    </section>
  )
}
