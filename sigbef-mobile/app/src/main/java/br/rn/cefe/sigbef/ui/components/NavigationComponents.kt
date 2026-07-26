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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Badge
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.ImportContacts
import androidx.compose.material.icons.filled.LibraryBooks
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.material.icons.filled.WifiOff
import androidx.compose.material.icons.outlined.Badge
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material.icons.outlined.ImportContacts
import androidx.compose.material.icons.outlined.LibraryBooks
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
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import br.rn.cefe.sigbef.model.Screen
import br.rn.cefe.sigbef.ui.theme.SigbefNavy
import br.rn.cefe.sigbef.ui.theme.SigbefWarning

@Composable
fun SigbefTopAppBar(
    title: String = "SIGBEF",
    showBack: Boolean = false,
    onBackClick: () -> Unit = {},
    isOffline: Boolean = false,
    /** Hora da última atualização; nulo quando nunca houve nenhuma. */
    ultimaSincronizacao: String? = null
) {
    Surface(
        shadowElevation = 2.dp,
        color = Color.White,
        modifier = Modifier.fillMaxWidth()
    ) {
        Column {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp)
                    .padding(horizontal = 16.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.Center
            ) {
                if (showBack) {
                    IconButton(
                        onClick = onBackClick,
                        modifier = Modifier.size(40.dp)
                    ) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Voltar",
                            tint = SigbefNavy
                        )
                    }
                    Spacer(modifier = Modifier.weight(1f))
                    Text(
                        text = title,
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold,
                        color = SigbefNavy
                    )
                    Spacer(modifier = Modifier.weight(1f))
                    Spacer(modifier = Modifier.size(40.dp))
                } else {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.Center
                    ) {
                        Icon(
                            imageVector = Icons.Default.MenuBook,
                            contentDescription = "Logo SIGBEF",
                            tint = SigbefNavy,
                            modifier = Modifier.size(24.dp)
                        )
                        Spacer(modifier = Modifier.size(8.dp))
                        Text(
                            text = title,
                            fontSize = 20.sp,
                            fontWeight = FontWeight.ExtraBold,
                            color = SigbefNavy,
                            letterSpacing = 0.5.sp
                        )
                    }
                }
            }

            if (isOffline) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(Color(0xFFFFDEAD))
                        .padding(horizontal = 16.dp, vertical = 6.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        imageVector = Icons.Default.WifiOff,
                        contentDescription = "Modo Offline",
                        tint = SigbefWarning,
                        modifier = Modifier.size(16.dp)
                    )
                    Spacer(modifier = Modifier.size(8.dp))
                    Text(
                        // Só fala em "última consulta" se ela existiu de
                        // fato; antes o texto prometia dados antigos mesmo
                        // quando nunca tinha havido sincronização nenhuma.
                        text = if (ultimaSincronizacao != null)
                            "Sem conexão — mostrando os dados de $ultimaSincronizacao"
                        else
                            "Sem conexão com a biblioteca",
                        fontSize = 12.sp,
                        color = Color(0xFF604100),
                        fontWeight = FontWeight.Medium
                    )
                }
            }
        }
    }
}

@Composable
fun SigbefBottomNavigation(
    currentScreen: Screen,
    onNavigate: (Screen) -> Unit,
    isOffline: Boolean = false
) {
    Surface(
        color = Color.White,
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

            Box {
                NavItem(
                    label = "Cartão",
                    selected = currentScreen == Screen.CARD,
                    selectedIcon = Icons.Default.Badge,
                    unselectedIcon = Icons.Outlined.Badge,
                    onClick = { onNavigate(Screen.CARD) }
                )
                if (isOffline) {
                    Box(
                        modifier = Modifier
                            .align(Alignment.TopEnd)
                            .clip(RoundedCornerShape(8.dp))
                            .background(Color(0xFF2E7D32))
                            .padding(horizontal = 4.dp, vertical = 2.dp)
                    ) {
                        Text(
                            text = "OFFLINE OK",
                            fontSize = 7.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color.White
                        )
                    }
                }
            }
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
            .background(if (selected) Color(0xFF7CBAFF) else Color.Transparent)
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
                tint = if (selected) Color(0xFF004A7D) else Color(0xFF5C6A78),
                modifier = Modifier.size(24.dp)
            )
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = label,
                fontSize = 11.sp,
                fontWeight = if (selected) FontWeight.Bold else FontWeight.Normal,
                color = if (selected) Color(0xFF004A7D) else Color(0xFF5C6A78)
            )
        }
    }
}
