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
    numero: '1.13.0',
    data: '10 de setembro de 2026',
    destaque: true,
    categorias: ['Acervo', 'Robustez'],
    itens: [
      { cat: 'Acervo', texto: 'Adicionar exemplares a um livro que já está no acervo: chegou mais uma leva do mesmo livro-texto, os exemplares entram no registro que já existe em vez de virar um título duplicado na busca' },
      { cat: 'Acervo', texto: 'A janela pergunta quantos, a prateleira e — opcional — os números de tombo já escritos nas cópias novas, no mesmo formato do cadastro' },
      { cat: 'Acervo', texto: 'Exemplar novo de livro com fila de espera já sai separado para quem espera' },
      { cat: 'Robustez', texto: 'A numeração automática de tombo podia repetir um número: ela contava exemplares em vez de olhar o maior número já usado, e um tombo corrigido na mão fazia a leva seguinte gerar o mesmo. Tombo repetido faz o balcão emprestar a cópia errada — agora a sequência pula número ocupado' },
    ],
  },
  {
    numero: '1.12.2',
    data: '4 de setembro de 2026',
    categorias: ['Acervo', 'Robustez'],
    itens: [
      { cat: 'Acervo', texto: 'Liberar um número de tombo para reaproveitar em outro exemplar, sem precisar dar baixa nem excluir o livro — a função já existia escondida em "deixe em branco para tirar o tombo", agora é um botão com esse nome' },
      { cat: 'Acervo', texto: 'Excluir um livro do acervo passa a perguntar se os números de tombo dele devem ficar livres para reuso, com "não" por padrão — antes ficavam presos para sempre, porque o livro sumia de toda tela' },
      { cat: 'Robustez', texto: 'Dar baixa continua sem liberar o tombo sozinha, de propósito: é a regra que impede dois exemplares com o mesmo número' },
      { cat: 'Robustez', texto: 'A janela de corrigir tombo cortava os botões Salvar e Cancelar fora da tela — corrigida' },
    ],
  },
  {
    numero: '1.12.1',
    data: '4 de setembro de 2026',
    categorias: ['Robustez'],
    itens: [
      { cat: 'Robustez', texto: 'Reverter baixa: desfaz uma baixa dada por engano, devolvendo o exemplar ao acervo com a situação certa (emprestado ou disponível)' },
      { cat: 'Robustez', texto: 'A multa lançada pela baixa é apagada — ela nunca deveria ter sido cobrada — e quem perdeu a reserva por causa da baixa volta para a fila na mesma posição' },
      { cat: 'Interface', texto: '"Dar baixa no exemplar" ganhou cor de perigo e saiu de perto de "Corrigir tombo" e "Mudar prateleira", que tinham a mesma aparência e causaram o clique errado' },
    ],
  },
  {
    numero: '1.12.0',
    data: '3 de setembro de 2026',
    categorias: ['Acervo', 'Robustez', 'Multiplataforma'],
    itens: [
      { cat: 'Robustez', texto: 'Restaurar uma cópia de segurança pela própria tela: Configurações → Ferramentas. Compara o banco de hoje com o do arquivo antes de qualquer coisa e exige a palavra RESTAURAR digitada' },
      { cat: 'Acervo', texto: 'Empréstimo de coleção: o professor leva a turma inteira com uma linha na tela, prazo de bimestre, sem esbarrar no limite de empréstimos simultâneos' },
      { cat: 'Acervo', texto: 'Isentar multa, com motivo obrigatório — o valor lançado continua no histórico, diferente de quitar' },
      { cat: 'Robustez', texto: 'Cadastro de livro pela tela passa a recusar ano inválido e ISBN repetido, do mesmo jeito que a importação por planilha já fazia' },
      { cat: 'Robustez', texto: 'Cartão de alerta que ficava preso na cor vermelha mesmo com o atraso zerado — corrigido' },
      { cat: 'Robustez', texto: 'As 14 tabelas do sistema ganharam barra de rolagem própria, vertical sempre e horizontal quando as colunas não cabem' },
      { cat: 'Multiplataforma', texto: 'Tema escuro de verdade no aplicativo Android: as telas usavam as cores do tema claro mesmo com o celular no escuro' },
    ],
  },
  {
    numero: '1.11.0',
    data: '27 de agosto de 2026',
    categorias: ['Acervo', 'Robustez', 'Multiplataforma'],
    itens: [
      { cat: 'Acervo', texto: 'Devolução em lote corrigida: anunciada na v1.9.0, o botão nunca chegou a funcionar de fato, e ficou quase um mês assim sem ninguém perceber' },
      { cat: 'Acervo', texto: 'Quitar multa parou de apagar o próprio histórico — o valor lançado agora fica registrado mesmo depois de recebido' },
      { cat: 'Acervo', texto: 'Isenção de multa (primeira versão), com motivo obrigatório' },
      { cat: 'Robustez', texto: 'Tela de Configurações passa a validar antes de gravar, e aceita vírgula nos valores em reais' },
      { cat: 'Robustez', texto: 'Janela do painel forçada maior que a tela em notebooks pequenos — corrigida' },
      { cat: 'Robustez', texto: 'Autoatendimento: Enter no campo do cartão disparava duas ações ao mesmo tempo — corrigido' },
      { cat: 'Multiplataforma', texto: 'Aplicativo do aluno: corrigida a quebra no Android 7, a câmera que ficava presa ao sair do leitor de QR, e o status de atraso que congelava sem rede' },
    ],
  },
  {
    numero: '1.10.4',
    data: '18 de agosto de 2026',
    categorias: ['Interface', 'Robustez'],
    itens: [
      { cat: 'Interface', texto: 'Formulário de cadastrar livro mais compacto: Editora/Categoria, Ano/Edição e Localização/Quantidade lado a lado, sinopse menor. A janela cai de 790 para 600 pixels de altura' },
      { cat: 'Robustez', texto: 'Nenhum diálogo do sistema nasce maior que a tela do computador — corrigido para os 14 diálogos que existem, não só o de cadastro' },
      { cat: 'Robustez', texto: 'O formulário de cadastrar livro ganhou rolagem com os botões sempre visíveis, como reforço para telas ainda menores' },
    ],
  },
  {
    numero: '1.10.3',
    data: '12 de agosto de 2026',
    categorias: ['Robustez'],
    itens: [
      { cat: 'Robustez', texto: 'Tela de auditoria: quem fez o quê no sistema, mais recente primeiro. O registro é gravado desde a v1.0; até agora não havia como consultar' },
      { cat: 'Robustez', texto: 'Busca livre por ação, detalhes ou nome de quem fez, mais um filtro por uma ação específica' },
      { cat: 'Robustez', texto: 'Só leitura: nenhuma regra do sistema muda, a tela só mostra o que já era gravado' },
    ],
  },
  {
    numero: '1.10.2',
    data: '12 de agosto de 2026',
    categorias: ['Acervo'],
    itens: [
      { cat: 'Acervo', texto: 'O tombo pode ser informado já no cadastro do livro. O exemplar costuma chegar com o número escrito, e antes era preciso cadastrar, deixar o sistema gerar e corrigir depois, um por um' },
      { cat: 'Acervo', texto: 'O campo é opcional: em branco, o sistema continua gerando o número. Para vários exemplares, separe por ; na ordem, como na importação por planilha' },
      { cat: 'Acervo', texto: 'Tombo repetido continua sendo recusado, dizendo qual livro já está com aquele número' },
    ],
  },
  {
    numero: '1.10.1',
    data: '12 de agosto de 2026',
    categorias: ['Acervo', 'Robustez'],
    itens: [
      { cat: 'Acervo', texto: 'Corrigir o tombo do exemplar: botão novo nos detalhes do livro. O código de barras, os empréstimos e o histórico ficam como estavam, só o número muda' },
      { cat: 'Robustez', texto: 'O tombo não pode repetir. O balcão procura o exemplar por código de barras ou por tombo, então dois iguais fariam o empréstimo registrar o livro errado sem avisar. Agora o sistema recusa e diz qual livro já está com aquele número' },
      { cat: 'Acervo', texto: 'Etiquetas em massa passa a respeitar o que está marcado na lista: chegaram seis livros novos, marca os seis e imprime seis. Sem nada marcado, continua imprimindo a busca atual' },
      { cat: 'Acervo', texto: 'A confirmação diz qual dos três casos vai imprimir, para não gastar papel por engano' },
    ],
  },
  {
    numero: '1.10.0',
    data: '11 de agosto de 2026',
    categorias: ['Acervo', 'Robustez', 'Site'],
    itens: [
      { cat: 'Acervo', texto: 'Editar livros do acervo: dá para corrigir título, autores, ISBN, editora, categoria, ano e sinopse de um livro já cadastrado, sem perder exemplares nem histórico' },
      { cat: 'Acervo', texto: 'Excluir vários livros de uma vez. Um livro com exemplar emprestado é barrado sozinho, sem cancelar os outros, e no fim aparece o resumo do que saiu e do que ficou' },
      { cat: 'Acervo', texto: 'A localização do exemplar pode ser editada, e a etiqueta de código de barras passa a imprimir a prateleira: a estante certa vai colada no livro' },
      { cat: 'Robustez', texto: 'Reiniciar o sistema: apaga acervo, usuários e empréstimos de teste e volta ao estado de instalação nova, para começar a usar de verdade ou instalar em outra escola' },
      { cat: 'Robustez', texto: 'A reinicialização exige digitar APAGAR TUDO por extenso e faz backup antes. Se o backup falhar, nada é apagado' },
      { cat: 'Site', texto: 'A página de Eventos passa a mostrar os próximos eventos, começando pela III FICTS e I FECETS de 16 de setembro, em Caicó' },
    ],
  },
  {
    numero: '1.9.0',
    data: '27 de julho de 2026',
    categorias: ['Acervo', 'Multiplataforma'],
    itens: [
      { cat: 'Acervo', texto: 'Devolução em lote: no fim do ano, vá passando o leitor na pilha inteira — cada leitura devolve na hora, sem confirmar um por um' },
      { cat: 'Acervo', texto: 'Um livro recusado no meio da pilha não interrompe os outros; o aviso aparece e a devolução continua' },
      { cat: 'Acervo', texto: 'No fim, os livros que têm fila de espera aparecem separados: são os que não voltam para a estante' },
      { cat: 'Multiplataforma', texto: 'O aplicativo avisa quando o prazo de devolução está chegando. O cálculo é feito no próprio celular: funciona em casa, no fim de semana e sem internet' },
      { cat: 'Multiplataforma', texto: 'O aviso nasce desligado — o aluno liga no cartão digital, quando quiser' },
    ],
  },
  {
    numero: '1.8.0',
    data: '27 de julho de 2026',
    categorias: ['Acervo', 'Interface', 'Robustez'],
    itens: [
      { cat: 'Acervo', texto: 'Conferência do acervo: passe o leitor na estante e receba a lista do que não foi encontrado, do que está emprestado e do que apareceu sem estar previsto' },
      { cat: 'Acervo', texto: 'Baixa de exemplar individual, com motivo (extraviado, danificado, descartado ou doado), sem tirar o título inteiro do acervo' },
      { cat: 'Acervo', texto: 'Livro perdido pelo aluno: dar baixa encerra o empréstimo e lança a multa, sem esperar uma devolução que não vai acontecer' },
      { cat: 'Interface', texto: 'Relatórios por período, com atalhos para este mês, este bimestre e este ano' },
      { cat: 'Interface', texto: 'Novo relatório de movimentação: empréstimos, devoluções, atrasos e multas do período, por mês e por turma — o número que a direção pede' },
      { cat: 'Robustez', texto: 'Cópia de segurança automática ao fechar o sistema, guardando as últimas 7 e apagando as antigas sozinha' },
      { cat: 'Robustez', texto: 'O backup passou a usar a função do próprio banco de dados, garantindo uma cópia consistente mesmo com o balcão trabalhando' },
    ],
  },
  {
    numero: '1.7.1',
    data: '27 de julho de 2026',
    categorias: ['Robustez', 'API'],
    itens: [
      { cat: 'Robustez', texto: 'O sistema passa a aguentar acervos de até 250 mil livros, com a biblioteca inteira usando ao mesmo tempo: balcão, autoatendimento e uma turma no celular' },
      { cat: 'Robustez', texto: 'A tela do acervo abre na hora mesmo em bibliotecas grandes, carregando por blocos em vez de montar a lista toda de uma vez' },
      { cat: 'Robustez', texto: 'Empréstimo de balcão ficou mais rápido em acervos grandes: a busca do exemplar pelo número de tombo agora usa índice' },
      { cat: 'Robustez', texto: 'Uma turma inteira consegue abrir o aplicativo no mesmo minuto sem receber "sem conexão com a biblioteca"' },
      { cat: 'Robustez', texto: 'No aplicativo, o catálogo continua disponível enquanto uma nova sincronização acontece — e sobrevive a uma queda de rede no meio' },
      { cat: 'API', texto: 'A rota do acervo passa a responder em páginas. Quem integra outro sistema precisa iterar as páginas; veja docs/API.md' },
    ],
  },
  {
    numero: '1.7.0',
    data: '26 de julho de 2026',
    categorias: ['Multiplataforma', 'API', 'Acervo', 'Interface'],
    itens: [
      { cat: 'Multiplataforma', texto: 'Aplicativo Android do aluno (v0.1): carteirinha digital com código de barras real, acervo, empréstimos e prazos no bolso — funcionando offline depois da primeira sincronização' },
      { cat: 'Multiplataforma', texto: 'Para conectar o celular, basta apontar a câmera para o QR code que a biblioteca mostra na tela' },
      { cat: 'Acervo', texto: 'Reserva e renovação pelo celular: o aluno entra na fila de um livro emprestado e renova o que está com ele, sem ir ao balcão' },
      { cat: 'Acervo', texto: 'Regras de renovação explícitas: não renova livro atrasado, com alguém na fila ou acima do limite. No balcão a bibliotecária continua podendo renovar em qualquer situação' },
      { cat: 'Interface', texto: 'Fila de espera no painel: quem espera cada livro, a posição de cada um e quais exemplares já estão separados aguardando retirada' },
      { cat: 'Interface', texto: 'Painel Uso do acervo: empréstimos por mês, por turma e por categoria, taxa de atraso e a lista dos livros que nunca saíram da estante' },
      { cat: 'Interface', texto: 'Relatório de pendências dos leitores: quem está com livro atrasado ou multa em aberto, com turma e e-mail para a cobrança' },
      { cat: 'Multiplataforma', texto: 'Minha leitura no app: quanto o aluno já leu, a categoria preferida dele e sugestões de próximos livros com o motivo de cada uma' },
      { cat: 'API', texto: 'A API passa a aceitar três gravações — entrar na fila, sair da fila e renovar —, sempre nos dados do próprio aluno logado. O acervo segue intocável pela rede' },
    ],
  },
  {
    numero: '1.6.2',
    data: '19 de julho de 2026',
    categorias: ['Interface'],
    itens: [
      { cat: 'Interface', texto: 'Identidade visual completa: logo do SIGBEF no login, no autoatendimento e no assistente inicial, e como ícone das janelas' },
      { cat: 'Interface', texto: 'Brasão da própria escola configurável, exibido no login, no cabeçalho e no autoatendimento' },
      { cat: 'Interface', texto: 'Ícones vetoriais na sidebar, nos cards e nos botões de ação, no lugar de símbolos de texto' },
      { cat: 'Interface', texto: 'As paletas de cores personalizadas agora se aplicam a todas as telas de forma consistente, com proteção contra cores que deixariam o texto ilegível' },
    ],
  },
  {
    numero: '1.6.1',
    data: '18 de julho de 2026',
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
