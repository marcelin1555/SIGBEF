package br.rn.cefe.sigbef.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "usuarios")
data class UsuarioEntity(
    @PrimaryKey val id: Int = 1,
    val nome: String,
    val matricula: String,
    val turma: String,
    val escola: String,
    val limiteEmprestimos: Int = 0
)

@Entity(tableName = "livros")
data class LivroEntity(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val titulo: String,
    val autor: String,
    val categoria: String,
    val ano: String,
    val tombo: String,
    val isbn: String,
    val sinopse: String,
    val disponivel: Boolean,
    val previsaoDevolucao: String? = null,
    val spineColorHex: String = "#1F4E79"
)

@Entity(tableName = "emprestimos")
data class EmprestimoEntity(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val livroTitulo: String,
    val autor: String,
    val dataDevolucao: String,
    val atrasado: Boolean = false,
    val devolvido: Boolean = false,
    val dataDevolvido: String? = null,
    val spineColorHex: String = "#1F4E79"
)
