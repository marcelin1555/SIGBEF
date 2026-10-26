import { Link } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faMedal, faMicrophone, faFlask } from '@fortawesome/free-solid-svg-icons'
import { TituloSecao } from './ui'

const itens = [
  {
    icon: faMedal,
    quando: 'Outubro de 2026',
    titulo: '2º lugar estadual no Desafio Liga Jovem',
    texto: 'Competição do Sebrae, categoria Educação Profissional e Técnico, Rio Grande do Norte.',
  },
  {
    icon: faMicrophone,
    quando: 'Julho de 2026',
    titulo: 'V Seminário Estadual de EPT',
    texto: 'Projeto selecionado para apresentação no seminário e colóquio da rede estadual, em Natal.',
  },
  {
    icon: faFlask,
    quando: 'Dezembro de 2026',
    titulo: 'XVI Feira de Ciências do Semiárido Potiguar',
    texto: 'Indicado pela III FICTS para a feira em Mossoró, na categoria Juvenil.',
  },
]

export default function Reconhecimentos() {
  return (
    <section className="py-20 px-4 bg-gray-50">
      <div className="max-w-5xl mx-auto">
        <TituloSecao titulo="Reconhecimentos">Onde o SIGBEF já foi avaliado e apresentado.</TituloSecao>

        <div className="grid md:grid-cols-3 gap-6">
          {itens.map(i => (
            <article key={i.titulo} className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
              <div className="w-11 h-11 rounded-xl bg-ambar/15 text-dark flex items-center justify-center mb-4">
                <FontAwesomeIcon icon={i.icon} className="text-lg" />
              </div>
              <p className="text-xs font-bold uppercase tracking-wide text-primary mb-1">{i.quando}</p>
              <h3 className="font-bold text-gray-800 text-lg leading-snug mb-2">{i.titulo}</h3>
              <p className="text-gray-500 text-sm leading-relaxed">{i.texto}</p>
            </article>
          ))}
        </div>

        <div className="text-center mt-8">
          <Link to="/eventos" className="text-primary font-semibold hover:text-dark transition-colors">
            Ver fotos e todos os eventos
          </Link>
        </div>
      </div>
    </section>
  )
}
