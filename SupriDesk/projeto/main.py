from supridesk.banco import Repositorio
from supridesk.regras import SupriDeskService
from supridesk.interface import iniciar


def main():
    repositorio = Repositorio()          # cria solicitacoes.db automaticamente
    servico = SupriDeskService(repositorio)
    iniciar(servico)


if __name__ == "__main__":
    main()
