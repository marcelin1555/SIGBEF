package com.example.sigbef.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.sigbef.data.SigbefRepository
import com.example.sigbef.model.Emprestimo
import com.example.sigbef.model.Livro
import com.example.sigbef.model.Screen
import com.example.sigbef.model.Usuario
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
            initialValue = SigbefRepository.defaultUsuario
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

    fun reservarLivro(bookId: Int) {
        viewModelScope.launch {
            repository.setReservaStatus(bookId, true)
            _actionNotification.value = "Reserva realizada com sucesso! Apresente sua carteirinha no balcão."
        }
    }

    fun cancelarReserva(bookId: Int) {
        viewModelScope.launch {
            repository.setReservaStatus(bookId, false)
            _actionNotification.value = "Reserva cancelada."
        }
    }

    fun solicitarRenovacao(emprestimoId: Int) {
        viewModelScope.launch {
            repository.solicitarRenovacao(emprestimoId)
            _actionNotification.value = "Solicitação de renovação enviada para a biblioteca!"
        }
    }

    fun clearNotification() {
        _actionNotification.value = null
    }
}
