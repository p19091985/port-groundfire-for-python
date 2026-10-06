# Implementação e testes de aceite

**Plano de execução e matriz de aceite, versão de 26/09/2026.** O launcher, a API, os adapters e testes iniciais já foram implementados. A tabela E01–E09 continua descrevendo o **aceite completo**, e sua existência não prova que cada lote foi concluído. Evidências e lacunas atuais: [README](README.md) e [registro P00–P08](../docs/godot_migration_strategy.md#projeto-encerramento-pendencias).

Referências: [arquitetura e operação](PROJETO.md), [interfaces e estados](CONTRATOS.md). Todos os artefatos do produto servidor ficarão em `groundfire-online-service/`. Mudanças futuras nos clientes serão realizadas nas respectivas versões e distribuídas com elas; não serão dependências de instalação do serviço.

## 1. Sequência de implementação

| Lote | Dependência | Entregas concretas | Aceite para concluir |
|---|---|---|---|
| E01 — Pacote independente | Especificação deste projeto | `pyproject.toml`, dependências com versões/hashes, namespace `gf_service`, fechamento do runtime headless, recursos/licenças/proveniência, build e launcher inicial. | Importar e iniciar worker em cópia isolada sem repositório, Pygame ou Godot; fixtures provam preservação de física/codec; script não informa sucesso sem processo pronto. |
| E02 — Schemas e persistência | E01 | OpenAPI REST, schemas WS/UDP novos e legados, fixtures, migrações SQLite, transações/idempotência/outbox, relógio testável, IDs e erros. | Todos os modelos validam nos dois adapters; incompatibilidade explícita; migração de base vazia e da versão anterior; idempotência/reserva concorrente sem duplicação. |
| E03 — Identidade e social | E02 | Conta/convidado, refresh/revogação/recuperação, amizade/bloqueio, presença, grupo/consentimentos, convites, chat, eventos e resync. | Dois clientes independentes completam fluxo; bloqueio impede entrega/replay; logout/recovery revogam credenciais; atraso/perda não criam mensagens/convites duplicados. |
| E04 — Diretório e compatibilidade | E02; E03 para permissões | Diretório vivo, nó/lease autenticado, registro administrativo, favoritos/histórico, reachability, projeção schema 1, master opcional e pool legado isolado. | Servidor vencido some; favorito permanece; protocolo/plataforma filtrados; registro anônimo não sobrescreve nó gerenciado; web não recebe opção UDP. |
| E05 — Salas e busca | E03, E04 | Regras/roster/pronto, bots, convites de sala, liderança, fila, reserva indivisível, cancelamento, expiração e jobs duráveis. | Concorrência não ultrapassa capacidade; mudança de roster invalida busca/pronto; todos os membros veem o mesmo destino/motivo de falha. |
| E06 — Partidas hospedadas | E01, E05 | Supervisor, pool de portas, handshake interno, tickets, WS 3/UDP 2, fases preparar/commit, runtime managed_lobby, retomada, espectador, resultado e revanche. | Partida real termina via comandos de jogo; nenhuma entrada sem reserva; reset de geração recusa credencial antiga; crash libera recursos sem fabricar vitória. |
| E07 — Integração dos dois jogos | E03–E06 | SDKs/adapters distribuíveis, HTTP/social, transporte WSS Python, WS 3/UDP 2 Godot, menus e estados de erro, capacidades desktop/web, armazenamento de sessão. | Python e Godot reais jogam juntos; web usa WSS; UX mostra estados corretos; LAN e jogo local passam regressão com serviço desligado. |
| E08 — Operação e distribuição | E01–E07 | Launcher completo, Git Bash/WSL/Linux, instalação offline, TLS/perfis, admin, métricas, limites, logs, drain, backup/restore, documentação operacional. | Somente a pasta distribuída inicia com o comando acordado; caminhos com espaço/acentos; stop não mata terceiros; restore consistente; não restam workers após encerramento normal. |
| E09 — Homologação | E01–E08 | Matriz de testes executável, relatório com evidências, simulação sob falha, carga/soak, builds dos clientes e guia do operador. | Todos os gates obrigatórios passam sem skip indevido; limites medidos publicados; nenhuma capacidade anunciada sem teste correspondente. |

Os lotes expressam dependências técnicas e critérios para aceitar o produto completo. A implementação atual cobre parte deles; decisões alteradas por evidência devem atualizar os documentos e os testes antes de declarar um lote concluído.

Dentro de E01, o launcher pode executar apenas os componentes presentes, com capabilities verdadeiras; não entregar endpoints vazios, respostas de sucesso fixas ou simulação de cadastro como se fossem serviço funcional. Release completa só ocorre após E09.

## 2. Organização prevista dos testes

```text
groundfire-online-service/tests/
  unit/                 # regras, autorização, expiração e estados
  contract/             # REST, social, jogo e compatibilidade
  integration/          # banco real, sockets, processos, API e workers
  simulation/           # partidas comandadas por clientes automáticos
  security/             # fronteiras de identidade, tickets, diretório e limites
  package/              # cópia independente, launcher, instalação e restore
  fixtures/             # protocolos/versionamento, seeds e replays reproduzíveis
```

Ferramentas propostas: pytest para o serviço/harness Python; executor headless Godot para codecs/jornadas sem renderização; build web real em navegador para WSS/origin/reconexão. As versões das ferramentas e a licença entram no lock de desenvolvimento. A distribuição de produção não precisa carregar editor Godot, navegador ou pytest; o pacote de diagnóstico/teste pode incluí-los como dependências separadas, com erro claro quando faltar a ferramenta.

Testes unitários usam relógio controlável para TTL; integração usa sockets/processos reais e deadlines. Aguardar condição/evento com limite, sem sleeps longos usados como prova de sucesso. Portas efêmeras/configuráveis evitam interferir nos jogos instalados. Cada teste usa banco/diretório temporários próprios, fecha sockets e recolhe somente os processos que criou, mesmo após falha.

Fixtures capturadas do comportamento atual congelam codecs e simulação antes da extração. Comparação semântica tolera diferenças explicitamente permitidas, como ID aleatório e timestamp; não elimina campos de dano, inventário, fases, terreno ou placar para fazer o teste passar. Regressão de gameplay deve apontar divergência reproduzível por seed e sequência de comandos.

## 3. Matriz funcional e de integração

| ID | Cenário | Prova exigida |
|---|---|---|
| T01 | Primeira execução e segunda execução | Configuração/segredos criados uma vez; dados persistem; migrações não repetem efeitos; nenhum usuário administrador com senha fixa. |
| T02 | Conta, convidado e conversão | Handles únicos sob concorrência; display names iguais não confundem ID; upgrade preserva ID/histórico; convidado sem privilégio de conta. |
| T03 | Refresh e recuperação | Resposta perdida recuperável com mesmo request_id; replay diferente revoga família; códigos de recuperação consumidos uma vez; logout bloqueia REST/socket/ticket pendente. |
| T04 | Amigos e bloqueio | Só destinatário aceita; bloqueio revoga presença, convite e replay; outro usuário não enumera sala privada pelo erro. |
| T05 | Presença e eventos | Desconectar todos os dispositivos expira presença; invisível oculta endpoint; deduplicação/cursor/resync recuperam após queda sem perder atualização. |
| T06 | Grupo e convite | Expiração/uso do código, senha e bloqueio; grupo cheio; troca de líder; membro saindo cancela busca; nenhum aceite em nome de terceiro. |
| T07 | Diretório vivo | Heartbeat mantém nó; lease vencido o remove; ETag/304 corretos; nenhuma entrada de demonstração contada como servidor real. |
| T08 | Compatibilidade e plataformas | UDP 1/WS 1–2 somente legacy; UDP 2/WS 3 gerenciados; versão incompatível recusada; Godot web recebe apenas transporte disponível. |
| T09 | Sala/pronto/bots | Regras válidas, bots ocupam vagas; alteração de roster limpa pronto; If-Match impede start com revisão antiga; start duplicado cria só um match/job. |
| T10 | Reserva concorrente | Dezenas de ingressos disputam as últimas vagas; ocupação nunca supera limite; grupo entra inteiro ou ninguém; reserva e slot retomável contam na mesma capacidade. |
| T11 | Cancelamento versus commit | Barreiras controlam a corrida; um único resultado terminal; sem worker/porta/reserva abandonados; cancelamento após início informa que a partida já começou. |
| T12 | Falha de alocação | Porta ocupada, runtime incompatível, processo que não fica ready, disco cheio; erro consultável; rollback de recursos; lobby volta ao estado autorizado. |
| T13 | Admissão e replay | Ticket de outro usuário/partida/geração/transporte é recusado; ACK perdido não cria outro slot; UDP direto não contorna validação. |
| T14 | Espectador | Assiste snapshots e troca observação na UI; quota própria; input, pronto e revanche negados; não altera inventário, terreno ou pontuação. |
| T15 | Retomada | Queda durante fase ativa; mesmo slot/inventário/placar; snapshot completo; conexão antiga invalidada; fora da janela recebe erro e política de espectador/reentrada. |
| T16 | Resultado e revanche | Só worker publica; resultado repetido não duplica histórico; cliente não falsifica vitória; revanche tem novo match_id, mesma sala e credenciais novas. |
| T17 | Chat e consumidor lento | Autorização/limites, escaping na UI, idempotência; fila limitada; cliente lento reconecta via resync, sem memória ilimitada. |
| T18 | Nó externo e publicação | Credencial escopada; DNS/endpoint inválido não publicado; probe não acessa destino interno proibido; register UDP não toma controle de nó gerenciado. |
| T19 | Continuidade local/LAN | Serviço encerrado; criar/listar/entrar/jogar LAN e jogar local permanecem funcionais em ambos desktops; web mostra capabilities reais. |
| T20 | Administração e privacidade | Jogador não usa admin; bootstrap único; ban/expulsão/drain auditados; logs, métricas e diretório sem senhas ou tokens. |
| T21 | Publicação Internet, quando habilitada | DNS/certificado/origins, HTTPS/WSS e versão efetivamente publicados; clientes em outra rede completam partida; web real não depende de URL local nem fallback de demonstração. |

Concorrência será testada com banco SQLite real, transações e múltiplas conexões. Mock de repositório não prova exclusão de vaga nem idempotência durável. Cada transição terminal exige verificações de banco, estado do worker e visão recebida pelos clientes, evitando sucesso apenas na resposta HTTP. T21 certifica uma implantação pública concreta; sua ausência permite certificar o pacote local/LAN, mas não anunciar a Internet como homologada.

## 4. Simulação real de jogo

O harness sobe o serviço em pasta temporária, cria identidades pela API pública, forma grupo/sala e conecta clientes por sockets. O teste não chama funções internas para forçar fase, dano, vitória ou saldo. Fixtures podem fixar seed, relógio determinístico do runtime de teste e configuração anunciada; todas as ações competitivas passam por comandos válidos do cliente.

| Cenário | Execução e verificações |
|---|---|
| S01 — Partida básica | Dois jogadores por WSS, mapa classic/seed 1, mínimo de rodadas permitido; aguardar fases, mirar/ajustar potência, disparar, observar colisão/dano/terreno, executar compras permitidas e terminar por regra normal. Validar saldo, munição, placar e resultado persistido. |
| S02 — Cliente misto | Um adapter Python real e um Godot headless real entram na mesma partida WS 3; pelo menos um espectador Godot; mesma sessão/roster/fases/placar nos clientes após normalizar renderização. |
| S03 — Transportes mistos | Python UDP 2 e Godot WSS 3 no perfil que permite UDP; mesma autoridade de capacidade; repetir disputa de última vaga entre os dois transports; nenhum bypass via UDP 1. |
| S04 — Bots e rodadas | Dois humanos simulados e bots autorizados do worker; várias seeds de mapa; completar fases e rodadas; bots não travam start e não extrapolam capacidade. |
| S05 — Queda e retorno | Derrubar conexão após tiro aceito e antes do snapshot; retomar na janela; não duplicar disparo/compra; reconstruir terreno/inventário; encerrar conexão antiga; completar partida. |
| S06 — Revanche | Completar partida, votar pela API, conferir novo match_id/geração e estado reiniciado; ticket/token anterior não entra na revanche; histórico contém dois resultados distintos. |
| S07 — Grupo incompleto | Três membros aceitam, um não conecta no prazo; preparação inteira é cancelada; nenhum jogo começa com consentimento parcial; slots liberados e todos recebem motivo. |
| S08 — Espectador adversarial | Enviar comandos de jogador pela conexão de espectador; worker rejeita sem alterar hash do estado autoritativo; espectador ainda recebe atualizações válidas. |
| S09 — Autoridade | Enviar compra sem saldo, item inválido, input fora de fase, replay de request_id, frequência excessiva; rejeição consistente; contador de comandos/recursos prova ausência de duplicação. |

Não basta receber `join_accept` ou alguns snapshots. A aprovação exige término válido da partida, resultado consistente e limpeza dos recursos. Deadlines impedem hang; falha salva seed, comandos, eventos e logs sem segredos para reprodução. Se uma seed tornar o roteiro de tiro incapaz de terminar, corrigir a estratégia do cliente automático, sem forçar vencedor por API interna.

A validação visual de botões/telas é complementar: amigos, convite, senha, detalhes do servidor, fila, cancelar, pronto, reconectar, observar e revanche devem conduzir às operações testadas. Preservar cores do Groundfire e ações equivalentes entre as edições; só screenshots não provam funcionalidade de rede.

### 4.1 Falhas de rede reproduzíveis

Harness com proxy de falhas configurável entre clientes/gateway/worker; registrar seed do injetor. Para UDP, simular perda de 3% e 10%, duplicação de 2%, reordenação e atraso variável de 20–150 ms. Para WSS/TCP, simular atraso, backpressure, interrupção de conexão e perda de resposta na camada de aplicação; não afirmar reordenação de frames entregues por TCP.

Critérios: comandos idempotentes não duplicam efeito; autoridade do worker não diverge; snapshots convergem quando a rede volta; retomada recupera estado dentro da janela; fora dela há erro/estado final explícito. Desempenho sob cada taxa é medido, sem pressupor que qualquer condição de rede garante jogo fluido. Testar ausência completa de conectividade, sem retry infinito ou travamento do loop gráfico.

## 5. Crash, persistência e operação

| ID | Interrupção | Aceite |
|---|---|---|
| F01 | Matar controle antes/depois de persistir job | Reinício reconcilia e não cria worker duplicado; jobs pendentes terminam ou falham com motivo. |
| F02 | Cair entre resgate e ACK de ingresso | Retry mantém um slot e uma identidade; ticket não pode ser reaproveitado por terceiro. |
| F03 | Cair após decisão de commit | Reenvio idempotente do commit; worker não inicia duas execuções; reserva consistente. |
| F04 | Matar gateway com worker vivo | Clientes WSS reconectam e retomam, respeitando janela; worker não inventa novos jogadores. |
| F05 | Matar worker durante rodada | Partida aborted, sem vencedor inferido; resultado parcial não vira final; processo novo não aceita credencial da geração antiga. |
| F06 | Falhar gravação de resultado | Retry do worker/outbox recupera resultado sem duplicar; se worker também morrer sem resultado durável, estado explicitamente indeterminado/aborted conforme regra. |
| F07 | Backup durante uso | Snapshot consistente, checksum e versão; restore em instância parada, integridade de relações e revogação de sessões restauradas por política. |
| F08 | Disco cheio/banco indisponível | Readiness/falhas coerentes; não confirmar escrita perdida; nenhum start que não possa ser registrado. |
| F09 | Ctrl+C/SIGTERM/stop | Drenagem, eventos e liberação de portas; só processos próprios encerrados; processo de teste de terceiro na máquina continua vivo. |
| F10 | Reinício com PID reutilizado | Nonce/horário/lease distinguem processo alheio; jamais encerrar por nome/PID isoladamente. |

Restore não deve ressuscitar refresh tokens, ingressos, reservas ou workers antigos. Marcar estado volátil como expirado, incrementar época da instalação quando necessário e exigir novo login/lease; preservar contas, amizades, favoritos e resultados confirmados. Backup contém material sensível e tem permissões/teste de acesso próprios; não enviar para serviço remoto por padrão.

## 6. Aceite do pacote independente

Procedimento executável obrigatório em E08/E09:

1. Produzir distribuição com runtime/código, recursos, migrações, wheels e manifestos necessários à plataforma alvo. Registrar versão/hash do núcleo de jogo incluído.
2. Copiar somente `groundfire-online-service/` para diretório temporário fora do repositório, incluindo caso com espaços e acentos. Não copiar arquivos irmãos nem apontar symlinks ao workspace.
3. Remover acesso ao repositório original dentro do ambiente de teste; limpar PYTHONPATH e instalações editáveis. Verificar imports externos proibidos e arquivos abertos em runtime.
4. Bloquear acesso externo à Internet para o perfil offline; manter loopback/rede de teste. Iniciar **`sh groundfire-online-service.sh`** e esperar `/readyz`; capturar saída/código de retorno.
5. Criar duas contas, amizade, grupo, sala e partida por clientes de teste independentes, sem editor Godot/Pygame instalados no host do serviço. Jogar até terminar; validar banco e resultado.
6. Reiniciar e conferir persistência; testar backup/restauração, status, segunda inicialização concorrente, porta em uso e configuração inválida.
7. Encerrar pelo launcher; verificar ausência de órfãos, lock abandonado e portas ocupadas. Segunda inicialização precisa funcionar sem limpeza manual.

Matriz obrigatória: Linux com POSIX sh; Windows com WSL; Windows com Git Bash e Python Windows. Certificar sinais/processos separadamente em Git Bash, não presumir comportamento idêntico ao Linux. Pacote portável depende de SO/arquitetura; ausência de runtime compatível deve falhar cedo com instrução clara. PowerShell puro não promete executar `sh` sem shell instalado.

Execução futura dos testes: `sh groundfire-online-service.sh test --suite standalone` para o pacote de validação; suítes `contract`, `integration`, `simulation` e `all` para desenvolvimento. O comando terá ajuda que discrimina ferramentas necessárias; ferramenta ausente não pode ser reportada como teste aprovado. É proibido rodar harness sobre banco/configuração de produção.

## 7. Carga e limites medidos

Perfil inicial de homologação proposto: 100 sessões sociais conectadas, 8 partidas simultâneas de até 8 jogadores, diretório sendo consultado, chat limitado e ciclo de reconexão durante 30 minutos. É uma carga de teste, não uma promessa de capacidade para qualquer máquina. Registrar CPU, RAM, SO, versão do runtime e configuração.

Medir percentis de latência de controle, atraso de tick, fila de snapshots, tempo de alocação, RAM inicial/final/pico, tamanho da outbox, locks do banco e tempo de recuperação. Critérios funcionais absolutos: zero excesso de capacidade, zero identidade/resultado trocado, zero fila sem limite e zero processo órfão em parada normal. Metas de latência/capacidade serão fixadas por hardware de referência antes do aceite de desempenho, com evidência reproduzível.

Adicionar teste de sobrecarga: ao esgotar capacidade, serviço mantém consultas/contas e responde `capacity_unavailable`; não sobe workers sem limite. Soak mais longo, com criação/encerramento repetidos, verifica crescimento persistente de memória/descritores. Não mascarar erro reduzindo silenciosamente o número de clientes ou descartando consumidores lentos sem registrar a ocorrência esperada.

## 8. Regressões e evidências

Durante implementação, preservar e adaptar as referências existentes na raiz do repositório:

- `tests/test_master_server_integration.py`: compatibilidade de consulta e TTL.
- `tests/test_online_match_simulation.py`: simulação do jogo e comportamento de rede existentes.
- `tests/test_groundfire_net_module.py`: diretório, gateway e módulos atuais.
- `scripts/validate_godot_udp_integration.py`: integração nativa Godot/Python.

Esses testes não serão imports de produção do serviço. Cenários relevantes terão fixtures/harness próprios dentro do pacote. A suíte dos clientes será executada nos checkouts respectivos; a instalação independente continuará sem precisar deles.

Cada execução de homologação produzirá um manifesto com commit/versão do serviço e clientes, hashes dos protocolos/runtime, plataforma, configuração sem segredos, seeds, lista de testes, duração, resultados, skips justificados e localização dos logs/replays. Capturas de tela demonstram jornadas de UI; traces e estado autoritativo demonstram gameplay. Um skip em cenário obrigatório bloqueia certificação daquela plataforma.

## 9. Definição de concluído

| Requisito do projeto | Evidência principal |
|---|---|
| SE01–SE03: independência e comando único | E01/E08, procedimento de isolamento, T01, F09/F10. |
| SE04: identidade sem provedor obrigatório | E03, T02/T03, teste offline. |
| SE05: diretório confiável | E04, T07/T08/T18. |
| SE06: social | E03, T04–T06/T17. |
| SE07: salas | E05, T09/T12, S04/S07. |
| SE08: busca/reserva | E05/E06, T10/T11/T13, S03/S07. |
| SE09: partida entre edições | E06/E07, T14–T16, S01–S09 e build web real. |
| SE10: operação | E08, T20, F01–F10 e carga medida. |
| SE11: LAN/legado preservados | E04/E07, T08/T19 e regressões existentes. |
| SE12: aceite executável | E09, relatório completo sem substituição por mocks/screenshots. |

Produto concluído significa: distribuição isolada funcional pelo comando solicitado, jornadas reais em ambas as edições, contratos versionados, falhas recuperáveis verificadas e guia operacional reproduzível. A documentação atual define esse trabalho; não afirma que ele já foi realizado.
