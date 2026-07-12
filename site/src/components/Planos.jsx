const planos = [
  {
    nome: 'Gratuito', preco: 'R$ 0', periodo: 'para sempre', destaque: false,
    descricao: 'Para qualquer escola pública que queira começar agora.',
    itens: ['Sistema completo de biblioteca','Empréstimos, devoluções e multas','Kiosk de autoatendimento','Relatórios em CSV','Código aberto MIT','Sem limite de livros ou usuários'],
    cta: 'Baixar grátis', href: 'https://github.com/marcelin1555/SIGBEF/releases',
  },
  {
    nome: 'Implantação Assistida', preco: 'R$ 800–1.500', periodo: 'pagamento único', destaque: true,
    descricao: 'Para escolas que querem ajuda para configurar e treinar a equipe.',
    itens: ['Tudo do plano gratuito','Instalação presencial ou remota','Cadastro inicial do acervo','Treinamento da equipe (4h)','Suporte por 30 dias'],
    cta: 'Fale conosco', href: 'https://wa.me/5584991424110',
  },
  {
    nome: 'Suporte Mensal', preco: 'R$ 99', periodo: 'por mês', destaque: false,
    descricao: 'Para escolas que querem suporte contínuo e atualizações.',
    itens: ['Tudo do plano gratuito','Suporte por WhatsApp e e-mail','Atualizações de versão','Backup configurado'],
    cta: 'Fale conosco', href: 'https://wa.me/5584991424110',
  },
]

export default function Planos() {
  return (
    <section id="planos" className="py-20 px-4 bg-white">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-[#1F4E79] mb-3">Planos</h2>
          <p className="text-gray-500 text-lg">Modelo Open Core: o sistema é gratuito. Os serviços são opcionais.</p>
        </div>

        <div className="grid md:grid-cols-3 gap-6 items-start">
          {planos.map((p) => (
            <div key={p.nome} className={`rounded-2xl border p-6 flex flex-col h-full ${p.destaque ? 'border-[#2E75B6] bg-[#1F4E79] text-white shadow-xl scale-105' : 'border-gray-200 bg-gray-50'}`}>
              {p.destaque && (
                <span className="self-start text-xs bg-yellow-400 text-[#1F4E79] font-bold px-3 py-1 rounded-full mb-3">Mais popular</span>
              )}
              <h3 className={`font-bold text-xl mb-1 ${p.destaque ? 'text-white' : 'text-gray-800'}`}>{p.nome}</h3>
              <div className="mb-3">
                <span className={`text-3xl font-bold ${p.destaque ? 'text-yellow-300' : 'text-[#2E75B6]'}`}>{p.preco}</span>
                <span className={`text-sm ml-1 ${p.destaque ? 'text-blue-200' : 'text-gray-400'}`}>{p.periodo}</span>
              </div>
              <p className={`text-sm mb-5 ${p.destaque ? 'text-blue-100' : 'text-gray-500'}`}>{p.descricao}</p>
              <ul className="space-y-2 mb-6 flex-1">
                {p.itens.map((item) => (
                  <li key={item} className={`flex items-start gap-2 text-sm ${p.destaque ? 'text-blue-100' : 'text-gray-600'}`}>
                    <span className="text-green-400 font-bold mt-0.5">✓</span>{item}
                  </li>
                ))}
              </ul>
              <a href={p.href} target="_blank" rel="noopener noreferrer"
                className={`block text-center font-bold py-3 rounded-xl transition-colors ${p.destaque ? 'bg-yellow-400 text-[#1F4E79] hover:bg-yellow-300' : 'bg-[#2E75B6] text-white hover:bg-[#1F4E79]'}`}>
                {p.cta}
              </a>
            </div>
          ))}
        </div>

        <p className="text-center mt-8 text-gray-400 text-sm">
          Redes municipais e secretarias de educação:{' '}
          <a href="https://wa.me/5584991424110" target="_blank" rel="noopener noreferrer"
            className="text-[#2E75B6] font-semibold underline underline-offset-2 hover:text-[#1F4E79] transition-colors">
            entre em contato
          </a>{' '}
          para o plano B2G a partir de R$ 8.000/ano.
        </p>
      </div>
    </section>
  )
}
