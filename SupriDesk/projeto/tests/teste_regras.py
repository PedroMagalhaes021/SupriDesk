import csv
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supridesk.banco import Repositorio
from supridesk.regras import (SupriDeskService, ValidacaoError,
                              TransicaoInvalidaError, PENDENTE,
                              EM_ATENDIMENTO, ATENDIDA)


class TestSupriDesk(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.pasta.name, "teste.db")
        self.servico = SupriDeskService(Repositorio(self.db))

    def tearDown(self):
        self.pasta.cleanup()

    def test_cadastro_inicia_pendente(self):
        id_ = self.servico.cadastrar("TI", "Mouse USB", "5", "Alta")
        r = self.servico.repositorio.buscar_por_id(id_)
        self.assertEqual(r["status"], PENDENTE)
        self.assertEqual(r["quantidade"], 5)
        self.assertTrue(r["data_hora"])

    def test_validacoes(self):
        casos = [("Administrativo", "Papel A4", "0", "Normal"),
                 ("Administrativo", "Papel A4", "-3", "Normal"),
                 ("Administrativo", "Papel A4", "abc", "Normal"),
                 ("Administrativo", "Papel A4", "2.5", "Normal"),
                 ("", "Papel A4", "1", "Normal"),
                 ("TI", "   ", "1", "Normal"),
                 ("TI", "Cabo", "", "Normal"),
                 ("TI", "Cabo", "1", "Urgente")]
        for caso in casos:
            with self.assertRaises(ValidacaoError, msg=str(caso)):
                self.servico.cadastrar(*caso)
        self.assertEqual(self.servico.listar(), [])

    def test_fluxo_e_bloqueios(self):
        id_ = self.servico.cadastrar("TI", "Mouse USB", "5", "Alta")
        with self.assertRaises(TransicaoInvalidaError):
            self.servico.concluir(id_)          # pulou etapa
        self.servico.iniciar_atendimento(id_)
        with self.assertRaises(TransicaoInvalidaError):
            self.servico.iniciar_atendimento(id_)  # repetida
        self.servico.concluir(id_)
        with self.assertRaises(TransicaoInvalidaError):
            self.servico.concluir(id_)          # repetida
        self.assertEqual(self.servico.repositorio.buscar_por_id(id_)["status"], ATENDIDA)

    def test_persistencia(self):
        self.servico.cadastrar("TI", "Mouse USB", "5", "Alta")
        novo = SupriDeskService(Repositorio(self.db))
        self.assertEqual(len(novo.listar()), 1)

    def test_busca_e_filtro(self):
        a = self.servico.cadastrar("TI", "Mouse USB", "5", "Alta")
        self.servico.cadastrar("Administrativo", "Papel A4", "10", "Normal")
        self.assertEqual(len(self.servico.listar("mouse")), 1)
        self.assertEqual(len(self.servico.listar("Admin")), 1)
        self.servico.iniciar_atendimento(a)
        self.servico.concluir(a)
        self.assertEqual(len(self.servico.listar(status=ATENDIDA)), 1)
        self.assertEqual(len(self.servico.listar(status=EM_ATENDIMENTO)), 0)
        self.assertEqual(len(self.servico.listar("Papel", ATENDIDA)), 0)

    def test_sql_injection_nao_funciona(self):
        self.servico.cadastrar("TI", "Mouse USB", "5", "Alta")
        self.assertEqual(self.servico.listar("' OR '1'='1"), [])

    def test_exportar_csv(self):
        self.servico.cadastrar("TI", "Mouse USB", "5", "Alta")
        caminho = os.path.join(self.pasta.name, "saida.csv")
        self.assertEqual(self.servico.exportar_csv(caminho), 1)
        with open(caminho, newline="", encoding="utf-8-sig") as f:
            linhas = list(csv.reader(f, delimiter=";"))
        self.assertEqual(linhas[0], ["ID", "Setor", "Material", "Quantidade",
                                     "Prioridade", "Status", "Data/Hora"])
        self.assertEqual(linhas[1][1:6], ["TI", "Mouse USB", "5", "Alta", "Pendente"])


if __name__ == "__main__":
    unittest.main()