package com.example.sigbef.data.remote

import android.content.Context
import android.content.SharedPreferences

class TokenManager(context: Context) {
    private val prefs: SharedPreferences = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE)

    companion object {
        private const val PREF_NAME = "sigbef_auth_prefs"
        private const val KEY_AUTH_TOKEN = "auth_token"
        private const val KEY_USER_MATRICULA = "user_matricula"

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

    fun saveAuthToken(token: String) {
        prefs.edit().putString(KEY_AUTH_TOKEN, token).apply()
    }

    fun getAuthToken(): String? {
        return prefs.getString(KEY_AUTH_TOKEN, null)
    }

    fun saveMatricula(matricula: String) {
        prefs.edit().putString(KEY_USER_MATRICULA, matricula).apply()
    }

    fun getMatricula(): String? {
        return prefs.getString(KEY_USER_MATRICULA, null)
    }

    fun clear() {
        prefs.edit().clear().apply()
    }

    fun hasValidToken(): Boolean {
        return !getAuthToken().isNull_or_blank()
    }
}

private fun String?.isNull_or_blank(): Boolean = this == null || this.trim().isEmpty()
