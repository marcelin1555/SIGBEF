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

/**
 * Retrato da leitura do aluno. Linha única (id = 1), como `usuarios`:
 * o aparelho guarda um leitor só.
 *
 * Fica em cache porque o aluno gosta de rever quanto leu — e ele
 * costuma abrir o app fora da escola, onde não há a rede da biblioteca.
 */
@Entity(tableName = "estatisticas_leitura")
data class EstatisticaLeituraEntity(
    @PrimaryKey val id: Int = 1,
    val totalLidos: Int = 0,
    val lidosNoAno: Int = 0,
    val diasMedios: Double = 0.0,
    val leitorDesde: String = "",
    val categoriaFavorita: String = "",
    val lidosNaFavorita: Int = 0
)

@Entity(tableName = "recomendacoes")
data class RecomendacaoEntity(
    @PrimaryKey val livroId: Int,
    val titulo: String,
    val categoria: String = "",
    /** Explicação da sugestão, escrita pela biblioteca. */
    val motivo: String = "",
    /** Preserva a ordem de prioridade que veio do servidor. */
    val ordem: Int = 0,
    val spineColorHex: String = "#1F4E79"
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
