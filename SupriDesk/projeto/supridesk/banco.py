import sqlite3
from contextlib import closing
from pathlib import Path

DB_PADRAO = Path(__file__).resolve().parent.parent / "solicitacoes.db"


class Repositorio:
    def __init__(self, caminho=DB_PADRAO):
        self.caminho = str(caminho)
        self._criar_tabela()

    def _conectar(self):
        conexao = sqlite3.connect(self.caminho)
        conexao.row_factory = sqlite3.Row
        return conexao

    def _criar_tabela(self):
        with closing(self._conectar()) as conexao, conexao:
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS solicitacoes (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    setor      TEXT    NOT NULL,
                    material   TEXT    NOT NULL,
                    quantidade INTEGER NOT NULL CHECK (quantidade > 0),
                    prioridade TEXT    NOT NULL,
                    status     TEXT    NOT NULL,
                    data_hora  TEXT    NOT NULL
                )
                """
            )

    def inserir(self, setor, material, quantidade, prioridade, status, data_hora):
        with closing(self._conectar()) as conexao, conexao:
            cursor = conexao.execute(
                "INSERT INTO solicitacoes "
                "(setor, material, quantidade, prioridade, status, data_hora) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (setor, material, quantidade, prioridade, status, data_hora),
            )
            return cursor.lastrowid

    def buscar_por_id(self, id_):
        with closing(self._conectar()) as conexao:
            return conexao.execute(
                "SELECT * FROM solicitacoes WHERE id = ?", (id_,)
            ).fetchone()

    def atualizar_status(self, id_, status_esperado, novo_status):
        """Atualiza apenas se o status atual for o esperado.

        Retorna True se a linha foi alterada (garante que a transição
        não seja repetida nem aplicada sobre um status inesperado).
        """
        with closing(self._conectar()) as conexao, conexao:
            cursor = conexao.execute(
                "UPDATE solicitacoes SET status = ? WHERE id = ? AND status = ?",
                (novo_status, id_, status_esperado),
            )
            return cursor.rowcount == 1

    def listar(self, texto=None, status=None):
        sql = "SELECT * FROM solicitacoes WHERE 1 = 1"
        parametros = []
        if texto:
            sql += (" AND (setor LIKE ? ESCAPE '\\' "
                    "OR material LIKE ? ESCAPE '\\')")
            escapado = (texto.replace("\\", "\\\\")
                             .replace("%", "\\%").replace("_", "\\_"))
            padrao = f"%{escapado}%"
            parametros += [padrao, padrao]
        if status:
            sql += " AND status = ?"
            parametros.append(status)
        sql += " ORDER BY id DESC"
        with closing(self._conectar()) as conexao:
            return conexao.execute(sql, parametros).fetchall()