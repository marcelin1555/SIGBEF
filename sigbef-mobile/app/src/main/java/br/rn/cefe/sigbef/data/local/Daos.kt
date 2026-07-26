package br.rn.cefe.sigbef.data.local

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import kotlinx.coroutines.flow.Flow

@Dao
interface UsuarioDao {
    @Query("SELECT * FROM usuarios WHERE id = 1 LIMIT 1")
    fun getUsuario(): Flow<UsuarioEntity?>

    @Query("SELECT * FROM usuarios WHERE id = 1 LIMIT 1")
    suspend fun getUsuarioOnce(): UsuarioEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertUsuario(usuario: UsuarioEntity)

    @Query("DELETE FROM usuarios")
    suspend fun clearAll()
}

@Dao
interface LivroDao {
    @Query("SELECT * FROM livros ORDER BY id ASC")
    fun getAllLivros(): Flow<List<LivroEntity>>

    @Query("SELECT * FROM livros WHERE id = :id LIMIT 1")
    fun getLivroById(id: Int): Flow<LivroEntity?>

    /** Leitura pontual, para completar a ficha depois de consultar a API. */
    @Query("SELECT * FROM livros WHERE id = :id LIMIT 1")
    suspend fun getLivroByIdOnce(id: Int): LivroEntity?

    /** Usado ao ressincronizar, para preservar sinopse e tombo já baixados. */
    @Query("SELECT * FROM livros")
    suspend fun listarTodosUmaVez(): List<LivroEntity>

    @Query("""
        SELECT * FROM livros 
        WHERE (:category = 'Todos' OR categoria LIKE '%' || :category || '%')
        AND (titulo LIKE '%' || :query || '%' OR autor LIKE '%' || :query || '%' OR isbn LIKE '%' || :query || '%' OR tombo LIKE '%' || :query || '%')
        ORDER BY titulo ASC
    """)
    fun searchLivros(query: String, category: String): Flow<List<LivroEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertLivros(livros: List<LivroEntity>)

    @Update
    suspend fun updateLivro(livro: LivroEntity)

    @Query("DELETE FROM livros")
    suspend fun clearAll()
}

@Dao
interface EmprestimoDao {
    @Query("SELECT * FROM emprestimos ORDER BY devolvido ASC, id DESC")
    fun getAllEmprestimos(): Flow<List<EmprestimoEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertEmprestimos(emprestimos: List<EmprestimoEntity>)

    @Query("DELETE FROM emprestimos")
    suspend fun clearAll()
}

@Dao
interface ReservaDao {
    /** Fila do aluno: quem já tem exemplar separado aparece primeiro. */
    @Query("SELECT * FROM reservas ORDER BY separado DESC, posicao ASC")
    fun getAllReservas(): Flow<List<ReservaEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertReservas(reservas: List<ReservaEntity>)

    @Query("DELETE FROM reservas")
    suspend fun clearAll()
}
