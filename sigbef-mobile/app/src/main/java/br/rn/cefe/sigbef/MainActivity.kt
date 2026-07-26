package br.rn.cefe.sigbef

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.SystemBarStyle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.animation.Crossfade
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
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
import br.rn.cefe.sigbef.ui.screens.ReadingScreen
import br.rn.cefe.sigbef.ui.screens.RenewInfoScreen
import br.rn.cefe.sigbef.ui.theme.MyApplicationTheme
import br.rn.cefe.sigbef.ui.theme.SigbefNavy
import br.rn.cefe.sigbef.ui.theme.SigbefWarning

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Ícones da barra de status em branco: ela fica sobre o cabeçalho
        // em gradiente navy, e no padrão claro o relógio e a bateria
        // sumiriam no azul escuro.
        enableEdgeToEdge(
            statusBarStyle = SystemBarStyle.dark(android.graphics.Color.TRANSPARENT)
        )
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
    val ultimaSync by viewModel.ultimaSincronizacao.collectAsState()
    val reservas by viewModel.reservas.collectAsState()
    val acaoEmCurso by viewModel.acaoEmCurso.collectAsState()
    val erroAcao by viewModel.erroAcao.collectAsState()
    val aviso by viewModel.actionNotification.collectAsState()
    val estatistica by viewModel.estatisticaLeitura.collectAsState()
    val recomendacoes by viewModel.recomendacoes.collectAsState()

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
                        ultimaSincronizacao = ultimaSync,
                        onNavigate = viewModel::navigateTo,
                        carregando = carregando,
                        onAtualizar = { viewModel.sincronizar() }
                    )

                    Screen.ACERVO -> AcervoScreen(
                        livros = livros,
                        isOffline = isOffline,
                        ultimaSincronizacao = ultimaSync,
                        // selectBook já busca a ficha completa (tombo e
                        // sinopse) e navega para o detalhe. Antes isto
                        // setava só o id e a ficha nunca era carregada.
                        onBookClick = { book -> viewModel.selectBook(book) },
                        onNavigate = viewModel::navigateTo,
                        searchQueryParam = searchQuery,
                        selectedCategoryParam = selectedCategory,
                        onSearchQueryChange = { query -> viewModel.setSearchQuery(query) },
                        onCategoryChange = { category -> viewModel.setSelectedCategory(category) },
                        carregando = carregando,
                        onAtualizar = { viewModel.sincronizar() }
                    )

                    Screen.BOOK_DETAIL, Screen.RESERVE -> {
                        val livro = selectedBook
                        if (livro != null) {
                            val minhaReserva = reservas.firstOrNull {
                                it.livroId == livro.id
                            }
                            BookDetailScreen(
                                livro = livro,
                                isOffline = isOffline,
                                onBackClick = { viewModel.navigateTo(Screen.ACERVO) },
                                onNavigate = viewModel::navigateTo,
                                reservaDoLivro = minhaReserva,
                                acaoEmCurso = acaoEmCurso,
                                onReservar = { viewModel.reservar(livro) },
                                onCancelarReserva = {
                                    minhaReserva?.let { viewModel.cancelarReserva(it) }
                                }
                            )
                        } else {
                            // Chegou aqui sem livro escolhido: volta ao acervo.
                            LaunchedEffect(Unit) { viewModel.navigateTo(Screen.ACERVO) }
                        }
                    }

                    Screen.LOANS -> LoansScreen(
                        emprestimos = emprestimos,
                        isOffline = isOffline,
                        ultimaSincronizacao = ultimaSync,
                        onNavigate = viewModel::navigateTo,
                        reservas = reservas,
                        acaoEmCurso = acaoEmCurso,
                        onRenovar = { viewModel.renovar(it) },
                        onCancelarReserva = { viewModel.cancelarReserva(it) },
                        carregando = carregando,
                        onAtualizar = { viewModel.sincronizar() }
                    )

                    Screen.RENEW_INFO -> RenewInfoScreen(
                        isOffline = isOffline,
                        onBackClick = { viewModel.navigateTo(Screen.LOANS) },
                        onNavigate = viewModel::navigateTo
                    )

                    Screen.READING -> ReadingScreen(
                        estatistica = estatistica,
                        recomendacoes = recomendacoes,
                        isOffline = isOffline,
                        onNavigate = viewModel::navigateTo,
                        ultimaSincronizacao = ultimaSync,
                        // Abrir a sugestão leva à ficha do livro, de onde
                        // dá para reservar — a recomendação vira ação.
                        onAbrirLivro = { id -> viewModel.selecionarLivroPorId(id) },
                        carregando = carregando,
                        onAtualizar = { viewModel.navigateTo(Screen.READING) }
                    )

                    Screen.CARD -> DigitalCardScreen(
                        usuario = currentUsuario,
                        isOffline = isOffline,
                        ultimaSincronizacao = ultimaSync,
                        onNavigate = viewModel::navigateTo,
                        onSair = { viewModel.sair() },
                        onTrocarBiblioteca = { viewModel.trocarBiblioteca() },
                        carregando = carregando,
                        onAtualizar = { viewModel.sincronizar() }
                    )
                }
            }

            // O estado da conexão e o botão de atualizar agora vivem na
            // barra do topo de cada tela. Antes era um chip solto
            // flutuando sobre o conteúdo, que com o cabeçalho em
            // gradiente passaria a cobrir o título.

            // Recusa da biblioteca: exige leitura, então para o aluno em
            // vez de passar despercebida no canto da tela.
            erroAcao?.let { mensagem ->
                AlertDialog(
                    onDismissRequest = { viewModel.limparErroAcao() },
                    confirmButton = {
                        TextButton(onClick = { viewModel.limparErroAcao() }) {
                            Text("Entendi")
                        }
                    },
                    title = { Text("Não deu certo") },
                    text = { Text(mensagem) }
                )
            }

            // Confirmação do que acabou de acontecer, some sozinha.
            aviso?.let { mensagem ->
                LaunchedEffect(mensagem) {
                    kotlinx.coroutines.delay(4000)
                    viewModel.clearNotification()
                }
                Surface(
                    modifier = Modifier
                        .align(Alignment.BottomCenter)
                        // Alto o bastante para passar da barra de navegação
                        // e da barra de ação do detalhe do livro — era ali
                        // que ele cobria justamente o botão recém-usado.
                        .padding(horizontal = 16.dp)
                        .padding(bottom = 180.dp),
                    shape = RoundedCornerShape(12.dp),
                    color = SigbefNavy,
                    shadowElevation = 8.dp
                ) {
                    Text(
                        text = mensagem,
                        color = Color.White,
                        fontSize = 14.sp,
                        modifier = Modifier.padding(16.dp)
                    )
                }
            }
        }
    }
}
