📦 SupriDesk — Gestão de Solicitações de Materiais

Aplicação desktop em Python para registrar, acompanhar e exportar solicitações internas de materiais (papel, periféricos, suprimentos etc.) feitas pelos setores de uma empresa.

O projeto usa apenas a biblioteca padrão do Python (tkinter, sqlite3, csv, unittest), ou seja, não precisa instalar nenhuma dependência externa.

Mostrar imagem Mostrar imagem Mostrar imagem Mostrar imagem

✨ Funcionalidades
Cadastro de solicitações com setor, material, quantidade e prioridade (Normal ou Alta).
Validação dos dados (campos obrigatórios, quantidade inteira positiva, prioridade válida).
Fluxo de status controlado: Pendente → Em atendimento → Atendida, sem pular etapas nem repetir transições.
Pesquisa por texto (setor ou material) e filtro por status.
Cores por status na tabela (amarelo, azul e verde).
Exportação para CSV (compatível com Excel), respeitando os filtros ativos.
Persistência em banco SQLite, criado automaticamente na primeira execução.
Testes automatizados das regras de negócio.
🚀 Como executar
Requisitos
Python 3.8 ou superior
Tkinter (já vem com o Python no Windows e macOS; no Linux pode ser necessário sudo apt install python3-tk)
Rodar o programa

Dentro da pasta projeto/:

bash
python main.py
Rodar os testes
bash
python -m unittest tests/teste_regras.py
🗂️ Estrutura do projeto
SupriDesk/
└── projeto/
    ├── main.py                  # Ponto de entrada da aplicação
    ├── LEIAME.txt               # Instruções rápidas de uso
    ├── solicitacoes.db          # Banco SQLite (gerado automaticamente)
    ├── supridesk/               # Pacote principal
    │   ├── __init__.py          # Marca a pasta como pacote Python
    │   ├── banco.py             # Camada de acesso a dados (SQLite)
    │   ├── regras.py            # Regras de negócio e validações
    │   └── interface.py         # Interface gráfica (Tkinter)
    └── tests/
        └── teste_regras.py      # Testes automatizados (unittest)
🧱 Arquitetura

O projeto é dividido em três camadas, cada uma com uma responsabilidade clara:

┌──────────────────────┐
│   interface.py       │  ← O que o usuário vê (Tkinter)
└──────────┬───────────┘
           │ chama
┌──────────▼───────────┐
│   regras.py          │  ← Validações e fluxo de status
└──────────┬───────────┘
           │ chama
┌──────────▼───────────┐
│   banco.py           │  ← Leitura e escrita no SQLite
└──────────────────────┘

A interface nunca acessa o banco diretamente: ela conversa apenas com o serviço de regras, que por sua vez usa o repositório. Isso facilita testar a lógica sem abrir nenhuma janela e permite trocar a interface ou o banco no futuro com pouco impacto.

📖 Explicação detalhada de cada arquivo
main.py — ponto de entrada

Monta as três camadas e inicia o programa:

python
repositorio = Repositorio()                   # cria solicitacoes.db automaticamente
servico = SupriDeskService(repositorio)       # injeta o repositório nas regras
iniciar(servico)                              # abre a janela, injetando o serviço

Esse padrão é chamado de injeção de dependência: cada camada recebe a de baixo pronta, o que torna o código simples de testar.

supridesk/__init__.py

Contém apenas uma docstring. Sua função é transformar a pasta supridesk/ em um pacote Python, permitindo imports como from supridesk.banco import Repositorio.

supridesk/banco.py — camada de dados

Define a classe Repositorio, responsável por toda a comunicação com o SQLite.

Elemento	O que faz
DB_PADRAO	Caminho padrão do banco: solicitacoes.db na raiz de projeto/.
__init__	Guarda o caminho do banco e cria a tabela se ainda não existir.
_conectar()	Abre uma conexão e configura row_factory = sqlite3.Row, permitindo acessar colunas pelo nome (registro["setor"]).
_criar_tabela()	Executa CREATE TABLE IF NOT EXISTS solicitacoes (...).
inserir(...)	Insere uma nova solicitação e retorna o id gerado.
buscar_por_id(id_)	Retorna uma solicitação específica (ou None).
atualizar_status(id_, status_esperado, novo_status)	Atualiza o status somente se o status atual for o esperado. Retorna True se alterou.
listar(texto, status)	Lista solicitações com filtros opcionais, da mais recente para a mais antiga.

Tabela solicitacoes:

Coluna	Tipo	Observação
id	INTEGER	Chave primária, autoincremento
setor	TEXT	Obrigatório
material	TEXT	Obrigatório
quantidade	INTEGER	Obrigatório, com CHECK (quantidade > 0)
prioridade	TEXT	Normal ou Alta
status	TEXT	Pendente, Em atendimento ou Atendida
data_hora	TEXT	Formato dd/mm/aaaa hh:mm:ss

Pontos importantes de design:

Consultas parametrizadas (?): todos os valores são passados separadamente do SQL, o que protege contra SQL Injection.
Escape de curingas no LIKE: os caracteres %, _ e \ digitados pelo usuário são escapados, para que sejam tratados como texto comum e não como curingas de busca.
Atualização condicional de status: o UPDATE ... WHERE id = ? AND status = ? evita condições de corrida (por exemplo, duas pessoas clicando no mesmo botão ao mesmo tempo): só uma conseguirá fazer a transição.
Gerenciamento de conexão: closing(...) fecha a conexão e o with conexao faz commit/rollback automaticamente.
supridesk/regras.py — regras de negócio

Concentra tudo o que não depende de tela nem de banco.

Constantes

PENDENTE, EM_ATENDIMENTO, ATENDIDA e a tupla STATUS.
PRIORIDADES = ("Normal", "Alta").
CABECALHO_CSV: títulos das colunas do arquivo exportado.

Exceções personalizadas

ValidacaoError: lançada quando os dados do cadastro são inválidos.
TransicaoInvalidaError: lançada quando uma mudança de status não é permitida.

Classe SupriDeskService

Método	Descrição
validar(...)	Remove espaços, verifica campos obrigatórios, garante que a quantidade seja um inteiro positivo (via regex [0-9]+, rejeitando -3, 2.5 e abc) e que a prioridade seja válida. Retorna os dados já normalizados.
cadastrar(...)	Valida, gera a data/hora atual e insere com status inicial Pendente.
iniciar_atendimento(id_)	Transição Pendente → Em atendimento.
concluir(id_)	Transição Em atendimento → Atendida.
_transicao(...)	Lógica comum às duas ações acima: confirma que a solicitação existe, que o status atual é o esperado e que a atualização no banco foi bem-sucedida.
listar(texto, status)	Normaliza os filtros (texto vazio vira None; status inválido é ignorado) e consulta o repositório.
exportar_csv(caminho, texto, status)	Exporta os registros (filtrados ou não) para CSV e retorna a quantidade de linhas.

Detalhes do CSV: usa ; como separador e codificação utf-8-sig (UTF-8 com BOM), o que faz o Excel em português abrir o arquivo corretamente, com acentos e colunas separadas.

Diagrama do fluxo de status:

 Pendente ──iniciar_atendimento──▶ Em atendimento ──concluir──▶ Atendida

Qualquer tentativa fora dessa ordem (ex.: concluir uma solicitação Pendente) gera TransicaoInvalidaError.

supridesk/interface.py — interface gráfica

Construída com Tkinter/ttk. A classe JanelaPrincipal (herda de ttk.Frame) recebe o serviço e monta toda a tela.

Métodos de construção da tela

Método	O que monta
_montar_formulario()	Bloco "Nova solicitação": campos Setor, Material, Quantidade, combo de Prioridade e botão Cadastrar.
_montar_filtros()	Bloco "Pesquisa": campo de texto (Enter também busca), combo de status, botões Buscar e Limpar filtros.
_montar_tabela()	Treeview com as 7 colunas, barra de rolagem e cores por status (
#fff4cc pendente, 
#d6e9ff em atendimento, 
#d8f5d8 atendida).
_montar_botoes()	Botões Iniciar atendimento, Concluir atendimento e Exportar CSV.

Métodos de ação

Método	O que faz
atualizar_tabela()	Limpa a tabela e a recarrega com os filtros atuais.
limpar_filtros()	Zera busca e status e recarrega.
cadastrar()	Envia os dados ao serviço; em caso de erro mostra aviso, em caso de sucesso limpa o formulário, devolve o foco ao campo Setor e atualiza a tabela.
_id_selecionado()	Retorna o ID da linha selecionada ou avisa que é preciso selecionar uma.
_executar_transicao(acao)	Executa a ação (iniciar/concluir), exibe aviso se for bloqueada, atualiza a tabela e mantém a linha selecionada.
iniciar_atendimento() / concluir()	Atalhos que chamam _executar_transicao com o método correspondente do serviço.
exportar_csv()	Abre o diálogo "Salvar como", exporta respeitando os filtros atuais e informa quantos registros foram salvos.

A função iniciar(servico) no final do arquivo cria a janela principal (tk.Tk()), define título e tamanho mínimo (760×520) e inicia o loop de eventos.

A interface não contém regra de negócio: ela só coleta dados, chama o serviço e exibe os resultados ou mensagens de erro.

tests/teste_regras.py — testes automatizados

Usa unittest. Cada teste roda com um banco temporário próprio (criado em setUp e apagado em tearDown), então os testes nunca mexem no solicitacoes.db real.

Teste	O que verifica
test_cadastro_inicia_pendente	Nova solicitação nasce como Pendente, com quantidade numérica e data/hora preenchida.
test_validacoes	Rejeita quantidade 0, -3, abc, 2.5, campos vazios ou só com espaços e prioridade inválida (Urgente); confirma que nada foi gravado.
test_fluxo_e_bloqueios	Bloqueia concluir sem iniciar, bloqueia repetir transições e confirma o status final Atendida.
test_persistencia	Os dados continuam disponíveis ao criar uma nova instância do repositório (simula reabrir o programa).
test_busca_e_filtro	Busca por texto (sem diferenciar maiúsculas/minúsculas), filtro por status e combinação dos dois.
test_sql_injection_nao_funciona	Busca com ' OR '1'='1 não retorna nada, provando que as consultas são seguras.
test_exportar_csv	Gera o CSV e confere cabeçalho, separador ; e conteúdo da linha.
solicitacoes.db

Arquivo do banco SQLite. É criado automaticamente na primeira execução. Contém os dados reais usados pela aplicação.

LEIAME.txt

Resumo curto, em texto simples, de como executar o programa e os testes.

🔒 Boas práticas aplicadas
Separação em camadas (interface / regras / dados).
Consultas SQL parametrizadas (proteção contra SQL Injection).
Validação centralizada, independente da interface.
Restrição CHECK no banco como segunda linha de defesa para a quantidade.
Transição de status atômica, evitando inconsistências.
Exceções próprias para tratar erros de forma clara.
Testes isolados com banco temporário.
🛣️ Ideias para evoluir o projeto
Editar e cancelar solicitações.
Registro de quem solicitou e de quem atendeu.
Relatórios e gráficos por setor ou período.
Ordenação por prioridade na tabela.
Controle de estoque integrado.
Empacotar como executável (.exe) com PyInstaller.
📌 Dica para o repositório

Crie um arquivo .gitignore na raiz para não versionar arquivos gerados automaticamente:

gitignore
__pycache__/
*.pyc
*.db
📄 Licença

Defina aqui a licença do projeto (por exemplo, MIT).
