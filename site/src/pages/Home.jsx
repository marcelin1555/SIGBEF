import { Link } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faBookOpen, faBarcode, faRotateLeft,
  faDesktop, faFileCsv, faUsers,
} from '@fortawesome/free-solid-svg-icons'
import Hero from '../components/Hero'
import Problema from '../components/Problema'
import Screenshots from '../components/Screenshots'
import Prova from '../components/Prova'
import ODS from '../components/ODS'
import Reconhecimentos from '../components/Reconhecimentos'
import { LINKS } from '../config'
import { TituloSecao } from '../components/ui'

// Números com fonte: acervo do CEFE (painel do sistema) e ensaio de carga de 19/10/2026.
const stats = [
  { valor: '2.867', label: 'títulos no acervo do CEFE' },
  { valor: '250 mil', label: 'livros no teste de carga' },
  { valor: '100%', label: 'sem internet' },
  { valor: '2º lugar', label: 'Desafio Liga Jovem RN' },
]

const features = [
  { icon: faBookOpen,   cor: 'bg-blue-100 text-primary',   titulo: 'Acervo completo',   texto: 'Cadastro por ISBN com busca por título ou autor' },
  { icon: faBarcode,    cor: 'bg-amber-100 text-amber-700',  titulo: 'Código de barras', texto: 'Geração automática no cadastro de cada livro' },
  { icon: faRotateLeft, cor: 'bg-blue-100 text-primary',   titulo: 'Empréstimos',       texto: 'Controle de prazo com cálculo automático de multa' },
  { icon: faDesktop,    cor: 'bg-amber-100 text-amber-700',  titulo: 'Autoatendimento',  texto: 'O próprio aluno empresta e devolve num terminal' },
  { icon: faFileCsv,    cor: 'bg-blue-100 text-primary',   titulo: 'Relatórios',        texto: 'Exportação em CSV com histórico completo' },
  { icon: faUsers,      cor: 'bg-amber-100 text-amber-700',  titulo: 'Multi-perfil',     texto: '4 níveis de acesso com permissões distintas' },
]

const passos = [
  { n: '1', titulo: 'Baixar',   texto: 'Baixe o instalador para Windows, Linux ou macOS. É gratuito e sem cadastro.' },
  { n: '2', titulo: 'Instalar', texto: 'Execute o instalador. Próximo, próximo, concluir. Pronto em menos de 5 minutos.' },
  { n: '3', titulo: 'Usar',     texto: 'Abra o SIGBEF. Sem internet, sem servidor, sem mensalidade.' },
]

export default function Home() {
  return (
    <>
      <Hero />

      {/* stats strip */}
      <div className="bg-primary py-4 px-4">
        <div className="max-w-4xl mx-auto grid grid-cols-2 sm:grid-cols-4 gap-4 text-center text-white">
          {stats.map(s => (
            <div key={s.label}>
              <div className="font-bold text-xl">{s.valor}</div>
              <div className="text-blue-100 text-xs">{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      <Problema />

      {/* feature grid */}
      <section className="py-20 px-4 bg-white">
        <div className="max-w-5xl mx-auto">
          <TituloSecao titulo="O que o SIGBEF faz">Tudo que uma biblioteca escolar precisa, num só lugar.</TituloSecao>

          <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-5">
            {features.map(f => (
              <Link key={f.titulo} to="/funcionalidades"
                className="flex gap-4 items-start p-5 rounded-xl border border-gray-100 bg-gray-50 hover:border-primary/30 hover:shadow-sm transition-all">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${f.cor}`}>
                  <FontAwesomeIcon icon={f.icon} className="text-base" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-800 mb-1">{f.titulo}</h3>
                  <p className="text-gray-500 text-sm leading-snug">{f.texto}</p>
                </div>
              </Link>
            ))}
          </div>

          <div className="text-center mt-8">
            <Link to="/funcionalidades"
              className="inline-flex items-center gap-2 text-primary font-semibold hover:text-dark transition-colors">
              Ver todas as funcionalidades
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
        </div>
      </section>

      <Screenshots />

      <Prova />

      <Reconhecimentos />

      {/* install steps */}
      <section id="como-instalar" className="py-20 px-4 bg-white">
        <div className="max-w-4xl mx-auto">
          <TituloSecao titulo="Como instalar">Três passos. Nenhuma configuração de servidor.</TituloSecao>

          <div className="grid sm:grid-cols-3 gap-8 mb-10">
            {passos.map(p => (
              <div key={p.n} className="text-center">
                <div className="w-14 h-14 rounded-full bg-primary text-white text-2xl font-bold flex items-center justify-center mx-auto mb-4">
                  {p.n}
                </div>
                <h3 className="font-bold text-gray-800 text-lg mb-2">{p.titulo}</h3>
                <p className="text-gray-500 text-sm leading-relaxed">{p.texto}</p>
              </div>
            ))}
          </div>

          <div className="text-center flex flex-col sm:flex-row gap-3 justify-center">
            <a href={LINKS.download} target="_blank" rel="noopener noreferrer"
              className="bg-primary text-white font-bold px-10 py-4 rounded-xl text-lg hover:bg-dark transition-colors shadow-md">
              Baixar SIGBEF grátis
            </a>
            <Link to="/download"
              className="border-2 border-primary text-primary font-semibold px-10 py-4 rounded-xl text-lg hover:bg-blue-50 transition-colors">
              Guia detalhado
            </Link>
          </div>
          <p className="text-center mt-3 text-gray-500 text-sm">Licença MIT · Código aberto · Sem limite de usuários</p>
        </div>
      </section>

      {/* pricing teaser */}
      <section className="py-16 px-4 bg-gray-50">
        <div className="max-w-3xl mx-auto text-center">
          <span className="inline-block bg-blue-100 text-primary text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wide mb-4">Modelo Open Core</span>
          <h2 className="text-3xl font-bold text-dark mb-4">O sistema é gratuito para sempre.</h2>
          <p className="text-gray-500 text-lg mb-8 max-w-xl mx-auto">
            Serviços como implantação, treinamento e suporte são opcionais e pagos.
            Escolas que só precisam do sistema nunca pagam nada.
          </p>
          <Link to="/planos"
            className="inline-block bg-dark text-white font-bold px-8 py-3.5 rounded-xl hover:bg-primary transition-colors">
            Ver planos e preços
          </Link>
        </div>
      </section>

      <ODS />
    </>
  )
}
