const requisitos = [
  { label: 'Sistema operacional', valor: 'Windows 7 a 11, Linux (x64) ou macOS' },
  { label: 'Espaço em disco', valor: 'Mínimo 100 MB livres' },
  { label: 'RAM', valor: 'Mínimo 512 MB (recomendado 1 GB)' },
  { label: 'Internet', valor: 'Não precisa — funciona 100% offline' },
  { label: 'Permissões', valor: 'Administrador para instalar; usuário normal para usar' },
]

const passos = [
  {
    n: '1', titulo: 'Baixe o instalador',
    texto: 'Acesse a página de releases no GitHub e baixe o pacote do seu sistema: instalador SIGBEF_Setup.exe (Windows), .tar.gz (Linux) ou .zip (macOS). É gratuito, sem cadastro, sem condições.',
    link: 'https://github.com/marcelin1555/SIGBEF/releases',
    linkLabel: 'Ir para releases',
  },
  {
    n: '2', titulo: 'Execute o instalador',
    texto: 'Dê duplo clique no arquivo baixado. Clique em "Próximo" nas telas que aparecerem e em "Concluir" no final. O processo leva menos de 5 minutos.',
  },
  {
    n: '3', titulo: 'Abra o SIGBEF',
    texto: 'Um atalho será criado na Área de Trabalho. Clique nele para abrir. No primeiro acesso, o sistema cria o banco de dados automaticamente.',
  },
  {
    n: '4', titulo: 'Faça login',
    texto: 'Login inicial: usuário admin, senha admin. Troque a senha depois de entrar pela primeira vez. Crie os demais usuários no painel de configurações.',
  },
]

const faq = [
  {
    q: 'Funciona sem internet?',
    r: 'Sim, 100% offline. O banco de dados fica no próprio computador. Nenhum dado sai da escola.',
  },
  {
    q: 'Preciso instalar mais alguma coisa?',
    r: 'Não. O instalador inclui tudo: Python, SQLite e todas as bibliotecas necessárias.',
  },
  {
    q: 'Funciona em Mac ou Linux?',
    r: 'Sim. Além do instalador para Windows, cada release traz um pacote portátil para Linux (.tar.gz) e para macOS (.zip). Também é possível rodar direto do código-fonte com Python 3.10+.',
  },
  {
    q: 'Quantos usuários posso cadastrar?',
    r: 'Sem limite. O sistema suporta quantos alunos, professores e bibliotecários a escola precisar.',
  },
  {
    q: 'Vou perder os dados ao atualizar?',
    r: 'Não. O banco de dados fica numa pasta separada e não é sobrescrito na atualização. Recomendamos fazer backup antes de qualquer atualização.',
  },
  {
    q: 'Posso instalar em mais de um computador?',
    r: 'Sim. A licença MIT permite instalações ilimitadas. Cada computador terá seu próprio banco de dados (não há sincronização entre máquinas ainda).',
  },
]

export default function DownloadPage() {
  return (
    <>
      {/* page header */}
      <div className="bg-gradient-to-br from-[#1F4E79] to-[#2E75B6] text-white py-14 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-blue-200 text-sm font-semibold uppercase tracking-widest mb-3">Instalação</p>
          <h1 className="text-4xl sm:text-5xl font-bold mb-4">Como instalar</h1>
          <p className="text-blue-100 text-lg max-w-2xl mx-auto mb-8">
            Quatro passos, menos de 5 minutos, zero configuração de servidor.
          </p>
          <a href="https://github.com/marcelin1555/SIGBEF/releases" target="_blank" rel="noopener noreferrer"
            className="inline-block bg-yellow-400 text-[#1F4E79] font-bold px-8 py-3.5 rounded-xl text-lg hover:bg-yellow-300 transition-colors shadow-lg">
            Baixar SIGBEF (última versão)
          </a>
        </div>
      </div>

      {/* requisitos */}
      <section className="py-16 px-4 bg-gray-50">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-[#1F4E79] mb-6">Requisitos do sistema</h2>
          <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
            {requisitos.map((r, i) => (
              <div key={r.label} className={`flex gap-4 px-6 py-4 ${i < requisitos.length - 1 ? 'border-b border-gray-100' : ''}`}>
                <span className="text-gray-500 text-sm w-44 shrink-0">{r.label}</span>
                <span className="text-gray-800 text-sm font-medium">{r.valor}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* passos */}
      <section className="py-16 px-4 bg-white">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-[#1F4E79] mb-10">Passo a passo</h2>
          <div className="space-y-8">
            {passos.map(p => (
              <div key={p.n} className="flex gap-5">
                <div className="w-10 h-10 rounded-full bg-[#2E75B6] text-white font-bold flex items-center justify-center shrink-0 text-sm">
                  {p.n}
                </div>
                <div className="pt-1">
                  <h3 className="font-bold text-gray-800 text-lg mb-1">{p.titulo}</h3>
                  <p className="text-gray-500 leading-relaxed text-sm">{p.texto}</p>
                  {p.link && (
                    <a href={p.link} target="_blank" rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 mt-3 text-sm text-[#2E75B6] font-semibold hover:text-[#1F4E79]">
                      {p.linkLabel}
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* faq */}
      <section className="py-16 px-4 bg-gray-50">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-[#1F4E79] mb-8">Perguntas frequentes</h2>
          <div className="space-y-4">
            {faq.map(item => (
              <div key={item.q} className="bg-white rounded-xl border border-gray-200 px-6 py-5">
                <h3 className="font-semibold text-gray-800 mb-2">{item.q}</h3>
                <p className="text-gray-500 text-sm leading-relaxed">{item.r}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* cta */}
      <section className="py-14 px-4 bg-[#1F4E79] text-white text-center">
        <h2 className="text-2xl font-bold mb-2">Tudo pronto?</h2>
        <p className="text-blue-200 mb-6">O download é direto, sem cadastro.</p>
        <a href="https://github.com/marcelin1555/SIGBEF/releases" target="_blank" rel="noopener noreferrer"
          className="inline-block bg-yellow-400 text-[#1F4E79] font-bold px-10 py-4 rounded-xl text-lg hover:bg-yellow-300 transition-colors shadow-lg">
          Baixar SIGBEF grátis
        </a>
      </section>
    </>
  )
}
