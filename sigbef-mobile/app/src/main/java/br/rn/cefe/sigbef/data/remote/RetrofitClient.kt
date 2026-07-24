package br.rn.cefe.sigbef.data.remote

import br.rn.cefe.sigbef.BuildConfig
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import java.util.concurrent.TimeUnit

/**
 * Cria o cliente HTTP apontando para o SIGBEF da escola.
 *
 * **Não existe endereço padrão de propósito.** Cada escola tem o seu
 * computador na própria rede; o endereço vem do pareamento (QR code ou
 * digitado) e é obrigatório. Antes havia aqui um domínio inventado
 * (`sigbef-api.cefe.edu.br`) que não existe e nunca existiria: o servidor
 * é local e fala HTTP.
 */
object RetrofitClient {

    private var currentBaseUrl: String? = null
    private var apiService: SigbefApiService? = null

    /**
     * @param baseUrl endereço do servidor da escola, ex.: `http://192.168.0.10:8765/`
     */
    fun getApiService(tokenManager: TokenManager, baseUrl: String): SigbefApiService {
        require(baseUrl.isNotBlank()) {
            "Endereço da biblioteca não configurado: faça o pareamento antes."
        }
        val normalizada = normalizar(baseUrl)
        if (apiService == null || currentBaseUrl != normalizada) {
            currentBaseUrl = normalizada
            apiService = criar(tokenManager, normalizada)
        }
        return apiService!!
    }

    /** Aceita "192.168.0.10:8765", "sigbef://ip:porta" ou a URL completa. */
    fun normalizar(entrada: String): String {
        var url = entrada.trim()
        if (url.startsWith("sigbef://")) {
            url = "http://" + url.removePrefix("sigbef://")
        }
        if (!url.startsWith("http://") && !url.startsWith("https://")) {
            url = "http://$url"
        }
        if (!url.endsWith("/")) {
            url += "/"
        }
        return url
    }

    fun limpar() {
        apiService = null
        currentBaseUrl = null
    }

    private fun criar(tokenManager: TokenManager, baseUrl: String): SigbefApiService {
        val construtor = OkHttpClient.Builder()
            .addInterceptor(AuthInterceptor(tokenManager))
            .connectTimeout(10, TimeUnit.SECONDS)
            .readTimeout(15, TimeUnit.SECONDS)
            .writeTimeout(15, TimeUnit.SECONDS)

        // Log só em build de depuração, e nunca imprimindo o acesso do aluno.
        if (BuildConfig.DEBUG) {
            val log = HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BASIC
                redactHeader("Authorization")
            }
            construtor.addInterceptor(log)
        }

        val moshi = Moshi.Builder()
            .addLast(KotlinJsonAdapterFactory())
            .build()

        return Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(construtor.build())
            .addConverterFactory(MoshiConverterFactory.create(moshi))
            .build()
            .create(SigbefApiService::class.java)
    }
}
