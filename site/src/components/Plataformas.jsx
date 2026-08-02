import { useState } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faDesktop, faMobileScreenButton, faGauge, faBarcode, faLayerGroup,
  faFileCsv, faChartLine, faClipboardCheck,
  faDatabase, faCashRegister, faPlug, faPalette, faIdCard,
  faMagnifyingGlass, faHourglassHalf, faArrowsRotate, faBell,
  faBookOpen, faQrcode, faWifi,
} from '@fortawesome/free-solid-svg-icons'

const plataformas = [
  {
    chave: 'desktop',
    titulo: 'Aplicativo desktop',
    subtitulo: 'Para a bibliotecária, no computador da biblioteca',
    icon: faDesktop,
    cor: 'text-[#2E75B6]',
    corAtiva: 'bg-[#2E75B6] text-white',
    itens: [
      { icon: faGauge, texto: 'Painel com indicadores em tempo real' },
      { icon: faBarcode, texto: 'Cadastro por ISBN, com código de barras gerado na hora' },
      { icon: faCashRegister, texto: 'Empréstimo, devolução e devolução em lote no balcão' },
      { icon: faLayerGroup, texto: 'Reservas com fila de espera' },
      { icon: faClipboardCheck, texto: 'Conferência do acervo (inventário) e baixa de exemplar' },
      { icon: faFileCsv, texto: 'Relatórios por período, exportados em CSV' },
      { icon: faChartLine, texto: 'Painel de uso: empréstimos por mês, turma e categoria' },
      { icon: faDatabase, texto: 'Backup automático do banco de dados' },
      { icon: faDesktop, texto: 'Terminal de autoatendimento (kiosk) para os alunos' },
      { icon: faPlug, texto: 'API REST opcional para integrar com outros sistemas' },
      { icon: faPalette, texto: 'Cores e brasão da escola personalizáveis' },
    ],
    rodape: 'Windows, Linux ou macOS. 100% offline — nenhum dado sai da escola.',
  },
  {
    chave: 'android',
    titulo: 'App Android',
    subtitulo: 'Para o aluno, no celular dele',
    icon: faMobileScreenButton,
    cor: 'text-green-700',
    corAtiva: 'bg-green-600 text-white',
    itens: [
      { icon: faIdCard, texto: 'Carteirinha digital com código de barras' },
      { icon: faMagnifyingGlass, texto: 'Busca no acervo — funciona offline após a 1ª sincronização' },
      { icon: faHourglassHalf, texto: 'Entra na fila de espera de um livro emprestado' },
      { icon: faArrowsRotate, texto: 'Renova o próprio empréstimo, com as mesmas regras do balcão' },
      { icon: faBell, texto: 'Aviso de devolução no celular, calculado no aparelho, sem internet' },
      { icon: faBookOpen, texto: '"Minha leitura": quanto já leu e sugestões de próximos livros' },
      { icon: faQrcode, texto: 'Pareamento com a biblioteca por QR code, sem digitar nada' },
      { icon: faWifi, texto: 'Sincroniza pela rede Wi-Fi da própria escola' },
    ],
    rodape: 'Android. Continua mostrando a carteirinha e os empréstimos mesmo sem sinal.',
  },
]

export default function Plataformas() {
  const [ativa, setAtiva] = useState('desktop')
  const plataforma = plataformas.find((p) => p.chave === ativa)

  return (
    <section className="py-20 px-4 bg-white">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-10">
          <h2 className="text-3xl sm:text-4xl font-bold text-[#1F4E79] mb-3">
            Duas telas, uma biblioteca só
          </h2>
          <p className="text-gray-500 text-lg">
            Escolha pra saber o que roda no computador da bibliotecária e o
            que vai no bolso do aluno.
          </p>
        </div>

        {/* Seletor de abas */}
        <div
          role="tablist"
          aria-label="Escolher plataforma"
          className="flex gap-2 bg-gray-100 rounded-2xl p-1.5 mb-8 max-w-md mx-auto"
        >
          {plataformas.map((p) => {
            const selecionada = p.chave === ativa
            return (
              <button
                key={p.chave}
                type="button"
                role="tab"
                id={`aba-${p.chave}`}
                aria-selected={selecionada}
                aria-controls={`painel-${p.chave}`}
                onClick={() => setAtiva(p.chave)}
                className={`flex-1 flex items-center justify-center gap-2 rounded-xl px-4 py-3 text-sm font-bold transition-colors ${
                  selecionada
                    ? `${p.corAtiva} shadow-sm`
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <FontAwesomeIcon icon={p.icon} />
                {p.titulo}
              </button>
            )
          })}
        </div>

        <div
          role="tabpanel"
          id={`painel-${plataforma.chave}`}
          aria-labelledby={`aba-${plataforma.chave}`}
          className="rounded-2xl border border-gray-200 p-6 sm:p-8"
        >
          <div className="flex items-center gap-3 mb-1">
            <FontAwesomeIcon icon={plataforma.icon} className={`text-xl ${plataforma.cor}`} />
            <h3 className="font-bold text-xl text-gray-900">{plataforma.titulo}</h3>
          </div>
          <p className="text-gray-500 text-sm mb-6">{plataforma.subtitulo}</p>

          <ul className="grid sm:grid-cols-2 gap-x-6 gap-y-3">
            {plataforma.itens.map((item) => (
              <li key={item.texto} className="flex items-start gap-3 text-gray-700 text-sm">
                <FontAwesomeIcon icon={item.icon} className={`mt-0.5 w-4 shrink-0 ${plataforma.cor}`} />
                {item.texto}
              </li>
            ))}
          </ul>

          <p className="text-gray-400 text-xs mt-6 pt-6 border-t border-gray-100">
            {plataforma.rodape}
          </p>
        </div>
      </div>
    </section>
  )
}
