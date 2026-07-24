package br.rn.cefe.sigbef.data.remote

import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import java.util.concurrent.TimeUnit

object RetrofitClient {

    private const val DEFAULT_BASE_URL = "https://sigbef-api.cefe.edu.br/"

    private var currentBaseUrl = DEFAULT_BASE_URL
    private var apiService: SigbefApiService? = null

    fun getApiService(tokenManager: TokenManager, baseUrl: String = DEFAULT_BASE_URL): SigbefApiService {
        if (apiService == null || currentBaseUrl != baseUrl) {
            currentBaseUrl = baseUrl
            apiService = createApiService(tokenManager, baseUrl)
        }
        return apiService!!
    }

    private fun createApiService(tokenManager: TokenManager, baseUrl: String): SigbefApiService {
        // Logging Interceptor for debugging HTTP requests/responses
        val loggingInterceptor = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }

        // Custom Auth Interceptor injecting Bearer JWT Token
        val authInterceptor = AuthInterceptor(tokenManager)

        // Configure OkHttpClient
        val okHttpClient = OkHttpClient.Builder()
            .addInterceptor(authInterceptor)
            .addInterceptor(loggingInterceptor)
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(15, TimeUnit.SECONDS)
            .writeTimeout(15, TimeUnit.SECONDS)
            .build()

        // Configure Moshi JSON Parser
        val moshi = Moshi.Builder()
            .addLast(KotlinJsonAdapterFactory())
            .build()

        // Build Retrofit Instance
        val retrofit = Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(okHttpClient)
            .addConverterFactory(MoshiConverterFactory.create(moshi))
            .build()

        return retrofit.create(SigbefApiService::class.java)
    }
}
