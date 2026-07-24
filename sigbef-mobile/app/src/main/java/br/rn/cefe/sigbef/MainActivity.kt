package br.rn.cefe.sigbef

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
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import br.rn.cefe.sigbef.data.SigbefRepository
import br.rn.cefe.sigbef.model.Livro
import br.rn.cefe.sigbef.model.Screen
import br.rn.cefe.sigbef.ui.SigbefViewModel
import br.rn.cefe.sigbef.ui.screens.AcervoScreen
import br.rn.cefe.sigbef.ui.screens.BookDetailScreen
import br.rn.cefe.sigbef.ui.screens.ConnectScreen
import br.rn.cefe.sigbef.ui.screens.DigitalCardScreen
import br.rn.cefe.sigbef.ui.screens.HomeScreen
import br.rn.cefe.sigbef.ui.screens.LoansScreen
import br.rn.cefe.sigbef.ui.screens.LoginScreen
import br.rn.cefe.sigbef.ui.screens.RenewInfoScreen
import br.rn.cefe.sigbef.ui.theme.MyApplicationTheme
import br.rn.cefe.sigbef.ui.theme.SigbefNavy
import br.rn.cefe.sigbef.ui.theme.SigbefWarning

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
    val carregando by viewModel.carregando.collectAsState()
    val erroLogin by viewModel.erroLogin.collectAsState()
    val erroConexao by viewModel.erroConexao.collectAsState()

    // A tela e o livro selecionado vivem no ViewModel, que sobrevive à
    // rotação do aparelho. Antes eram variáveis locais em `remember`, e
    // girar o celular jogava o aluno de volta para o pareamento.
    val currentScreen by viewModel.currentScreen.collectAsState()
    val selectedBook by viewModel.selectedBook.collectAsState()

    val currentUsuario = usuario

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
                    // O endereço informado agora é guardado, em vez de
                    // descartado como acontecia antes.
                    Screen.CONNECT -> ConnectScreen(
                        carregando = carregando,
                        erro = erroConexao,
                        onConnected = { endereco ->
                            viewModel.parear(endereco) {
                                viewModel.navigateTo(Screen.LOGIN)
                            }
                        }
                    )

                    Screen.LOGIN -> LoginScreen(
                        carregando = carregando,
                        erro = erroLogin,
                        onEntrar = { matricula, senha ->
                            viewModel.entrar(matricula, senha) {
                                viewModel.navigateTo(Screen.HOME)
                            }
                        }
                    )

                    Screen.HOME -> HomeScreen(
                        usuario = currentUsuario,
                        emprestimos = emprestimos,
                        isOffline = isOffline,
                        onNavigate = viewModel::navigateTo
                    )

                    Screen.ACERVO -> AcervoScreen(
                        livros = livros,
                        isOffline = isOffline,
                        // selectBook já busca a ficha completa (tombo e
                        // sinopse) e navega para o detalhe. Antes isto
                        // setava só o id e a ficha nunca era carregada.
                        onBookClick = { book -> viewModel.selectBook(book) },
                        onNavigate = viewModel::navigateTo,
                        searchQueryParam = searchQuery,
                        selectedCategoryParam = selectedCategory,
                        onSearchQueryChange = { query -> viewModel.setSearchQuery(query) },
                        onCategoryChange = { category -> viewModel.setSelectedCategory(category) }
                    )

                    Screen.BOOK_DETAIL, Screen.RESERVE -> {
                        val livro = selectedBook
                        if (livro != null) {
                            BookDetailScreen(
                                livro = livro,
                                isOffline = isOffline,
                                onBackClick = { viewModel.navigateTo(Screen.ACERVO) },
                                onNavigate = viewModel::navigateTo
                            )
                        } else {
                            // Chegou aqui sem livro escolhido: volta ao acervo.
                            LaunchedEffect(Unit) { viewModel.navigateTo(Screen.ACERVO) }
                        }
                    }

                    Screen.LOANS -> LoansScreen(
                        emprestimos = emprestimos,
                        isOffline = isOffline,
                        onNavigate = viewModel::navigateTo
                    )

                    Screen.RENEW_INFO -> RenewInfoScreen(
                        isOffline = isOffline,
                        onBackClick = { viewModel.navigateTo(Screen.LOANS) },
                        onNavigate = viewModel::navigateTo
                    )

                    Screen.CARD -> DigitalCardScreen(
                        usuario = currentUsuario,
                        isOffline = isOffline,
                        onNavigate = viewModel::navigateTo,
                        onSair = { viewModel.sair() },
                        onTrocarBiblioteca = { viewModel.trocarBiblioteca() }
                    )
                }
            }

            // Estado real da conexão. Antes isto era um interruptor manual
            // que abria marcado como "Online" sem nunca ter feito uma
            // requisição. Agora reflete o último contato com a biblioteca,
            // e tocar nele tenta reconectar e atualizar.
            if (currentScreen != Screen.CONNECT && currentScreen != Screen.LOGIN) {
                Box(
                    modifier = Modifier
                        .align(Alignment.TopEnd)
                        .padding(top = 40.dp, end = 12.dp)
                ) {
                    AssistChip(
                        onClick = { viewModel.sincronizar() },
                        label = {
                            Text(
                                text = when {
                                    carregando -> "Atualizando…"
                                    isOffline -> "Sem conexão"
                                    else -> "Conectado"
                                },
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold,
                                color = if (isOffline) Color(0xFF604100) else SigbefNavy
                            )
                        },
                        leadingIcon = {
                            Icon(
                                imageVector = if (isOffline) Icons.Default.WifiOff else Icons.Default.Wifi,
                                contentDescription = "Atualizar dados da biblioteca",
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
