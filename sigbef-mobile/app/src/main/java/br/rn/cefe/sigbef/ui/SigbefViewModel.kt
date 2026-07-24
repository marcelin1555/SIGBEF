package br.rn.cefe.sigbef.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import br.rn.cefe.sigbef.data.SigbefRepository
import br.rn.cefe.sigbef.model.Emprestimo
import br.rn.cefe.sigbef.model.Livro
import br.rn.cefe.sigbef.model.Screen
import br.rn.cefe.sigbef.model.Usuario
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

class SigbefViewModel(application: Application) : AndroidViewModel(application) {

    private val repository = SigbefRepository.getInstance(application)

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
    }

    fun setSearchQuery(query: String) {
        _searchQuery.value = query
    }

    fun setSelectedCategory(category: String) {
        _selectedCategory.value = category
    }

    fun selectBook(book: Livro) {
        _selectedBookId.value = book.id
        navigateTo(Screen.BOOK_DETAIL)
        // Sinopse e tombo só existem na ficha completa
        viewModelScope.launch { repository.sincronizarDetalheLivro(book.id) }
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
            repository.sair()
            navigateTo(Screen.LOGIN)
        }
    }

    /** Esquece a biblioteca e volta ao pareamento (trocar de escola). */
    fun trocarBiblioteca() {
        viewModelScope.launch {
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
        viewModelScope.launch {
            _carregando.value = true
            val acervo = repository.sincronizarAcervo(_searchQuery.value)
            val situacao = repository.sincronizarSituacao()
            _isOffline.value = !(acervo || situacao)
            if (acervo || situacao) marcarSincronizacao()
            _carregando.value = false
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

    // Reservar, renovar e emprestar NÃO são funções do aplicativo: a API
    // da biblioteca é somente leitura, então qualquer botão aqui estaria
    // mentindo para o aluno. As telas orientam a procurar o balcão.
}
