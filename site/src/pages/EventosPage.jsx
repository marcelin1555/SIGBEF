import { useEffect, useRef, useState } from 'react'
import { LINKS } from '../config'
import { CabecalhoPagina } from '../components/ui'

// Eventos que ainda vão acontecer. Não têm galeria: quando o evento
// passar, é só mover a entrada pro array `eventos` de baixo e soltar as
// fotos em public/eventos/<id>/.
const proximos = [
  {
    id: 'expoiern-2026',
    titulo: 'EXPOIERN 2026: Tec Mulheres',
    data: '5 de novembro de 2026',
    dataISO: '2026-11-05',
    local: 'Jardim de Piranhas/RN',
    descricao:
      'Projeto aprovado para a mostra de tecnologia, educação, ciência e protagonismo feminino ' +
      'do IERN, Campus Maria do Carmo Ferreira. A equipe apresenta o SIGBEF funcionando ' +
      'com o acervo real da biblioteca do CEFE.',
  },
  {
    id: 'fcsp-2026',
    titulo: 'XVI Feira de Ciências do Semiárido Potiguar',
    data: '3 e 4 de dezembro de 2026',
    dataISO: '2026-12-03',
    local: 'Mossoró/RN',
    descricao:
      'Indicado pela III FICTS, o SIGBEF participa da Feira Juvenil, realizada pela UFERSA no ' +
      'Parque de Exposições Expocenter. A equipe leva o sistema funcionando para o público ' +
      'e para os avaliadores.',
  },
]

// Cada evento tem uma pasta em public/eventos/<id>/ com as fotos.
// Pra adicionar fotos: solta os arquivos na pasta e lista aqui embaixo.
const eventos = [
  {
    id: 'liga-jovem-2026',
    titulo: 'Desafio Liga Jovem: 2º lugar na etapa estadual',
    data: '6 de outubro de 2026',
    local: 'On-line',
    descricao:
      'Na banca estadual do Rio Grande do Norte da 4ª edição do Desafio Liga Jovem, do Sebrae, ' +
      'categoria Educação Profissional e Técnico, a equipe apresentou o SIGBEF ao vivo para ' +
      'os jurados e ficou em 2º lugar.',
    fotos: [],
  },
  {
    id: 'ficts-fecets-2026',
    titulo: 'III FICTS e I FECETS: Etapa Caicó',
    data: '16 de setembro de 2026',
    local: 'Caicó/RN',
    descricao:
      'A equipe apresentou o SIGBEF na III Feira de Iniciação Científica e Tecnológica do ' +
      'Seridó, na categoria Juvenil, com o sistema rodando com o acervo real da biblioteca ' +
      'do CEFE. O projeto foi indicado para a XVI Feira de Ciências do Semiárido Potiguar.',
    fotos: [],
  },
  {
    id: 'coloquio-ept-2026',
    titulo: 'V Seminário e II Colóquio de EPT da Rede Estadual do RN',
    data: '22 de julho de 2026',
    local: 'Natal/RN',
    descricao:
      'A equipe apresentou o SIGBEF no colóquio estadual de Educação Profissional e ' +
      'Tecnológica, mostrando o sistema em produção na biblioteca do CEFE. Do evento ' +
      'já saíram os primeiros convites de escolas de outras regiões interessadas em ' +
      'implantar o sistema.',
    fotos: [
      { src: '/eventos/coloquio-ept-2026/coloquio-05.webp', alt: 'Apresentação do SIGBEF no telão principal do evento' },
      { src: '/eventos/coloquio-ept-2026/coloquio-03.webp', alt: 'Equipe no palco do V Seminário e II Colóquio de EPT' },
      { src: '/eventos/coloquio-ept-2026/coloquio-04.webp', alt: 'Equipe no palco durante a cerimônia do evento' },
      { src: '/eventos/coloquio-ept-2026/coloquio-06.webp', alt: 'Vista do palco e do telão do colóquio' },
      { src: '/eventos/coloquio-ept-2026/coloquio-01.webp', alt: 'Equipe do SIGBEF reunida no colóquio, em Natal' },
      { src: '/eventos/coloquio-ept-2026/coloquio-02.webp', alt: 'Integrantes da equipe no espaço do evento' },
      { src: '/eventos/coloquio-ept-2026/coloquio-07.webp', alt: 'Foto com os participantes do colóquio' },
    ],
  },
]

function Galeria({ fotos, onAbrir }) {
  // Evento sem fotos (por exemplo, banca on-line) não mostra galeria vazia.
  if (fotos.length === 0) return null
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
      {fotos.map(foto => (
        <button key={foto.src} type="button" onClick={() => onAbrir(foto)}
          className="group relative rounded-xl overflow-hidden aspect-[4/3] bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary">
          <img src={foto.src.replace('.webp', '-mini.webp')} alt={foto.alt} loading="lazy"
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
        </button>
      ))}
    </div>
  )
}

export default function EventosPage() {
  const [fotoAberta, setFotoAberta] = useState(null)
  const botaoFechar = useRef(null)

  // Lightbox acessível: fecha com Esc, trava o scroll da página e foca o botão
  useEffect(() => {
    if (!fotoAberta) return
    const aoTeclar = e => { if (e.key === 'Escape') setFotoAberta(null) }
    document.addEventListener('keydown', aoTeclar)
    document.body.style.overflow = 'hidden'
    botaoFechar.current?.focus()
    return () => {
      document.removeEventListener('keydown', aoTeclar)
      document.body.style.overflow = ''
    }
  }, [fotoAberta])

  return (
    <>
      {/* page header */}
      <CabecalhoPagina rotulo="Comunidade" titulo="Eventos">
        O SIGBEF fora da biblioteca: apresentações, feiras e encontros onde o projeto esteve.
      </CabecalhoPagina>

      {/* próximos eventos */}
      {proximos.length > 0 && (
        <section className="py-14 px-4 bg-white">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-sm font-bold uppercase tracking-widest text-primary mb-6">
              Próximos eventos
            </h2>
            <div className="space-y-6">
              {proximos.map(ev => (
                <article key={ev.id}
                  className="border-l-4 border-primary bg-blue-50/60 rounded-r-2xl p-6 sm:p-8">
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs font-bold uppercase tracking-wide mb-3">
                    <span className="bg-primary text-white px-2.5 py-1 rounded-full">Em breve</span>
                    <time className="text-dark" dateTime={ev.dataISO}>{ev.data}</time>
                    <span className="text-gray-300" aria-hidden="true">•</span>
                    <span className="text-gray-500">{ev.local}</span>
                  </div>
                  <h3 className="text-xl sm:text-2xl font-bold text-dark mb-3">{ev.titulo}</h3>
                  <p className="text-gray-600 leading-relaxed">{ev.descricao}</p>
                </article>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* lista de eventos */}
      <section className="py-16 px-4 bg-gray-50">
        <div className="max-w-4xl mx-auto space-y-10">
          <h2 className="text-sm font-bold uppercase tracking-widest text-gray-400">
            Já aconteceram
          </h2>
          {eventos.map(ev => (
            <article key={ev.id} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 sm:p-8">
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs font-bold uppercase tracking-wide mb-3">
                <span className="text-primary">{ev.data}</span>
                <span className="text-gray-300">•</span>
                <span className="text-gray-500">{ev.local}</span>
              </div>
              <h2 className="text-xl sm:text-2xl font-bold text-dark mb-3">{ev.titulo}</h2>
              <p className="text-gray-600 leading-relaxed mb-6">{ev.descricao}</p>
              <Galeria fotos={ev.fotos} onAbrir={setFotoAberta} />
            </article>
          ))}
        </div>
      </section>

      {/* convite */}
      <section className="py-14 px-4 bg-white text-center">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-2xl font-bold text-dark mb-3">Quer o SIGBEF no seu evento ou na sua escola?</h2>
          <p className="text-gray-500 mb-6">
            Fazemos demonstrações para escolas e redes de ensino, presenciais ou por chamada de vídeo.
          </p>
          <a href={LINKS.whatsapp} target="_blank" rel="noopener noreferrer"
            className="inline-block bg-primary text-white font-bold px-6 py-3 rounded-xl hover:bg-dark transition-colors">
            Falar com a equipe
          </a>
        </div>
      </section>

      {/* lightbox simples */}
      {fotoAberta && (
        <div role="dialog" aria-modal="true" aria-label={fotoAberta.alt}
          className="fixed inset-0 z-[60] bg-black/80 flex items-center justify-center p-4 overscroll-contain"
          onClick={() => setFotoAberta(null)}>
          <button type="button" aria-label="Fechar foto ampliada" ref={botaoFechar}
            className="absolute top-4 right-4 text-white/80 hover:text-white p-2"
            onClick={() => setFotoAberta(null)}>
            <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          <img src={fotoAberta.src} alt={fotoAberta.alt}
            className="max-w-full max-h-[85vh] rounded-lg shadow-2xl"
            onClick={e => e.stopPropagation()} />
        </div>
      )}
    </>
  )
}
