// Peças visuais que se repetem em várias páginas.

// Faixa azul do topo das páginas internas (Funcionalidades, Planos, Equipe...).
export function CabecalhoPagina({ rotulo, titulo, children, extra }) {
  return (
    <div className="bg-gradient-to-br from-dark to-primary text-white py-14 px-4">
      <div className="max-w-4xl mx-auto text-center">
        <p className="text-blue-200 text-sm font-semibold uppercase tracking-widest mb-3">{rotulo}</p>
        <h1 className="text-4xl sm:text-5xl font-bold mb-4">{titulo}</h1>
        <p className={`text-blue-100 text-lg max-w-2xl mx-auto${extra ? ' mb-8' : ''}`}>{children}</p>
        {extra}
      </div>
    </div>
  )
}

// Título centralizado com subtítulo, usado no início das seções.
export function TituloSecao({ titulo, children }) {
  return (
    <div className="text-center mb-12">
      <h2 className="text-3xl sm:text-4xl font-bold text-dark mb-3">{titulo}</h2>
      {children && <p className="text-gray-500 text-lg">{children}</p>}
    </div>
  )
}
