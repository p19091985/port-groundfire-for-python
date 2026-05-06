# Joga Jogo Automatico

Este documento registra o estado das ferramentas para iniciar partidas LAN automaticas de Groundfire com servidor, multiplos clientes e jogadores controlados pela IA.

Data da ultima atualizacao: 2026-05-05.

## Objetivo

Criar um fluxo de desenvolvimento em que um unico comando possa subir uma partida multiplayer local rapidamente:

1. Iniciar um servidor LAN.
2. Conectar varios clientes automaticamente.
3. Permitir que os clientes entrem como jogadores de computador.
4. Abrir uma janela Pygame por jogador IA por default para ver o jogo rodando na tela.
5. Configurar a partida automatica com 20 rounds por default.
6. Registrar comandos, stdout, stderr, eventos de rede, PIDs e encerramentos em logs.
7. Validar tudo com testes automatizados.

## Estado atual

| Item | Status | Evidencia |
|---|---|---|
| `iniciar-all.sh` | Implementado | Sem argumentos abre interface Ttk; com `-A` orquestra `iniciar-server.sh` + `iniciar-clientes.sh` e abre uma tela Pygame para cada tank IA. |
| `iniciar-server.sh` | Implementado | Inicia servidor LAN por `-A` e abre um cliente visual local; `--sem-tela` mantem somente servidor headless. |
| `iniciar-clientes.sh` | Implementado | Abre N clientes por `-n`; `-a` entra como IA, com todos os clientes visiveis por default. |
| Modos CLI e Ttk explicitos | Implementado | Os tres launchers documentam `--menu` para interface Ttk e `--cli` para comando de texto. |
| Menu Ttk do jogo completo | Implementado | `./iniciar-all.sh` abre painel Ttk para configurar servidor, clientes, uma tela por jogador IA, timeouts, senha, delay e detach. |
| Menu Ttk do jogo sem corte | Implementado | A janela de `iniciar-all.sh` abre maior e usa area rolavel para manter status e botoes sempre acessiveis. |
| Menu Ttk do servidor | Implementado | Ttk com validacao de host, porta, descoberta, nome, senha e opcao de tela local antes de disparar subprocesso. |
| Menu Ttk dos clientes | Implementado | Ttk com validacao de quantidade, host, porta, timeouts, keepalive, delay, IA, tela por jogador, once e detach. |
| Cliente IA em rede | Implementado | `JoinRequest.is_computer=True` faz o servidor controlar o tank pela IA do `MatchController`. |
| Clientes IA visuais | Implementado | Cada cliente IA visivel usa `groundfire.client --computer-player` sem `--headless-client`, renderizando a partida na tela enquanto o servidor controla o tank. |
| Cliente headless para automacao | Implementado | `groundfire.client --headless-client` conecta sem abrir janela Pygame. |
| Clientes headless persistentes | Implementado | Quando `--visible-count` limita as telas ou `--sem-tela` e usado, os clientes IA headless ficam vivos por `86400s` por default ou ate `Ctrl+C`. |
| Partida de 20 rounds | Implementado | `iniciar-all.sh -A` usa `--rounds 20` por default e repassa para `groundfire.server`. |
| Logs centrais por default | Implementado | `logs/server_debug.log`, `logs/clients_debug.log` e `logs/all_debug.log`. |
| Logs por processo | Implementado | `iniciar-all.sh` cria logs do servidor/client launcher, `iniciar-server.sh` cria log do cliente visual e `iniciar-clientes.sh` cria logs por cliente. |
| Eventos estruturados de conexao | Implementado | `--log-network-events` registra connect, hello, join, reject, timeout e disconnect. |
| Validacao de portas | Implementado | Scripts rejeitam portas nao numericas e fora de `1..65535`. |
| Validacao de hosts | Implementado | Scripts rejeitam host vazio, espacos, IPv4 fora de faixa e DNS malformado. |
| Verificacao UDP do servidor | Implementado | `iniciar-clientes.sh --check-server` faz ping UDP antes de abrir clientes; o menu dos clientes vem com essa verificacao ligada. |
| Presets de clientes/tanks | Implementado | Menus e CLI aceitam presets 2, 4, 6, 8 e 12 via `--preset`. |
| Rotacao de logs centrais | Implementado | `GROUNDFIRE_LOG_MAX_BYTES` e `GROUNDFIRE_LOG_BACKUPS` controlam rotacao dos logs centrais. |
| Validacao nos menus | Implementado | As interfaces Ttk bloqueiam entradas invalidas antes de chamar o shell. |
| Compatibilidade com `sh` | Implementado | Os tres launchers reexecutam em Bash se chamados como `sh iniciar-*.sh`. |
| Cleanup de processos | Implementado | `iniciar-server.sh`, `iniciar-clientes.sh` e `iniciar-all.sh` encerram filhos em `Ctrl+C`, exceto em `--detach`. |
| Testes pytest dos launchers | Implementado | `tests/test_lan_launch_scripts.py`. |
| Teste real do `iniciar-all.sh` | Implementado | Pytest sobe servidor e 6 clientes IA em `--sem-tela`, confirma 6 `join_accept` e encerra tudo. |
| Teste shell customizado | Implementado | `tests/shell/test_lan_launchers.sh`. |
| Suite Bats no CI | Implementado | `.github/workflows/ci.yml` instala Bats no Linux e executa `tests/shell/test_lan_launchers.bats`. |
| Testes de protocolo/IA | Implementado | `tests/test_groundfire_codec.py`, `tests/test_groundfire_entrypoints.py`, `tests/test_client_server_apps.py`. |
| README | Implementado | A tabela de scripts cita `iniciar-all.sh`, `iniciar-server.sh` e `iniciar-clientes.sh`. |

## Como usar

Abrir a interface grafica Ttk para configurar e iniciar a partida completa:

```bash
./iniciar-all.sh
./iniciar-all.sh --menu
```

Iniciar uma partida automatica completa com 1 servidor, 6 tanks IA, 20 rounds e 6 janelas Pygame mostrando o jogo:

```bash
./iniciar-all.sh -A
./iniciar-all.sh --cli --rounds 20
```

Alterar a quantidade de rounds:

```bash
./iniciar-all.sh -A --rounds 20
```

Iniciar outra quantidade de tanks IA:

```bash
./iniciar-all.sh -A -n 8
```

Usar um preset frequente de tanks IA:

```bash
./iniciar-all.sh -A --preset 8
```

Iniciar servidor LAN e abrir uma tela local conectada a ele:

```bash
./iniciar-server.sh -A
./iniciar-server.sh --cli
```

Iniciar apenas o servidor headless, sem abrir tela:

```bash
./iniciar-server.sh -A --sem-tela
```

Abrir a interface Ttk do servidor:

```bash
./iniciar-server.sh
./iniciar-server.sh --menu
```

Abrir 4 clientes humanos:

```bash
./iniciar-clientes.sh -n 4
./iniciar-clientes.sh --cli -n 4
```

Abrir 4 clientes como IA, com 4 janelas visiveis na tela:

```bash
./iniciar-clientes.sh -n 4 -a
```

Abrir 4 clientes IA, mas mostrar somente 1 janela e deixar 3 headless:

```bash
./iniciar-clientes.sh -n 4 -a --visible-count 1
```

Usar um preset frequente de clientes:

```bash
./iniciar-clientes.sh --preset 4 -a
```

Abrir 4 clientes IA totalmente headless, util para teste/CI:

```bash
./iniciar-clientes.sh -n 4 -a --sem-tela
```

Conectar clientes a outro computador da LAN:

```bash
./iniciar-clientes.sh -n 4 -a --host 192.168.0.10
```

Verificar se o servidor responde por UDP antes de abrir clientes:

```bash
./iniciar-clientes.sh --check-only --host 127.0.0.1 --port 27015
./iniciar-clientes.sh -n 4 -a --check-server
```

Abrir a interface Ttk dos clientes:

```bash
./iniciar-clientes.sh
./iniciar-clientes.sh --menu
```

Testar comandos sem abrir processos reais:

```bash
./iniciar-all.sh -A --dry-run
./iniciar-server.sh -A --dry-run
./iniciar-clientes.sh -n 4 -a --dry-run
```

Mesmo se chamado com `sh`, o launcher troca para Bash automaticamente:

```bash
sh iniciar-all.sh -A --dry-run
```

Manter a partida automatica viva por outro intervalo:

```bash
./iniciar-all.sh -A --keepalive-seconds 3600
```

Forcar a partida completa sem abrir janela, util em ambiente sem display:

```bash
./iniciar-all.sh -A --sem-tela
```

## Logs

Logs centrais padrao:

```text
logs/all_debug.log
logs/server_debug.log
logs/clients_debug.log
```

Logs por execucao/processo:

```text
logs/iniciar-all-YYYYMMDD-HHMMSS-server.log
logs/iniciar-all-YYYYMMDD-HHMMSS-clients.log
logs/iniciar-clientes-YYYYMMDD-HHMMSS-cliente-N.log
logs/iniciar-server-YYYYMMDD-HHMMSS-visible-client.log
```

Os nomes centrais podem ser sobrescritos:

```bash
GROUNDFIRE_ALL_LOG_FILE=logs/minha_partida.log ./iniciar-all.sh -A
GROUNDFIRE_SERVER_LOG_FILE=logs/meu_server.log ./iniciar-server.sh -A
GROUNDFIRE_CLIENTS_LOG_FILE=logs/meus_clientes.log ./iniciar-clientes.sh -n 4 -a
```

Rotacao dos logs centrais:

```bash
GROUNDFIRE_LOG_MAX_BYTES=1048576 GROUNDFIRE_LOG_BACKUPS=5 ./iniciar-all.sh -A
```

Quando o arquivo central passa do limite, ele vira `.1`, o `.1` anterior vira `.2` e assim por diante ate o limite de backups.

## Testes

Ultima verificacao local:

```bash
.venv/bin/python -m pytest
# 225 passed
```

Comandos de verificacao:

```bash
bash -n iniciar-server.sh iniciar-clientes.sh iniciar-all.sh tests/shell/test_lan_launchers.sh
tests/shell/test_lan_launchers.sh
bats tests/shell/test_lan_launchers.bats  # quando Bats estiver instalado
.venv/bin/python -m pytest tests/test_lan_launch_scripts.py
.venv/bin/python -m pytest tests/test_groundfire_entrypoints.py tests/test_client_server_apps.py
.venv/bin/python -m pytest
```

## O que foi feito nesta rodada

1. Logs centrais viraram default:
   `server_debug.log`, `clients_debug.log` e `all_debug.log`.

2. O stdout/stderr do menu Tk agora passa pelo log central do respectivo launcher.

3. Foi criado o modo headless de cliente conectado:
   `groundfire.client --headless-client`.

4. Clientes automaticos IA agora podem abrir janela Pygame e usam `--headless-client` somente quando `--visible-count` limita as telas ou `--sem-tela` e usado.

5. Os clientes headless de `iniciar-all.sh -A` e `iniciar-clientes.sh -a` ficam vivos por default por `86400s`, para que a partida continue rodando ate `Ctrl+C`; `--sem-tela` mantem todos sem janela.

6. Foi adicionado `--log-network-events` ao cliente, registrando eventos como `connecting`, `hello_accept`, `join_accept`, `join_reject`, `join_timeout` e `disconnect`.

7. `iniciar-server.sh`, `iniciar-clientes.sh` e `iniciar-all.sh` validam portas antes de abrir processos.

8. `iniciar-clientes.sh` ganhou cleanup com `trap` para encerrar clientes filhos em interrupcao.

9. Foi criado o teste shell customizado `tests/shell/test_lan_launchers.sh`.

10. Foi criado um teste end-to-end real que executa `iniciar-all.sh -A --sem-tela` sem `--dry-run`, confirma 6 `join_accept` e encerra o grupo de processos.

11. O README passou a listar os scripts de automacao LAN.

12. Foi corrigido um bug no handoff para o jogo legacy que chamava `ROUND_STARTING` uma vez por jogador configurado.

13. `iniciar-all.sh` foi refatorado para usar explicitamente `iniciar-server.sh` e `iniciar-clientes.sh`, em vez de chamar `python -m groundfire.server/client` diretamente.

14. `iniciar-all.sh` ganhou interface Ttk propria para configurar e disparar o fluxo completo.

15. `iniciar-clientes.sh` passou a aceitar `--client-delay` e `--join-timeout`, permitindo que o orquestrador controle esses tempos sem duplicar logica.

16. `iniciar-all.sh` passou a iniciar servidor e clientes em grupos de processo proprios via `setsid` quando disponivel, melhorando o encerramento completo em `Ctrl+C` e falhas.

17. `--once` agora e respeitado tambem no cliente IA headless: o launcher usa `--keepalive-seconds 0` e o entrypoint `groundfire.client` ignora keepalive quando `--headless-client --once` e usado.

18. Foi adicionada validacao profunda de host nos tres launchers:
    aceita `localhost`, IPv4 valido e nomes DNS/hostnames bem formados; rejeita espacos, hosts vazios e IPv4 fora de faixa.

19. Foi adicionada rotacao controlada dos logs centrais com:
    `GROUNDFIRE_LOG_MAX_BYTES` e `GROUNDFIRE_LOG_BACKUPS`.

20. As interfaces graficas validam entradas antes de disparar subprocessos, reduzindo falhas silenciosas vindas do menu.

21. Os menus individuais de servidor e clientes foram migrados para Ttk, padronizando a familia visual com `iniciar-all.sh`.

22. Foi criada a suite Bats `tests/shell/test_lan_launchers.bats`, mantendo tambem o teste shell puro para ambientes sem Bats.

23. `iniciar-clientes.sh -a` passou a abrir clientes IA em janela Pygame; `--visible-count` limita quantos ficam visiveis.

24. `iniciar-all.sh -A` passou a abrir o jogo na tela por default, repassando a quantidade de tanks como `--visible-count`.

25. `iniciar-server.sh -A` passou a iniciar um cliente visual local por default; `--sem-tela` ou `--server-only` preserva o modo servidor puro.

26. Foram adicionados testes pytest, shell puro e Bats para cobrir cliente visivel, modo `--sem-tela` e dry-runs dos novos comandos.

27. Os tres launchers agora reexecutam em Bash quando chamados com `sh iniciar-*.sh`, evitando o erro `set: Illegal option -o pipefail`.

28. `iniciar-clientes.sh` ganhou verificacao de alcance UDP:
    `--check-server` valida o servidor antes de abrir clientes e `--check-only` apenas testa e sai.

29. O menu Ttk dos clientes ganhou verificacao UDP por default e botao dedicado para testar o servidor.

30. `iniciar-all.sh` e `iniciar-clientes.sh` ganharam presets 2, 4, 6, 8 e 12 no menu e na CLI por `--preset`.

31. O workflow `.github/workflows/ci.yml` agora instala Bats no job Linux e executa `tests/shell/test_lan_launchers.bats`.

32. Os testes pytest, shell puro e Bats cobrem presets, verificacao UDP em dry-run, `--check-only` sem traceback e Bats no CI.

33. `groundfire.server`, `iniciar-server.sh` e `iniciar-all.sh` ganharam `--rounds`/`--num-rounds`; o `iniciar-all.sh -A` usa 20 rounds por default.

34. Foi verificada uma execucao real com `iniciar-all.sh -A --rounds 20 --sem-tela`: servidor respondeu, 6 clientes IA conectaram com `join_accept`, e um cliente de prova recebeu snapshot `round=1`, `num_rounds=20`, `phase=round_starting`.

35. Os tres launchers passaram a documentar e aceitar os modos explicitos:
    `--menu` para interface grafica Ttk e `--cli` para comando de texto.

36. Os testes dos launchers agora validam `--help` com os dois modos e dry-runs usando `--cli`.

37. `iniciar-all.sh -A -n 6` e `iniciar-clientes.sh -n 6 -a` agora abrem 6 janelas Pygame por default; `--visible-count 1` preserva o modo com uma janela e o restante headless.

38. O menu Ttk de `iniciar-all.sh` ganhou janela inicial maior e rolagem vertical para evitar corte dos botoes em telas menores.

## O que ainda falta

Nao ha pendencias obrigatorias nem opcionais registradas neste plano.

As melhorias que estavam pendentes tambem ja foram concluidas:

1. Bats e instalado no CI Linux e executa `tests/shell/test_lan_launchers.bats`.

2. O menu dos clientes e a CLI validam a alcancabilidade UDP do servidor antes de abrir instancias.

3. Os presets 2, 4, 6, 8 e 12 estao disponiveis no menu e na CLI de `iniciar-all.sh` e `iniciar-clientes.sh`.
