package br.rn.cefe.sigbef.data.remote

import okhttp3.Interceptor
import okhttp3.Response

/** Anexa o acesso do aluno em toda chamada que já o tenha. */
class AuthInterceptor(private val tokenManager: TokenManager) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val construtor = chain.request().newBuilder()
            .header("Accept", "application/json")

        val token = tokenManager.obterToken()
        if (!token.isNullOrBlank()) {
            construtor.header("Authorization", "Bearer $token")
        }
        return chain.proceed(construtor.build())
    }
}
