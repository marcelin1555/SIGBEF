import { TituloSecao } from './ui'

// Mesmos dados do pitch e do relatório: preço público quando existe, "sob consulta" quando não.
const colunas = [
  { key: 'custo', label: 'Custo' },
  { key: 'infra', label: 'O que precisa para rodar' },
  { key: 'codigo', label: 'Código aberto' },
  { key: 'autoatendimento', label: 'Autoatendimento do aluno' },
]

const sistemas = [
  { nome: 'SIGBEF', custo: 'R$ 0', infra: 'O computador da biblioteca, sem internet', codigo: 'Sim (MIT)', autoatendimento: 'Sim' },
  { nome: 'Pergamum', custo: 'Pago, sob consulta', infra: 'Servidor ou nuvem', codigo: 'Não', autoatendimento: '—' },
  { nome: 'Sophia', custo: 'Pago, sob consulta', infra: 'Servidor ou nuvem', codigo: 'Não', autoatendimento: '—' },
  { nome: 'Biblivre', custo: 'R$ 0', infra: 'Servidor com Java, Tomcat e PostgreSQL', codigo: 'Sim (GPL)', autoatendimento: '—' },
  { nome: 'Planilha', custo: 'R$ 0', infra: 'O computador da biblioteca', codigo: 'Não se aplica', autoatendimento: 'Não' },
]

export default function Comparativo() {
  return (
    <section className="py-20 px-4 bg-gray-50">
      <div className="max-w-5xl mx-auto">
        <TituloSecao titulo="Como o SIGBEF se compara">Gratuito, sem servidor e com código aberto ao mesmo tempo.</TituloSecao>

        <div className="overflow-x-auto rounded-2xl border border-gray-200 shadow-sm bg-white">
          <table className="w-full min-w-[680px] text-sm">
            <thead>
              <tr className="bg-dark text-white">
                <th scope="col" className="text-left px-4 py-3 font-semibold">Sistema</th>
                {colunas.map(c => (
                  <th key={c.key} scope="col" className="text-left px-4 py-3 font-semibold">{c.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sistemas.map((s, i) => {
                const nosso = s.nome === 'SIGBEF'
                return (
                  <tr key={s.nome} className={nosso ? 'bg-blue-50 border-b-2 border-primary' : i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <th scope="row" className={`text-left px-4 py-3 ${nosso ? 'text-dark font-bold' : 'text-gray-700 font-semibold'}`}>{s.nome}</th>
                    {colunas.map(c => (
                      <td key={c.key} className={`px-4 py-3 ${nosso ? 'text-dark font-semibold' : 'text-gray-600'}`}>{s[c.key]}</td>
                    ))}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        <p className="text-gray-400 text-xs mt-3">
          "—" quando não encontramos informação pública. Preço do Pergamum: contrato da UFSB, 2017 (R$ 27.200).
        </p>
      </div>
    </section>
  )
}
