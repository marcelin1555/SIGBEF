package br.rn.cefe.sigbef.data

import android.content.Context
import br.rn.cefe.sigbef.data.local.EmprestimoEntity
import br.rn.cefe.sigbef.data.local.EstatisticaLeituraEntity
import br.rn.cefe.sigbef.data.local.LivroEntity
import br.rn.cefe.sigbef.data.local.RecomendacaoEntity
import br.rn.cefe.sigbef.data.local.ReservaEntity
import br.rn.cefe.sigbef.data.local.SigbefDatabase
import br.rn.cefe.sigbef.data.local.UsuarioEntity
import br.rn.cefe.sigbef.data.remote.LoginRequest
import br.rn.cefe.sigbef.data.remote.ReservaRequest
import br.rn.cefe.sigbef.data.remote.RetrofitClient
import br.rn.cefe.sigbef.data.remote.TokenManager
import br.rn.cefe.sigbef.model.Emprestimo
import br.rn.cefe.sigbef.model.EstatisticaLeitura
import br.rn.cefe.sigbef.model.Livro
import br.rn.cefe.sigbef.model.Recomendacao
import br.rn.cefe.sigbef.model.Reserva
import br.rn.cefe.sigbef.model.Usuario
import kotlin.math.abs
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

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

    val reservasFlow: Flow<List<Reserva>> =
        db.reservaDao().getAllReservas().map { lista ->
            lista.map { it.toDomain() }
        }

    val estatisticaFlow: Flow<EstatisticaLeitura> =
        db.leituraDao().getEstatisticas().map { it?.toDomain()
            ?: EstatisticaLeitura() }

    val recomendacoesFlow: Flow<List<Recomendacao>> =
        db.leituraDao().getRecomendacoes().map { lista ->
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
    suspend fun parear(endereco: String): String? {
        val normalizada = RetrofitClient.normalizar(endereco)
        if (!RetrofitClient.eEnderecoLocal(normalizada)) {
            return "Esse endereço não parece ser da rede da escola. O " +
                "SIGBEF fica num computador da própria escola (algo como " +
                "192.168.x.x)."
        }
        // Trocar de biblioteca encerra a sessão: o acesso é emitido por um
        // servidor e não vale no outro — mandá-lo para lá seria entregar o
        // token do aluno a quem não o emitiu.
        if (tokenManager.obterServidor() != normalizada) {
            limparCache()
            tokenManager.sair()
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
        db.reservaDao().clearAll()
        db.livroDao().clearAll()
        db.usuarioDao().clearAll()
        db.leituraDao().limparRecomendacoes()
        db.leituraDao().limparEstatisticas()
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
                escola = corpo.instituicao.orEmpty()
            )
        )
        // Traz turma e situação, que só existem nesta outra rota
        runCatching { sincronizarSituacao() }
        return null
    }

    // --------------------------------------------------- sincronizações
    /** Busca no acervo e guarda o resultado como cache. */
    /**
     * Baixa o acervo inteiro para o cache, uma página por vez.
     *
     * Sempre sem termo de busca: o filtro da tela é local (o DAO faz o
     * LIKE), então sincronizar com a busca ativa substituiria todo o
     * acervo guardado pelos poucos resultados daquela palavra — o aluno
     * ficaria sem catálogo offline.
     *
     * Em páginas porque o servidor deixou de mandar tudo de uma vez: um
     * acervo grande virava um JSON de dezenas de MB, que o aparelho
     * tinha que segurar inteiro na memória antes de gravar a primeira
     * linha. Agora chega em blocos e cada bloco vai direto para o banco.
     */
    suspend fun sincronizarAcervo(): Boolean {
        // Guarda o que já foi baixado da ficha completa para não perder
        // sinopse e tombo a cada sincronização.
        val jaBaixados = db.livroDao().listarTodosUmaVez()
            .associateBy { it.id }

        var pagina = 1
        var totalPaginas = 1
        var algumaChegou = false

        while (pagina <= totalPaginas && pagina <= MAX_PAGINAS_ACERVO) {
            val resposta = runCatching {
                api().buscarLivros(q = "", pagina = pagina,
                                   limite = LIVROS_POR_PAGINA)
            }.getOrElse { return algumaChegou }
            if (!resposta.isSuccessful) return algumaChegou
            val corpo = resposta.body() ?: return algumaChegou

            // A limpeza só acontece depois que a primeira página chega:
            // se a rede cair no meio, o aluno fica com o catálogo antigo
            // em vez de ficar sem catálogo nenhum.
            if (pagina == 1) {
                totalPaginas = corpo.paginas.coerceAtLeast(1)
                db.livroDao().clearAll()
            }

            db.livroDao().insertLivros(
                corpo.livros.map { dto ->
                    val anterior = jaBaixados[dto.id]
                    LivroEntity(
                        id = dto.id,
                        titulo = dto.titulo,
                        autor = dto.autores.orEmpty(),
                        categoria = dto.categoria.orEmpty(),
                        ano = dto.anoPublicacao?.toString().orEmpty(),
                        // O tombo pertence ao exemplar; só vem no detalhe.
                        tombo = anterior?.tombo.orEmpty(),
                        isbn = dto.isbn.orEmpty(),
                        sinopse = anterior?.sinopse.orEmpty(),
                        disponivel = dto.disponiveis > 0,
                        previsaoDevolucao = null,
                        spineColorHex = corDaLombada(dto.titulo)
                    )
                }
            )
            algumaChegou = true
            if (corpo.livros.isEmpty()) break
            pagina++
        }
        return algumaChegou
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

        // O nome da instituição só vem no login; preserva o que já está
        // salvo para não apagar o cabeçalho da carteirinha.
        val escolaAtual = db.usuarioDao().getUsuarioOnce()?.escola.orEmpty()
        db.usuarioDao().insertUsuario(
            UsuarioEntity(
                id = 1,
                nome = dto.nome,
                matricula = dto.matricula,
                turma = dto.turma.orEmpty(),
                escola = escolaAtual,
                limiteEmprestimos = dto.limiteEmprestimos,
                podePegar = dto.podePegar,
                situacao = dto.situacao.orEmpty()
            )
        )

        db.emprestimoDao().clearAll()
        val hoje = hojeIso()
        // Abertos e já devolvidos convivem na mesma tabela; o campo
        // `devolvido` é o que a tela usa para separar as duas seções.
        db.emprestimoDao().insertEmprestimos(
            (dto.emprestimosAbertos + dto.historico).map { emp ->
                val prevista = emp.dataPrevista?.take(10).orEmpty()
                val devolvido = emp.dataDevolucao != null
                EmprestimoEntity(
                    id = emp.id,
                    livroTitulo = emp.titulo,
                    autor = "",
                    dataDevolucao = prevista,
                    // Atraso vem da DATA, não da multa: a multa só é
                    // lançada na devolução, então num empréstimo ainda
                    // aberto ela vale sempre 0 e um livro vencido há
                    // semanas apareceria como "Em dia". Já devolvido
                    // nunca é "atrasado": aquilo é passado.
                    atrasado = !devolvido && prevista.isNotEmpty()
                                && prevista < hoje,
                    devolvido = devolvido,
                    dataDevolvido = emp.dataDevolucao,
                    spineColorHex = corDaLombada(emp.titulo),
                    renovacoes = emp.renovacoes,
                    podeRenovar = emp.podeRenovar,
                    motivoRenovacao = emp.motivoRenovacao.orEmpty()
                )
            }
        )

        db.reservaDao().clearAll()
        db.reservaDao().insertReservas(
            dto.reservasAtivas.map { r ->
                ReservaEntity(
                    id = r.id,
                    livroId = r.livroId,
                    titulo = r.titulo,
                    posicao = r.posicao,
                    separado = r.separado,
                    retirarAte = r.retirarAte?.take(10),
                    spineColorHex = corDaLombada(r.titulo)
                )
            }
        )
        return true
    }

    /**
     * Traz o retrato de leitura e as sugestões.
     *
     * Chamada quando a tela abre, não a cada sincronização: do lado do
     * servidor a recomendação é a consulta mais cara que existe.
     */
    suspend fun sincronizarLeitura(): Boolean {
        val matricula = tokenManager.obterMatricula() ?: return false
        val resposta = runCatching { api().leitura(matricula) }
            .getOrElse { return false }
        val dto = resposta.body()?.takeIf { resposta.isSuccessful } ?: return false

        val e = dto.estatisticas
        db.leituraDao().salvarEstatisticas(
            EstatisticaLeituraEntity(
                totalLidos = e.totalLidos,
                lidosNoAno = e.lidosNoAno,
                diasMedios = e.diasMedios,
                leitorDesde = e.leitorDesde.orEmpty(),
                categoriaFavorita = e.categoriaFavorita.orEmpty(),
                lidosNaFavorita = e.lidosNaFavorita
            )
        )
        db.leituraDao().limparRecomendacoes()
        db.leituraDao().salvarRecomendacoes(
            dto.recomendacoes.mapIndexed { i, r ->
                RecomendacaoEntity(
                    livroId = r.id,
                    titulo = r.titulo,
                    categoria = r.categoria.orEmpty(),
                    motivo = r.motivo.orEmpty(),
                    ordem = i,
                    spineColorHex = corDaLombada(r.titulo)
                )
            }
        )
        return true
    }

    // ------------------------------------------------- ações do aluno
    /**
     * Traduz uma recusa da API na frase que o aluno lê.
     *
     * O 409 é o caso interessante: o servidor já escreveu a explicação
     * ("Outro leitor está esperando…"), então ela é repassada tal e qual
     * em vez de ser substituída por um texto genérico daqui.
     */
    private fun mensagemDeErro(codigo: Int, corpoErro: String?): String {
        val doServidor = corpoErro
            ?.let { runCatching { RetrofitClient.lerErro(it) }.getOrNull() }
            ?.takeIf { it.isNotBlank() }
        return when {
            doServidor != null -> doServidor
            codigo == 401 -> "Seu acesso expirou. Entre de novo."
            codigo == 403 -> "A biblioteca não permitiu esta ação."
            codigo == 404 -> "A biblioteca não encontrou este registro."
            else -> "A biblioteca recusou a ação (erro $codigo)."
        }
    }

    private val semRede =
        "Não consegui falar com a biblioteca. Confira se você está no " +
            "Wi-Fi da escola."

    /**
     * Entra na fila de espera de um livro.
     * @return null se deu certo; a explicação da biblioteca se não.
     */
    suspend fun reservar(livroId: Int): String? {
        val resposta = runCatching { api().reservar(ReservaRequest(livroId)) }
            .getOrElse { return semRede }
        if (!resposta.isSuccessful) {
            return mensagemDeErro(resposta.code(),
                                  resposta.errorBody()?.string())
        }
        sincronizarSituacao()
        return null
    }

    /** Desiste da fila. @return null em caso de sucesso. */
    suspend fun cancelarReserva(reservaId: Int): String? {
        val resposta = runCatching { api().cancelarReserva(reservaId) }
            .getOrElse { return semRede }
        if (!resposta.isSuccessful) {
            return mensagemDeErro(resposta.code(),
                                  resposta.errorBody()?.string())
        }
        sincronizarSituacao()
        return null
    }

    /**
     * Renova o próprio empréstimo. As regras (prazo vencido, fila de
     * espera, limite) são decididas pela biblioteca, não aqui.
     * @return null em caso de sucesso.
     */
    suspend fun renovar(emprestimoId: Int): String? {
        val resposta = runCatching { api().renovar(emprestimoId) }
            .getOrElse { return semRede }
        if (!resposta.isSuccessful) {
            return mensagemDeErro(resposta.code(),
                                  resposta.errorBody()?.string())
        }
        sincronizarSituacao()
        return null
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
         * Tamanho do bloco na sincronização do acervo, igual ao teto que
         * a API aceita. Bloco pequeno multiplica idas à rede (um acervo
         * de 250 mil viraria mais de mil requisições); grande demais
         * traz de volta o problema do JSON gigante. Em 500, cada
         * resposta fica na casa de centenas de KB.
         */
        private const val LIVROS_POR_PAGINA = 500

        /**
         * Teto de segurança. Com 500 por página, cobre 1,25 milhão de
         * livros — muito além de qualquer biblioteca escolar. Existe
         * para o app nunca entrar em laço infinito se o servidor
         * devolver uma contagem de páginas errada.
         */
        private const val MAX_PAGINAS_ACERVO = 2_500

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
    podePegar = podePegar,
    situacao = situacao,
    limMaxLivros = limiteEmprestimos
)

fun Usuario.toEntity() = UsuarioEntity(
    id = id,
    nome = nome,
    matricula = matricula,
    turma = turma,
    escola = escola,
    podePegar = podePegar,
    situacao = situacao,
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

fun EmprestimoEntity.toDomain() = Emprestimo(
    id = id,
    livroTitulo = livroTitulo,
    autor = autor,
    dataDevolucao = dataDevolucao,
    atrasado = atrasado,
    devolvido = devolvido,
    dataDevolvido = dataDevolvido,
    spineColorHex = spineColorHex,
    renovacoes = renovacoes,
    podeRenovar = podeRenovar,
    motivoRenovacao = motivoRenovacao
)

fun EstatisticaLeituraEntity.toDomain() = EstatisticaLeitura(
    totalLidos = totalLidos,
    lidosNoAno = lidosNoAno,
    diasMedios = diasMedios,
    leitorDesde = leitorDesde,
    categoriaFavorita = categoriaFavorita,
    lidosNaFavorita = lidosNaFavorita
)

fun RecomendacaoEntity.toDomain() = Recomendacao(
    livroId = livroId,
    titulo = titulo,
    categoria = categoria,
    motivo = motivo,
    spineColorHex = spineColorHex
)

fun ReservaEntity.toDomain() = Reserva(
    id = id,
    livroId = livroId,
    titulo = titulo,
    posicao = posicao,
    separado = separado,
    retirarAte = retirarAte,
    spineColorHex = spineColorHex
)
