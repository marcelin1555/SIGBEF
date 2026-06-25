import Planos from '../components/Planos'

const faq = [
  {
    q: 'O plano gratuito é realmente completo?',
    r: 'Sim. O sistema inteiro, com todas as funcionalidades (empréstimos, kiosk, relatórios, multi-perfil), está disponível gratuitamente para sempre sob licença MIT. Não é demo, não tem limite de tempo.',
  },
  {
    q: 'Por que existe um plano pago se o sistema é gratuito?',
    r: 'Esse é o modelo Open Core: o software é livre, mas instalação, treinamento e suporte contínuo são serviços que demandam tempo da equipe. Escolas com TI própria usam de graça. Escolas que precisam de ajuda contratam o serviço.',
  },
  {
    q: 'O que inclui a implantação assistida?',
    r: 'A equipe do SIGBEF instala o sistema, importa o acervo existente (se houver), configura os usuários e faz um treinamento de 4 horas com a bibliotecária e os alunos. O suporte pós-instalação dura 30 dias.',
  },
  {
    q: 'Tem desconto para redes municipais?',
    r: 'Sim. Redes com múltiplas escolas têm condições especiais no plano B2G, a partir de R$ 8.000 por ano com suporte dedicado. Entre em contato pelo GitHub Issues para montar uma proposta.',
  },
  {
    q: 'Posso migrar do plano gratuito para o suporte mensal depois?',
    r: 'Sim, em qualquer momento. Os dados são preservados e não há custo de migração.',
  },
]

export default function PlanosPage() {
  return (
    <>
      {/* page header */}
      <div className="bg-gradient-to-br from-[#1F4E79] to-[#2E75B6] text-white py-14 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-blue-200 text-sm font-semibold uppercase tracking-widest mb-3">Preços</p>
          <h1 className="text-4xl sm:text-5xl font-bold mb-4">Planos</h1>
          <p className="text-blue-100 text-lg max-w-2xl mx-auto">
            O sistema é gratuito para sempre. Os serviços são opcionais.
          </p>
        </div>
      </div>

      <Planos />

      {/* faq */}
      <section className="py-16 px-4 bg-gray-50">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-[#1F4E79] mb-8 text-center">Dúvidas sobre os planos</h2>
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

      {/* contact cta */}
      <section className="py-14 px-4 bg-white text-center">
        <h2 className="text-2xl font-bold text-[#1F4E79] mb-2">Ficou alguma dúvida?</h2>
        <p className="text-gray-500 mb-6">Abra uma issue no GitHub ou entre em contato direto.</p>
        <a href="https://github.com/marcelin1555/SIGBEF/issues" target="_blank" rel="noopener noreferrer"
          className="inline-block border-2 border-[#2E75B6] text-[#2E75B6] font-bold px-8 py-3.5 rounded-xl hover:bg-blue-50 transition-colors">
          Falar com a equipe
        </a>
      </section>
    </>
  )
}
