package br.rn.cefe.sigbef.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

/**
 * Banco local do aplicativo.
 *
 * É apenas um **cache** do que veio da biblioteca: acervo consultado,
 * empréstimos do aluno e os dados da carteirinha. Nada nasce aqui.
 *
 * Antes este arquivo trazia um acervo inventado (6 livros com tombos
 * falsos), uma aluna fictícia e empréstimos de mentira, que o app exibia
 * como se fossem reais mesmo sem nunca ter falado com a biblioteca. Isso
 * foi removido: sem conexão e sem login, as telas ficam legitimamente
 * vazias.
 *
 * A versão do schema subiu para 2 e a migração é destrutiva de propósito:
 * aparelhos que rodaram a versão anterior precisam perder os dados falsos.
 */
@Database(
    entities = [UsuarioEntity::class, LivroEntity::class, EmprestimoEntity::class,
                ReservaEntity::class],
    version = 5,
    exportSchema = false
)
abstract class SigbefDatabase : RoomDatabase() {
    abstract fun usuarioDao(): UsuarioDao
    abstract fun livroDao(): LivroDao
    abstract fun emprestimoDao(): EmprestimoDao
    abstract fun reservaDao(): ReservaDao

    companion object {
        @Volatile
        private var INSTANCE: SigbefDatabase? = null

        fun getDatabase(context: Context): SigbefDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    SigbefDatabase::class.java,
                    "sigbef_database"
                )
                    // Descarta o banco antigo (que continha os dados de
                    // demonstração) em vez de tentar migrá-lo.
                    .fallbackToDestructiveMigration(dropAllTables = true)
                    .build()
                INSTANCE = instance
                instance
            }
        }
    }
}
