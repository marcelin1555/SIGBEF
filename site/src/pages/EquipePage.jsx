import Equipe from '../components/Equipe'

const linha_do_tempo = [
  { ano: '2024', evento: 'Marcello identifica o problema: a biblioteca do CEFE usava planilhas para controlar empréstimos.' },
  { ano: 'jan/25', evento: 'Início do desenvolvimento do SIGBEF como projeto pessoal durante as aulas de Banco de Dados.' },
  { ano: 'mar/25', evento: 'Primeira versão funcional testada na biblioteca do CEFE com a bibliotecária Jaqueline Oliveira.' },
  { ano: 'abr/25', evento: 'A equipe DLJ4 se forma: Júlia e Maria Laura entram no projeto para o desafio do Sebrae.' },
  { ano: 'jun/25', evento: 'SIGBEF v1.2.0 lançado com instalador Windows, kiosk e sistema de multas.' },
]

export default function EquipePage() {
  return (
    <>
      {/* page header */}
      <div className="bg-gradient-to-br from-[#1F4E79] to-[#2E75B6] text-white py-14 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-blue-200 text-sm font-semibold uppercase tracking-widest mb-3">Sobre</p>
          <h1 className="text-4xl sm:text-5xl font-bold mb-4">Equipe</h1>
          <p className="text-blue-100 text-lg max-w-2xl mx-auto">
            Estudantes do CEFE, escola pública do Rio Grande do Norte, que decidiram resolver um problema real da própria escola.
          </p>
        </div>
      </div>

      <Equipe />

      {/* linha do tempo */}
      <section className="py-20 px-4 bg-white">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-[#1F4E79] mb-10 text-center">História do projeto</h2>
          <div className="relative pl-8 border-l-2 border-gray-200 space-y-8">
            {linha_do_tempo.map(item => (
              <div key={item.ano} className="relative">
                <span className="absolute -left-[2.25rem] top-0.5 w-5 h-5 rounded-full bg-[#2E75B6] border-2 border-white shadow" />
                <div className="text-xs font-bold text-[#2E75B6] uppercase tracking-wide mb-1">{item.ano}</div>
                <p className="text-gray-600 text-sm leading-relaxed">{item.evento}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* missão */}
      <section className="py-16 px-4 bg-[#1F4E79] text-white text-center">
        <div className="max-w-2xl mx-auto">
          <div className="text-4xl mb-4">🏫</div>
          <blockquote className="text-xl sm:text-2xl font-semibold italic text-yellow-300 mb-4">
            "Escola pública brasileira merece a mesma tecnologia que escola privada tem."
          </blockquote>
          <p className="text-blue-200 text-sm">
            O SIGBEF nasceu dessa convicção. É livre, é aberto, e vai continuar sendo.
          </p>
        </div>
      </section>
    </>
  )
}
