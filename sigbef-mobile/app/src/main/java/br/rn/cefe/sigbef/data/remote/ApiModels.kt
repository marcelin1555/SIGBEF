package br.rn.cefe.sigbef.data.remote

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

/**
 * DTOs espelhando exatamente o JSON da API do SIGBEF desktop
 * (ver docs/API.md e sigbef/api.py).
 *
 * Os nomes em snake_case seguem o servidor porque foram conferidos
 * contra a resposta real, não deduzidos.
 */

// ---------------------------------------------------------------- login
@JsonClass(generateAdapter = true)
data class LoginRequest(
    val matricula: String,
    val senha: String
)

@JsonClass(generateAdapter = true)
data class LoginResponse(
    val token: String,
    val usuario: UsuarioLoginDto
)

@JsonClass(generateAdapter = true)
data class UsuarioLoginDto(
    val nome: String,
    val matricula: String,
    val perfil: String
)

// ---------------------------------------------------------------- acervo
/** Envelope de GET /api/v1/livros — a lista vem dentro de "livros". */
@JsonClass(generateAdapter = true)
data class ListaLivrosResponse(
    val total: Int = 0,
    val livros: List<LivroResumoDto> = emptyList()
)

/**
 * Livro na LISTAGEM. Atenção: aqui `autores` é uma String única
 * ("George Orwell"); no detalhe é uma lista. O servidor devolve assim.
 */
@JsonClass(generateAdapter = true)
data class LivroResumoDto(
    val id: Int,
    val titulo: String,
    val isbn: String? = null,
    @Json(name = "ano_publicacao") val anoPublicacao: Int? = null,
    val edicao: String? = null,
    val categoria: String? = null,
    val editora: String? = null,
    val autores: String? = null,
    @Json(name = "total_exemplares") val totalExemplares: Int = 0,
    val disponiveis: Int = 0
)

/** Livro no DETALHE — aqui `autores` é lista e vêm os exemplares. */
@JsonClass(generateAdapter = true)
data class LivroDetalheDto(
    val id: Int,
    val titulo: String,
    val isbn: String? = null,
    @Json(name = "ano_publicacao") val anoPublicacao: Int? = null,
    val edicao: String? = null,
    val sinopse: String? = null,
    val editora: String? = null,
    val categoria: String? = null,
    val autores: List<String> = emptyList(),
    val exemplares: List<ExemplarDto> = emptyList()
)

/** O número de tombo mora aqui, não no livro. */
@JsonClass(generateAdapter = true)
data class ExemplarDto(
    @Json(name = "numero_tombo") val numeroTombo: String,
    @Json(name = "codigo_barras") val codigoBarras: String? = null,
    val localizacao: String? = null,
    val status: String
)

// ----------------------------------------------------- situação do leitor
/**
 * GET /api/v1/usuarios/{matricula}/emprestimos devolve a situação
 * completa do leitor, não só a lista de empréstimos.
 */
@JsonClass(generateAdapter = true)
data class SituacaoLeitorResponse(
    val nome: String,
    val matricula: String,
    val turma: String? = null,
    val perfil: String,
    val ativo: Boolean = true,
    @Json(name = "pode_pegar") val podePegar: Boolean = true,
    val situacao: String? = null,
    @Json(name = "limite_emprestimos") val limiteEmprestimos: Int = 0,
    @Json(name = "multas_em_aberto") val multasEmAberto: Double = 0.0,
    @Json(name = "emprestimos_abertos") val emprestimosAbertos: List<EmprestimoDto> = emptyList(),
    @Json(name = "reservas_ativas") val reservasAtivas: List<ReservaDto> = emptyList()
)

@JsonClass(generateAdapter = true)
data class EmprestimoDto(
    val id: Int,
    val titulo: String,
    @Json(name = "codigo_barras") val codigoBarras: String? = null,
    @Json(name = "data_emprestimo") val dataEmprestimo: String? = null,
    @Json(name = "data_prevista") val dataPrevista: String? = null,
    @Json(name = "data_devolucao") val dataDevolucao: String? = null,
    val multa: Double = 0.0,
    val origem: String? = null
)

@JsonClass(generateAdapter = true)
data class ReservaDto(
    val titulo: String,
    val posicao: Int = 0,
    val separado: Boolean = false,
    @Json(name = "retirar_ate") val retirarAte: String? = null
)

// ------------------------------------------------------------------ ping
@JsonClass(generateAdapter = true)
data class PingResponse(
    val ok: Boolean = false,
    val servico: String? = null,
    val versao: String? = null
)
