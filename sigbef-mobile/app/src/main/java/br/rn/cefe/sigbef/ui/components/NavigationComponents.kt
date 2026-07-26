package br.rn.cefe.sigbef.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Badge
import androidx.compose.material.icons.filled.CloudOff
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.ImportContacts
import androidx.compose.material.icons.filled.LibraryBooks
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.WifiOff
import androidx.compose.material.icons.outlined.Badge
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material.icons.outlined.ImportContacts
import androidx.compose.material.icons.outlined.LibraryBooks
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import br.rn.cefe.sigbef.model.Screen
import br.rn.cefe.sigbef.ui.theme.SigbefBlueFundo
import br.rn.cefe.sigbef.ui.theme.SigbefGold
import br.rn.cefe.sigbef.ui.theme.SigbefMuted
import br.rn.cefe.sigbef.ui.theme.SigbefNavy
import br.rn.cefe.sigbef.ui.theme.SigbefSuccess
import br.rn.cefe.sigbef.ui.theme.SigbefSurface
import br.rn.cefe.sigbef.ui.theme.SigbefWarning
import br.rn.cefe.sigbef.ui.theme.SigbefWarningFundo
import br.rn.cefe.sigbef.ui.theme.SigbefWarningInk

/**
 * Barra do topo, em gradiente da marca fechado pela faixa dourada — a
 * mesma assinatura do site.
 *
 * Ela absorveu o título de cada tela. Antes a barra dizia só "SIGBEF" e
 * logo abaixo o corpo repetia um título grande ("Meus empréstimos"),
 * gastando duas faixas de altura com uma informação só.
 *
 * @param title nome da tela; "SIGBEF" com a marca ao lado quando é a
 *        abertura.
 * @param subtitle linha de apoio, opcional.
 */
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
        shadowElevation = 2.dp,
        color = SigbefSurface,
        modifier = Modifier.fillMaxWidth()
    ) {
        Column {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    // O gradiente sobe por baixo da barra de status, e o
                    // conteúdo desce o suficiente para não ficar embaixo
                    // do relógio.
                    .background(GradienteMarca)
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
                            modifier = Modifier.size(40.dp)
                        ) {
                            Icon(
                                imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                                contentDescription = "Voltar",
                                tint = Color.White
                            )
                        }
                        Spacer(modifier = Modifier.size(4.dp))
                    } else {
                        Spacer(modifier = Modifier.size(12.dp))
                        Icon(
                            imageVector = Icons.Default.MenuBook,
                            contentDescription = "Logo SIGBEF",
                            tint = Color.White,
                            modifier = Modifier.size(24.dp)
                        )
                        Spacer(modifier = Modifier.size(10.dp))
                    }
                    Text(
                        text = title,
                        fontSize = if (showBack) 18.sp else 20.sp,
                        fontWeight = if (showBack) FontWeight.Bold
                                     else FontWeight.ExtraBold,
                        color = Color.White,
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
                            modifier = Modifier.size(44.dp)
                        ) {
                            if (carregando) {
                                CircularProgressIndicator(
                                    color = Color.White,
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
                                    tint = if (isOffline) SigbefGold
                                           else Color.White
                                )
                            }
                        }
                    }
                }

                if (!subtitle.isNullOrBlank()) {
                    Text(
                        text = subtitle,
                        fontSize = 13.sp,
                        color = Color.White.copy(alpha = 0.85f),
                        modifier = Modifier.padding(
                            start = 20.dp, end = 20.dp, bottom = 14.dp
                        )
                    )
                }
            }

            // A faísca dourada da marca. 4dp de propósito: o guia manda
            // usar dourado como realce, nunca em bloco grande.
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(4.dp)
                    .background(SigbefGold)
            )

            if (isOffline) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(SigbefWarningFundo)
                        .padding(horizontal = 16.dp, vertical = 8.dp),
                    // Top, e não Center: o texto quebra em duas linhas em
                    // tela estreita, e centralizado o ícone flutuaria no
                    // meio delas.
                    verticalAlignment = Alignment.Top
                ) {
                    Icon(
                        imageVector = Icons.Default.WifiOff,
                        contentDescription = "Modo Offline",
                        tint = SigbefWarning,
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
                        fontSize = 12.sp,
                        color = SigbefWarningInk,
                        fontWeight = FontWeight.Medium
                    )
                }
            }
        }
    }
}

/**
 * Barra de navegação.
 *
 * Não recebe mais `isOffline`: o estado da conexão é dito uma vez só, na
 * tarja do topo. Repeti-lo aqui embaixo virava ruído — e era o que
 * empurrava um selo cortado para cima do "Cartão".
 */
@Composable
fun SigbefBottomNavigation(
    currentScreen: Screen,
    onNavigate: (Screen) -> Unit
) {
    Surface(
        color = SigbefSurface,
        shadowElevation = 8.dp,
        shape = RoundedCornerShape(topStart = 16.dp, topEnd = 16.dp),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 8.dp, horizontal = 12.dp),
            horizontalArrangement = Arrangement.SpaceAround,
            verticalAlignment = Alignment.CenterVertically
        ) {
            NavItem(
                label = "Início",
                selected = currentScreen == Screen.HOME,
                selectedIcon = Icons.Default.Home,
                unselectedIcon = Icons.Outlined.Home,
                onClick = { onNavigate(Screen.HOME) }
            )

            NavItem(
                label = "Acervo",
                selected = currentScreen == Screen.ACERVO || currentScreen == Screen.BOOK_DETAIL,
                selectedIcon = Icons.Default.LibraryBooks,
                unselectedIcon = Icons.Outlined.LibraryBooks,
                onClick = { onNavigate(Screen.ACERVO) }
            )

            NavItem(
                label = "Empréstimos",
                selected = currentScreen == Screen.LOANS || currentScreen == Screen.RENEW_INFO,
                selectedIcon = Icons.Default.ImportContacts,
                unselectedIcon = Icons.Outlined.ImportContacts,
                onClick = { onNavigate(Screen.LOANS) }
            )

            // Havia aqui um selo verde "OFFLINE OK" sobre o Cartão. Saiu:
            // ficava colado na borda da tela e cortado, tinha 7sp (nem
            // dava para ler), e um "OK" verde contradizia a tarja âmbar
            // de "sem conexão" logo acima. O mesmo recado agora está na
            // tarja do topo, que tem largura para dizê-lo por extenso.
            NavItem(
                label = "Cartão",
                selected = currentScreen == Screen.CARD,
                selectedIcon = Icons.Default.Badge,
                unselectedIcon = Icons.Outlined.Badge,
                onClick = { onNavigate(Screen.CARD) }
            )
        }
    }
}

@Composable
private fun NavItem(
    label: String,
    selected: Boolean,
    selectedIcon: androidx.compose.ui.graphics.vector.ImageVector,
    unselectedIcon: androidx.compose.ui.graphics.vector.ImageVector,
    onClick: () -> Unit
) {
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(12.dp))
            .background(if (selected) SigbefBlueFundo else Color.Transparent)
            .clickable { onClick() }
            .padding(horizontal = 16.dp, vertical = 6.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(
                imageVector = if (selected) selectedIcon else unselectedIcon,
                contentDescription = label,
                tint = if (selected) SigbefNavy else SigbefMuted,
                modifier = Modifier.size(24.dp)
            )
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = label,
                fontSize = 11.sp,
                fontWeight = if (selected) FontWeight.Bold else FontWeight.Normal,
                color = if (selected) SigbefNavy else SigbefMuted
            )
        }
    }
}
