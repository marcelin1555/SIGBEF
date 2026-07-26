package br.rn.cefe.sigbef.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.material.icons.filled.Schedule
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Tune
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import br.rn.cefe.sigbef.model.Livro
import br.rn.cefe.sigbef.model.Screen
import br.rn.cefe.sigbef.ui.components.BookSpineView
import br.rn.cefe.sigbef.ui.components.dataParaLer
import br.rn.cefe.sigbef.ui.components.SigbefBottomNavigation
import br.rn.cefe.sigbef.ui.components.SigbefTopAppBar
import br.rn.cefe.sigbef.ui.theme.SigbefBackground
import br.rn.cefe.sigbef.ui.theme.SigbefInk
import br.rn.cefe.sigbef.ui.theme.SigbefLine
import br.rn.cefe.sigbef.ui.theme.SigbefMuted
import br.rn.cefe.sigbef.ui.theme.SigbefNavy
import br.rn.cefe.sigbef.ui.theme.SigbefSuccess
import br.rn.cefe.sigbef.ui.theme.SigbefSuccessFundo
import br.rn.cefe.sigbef.ui.theme.SigbefSurfaceContainerLow
import br.rn.cefe.sigbef.ui.theme.SigbefWarning
import br.rn.cefe.sigbef.ui.theme.SigbefWarningFundo

@Composable
fun AcervoScreen(
    livros: List<Livro>,
    isOffline: Boolean,
    ultimaSincronizacao: String? = null,
    onBookClick: (Livro) -> Unit,
    onNavigate: (Screen) -> Unit,
    searchQueryParam: String = "",
    selectedCategoryParam: String = "Todos",
    onSearchQueryChange: ((String) -> Unit)? = null,
    onCategoryChange: ((String) -> Unit)? = null,
    /** Buscar dados novos na biblioteca. */
    onAtualizar: (() -> Unit)? = null,
    carregando: Boolean = false
) {
    var searchQueryLocal by remember { mutableStateOf(searchQueryParam) }
    var selectedCategoryLocal by remember { mutableStateOf(selectedCategoryParam) }

    val searchQuery = if (onSearchQueryChange != null) searchQueryParam else searchQueryLocal
    val selectedCategory = if (onCategoryChange != null) selectedCategoryParam else selectedCategoryLocal

    // Categorias derivadas do acervo REAL que chegou da biblioteca, não
    // uma lista fixa inventada (antes: Literatura/Didáticos/HQ/Exatas, que
    // podiam nem existir no acervo da escola). Só aparece o que existe.
    val categories = remember(livros) {
        listOf("Todos") + livros
            .map { it.categoria }
            .filter { it.isNotBlank() }
            .distinct()
            .sorted()
    }

    val filteredLivros = if (onSearchQueryChange != null) {
        livros
    } else {
        livros.filter { livro ->
            val matchesSearch = searchQuery.isBlank() ||
                    livro.titulo.contains(searchQuery, ignoreCase = true) ||
                    livro.autor.contains(searchQuery, ignoreCase = true) ||
                    livro.categoria.contains(searchQuery, ignoreCase = true)

            val matchesCategory = selectedCategory == "Todos" ||
                    livro.categoria.contains(selectedCategory, ignoreCase = true)

            matchesSearch && matchesCategory
        }
    }

    Scaffold(
        topBar = {
            SigbefTopAppBar(
                title = "Acervo",
                isOffline = isOffline,
                ultimaSincronizacao = ultimaSincronizacao,
                onAtualizar = onAtualizar,
                carregando = carregando
            )
        },
        bottomBar = {
            SigbefBottomNavigation(
                currentScreen = Screen.ACERVO,
                onNavigate = onNavigate
            )
        },
        containerColor = SigbefBackground
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
        ) {
            // Search Input & Filter Section
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 20.dp, vertical = 12.dp)
            ) {
                OutlinedTextField(
                    value = searchQuery,
                    onValueChange = { newQuery ->
                        searchQueryLocal = newQuery
                        onSearchQueryChange?.invoke(newQuery)
                    },
                    // Os campos aqui são os mesmos do LIKE em LivroDao:
                    // categoria não entra, ela é o filtro de chips abaixo.
                    placeholder = { Text("Título, autor, ISBN ou tombo") },
                    leadingIcon = {
                        Icon(
                            imageVector = Icons.Default.Search,
                            contentDescription = "Buscar",
                            tint = SigbefMuted
                        )
                    },
                    trailingIcon = {
                        if (searchQuery.isNotEmpty()) {
                            IconButton(onClick = {
                                searchQueryLocal = ""
                                onSearchQueryChange?.invoke("")
                            }) {
                                Icon(
                                    imageVector = Icons.Default.Close,
                                    contentDescription = "Limpar busca",
                                    tint = SigbefMuted
                                )
                            }
                        } else {
                            Box(
                                modifier = Modifier
                                    .padding(end = 8.dp)
                                    .size(36.dp)
                                    .clip(CircleShape)
                                    .background(SigbefNavy.copy(alpha = 0.1f)),
                                contentAlignment = Alignment.Center
                            ) {
                                Icon(
                                    imageVector = Icons.Default.Tune,
                                    contentDescription = "Filtro",
                                    tint = SigbefNavy,
                                    modifier = Modifier.size(20.dp)
                                )
                            }
                        }
                    },
                    singleLine = true,
                    // A busca roda no que já foi baixado (SQL no Room), então
                    // funciona sem rede. Antes o campo era desabilitado
                    // offline, sem motivo.
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(24.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedContainerColor = Color.White,
                        unfocusedContainerColor = Color.White,
                        disabledContainerColor = SigbefSurfaceContainerLow,
                        focusedBorderColor = SigbefNavy,
                        unfocusedBorderColor = SigbefLine
                    )
                )

                Spacer(modifier = Modifier.height(12.dp))

                // Category Chips
                LazyRow(
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    items(categories) { cat ->
                        val selected = selectedCategory == cat
                        FilterChip(
                            selected = selected,
                            onClick = {
                                selectedCategoryLocal = cat
                                onCategoryChange?.invoke(cat)
                            },
                            label = { Text(cat, fontSize = 13.sp) },
                            shape = RoundedCornerShape(20.dp),
                            colors = FilterChipDefaults.filterChipColors(
                                selectedContainerColor = SigbefNavy,
                                selectedLabelColor = Color.White,
                                containerColor = Color.White,
                                labelColor = SigbefInk
                            ),
                            border = FilterChipDefaults.filterChipBorder(
                                enabled = true,
                                selected = selected,
                                borderColor = SigbefLine,
                                selectedBorderColor = SigbefNavy
                            )
                        )
                    }
                }

                Spacer(modifier = Modifier.height(12.dp))

                Text(
                    text = "Resultados — ${filteredLivros.size} encontrados",
                    fontSize = 13.sp,
                    color = SigbefMuted
                )
            }

            // Empty Search State
            if (filteredLivros.isEmpty()) {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    Icon(
                        imageVector = Icons.Default.MenuBook,
                        contentDescription = "Livro não encontrado",
                        tint = SigbefMuted.copy(alpha = 0.5f),
                        modifier = Modifier.size(72.dp)
                    )

                    Spacer(modifier = Modifier.height(16.dp))

                    Text(
                        text = "Nenhum livro encontrado para '$searchQuery'",
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold,
                        color = SigbefInk,
                        textAlign = androidx.compose.ui.text.style.TextAlign.Center
                    )

                    Spacer(modifier = Modifier.height(8.dp))

                    Text(
                        text = "Tente buscar só pelo sobrenome do autor ou verifique a ortografia.",
                        fontSize = 14.sp,
                        color = SigbefMuted,
                        textAlign = androidx.compose.ui.text.style.TextAlign.Center
                    )

                    Spacer(modifier = Modifier.height(24.dp))

                    Button(
                        onClick = {
                            searchQueryLocal = ""
                            selectedCategoryLocal = "Todos"
                            onSearchQueryChange?.invoke("")
                            onCategoryChange?.invoke("Todos")
                        },
                        colors = ButtonDefaults.buttonColors(containerColor = SigbefNavy),
                        shape = RoundedCornerShape(8.dp)
                    ) {
                        Text("LIMPAR BUSCA")
                    }
                }
            } else {
                // Book List
                LazyColumn(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(horizontal = 20.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    items(filteredLivros) { livro ->
                        BookCard(
                            livro = livro,
                            onClick = { onBookClick(livro) }
                        )
                    }
                    item {
                        Spacer(modifier = Modifier.height(16.dp))
                    }
                }
            }
        }
    }
}

@Composable
private fun BookCard(
    livro: Livro,
    onClick: () -> Unit
) {
    val spineColor = try {
        Color(android.graphics.Color.parseColor(livro.spineColorHex))
    } catch (e: Exception) {
        SigbefNavy
    }

    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .height(132.dp)
            .clickable { onClick() },
        shape = RoundedCornerShape(12.dp),
        color = Color.White,
        shadowElevation = 2.dp,
        border = androidx.compose.foundation.BorderStroke(1.dp, SigbefLine)
    ) {
        Row(
            modifier = Modifier.fillMaxSize()
        ) {
            // Book Spine
            BookSpineView(
                title = livro.titulo,
                backgroundColor = spineColor,
                width = 42.dp,
                height = 132.dp
            )

            // Content
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(14.dp),
                verticalArrangement = Arrangement.SpaceBetween
            ) {
                Column {
                    Text(
                        text = livro.titulo,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold,
                        color = SigbefInk,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                    Spacer(modifier = Modifier.height(2.dp))
                    Text(
                        text = livro.autor,
                        fontSize = 13.sp,
                        color = SigbefMuted,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = livro.categoria,
                        fontSize = 12.sp,
                        color = SigbefMuted,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                        modifier = Modifier.weight(1f)
                    )

                    Spacer(modifier = Modifier.width(8.dp))

                    if (livro.disponivel) {
                        Row(
                            modifier = Modifier
                                .clip(RoundedCornerShape(6.dp))
                                .background(SigbefSuccessFundo)
                                .padding(horizontal = 8.dp, vertical = 4.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(
                                imageVector = Icons.Default.CheckCircle,
                                contentDescription = "Disponível",
                                tint = SigbefSuccess,
                                modifier = Modifier.size(14.dp)
                            )
                            Spacer(modifier = Modifier.width(4.dp))
                            Text(
                                text = "Disponível",
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold,
                                color = SigbefSuccess
                            )
                        }
                    } else {
                        Row(
                            modifier = Modifier
                                .clip(RoundedCornerShape(6.dp))
                                .background(SigbefWarningFundo)
                                .padding(horizontal = 8.dp, vertical = 4.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(
                                imageVector = Icons.Default.Schedule,
                                contentDescription = "Devolução",
                                tint = SigbefWarning,
                                modifier = Modifier.size(14.dp)
                            )
                            Spacer(modifier = Modifier.width(4.dp))
                            Text(
                                text = livro.previsaoDevolucao
                                    ?.let { "Volta em ${dataParaLer(it)}" }
                                    ?: "Emprestado",
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold,
                                color = SigbefWarning
                            )
                        }
                    }
                }
            }
        }
    }
}
