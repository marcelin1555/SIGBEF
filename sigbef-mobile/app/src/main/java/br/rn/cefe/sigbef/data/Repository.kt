package br.rn.cefe.sigbef.data

import android.content.Context
import br.rn.cefe.sigbef.data.local.EmprestimoEntity
import br.rn.cefe.sigbef.data.local.LivroEntity
import br.rn.cefe.sigbef.data.local.SigbefDatabase
import br.rn.cefe.sigbef.data.local.UsuarioEntity
import br.rn.cefe.sigbef.model.Emprestimo
import br.rn.cefe.sigbef.model.Livro
import br.rn.cefe.sigbef.model.Usuario
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

class SigbefRepository(private val db: SigbefDatabase) {

    val usuarioFlow: Flow<Usuario> = db.usuarioDao().getUsuario().map { entity ->
        entity?.toDomain() ?: usuarioVazio
    }

    val livrosFlow: Flow<List<Livro>> = db.livroDao().getAllLivros().map { list ->
        list.map { it.toDomain() }
    }

    val emprestimosFlow: Flow<List<Emprestimo>> = db.emprestimoDao().getAllEmprestimos().map { list ->
        list.map { it.toDomain() }
    }

    fun searchLivros(query: String, category: String): Flow<List<Livro>> {
        return db.livroDao().searchLivros(query, category).map { list ->
            list.map { it.toDomain() }
        }
    }

    fun getLivroById(id: Int): Flow<Livro?> {
        return db.livroDao().getLivroById(id).map { entity ->
            entity?.toDomain()
        }
    }

    suspend fun updateUsuario(usuario: Usuario) {
        db.usuarioDao().insertUsuario(usuario.toEntity())
    }

    companion object {
        /** Estado antes de o aluno entrar: nenhum dado inventado. */
        val usuarioVazio = Usuario()

        @Volatile
        private var INSTANCE: SigbefRepository? = null

        fun getInstance(context: Context): SigbefRepository {
            return INSTANCE ?: synchronized(this) {
                val database = SigbefDatabase.getDatabase(context)
                val instance = SigbefRepository(database)
                INSTANCE = instance
                instance
            }
        }
    }
}

// Extension Mappers between Room Entities and Domain Models
fun UsuarioEntity.toDomain() = Usuario(
    id = id,
    nome = nome,
    matricula = matricula,
    turma = turma,
    escola = escola
)

fun Usuario.toEntity() = UsuarioEntity(
    id = id,
    nome = nome,
    matricula = matricula,
    turma = turma,
    escola = escola
)

fun LivroEntity.toDomain() = Livro(
    id = id,
    titulo = titulo,
    autor = autor,
    categoria = categoria,
    ano = ano,
    tombo = tombo,
    isbn = isbn,
    sinopse = sinopse,
    disponivel = disponivel,
    previsaoDevolucao = previsaoDevolucao,
    spineColorHex = spineColorHex
)

fun Livro.toEntity() = LivroEntity(
    id = id,
    titulo = titulo,
    autor = autor,
    categoria = categoria,
    ano = ano,
    tombo = tombo,
    isbn = isbn,
    sinopse = sinopse,
    disponivel = disponivel,
    previsaoDevolucao = previsaoDevolucao,
    spineColorHex = spineColorHex
)

fun EmprestimoEntity.toDomain() = Emprestimo(
    id = id,
    livroTitulo = livroTitulo,
    autor = autor,
    dataDevolucao = dataDevolucao,
    atrasado = atrasado,
    devolvido = devolvido,
    dataDevolvido = dataDevolvido,
    spineColorHex = spineColorHex
)

fun Emprestimo.toEntity() = EmprestimoEntity(
    id = id,
    livroTitulo = livroTitulo,
    autor = autor,
    dataDevolucao = dataDevolucao,
    atrasado = atrasado,
    devolvido = devolvido,
    dataDevolvido = dataDevolvido,
    spineColorHex = spineColorHex
)
