package br.rn.cefe.sigbef.data.remote

import android.content.Context
import android.content.SharedPreferences

/**
 * Guarda no aparelho o que o app precisa lembrar entre aberturas:
 * o endereço da biblioteca (definido no pareamento) e o acesso do aluno.
 *
 * O acesso é pessoal e expira sozinho no servidor. `allowBackup` está
 * desligado no manifesto para que isso não vá parar numa cópia na nuvem.
 */
class TokenManager(context: Context) {

    private val prefs: SharedPreferences =
        context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE)

    companion object {
        private const val PREF_NAME = "sigbef_auth_prefs"
        private const val KEY_TOKEN = "auth_token"
        private const val KEY_MATRICULA = "user_matricula"
        private const val KEY_SERVIDOR = "endereco_servidor"

        @Volatile
        private var INSTANCE: TokenManager? = null

        fun getInstance(context: Context): TokenManager {
            return INSTANCE ?: synchronized(this) {
                val instance = TokenManager(context.applicationContext)
                INSTANCE = instance
                instance
            }
        }
    }

    // ----------------------------------------------------- servidor
    /** Endereço do SIGBEF da escola, obtido no pareamento. */
    fun salvarServidor(endereco: String) {
        prefs.edit().putString(KEY_SERVIDOR, endereco).apply()
    }

    fun obterServidor(): String? = prefs.getString(KEY_SERVIDOR, null)

    fun temServidor(): Boolean = !obterServidor().isNullOrBlank()

    // -------------------------------------------------------- acesso
    fun salvarAcesso(token: String, matricula: String) {
        prefs.edit()
            .putString(KEY_TOKEN, token)
            .putString(KEY_MATRICULA, matricula)
            .apply()
    }

    fun obterToken(): String? = prefs.getString(KEY_TOKEN, null)

    fun obterMatricula(): String? = prefs.getString(KEY_MATRICULA, null)

    fun estaLogado(): Boolean = !obterToken().isNullOrBlank()

    /** Sai da conta mas mantém o pareamento com a biblioteca. */
    fun sair() {
        prefs.edit()
            .remove(KEY_TOKEN)
            .remove(KEY_MATRICULA)
            .apply()
    }

    /** Esquece tudo, inclusive a escola. */
    fun limparTudo() {
        prefs.edit().clear().apply()
    }
}
