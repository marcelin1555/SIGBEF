import { Link } from 'react-router-dom'
import { VERSAO } from '../versao'
import { LINKS } from '../config'

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-400">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-12">
        <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-8 mb-10">

          {/* brand */}
          <div className="md:col-span-1">
            <div className="flex items-center gap-3 mb-3">
              <img src="/logo-64.png" alt="SIGBEF" width="32" height="32" className="h-8 w-8 rounded" />
              <div>
                <div className="text-white font-bold text-lg leading-none">SIGBEF</div>
                <div className="text-xs text-gray-400">{`v${VERSAO} · Licença MIT`}</div>
              </div>
            </div>
            <p className="text-xs text-gray-400 leading-relaxed">
              Sistema gratuito de gestão de biblioteca escolar, feito por estudantes do CEFE, RN.
            </p>
          </div>

          {/* produto */}
          <div>
            <h4 className="text-white font-semibold text-sm mb-3">Produto</h4>
            <ul className="space-y-2 text-sm">
              <li><Link to="/funcionalidades" className="hover:text-white transition-colors">Funcionalidades</Link></li>
              <li><Link to="/download" className="hover:text-white transition-colors">Como instalar</Link></li>
              <li><Link to="/planos" className="hover:text-white transition-colors">Planos e preços</Link></li>
              <li><Link to="/novidades" className="hover:text-white transition-colors">Novidades</Link></li>
              <li>
                <a href={LINKS.download} target="_blank" rel="noopener noreferrer"
                  className="hover:text-white transition-colors">Releases</a>
              </li>
            </ul>
          </div>

          {/* projeto */}
          <div>
            <h4 className="text-white font-semibold text-sm mb-3">Projeto</h4>
            <ul className="space-y-2 text-sm">
              <li><Link to="/equipe" className="hover:text-white transition-colors">Equipe</Link></li>
              <li><Link to="/eventos" className="hover:text-white transition-colors">Eventos</Link></li>
              <li>
                <a href={LINKS.repositorio} target="_blank" rel="noopener noreferrer"
                  className="hover:text-white transition-colors">GitHub</a>
              </li>
              <li>
                <a href={LINKS.problemas} target="_blank" rel="noopener noreferrer"
                  className="hover:text-white transition-colors">Reportar problema</a>
              </li>
              <li>
                <a href={LINKS.whatsapp} target="_blank" rel="noopener noreferrer"
                  className="hover:text-white transition-colors">Fale conosco (WhatsApp)</a>
              </li>
            </ul>
          </div>

          {/* download cta */}
          <div>
            <h4 className="text-white font-semibold text-sm mb-3">Começar agora</h4>
            <p className="text-xs text-gray-400 mb-3">Gratuito, sem cadastro, sem limite de usuários.</p>
            <a href={LINKS.download} target="_blank" rel="noopener noreferrer"
              className="inline-block bg-primary text-white text-sm font-bold px-4 py-2 rounded-lg hover:bg-dark transition-colors">
              Baixar SIGBEF
            </a>
          </div>
        </div>

        <div className="border-t border-gray-800 pt-6 flex flex-col sm:flex-row justify-between gap-2 text-xs text-gray-400">
          <p>Feito no CEFE, escola pública do Rio Grande do Norte.</p>
          <p>© 2026 SIGBEF. Código aberto sob licença MIT.</p>
        </div>
      </div>
    </footer>
  )
}
