package br.rn.cefe.sigbef.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import br.rn.cefe.sigbef.data.SigbefRepository
import br.rn.cefe.sigbef.model.Emprestimo
import br.rn.cefe.sigbef.model.EstatisticaLeitura
import br.rn.cefe.sigbef.model.Livro
import br.rn.cefe.sigbef.model.Recomendacao
import br.rn.cefe.sigbef.model.Reserva
import br.rn.cefe.sigbef.model.Screen
import br.rn.cefe.sigbef.model.Usuario
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

class SigbefViewModel(application: Application) : AndroidViewModel(application) {

    private val repository = SigbefRepository.getInstance(application)

    // ------------------------------------------- sincronizacoes em voo
    /**
     * Toda sincronizacao roda sob este Job, e nao solta no escopo da
     * tela.
     *
     * Sem isso havia uma corrida com consequencia seria num celular
     * compartilhado -- que e o caso comum na escola, onde poucos alunos
     * tem aparelho proprio. `sair()` limpava o cache, mas nao cancelava
     * a sincronizacao ja em voo: a resposta chegava depois e regravava
     * nome, matricula, emprestimos e reservas no banco recem-limpo. O
     * aluno seguinte entrava e via a carteirinha do anterior.
     *
     * O Job e filho do escopo da tela, entao continua morrendo junto com
     * a ViewModel; a diferenca e poder ser cancelado sozinho, sem
     * derrubar o escopo inteiro.
     */
    private var sincronizacoes = novoJobDeSincronizacao()

    private fun novoJobDeSincronizacao() =
        SupervisorJob(viewModelScope.coroutineContext[Job])

    /** Lanca uma sincronizacao sob o Job que `sair()` sabe cancelar. */
    private fun sincronizando(bloco: suspend () -> Unit) {
        viewModelScope.launch(sincronizacoes) { bloco() }
    }

    /**
     * Para toda sincronizacao em voo e **espera** ela parar de verdade.
     *
     * O `join` e a parte que importa: cancelar so pede para parar. Sem
     * esperar, a limpeza do cache poderia acontecer no meio de uma
     * gravacao que ainda estava a caminho -- exatamente o defeito que
     * isto conserta.
     */
    private suspend fun pararSincronizacoes() {
        sincronizacoes.cancelAndJoin()
        sincronizacoes = novoJobDeSincronizacao()
    }

    // ------------------------------------------------------ navegação
    private val _currentScreen = MutableStateFlow(
        when {
            repository.estaLogado() -> Screen.HOME
            repository.estaPareado() -> Screen.LOGIN
            else -> Screen.CONNECT
        }
    )
    val currentScreen: StateFlow<Screen> = _currentScreen.asStateFlow()

    /**
     * Offline = a biblioteca não respondeu. Antes isso era um interruptor
     * manual que abria marcado como "conectado" sem nunca ter tentado
     * falar com ninguém.
     */
    private val _isOffline = MutableStateFlow(true)
    val isOffline: StateFlow<Boolean> = _isOffline.asStateFlow()

    private val _carregando = MutableStateFlow(false)
    val carregando: StateFlow<Boolean> = _carregando.asStateFlow()

    private val _erroLogin = MutableStateFlow<String?>(null)
    val erroLogin: StateFlow<String?> = _erroLogin.asStateFlow()

    private val _erroConexao = MutableStateFlow<String?>(null)
    val erroConexao: StateFlow<String?> = _erroConexao.asStateFlow()

    /** Quando o cache foi atualizado pela última vez (para o banner). */
    private val _ultimaSincronizacao = MutableStateFlow<String?>(null)
    val ultimaSincronizacao: StateFlow<String?> = _ultimaSincronizacao.asStateFlow()

    private val _searchQuery = MutableStateFlow("")
    val searchQuery: StateFlow<String> = _searchQuery.asStateFlow()

    private val _selectedCategory = MutableStateFlow("Todos")
    val selectedCategory: StateFlow<String> = _selectedCategory.asStateFlow()

    private val _selectedBookId = MutableStateFlow<Int?>(null)
    val selectedBookId: StateFlow<Int?> = _selectedBookId.asStateFlow()

    private val _actionNotification = MutableStateFlow<String?>(null)
    val actionNotification: StateFlow<String?> = _actionNotification.asStateFlow()

    // --------------------------------------------- dados vindos do cache
    val usuario: StateFlow<Usuario> = repository.usuarioFlow
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000),
                 SigbefRepository.usuarioVazio)

    val emprestimos: StateFlow<List<Emprestimo>> = repository.emprestimosFlow
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    val reservas: StateFlow<List<Reserva>> = repository.reservasFlow
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    val estatisticaLeitura: StateFlow<EstatisticaLeitura> =
        repository.estatisticaFlow.stateIn(
            viewModelScope, SharingStarted.WhileSubscribed(5000),
            EstatisticaLeitura())

    val recomendacoes: StateFlow<List<Recomendacao>> =
        repository.recomendacoesFlow.stateIn(
            viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    @OptIn(ExperimentalCoroutinesApi::class)
    val livros: StateFlow<List<Livro>> = kotlinx.coroutines.flow.combine(
        _searchQuery, _selectedCategory
    ) { query, cat -> Pair(query, cat) }
        .flatMapLatest { (query, cat) -> repository.searchLivros(query, cat) }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    @OptIn(ExperimentalCoroutinesApi::class)
    val selectedBook: StateFlow<Livro?> = _selectedBookId.flatMapLatest { id ->
        if (id != null) repository.getLivroById(id) else MutableStateFlow(null)
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), null)

    init {
        // Ao reabrir já logado, atualiza os dados em vez de deixar o
        // cache congelado (antes só testava a conexão sem buscar nada).
        when {
            repository.estaLogado() -> sincronizar()
            repository.estaPareado() -> verificarConexao()
        }
    }

    // ------------------------------------------------------------ ações
    fun navigateTo(screen: Screen) {
        _currentScreen.value = screen
        // A recomendação é a consulta mais cara do servidor; buscada só
        // quando a tela abre, nunca junto das sincronizações de rotina.
        if (screen == Screen.READING) {
            sincronizando {
                _carregando.value = true
                try {
                    if (repository.sincronizarLeitura()) {
                        _isOffline.value = false
                        marcarSincronizacao()
                    }
                } finally {
                    _carregando.value = false
                }
            }
        }
    }

    fun setSearchQuery(query: String) {
        _searchQuery.value = query
    }

    fun setSelectedCategory(category: String) {
        _selectedCategory.value = category
    }

    /**
     * Abre a ficha de um livro sabendo só o id — o caminho de quem veio
     * de uma recomendação, onde não há o objeto completo em mãos.
     */
    fun selecionarLivroPorId(livroId: Int) {
        _selectedBookId.value = livroId
        navigateTo(Screen.BOOK_DETAIL)
        sincronizando { repository.sincronizarDetalheLivro(livroId) }
    }

    fun selectBook(book: Livro) {
        _selectedBookId.value = book.id
        navigateTo(Screen.BOOK_DETAIL)
        // Sinopse e tombo só existem na ficha completa
        sincronizando { repository.sincronizarDetalheLivro(book.id) }
    }

    /**
     * Guarda o endereço da biblioteca e só avança se ela responder. Antes
     * avançava sempre, e um endereço errado prendia o aluno no login sem
     * caminho de volta.
     */
    fun parear(endereco: String, aoConectar: () -> Unit) {
        viewModelScope.launch {
            _carregando.value = true
            _erroConexao.value = null

            val recusa = repository.parear(endereco)
            if (recusa != null) {
                _erroConexao.value = recusa
                _carregando.value = false
                return@launch
            }

            val ok = repository.testarConexao()
            _isOffline.value = !ok
            _carregando.value = false
            if (ok) {
                aoConectar()
            } else {
                _erroConexao.value = "Não encontrei a biblioteca nesse " +
                    "endereço. Confira o número e se você está no Wi-Fi " +
                    "da escola."
            }
        }
    }

    fun limparErroConexao() {
        _erroConexao.value = null
    }

    /** Sai da conta, mantendo o pareamento com a escola. */
    fun sair() {
        viewModelScope.launch {
            pararSincronizacoes()
            repository.sair()
            navigateTo(Screen.LOGIN)
        }
    }

    /** Esquece a biblioteca e volta ao pareamento (trocar de escola). */
    fun trocarBiblioteca() {
        viewModelScope.launch {
            pararSincronizacoes()
            repository.desparear()
            navigateTo(Screen.CONNECT)
        }
    }

    fun entrar(matricula: String, senha: String, aoEntrar: () -> Unit) {
        viewModelScope.launch {
            _carregando.value = true
            _erroLogin.value = null
            val erro = repository.entrar(matricula, senha)
            _carregando.value = false
            if (erro == null) {
                _isOffline.value = false
                marcarSincronizacao()
                sincronizar()
                aoEntrar()
            } else {
                _erroLogin.value = erro
            }
        }
    }

    fun limparErroLogin() {
        _erroLogin.value = null
    }

    fun verificarConexao() {
        viewModelScope.launch {
            _isOffline.value = !repository.testarConexao()
        }
    }

    /** Atualiza acervo e situação do leitor a partir da biblioteca. */
    fun sincronizar() {
        sincronizando {
            _carregando.value = true
            // `finally` porque agora a sincronizacao pode mesmo ser
            // cancelada no meio (ao sair da conta). Sem ele, o
            // cancelamento pularia a linha que desliga o indicador e a
            // tela ficaria carregando para sempre.
            try {
                val acervo = repository.sincronizarAcervo()
                val situacao = repository.sincronizarSituacao()
                _isOffline.value = !(acervo || situacao)
                if (acervo || situacao) marcarSincronizacao()
            } finally {
                _carregando.value = false
            }
        }
    }

    private fun marcarSincronizacao() {
        _ultimaSincronizacao.value = java.text.SimpleDateFormat(
            "HH'h'mm", java.util.Locale("pt", "BR")
        ).format(java.util.Date())
    }

    fun clearNotification() {
        _actionNotification.value = null
    }

    // ------------------------------------------------- ações do aluno
    // Reservar, cancelar e renovar são as três únicas coisas que o app
    // grava na biblioteca, sempre nos dados do próprio aluno. Emprestar
    // e devolver seguem sendo do balcão: exigem o livro na mão.

    /** Erro da última ação; vira alerta na tela e some ao ser lido. */
    private val _erroAcao = MutableStateFlow<String?>(null)
    val erroAcao: StateFlow<String?> = _erroAcao.asStateFlow()

    fun limparErroAcao() {
        _erroAcao.value = null
    }

    /** Alguma ação está em andamento — trava o botão para não repetir. */
    private val _acaoEmCurso = MutableStateFlow(false)
    val acaoEmCurso: StateFlow<Boolean> = _acaoEmCurso.asStateFlow()

    /**
     * Roda uma ação da biblioteca cuidando do estado comum: trava o
     * botão, guarda a recusa e avisa quando dá certo.
     */
    private fun executar(aviso: String, acao: suspend () -> String?) {
        if (_acaoEmCurso.value) return
        viewModelScope.launch {
            _acaoEmCurso.value = true
            _erroAcao.value = null
            val erro = acao()
            _acaoEmCurso.value = false
            if (erro == null) {
                _isOffline.value = false
                marcarSincronizacao()
                _actionNotification.value = aviso
            } else {
                _erroAcao.value = erro
            }
        }
    }

    fun reservar(livro: Livro) {
        executar("Você entrou na fila de \"${livro.titulo}\". A biblioteca " +
                 "avisa quando for a sua vez.") {
            repository.reservar(livro.id)
        }
    }

    fun cancelarReserva(reserva: Reserva) {
        executar("Você saiu da fila de \"${reserva.titulo}\".") {
            repository.cancelarReserva(reserva.id)
        }
    }

    fun renovar(emprestimo: Emprestimo) {
        executar("\"${emprestimo.livroTitulo}\" foi renovado.") {
            repository.renovar(emprestimo.id)
        }
    }
}
