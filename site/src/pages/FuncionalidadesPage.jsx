import { Link } from 'react-router-dom'
import Funcionalidades from '../components/Funcionalidades'
import Plataformas from '../components/Plataformas'
import Comparativo from '../components/Comparativo'
import { LINKS } from '../config'
import { CabecalhoPagina } from '../components/ui'

export default function FuncionalidadesPage() {
  return (
    <>
      {/* page header */}
      <CabecalhoPagina rotulo="Produto" titulo="Funcionalidades">
        Tudo que um sistema de biblioteca escolar precisa, sem custo e sem complicação.
      </CabecalhoPagina>

      <Funcionalidades />
      <Plataformas />
      <Comparativo />

      {/* cta */}
      <section className="py-16 px-4 bg-white text-center">
        <h2 className="text-2xl font-bold text-dark mb-3">Pronto para começar?</h2>
        <p className="text-gray-500 mb-6">Instala em 5 minutos, funciona sem internet.</p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <a href={LINKS.download} target="_blank" rel="noopener noreferrer"
            className="bg-primary text-white font-bold px-8 py-3.5 rounded-xl hover:bg-dark transition-colors shadow-md">
            Baixar grátis
          </a>
          <Link to="/download"
            className="border-2 border-gray-300 text-gray-700 font-semibold px-8 py-3.5 rounded-xl hover:border-primary hover:text-primary transition-colors">
            Guia de instalação
          </Link>
        </div>
      </section>
    </>
  )
}
