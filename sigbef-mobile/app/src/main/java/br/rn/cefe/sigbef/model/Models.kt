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
    RESERVE
}
