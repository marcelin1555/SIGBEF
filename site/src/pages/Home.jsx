import { Link } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faBookOpen, faBarcode, faRotateLeft,
  faDesktop, faFileCsv, faUsers,
} from '@fortawesome/free-solid-svg-icons'
import Hero from '../components/Hero'
import Problema from '../components/Problema'
import Prova from '../components/Prova'
import ODS from '../components/ODS'

const stats = [
  { valor: '+1.000', label: 'livros suportados' },
  { valor: '100%', label: 'offline' },
  { valor: '5 min', label: 'para instalar' },
  { valor: 'MIT', label: 'licença livre' },
]

const features = [
  { icon: faBookOpen,   cor: 'bg-blue-100 text-blue-600',   titulo: 'Acervo completo',   texto: 'Cadastro por ISBN com busca por título ou autor' },
  { icon: faBarcode,    cor: 'bg-purple-100 text-purple-600', titulo: 'Código de barras', texto: 'Geração automática no cadastro de cada livro' },
  { icon: faRotateLeft, cor: 'bg-green-100 text-green-600',  titulo: 'Empréstimos',       texto: 'Controle de prazo com cálculo automático de multa' },
  { icon: faDesktop,    cor: 'bg-indigo-100 text-indigo-600', titulo: 'Kiosk',            texto: 'Terminal de autoatendimento para alunos' },
  { icon: faFileCsv,    cor: 'bg-red-100 text-red-600',      titulo: 'Relatórios',        texto: 'Exportação em CSV com histórico completo' },
  { icon: faUsers,      cor: 'bg-yellow-100 text-yellow-700', titulo: 'Multi-perfil',     texto: '4 níveis de acesso com permissões distintas' },
]

const passos = [
  { n: '1', titulo: 'Baixar',   texto: 'Acesse o GitHub e baixe o instalador .exe. É gratuito, sem cadastro.' },
  { n: '2', titulo: 'Instalar', texto: 'Execute o instalador. Próximo, próximo, concluir. Pronto em menos de 5 minutos.' },
  { n: '3', titulo: 'Usar',     texto: 'Abra o SIGBEF. Sem internet, sem servidor, sem mensalidade.' },
]

export default function Home() {
  return (
    <>
      <Hero />

      {/* stats strip */}
      <div className="bg-[#2E75B6] py-4 px-4">
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
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-[#1F4E79] mb-3">O que o SIGBEF faz</h2>
            <p className="text-gray-500 text-lg">Tudo que uma biblioteca escolar precisa, num só lugar.</p>
          </div>

          <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-5">
            {features.map(f => (
              <div key={f.titulo} className="flex gap-4 items-start p-5 rounded-xl border border-gray-100 bg-gray-50 hover:border-[#2E75B6]/30 hover:shadow-sm transition-all">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${f.cor}`}>
                  <FontAwesomeIcon icon={f.icon} className="text-base" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-800 mb-1">{f.titulo}</h3>
                  <p className="text-gray-500 text-sm leading-snug">{f.texto}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="text-center mt-8">
            <Link to="/funcionalidades"
              className="inline-flex items-center gap-2 text-[#2E75B6] font-semibold hover:text-[#1F4E79] transition-colors">
              Ver todas as funcionalidades
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
        </div>
      </section>

      <Prova />

      {/* install steps */}
      <section id="como-instalar" className="py-20 px-4 bg-gray-50">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-[#1F4E79] mb-3">Como instalar</h2>
            <p className="text-gray-500 text-lg">Três passos. Nenhuma configuração de servidor.</p>
          </div>

          <div className="grid sm:grid-cols-3 gap-8 mb-10">
            {passos.map(p => (
              <div key={p.n} className="text-center">
                <div className="w-14 h-14 rounded-full bg-[#2E75B6] text-white text-2xl font-bold flex items-center justify-center mx-auto mb-4">
                  {p.n}
                </div>
                <h3 className="font-bold text-gray-800 text-lg mb-2">{p.titulo}</h3>
                <p className="text-gray-500 text-sm leading-relaxed">{p.texto}</p>
              </div>
            ))}
          </div>

          <div className="text-center flex flex-col sm:flex-row gap-3 justify-center">
            <a href="https://github.com/marcelin1555/SIGBEF/releases" target="_blank" rel="noopener noreferrer"
              className="bg-[#2E75B6] text-white font-bold px-10 py-4 rounded-xl text-lg hover:bg-[#1F4E79] transition-colors shadow-md">
              Baixar SIGBEF grátis
            </a>
            <Link to="/download"
              className="border-2 border-[#2E75B6] text-[#2E75B6] font-semibold px-10 py-4 rounded-xl text-lg hover:bg-blue-50 transition-colors">
              Guia detalhado
            </Link>
          </div>
          <p className="text-center mt-3 text-gray-400 text-sm">Licença MIT · Código aberto · Sem limite de usuários</p>
        </div>
      </section>

      {/* pricing teaser */}
      <section className="py-16 px-4 bg-white">
        <div className="max-w-3xl mx-auto text-center">
          <span className="inline-block bg-blue-100 text-[#2E75B6] text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wide mb-4">Modelo Open Core</span>
          <h2 className="text-3xl font-bold text-[#1F4E79] mb-4">O sistema é gratuito para sempre.</h2>
          <p className="text-gray-500 text-lg mb-8 max-w-xl mx-auto">
            Serviços como implantação, treinamento e suporte são opcionais e pagos.
            Escolas que só precisam do sistema nunca pagam nada.
          </p>
          <Link to="/planos"
            className="inline-block bg-[#1F4E79] text-white font-bold px-8 py-3.5 rounded-xl hover:bg-[#2E75B6] transition-colors">
            Ver planos e preços
          </Link>
        </div>
      </section>

      <ODS />
    </>
  )
}
