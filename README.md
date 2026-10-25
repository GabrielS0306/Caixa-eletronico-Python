# Caixa Eletrônico em Python

Projeto de estudo desenvolvido em Python para praticar os fundamentos da linguagem por meio da simulação de um caixa eletrônico no terminal.

## Funcionalidades

* Acesso protegido por PIN de 4 a 6 dígitos, com bloqueio após 3 tentativas incorretas
* Alteração de PIN pelo menu
* Depósitos e saques com validação de valores
* Bloqueio de saques com saldo insuficiente
* Saque em cédulas de R$ 200, 100, 50, 20 e 10, com o menor número de notas possível
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
├── main.py                     # Ponto de entrada do programa
├── caixa_eletronico/           # Pacote com o código da aplicação
│   ├── formatacao.py           # Formatação de valores em reais e datas
│   ├── nucleo/                 # Regras de negócio
│   │   ├── conta_bancaria.py   # Classe ContaBancaria, depósitos e saques
│   │   ├── cedulas.py          # Cálculo das cédulas entregues no saque
│   │   └── seguranca.py        # PIN: validação e hash com PBKDF2
│   ├── armazenamento/          # Leitura e gravação dos dados
│   │   └── persistencia.py     # Conversão da conta para o dados.json
│   └── interface/              # Interação com o usuário no terminal
│       ├── menu.py             # Menu, PIN e leitura de valores
│       ├── historico.py        # Exibição do histórico de transações
│       └── relatorio.py        # Cálculo e exibição do relatório da conta
├── tests/                      # Testes automatizados (unittest)
├── dados.json                  # Criado ao usar o programa (fora do Git)
├── README.md
└── .gitignore
```

As camadas dependem apenas "para dentro": `interface` usa `armazenamento` e `nucleo`, `armazenamento` usa `nucleo`, e `nucleo` não conhece as outras duas.

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
   python main.py
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

O PIN é salvo apenas como hash (PBKDF2 com salt aleatório), nunca em texto puro. Na primeira execução, o programa pede para cadastrar um PIN.

Por padrão, o PIN não aparece enquanto é digitado. No terminal integrado do VS Code no Windows, onde a leitura escondida não funciona, o PIN fica visível e o programa avisa isso. Para escondê-lo, execute em um PowerShell ou Windows Terminal fora do VS Code.

Para desbloquear a conta durante os estudos, altere `"tentativas_falhas"` para `0` no `dados.json`. Para cadastrar um novo PIN, troque a seção `"seguranca"` por `null`.

## Autor

Gabriel
