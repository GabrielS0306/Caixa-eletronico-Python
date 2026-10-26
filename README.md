# Caixa Eletrônico em Python

Projeto de estudo desenvolvido em Python para praticar os fundamentos da linguagem por meio da simulação de um caixa eletrônico no terminal.

## Funcionalidades

* Várias contas, cada uma com número próprio (a partir de 1001), titular e PIN
* Abertura de conta pelo menu inicial
* Acesso protegido por PIN de 4 a 6 dígitos, com bloqueio após 3 tentativas incorretas
* Alteração de PIN pelo menu
* Depósitos, saques e transferências entre contas, com validação de valores
* Bloqueio de saques e transferências com saldo insuficiente
* Saque em cédulas de R$ 200, 100, 50, 20 e 10, com o menor número de notas possível
* Consulta de saldo
* Histórico de transações com data e hora
* Extrato por período, com exportação para CSV pronto para abrir no Excel
* Relatório da conta (totais e quantidades de depósitos, saques e transferências)
* Dados salvos em um banco SQLite (`banco.db`), com cada operação gravada por inteiro ou não gravada
* Arquivos de dados corrompidos são guardados como cópia, nunca sobrescritos
* Valores monetários calculados com `Decimal`, sem erros de arredondamento
* Valores exibidos no formato brasileiro (`R$ 1.234,56`)

## Tecnologias

* Python 3.11 ou superior (somente a biblioteca padrão)
* SQLite, pelo módulo `sqlite3` que já vem com o Python

## Estrutura do projeto

```text
caixa_eletronico/
├── main.py                     # Ponto de entrada do programa
├── caixa_eletronico/           # Pacote com o código da aplicação
│   ├── formatacao.py           # Formatação de valores em reais e datas
│   ├── nucleo/                 # Regras de negócio
│   │   ├── banco.py            # Classe Banco: abertura e busca de contas
│   │   ├── conta_bancaria.py   # Classe ContaBancaria: depósitos, saques e transferências
│   │   ├── cedulas.py          # Cálculo das cédulas entregues no saque
│   │   ├── extrato.py          # Filtro de transações por período
│   │   └── seguranca.py        # PIN: validação e hash com PBKDF2
│   ├── armazenamento/          # Leitura e gravação dos dados
│   │   ├── persistencia.py     # Leitura e gravação no banco SQLite
│   │   ├── formato_json.py     # Importação do dados.json de versões anteriores
│   │   └── exportacao.py       # Exportação do extrato para CSV
│   └── interface/              # Interação com o usuário no terminal
│       ├── menu.py             # Menu, PIN e leitura de valores
│       ├── historico.py        # Exibição do histórico de transações
│       └── relatorio.py        # Cálculo e exibição do relatório da conta
├── tests/                      # Testes automatizados (unittest)
├── banco.db                    # Banco SQLite criado ao usar o programa (fora do Git)
├── extratos/                   # CSVs exportados (fora do Git)
├── README.md
└── .gitignore
```

As camadas dependem apenas "para dentro": `interface` usa `armazenamento` e `nucleo`, `armazenamento` usa `nucleo`, e `nucleo` não conhece as outras duas.

## Como executar

1. Clone o repositório:

   ```bash
   git clone https://github.com/GabrielS0306/Caixa-eletronico-Python.git
   ```

2. Entre na pasta:

   ```bash
   cd Caixa-eletronico-Python
   ```

3. Execute o programa:

   ```bash
   python main.py
   ```

## Como rodar os testes

Na raiz do projeto:

```bash
python -m unittest
```

## Objetivo

Praticar funções, classes, módulos, exceções, condicionais, laços de repetição, persistência com SQLite e testes automatizados.

## Observação

Este projeto tem finalidade educacional. O arquivo `banco.db` é criado automaticamente na primeira operação e não é versionado no Git.

O banco tem duas tabelas: `contas` e `transacoes`. Os valores em dinheiro são guardados em centavos (`1050` = R$ 10,50), e cada operação é gravada numa transação do SQLite: ou tudo é salvo, ou nada é.

O PIN é salvo apenas como hash (PBKDF2 com salt aleatório), nunca em texto puro. Ao abrir uma conta, o programa pede o nome do titular e um PIN, e informa o número da nova conta.

Na primeira execução, o `dados.json` de versões anteriores é importado para o `banco.db` e guardado como `dados.json.migrado`. Se ele tiver uma única conta (formato mais antigo), ela passa a ser a de número 1001, mantendo saldo, histórico e PIN.

Se o `banco.db` (ou o `dados.json` a importar) estiver corrompido, ele é renomeado para `*.corrompido-<data-hora>` e o caixa começa sem contas. Se o arquivo existir mas não puder ser aberto (por exemplo, em uso por outro programa), o caixa não inicia, para não arriscar perder dados.

Por padrão, o PIN não aparece enquanto é digitado. No terminal integrado do VS Code no Windows, onde a leitura escondida não funciona, o PIN fica visível e o programa avisa isso. Para escondê-lo, execute em um PowerShell ou Windows Terminal fora do VS Code.

Para desbloquear uma conta durante os estudos (troque `1001` pelo número da conta):

```bash
python -c "import sqlite3; c = sqlite3.connect('banco.db'); c.execute('UPDATE contas SET tentativas_falhas = 0 WHERE numero = ?', ('1001',)); c.commit()"
```

Para cadastrar um novo PIN no próximo acesso, use `UPDATE contas SET pin_salt = NULL, pin_hash = NULL WHERE numero = ?` no mesmo comando. Também é possível abrir o `banco.db` com o [DB Browser for SQLite](https://sqlitebrowser.org/).

## Autor

Gabriel.S
