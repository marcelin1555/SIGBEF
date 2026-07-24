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

    // Navigation & UI State
    private val _currentScreen = MutableStateFlow(Screen.CONNECT)
    val currentScreen: StateFlow<Screen> = _currentScreen.asStateFlow()

    private val _isOffline = MutableStateFlow(false)
    val isOffline: StateFlow<Boolean> = _isOffline.asStateFlow()

    private val _searchQuery = MutableStateFlow("")
    val searchQuery: StateFlow<String> = _searchQuery.asStateFlow()

    private val _selectedCategory = MutableStateFlow("Todos")
    val selectedCategory: StateFlow<String> = _selectedCategory.asStateFlow()

    private val _selectedBookId = MutableStateFlow<Int?>(1)
    val selectedBookId: StateFlow<Int?> = _selectedBookId.asStateFlow()

    private val _actionNotification = MutableStateFlow<String?>(null)
    val actionNotification: StateFlow<String?> = _actionNotification.asStateFlow()

    // Reactive Flows from Room Database
    val usuario: StateFlow<Usuario> = repository.usuarioFlow
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = SigbefRepository.usuarioVazio
        )

    val emprestimos: StateFlow<List<Emprestimo>> = repository.emprestimosFlow
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = emptyList()
        )

    @OptIn(ExperimentalCoroutinesApi::class)
    val livros: StateFlow<List<Livro>> = kotlinx.coroutines.flow.combine(
        _searchQuery,
        _selectedCategory
    ) { query, cat ->
        Pair(query, cat)
    }.flatMapLatest { (query, cat) ->
        repository.searchLivros(query, cat)
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = emptyList()
    )

    @OptIn(ExperimentalCoroutinesApi::class)
    val selectedBook: StateFlow<Livro?> = _selectedBookId.flatMapLatest { id ->
        if (id != null) {
            repository.getLivroById(id)
        } else {
            MutableStateFlow(null)
        }
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = null
    )

    // User Actions
    fun navigateTo(screen: Screen) {
        _currentScreen.value = screen
    }

    fun toggleOfflineMode() {
        _isOffline.value = !_isOffline.value
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
    }

    // Reservar, renovar e emprestar NÃO são funções do aplicativo: a API
    // da biblioteca é somente leitura, então qualquer botão aqui estaria
    // mentindo para o aluno (a bibliotecária nunca receberia o pedido).
    // As telas orientam a procurar o balcão.

    fun clearNotification() {
        _actionNotification.value = null
    }
}
