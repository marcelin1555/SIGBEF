package br.rn.cefe.sigbef.data.remote

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class LoginRequest(
    @Json(name = "matricula") val matricula: String,
    @Json(name = "senha") val senha: String
)

@JsonClass(generateAdapter = true)
data class LoginResponse(
    @Json(name = "success") val success: Boolean,
    @Json(name = "token") val token: String?,
    @Json(name = "mensagem") val mensagem: String?,
    @Json(name = "usuario") val usuario: UsuarioDto?
)

@JsonClass(generateAdapter = true)
data class UsuarioDto(
    @Json(name = "id") val id: Int,
    @Json(name = "nome") val nome: String,
    @Json(name = "matricula") val matricula: String,
    @Json(name = "turma") val turma: String,
    @Json(name = "escola") val escola: String
)

@JsonClass(generateAdapter = true)
data class LivroDto(
    @Json(name = "id") val id: Int,
    @Json(name = "titulo") val titulo: String,
    @Json(name = "autor") val autor: String,
    @Json(name = "categoria") val categoria: String,
    @Json(name = "ano") val ano: String,
    @Json(name = "tombo") val tombo: String,
    @Json(name = "isbn") val isbn: String,
    @Json(name = "sinopse") val sinopse: String,
    @Json(name = "disponivel") val disponivel: Boolean,
    @Json(name = "previsaoDevolucao") val previsaoDevolucao: String? = null,
    @Json(name = "spineColorHex") val spineColorHex: String? = "#1F4E79",
    @Json(name = "reservadoPeloUsuario") val reservadoPeloUsuario: Boolean = false
)

@JsonClass(generateAdapter = true)
data class EmprestimoDto(
    @Json(name = "id") val id: Int,
    @Json(name = "livroTitulo") val livroTitulo: String,
    @Json(name = "autor") val autor: String,
    @Json(name = "dataDevolucao") val dataDevolucao: String,
    @Json(name = "atrasado") val atrasado: Boolean,
    @Json(name = "devolvido") val devolvido: Boolean = false,
    @Json(name = "dataDevolvido") val dataDevolvido: String? = null,
    @Json(name = "spineColorHex") val spineColorHex: String? = "#1F4E79",
    @Json(name = "renovacoesRestantes") val renovacoesRestantes: Int = 2,
    @Json(name = "renovacaoPendente") val renovacaoPendente: Boolean = false
)

@JsonClass(generateAdapter = true)
data class ApiResponse<T>(
    @Json(name = "success") val success: Boolean,
    @Json(name = "mensagem") val mensagem: String,
    @Json(name = "data") val data: T? = null
)
