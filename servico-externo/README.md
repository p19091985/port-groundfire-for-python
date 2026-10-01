# Serviço externo Groundfire

**Estado em 26/09/2026: implementação funcional em validação.** A API FastAPI, SQLite, runtime headless empacotado, supervisor de partidas, launcher e adapters Python/Godot existem. A homologação Linux/web, carga, implantação pública, administração completa e jornadas sociais nas duas interfaces continuam abertas no [registro da migração](../docs/godot_migration_strategy.md#projeto-encerramento-pendencias).

O pacote foi preparado para rodar com **somente** `servico-externo/` copiado para outra máquina, sem as pastas irmãs do repositório. Ele oferece identidade/convidado, presença, amigos, grupos, convites, salas, fila e reserva, eventos/chat e partida hospedada com ingresso de uso único. O cliente Python usa [`service_client.py`](../versao-python/src/groundfire/service_client.py); o Godot usa [`scripts/online/`](../versao-godot/godot/scripts/online/). O servidor LAN/direto permanece independente deste produto.

## Documentos do projeto

| Documento | Conteúdo |
|---|---|
| [PROJETO.md](PROJETO.md) | Requisitos SE01–SE12 e arquitetura alvo; a auditoria inicial é um retrato anterior ao código. |
| [CONTRATOS.md](CONTRATOS.md) | Contrato alvo de HTTP/WS/UDP, inclusive recursos ainda não implementados; conferir a API executável em `/docs`. |
| [IMPLEMENTACAO-E-TESTES.md](IMPLEMENTACAO-E-TESTES.md) | Lotes E01–E09 e matriz de aceite; distingue evidências já obtidas dos gates restantes. |

O [projeto integrado de encerramento das pendências](../docs/godot_migration_strategy.md#projeto-encerramento-pendencias) relaciona esses lotes à fidelidade Python/Godot, às telas dos dois clientes e à homologação dos pacotes. O serviço continua sendo um produto instalado independentemente; esse vínculo é documental, não uma dependência de runtime.

## Inicialização

Dentro da pasta do sistema:

```sh
cd servico-externo
sh servico-externo.sh
```

A partir da raiz do repositório, o mesmo launcher será acessível por:

```sh
sh servico-externo/servico-externo.sh
```

`servico-externo.sh` fica **dentro de `servico-externo/`**. Ele cria `.venv` e instala as dependências na primeira execução; a instalação inicial requer acesso ao índice de pacotes ou dependências já disponíveis. O comando `check` verifica hashes do runtime e inicializa o banco; `test` instala as dependências de teste e executa a suíte da pasta. `start` verifica o runtime, inicia a API e encerra os workers criados por esta instância ao terminar.

No Windows, use o launcher nativo, sem Git Bash ou WSL:

```powershell
cd servico-externo
.\servico-externo.bat
# Ou, para verificar o pacote sem iniciar a API:
.\servico-externo.bat check
```

O `.bat` chama `servico-externo.ps1` da mesma pasta. Ele usa Python 3.11–3.14 (o serviço importa `tomllib`), cria `.venv` local e instala as dependências na primeira execução. Se necessário, defina `GF_SERVICE_PYTHON` com o caminho do executável Python, sem argumentos. As execuções seguintes reutilizam o ambiente. Uma `.venv` de Linux/WSL não é reutilizável pelo Windows; o launcher informa o problema sem apagar a pasta. A política de execução do PowerShell é ajustada apenas para o processo iniciado pelo `.bat`.

Todos os comandos da tabela também funcionam substituindo `sh servico-externo.sh` por `.\servico-externo.bat`: `start`, `check`, `status`, `stop`, `backup`, `restore --file "CAMINHO"` e `test`. Para iniciar a partir da raiz do repositório: `.\servico-externo\servico-externo.bat`. Sem argumentos, inicia a API local; use outro terminal para `status` ou `stop`.

## Console gráfico local

No Windows, execute `servico-externo.bat gui` dentro desta pasta. Em Linux/macOS, execute `sh servico-externo.sh gui`. O comando inicia o serviço, se necessário, e abre o console no navegador. Se o serviço já estiver ativo, abre a instância existente. Mantenha o terminal aberto enquanto o serviço estiver em execução.

O painel mostra jogadores online, fila, salas, partidas, workers e eventos recentes. Em **Operações**, é possível criar um backup verificado do SQLite ou parar a instância. As telas se atualizam a cada cinco segundos e também têm atualização manual. O console está disponível somente quando `[service].bind` aponta para a máquina local; ele exige a chave temporária do processo, entregue pelo comando `gui` no fragmento da URL e removida da barra de endereços após a abertura. Não compartilhe a URL de abertura. Nenhum recurso externo de fonte, script ou imagem é necessário.

**Validação do launcher Windows em 30/09/2026:** criação da `.venv` e instalação em cópia isolada com espaço/acento, `check`, início da API, `/readyz`, `status`, parada autenticada com limpeza do PID e cinco testes de jornada da API via `test` aprovados. O manifesto desatualizado foi recalculado para os arquivos vendorizados existentes; `.gitattributes` e o gerador preservam LF para manter os hashes entre sistemas. A verificação SHA-256 continua obrigatória. Esse ensaio não certifica implantação pública ou todas as jornadas do serviço.

| Comando | Uso |
|---|---|
| `sh servico-externo.sh` ou `sh servico-externo.sh start` | Inicia API local em `127.0.0.1:27880` por padrão. |
| `sh servico-externo.sh gui` | Inicia ou abre o serviço com o console gráfico no navegador local. |
| `sh servico-externo.sh check` / `status` | Verifica pacote/banco ou consulta `/readyz` do processo ativo. |
| `sh servico-externo.sh stop` | Solicita parada autenticada da instância registrada. |
| `sh servico-externo.sh backup` | Cria backup SQLite com manifesto SHA-256 em `backups/`. |
| `sh servico-externo.sh restore --file CAMINHO` | Restaura backup verificado com serviço parado. |
| `sh servico-externo.sh test` | Executa `pytest` no pacote isolado. |

Com o serviço ativo, verifique `http://127.0.0.1:27880/readyz` e explore as rotas atuais em `http://127.0.0.1:27880/docs`. A configuração opcional é um `config.toml` na pasta do serviço, ou arquivo indicado por `GF_SERVICE_CONFIG`. As chaves `[service]`, `[storage]`, `[identity]`, `[social]` e `[matches]` e seus defaults estão em [`src/gf_service/config.py`](src/gf_service/config.py). Não confunda a porta HTTP `27880` com as portas dinâmicas dos workers.

O perfil padrão é local e não exige Steam, GitHub, banco remoto, Docker, domínio ou serviço pago. Publicação na Internet requer endereço público, HTTPS/WSS, origem permitida, portas dos workers e ensaio de implantação; o pacote ainda não inclui essa homologação. O jogo LAN continua utilizável sem o serviço externo.

**Validação em 26/09/2026:** suíte do serviço aprovada com partida autoritativa real, ingresso WebSocket autenticado de uso único, cópia isolada em caminho Windows com espaço/acento e encerramento coordenado. Consulte o [registro P00–P08](../docs/godot_migration_strategy.md#registro-implementacao-2026-09-26) para os limites da validação.
