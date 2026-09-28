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

No Windows, use Git Bash ou WSL para executar o comando `sh`; PowerShell sem um ambiente POSIX não fornece esse executável.

| Comando | Uso |
|---|---|
| `sh servico-externo.sh` ou `sh servico-externo.sh start` | Inicia API local em `127.0.0.1:27880` por padrão. |
| `sh servico-externo.sh check` / `status` | Verifica pacote/banco ou consulta `/readyz` do processo ativo. |
| `sh servico-externo.sh stop` | Solicita parada autenticada da instância registrada. |
| `sh servico-externo.sh backup` | Cria backup SQLite com manifesto SHA-256 em `backups/`. |
| `sh servico-externo.sh restore --file CAMINHO` | Restaura backup verificado com serviço parado. |
| `sh servico-externo.sh test` | Executa `pytest` no pacote isolado. |

Com o serviço ativo, verifique `http://127.0.0.1:27880/readyz` e explore as rotas atuais em `http://127.0.0.1:27880/docs`. A configuração opcional é um `config.toml` na pasta do serviço, ou arquivo indicado por `GF_SERVICE_CONFIG`. As chaves `[service]`, `[storage]`, `[identity]`, `[social]` e `[matches]` e seus defaults estão em [`src/gf_service/config.py`](src/gf_service/config.py). Não confunda a porta HTTP `27880` com as portas dinâmicas dos workers.

O perfil padrão é local e não exige Steam, GitHub, banco remoto, Docker, domínio ou serviço pago. Publicação na Internet requer endereço público, HTTPS/WSS, origem permitida, portas dos workers e ensaio de implantação; o pacote ainda não inclui essa homologação. O jogo LAN continua utilizável sem o serviço externo.

**Validação em 26/09/2026:** suíte do serviço aprovada com partida autoritativa real, ingresso WebSocket autenticado de uso único, cópia isolada em caminho Windows com espaço/acento e encerramento coordenado. Consulte o [registro P00–P08](../docs/godot_migration_strategy.md#registro-implementacao-2026-09-26) para os limites da validação.
