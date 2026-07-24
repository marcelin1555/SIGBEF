package br.rn.cefe.sigbef.data.remote

import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface SigbefApiService {

    @POST("api/v1/auth/login")
    suspend fun login(@Body request: LoginRequest): Response<LoginResponse>

    @GET("api/v1/aluno/perfil")
    suspend fun getPerfil(): Response<UsuarioDto>

    @GET("api/v1/acervo/livros")
    suspend fun getLivros(
        @Query("busca") query: String? = null,
        @Query("categoria") categoria: String? = null
    ): Response<List<LivroDto>>

    @GET("api/v1/acervo/livros/{id}")
    suspend fun getLivroDetail(@Path("id") id: Int): Response<LivroDto>

    @POST("api/v1/acervo/livros/{id}/reservar")
    suspend fun reservarLivro(@Path("id") id: Int): Response<ApiResponse<Boolean>>

    @POST("api/v1/acervo/livros/{id}/cancelar-reserva")
    suspend fun cancelarReserva(@Path("id") id: Int): Response<ApiResponse<Boolean>>

    @GET("api/v1/emprestimos")
    suspend fun getEmprestimos(): Response<List<EmprestimoDto>>

    @POST("api/v1/emprestimos/{id}/renovar")
    suspend fun solicitarRenovacao(@Path("id") id: Int): Response<ApiResponse<Boolean>>
}
