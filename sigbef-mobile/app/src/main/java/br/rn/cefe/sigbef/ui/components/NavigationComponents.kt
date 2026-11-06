package br.rn.cefe.sigbef.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.CloudOff
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.WifiOff
import androidx.compose.material.icons.outlined.Badge
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material.icons.outlined.ImportContacts
import androidx.compose.material.icons.outlined.LibraryBooks
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import br.rn.cefe.sigbef.model.Screen
import br.rn.cefe.sigbef.ui.theme.SigbefCores

/** Cabeçalho neutro com título, atualização e aviso de conexão. */
@Composable
fun SigbefTopAppBar(
    title: String = "SIGBEF",
    subtitle: String? = null,
    showBack: Boolean = false,
    onBackClick: () -> Unit = {},
    isOffline: Boolean = false,
    /** Hora da última atualização; nulo quando nunca houve nenhuma. */
    ultimaSincronizacao: String? = null,
    /** Buscar dados novos na biblioteca. Sem isto, o botão não aparece. */
    onAtualizar: (() -> Unit)? = null,
    carregando: Boolean = false
) {
    Surface(
        shadowElevation = 0.dp,
        color = SigbefCores.atual.superficie,
        modifier = Modifier.fillMaxWidth()
    ) {
        Column {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    // A superfície ocupa a área do relógio; o conteúdo respeita o inset.
                    .background(SigbefCores.atual.superficie)
                    .statusBarsPadding()
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(56.dp)
                        .padding(horizontal = 8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    if (showBack) {
                        IconButton(
                            onClick = onBackClick,
                            modifier = Modifier.size(48.dp)
                        ) {
                            Icon(
                                imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                                contentDescription = "Voltar",
                                tint = SigbefCores.atual.tinta
                            )
                        }
                        Spacer(modifier = Modifier.size(4.dp))
                    } else {
                        Spacer(modifier = Modifier.size(12.dp))
                        Icon(
                            imageVector = Icons.Default.MenuBook,
                            contentDescription = "Logo SIGBEF",
                            tint = SigbefCores.atual.tinta,
                            modifier = Modifier.size(24.dp)
                        )
                        Spacer(modifier = Modifier.size(10.dp))
                    }
                    Text(
                        text = title,
                        style = if (showBack) MaterialTheme.typography.titleLarge
                                else MaterialTheme.typography.headlineSmall,
                        color = SigbefCores.atual.tinta,
                        letterSpacing = if (showBack) 0.sp else 0.5.sp,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                        modifier = Modifier.weight(1f, fill = false)
                    )

                    Spacer(modifier = Modifier.weight(1f))

                    // Atualizar mora aqui, no canto da barra, onde se
                    // espera. Antes era um chip solto flutuando sobre a
                    // tela, que agora bateria no cabeçalho.
                    if (onAtualizar != null) {
                        IconButton(
                            onClick = onAtualizar,
                            enabled = !carregando,
                            modifier = Modifier.size(48.dp)
                        ) {
                            if (carregando) {
                                CircularProgressIndicator(
                                    color = SigbefCores.atual.tinta,
                                    strokeWidth = 2.dp,
                                    modifier = Modifier.size(18.dp)
                                )
                            } else {
                                Icon(
                                    imageVector = if (isOffline)
                                        Icons.Default.CloudOff
                                    else Icons.Default.Refresh,
                                    contentDescription = if (isOffline)
                                        "Sem conexão. Tocar para tentar de novo"
                                    else "Atualizar dados da biblioteca",
                                    tint = if (isOffline) SigbefCores.atual.aviso
                                           else SigbefCores.atual.tinta
                                )
                            }
                        }
                    }
                }

                if (!subtitle.isNullOrBlank()) {
                    Text(
                        text = subtitle,
                        style = MaterialTheme.typography.bodySmall,
                        color = SigbefCores.atual.secundario,
                        modifier = Modifier.padding(
                            start = 20.dp, end = 20.dp, bottom = 14.dp
                        )
                    )
                }
            }

            // Separação discreta entre cabeçalho e conteúdo.
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(1.dp)
                    .background(SigbefCores.atual.linha)
            )

            if (isOffline) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(SigbefCores.atual.avisoFundo)
                        .padding(horizontal = 16.dp, vertical = 8.dp),
                    // Top, e não Center: o texto quebra em duas linhas em
                    // tela estreita, e centralizado o ícone flutuaria no
                    // meio delas.
                    verticalAlignment = Alignment.Top
                ) {
                    Icon(
                        imageVector = Icons.Default.WifiOff,
                        contentDescription = "Modo Offline",
                        tint = SigbefCores.atual.aviso,
                        modifier = Modifier
                            .size(16.dp)
                            .padding(top = 1.dp)
                    )
                    Spacer(modifier = Modifier.size(8.dp))
                    Text(
                        // Só fala em "última consulta" se ela existiu de
                        // fato; antes o texto prometia dados antigos mesmo
                        // quando nunca tinha havido sincronização nenhuma.
                        //
                        // A segunda frase é o que o aluno precisa saber no
                        // balcão: sem sinal, o cartão continua valendo.
                        text = if (ultimaSincronizacao != null)
                            "Sem conexão — dados de $ultimaSincronizacao. " +
                                "Seu cartão continua funcionando."
                        else
                            "Sem conexão com a biblioteca. Seu cartão " +
                                "continua funcionando.",
                        style = MaterialTheme.typography.labelMedium,
                        color = SigbefCores.atual.avisoTinta,
                    )
                }
            }
        }
    }
}

/**
 * Navegação Material com quatro destinos e estado selecionado acessível.
 *
 * Não recebe `isOffline`: o estado da conexão é dito uma vez só, na
 * tarja do topo.
 */
@Composable
fun SigbefBottomNavigation(
    currentScreen: Screen,
    onNavigate: (Screen) -> Unit
) {
    Column(modifier = Modifier.background(SigbefCores.atual.superficie)) {
        Box(Modifier.fillMaxWidth().height(1.dp).background(SigbefCores.atual.linha))
        NavigationBar(
            containerColor = SigbefCores.atual.superficie,
            tonalElevation = 0.dp
        ) {
            val destinos = listOf(Screen.HOME, Screen.ACERVO, Screen.LOANS, Screen.CARD)
            val nomes = listOf("Início", "Acervo", "Empréstimos", "Cartão")
            val icones = listOf(Icons.Outlined.Home, Icons.Outlined.LibraryBooks,
                Icons.Outlined.ImportContacts, Icons.Outlined.Badge)
            destinos.forEachIndexed { index, destino ->
                val selecionado = currentScreen == destino ||
                    (destino == Screen.ACERVO && currentScreen == Screen.BOOK_DETAIL) ||
                    (destino == Screen.LOANS && currentScreen == Screen.RENEW_INFO)
                NavigationBarItem(
                    selected = selecionado,
                    onClick = { onNavigate(destino) },
                    icon = { Icon(icones[index], contentDescription = null) },
                    label = { Text(nomes[index], style = MaterialTheme.typography.labelSmall) },
                    colors = NavigationBarItemDefaults.colors(
                        selectedIconColor = MaterialTheme.colorScheme.primary,
                        selectedTextColor = MaterialTheme.colorScheme.primary,
                        indicatorColor = SigbefCores.atual.azulFundo,
                        unselectedIconColor = SigbefCores.atual.secundario,
                        unselectedTextColor = SigbefCores.atual.secundario
                    )
                )
            }
        }
    }
}
