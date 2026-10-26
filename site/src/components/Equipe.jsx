import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faCode, faBullhorn, faChartLine, faChalkboardUser } from '@fortawesome/free-solid-svg-icons'
import { TituloSecao } from './ui'

const membros = [
  {
    nome: 'Marcello Melo',
    papel: 'Dev / Líder',
    icon: faCode,
    corIcon: 'bg-blue-100 text-blue-600',
    descricao: 'Concebeu, projetou e codificou o SIGBEF. Python, SQLite e arquitetura do sistema.',
  },
  {
    nome: 'Júlia Kelly',
    papel: 'Comunicação',
    icon: faBullhorn,
    corIcon: 'bg-pink-100 text-pink-600',
    descricao: 'Pitch, roteiro do vídeo e pesquisa de usuário com a bibliotecária do CEFE.',
  },
  {
    nome: 'Maria Laura',
    papel: 'Modelo de negócio',
    icon: faChartLine,
    corIcon: 'bg-green-100 text-green-600',
    descricao: 'Projeções financeiras, análise de concorrentes e modelo Open Core.',
  },
  {
    nome: 'Pedro Jonath',
    papel: 'Orientador',
    icon: faChalkboardUser,
    corIcon: 'bg-yellow-100 text-yellow-700',
    descricao: 'Professor do CEFE. Leciona Banco de Dados e POO, as disciplinas que fundamentam o sistema.',
  },
]

export default function Equipe() {
  return (
    <section id="equipe" className="py-20 px-4 bg-gray-50">
      <div className="max-w-4xl mx-auto">
        <TituloSecao titulo="Equipe">Feito por estudantes do CEFE, escola pública do Rio Grande do Norte.</TituloSecao>

        <div className="grid sm:grid-cols-2 gap-6">
          {membros.map((m) => (
            <div key={m.nome} className="bg-white rounded-2xl p-6 border border-gray-100 flex gap-4 items-start hover:shadow-md transition-shadow">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${m.corIcon}`}>
                <FontAwesomeIcon icon={m.icon} className="text-xl" />
              </div>
              <div>
                <h3 className="font-bold text-gray-800 text-lg">{m.nome}</h3>
                <span className="text-xs text-primary font-semibold uppercase tracking-wide">{m.papel}</span>
                <p className="text-gray-500 text-sm mt-2 leading-relaxed">{m.descricao}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
