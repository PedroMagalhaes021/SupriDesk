import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from .regras import (PRIORIDADES, STATUS, ValidacaoError,
                     TransicaoInvalidaError, PENDENTE, EM_ATENDIMENTO, ATENDIDA)

TODOS = "Todos"


class JanelaPrincipal(ttk.Frame):
    def __init__(self, master, servico):
        super().__init__(master, padding=10)
        self.servico = servico
        self.pack(fill="both", expand=True)
        self._montar_formulario()
        self._montar_filtros()
        self._montar_tabela()
        self._montar_botoes()
        self.atualizar_tabela()

    # ---------- construção ----------
    def _montar_formulario(self):
        quadro = ttk.LabelFrame(self, text="Nova solicitação", padding=10)
        quadro.pack(fill="x")

        self.var_setor = tk.StringVar()
        self.var_material = tk.StringVar()
        self.var_quantidade = tk.StringVar()
        self.var_prioridade = tk.StringVar(value=PRIORIDADES[0])

        ttk.Label(quadro, text="Setor:").grid(row=0, column=0, sticky="w")
        self.ent_setor = ttk.Entry(quadro, textvariable=self.var_setor, width=22)
        self.ent_setor.grid(row=0, column=1, padx=5, pady=3)

        ttk.Label(quadro, text="Material:").grid(row=0, column=2, sticky="w")
        ttk.Entry(quadro, textvariable=self.var_material, width=26).grid(
            row=0, column=3, padx=5, pady=3)

        ttk.Label(quadro, text="Quantidade:").grid(row=1, column=0, sticky="w")
        ttk.Entry(quadro, textvariable=self.var_quantidade, width=10).grid(
            row=1, column=1, padx=5, pady=3, sticky="w")

        ttk.Label(quadro, text="Prioridade:").grid(row=1, column=2, sticky="w")
        ttk.Combobox(quadro, textvariable=self.var_prioridade, values=PRIORIDADES,
                     state="readonly", width=12).grid(
            row=1, column=3, padx=5, pady=3, sticky="w")

        ttk.Button(quadro, text="Cadastrar", command=self.cadastrar).grid(
            row=0, column=4, rowspan=2, padx=10, ipadx=8, ipady=6)

    def _montar_filtros(self):
        quadro = ttk.LabelFrame(self, text="Pesquisa", padding=10)
        quadro.pack(fill="x", pady=8)

        self.var_busca = tk.StringVar()
        self.var_filtro_status = tk.StringVar(value=TODOS)

        ttk.Label(quadro, text="Setor ou Material:").pack(side="left")
        entrada = ttk.Entry(quadro, textvariable=self.var_busca, width=25)
        entrada.pack(side="left", padx=5)
        entrada.bind("<Return>", lambda _e: self.atualizar_tabela())

        ttk.Label(quadro, text="Status:").pack(side="left", padx=(10, 0))
        combo = ttk.Combobox(quadro, textvariable=self.var_filtro_status,
                             values=(TODOS,) + STATUS, state="readonly", width=16)
        combo.pack(side="left", padx=5)
        combo.bind("<<ComboboxSelected>>", lambda _e: self.atualizar_tabela())

        ttk.Button(quadro, text="Buscar", command=self.atualizar_tabela).pack(
            side="left", padx=5)
        ttk.Button(quadro, text="Limpar filtros", command=self.limpar_filtros).pack(
            side="left")

    def _montar_tabela(self):
        quadro = ttk.Frame(self)
        quadro.pack(fill="both", expand=True)

        colunas = ("id", "setor", "material", "quantidade",
                   "prioridade", "status", "data_hora")
        titulos = ("ID", "Setor", "Material", "Qtd.", "Prioridade", "Status", "Data/Hora")
        larguras = (50, 130, 200, 60, 90, 120, 150)

        self.tabela = ttk.Treeview(quadro, columns=colunas, show="headings",
                                   selectmode="browse", height=12)
        for col, titulo, largura in zip(colunas, titulos, larguras):
            self.tabela.heading(col, text=titulo)
            self.tabela.column(col, width=largura,
                               anchor="center" if col in ("id", "quantidade") else "w")

        self.tabela.tag_configure(PENDENTE, background="#fff4cc")
        self.tabela.tag_configure(EM_ATENDIMENTO, background="#d6e9ff")
        self.tabela.tag_configure(ATENDIDA, background="#d8f5d8")

        barra = ttk.Scrollbar(quadro, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=barra.set)
        self.tabela.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

    def _montar_botoes(self):
        quadro = ttk.Frame(self)
        quadro.pack(fill="x", pady=(8, 0))
        ttk.Button(quadro, text="Iniciar atendimento",
                   command=self.iniciar_atendimento).pack(side="left", padx=(0, 5))
        ttk.Button(quadro, text="Concluir atendimento",
                   command=self.concluir).pack(side="left", padx=5)
        ttk.Button(quadro, text="Exportar CSV",
                   command=self.exportar_csv).pack(side="right")

    # ---------- ações ----------
    def atualizar_tabela(self):
        self.tabela.delete(*self.tabela.get_children())
        status = self.var_filtro_status.get()
        registros = self.servico.listar(
            self.var_busca.get(), None if status == TODOS else status)
        for r in registros:
            self.tabela.insert("", "end", iid=str(r["id"]), tags=(r["status"],),
                               values=(r["id"], r["setor"], r["material"],
                                       r["quantidade"], r["prioridade"],
                                       r["status"], r["data_hora"]))

    def limpar_filtros(self):
        self.var_busca.set("")
        self.var_filtro_status.set(TODOS)
        self.atualizar_tabela()

    def cadastrar(self):
        try:
            self.servico.cadastrar(self.var_setor.get(), self.var_material.get(),
                                   self.var_quantidade.get(), self.var_prioridade.get())
        except ValidacaoError as erro:
            messagebox.showwarning("Dados inválidos", str(erro))
            return
        self.var_setor.set("")
        self.var_material.set("")
        self.var_quantidade.set("")
        self.var_prioridade.set(PRIORIDADES[0])
        self.ent_setor.focus_set()
        self.atualizar_tabela()
        messagebox.showinfo("Sucesso", "Solicitação cadastrada com status Pendente.")

    def _id_selecionado(self):
        selecao = self.tabela.selection()
        if not selecao:
            messagebox.showinfo("Seleção", "Selecione uma solicitação na tabela.")
            return None
        return int(selecao[0])

    def _executar_transicao(self, acao):
        id_ = self._id_selecionado()
        if id_ is None:
            return
        try:
            acao(id_)
        except TransicaoInvalidaError as erro:
            messagebox.showwarning("Operação bloqueada", str(erro))
        self.atualizar_tabela()
        if self.tabela.exists(str(id_)):
            self.tabela.selection_set(str(id_))

    def iniciar_atendimento(self):
        self._executar_transicao(self.servico.iniciar_atendimento)

    def concluir(self):
        self._executar_transicao(self.servico.concluir)

    def exportar_csv(self):
        caminho = filedialog.asksaveasfilename(
            title="Exportar histórico", defaultextension=".csv",
            initialfile="historico_solicitacoes.csv",
            filetypes=[("Arquivo CSV", "*.csv")])
        if not caminho:
            return
        try:
            status = self.var_filtro_status.get()
            total = self.servico.exportar_csv(
                caminho, self.var_busca.get(), None if status == TODOS else status)
        except OSError as erro:
            messagebox.showerror("Erro", f"Não foi possível salvar o arquivo:\n{erro}")
            return
        messagebox.showinfo("Exportação concluída",
                            f"{total} registro(s) exportado(s) para:\n{caminho}")


def iniciar(servico):
    raiz = tk.Tk()
    raiz.title("SupriDesk - Gestão de Solicitações de Materiais")
    raiz.minsize(760, 520)
    JanelaPrincipal(raiz, servico)
    raiz.mainloop()