# Groundfire Python Port: Roadmap de Refatoracao 2026

> Status desta entrega
>
> Este roadmap descreve a execucao sugerida da modernizacao.
> A refatoracao principal ainda nao foi iniciada nesta etapa.

## Premissas

- preservar a jogabilidade protegida pelos testes existentes;
- nao quebrar o jogo atual sem trilha de migracao;
- priorizar isolamento de simulacao, assets e estado antes de rede;
- manter o runtime jogavel ao fim de cada fase.

## Fase 0 - Auditoria e mapeamento do codigo

Objetivo:

- consolidar inventario de modulos, assets, estados, dependencias e hotspots.

Arquivos ou modulos afetados:

- `src/*`
- `tests/*`
- `conf/*`
- `data/*`

Riscos:

- subestimar acoplamentos escondidos;
- ignorar divergencias reais com o legado em C++.

Dependencias:

- nenhuma.

Criterios de sucesso:

- inventario fechado;
- mapa de riscos aprovado;
- baseline tecnica documentada.

Impacto esperado:

- elimina refatoracao cega;
- cria a base de decisao das fases seguintes.

## Fase 1 - Hardening minimo antes da reorganizacao

Objetivo:

- corrigir desvios estruturais que atrapalham a extracao do nucleo.

Arquivos ou modulos afetados:

- `src/game.py`
- `src/shopmenu.py`
- `src/winnermenu.py`
- `src/font.py`
- `src/weapons_impl.py`
- `src/missile.py`
- `src/mirv.py`
- `src/quake.py`
- `src/blast.py`
- `src/trail.py`

Riscos:

- regressao de fidelidade se faltar cobertura de teste em UI e render.

Dependencias:

- Fase 0 concluida;
- ampliar testes para fluxo humano e bugs de tela.

Criterios de sucesso:

- `read_settings()` passa a ser chamado corretamente;
- input humano deixa de quebrar `ShopMenu` e `WinnerMenu`;
- duplicacao de desenho e ciclo de draw ficam saneados;
- bootstrap deixa de criar trabalho desnecessario fora do round.

Impacto esperado:

- reduz comportamento incidental;
- aproxima o port do contrato do C++ antes da modernizacao maior.

## Fase 2 - Isolamento de modulos criticos

Objetivo:

- separar simulacao de infraestrutura.

Arquivos ou modulos afetados:

- `src/game.py`
- `src/tank.py`
- `src/player.py`
- `src/humanplayer.py`
- `src/aiplayer.py`
- `src/weapon.py`
- `src/weapons_impl.py`
- `src/shell.py`
- `src/missile.py`
- `src/mirv.py`
- `src/machinegunround.py`
- `src/landscape.py`

Riscos:

- circularidades temporarias;
- regressao na ordem de update.

Dependencias:

- Fase 1;
- testes de simulacao fortalecidos.

Criterios de sucesso:

- gameplay deixa de depender de `pygame` diretamente;
- input vira comando;
- entidades reduzem dependencia do objeto `Game`.

Impacto esperado:

- abre caminho para modo headless;
- prepara serializacao de estado.

## Fase 3 - Reorganizacao arquitetural

Objetivo:

- mover o projeto para pacotes por dominio com interfaces claras.

Arquivos ou modulos afetados:

- praticamente todo `src/`.

Riscos:

- grande volume de mudancas de imports;
- conflitos se feito em um unico patch grande.

Dependencias:

- Fase 2;
- layout alvo aprovado.

Criterios de sucesso:

- pacote `groundfire/` ou equivalente estabelecido;
- imports limpos, sem `sys.path.append`;
- fronteiras claras entre `core`, `sim`, `render`, `ui`, `assets`, `input`, `audio` e `network`.

Impacto esperado:

- melhora manutencao e testabilidade;
- reduz blast radius das fases seguintes.

## Fase 4 - Modernizacao do pipeline de assets

Objetivo:

- substituir `.tga`, introduzir manifest e separar source assets de runtime assets.

Arquivos ou modulos afetados:

- `data/*`
- `src/game.py`
- `src/font.py`
- `src/interface.py`
- `src/menu.py`
- `src/weapon.py`
- `scripts/generate_readme_art.py`
- novo subsistema `assets/`

Riscos:

- inversao visual por orientacao;
- perda de alpha;
- regressao em paths hardcoded.

Dependencias:

- utilitario de conversao validado;
- baseline visual estabelecida.

Criterios de sucesso:

- assets `.png` convertidos e validados;
- runtime resolve recursos por manifest ou aliases semanticos;
- `fonts` deixa de ser carregada duas vezes;
- `.tga` sai da trilha principal de build/runtime.

Impacto esperado:

- simplifica manutencao;
- prepara empacotamento e cache modernos.

## Fase 5 - Refatoracao da logica do jogo para tick fixo

Objetivo:

- tornar a simulacao deterministica o suficiente para rede, replays e servidor dedicado.

Arquivos ou modulos afetados:

- `game.py`
- `landscape.py`
- `tank.py`
- `player.py`
- `aiplayer.py`
- projetis e armas

Riscos:

- maior chance de regressao de gameplay;
- possiveis mudancas em trajetorias e timings.

Dependencias:

- Fases 2, 3 e 4;
- testes de fidelidade ampliados.

Criterios de sucesso:

- loop de simulacao usa tick fixo;
- RNG da partida e explicito;
- projetis nao dependem de `time.time()` do processo;
- testes de balistica passam no novo clock.

Impacto esperado:

- habilita snapshots, replays, rollback leve e servidor headless.

## Fase 6 - Preparacao para multiplayer

Objetivo:

- introduzir contratos internos de rede sem ainda ligar a stack completa.

Arquivos ou modulos afetados:

- novo `network/protocol`
- `core/events.py`
- `core/ids.py`
- `sim/world.py`
- `gameplay/player_commands.py`

Riscos:

- schema de mensagens ruim pode engessar a implementacao futura.

Dependencias:

- Fase 5 pronta.

Criterios de sucesso:

- entidades com IDs estaveis;
- comandos serializaveis;
- eventos de dominio definidos;
- snapshots e deltas de prototipo em memoria.

Impacto esperado:

- cria a fronteira entre cliente e servidor;
- diminui risco da primeira implementacao de rede.

## Fase 7 - Prototipo LAN e servidor dedicado

Objetivo:

- provar a arquitetura de rede em ambiente controlado.

Arquivos ou modulos afetados:

- `network/discovery/*`
- `network/client/*`
- `network/server/*`
- `network/session/*`
- bootstrap local/headless

Riscos:

- sincronizacao de terreno e missiles guiados;
- bugs de sessao e reconnect;
- regressao de UX em menus.

Dependencias:

- Fase 6;
- modo headless funcional.

Criterios de sucesso:

- servidor sobe sem janela;
- cliente lista partidas LAN;
- handshake de sessao funciona;
- round simples roda entre dois clientes e um servidor.

Impacto esperado:

- primeira prova real de escalabilidade da nova arquitetura.

## Fase 8 - Testes, profiling e hardening

Objetivo:

- estabilizar o sistema para evolucao continuada.

Arquivos ou modulos afetados:

- `tests/*`
- CI e configuracao do projeto
- benchmarks e ferramentas de profiling

Riscos:

- pular esta fase reduz drasticamente o valor das fases anteriores.

Dependencias:

- fases anteriores concluidas em versao funcional.

Criterios de sucesso:

- suite de testes por camada;
- testes de rede e integracao;
- benchmarks de simulacao e render;
- pipeline de CI funcionando;
- regressao visual e de assets validada.

Impacto esperado:

- base pronta para expansao segura.

## Roadmap especifico de rede

### Marco N1 - Contratos de comando e evento

Objetivo:

- padronizar `PlayerCommand`, `ServerEvent` e `SnapshotState`.

Entregas:

- schema versionado;
- IDs estaveis de jogador, entidade e sessao;
- eventos de round, disparo, dano, explosao e shop.

### Marco N2 - Descoberta LAN e handshake

Objetivo:

- permitir listar partidas locais e entrar nelas.

Entregas:

- beacon UDP;
- browser LAN;
- handshake com versao de protocolo, seed da partida e token de sessao.

### Marco N3 - Servidor autoritativo minimo

Objetivo:

- executar um round simples de forma remota e headless.

Entregas:

- servidor dedicado;
- replicacao basica de tanques, disparos e explosoes;
- sincronizacao de score, turnos e round.

### Marco N4 - Latencia e reconciliacao

Objetivo:

- tornar a experiencia jogavel fora da LAN perfeita.

Entregas:

- interpolacao;
- predicao visual local;
- reconciliacao leve para missile guiado;
- metricas e logs de rede.

## Prioridades executivas

### Curto prazo

- Fase 1 e Fase 2.
- Corrigir bugs estruturais e extrair simulacao de `pygame`.

### Medio prazo

- Fase 3, Fase 4 e Fase 5.
- Reorganizar o projeto, modernizar assets e introduzir tick fixo.

### Longo prazo

- Fase 6, Fase 7 e Fase 8.
- Levantar rede, servidor dedicado e hardening final.

## Proximos passos recomendados antes de implementacao pesada

1. Aprovar a arquitetura alvo e o escopo da Fase 1.
2. Decidir o layout final do pacote (`src/groundfire/...` ou equivalente).
3. Definir a politica de compatibilidade do port: fidelidade estrita ao C++ ou modernizacao seletiva.
4. Registrar baseline visual e de comportamento antes das primeiras correcoes.
5. Executar a migracao inicial de assets para `.png` em arvore paralela, sem trocar ainda o runtime principal.
