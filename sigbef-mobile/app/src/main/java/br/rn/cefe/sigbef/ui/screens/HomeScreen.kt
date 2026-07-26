package br.rn.cefe.sigbef.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Autorenew
import androidx.compose.material.icons.filled.Badge
import androidx.compose.material.icons.filled.ImportContacts
import androidx.compose.material.icons.filled.LibraryBooks
import androidx.compose.material.icons.filled.Schedule
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import br.rn.cefe.sigbef.model.Emprestimo
import br.rn.cefe.sigbef.model.Screen
import br.rn.cefe.sigbef.model.Usuario
import br.rn.cefe.sigbef.ui.components.SigbefBottomNavigation
import br.rn.cefe.sigbef.ui.components.SigbefTopAppBar
import br.rn.cefe.sigbef.ui.theme.SigbefBackground
import br.rn.cefe.sigbef.ui.theme.SigbefBlue
import br.rn.cefe.sigbef.ui.theme.SigbefBlueFundo
import br.rn.cefe.sigbef.ui.theme.SigbefError
import br.rn.cefe.sigbef.ui.theme.SigbefErrorFundo
import br.rn.cefe.sigbef.ui.theme.SigbefInk
import br.rn.cefe.sigbef.ui.theme.SigbefLine
import br.rn.cefe.sigbef.ui.theme.SigbefMuted
import br.rn.cefe.sigbef.ui.theme.SigbefNavy
import br.rn.cefe.sigbef.ui.theme.SigbefSuccess
import br.rn.cefe.sigbef.ui.theme.SigbefWarning
import br.rn.cefe.sigbef.ui.theme.SigbefWarningFundo
import br.rn.cefe.sigbef.ui.theme.SigbefWarningInk

@Composable
fun HomeScreen(
    usuario: Usuario,
    emprestimos: List<Emprestimo> = emptyList(),
    isOffline: Boolean,
    ultimaSincronizacao: String? = null,
    onNavigate: (Screen) -> Unit,
    /** Buscar dados novos na biblioteca. */
    onAtualizar: (() -> Unit)? = null,
    carregando: Boolean = false
) {
    val ativos = emprestimos.filter { !it.devolvido }
    val atrasados = ativos.filter { it.atrasado }
    val maxLivros = usuario.limMaxLivros
    Scaffold(
        topBar = {
            // A saudação vive dentro do gradiente: é o que identifica a
            // tela, e repeti-la no corpo gastava duas faixas de altura
            // com a mesma informação.
            SigbefTopAppBar(
                title = if (usuario.vazio) "SIGBEF"
                        else "Olá, ${usuario.nome.split(" ").first()}!",
                subtitle = usuario.turma.ifBlank { null },
                isOffline = isOffline,
                ultimaSincronizacao = ultimaSincronizacao,
                onAtualizar = onAtualizar,
                carregando = carregando
            )
        },
        bottomBar = {
            SigbefBottomNavigation(
                currentScreen = Screen.HOME,
                onNavigate = onNavigate
            )
        },
        containerColor = SigbefBackground
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(horizontal = 20.dp, vertical = 16.dp),
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            Column {
                // Main Status Card
                Surface(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                    color = Color.White,
                    shadowElevation = 2.dp,
                    border = androidx.compose.foundation.BorderStroke(1.dp, SigbefLine)
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp)
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.Top
                        ) {
                            Column {
                                Text(
                                    text = if (ativos.isEmpty()) "Nenhum livro emprestado" else "${ativos.size} ${if (ativos.size == 1) "livro com você" else "livros com você"}",
                                    fontSize = 18.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = SigbefInk
                                )

                                Spacer(modifier = Modifier.height(6.dp))

                                if (atrasados.isNotEmpty()) {
                                    Row(
                                        modifier = Modifier
                                            .clip(RoundedCornerShape(6.dp))
                                            .background(SigbefErrorFundo)
                                            .padding(horizontal = 8.dp, vertical = 4.dp),
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        Icon(
                                            imageVector = Icons.Default.Schedule,
                                            contentDescription = null,
                                            tint = SigbefError,
                                            modifier = Modifier.size(14.dp)
                                        )
                                        Spacer(modifier = Modifier.width(4.dp))
                                        Text(
                                            text = "${atrasados.size} com devolução em atraso",
                                            fontSize = 12.sp,
                                            fontWeight = FontWeight.SemiBold,
                                            color = SigbefError
                                        )
                                    }
                                } else if (ativos.isNotEmpty()) {
                                    Row(
                                        modifier = Modifier
                                            .clip(RoundedCornerShape(6.dp))
                                            .background(SigbefWarningFundo)
                                            .padding(horizontal = 8.dp, vertical = 4.dp),
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        Icon(
                                            imageVector = Icons.Default.Schedule,
                                            contentDescription = null,
                                            tint = SigbefWarning,
                                            modifier = Modifier.size(14.dp)
                                        )
                                        Spacer(modifier = Modifier.width(4.dp))
                                        Text(
                                            // Calculado a partir das datas reais.
                                            // Antes era o texto fixo "1 vence em
                                            // 3 dias", que aparecia igual mesmo
                                            // com o livro vencendo hoje.
                                            text = proximoVencimento(ativos),
                                            fontSize = 12.sp,
                                            fontWeight = FontWeight.SemiBold,
                                            color = SigbefWarning
                                        )
                                    }
                                } else {
                                    Text(
                                        text = "Explore o acervo da biblioteca",
                                        fontSize = 13.sp,
                                        color = SigbefMuted
                                    )
                                }
                            }

                            Box(
                                modifier = Modifier
                                    .size(40.dp)
                                    .clip(CircleShape)
                                    .background(SigbefBlueFundo),
                                contentAlignment = Alignment.Center
                            ) {
                                Icon(
                                    imageVector = Icons.Default.ImportContacts,
                                    contentDescription = null,
                                    tint = SigbefNavy,
                                    modifier = Modifier.size(20.dp)
                                )
                            }
                        }

                        // Barra do limite só quando a biblioteca informou
                        // o limite (maxLivros > 0). Antes ela usava um
                        // limite que nunca era preenchido, mostrando sempre
                        // "X de 0 do limite".
                        if (maxLivros > 0) {
                            Spacer(modifier = Modifier.height(16.dp))
                            LinearProgressIndicator(
                                progress = { (ativos.size.toFloat() / maxLivros.toFloat()).coerceIn(0f, 1f) },
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .height(8.dp)
                                    .clip(RoundedCornerShape(4.dp)),
                                color = SigbefBlue,
                                trackColor = SigbefLine
                            )
                            Spacer(modifier = Modifier.height(6.dp))
                            Text(
                                text = "${ativos.size} de $maxLivros do limite",
                                fontSize = 12.sp,
                                color = SigbefMuted,
                                modifier = Modifier.align(Alignment.End)
                            )
                        }

                        // A biblioteca já informava quando o aluno está
                        // impedido (multa, atraso, limite), e o app jogava
                        // fora. Melhor saber aqui que descobrir no balcão.
                        if (!usuario.podePegar && usuario.situacao.isNotBlank()) {
                            Spacer(modifier = Modifier.height(12.dp))
                            Surface(
                                modifier = Modifier.fillMaxWidth(),
                                shape = RoundedCornerShape(8.dp),
                                color = SigbefWarningFundo
                            ) {
                                Row(
                                    modifier = Modifier.padding(10.dp),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Icon(
                                        imageVector = Icons.Default.Schedule,
                                        contentDescription = null,
                                        tint = SigbefWarning,
                                        modifier = Modifier.size(16.dp)
                                    )
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Text(
                                        text = usuario.situacao,
                                        fontSize = 12.sp,
                                        color = SigbefWarningInk
                                    )
                                }
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(20.dp))

                // Bento Grid Shortcuts (2x2)
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    BentoShortcutCard(
                        title = "Buscar no acervo",
                        icon = Icons.Default.Search,
                        onClick = { onNavigate(Screen.ACERVO) },
                        modifier = Modifier.weight(1f)
                    )
                    BentoShortcutCard(
                        title = "Meu cartão",
                        icon = Icons.Default.Badge,
                        onClick = { onNavigate(Screen.CARD) },
                        modifier = Modifier.weight(1f)
                    )
                }

                Spacer(modifier = Modifier.height(12.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    BentoShortcutCard(
                        title = "Meus empréstimos",
                        icon = Icons.Default.LibraryBooks,
                        onClick = { onNavigate(Screen.LOANS) },
                        modifier = Modifier.weight(1f)
                    )
                    BentoShortcutCard(
                        title = "Como renovar",
                        icon = Icons.Default.Autorenew,
                        onClick = { onNavigate(Screen.RENEW_INFO) },
                        modifier = Modifier.weight(1f)
                    )
                }
            }

            // Bottom Connection Status Footer
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 8.dp),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Box(
                    modifier = Modifier
                        .size(8.dp)
                        .clip(CircleShape)
                        .background(if (!isOffline) SigbefSuccess else SigbefWarning)
                )
                Spacer(modifier = Modifier.width(6.dp))
                Text(
                    // O nome da escola vem da biblioteca; quando ainda não
                    // se sabe, o texto é neutro (antes o modo offline
                    // trazia "CEFE" chumbado, errado para outra escola).
                    text = when {
                        usuario.escola.isBlank() && !isOffline ->
                            "Conectado à biblioteca da escola"
                        usuario.escola.isBlank() ->
                            "Sem conexão com a biblioteca"
                        !isOffline -> "Conectado à ${usuario.escola}"
                        else -> "Sem conexão — ${usuario.escola}"
                    },
                    fontSize = 13.sp,
                    color = SigbefMuted
                )
            }
        }
    }
}

@Composable
private fun BentoShortcutCard(
    title: String,
    icon: ImageVector,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    // Altura natural (ícone + rótulo). Antes o card era quase quadrado
    // (aspectRatio 1.1) com o rótulo empurrado para a base, o que abria
    // um vão vazio enorme em tela de celular.
    Surface(
        modifier = modifier.clickable { onClick() },
        shape = RoundedCornerShape(16.dp),
        color = Color.White,
        shadowElevation = 1.dp,
        border = androidx.compose.foundation.BorderStroke(1.dp, SigbefLine)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
            horizontalAlignment = Alignment.Start
        ) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .clip(RoundedCornerShape(10.dp))
                    .background(SigbefBlueFundo),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = icon,
                    contentDescription = title,
                    tint = SigbefNavy,
                    modifier = Modifier.size(22.dp)
                )
            }

            Text(
                text = title,
                fontSize = 14.sp,
                fontWeight = FontWeight.SemiBold,
                color = SigbefInk,
                lineHeight = 18.sp
            )
        }
    }
}

/**
 * Texto do prazo mais próximo, calculado das datas reais dos empréstimos.
 *
 * As datas chegam em ISO (yyyy-MM-dd), o mesmo formato do SQLite, então a
 * comparação de texto já ordena certo e não é preciso java.time (que
 * exigiria desugaring no minSdk 24).
 */
private fun proximoVencimento(ativos: List<Emprestimo>): String {
    val hoje = java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.US)
        .format(java.util.Date())

    val datas = ativos.mapNotNull { it.dataDevolucao.take(10).ifBlank { null } }.sorted()
    val proxima = datas.firstOrNull() ?: return "${ativos.size} livro(s) com você"

    val dias = diasEntre(hoje, proxima)
    val quantos = datas.count { it == proxima }
    val quem = if (quantos > 1) "$quantos vencem" else "1 vence"

    return when {
        dias < 0 -> "$quem — prazo vencido"
        dias == 0L -> "$quem hoje"
        dias == 1L -> "$quem amanhã"
        else -> "$quem em $dias dias"
    }
}

/** Diferença em dias entre duas datas ISO; 0 se alguma não parsear. */
private fun diasEntre(de: String, ate: String): Long {
    val fmt = java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.US)
    return try {
        val a = fmt.parse(de) ?: return 0
        val b = fmt.parse(ate) ?: return 0
        (b.time - a.time) / (1000L * 60 * 60 * 24)
    } catch (e: java.text.ParseException) {
        0
    }
}
