# Caixa Eletrônico em Python

Projeto de estudo desenvolvido em Python para praticar os fundamentos da linguagem por meio da simulação de um caixa eletrônico no terminal.

## Funcionalidades

* Depósitos e saques com validação de valores
* Bloqueio de saques com saldo insuficiente
* Consulta de saldo
* Histórico de transações com data e hora
* Relatório da conta (totais e quantidades de depósitos e saques)
* Dados salvos em `dados.json` entre execuções
* Valores monetários calculados com `Decimal`, sem erros de arredondamento
* Valores exibidos no formato brasileiro (`R$ 1.234,56`)

## Tecnologias

* Python 3 (somente a biblioteca padrão)

## Estrutura do projeto

```text
caixa_eletronico/
├── caixa.py            # Menu interativo e leitura de valores
├── conta_bancaria.py   # Classe ContaBancaria e regras de negócio
├── historico.py        # Exibição do histórico de transações
├── relatorio.py        # Cálculo e exibição do relatório da conta
├── persistencia.py     # Leitura e gravação do dados.json
├── formatacao.py       # Formatação de valores em reais
├── tests/              # Testes automatizados (unittest)
├── README.md
└── .gitignore
```

## Como executar

1. Clone o repositório:

   ```bash
   git clone URL_DO_SEU_REPOSITORIO
   ```

2. Entre na pasta:

   ```bash
   cd caixa_eletronico
   ```

3. Execute o programa:

   ```bash
   python caixa.py
   ```

## Como rodar os testes

Na raiz do projeto:

```bash
python -m unittest
```

## Objetivo

Praticar funções, classes, módulos, exceções, condicionais, laços de repetição, persistência em arquivo e testes automatizados.

## Observação

Este projeto tem finalidade educacional. O arquivo `dados.json` é criado automaticamente na primeira operação e não é versionado no Git.

## Autor

Gabriel
