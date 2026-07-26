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

    private val moshiErro by lazy {
        Moshi.Builder().addLast(KotlinJsonAdapterFactory()).build()
            .adapter(ErroResponse::class.java)
    }

    /**
     * Extrai a mensagem de dentro de um corpo de erro da API.
     *
     * Existe porque as recusas por regra de negócio (409) trazem a frase
     * já escrita para o aluno — vale mais mostrá-la do que inventar um
     * texto genérico no app.
     */
    fun lerErro(corpo: String): String =
        runCatching { moshiErro.fromJson(corpo)?.erro }.getOrNull().orEmpty()

    /**
     * Confere se o endereço é de rede local, antes de aceitar o pareamento.
     *
     * Como o app manda matrícula e senha em HTTP (texto puro), ele não pode
     * conectar em qualquer host da internet: aceita só IP privado
     * (10.x, 192.168.x, 172.16–31.x), loopback, ou nomes .local/.lan.
     * Isso é validado sem resolução DNS — só analisando o texto do host.
     */
    fun eEnderecoLocal(url: String): Boolean {
        val host = try {
            java.net.URI(normalizar(url)).host ?: return false
        } catch (e: Exception) {
            return false
        }

        // Octetos de IPv4 → checa faixas privadas
        val octetos = host.split(".")
        if (octetos.size == 4 && octetos.all { it.toIntOrNull() in 0..255 }) {
            val a = octetos[0].toInt()
            val b = octetos[1].toInt()
            return a == 10 ||
                (a == 192 && b == 168) ||
                (a == 172 && b in 16..31) ||
                a == 127
        }

        // Nome de host: só os sufixos de rede local
        val h = host.lowercase()
        return h == "localhost" || h.endsWith(".local") || h.endsWith(".lan")
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
