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
    val limiteEmprestimos: Int = 0,
    // Situação vinda da biblioteca ("OK: 1 de 3 empréstimos em uso",
    // "Há multas em aberto..."). Serve para avisar o aluno antes de ele
    // ir ao balcão e descobrir que está impedido.
    val podePegar: Boolean = true,
    val situacao: String = ""
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
    val spineColorHex: String = "#1F4E79",
    val renovacoes: Int = 0,
    // Veredito da biblioteca sobre a renovação, guardado junto para o
    // botão continuar coerente quando o aluno abre o app sem rede.
    val podeRenovar: Boolean = false,
    val motivoRenovacao: String = ""
)

@Entity(tableName = "reservas")
data class ReservaEntity(
    @PrimaryKey val id: Int,
    val livroId: Int,
    val titulo: String,
    /** 1 = próximo da fila. */
    val posicao: Int = 0,
    /** O exemplar já está separado no balcão esperando o aluno. */
    val separado: Boolean = false,
    val retirarAte: String? = null,
    val spineColorHex: String = "#1F4E79"
)
