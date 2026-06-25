import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faBook, faGraduationCap, faDesktop,
  faGauge, faBarcode, faQrcode, faRotateLeft, faClock,
  faFileCsv, faShield, faGear, faMagnifyingGlass,
  faHandPointer, faClockRotateLeft, faCircleExclamation,
  faUserCheck, faIdCard,
} from '@fortawesome/free-solid-svg-icons'

const grupos = [
  {
    titulo: 'Bibliotecário',
    icon: faBook,
    cor: 'bg-blue-50 border-blue-200',
    corIcon: 'bg-[#2E75B6] text-white',
    corTitulo: 'text-[#1F4E79]',
    itens: [
      { icon: faGauge, texto: 'Painel com indicadores em tempo real' },
      { icon: faBarcode, texto: 'Cadastro de livros por ISBN' },
      { icon: faQrcode, texto: 'Geração automática de código de barras' },
      { icon: faRotateLeft, texto: 'Empréstimos e devoluções no balcão' },
      { icon: faClock, texto: 'Cálculo automático de multas' },
      { icon: faFileCsv, texto: 'Relatórios exportados em CSV' },
      { icon: faShield, texto: 'Auditoria completa de operações' },
      { icon: faGear, texto: 'Configurações de prazos e limites' },
    ],
  },
  {
    titulo: 'Aluno / Professor',
    icon: faGraduationCap,
    cor: 'bg-green-50 border-green-200',
    corIcon: 'bg-green-600 text-white',
    corTitulo: 'text-green-800',
    itens: [
      { icon: faMagnifyingGlass, texto: 'Pesquisa por título, autor ou ISBN' },
      { icon: faHandPointer, texto: 'Empréstimo em 1 clique' },
      { icon: faClockRotateLeft, texto: 'Histórico pessoal de empréstimos' },
      { icon: faCircleExclamation, texto: 'Status de multas e bloqueios' },
      { icon: faIdCard, texto: '4 perfis com permissões distintas' },
    ],
  },
  {
    titulo: 'Kiosk (autoatendimento)',
    icon: faDesktop,
    cor: 'bg-yellow-50 border-yellow-200',
    corIcon: 'bg-yellow-500 text-white',
    corTitulo: 'text-yellow-800',
    itens: [
      { icon: faDesktop, texto: 'Terminal independente para alunos' },
      { icon: faIdCard, texto: 'Login por matrícula ou nome' },
      { icon: faRotateLeft, texto: 'Empréstimo e devolução autônomos' },
      { icon: faClock, texto: 'Logout automático após 90 segundos' },
      { icon: faUserCheck, texto: 'Sem necessidade de bibliotecário presente' },
    ],
  },
]

export default function Funcionalidades() {
  return (
    <section id="funcionalidades" className="py-20 px-4 bg-gray-50">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-[#1F4E79] mb-3">Funcionalidades</h2>
          <p className="text-gray-500 text-lg">Um sistema completo para cada perfil de usuário.</p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {grupos.map((g) => (
            <div key={g.titulo} className={`rounded-2xl border p-6 ${g.cor}`}>
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 ${g.corIcon}`}>
                <FontAwesomeIcon icon={g.icon} className="text-xl" />
              </div>
              <h3 className={`font-bold text-xl mb-4 ${g.corTitulo}`}>{g.titulo}</h3>
              <ul className="space-y-2.5">
                {g.itens.map((item) => (
                  <li key={item.texto} className="flex items-start gap-3 text-gray-700 text-sm">
                    <FontAwesomeIcon icon={item.icon} className="text-gray-400 mt-0.5 w-4 shrink-0" />
                    {item.texto}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
