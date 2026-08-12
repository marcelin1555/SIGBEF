import Equipe from '../components/Equipe'

const linha_do_tempo = [
  { ano: 'jan/26', evento: 'Marcello identifica o problema, a biblioteca do CEFE controlava tudo em planilha, e começa o SIGBEF durante as aulas de Banco de Dados.' },
  { ano: 'mar/26', evento: 'Primeira versão funcional testada na biblioteca do CEFE com a bibliotecária Jaqueline Dantas.' },
  { ano: 'abr/26', evento: 'A equipe DLJ4 se forma: Júlia e Maria Laura entram no projeto para o desafio do Sebrae.' },
  { ano: 'mai/26', evento: 'SIGBEF v1.2.0 lançado com instalador Windows, kiosk e sistema de multas.' },
  { ano: 'jun/26', evento: 'v1.3.0: site oficial multi-página no ar, com ícones e novo hero.' },
  { ano: 'jul/26', evento: 'v1.4.0: importação de acervo por CSV, cartão do aluno, etiquetas em massa e edição de usuários.' },
  { ano: 'jul/26', evento: 'v1.5.0: distribuição multiplataforma, com pacotes para Windows, Linux e macOS em cada release.' },
  { ano: 'jul/26', evento: 'v1.6.0: reservas com fila de espera e API REST somente leitura, para outros sistemas da escola consultarem o acervo.' },
  { ano: 'jul/26', evento: 'v1.6.2: identidade visual completa, com brasão da escola e temas de cor personalizáveis.' },
  { ano: 'jul/26', evento: 'A equipe apresenta o SIGBEF no V Seminário e II Colóquio de EPT da Rede Estadual do RN, em Natal — e sai de lá com os primeiros convites de outras escolas.' },
  { ano: 'jul/26', evento: 'v1.7.0: aplicativo Android do aluno — carteirinha digital, empréstimos e prazos no bolso, funcionando offline.' },
  { ano: 'jul/26', evento: 'v1.8.0: conferência do acervo, baixa de exemplar individual e backup automático do banco de dados.' },
  { ano: 'jul/26', evento: 'v1.9.0: devolução em lote no balcão e aviso de vencimento no celular do aluno.' },
  { ano: 'ago/26', evento: 'Cinco funções pedidas pela bibliotecária Laiane Ramos: reiniciar o sistema para instalar em outra escola, editar livros do acervo, excluir em massa, editar a localização do exemplar e mostrar a prateleira na etiqueta.' },
  { ano: 'ago/26', evento: 'A equipe prepara a inscrição na III FICTS e I FECETS, feira de iniciação científica do Seridó, com apresentação presencial em Caicó no dia 16 de setembro.' },
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
              <div key={item.evento} className="relative">
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
          <div aria-hidden="true" className="text-4xl mb-4">🏫</div>
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
