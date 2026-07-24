package br.rn.cefe.sigbef.data

import android.content.Context
import br.rn.cefe.sigbef.data.local.EmprestimoEntity
import br.rn.cefe.sigbef.data.local.LivroEntity
import br.rn.cefe.sigbef.data.local.SigbefDatabase
import br.rn.cefe.sigbef.data.local.UsuarioEntity
import br.rn.cefe.sigbef.data.remote.LoginRequest
import br.rn.cefe.sigbef.data.remote.RetrofitClient
import br.rn.cefe.sigbef.data.remote.TokenManager
import br.rn.cefe.sigbef.model.Emprestimo
import br.rn.cefe.sigbef.model.Livro
import br.rn.cefe.sigbef.model.Usuario
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlin.math.abs

/**
 * Ponte entre a biblioteca (API do desktop) e o aparelho (cache Room).
 *
 * A tela sempre lê do Room, para funcionar sem rede; as funções
 * `sincronizar*` buscam na API e atualizam o cache. Nada é inventado
 * aqui: sem sincronizar, o cache fica vazio e as telas mostram estado
 * vazio de verdade.
 */
class SigbefRepository(
    private val db: SigbefDatabase,
    private val tokenManager: TokenManager
) {

    // ------------------------------------------------ leitura (cache)
    val usuarioFlow: Flow<Usuario> = db.usuarioDao().getUsuario().map { entity ->
        entity?.toDomain() ?: usuarioVazio
    }

    val livrosFlow: Flow<List<Livro>> = db.livroDao().getAllLivros().map { lista ->
        lista.map { it.toDomain() }
    }

    val emprestimosFlow: Flow<List<Emprestimo>> =
        db.emprestimoDao().getAllEmprestimos().map { lista ->
            lista.map { it.toDomain() }
        }

    fun searchLivros(query: String, category: String): Flow<List<Livro>> =
        db.livroDao().searchLivros(query, category).map { lista ->
            lista.map { it.toDomain() }
        }

    fun getLivroById(id: Int): Flow<Livro?> =
        db.livroDao().getLivroById(id).map { it?.toDomain() }

    suspend fun updateUsuario(usuario: Usuario) {
        db.usuarioDao().insertUsuario(usuario.toEntity())
    }

    // ------------------------------------------------------ pareamento
    /**
     * @return null se o endereço foi aceito; uma mensagem se for recusado
     *         por não ser um endereço de rede local.
     */
    fun parear(endereco: String): String? {
        val normalizada = RetrofitClient.normalizar(endereco)
        if (!RetrofitClient.eEnderecoLocal(normalizada)) {
            return "Esse endereço não parece ser da rede da escola. O " +
                "SIGBEF fica num computador da própria escola (algo como " +
                "192.168.x.x)."
        }
        tokenManager.salvarServidor(normalizada)
        RetrofitClient.limpar()
        return null
    }

    fun estaPareado(): Boolean = tokenManager.temServidor()

    fun estaLogado(): Boolean = tokenManager.estaLogado()

    /** Sai da conta e apaga o cache deste aluno (nada do anterior fica). */
    suspend fun sair() {
        limparCache()
        tokenManager.sair()
        RetrofitClient.limpar()
    }

    /** Esquece também a biblioteca, para trocar de escola. */
    suspend fun desparear() {
        limparCache()
        tokenManager.limparTudo()
        RetrofitClient.limpar()
    }

    private suspend fun limparCache() {
        db.emprestimoDao().clearAll()
        db.livroDao().clearAll()
        db.usuarioDao().clearAll()
    }

    private fun api() = RetrofitClient.getApiService(
        tokenManager,
        tokenManager.obterServidor()
            ?: throw IllegalStateException("Biblioteca não pareada.")
    )

    /** Testa se a biblioteca responde. Usado para saber se está offline. */
    suspend fun testarConexao(): Boolean = runCatching {
        api().ping().isSuccessful
    }.getOrDefault(false)

    // ----------------------------------------------------------- login
    /**
     * Entra com matrícula e senha do sistema da biblioteca.
     * @return null em caso de sucesso; a mensagem de erro caso contrário.
     */
    suspend fun entrar(matricula: String, senha: String): String? {
        val resposta = runCatching {
            api().login(LoginRequest(matricula.trim(), senha))
        }.getOrElse {
            return "Não consegui falar com a biblioteca. Confira se você " +
                "está no Wi-Fi da escola."
        }

        if (!resposta.isSuccessful) {
            return when (resposta.code()) {
                401 -> "Matrícula ou senha incorretos."
                403 -> "A biblioteca está com o acesso pelo aplicativo desligado."
                else -> "A biblioteca recusou a entrada (erro ${resposta.code()})."
            }
        }
        val corpo = resposta.body() ?: return "Resposta vazia da biblioteca."
        tokenManager.salvarAcesso(corpo.token, corpo.usuario.matricula)

        db.usuarioDao().insertUsuario(
            UsuarioEntity(
                id = 1,
                nome = corpo.usuario.nome,
                matricula = corpo.usuario.matricula,
                turma = "",
                escola = ""
            )
        )
        // Traz turma e situação, que só existem nesta outra rota
        runCatching { sincronizarSituacao() }
        return null
    }

    // --------------------------------------------------- sincronizações
    /** Busca no acervo e guarda o resultado como cache. */
    suspend fun sincronizarAcervo(termo: String = ""): Boolean {
        val resposta = runCatching { api().buscarLivros(q = termo) }
            .getOrElse { return false }
        if (!resposta.isSuccessful) return false
        val livros = resposta.body()?.livros ?: return false

        db.livroDao().clearAll()
        db.livroDao().insertLivros(
            livros.map { dto ->
                LivroEntity(
                    id = dto.id,
                    titulo = dto.titulo,
                    autor = dto.autores.orEmpty(),
                    categoria = dto.categoria.orEmpty(),
                    ano = dto.anoPublicacao?.toString().orEmpty(),
                    // O tombo pertence ao exemplar; só vem no detalhe.
                    tombo = "",
                    isbn = dto.isbn.orEmpty(),
                    sinopse = "",
                    disponivel = dto.disponiveis > 0,
                    previsaoDevolucao = null,
                    spineColorHex = corDaLombada(dto.titulo)
                )
            }
        )
        return true
    }

    /** Completa a ficha de um livro (sinopse e tombo do 1º exemplar). */
    suspend fun sincronizarDetalheLivro(id: Int): Boolean {
        val resposta = runCatching { api().detalheLivro(id) }
            .getOrElse { return false }
        val dto = resposta.body()?.takeIf { resposta.isSuccessful } ?: return false

        val atual = db.livroDao().getLivroByIdOnce(id) ?: return false
        db.livroDao().updateLivro(
            atual.copy(
                sinopse = dto.sinopse.orEmpty(),
                isbn = dto.isbn.orEmpty(),
                autor = dto.autores.joinToString(", "),
                categoria = dto.categoria.orEmpty(),
                ano = dto.anoPublicacao?.toString().orEmpty(),
                tombo = dto.exemplares.firstOrNull()?.numeroTombo.orEmpty(),
                disponivel = dto.exemplares.any { it.status == "DISPONIVEL" }
            )
        )
        return true
    }

    /** Traz a situação do leitor: carteirinha + empréstimos em aberto. */
    suspend fun sincronizarSituacao(): Boolean {
        val matricula = tokenManager.obterMatricula() ?: return false
        val resposta = runCatching { api().situacaoLeitor(matricula) }
            .getOrElse { return false }
        val dto = resposta.body()?.takeIf { resposta.isSuccessful } ?: return false

        db.usuarioDao().insertUsuario(
            UsuarioEntity(
                id = 1,
                nome = dto.nome,
                matricula = dto.matricula,
                turma = dto.turma.orEmpty(),
                escola = "",
                limiteEmprestimos = dto.limiteEmprestimos
            )
        )

        db.emprestimoDao().clearAll()
        val hoje = hojeIso()
        db.emprestimoDao().insertEmprestimos(
            dto.emprestimosAbertos.map { emp ->
                val prevista = emp.dataPrevista?.take(10).orEmpty()
                EmprestimoEntity(
                    id = emp.id,
                    livroTitulo = emp.titulo,
                    autor = "",
                    dataDevolucao = prevista,
                    // Atraso vem da DATA, não da multa: a multa só é
                    // lançada na devolução, então num empréstimo ainda
                    // aberto ela vale sempre 0 e um livro vencido há
                    // semanas apareceria como "Em dia".
                    atrasado = prevista.isNotEmpty() && prevista < hoje,
                    devolvido = emp.dataDevolucao != null,
                    dataDevolvido = emp.dataDevolucao,
                    spineColorHex = corDaLombada(emp.titulo)
                )
            }
        )
        return true
    }

    /**
     * Data de hoje em ISO (yyyy-MM-dd), no mesmo formato que o SQLite
     * devolve — assim a comparação de texto já ordena corretamente e o
     * app não precisa de java.time (que exigiria desugaring no minSdk 24).
     */
    private fun hojeIso(): String =
        java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.US)
            .format(java.util.Date())

    companion object {
        /** Estado antes de o aluno entrar: nenhum dado inventado. */
        val usuarioVazio = Usuario()

        /**
         * Cor da lombada derivada do título, só para a lista não ficar
         * monótona. É decisão visual local — a biblioteca não guarda cor.
         */
        private val PALETA = listOf(
            "#1F4E79", "#2E75B6", "#4C92C9", "#2A64A0", "#3B7EA1"
        )

        fun corDaLombada(titulo: String): String =
            PALETA[abs(titulo.hashCode()) % PALETA.size]

        @Volatile
        private var INSTANCE: SigbefRepository? = null

        fun getInstance(context: Context): SigbefRepository {
            return INSTANCE ?: synchronized(this) {
                val instance = SigbefRepository(
                    SigbefDatabase.getDatabase(context),
                    TokenManager.getInstance(context)
                )
                INSTANCE = instance
                instance
            }
        }
    }
}

// Conversões entre as entidades do Room e os modelos de domínio
fun UsuarioEntity.toDomain() = Usuario(
    id = id,
    nome = nome,
    matricula = matricula,
    turma = turma,
    escola = escola,
    limMaxLivros = limiteEmprestimos
)

fun Usuario.toEntity() = UsuarioEntity(
    id = id,
    nome = nome,
    matricula = matricula,
    turma = turma,
    escola = escola,
    limiteEmprestimos = limMaxLivros
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
