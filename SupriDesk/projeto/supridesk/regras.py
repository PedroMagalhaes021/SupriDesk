import csv
import re
from datetime import datetime

PENDENTE = "Pendente"
EM_ATENDIMENTO = "Em atendimento"
ATENDIDA = "Atendida"
STATUS = (PENDENTE, EM_ATENDIMENTO, ATENDIDA)
PRIORIDADES = ("Normal", "Alta")

CABECALHO_CSV = ["ID", "Setor", "Material", "Quantidade",
                 "Prioridade", "Status", "Data/Hora"]


class ValidacaoError(Exception):
    """Dados de cadastro inválidos."""


class TransicaoInvalidaError(Exception):
    """Mudança de status não permitida."""


class SupriDeskService:
    def __init__(self, repositorio):
        self.repositorio = repositorio

    # ---------- cadastro ----------
    @staticmethod
    def validar(setor, material, quantidade, prioridade):
        setor = (setor or "").strip()
        material = (material or "").strip()
        quantidade = str(quantidade if quantidade is not None else "").strip()
        prioridade = (prioridade or "").strip()

        if not setor:
            raise ValidacaoError("O campo Setor é obrigatório.")
        if not material:
            raise ValidacaoError("O campo Material é obrigatório.")
        if not quantidade:
            raise ValidacaoError("O campo Quantidade é obrigatório.")
        if not prioridade:
            raise ValidacaoError("O campo Prioridade é obrigatório.")
        if not re.fullmatch(r"[0-9]+", quantidade) or int(quantidade) <= 0:
            raise ValidacaoError("A quantidade deve ser um número inteiro positivo.")
        if prioridade not in PRIORIDADES:
            raise ValidacaoError("Prioridade deve ser Normal ou Alta.")
        return setor, material, int(quantidade), prioridade

    def cadastrar(self, setor, material, quantidade, prioridade):
        setor, material, quantidade, prioridade = self.validar(
            setor, material, quantidade, prioridade
        )
        data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        return self.repositorio.inserir(
            setor, material, quantidade, prioridade, PENDENTE, data_hora
        )

    # ---------- fluxo de atendimento ----------
    def iniciar_atendimento(self, id_):
        self._transicao(id_, PENDENTE, EM_ATENDIMENTO,
                        "Só é possível iniciar o atendimento de solicitações Pendentes.")

    def concluir(self, id_):
        self._transicao(id_, EM_ATENDIMENTO, ATENDIDA,
                        "Só é possível concluir solicitações Em atendimento.")

    def _transicao(self, id_, de, para, mensagem):
        registro = self.repositorio.buscar_por_id(id_)
        if registro is None:
            raise TransicaoInvalidaError("Solicitação não encontrada.")
        if registro["status"] != de:
            raise TransicaoInvalidaError(
                f"{mensagem} Status atual: {registro['status']}."
            )
        if not self.repositorio.atualizar_status(id_, de, para):
            raise TransicaoInvalidaError("O status mudou durante a operação. Atualize a tabela.")

    # ---------- consulta ----------
    def listar(self, texto=None, status=None):
        texto = (texto or "").strip() or None
        status = status if status in STATUS else None
        return self.repositorio.listar(texto, status)

    # ---------- CSV ----------
    def exportar_csv(self, caminho, texto=None, status=None):
        """Exporta o histórico (respeitando filtros, se informados). Retorna nº de linhas."""
        registros = self.listar(texto, status)
        with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
            escritor = csv.writer(arquivo, delimiter=";")
            escritor.writerow(CABECALHO_CSV)
            for r in registros:
                escritor.writerow([r["id"], r["setor"], r["material"],
                                   r["quantidade"], r["prioridade"],
                                   r["status"], r["data_hora"]])
        return len(registros)