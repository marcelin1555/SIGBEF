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
 * aqui. A API grava em exatamente três lugares (reservar, cancelar a
 * própria reserva e renovar o próprio empréstimo); o acervo em si só é
 * lido, e qualquer outro POST recebe 405 do servidor.
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
        @Query("disponiveis") disponiveis: String = "0",
        @Query("pagina") pagina: Int = 1,
        @Query("limite") limite: Int = 200
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

    /**
     * Retrato da leitura do aluno e sugestões de próximos livros.
     *
     * Rota separada da de empréstimos porque a recomendação é cara e não
     * precisa ser recalculada a cada reserva ou renovação.
     */
    @GET("api/v1/usuarios/{matricula}/leitura")
    suspend fun leitura(
        @Path("matricula") matricula: String,
        @Query("limite") limite: Int = 6
    ): Response<LeituraResponse>

    /**
     * Entra na fila de espera de um livro sem exemplar livre.
     * 409 quando a regra da biblioteca recusa (livro disponível, limite
     * de reservas atingido, reserva repetida) — a mensagem vem pronta.
     */
    @POST("api/v1/reservas")
    suspend fun reservar(@Body request: ReservaRequest): Response<ReservaCriadaResponse>

    /** Desiste da fila. O servidor recusa reserva que seja de outro aluno. */
    @POST("api/v1/reservas/{id}/cancelar")
    suspend fun cancelarReserva(@Path("id") id: Int): Response<Unit>

    /**
     * Estende o prazo do próprio empréstimo.
     * 409 quando venceu, quando alguém está na fila ou quando o limite de
     * renovações acabou; 403 se o empréstimo for de outro leitor.
     */
    @POST("api/v1/emprestimos/{id}/renovar")
    suspend fun renovar(@Path("id") id: Int): Response<RenovacaoResponse>
}
