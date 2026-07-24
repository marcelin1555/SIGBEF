package com.example

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.animation.Crossfade
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Wifi
import androidx.compose.material.icons.filled.WifiOff
import androidx.compose.material3.AssistChip
import androidx.compose.material3.AssistChipDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.sigbef.data.SigbefRepository
import com.example.sigbef.model.Livro
import com.example.sigbef.model.Screen
import com.example.sigbef.ui.SigbefViewModel
import com.example.sigbef.ui.screens.AcervoScreen
import com.example.sigbef.ui.screens.BookDetailScreen
import com.example.sigbef.ui.screens.ConnectScreen
import com.example.sigbef.ui.screens.DigitalCardScreen
import com.example.sigbef.ui.screens.HomeScreen
import com.example.sigbef.ui.screens.LoansScreen
import com.example.sigbef.ui.screens.LoginScreen
import com.example.sigbef.ui.screens.RenewInfoScreen
import com.example.ui.theme.MyApplicationTheme
import com.example.ui.theme.SigbefNavy
import com.example.ui.theme.SigbefWarning

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            MyApplicationTheme {
                SigbefApp()
            }
        }
    }
}

@Composable
fun SigbefApp() {
    val viewModel: SigbefViewModel = viewModel()

    val usuario by viewModel.usuario.collectAsState()
    val livros by viewModel.livros.collectAsState()
    val emprestimos by viewModel.emprestimos.collectAsState()
    val isOffline by viewModel.isOffline.collectAsState()
    val searchQuery by viewModel.searchQuery.collectAsState()
    val selectedCategory by viewModel.selectedCategory.collectAsState()

    var currentScreen by remember { mutableStateOf(Screen.CONNECT) }
    var selectedBookId by remember { mutableStateOf<Int?>(livros.firstOrNull()?.id ?: 1) }

    val currentUsuario = usuario
    val selectedBook = livros.find { it.id == selectedBookId } ?: livros.firstOrNull() ?: SigbefRepository.sampleLivros.first()

    Surface(
        modifier = Modifier.fillMaxSize(),
        color = MaterialTheme.colorScheme.background
    ) {
        Box(modifier = Modifier.fillMaxSize()) {
            Crossfade(
                targetState = currentScreen,
                label = "ScreenTransition"
            ) { screen ->
                when (screen) {
                    Screen.CONNECT -> ConnectScreen(
                        onConnected = {
                            currentScreen = Screen.LOGIN
                        }
                    )

                    Screen.LOGIN -> LoginScreen(
                        onLoginSuccess = {
                            currentScreen = Screen.HOME
                        }
                    )

                    Screen.HOME -> HomeScreen(
                        usuario = currentUsuario,
                        emprestimos = emprestimos,
                        isOffline = isOffline,
                        onNavigate = { dest -> currentScreen = dest }
                    )

                    Screen.ACERVO -> AcervoScreen(
                        livros = livros,
                        isOffline = isOffline,
                        onBookClick = { book ->
                            selectedBookId = book.id
                            currentScreen = Screen.BOOK_DETAIL
                        },
                        onNavigate = { dest -> currentScreen = dest },
                        searchQueryParam = searchQuery,
                        selectedCategoryParam = selectedCategory,
                        onSearchQueryChange = { query -> viewModel.setSearchQuery(query) },
                        onCategoryChange = { category -> viewModel.setSelectedCategory(category) }
                    )

                    Screen.BOOK_DETAIL -> BookDetailScreen(
                        livro = selectedBook,
                        isOffline = isOffline,
                        onBackClick = { currentScreen = Screen.ACERVO },
                        onNavigate = { dest -> currentScreen = dest },
                        onReserveClick = { bookId -> viewModel.reservarLivro(bookId) },
                        onCancelReserveClick = { bookId -> viewModel.cancelarReserva(bookId) }
                    )

                    Screen.LOANS -> LoansScreen(
                        emprestimos = emprestimos,
                        isOffline = isOffline,
                        onNavigate = { dest -> currentScreen = dest },
                        onRequestRenewal = { emprestimoId -> viewModel.solicitarRenovacao(emprestimoId) }
                    )

                    Screen.RENEW_INFO -> RenewInfoScreen(
                        isOffline = isOffline,
                        onBackClick = { currentScreen = Screen.LOANS },
                        onNavigate = { dest -> currentScreen = dest }
                    )

                    Screen.CARD -> DigitalCardScreen(
                        usuario = currentUsuario,
                        isOffline = isOffline,
                        onNavigate = { dest -> currentScreen = dest }
                    )

                    Screen.RESERVE -> BookDetailScreen(
                        livro = selectedBook,
                        isOffline = isOffline,
                        onBackClick = { currentScreen = Screen.ACERVO },
                        onNavigate = { dest -> currentScreen = dest },
                        onReserveClick = { bookId -> viewModel.reservarLivro(bookId) },
                        onCancelReserveClick = { bookId -> viewModel.cancelarReserva(bookId) }
                    )
                }
            }

            // Quick Offline Toggle Badge (Top Right)
            if (currentScreen != Screen.CONNECT && currentScreen != Screen.LOGIN) {
                Box(
                    modifier = Modifier
                        .align(Alignment.TopEnd)
                        .padding(top = 40.dp, end = 12.dp)
                ) {
                    AssistChip(
                        onClick = { viewModel.toggleOfflineMode() },
                        label = {
                            Text(
                                text = if (isOffline) "Modo Offline: ON" else "Online",
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold,
                                color = if (isOffline) Color(0xFF604100) else SigbefNavy
                            )
                        },
                        leadingIcon = {
                            Icon(
                                imageVector = if (isOffline) Icons.Default.WifiOff else Icons.Default.Wifi,
                                contentDescription = "Alternar Modo Offline",
                                tint = if (isOffline) SigbefWarning else SigbefNavy,
                                modifier = Modifier.padding(start = 2.dp)
                            )
                        },
                        colors = AssistChipDefaults.assistChipColors(
                            containerColor = if (isOffline) Color(0xFFFFDEAD) else Color(0xFFD1E4FF)
                        ),
                        border = AssistChipDefaults.assistChipBorder(
                            enabled = true,
                            borderColor = if (isOffline) SigbefWarning else SigbefNavy
                        ),
                        shape = RoundedCornerShape(16.dp)
                    )
                }
            }
        }
    }
}
