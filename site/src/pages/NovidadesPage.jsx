import { Link } from 'react-router-dom'

const CATEGORIA_COR = {
  Acervo: 'bg-blue-50 text-blue-700',
  Usuários: 'bg-purple-50 text-purple-700',
  Interface: 'bg-pink-50 text-pink-700',
  Robustez: 'bg-emerald-50 text-emerald-700',
  Site: 'bg-amber-50 text-amber-700',
  Segurança: 'bg-red-50 text-red-700',
  Multiplataforma: 'bg-indigo-50 text-indigo-700',
  API: 'bg-cyan-50 text-cyan-700',
}

function Badge({ texto }) {
  return (
    <span className={`inline-block text-xs font-bold px-2.5 py-1 rounded-full mr-2 mb-2 ${CATEGORIA_COR[texto] || 'bg-gray-100 text-gray-600'}`}>
      {texto}
    </span>
  )
}

const versoes = [
  {
    numero: '1.6.1',
    data: '18 de julho de 2026',
    destaque: true,
    categorias: ['Acervo', 'Interface'],
    itens: [
      { cat: 'Acervo', texto: 'Aviso por e-mail também quando o livro reservado fica separado para retirada (opt-in, junto com o aviso de vencimento)' },
      { cat: 'Acervo', texto: 'Busca avançada no acervo: filtro por categoria na pesquisa da bibliotecária e do aluno, além do texto livre' },
      { cat: 'Acervo', texto: 'Importação por planilha preserva o número de tombo do livro físico, que também serve para emprestar no balcão' },
      { cat: 'Interface', texto: 'Tela de Configurações mais limpa, sem bordas duplicadas nos blocos internos' },
    ],
  },
  {
    numero: '1.6.0',
    data: '10 de julho de 2026',
    categorias: ['Acervo', 'API', 'Segurança', 'Interface'],
    itens: [
      { cat: 'Acervo', texto: 'Reservas com fila de espera: peça um livro emprestado assim que ele voltar, sem precisar checar toda hora' },
      { cat: 'API', texto: 'API REST somente leitura (opt-in) para outros sistemas da escola consultarem acervo e empréstimos' },
      { cat: 'Acervo', texto: 'Avisos de vencimento por e-mail (opt-in), lembrando o leitor alguns dias antes do prazo' },
      { cat: 'Segurança', texto: 'Login mais resistente a ataques de força bruta e enumeração de matrícula' },
      { cat: 'Interface', texto: 'Devolução com um clique na tela de empréstimos abertos, sem digitar código' },
    ],
  },
  {
    numero: '1.5.1',
    data: '8 de julho de 2026',
    categorias: ['Robustez'],
    itens: [
      { cat: 'Robustez', texto: 'Melhorias internas de código e organização, sem mudança no uso do sistema.' },
    ],
  },
  {
    numero: '1.5.0',
    data: '8 de julho de 2026',
    categorias: ['Multiplataforma', 'Site'],
    itens: [
      { cat: 'Multiplataforma', texto: 'O SIGBEF agora é oficialmente multiplataforma: além do instalador para Windows, cada versão traz pacote portátil para Windows, .tar.gz para Linux e aplicativo nativo para macOS' },
      { cat: 'Multiplataforma', texto: 'Os pacotes das 3 plataformas passam a ser gerados e publicados automaticamente a cada nova versão, direto na página de releases' },
      { cat: 'Site', texto: 'Guia de instalação e requisitos atualizados com os novos sistemas suportados' },
    ],
  },
  {
    numero: '1.4.0',
    data: '2 de julho de 2026',
    categorias: ['Acervo', 'Usuários', 'Interface', 'Robustez', 'Site'],
    itens: [
      { cat: 'Acervo', texto: 'Importação de acervo em massa via planilha CSV, com modelo pronto para baixar e proteção contra livro duplicado' },
      { cat: 'Acervo', texto: 'Impressão de etiquetas de código de barras de todo o acervo (ou de uma busca) numa página só' },
      { cat: 'Acervo', texto: 'Exclusão de livros do acervo, preservando o histórico de empréstimos já realizados' },
      { cat: 'Usuários', texto: 'Edição de cadastro: nome, contato, perfil e série/turma — útil na virada de ano letivo' },
      { cat: 'Usuários', texto: 'Exclusão de usuários sem histórico, com proteção contra remoção acidental do próprio acesso' },
      { cat: 'Usuários', texto: 'Impressão do cartão de biblioteca com código de barras, no tamanho padrão de crachá' },
      { cat: 'Interface', texto: 'Tema visual refinado: tabelas mais legíveis, destaque nos campos em uso e efeitos visuais que se adaptam a qualquer paleta de cores escolhida' },
      { cat: 'Robustez', texto: 'Correção de uma falha rara em que dois terminais emprestando o mesmo livro ao mesmo tempo podiam gerar conflito' },
      { cat: 'Robustez', texto: 'Busca no acervo muito mais rápida em bibliotecas com acervo grande' },
      { cat: 'Site', texto: 'Contato direto por WhatsApp em todo o site' },
    ],
  },
  {
    numero: '1.3.0',
    data: '25 de junho de 2026',
    categorias: ['Site'],
    itens: [
      { cat: 'Site', texto: 'Site oficial reconstruído: 5 páginas (Home, Funcionalidades, Como instalar, Planos, Equipe) em vez de uma landing única' },
      { cat: 'Site', texto: 'Novo hero com mockup do painel do SIGBEF e ícones profissionais em todo o site' },
      { cat: 'Site', texto: 'Página de planos com FAQ de preços e página de equipe com linha do tempo do projeto' },
    ],
  },
  {
    numero: '1.2.0',
    data: '24 de maio de 2026',
    categorias: ['Usuários'],
    itens: [
      { cat: 'Usuários', texto: 'Campo "Série / Turma" no cadastro de aluno, pedido pela própria biblioteca do CEFE' },
      { cat: 'Acervo', texto: 'Integração opcional com Google Books e Open Library para preencher o cadastro de um livro automaticamente pelo ISBN, mantendo o sistema 100% funcional offline para quem não usar' },
      { cat: 'Robustez', texto: 'Bibliotecas com banco de dados de versões anteriores são atualizadas automaticamente, sem precisar recadastrar nada' },
    ],
  },
  {
    numero: '1.1.0',
    data: '22 de maio de 2026',
    categorias: ['Interface'],
    itens: [
      { cat: 'Interface', texto: 'Personalização de cores: 5 paletas prontas (incluindo Verde Floresta e Roxo Universitário) ou cores escolhidas manualmente pela escola' },
      { cat: 'Interface', texto: 'Tela de Configurações ganhou rolagem, evitando conteúdo cortado em telas menores' },
      { cat: 'Acervo', texto: 'Dados de demonstração com nomes realistas, para facilitar apresentações e testes' },
    ],
  },
  {
    numero: '1.0.0',
    data: '5 de maio de 2026',
    categorias: ['Segurança'],
    itens: [
      { cat: 'Segurança', texto: 'Primeira versão estável, pronta para uso em produção — removidas credenciais de demonstração da tela de login' },
      { cat: 'Acervo', texto: 'Cadastro completo de livros e usuários, com geração automática de código de barras para exemplares e cartões' },
      { cat: 'Usuários', texto: 'Empréstimos e devoluções com cálculo automático de multa, no balcão ou no terminal de autoatendimento' },
      { cat: 'Interface', texto: 'Relatórios de acervo, empréstimos e usuários exportáveis em CSV' },
      { cat: 'Segurança', texto: 'Senhas protegidas com hash PBKDF2-SHA256 e sal aleatório' },
    ],
  },
]

export default function NovidadesPage() {
  return (
    <>
      {/* page header */}
      <div className="bg-gradient-to-br from-[#1F4E79] to-[#2E75B6] text-white py-14 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-blue-200 text-sm font-semibold uppercase tracking-widest mb-3">Changelog</p>
          <h1 className="text-4xl sm:text-5xl font-bold mb-4">Novidades</h1>
          <p className="text-blue-100 text-lg max-w-2xl mx-auto">
            O SIGBEF está em desenvolvimento ativo. Veja tudo que já mudou, versão por versão.
          </p>
        </div>
      </div>

      <section className="py-16 px-4 bg-white">
        <div className="max-w-3xl mx-auto space-y-12">
          {versoes.map((v, i) => (
            <div key={v.numero} className="relative">
              <div className="flex flex-wrap items-baseline gap-3 mb-1">
                <h2 className="text-2xl font-bold text-[#1F4E79]">
                  v{v.numero}
                </h2>
                {i === 0 && (
                  <span className="bg-yellow-400 text-[#1F4E79] text-xs font-bold px-2.5 py-1 rounded-full">
                    Versão atual
                  </span>
                )}
                <span className="text-gray-400 text-sm">{v.data}</span>
              </div>

              <div className="mb-4">
                {v.categorias.map(c => <Badge key={c} texto={c} />)}
              </div>

              <ul className="space-y-2.5 border-l-2 border-gray-100 pl-5">
                {v.itens.map((item, idx) => (
                  <li key={idx} className="text-gray-600 text-[15px] leading-relaxed relative">
                    <span className="absolute -left-[1.45rem] top-2 w-2 h-2 rounded-full bg-[#2E75B6]" />
                    {item.texto}
                  </li>
                ))}
              </ul>

              {i < versoes.length - 1 && <div className="border-b border-gray-100 mt-10" />}
            </div>
          ))}
        </div>
      </section>

      {/* cta */}
      <section className="py-16 px-4 bg-gray-50 text-center">
        <h2 className="text-2xl font-bold text-[#1F4E79] mb-3">Quer testar a versão mais recente?</h2>
        <p className="text-gray-500 mb-6">Gratuito, offline, sem cadastro.</p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <a href="https://github.com/marcelin1555/SIGBEF/releases" target="_blank" rel="noopener noreferrer"
            className="bg-[#2E75B6] text-white font-bold px-8 py-3.5 rounded-xl hover:bg-[#1F4E79] transition-colors shadow-md">
            Baixar SIGBEF
          </a>
          <Link to="/funcionalidades"
            className="border-2 border-gray-300 text-gray-700 font-semibold px-8 py-3.5 rounded-xl hover:border-[#2E75B6] hover:text-[#2E75B6] transition-colors">
            Ver funcionalidades
          </Link>
        </div>
      </section>
    </>
  )
}
