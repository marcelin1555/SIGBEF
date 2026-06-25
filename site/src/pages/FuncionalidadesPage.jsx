import { Link } from 'react-router-dom'
import Funcionalidades from '../components/Funcionalidades'
import Comparativo from '../components/Comparativo'

export default function FuncionalidadesPage() {
  return (
    <>
      {/* page header */}
      <div className="bg-gradient-to-br from-[#1F4E79] to-[#2E75B6] text-white py-14 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-blue-200 text-sm font-semibold uppercase tracking-widest mb-3">Produto</p>
          <h1 className="text-4xl sm:text-5xl font-bold mb-4">Funcionalidades</h1>
          <p className="text-blue-100 text-lg max-w-2xl mx-auto">
            Tudo que um sistema de biblioteca escolar precisa, sem custo e sem complicação.
          </p>
        </div>
      </div>

      <Funcionalidades />
      <Comparativo />

      {/* cta */}
      <section className="py-16 px-4 bg-white text-center">
        <h2 className="text-2xl font-bold text-[#1F4E79] mb-3">Pronto para começar?</h2>
        <p className="text-gray-500 mb-6">Instala em 5 minutos, funciona sem internet.</p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <a href="https://github.com/marcelin1555/SIGBEF/releases" target="_blank" rel="noopener noreferrer"
            className="bg-[#2E75B6] text-white font-bold px-8 py-3.5 rounded-xl hover:bg-[#1F4E79] transition-colors shadow-md">
            Baixar grátis
          </a>
          <Link to="/download"
            className="border-2 border-gray-300 text-gray-700 font-semibold px-8 py-3.5 rounded-xl hover:border-[#2E75B6] hover:text-[#2E75B6] transition-colors">
            Guia de instalação
          </Link>
        </div>
      </section>
    </>
  )
}
