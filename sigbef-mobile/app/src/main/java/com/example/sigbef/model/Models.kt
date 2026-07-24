package com.example.sigbef.model

data class Usuario(
    val id: Int = 1,
    val nome: String = "Maria Eduarda Silva",
    val matricula: String = "2026045892",
    val turma: String = "3ª série — Técnico em Informática",
    val escola: String = "Biblioteca do CEFE",
    val perfil: String = "ALUNO",
    val podePegar: Boolean = true,
    val limMaxLivros: Int = 3
)

data class Livro(
    val id: Int,
    val titulo: String,
    val autor: String,
    val categoria: String,
    val ano: String = "2021",
    val tombo: String = "4.821",
    val isbn: String = "978-85-359",
    val sinopse: String = "Bento Santiago, o narrador, conta a história de sua vida desde a infância, a promessa da mãe de fazê-lo padre, o amor por Capitu, o seminário, a amizade com Escobar, o casamento e o trágico desfecho alimentado pelo ciúme e a dúvida. Uma das maiores obras da literatura brasileira.",
    val disponivel: Boolean = true,
    val previsaoDevolucao: String? = null,
    val spineColorHex: String = "#1F4E79",
    val reservadoPeloUsuario: Boolean = false
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
    val renovacoesRestantes: Int = 2,
    val renovacaoPendente: Boolean = false
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
