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
        if (repository.estaPareado()) {
            verificarConexao()
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

    /** Guarda o endereço da biblioteca lido no QR (ou digitado). */
    fun parear(endereco: String, aoConcluir: () -> Unit) {
        viewModelScope.launch {
            _carregando.value = true
            repository.parear(endereco)
            _isOffline.value = !repository.testarConexao()
            _carregando.value = false
            aoConcluir()
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

    fun sair() {
        repository.sair()
        _currentScreen.value = Screen.LOGIN
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
