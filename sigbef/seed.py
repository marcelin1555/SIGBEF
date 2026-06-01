"""
SIGBEF — Popula o banco com usuários de exemplo, livros e exemplares.

Executado automaticamente na primeira execução do sistema. Pode ser rodado
manualmente com:

    python -m sigbef.seed
"""
from __future__ import annotations

from .auth import gerar_hash
from .database import db_cursor
from .servicos import cadastrar_livro, cadastrar_usuario


USUARIOS_PADRAO = [
    # (nome, matricula, perfil, senha, email, turma)
    ("Marcello Melo",            "admin",     "ADMINISTRADOR", "admin123",     "marcello@cefe.edu",        ""),
    ("Laiane Souza",             "laiane",    "BIBLIOTECARIO", "laiane123",    "laiane@cefe.edu",          ""),
    ("Jaqueline Oliveira",       "jaqueline", "BIBLIOTECARIO", "jaqueline123", "jaqueline@cefe.edu",       ""),
    ("Macilene Lima",            "macilene",  "PROFESSOR",     "macilene123",  "macilene@cefe.edu",        ""),
    ("Lucas Pereira Santos",     "2024001",   "ALUNO",         "lucas123",     "lucas.santos@cefe.edu",    "3º Ano Técnico em Informática"),
    ("Beatriz Almeida Rocha",    "2024002",   "ALUNO",         "beatriz123",   "beatriz.rocha@cefe.edu",   "2º Ano Técnico em Administração"),
]


LIVROS_PADRAO = [
    {
        "titulo": "Dom Casmurro",
        "autores": ["Machado de Assis"],
        "isbn": "9788535910663",
        "editora": "Companhia das Letras",
        "categoria": "Literatura Brasileira",
        "ano": 1899,
        "edicao": "1ª",
        "sinopse": "Romance clássico de Machado de Assis sobre Bento e Capitu.",
        "quantidade_exemplares": 3,
        "localizacao": "Estante A — Prateleira 1",
    },
    {
        "titulo": "Vidas Secas",
        "autores": ["Graciliano Ramos"],
        "isbn": "9788501010220",
        "editora": "Record",
        "categoria": "Literatura Brasileira",
        "ano": 1938,
        "edicao": "98ª",
        "sinopse": "Família retirante luta pela sobrevivência no sertão nordestino.",
        "quantidade_exemplares": 2,
        "localizacao": "Estante A — Prateleira 2",
    },
    {
        "titulo": "O Cortiço",
        "autores": ["Aluísio Azevedo"],
        "isbn": "9788508133024",
        "editora": "Ática",
        "categoria": "Literatura Brasileira",
        "ano": 1890,
        "edicao": "30ª",
        "sinopse": "Romance naturalista que retrata um cortiço carioca.",
        "quantidade_exemplares": 2,
        "localizacao": "Estante A — Prateleira 2",
    },
    {
        "titulo": "Cálculo - Volume 1",
        "autores": ["James Stewart"],
        "isbn": "9788522112586",
        "editora": "Cengage",
        "categoria": "Matemática",
        "ano": 2014,
        "edicao": "8ª",
        "sinopse": "Livro-texto fundamental para cursos de cálculo diferencial e integral.",
        "quantidade_exemplares": 4,
        "localizacao": "Estante B — Prateleira 1",
    },
    {
        "titulo": "Algoritmos: Teoria e Prática",
        "autores": ["Thomas Cormen", "Charles Leiserson", "Ronald Rivest", "Clifford Stein"],
        "isbn": "9788535236996",
        "editora": "GEN LTC",
        "categoria": "Computação",
        "ano": 2012,
        "edicao": "3ª",
        "sinopse": "Referência clássica em algoritmos e estruturas de dados.",
        "quantidade_exemplares": 3,
        "localizacao": "Estante C — Prateleira 1",
    },
    {
        "titulo": "Python Fluente",
        "autores": ["Luciano Ramalho"],
        "isbn": "9788550804651",
        "editora": "Novatec",
        "categoria": "Computação",
        "ano": 2015,
        "edicao": "1ª",
        "sinopse": "Programação Python idiomática e eficiente.",
        "quantidade_exemplares": 2,
        "localizacao": "Estante C — Prateleira 2",
    },
    {
        "titulo": "Estruturas de Dados e Algoritmos com Java",
        "autores": ["Michael Goodrich", "Roberto Tamassia"],
        "isbn": "9788582602409",
        "editora": "Bookman",
        "categoria": "Computação",
        "ano": 2013,
        "edicao": "5ª",
        "sinopse": "Estruturas de dados aplicadas com exemplos em Java.",
        "quantidade_exemplares": 2,
        "localizacao": "Estante C — Prateleira 2",
    },
    {
        "titulo": "Sapiens — Uma breve história da humanidade",
        "autores": ["Yuval Noah Harari"],
        "isbn": "9788525432186",
        "editora": "L&PM",
        "categoria": "História",
        "ano": 2015,
        "edicao": "1ª",
        "sinopse": "Panorama da história da humanidade desde os primeiros homens.",
        "quantidade_exemplares": 3,
        "localizacao": "Estante D — Prateleira 1",
    },
    {
        "titulo": "1984",
        "autores": ["George Orwell"],
        "isbn": "9788535914849",
        "editora": "Companhia das Letras",
        "categoria": "Literatura Estrangeira",
        "ano": 1949,
        "edicao": "1ª",
        "sinopse": "Romance distópico sobre vigilância e totalitarismo.",
        "quantidade_exemplares": 4,
        "localizacao": "Estante E — Prateleira 1",
    },
    {
        "titulo": "Física para Cientistas e Engenheiros",
        "autores": ["Raymond Serway", "John Jewett"],
        "isbn": "9788522112685",
        "editora": "Cengage",
        "categoria": "Física",
        "ano": 2016,
        "edicao": "2ª",
        "sinopse": "Livro-texto de física universitária com aplicações em engenharia.",
        "quantidade_exemplares": 3,
        "localizacao": "Estante B — Prateleira 2",
    },
]


def banco_vazio() -> bool:
    with db_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS qt FROM usuario")
        return cur.fetchone()["qt"] == 0


def popular_se_vazio() -> bool:
    """Popula o banco apenas se ainda não houver dados. Retorna True se populou."""
    if not banco_vazio():
        return False
    popular_dados_demo()
    return True


def popular_dados_demo() -> None:
    """Adiciona livros e usuários de demonstração ao banco.

    Usado pelo administrador a partir da tela de Configurações quando
    quiser testar o sistema. Diferente de `popular_se_vazio`, esta função
    pode ser chamada mesmo com o banco já contendo dados.
    """
    from .database import db_cursor

    # Cadastrar apenas usuários de demo que ainda não existem
    for nome, matr, perfil, senha, email, turma in USUARIOS_PADRAO:
        if matr == "admin":
            # Não recriar admin — o primeiro admin é criado no wizard
            continue
        with db_cursor() as cur:
            cur.execute("SELECT 1 FROM usuario WHERE matricula = ?", (matr,))
            if cur.fetchone():
                continue
        try:
            cadastrar_usuario(
                nome=nome, matricula=matr, perfil=perfil,
                senha=senha, email=email, turma=turma,
            )
        except Exception:
            pass

    # Cadastrar livros (não checa duplicidade — pode chamar várias vezes
    # se quiser mais dados de teste)
    for liv in LIVROS_PADRAO:
        try:
            cadastrar_livro(**liv)
        except Exception:
            pass


def main():
    from .database import init_database
    init_database()
    if popular_se_vazio():
        print("Banco populado com dados de demonstração.")
    else:
        print("Banco já contém dados — nenhum seed aplicado.")


if __name__ == "__main__":
    main()
