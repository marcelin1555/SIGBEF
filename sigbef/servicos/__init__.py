"""
SIGBEF — Camada de serviços (regras de negócio).

Um módulo por assunto. Tudo é reexportado aqui, então as telas e a API
continuam chamando `servicos.realizar_emprestimo(...)` sem saber em
qual arquivo a função mora.
"""
from ..erros import RegraNegocioError
from .comum import (
    _codigo_barras_unico,
)
from .regras import (
    _atraso_e_multa,
    _limite_para_perfil,
    _prazo_colecao,
    _prazo_para_perfil,
    _teto_colecao,
)
from .acervo import (
    ANO_MAXIMO,
    ANO_MINIMO,
    adicionar_exemplares,
    buscar_metadados_isbn,
    cadastrar_livro,
    consulta_de_busca,
    contar_livros,
    definir_isbn_lookup,
    detalhes_livro,
    editar_livro,
    excluir_livro,
    isbn_lookup_ativo,
    listar_autores,
    listar_categorias,
    listar_exemplares_disponiveis,
    listar_livros,
    _filtro_de_livros,
    _inserir_livro_cur,
    _PALAVRA,
    _tombo_em_uso,
    _upsert_nome,
    _validar_ano,
    _validar_isbn_inedito,
    _validar_titulo_autores,
    _validar_tombos_ineditos,
)
from .importacao import (
    gerar_modelo_csv,
    importar_acervo_csv,
    MODELO_CSV,
    _ALIASES_CSV,
    _corrigir_numero_de_planilha,
    _normalizar_cabecalho,
    _NOTACAO_CIENTIFICA,
    _NUMERO_DE_PLANILHA,
)
from .emprestimos import (
    dono_do_emprestimo_aberto,
    isentar_multa,
    listar_emprestimos_em_aberto,
    listar_emprestimos_usuario,
    localizar_exemplar,
    localizar_usuario,
    pode_renovar,
    quitar_multa,
    realizar_devolucao,
    realizar_emprestimo,
    renovar_emprestimo,
    saldo_multa,
    status_usuario,
    StatusUsuario,
    _motivo_para_nao_renovar,
)
from .exemplares import (
    alterar_localizacao_exemplar,
    alterar_tombo_exemplar,
    baixar_exemplar,
    candidato_de_reabertura,
    listar_exemplares_para_etiquetas,
    MOTIVOS_BAIXA,
    reverter_baixa,
)
from .usuarios import (
    alterar_senha,
    alternar_status_usuario,
    atualizar_usuario,
    cadastrar_usuario,
    excluir_usuario,
    gerar_cartao_usuario,
    listar_usuarios,
    obter_usuario,
)
from .colecao import (
    devolver_colecao,
    emprestar_colecao,
    listar_colecoes_em_aberto,
)
from .relatorios import (
    emprestimos_por_categoria,
    emprestimos_por_mes,
    emprestimos_por_turma,
    estatisticas,
    livros_nunca_emprestados,
    relatorio_circulacao,
    relatorio_inadimplentes,
    relatorio_movimentacao,
    resumo_de_uso,
    _recorte_de_periodo,
)
from .leitor import (
    estatisticas_do_leitor,
    recomendacoes_para,
)
from .auditoria import (
    contar_auditoria,
    listar_acoes_auditoria,
    listar_auditoria,
    _filtro_de_auditoria,
)
from .configuracao import (
    BRASAO_CHAVE,
    BRASAO_LIMITE_BYTES,
    CAMPOS_CONFIG,
    CHAVES_SIGILOSAS,
    definir_config_auditada,
    definir_preferencia,
    normalizar_config,
    obter_brasao,
    obter_config,
    remover_brasao,
    salvar_brasao,
    salvar_configuracoes,
    _MAGIC_GIF,
    _MAGIC_PNG,
)
