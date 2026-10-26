import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faBookOpen, faScaleBalanced } from '@fortawesome/free-solid-svg-icons'
import { LINKS } from '../config'

export default function ODS() {
  return (
    <section className="py-20 px-4 bg-dark text-white">
      <div className="max-w-4xl mx-auto text-center">
        <h2 className="text-3xl sm:text-4xl font-bold mb-4">Impacto que vai além da biblioteca</h2>
        <p className="text-blue-200 text-lg mb-12 max-w-2xl mx-auto">
          O SIGBEF se alinha a dois Objetivos de Desenvolvimento Sustentável da ONU.
        </p>

        <div className="grid sm:grid-cols-2 gap-6 mb-12">
          <div className="bg-white/10 rounded-2xl p-8 border border-white/20">
            <div className="w-16 h-16 rounded-2xl bg-blue-400/30 flex items-center justify-center mx-auto mb-4">
              <FontAwesomeIcon icon={faBookOpen} className="text-3xl text-ambar-claro" />
            </div>
            <div className="text-ambar-claro font-bold text-lg mb-1">ODS 4</div>
            <div className="font-bold text-xl mb-3">Educação de Qualidade</div>
            <p className="text-blue-100 text-sm leading-relaxed">
              Garante acesso funcional ao acervo da biblioteca escolar, base essencial para o aprendizado.
            </p>
          </div>
          <div className="bg-white/10 rounded-2xl p-8 border border-white/20">
            <div className="w-16 h-16 rounded-2xl bg-blue-400/30 flex items-center justify-center mx-auto mb-4">
              <FontAwesomeIcon icon={faScaleBalanced} className="text-3xl text-ambar-claro" />
            </div>
            <div className="text-ambar-claro font-bold text-lg mb-1">ODS 10</div>
            <div className="font-bold text-xl mb-3">Redução das Desigualdades</div>
            <p className="text-blue-100 text-sm leading-relaxed">
              Leva para a escola pública, de graça, um tipo de sistema que costuma ser pago.
            </p>
          </div>
        </div>

        <blockquote className="text-xl sm:text-2xl font-semibold italic text-ambar-claro max-w-2xl mx-auto mb-10">
          "Escola pública brasileira merece a mesma tecnologia que escola privada tem."
        </blockquote>

        <a href={LINKS.download} target="_blank" rel="noopener noreferrer"
          className="inline-block bg-ambar text-dark font-bold px-10 py-4 rounded-xl text-lg hover:bg-ambar-claro transition-colors shadow-lg">
          Baixar agora, é gratuito
        </a>
      </div>
    </section>
  )
}
