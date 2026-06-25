const sim = '✅'
const nao = '❌'

const concorrentes = [
  { nome: 'SIGBEF',    gratuito: sim, offline: sim, kiosk: sim, instalador: sim, suporte: sim, opensource: sim },
  { nome: 'Pergamum', gratuito: nao, offline: nao, kiosk: nao, instalador: nao, suporte: sim, opensource: nao },
  { nome: 'Sophia',   gratuito: nao, offline: nao, kiosk: nao, instalador: nao, suporte: sim, opensource: nao },
  { nome: 'Biblivre', gratuito: sim, offline: nao, kiosk: nao, instalador: nao, suporte: nao, opensource: sim },
  { nome: 'Excel',    gratuito: sim, offline: sim, kiosk: nao, instalador: nao, suporte: nao, opensource: nao },
]

const colunas = [
  { key: 'gratuito', label: 'Gratuito' },
  { key: 'offline',  label: 'Offline' },
  { key: 'kiosk',    label: 'Kiosk' },
  { key: 'instalador', label: 'Instalador Windows' },
  { key: 'suporte',  label: 'Suporte em português' },
  { key: 'opensource', label: 'Código aberto' },
]

export default function Comparativo() {
  return (
    <section className="py-20 px-4 bg-gray-50">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-[#1F4E79] mb-3">Como o SIGBEF se compara</h2>
          <p className="text-gray-500 text-lg">A única solução grátis que funciona offline e tem código aberto.</p>
        </div>

        <div className="overflow-x-auto rounded-2xl border border-gray-200 shadow-sm">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[#1F4E79] text-white">
                <th className="text-left px-4 py-3 font-semibold">Sistema</th>
                {colunas.map(c => (
                  <th key={c.key} className="px-3 py-3 font-semibold text-center">{c.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {concorrentes.map((row, i) => (
                <tr key={row.nome} className={
                  row.nome === 'SIGBEF'
                    ? 'bg-blue-50 font-bold border-b-2 border-[#2E75B6]'
                    : i % 2 === 0 ? 'bg-white' : 'bg-gray-50'
                }>
                  <td className={`px-4 py-3 ${row.nome === 'SIGBEF' ? 'text-[#1F4E79]' : 'text-gray-700'}`}>
                    {row.nome}
                    {row.nome === 'SIGBEF' && (
                      <span className="ml-2 text-xs bg-[#2E75B6] text-white px-2 py-0.5 rounded-full font-normal">você</span>
                    )}
                  </td>
                  {colunas.map(c => (
                    <td key={c.key} className="px-3 py-3 text-center text-base">{row[c.key]}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  )
}
