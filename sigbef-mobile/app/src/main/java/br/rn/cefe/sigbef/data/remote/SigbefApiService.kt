package br.rn.cefe.sigbef.data.remote

import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

/**
 * Rotas da API do SIGBEF desktop.
 *
 * Todas conferidas contra sigbef/api.py — não há nenhuma rota inventada
 * aqui. Fora o login, a API é **somente leitura**: qualquer POST em outro
 * caminho recebe 405 do servidor, então reservar/renovar não existem.
 */
interface SigbefApiService {

    /** Testa se a biblioteca está acessível. Não exige token. */
    @GET("api/v1/ping")
    suspend fun ping(): Response<PingResponse>

    /** Único POST da API: troca matrícula e senha por um acesso do aluno. */
    @POST("api/v1/login")
    suspend fun login(@Body request: LoginRequest): Response<LoginResponse>

    /**
     * Busca no acervo.
     * @param q termo livre (título, autor, ISBN); vazio lista tudo
     * @param disponiveis "1" para trazer só o que tem exemplar livre
     */
    @GET("api/v1/livros")
    suspend fun buscarLivros(
        @Query("q") q: String = "",
        @Query("disponiveis") disponiveis: String = "0"
    ): Response<ListaLivrosResponse>

    /** Ficha do livro, com sinopse e os exemplares (onde mora o tombo). */
    @GET("api/v1/livros/{id}")
    suspend fun detalheLivro(@Path("id") id: Int): Response<LivroDetalheDto>

    /**
     * Situação do leitor: dados da carteirinha, empréstimos em aberto e
     * reservas. O servidor só devolve se a matrícula for a do dono do
     * acesso — pedir a de outro aluno resulta em 403.
     */
    @GET("api/v1/usuarios/{matricula}/emprestimos")
    suspend fun situacaoLeitor(
        @Path("matricula") matricula: String
    ): Response<SituacaoLeitorResponse>
}
