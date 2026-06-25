const passos = [
  { numero: '1', titulo: 'Baixar', texto: 'Acesse o GitHub e baixe o instalador SIGBEF_Setup_v1.2.0.exe. É gratuito, sem cadastro.' },
  { numero: '2', titulo: 'Instalar', texto: 'Execute o instalador. Próximo, próximo, concluir. Pronto em menos de 5 minutos.' },
  { numero: '3', titulo: 'Usar', texto: 'Abra o SIGBEF. Sem internet, sem servidor, sem mensalidade. Funciona em qualquer PC com Windows.' },
]

export default function ComoInstalar() {
  return (
    <section id="como-instalar" className="py-20 px-4 bg-white">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-[#1F4E79] mb-3">Como instalar</h2>
          <p className="text-gray-500 text-lg">Três passos. Nenhuma configuração de servidor.</p>
        </div>

        <div className="grid sm:grid-cols-3 gap-8">
          {passos.map((p) => (
            <div key={p.numero} className="text-center">
              <div className="w-14 h-14 rounded-full bg-[#2E75B6] text-white text-2xl font-bold flex items-center justify-center mx-auto mb-4">
                {p.numero}
              </div>
              <h3 className="font-bold text-gray-800 text-lg mb-2">{p.titulo}</h3>
              <p className="text-gray-500 text-sm leading-relaxed">{p.texto}</p>
            </div>
          ))}
        </div>

        <div className="mt-12 text-center">
          <a href="https://github.com/marcelin1555/SIGBEF/releases" target="_blank" rel="noopener noreferrer"
            className="inline-block bg-[#2E75B6] text-white font-bold px-10 py-4 rounded-xl text-lg hover:bg-[#1F4E79] transition-colors shadow-md">
            Baixar SIGBEF grátis
          </a>
          <p className="mt-3 text-gray-400 text-sm">Licença MIT · Código aberto · Sem limite de usuários</p>
        </div>
      </div>
    </section>
  )
}
