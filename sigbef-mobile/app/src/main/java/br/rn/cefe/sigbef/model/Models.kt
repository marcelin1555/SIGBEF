package br.rn.cefe.sigbef.model

// Modelos de domínio.
//
// Nenhum campo tem valor padrão "de exemplo": um dado que falte tem de
// aparecer vazio, nunca preenchido com informação inventada. Antes havia
// aqui o nome de uma aluna fictícia e a ficha do Dom Casmurro como
// padrão, o que faria o app exibir dado falso como se fosse real.

data class Usuario(
    val id: Int = 0,
    val nome: String = "",
    val matricula: String = "",
    val turma: String = "",
    val escola: String = "",
    val perfil: String = "",
    val podePegar: Boolean = true,
    /** Explicação da biblioteca quando o aluno está impedido. */
    val situacao: String = "",
    // Limite de empréstimos simultâneos do perfil, vindo da biblioteca.
    // 0 = ainda não sabido; a Home só desenha a barra quando > 0.
    val limMaxLivros: Int = 0
) {
    /** Ainda não há ninguém logado neste aparelho. */
    val vazio: Boolean get() = matricula.isBlank()
}

data class Livro(
    val id: Int,
    val titulo: String,
    val autor: String,
    val categoria: String,
    val ano: String = "",
    val tombo: String = "",
    val isbn: String = "",
    val sinopse: String = "",
    val disponivel: Boolean = true,
    val previsaoDevolucao: String? = null,
    // Cor da lombada: derivada localmente do título, só para a lista não
    // ficar monótona. Não vem da biblioteca.
    val spineColorHex: String = "#1F4E79"
)

data class Emprestimo(
    val id: Int,
    val livroTitulo: String,
    val autor: String,
    val dataDevolucao: String,
    val atrasado: Boolean,
    val devolvido: Boolean = false,
    val dataDevolvido: String? = null,
    val spineColorHex: String = "#1F4E79",
    val renovacoes: Int = 0,
    /** A biblioteca já disse se este livro pode ser renovado. */
    val podeRenovar: Boolean = false,
    /** Quando não pode, a frase que explica o porquê ao aluno. */
    val motivoRenovacao: String = ""
)

data class Reserva(
    val id: Int,
    val livroId: Int,
    val titulo: String,
    val posicao: Int = 0,
    val separado: Boolean = false,
    val retirarAte: String? = null,
    val spineColorHex: String = "#1F4E79"
)

/** O que o aluno leu. Vem da biblioteca, calculado sobre devoluções. */
data class EstatisticaLeitura(
    val totalLidos: Int = 0,
    val lidosNoAno: Int = 0,
    val diasMedios: Double = 0.0,
    val leitorDesde: String = "",
    val categoriaFavorita: String = "",
    val lidosNaFavorita: Int = 0
) {
    /** Nunca devolveu nada — a tela mostra convite, não números zerados. */
    val vazia: Boolean get() = totalLidos == 0
}

data class Recomendacao(
    val livroId: Int,
    val titulo: String,
    val categoria: String = "",
    /** "Quem leu X também leu", "Ninguém pegou ainda…" */
    val motivo: String = "",
    val spineColorHex: String = "#1F4E79"
)

enum class Screen {
    CONNECT,
    LOGIN,
    HOME,
    ACERVO,
    BOOK_DETAIL,
    LOANS,
    RENEW_INFO,
    CARD,
    RESERVE,
    READING
}
