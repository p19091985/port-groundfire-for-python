# Plano para Fidelidade 100% do Browser de Servidores

Este documento lista tudo que precisa existir para o browser de servidores do Groundfire ficar fiel, visual e funcionalmente, às telas anexadas inspiradas no Counter-Strike 1.6.

Referências usadas:

- `/home/patrik/Desktop/Screenshot_2026-05-02_10-04-25.png`: botão `Find Servers`.
- `/home/patrik/Desktop/Screenshot_2026-05-02_10-00-56.png`: aba `Lan` vazia.
- `/home/patrik/Desktop/Screenshot_2026-05-02_10-00-38.png`: aba `History` vazia.
- `/home/patrik/Desktop/Screenshot_2026-05-02_10-00-22.png`: aba `Unique` com descrição.
- `/home/patrik/Desktop/Screenshot_2026-05-02_09-59-59.png`: aba `Favorites` com lista.
- `/home/patrik/Desktop/Screenshot_2026-05-02_09-59-34.png`: aba `Internet` populada.

## Objetivo

Implementar uma tela que pareça, se comporte e seja testada como as telas dos anexos:

- Mesmo layout geral.
- Mesmas abas.
- Mesmas colunas por aba.
- Mesmas mensagens vazias.
- Mesmos botões por aba.
- Mesma hierarquia visual, cores, bordas, scrollbar, linhas e espaçamentos.
- Mesmo fluxo de servidores: internet, favoritos, únicos, histórico e LAN.
- Rede nativa do projeto, sem depender de Steam, Counter-Strike ou bibliotecas externas de rede.
- Testes de cliente, servidor e master server usando UDP real, sem mockar rede.

## Matriz de Cobertura dos Anexos

| Anexo | Estado exigido | Tela/aba | Deve existir no projeto |
|:---|:---|:---|:---|
| `Screenshot_2026-05-02_10-04-25.png` | Botão isolado | Menu inicial | Botão `Find Servers` com mesmo texto, cor, padding e estado de hover/click |
| `Screenshot_2026-05-02_09-59-34.png` | Lista populada | `Internet` | 124 servidores de fixture visual, colunas, quick refresh, refresh all, connect e link inferior |
| `Screenshot_2026-05-02_09-59-59.png` | Lista populada | `Favorites` | 5 favoritos, add current server, add a server, refresh, connect |
| `Screenshot_2026-05-02_10-00-22.png` | Lista populada | `Unique` | 4 servidores deduplicados, coluna `Server description`, refresh all |
| `Screenshot_2026-05-02_10-00-38.png` | Lista vazia | `History` | Mensagem vazia, coluna `Last played`, refresh e connect desabilitado |
| `Screenshot_2026-05-02_10-00-56.png` | Lista vazia | `Lan` | Mensagem vazia, refresh e connect desabilitado |

Essa matriz deve virar teste visual. Cada linha precisa de fixture determinística e captura automatizada.

## Escopo de Fidelidade

### Botão `Find Servers`

O botão precisa bater com o anexo:

- Texto exato: `Find Servers`.
- Tamanho e proporção próximos do recorte.
- Fundo azul escuro com aparência de botão clássico.
- Texto cinza claro/branco.
- Estado normal, hover, pressionado e desabilitado.
- Posição no menu principal conforme a composição final do menu.

Critérios de aceite:

- O botão aparece no primeiro menu.
- O clique abre a tela `Servers`.
- Teste visual confirma cor, caixa e texto dentro da tolerância definida.

### Janela `Servers`

A janela deve reproduzir a estrutura dos anexos:

- Título externo da janela igual ao anexo: `Counter-Strike`, caso o objetivo seja pixel-perfect absoluto.
- Título/legenda visual `Servers` no topo interno.
- Aparência verde/cinza militar.
- Botão `x` no canto superior direito da janela interna.
- Botões/minibarra de sistema visíveis no anexo: minimizar, maximizar/restaurar e fechar, se a janela for desenhada pelo próprio jogo.
- Grip de resize no canto inferior direito.
- Abas horizontais:
  - `Internet`
  - `Favorites`
  - `Unique`
  - `History`
  - `Lan`
- Aba ativa com texto amarelo.
- Aba inativa com texto claro.
- Borda fina em torno da janela, tabela e rodapé.
- Área de tabela ocupando quase toda a janela.
- Scrollbar vertical à direita, com seta superior, trilho, thumb e seta inferior.
- Rodapé com botões à esquerda/direita.
- Link inferior: `Open the list of all servers (5300+)`.

Critérios de aceite:

- Em resolução base, os retângulos principais ficam nas mesmas posições relativas dos anexos.
- Em outras resoluções, a tela escala mantendo proporções e sem sobreposição.
- Capturas automatizadas comparam a UI renderizada com as imagens de referência.
- Se a titlebar for do sistema operacional e variar, o teste visual deve recortar somente a área interna. Se a meta for 100% idêntica ao anexo inteiro, desenhar titlebar própria no Pygame.

### Elementos Fixos de Layout

Esses detalhes precisam ser medidos nos anexos e registrados antes da implementação final:

- Resolução de referência de cada anexo.
- Retângulo externo da janela.
- Altura da titlebar.
- Margens internas.
- Altura das abas.
- Largura de cada aba.
- Altura do cabeçalho da tabela.
- Altura exata de cada linha.
- Posição e largura de cada coluna por aba.
- Largura da scrollbar.
- Altura das setas da scrollbar.
- Tamanho do thumb para cada estado.
- Retângulo dos botões do rodapé.
- Retângulo do link inferior.
- Posição do texto dentro dos botões.
- Cor RGB de fundo principal, fundo de tabela, bordas, texto ativo, texto inativo, texto desabilitado e seleção.

Arquivo sugerido para guardar essas medições:

```text
docs/references/server_browser/measurements.json
```

Formato sugerido:

```json
{
  "base_resolution": [1280, 768],
  "window_rect": [0, 0, 1280, 742],
  "tabs": {
    "internet": [6, 70, 79, 96]
  },
  "columns": {
    "internet": {
      "servers": [23, 100, 939, 118],
      "game": [939, 100, 1051, 118],
      "players": [1051, 100, 1105, 118],
      "map": [1105, 100, 1197, 118],
      "latency": [1197, 100, 1254, 118]
    }
  }
}
```

### Estados Visuais Obrigatórios

Todos os elementos interativos precisam de estados:

- Normal.
- Hover.
- Pressionado.
- Ativo/selecionado.
- Desabilitado.
- Foco de teclado.

Aplica-se a:

- Abas.
- Linhas da tabela.
- Cabeçalhos ordenáveis.
- Botões do rodapé.
- Link `Open the list of all servers (5300+)`.
- Scrollbar.
- Botão `x`.
- Checkboxes e campos dos diálogos.

Critérios de aceite:

- `Connect` fica desabilitado quando não existe seleção.
- Aba ativa fica com texto amarelo.
- Linha selecionada tem fundo diferente.
- Cabeçalho ordenado indica direção de ordenação sem quebrar a fidelidade visual.
- Hover não desloca texto nem altera tamanho de botão.

## Abas e Conteúdo

### Aba `Internet`

Tela populada deve ter:

- Cabeçalho: `Servers`, `Game`, `Players`, `Map`, `Latency`.
- Contador: `Servers (124)` ou número real retornado pelo master server.
- Ícone pequeno antes de `Servers`, como no anexo.
- Linhas com nomes longos sem quebrar o layout.
- Colunas alinhadas como no anexo.
- Botões:
  - `Change filters`
  - `Quick refresh`
  - `Refresh all`
  - `Connect`
- Link inferior `Open the list of all servers (5300+)`.

Tela vazia deve ter:

- Mensagem exata: `No internet games responded to the query.`
- Botões `Refresh` e `Connect`, com `Connect` desabilitado.

Rede necessária:

- Master server Groundfire nativo.
- Servidor publica entrada no master server.
- Browser consulta master server.
- Refresh geral consulta de novo.
- Quick refresh pinga o servidor selecionado.
- Latência vem de ping UDP real.
- Link `Open the list of all servers (5300+)` abre/força uma query sem filtros ao master server e exibe todos os servidores conhecidos pelo master.

Critérios de aceite:

- Com um master server real rodando, a aba Internet mostra servidores publicados.
- Sem master server ou sem resposta, mostra a mensagem vazia correta.
- Teste de integração sobe master, servidor e cliente reais por UDP e conecta.

### Aba `Favorites`

Tela deve ter:

- Cabeçalho: `Servers`, `Game`, `Players`, `Map`, `Latency`.
- Ícone pequeno antes de `Servers`.
- Contador: `Servers (N)`.
- Lista persistida em arquivo local.
- Linhas manuais podem aparecer só como `host:port` e `-` nas colunas sem metadados, como no anexo.
- Botões:
  - `Change filters`
  - `Add Current Server`
  - `Add a Server`
  - `Refresh`
  - `Connect`

Funcionalidades:

- `Add a Server` abre diálogo para digitar `host:port`.
- `Add Current Server` adiciona o servidor selecionado ou o servidor conectado atual, quando houver sessão.
- `Refresh` atualiza metadados/ping dos favoritos.
- Favoritos sobrevivem ao reiniciar o jogo.

Critérios de aceite:

- Adicionar manualmente `127.0.0.1:27015` aparece na lista.
- Servidor real favorito atualiza colunas após refresh.
- Servidor offline continua listado com colunas `-`.

### Aba `Unique`

Tela deve ter:

- Cabeçalho: `Servers`, `Server description`, `Game`, `Players`, `Map`, `Latency`.
- Ícone pequeno antes de `Servers`.
- Dedupe por `host:port`, preservando a melhor entrada disponível.
- Descrição longa cortada sem invadir outras colunas.
- Botões:
  - `Change filters`
  - `Quick refresh`
  - `Refresh all`
  - `Connect`

Critérios de aceite:

- O mesmo servidor presente em Internet, LAN e Favorites aparece uma única vez.
- Se existir descrição, ela aparece na coluna `Server description`.
- Ordenação e filtros funcionam com a lista deduplicada.

### Aba `History`

Tela deve ter:

- Cabeçalho: `Servers`, `Game`, `Players`, `Map`, `Latency`, `Last played`.
- Ícone pequeno antes de `Servers`.
- Mensagem vazia exata: `No servers have been played recently.`
- Botões:
  - `Change filters`
  - `Refresh`
  - `Connect`

Funcionalidades:

- Toda conexão bem-sucedida grava histórico.
- Histórico grava data/hora.
- Histórico persiste em disco.
- Conectar em item do histórico funciona como conexão direta.

Critérios de aceite:

- Após conectar em servidor real, o item aparece no History.
- `Last played` aparece preenchido.
- Sem histórico, a mensagem vazia aparece igual ao anexo.

### Aba `Lan`

Tela deve ter:

- Cabeçalho: `Servers`, `Game`, `Players`, `Map`, `Latency`.
- Ícone pequeno antes de `Servers`.
- Mensagem vazia exata: `No internet games responded to the query.`
- Botões:
  - `Change filters`
  - `Refresh`
  - `Connect`

Funcionalidades:

- Servidores LAN publicam anúncio UDP.
- Browser escuta anúncios UDP.
- Refresh força nova coleta/poll.
- Entradas LAN expiram quando param de responder.

Critérios de aceite:

- Com servidor LAN real rodando, item aparece.
- Sem servidor LAN, mensagem vazia aparece.
- Teste usa socket UDP real em loopback.

## Diálogos Necessários

### `Change filters`

Precisa ter aparência clássica e filtros funcionais:

- Campo texto para nome/descrição/mapa.
- Mostrar/esconder servidores cheios.
- Mostrar/esconder servidores vazios.
- Mostrar/esconder servidores protegidos por senha.
- Filtro de região.
- Filtro de servidor secure.
- Filtro de latência máxima.
- Botões `Apply`, `Clear`, `Close`.

Critérios de aceite:

- Filtro altera a lista imediatamente ou ao aplicar.
- Filtros afetam Internet, Favorites, Unique, History e Lan.
- Estado visual dos checkboxes fica claro.
- Fechar o diálogo sem aplicar deve preservar o estado anterior, se o comportamento escolhido for igual ao Counter-Strike. Se o projeto aplicar em tempo real, documentar essa diferença e ajustar testes.

### `Add a Server`

Precisa permitir:

- Digitar `host:port`.
- Porta padrão quando usuário digita só host.
- Validação de porta entre `1` e `65535`.
- Botões `Add` e `Cancel`.
- Ao adicionar, item entra em Favorites.

Critérios de aceite:

- `127.0.0.1:27015` cria favorito.
- `127.0.0.1` usa porta padrão.
- Porta inválida mostra erro e não adiciona.
- Campo aceita colar texto.
- Enter confirma.
- Escape cancela.

### Senha de Servidor

Precisa permitir:

- Ao clicar `Connect` em servidor protegido, abrir diálogo de senha.
- Campo mascarado com `*`.
- Botões `Connect` e `Cancel`.
- Enviar senha no `JoinRequest`.
- Servidor rejeitar sem senha ou senha errada.

Critérios de aceite:

- Sem senha: `password_required`.
- Senha errada: `bad_password`.
- Senha correta: `JoinAccept`.
- Enter confirma.
- Escape cancela.
- Histórico só grava conexão aceita, nunca rejeitada.

## Interação e Teclado

Comportamentos obrigatórios para ficar usável e fiel:

- Clique em aba troca aba.
- Clique em linha seleciona linha.
- Duplo clique em linha conecta.
- Enter conecta no servidor selecionado.
- Escape fecha diálogo; na tela principal de servidores, volta ao menu anterior.
- Setas cima/baixo mudam seleção.
- Page Up/Page Down rolam uma página.
- Scroll wheel move a lista.
- Clique no cabeçalho ordena.
- Segundo clique no mesmo cabeçalho inverte ordem.
- Clique no trilho da scrollbar move página.
- Arrastar o thumb da scrollbar rola a lista.
- Botão `x` fecha a janela `Servers`.

Critérios de aceite:

- A seleção nunca sai dos limites da lista.
- A seleção acompanha a rolagem.
- Nenhuma ação de teclado funciona em diálogo errado.
- Conexão por duplo clique e por botão usam o mesmo fluxo.

## Ordenação

Regras por coluna:

- `Servers`: alfabética por nome.
- `Server description`: alfabética por descrição.
- `Game`: alfabética por jogo/modo.
- `Players`: numérica por jogadores atuais e depois máximo.
- `Map`: alfabética por mapa.
- `Latency`: numérica, com servidores sem ping no fim.
- `Last played`: data/hora mais recente primeiro.

Critérios de aceite:

- Ordenação preserva seleção quando possível.
- Ordenação em `Unique` continua deduplicada.
- Ordenação em lista vazia não quebra.

## Rede Nativa Necessária

Tudo deve usar apenas biblioteca padrão do Python:

- `socket`
- `selectors`
- `json`
- `dataclasses`
- `time`
- `threading` nos testes de integração, se necessário

Componentes:

- `groundfire_net.transport`: UDP não bloqueante.
- `groundfire_net.codec`: envelope JSON.
- `groundfire_net.discovery`: descoberta LAN.
- `groundfire_net.browser`: favoritos, histórico, Internet persistida.
- `groundfire_net.master`: master server nativo.
- `groundfire_net.server`: loop de servidor.

Fluxos obrigatórios:

1. Servidor abre porta de jogo.
2. Servidor anuncia LAN.
3. Servidor registra no master server.
4. Browser LAN recebe anúncio.
5. Browser Internet consulta master.
6. Browser pinga servidor.
7. Cliente conecta por item da lista.
8. Cliente conecta por `host:port`.
9. Servidor aceita ou rejeita senha.
10. Histórico grava conexão.

## Master Server Nativo

Para substituir a parte externa que não existe no projeto:

- Criar/usar `groundfire-master`.
- Protocolo UDP JSON:
  - `register`
  - `unregister`
  - `query`
  - `register_ok`
  - `query_response`
- TTL para remover servidores mortos.
- Query por jogo, região, secure, senha, cheio/vazio.
- Registro deve incluir:
  - nome
  - host
  - porta
  - jogo
  - mapa
  - jogadores
  - máximo de jogadores
  - senha sim/não
  - região
  - secure sim/não
  - descrição
  - versão do protocolo

Critérios de aceite:

- `python -m src.groundfire.master` sobe o master.
- `python -m src.groundfire.server --master-server 127.0.0.1:27017` publica o servidor.
- Aba Internet encontra o servidor.
- Ao fechar servidor, ele é removido por unregister ou TTL.

## Pixel-Fidelity Visual

Para chegar em 100% fiel aos anexos, criar uma bateria de testes visuais.

### Referências

Copiar os anexos para:

```text
docs/references/server_browser/
```

Nomes sugeridos:

```text
find_servers_button.png
internet_populated.png
favorites_populated.png
unique_populated.png
history_empty.png
lan_empty.png
```

### Renderer de teste

Criar um teste que:

- Abre Pygame com `SDL_VIDEODRIVER=dummy`.
- Renderiza cada estado do browser em resolução fixa.
- Salva captura em `.tmp/server_browser_actual/`.
- Compara com a imagem de referência.
- Usa tolerância configurável.

Critérios:

- Diferença máxima ideal: `0%`.
- Diferença aceitável temporária: `<= 1%` por causa de fonte/compositor.
- Texto não pode sair da célula.
- Nenhum botão pode sobrepor outro.
- Scrollbar deve estar na mesma lateral e proporção.

Observação:

- A barra de título real do sistema operacional pode variar por tema/desktop. Para fidelidade absoluta, a comparação deve focar a área interna renderizada pelo jogo ou desenhar uma titlebar própria controlada pelo Pygame.

## Dados de Demonstração Para Bater Com os Anexos

Para validar telas iguais aos anexos, criar fixtures determinísticas:

- Internet com `124` servidores.
- Favorites com `5` servidores.
- Unique com `4` servidores e descrições.
- History vazio.
- Lan vazio.

Arquivo sugerido:

```text
tests/fixtures/server_browser_reference_data.json
```

Esses dados são só para teste visual. O jogo real deve continuar usando rede real.

### Conteúdo mínimo da fixture visual

A fixture deve reproduzir os anexos, incluindo:

- Nomes longos com símbolos.
- Jogos/modos variados: `Counter-Strike`, `Zombie Plague`, `Zombie Escape`, `Ghost Fury`, etc.
- Mapas variados: `de_dust2`, `de_inferno`, `zm_fox`, `fy_snow`, etc.
- Latências variadas.
- Servidores com 0 jogadores, servidores cheios e servidores protegidos por senha.
- Descrições longas na aba `Unique`.
- Favoritos como IPs brutos.
- Histórico vazio.
- LAN vazio.

Mesmo que o Groundfire não use mapas/modos do Counter-Strike no jogo real, esses dados podem existir somente como fixture visual para testar fidelidade aos anexos.

## Testes Obrigatórios Sem Mockar Rede

Criar/manter testes de integração que sobem componentes reais:

- Master server UDP real.
- Servidor Groundfire UDP real.
- Cliente Groundfire UDP real.
- Browser consultando master real.
- Browser recebendo LAN real.
- Cliente conectando via Internet.
- Cliente conectando via LAN.
- Cliente conectando via Favorites.
- Cliente conectando via History.
- Cliente conectando por `host:port`.
- Cliente com senha errada.
- Cliente com senha correta.
- Dois clientes conectando ao mesmo servidor.
- Servidor cheio rejeitando cliente.
- Servidor parando e sumindo do master por TTL.

Arquivos sugeridos:

- `tests/test_master_server_integration.py`
- `tests/test_server_browser_visual_fidelity.py`
- `tests/test_server_browser_real_network_paths.py`

## Checklist de Implementação

### Fase 1: Congelar contrato visual

- Copiar screenshots para `docs/references/server_browser/`.
- Medir posições dos elementos nos anexos.
- Definir resolução base.
- Definir paleta exata.
- Definir fonte/tamanho/spacing.
- Definir retângulos exatos das abas, tabela, botões e scrollbar.
- Criar `measurements.json`.
- Criar fixture visual com os mesmos dados aparentes dos anexos.

### Fase 2: Renderer fiel

- Separar renderer do browser em componente testável.
- Criar estado determinístico por aba.
- Ajustar cores e linhas.
- Ajustar tamanhos de fonte.
- Ajustar alinhamento de colunas.
- Ajustar scrollbar.
- Ajustar estados desabilitados.
- Implementar ícone pequeno antes do texto `Servers`.
- Implementar resize grip visual.
- Decidir se titlebar será do SO ou desenhada pelo jogo.

### Fase 3: Fluxos de UI

- Implementar duplo clique para conectar.
- Implementar seleção por teclado.
- Implementar scroll wheel.
- Implementar ordenação por cabeçalho.
- Implementar modal de filtros fiel.
- Implementar modal de adicionar servidor fiel.
- Implementar modal de senha fiel.
- Implementar link `Open the list of all servers (5300+)`.
- Implementar drag do thumb da scrollbar.
- Implementar clique no trilho da scrollbar.
- Implementar estados hover/pressed em botões, abas e linhas.

### Fase 4: Rede e persistência

- Garantir master server nativo.
- Garantir publicação periódica do servidor.
- Garantir unregister/TTL.
- Garantir favoritos persistidos.
- Garantir histórico persistido.
- Garantir ping real.
- Garantir senha real no join.
- Garantir filtros Internet/Unique/Lan/Favorites/History.

### Fase 5: Testes reais

- Testes unitários para codec.
- Testes unitários para persistência.
- Testes reais de UDP para master.
- Testes reais de UDP para cliente/servidor.
- Testes reais de browser consultando master.
- Testes reais de LAN discovery.
- Testes de screenshot.
- Testes de regressão para `run_game.sh --once`.
- Teste de servidor cheio rejeitando cliente real.
- Teste de histórico gravado somente após conexão aceita.
- Teste do link `Open the list of all servers (5300+)`.

### Fase 6: Aceite final

- Rodar:

```bash
python3 -m unittest
python3 scripts/run_quality_checks.py
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy ./run_game.sh --once
python3 -m src.groundfire.master --host 127.0.0.1 --port 0 --ticks 1
python3 -m src.groundfire.server --port 0 --discovery-port 0 --ticks 1
```

- Gerar capturas novas.
- Comparar com os anexos.
- Corrigir diferenças até passar nos limites definidos.

## Definition of Done

O projeto só deve ser considerado 100% fiel quando:

- Todas as telas dos anexos têm estado equivalente no Groundfire.
- Todos os textos visíveis estão corretos.
- Todas as abas funcionam.
- Todos os botões funcionam.
- Todos os estados vazios funcionam.
- Todos os estados populados funcionam.
- Visual passa em teste de screenshot.
- Master server real funciona.
- Servidor real publica no master.
- Browser real encontra servidores.
- Cliente real conecta.
- Senha real é validada.
- Favoritos e histórico persistem.
- LAN real funciona.
- Não existe biblioteca externa de rede.
- A suíte completa passa.
- Testes visuais cobrem os seis anexos.
- `measurements.json` existe e é usado pelos testes.
- Diferenças aceitas estão documentadas explicitamente.

## Arquivos Prováveis de Trabalho

- `src/groundfire/ui/menus.py`
- `src/groundfire/ui/interface.py`
- `src/groundfire/network/browser.py`
- `src/groundfire/network/messages.py`
- `src/groundfire/network/lan.py`
- `src/groundfire/app/client.py`
- `src/groundfire/app/server.py`
- `src/groundfire/master.py`
- `groundfire/master.py`
- `groundfire_net/browser.py`
- `groundfire_net/master.py`
- `groundfire_net/transport.py`
- `tests/test_canonical_local_menu.py`
- `tests/test_master_server_integration.py`
- `tests/test_server_browser_visual_fidelity.py`

## Riscos

- Fonte do sistema pode mudar medidas de texto.
- Barra de título do sistema operacional pode variar.
- Capturas tiradas em outro tema GTK/KDE podem diferir.
- Rede UDP local pode ser bloqueada por firewall.
- Pixel-perfect absoluto pode exigir renderer próprio para a janela inteira.

## Decisão Recomendada

Para ficar realmente igual aos anexos, separar duas metas:

1. Fidelidade funcional: rede real, abas, filtros, favoritos, histórico, master server e senha.
2. Fidelidade visual: renderer com screenshots golden e ajustes finos de pixel.

A primeira meta garante que o projeto funciona. A segunda garante que ele fica visualmente igual.

## Status Implementado em 2026-05-03

- Rede multiplayer funcional do Groundfire: master server nativo, publicação do servidor, consulta do browser, LAN discovery, favoritos, histórico, senha e conexão real cliente/servidor.
- Browser: abas `Internet`, `Favorites`, `Unique`, `History` e `Lan`, colunas por aba, seleção, ordenação, filtros, refresh, quick refresh, add server, add favorite, connect, duplo clique, scroll wheel, clique no trilho e arraste do thumb.
- Fidelidade dos anexos: link inferior ajustado para `Open the list of all servers (5300+)`, mensagem vazia da aba `Lan` igual ao anexo, botão `Find Servers` com estilo próprio próximo ao anexo, estados hover/pressed/desabilitado nos botões principais, destaque de linha e resize grip visual.
- Histórico: agora é gravado somente depois que o servidor real aceita o join; conexão rejeitada por senha não grava entrada no `History`.
- Testes reais adicionados: cliente conectando por `Favorites`, cliente conectando por `History`, rejeição por senha sem gravar histórico, drag da scrollbar e textos de referência do browser.
- Verificação atual: `python3 -m unittest` passa com 188 testes; `python3 scripts/run_quality_checks.py` passa; smoke do `run_game.sh --once`, smoke do master e smoke do servidor passam.

Decisão visual tomada: a titlebar externa do sistema operacional é recortada/ignorada nos testes automatizados, porque varia por tema/desktop. A comparação pixel a pixel cobre a área interna do browser e o botão `Find Servers`.

## Conjunto de Testes Atual do Browser/Multiplayer

Este pacote cobre a parte de browser de servidores e conexão multiplayer sem usar mocks de rede nos fluxos críticos:

- `tests/test_canonical_local_menu.py`
  - Abre a tela pelo botão `Find Servers`.
  - Valida abas `Internet`, `Favorites`, `Unique`, `History`, `Lan`.
  - Valida colunas esperadas por aba, mensagens vazias e botões de cada estado.
  - Valida link `Open the list of all servers (5300+)`.
  - Valida `Add Favorite`, `Add a Server`, `Refresh`, `Quick refresh`, `Refresh all`, `Connect`.
  - Valida filtros por texto, região, latência, servidor cheio/vazio, senha e secure.
  - Valida filtros aplicados em `Favorites`, `History` e `Lan`.
  - Valida ordenação, seleção, duplo clique, teclado, wheel, clique no trilho e drag do thumb.
  - Valida modal de senha e modal de adicionar servidor.
  - Valida estados hover/pressed/desabilitado dos controles principais.

- `tests/test_server_browser_real_network_paths.py`
  - Valida anúncio LAN por UDP real.
  - Valida entrada LAN descoberta conectando cliente real a servidor real.
  - Valida servidor cheio rejeitando segundo cliente real.
  - Valida cliente conectando por `Favorites` e depois por `History`.
  - Valida rejeição por senha sem gravar histórico.

- `tests/test_master_server_integration.py`
  - Valida servidor publicando no master nativo.
  - Valida browser consultando master nativo.
  - Valida cliente conectando com senha correta.
  - Valida senha errada.
  - Valida conexão direta por host/porta e slot solicitado.
  - Valida TTL/unregister de entradas do master.

- `tests/test_server_browser_visual_fidelity.py`
  - Valida existência e dimensões dos seis anexos copiados.
  - Valida `measurements.json`.
  - Valida fixture visual com contagens esperadas: Internet 124, Favorites 5, Unique 4, History vazio, Lan vazio.
  - Valida retângulos medidos dentro dos limites das imagens.
  - Renderiza screenshots reais em SDL dummy para os seis estados.
  - Salva os PNGs atuais em `.tmp/server_browser_actual/`.
  - Compara as capturas atuais contra os anexos por pixel/tolerância.
  - Usa `visual_comparison` em `measurements.json` como contrato de tolerância.

## Falta Implementar Para 100% Idêntico aos Anexos

Funcionalmente, o multiplayer/conexão do Groundfire está coberto. O teste screenshot/golden com tolerância também está implementado. O que ainda falta para pixel-perfect absoluto, isto é, tolerância visual muito baixa ou zero:

- Reduzir gradualmente as tolerâncias de `visual_comparison` em `measurements.json` até a diferença ficar próxima de zero.
- Ajustar fonte e atlas de texto para bater com o bitmap/pixel font dos anexos.
- Ajustar medidas exatas de espaçamentos, larguras de colunas, altura de linhas, posição dos botões, scrollbar, resize grip e cores finais.
- Afinar estados visuais de hover/pressed/focus para abas, linhas, botões, setas e link inferior até passarem com tolerância menor.
- Se o objetivo virar comparar o anexo inteiro, incluindo barra do sistema, desenhar uma titlebar própria no Pygame com título `Counter-Strike`, botões minimizar/maximizar/fechar e bordas iguais ao anexo.
- Opcionalmente trocar os anexos por goldens gerados pelo próprio projeto depois que a fidelidade visual for aprovada manualmente.

Observação importante: não falta integração com servidores reais de Counter-Strike/Steam porque o requisito definido para este projeto foi rede nativa do Groundfire, sem bibliotecas externas de rede. Se um dia a meta mudar para conectar em servidores CS 1.6 reais, isso vira outro escopo de protocolo.
