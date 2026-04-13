<p align="center">
  <img src="media/img/readme-hero.png" alt="Groundfire - arte de abertura montada com assets do jogo" width="720">
</p>

<h1 align="center">🔥 Groundfire — Port Python</h1>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.25.0-0d6efd?style=for-the-badge" alt="version">
  <img src="https://img.shields.io/badge/status-em%20desenvolvimento-bd3b3b?style=for-the-badge" alt="status">
  <img src="https://img.shields.io/badge/license-MIT-292929?style=for-the-badge" alt="License">
</p>
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%20—%203.13-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Pygame-2.6.1-1f6f43?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iMTAiIGZpbGw9IndoaXRlIi8+PC9zdmc+" alt="Pygame">
  <img src="https://img.shields.io/badge/rede-mpgameserver%20%7C%20msgpack-4B8BBE?style=flat-square" alt="Rede">
</p>

<p align="center">
  <kbd><a href="#portugues">🇧🇷 Português</a></kbd>&nbsp;&nbsp;
  <kbd><a href="#english">🇬🇧 English</a></kbd>
</p>

---

<a id="portugues"></a>

<h2 align="center">🇧🇷 Português</h2>

<p align="center"><strong>Port em Python/Pygame do Groundfire v0.25, com foco em preservação, jogabilidade clássica e compatibilidade moderna.</strong></p>

<p align="center"><code>Versão atual do pacote: 0.25.0</code></p>

<p align="center"><em>Groundfire é um jogo clássico de artilharia entre tanques, com terreno destrutível, combate balístico, economia entre rodadas, armas especiais, IA adversária e suporte a execução local ou cliente/servidor.</em></p>

---

### 📑 Índice

| | Seção | | Seção |
|---|---|---|---|
| 🎯 | [O que é este projeto?](#o-que-e-este-projeto) | 🎮 | [Jogabilidade](#jogabilidade) |
| 🖼️ | [Capturas e arte do jogo](#capturas-e-arte-do-jogo) | 🕹️ | [Controles padrão](#controles-padrao) |
| 💻 | [Requisitos de hardware e software](#requisitos-de-hardware-e-software) | ⚙️ | [Configuração do jogo](#configuracao-do-jogo) |
| 📦 | [Instalação passo a passo](#instalacao-passo-a-passo) | 🌐 | [Modo local e modo online](#modo-local-e-modo-online) |
| ▶️ | [Como iniciar o jogo](#como-iniciar-o-jogo) | 📂 | [Estrutura do repositório](#estrutura-do-repositorio) |
| 📜 | [Scripts de inicialização](#scripts-de-inicializacao) | 🏗️ | [Arquitetura de manutenção](#arquitetura-de-manutencao) |
| 📖 | [Documentação técnica incorporada](#documentacao-tecnica-incorporada) | 🧪 | [Testes automatizados e QA](#testes-automatizados-e-qa) |
| 🔧 | [Solução de problemas frequentes](#solucao-de-problemas-frequentes) | 🏆 | [Créditos e preservação histórica](#creditos-e-preservacao-historica) |
| 📄 | [Licença](#licenca) | | |

---

<a id="o-que-e-este-projeto"></a>

## 🎯 O que é este projeto?

O **Groundfire — Port Python** é uma adaptação em Python/Pygame do jogo **Groundfire v0.25**, criado originalmente por **Tom Russell**. A proposta deste repositório é manter o espírito do jogo original vivo em uma base mais fácil de executar, estudar, testar e evoluir em ambientes Python atuais.

O jogo coloca tanques em um terreno deformável. Cada jogador controla ângulo, potência, movimento, escudo, combustível de salto e escolha de armas. Entre as rodadas, a economia permite comprar munição e melhorias.

### Objetivo

Oferecer uma versão moderna e verificável do Groundfire para:

- 🎮 Jogar partidas locais com apresentação clássica
- 🔬 Preservar comportamento, ritmo e sensação do jogo original
- 🐍 Portar sistemas gradualmente para Python sem transformar o projeto em um remake solto
- ✅ Manter cobertura automatizada para mecânicas, renderização, rede, terreno e fidelidade
- 📚 Facilitar estudo de arquitetura de jogos 2D com Pygame

### Principais capacidades

| Capacidade | Descrição |
|---|---|
| 💥 Terreno destrutível | Formação de crateras e desabamentos |
| 🎯 Combate de artilharia | Ângulo, potência, gravidade e dano em área |
| 🚀 Tanques completos | Movimentação, jump jets, escudo e ciclo de vida por rodada |
| 🔫 Arsenal variado | Shell, Missile, MIRV, Nuke e Machine Gun |
| 🤖 IA adversária | Oponentes controlados por computador |
| 🛒 Loja entre rodadas | Compra de armas e upgrades |
| 🖥️ Runtime moderno | Entrada local clássica + servidor headless |
| 🧪 Testes de regressão | Fidelidade para manter o port sob controle |

### Escopo atual

> [!IMPORTANT]
> Este projeto ainda está em desenvolvimento. O objetivo não é apenas fazer um jogo parecido rodar em Python; o objetivo é preservar a experiência do Groundfire com o máximo de fidelidade prática, enquanto a base é reorganizada para manutenção moderna.

| Área | Estado | Observação |
|:---|:---:|:---|
| Jogo local | 🟢 ativo | Fluxo principal jogável pelo menu clássico |
| Runtime canônico | 🟢 ativo | Entrada moderna usada pelos wrappers `groundfire` |
| IA local | 🟢 ativa | Jogadores controlados pelo computador estão implementados |
| Terreno destrutível | 🟢 ativo | Crateras, queda de terreno e efeitos possuem testes dedicados |
| Loja entre rodadas | 🟢 ativa | Compra de armas e jump jets |
| Rede | 🟡 em evolução | Cliente, servidor headless, descoberta LAN e transporte seguro |
| Fidelidade histórica | 🟡 em evolução | Testes e registros ajudam a comparar comportamento |

---

<a id="capturas-e-arte-do-jogo"></a>

## 🖼️ Capturas e arte do jogo

As imagens abaixo foram geradas a partir de assets do próprio projeto e ajudam a visualizar a atmosfera do port.

<table align="center">
  <tr>
    <td align="center">
      <img src="media/img/readme-hero.png" alt="Arte de abertura do Groundfire" width="420"><br>
      <sub><b>Arte de abertura do Groundfire</b></sub>
    </td>
    <td align="center">
      <img src="media/img/readme-showcase.png" alt="Showcase visual do Groundfire" width="420"><br>
      <sub><b>Showcase visual — jogo e loja</b></sub>
    </td>
  </tr>
</table>

---

<a id="requisitos-de-hardware-e-software"></a>

## 💻 Requisitos de hardware e software

### Requisitos de software

| Item | Requisito |
|:---|:---|
| 🐍 Python | 3.10, 3.11, 3.12 ou 3.13 |
| 🖥️ Interface gráfica | Ambiente com suporte a janela Pygame |
| 📦 Dependências principais | `pygame`, `msgpack`, `mpgameserver` |
| 🖧 Sistema operacional | Windows, Linux, macOS ou WSL com suporte gráfico |
| 📄 Licença | MIT |

### Dependências do ambiente atual

As dependências estão centralizadas em [`requirements.txt`](requirements.txt) e também declaradas em [`pyproject.toml`](pyproject.toml):

| Pacote | Versão | Uso |
|:---|:---:|:---|
| `pygame` | `2.6.1` | Janela, entrada, renderização 2D e áudio |
| `msgpack` | `1.1.2` | Serialização de mensagens |
| `mpgameserver` | `0.2.4` | Infraestrutura do modo cliente/servidor |
| `ruff` | `0.15.7` | Lint e organização de imports em desenvolvimento |
| `mypy` | `1.19.1` | Checagem estática opcional em desenvolvimento |

### Requisitos práticos de hardware

| Recurso | Mínimo prático | Recomendado | Observações |
|:---|:---:|:---:|:---|
| CPU | 2 núcleos | 4+ núcleos | Pygame e simulação 2D rodam bem em máquinas comuns |
| RAM | 2 GB | 4+ GB | Suficiente para jogo local e testes |
| Armazenamento | 500 MB livres | 1 GB livre | Inclui `.venv`, dependências e assets |
| GPU | Não obrigatória | Aceleração básica | Depende do suporte local do SDL/Pygame |
| Tela | 1024 × 768 | 1280 × 720+ | O default atual usa 1024 × 768 |

> [!NOTE]
> Em Linux, pode ser necessário instalar bibliotecas do sistema usadas pelo SDL/Pygame, especialmente em ambientes mínimos ou servidores com interface gráfica reduzida.

---

<a id="instalacao-passo-a-passo"></a>

## 📦 Instalação passo a passo

> [!NOTE]
> A forma mais simples de usar o projeto é executar um dos scripts `run_game.*`. Eles procuram uma versão compatível do Python, criam ou reparam `.venv`, atualizam o `pip`, instalam dependências e iniciam o jogo.

### 1️⃣ Clonar o repositório

```bash
git clone https://github.com/p19091985/port-groundfire-for-python.git
cd port-groundfire-for-python
```

### 2️⃣ Instalação automática (recomendada)

<table>
<tr>
<td><b>🪟 Windows CMD</b></td>
<td><b>🪟 Windows PowerShell</b></td>
<td><b>🐧 Linux / 🍎 macOS / WSL</b></td>
</tr>
<tr>
<td>

```bat
run_game.bat
```

</td>
<td>

```powershell
.\run_game.ps1
```

</td>
<td>

```bash
./run_game.sh
```

</td>
</tr>
</table>

O fluxo automático executa, em ordem:

1. Procura Python 3.10 a 3.13
2. Cria `.venv` quando necessário
3. Recria `.venv` se o Python for incompatível
4. Atualiza `pip`
5. Instala [`requirements.txt`](requirements.txt)
6. Inicia o jogo pelo ponto de entrada local

### 3️⃣ Instalação manual

<details>
<summary>🔽 Expandir instruções de instalação manual</summary>

#### 3.1 Criar ambiente virtual

```bash
python -m venv .venv
```

#### 3.2 Ativar o ambiente virtual

**Linux / macOS / WSL**

```bash
source .venv/bin/activate
```

**Windows CMD**

```bat
.venv\Scripts\activate.bat
```

**Windows PowerShell**

```powershell
.venv\Scripts\Activate.ps1
```

#### 3.3 Instalar o pacote

```bash
python -m pip install --upgrade pip
pip install -e .
```

#### 3.4 Iniciar após instalação manual

```bash
groundfire
```

Alternativas equivalentes:

```bash
python -m groundfire.client
python src/main.py
```

</details>

---

<a id="como-iniciar-o-jogo"></a>

## ▶️ Como iniciar o jogo

| Modo | Comando |
|:---|:---|
| **Local recomendado** | `groundfire` |
| Forçar fluxo clássico local | `python -m groundfire.client --classic-local` |
| Forçar runtime canônico local | `python -m groundfire.client --canonical-local` |
| Com nome de jogador e IAs | `python -m groundfire.client --player-name Jogador --ai-players 2` |
| Smoke test (um frame) | `python -m groundfire.client --once` |

---

<a id="scripts-de-inicializacao"></a>

## 📜 Scripts de inicialização

| Arquivo | Função | Quando usar |
|:---|:---|:---|
| [`run_game.sh`](run_game.sh) | Prepara `.venv`, instala deps e inicia o jogo | 🐧 Linux / 🍎 macOS / WSL |
| [`run_game.bat`](run_game.bat) | Prepara `.venv`, instala deps e inicia o jogo | 🪟 Windows CMD |
| [`run_game.ps1`](run_game.ps1) | Prepara `.venv`, instala deps e inicia o jogo | 🪟 Windows PowerShell |
| [`scripts/run_quality_checks.py`](scripts/run_quality_checks.py) | Compilação, testes, lint e tipagem | Validação antes de publicar |
| [`scripts/profile_round_simulation.py`](scripts/profile_round_simulation.py) | Mede desempenho de simulação | Diagnóstico de performance |
| [`scripts/generate_readme_art.py`](scripts/generate_readme_art.py) | Gera arte usada no README | Manutenção de imagens |
| [`scripts/convert_legacy_tga_assets.py`](scripts/convert_legacy_tga_assets.py) | Auxilia conversão de assets históricos | Manutenção de assets |

> [!TIP]
> Use `run_game.*` para jogar, `scripts/run_quality_checks.py` para validar o projeto e os demais scripts quando estiver mantendo arte, assets ou desempenho.

---

<a id="jogabilidade"></a>

## 🎮 Jogabilidade

### Mecânicas centrais

- 🎯 Mira de artilharia com ângulo e potência
- 🌍 Gravidade influenciando trajetória dos projéteis
- 💥 Terreno destrutível com crateras e desabamentos
- 🚀 Tanques com movimento horizontal e jump jets
- 🛡️ Dano em área, escudo, fumaça, rastro e efeitos de explosão
- 💰 Pontuação e economia entre rodadas
- 🛒 Compra de armas e upgrades na loja
- 🤖 Adversários controlados por IA

### Armas disponíveis no port

| Arma | Ícone | Papel |
|:---|:---:|:---|
| `Shell` | 💣 | Projétil explosivo padrão |
| `Machine Gun` | 🔫 | Rajada rápida com dano baixo por disparo |
| `MIRV` | 🎆 | Projétil que se divide em subprojéteis |
| `Missile` | 🚀 | Projétil guiado |
| `Nuke` | ☢️ | Explosão de grande raio e alto impacto |

### Fluxo recomendado de partida

```
1. 🏁 Iniciar pelo menu local clássico
2. 👥 Configurar jogadores humanos e IAs
3. 🎯 Ajustar ângulo e potência
4. 💥 Disparar observando vento, terreno e distância
5. 🛡️ Usar movimento, jump jets e escudo para sobreviver
6. 🛒 Comprar armas e upgrades entre rodadas
7. 🏆 Repetir até definir o vencedor
```

---

<a id="controles-padrao"></a>

## 🕹️ Controles padrão

Os controles podem ser ajustados em [`conf/controls.ini`](conf/controls.ini) ou pelos menus internos de controle.

| Ação | Tecla (Jogador 1) |
|:---|:---:|
| 🔥 Atirar | `Space` |
| ⬆️ Aumentar ângulo do canhão | `W` |
| ⬇️ Diminuir ângulo do canhão | `S` |
| ⬅️ Girar canhão para a esquerda | `A` |
| ➡️ Girar canhão para a direita | `D` |
| ◀️ Mover tanque para a esquerda | `J` |
| ▶️ Mover tanque para a direita | `L` |
| 🚀 Jump jets | `I` |
| 🛡️ Escudo | `K` |
| 🔄 Próxima arma | `O` |
| 🔄 Arma anterior | `U` |

> O arquivo [`conf/controls.ini`](conf/controls.ini) também contém layouts de joystick para até **oito jogadores**. Os códigos seguem o mapeamento usado pelo Pygame/SDL no ambiente local.

---

<a id="configuracao-do-jogo"></a>

## ⚙️ Configuração do jogo

As configurações principais ficam em [`conf/options.ini`](conf/options.ini).

| Seção | O que controla |
|:---|:---|
| `[Graphics]` | Largura, altura, profundidade de cor, FPS visível e tela cheia |
| `[Effects]` | Fade de explosão, whiteout e rastro |
| `[Terrain]` | Quantidade de fatias, largura e queda do terreno |
| `[Quake]` | Duração, intervalo, amplitude e frequência de terremotos |
| `[Shell]` `[Nuke]` `[Missile]` `[Mirv]` `[MachineGun]` | Dano, cooldown, raio, velocidade e parâmetros de armas |
| `[Tank]` | Velocidade, tamanho, ângulo, potência, gravidade, boost e combustível |
| `[Price]` | Preços de armas e upgrades |
| `[Colours]` | Cores dos tanques |
| `[Interface]` | Modo do menu local, como `classic` ou runtime canônico |

> [!TIP]
> Para experimentar balanceamento, altere os valores em `conf/options.ini` e reinicie o jogo. Mantenha mudanças de gameplay acompanhadas por testes quando elas forem parte de uma contribuição.

---

<a id="modo-local-e-modo-online"></a>

## 🌐 Modo local e modo online

### 🖥️ Jogo local

O modo local é o caminho principal de uso atual:

```bash
groundfire
```

O valor `LocalMenuMode=classic` em [`conf/options.ini`](conf/options.ini) faz o jogo abrir com a apresentação clássica por padrão.

### 🖧 Servidor headless

O projeto também inclui um servidor autoritativo sem interface gráfica:

```bash
groundfire-server --server-name "Groundfire Server"
```

Ou, sem console script:

```bash
python -m groundfire.server --host 0.0.0.0 --port 45000
```

### 🔗 Cliente conectado

Para conectar em um servidor:

```bash
groundfire --connect 127.0.0.1:45000 --player-name Jogador
```

Se a porta for omitida, o cliente usa a porta padrão definida no protocolo de rede.

### 🔑 Chaves do transporte seguro

O servidor usa caminhos padrão em `conf/network/` para chave privada e chave pública. Quando necessário, esses arquivos são criados pelo fluxo do servidor.

> [!IMPORTANT]
> O modo de rede existe para evolução e testes. Para jogar sem atrito, prefira o modo local até que a experiência online esteja completamente estabilizada.

---

<a id="estrutura-do-repositorio"></a>

## 📂 Estrutura do repositório

```
port-groundfire-for-python/
├── 📁 conf/                configurações do jogo, controles e mapeamento de assets
├── 📁 data/                imagens, sons, fonte e sprites do jogo
├── 📁 media/
│   └── 📁 img/             capturas e imagens geradas para o README
├── 📁 groundfire/          wrappers públicos para execução como pacote
├── 📁 scripts/             ferramentas de QA, arte, assets e perfilamento
├── 📁 src/                 código principal do port Python
│   └── 📁 groundfire/      runtime canônico organizado por domínio
├── 📁 tests/               testes automatizados
├── 🦇 run_game.bat         inicializador Windows CMD
├── ⚡ run_game.ps1         inicializador Windows PowerShell
├── 🐧 run_game.sh          inicializador Linux/macOS/WSL
├── 📋 pyproject.toml       metadados, scripts e configuração de ferramentas
└── 📋 requirements.txt     dependências de runtime e desenvolvimento
```

### Conteúdo técnico incorporado

| Conteúdo | Localização |
|:---|:---|
| [`cpp_output.txt`](cpp_output.txt) | Registro de execução histórica para comparação |
| Análise arquitetural 2026 | [Documentação Técnica ↓](#documentacao-tecnica-incorporada) |
| Roadmap de refatoração 2026 | [Documentação Técnica ↓](#documentacao-tecnica-incorporada) |
| Modo online seguro | [Documentação Técnica ↓](#documentacao-tecnica-incorporada) |
| Playtest do controle clássico | [Documentação Técnica ↓](#documentacao-tecnica-incorporada) |

---

<a id="arquitetura-de-manutencao"></a>

## 🏗️ Arquitetura de manutenção

O projeto mantém duas camadas importantes:

- **Camada de compatibilidade histórica** em [`src/`](src) — preserva nomes e organização próximos do port inicial
- **Camada canônica** em [`src/groundfire/`](src/groundfire) — separa aplicação, simulação, rede, renderização, entrada e gameplay

### Mapa de módulos principais

| Caminho | Responsabilidade |
|:---|:---|
| [`src/main.py`](src/main.py) | Entrada local de compatibilidade |
| [`groundfire/client.py`](groundfire/client.py) | Wrapper público do cliente |
| [`groundfire/server.py`](groundfire/server.py) | Wrapper público do servidor |
| [`src/groundfire/client.py`](src/groundfire/client.py) | Parser e orquestração do cliente canônico |
| [`src/groundfire/server.py`](src/groundfire/server.py) | Parser e orquestração do servidor headless |
| [`src/groundfire/app/`](src/groundfire/app) | Fluxos de aplicação local, cliente, servidor e frontend |
| [`src/groundfire/sim/`](src/groundfire/sim) | Mundo, terreno, registro e partida simulada |
| [`src/groundfire/gameplay/`](src/groundfire/gameplay) | Controlador de partida e constantes de gameplay |
| [`src/groundfire/network/`](src/groundfire/network) | Mensagens, codec, LAN, estado do cliente e backend |
| [`src/groundfire/render/`](src/groundfire/render) | Terreno, cena, HUD, primitivas e visual de entidades |
| [`src/groundfire/input/`](src/groundfire/input) | Comandos e controles |
| [`src/game.py`](src/game.py) | Loop e transições do fluxo clássico |
| [`src/tank.py`](src/tank.py) | Movimentação, dano, disparo e ciclo de vida do tanque |
| [`src/aiplayer.py`](src/aiplayer.py) | Mira, escolha de alvo e comportamento da IA |
| [`src/weapons_impl.py`](src/weapons_impl.py) | Implementações concretas de armas |
| [`src/shopmenu.py`](src/shopmenu.py) | Compra entre rodadas |

### Princípios de manutenção

- 🔒 Preservar nomes e comportamentos quando isso ajuda a comparar com o jogo original
- 📦 Mover regras compartilhadas para `src/groundfire/` quando houver ganho claro
- 🧱 Manter renderização, simulação, entrada e rede separadas
- ✅ Acompanhar mudanças de comportamento com testes automatizados
- ⚠️ Evitar refatorações grandes sem uma razão verificável

---

<a id="documentacao-tecnica-incorporada"></a>

## 📖 Documentação técnica incorporada

> [!NOTE]
> Esta seção consolida o conteúdo dos arquivos Markdown técnicos que antes ficavam separados. Os arquivos originais foram incorporados aqui para manter o histórico técnico em um único documento. Clique para expandir cada seção.

---

<details>
<summary><h3>📐 Análise Arquitetural 2026</h3></summary>

<a id="analise-arquitetural-2026"></a>

> **Status desta entrega:** Esta etapa contem analise, planejamento e preparacao. Nenhuma refatoracao estrutural do runtime principal foi iniciada. O unico artefato executavel novo desta etapa e um utilitario isolado de conversao de assets `.tga`.

#### Escopo e metodo

Base analisada:

- `src/`: 39 modulos Python, 6591 linhas.
- `tests/`: 5 arquivos Python, 1164 linhas.
- `data/`: 22 assets, sendo 12 `.tga` e 10 `.wav`.
- `scripts/`: 1 script auxiliar que tambem consome `.tga`.
- teste executado: `python -m unittest discover -s tests -p "test_*.py"` -> 22 testes OK.
- referencia C++ consultada via `git show` em `groundfire-0.25/src/game.cc`, `tank.cc`, `interface.cc` e `font.cc`.

Observacao: a arvore `groundfire-0.25/` esta removida no worktree atual. Para nao interferir nas mudancas locais do usuario, a comparacao com o legado foi feita apenas por leitura do `HEAD`, sem restaurar nada no disco.

#### 1. Visao geral do estado atual

##### Estrutura do projeto

```text
port-groundfire-for-python/
|- conf/        configuracao de graficos e controles
|- data/        texturas TGA e sons WAV
|- media/img/   imagens do README
|- scripts/     tooling auxiliar
|- src/         port Python/Pygame
|- tests/       testes de fidelidade e fluxo
|- cpp_output.txt
|- requirements.txt
`- run_game.(bat|ps1|sh)
```

##### Dependencias

Dependencia declarada:

- `pygame==2.6.1`

Ausencias relevantes para 2026:

- sem `pyproject.toml`;
- sem CI visivel;
- sem linter/formatter/type-check;
- sem empacotamento moderno;
- sem infraestrutura de rede;
- sem manifest de assets;
- sem ferramentas de profiling ou replay.

##### Ponto de entrada e fluxo principal

Ponto de entrada:

- `src/main.py`

Fluxo atual:

1. script de launch cria `.venv`, instala dependencias e executa `src/main.py`;
2. `src/main.py` ajusta `sys.path`, instancia `Game()` e chama `loop_once()` em loop;
3. `Game.__init__()` carrega configuracao, interface, texturas, controles, fonte, som, um `Landscape` inicial e `MainMenu`;
4. `Game.loop_once()` calcula `dt` por `time.time()`, atualiza menus ou round e desenha na mesma passagem.

##### Modulos principais

- `game.py`: bootstrap, maquina de estados, rounds, recursos e lista de entidades.
- `interface.py`: janela, input, texturas e conversao de coordenadas.
- `landscape.py`: geracao de terreno, explosoes e colisao.
- `tank.py`: movimento, aim, armas, dano e HUD.
- `weapon.py` + `weapons_impl.py`: armas e cooldown/ammo.
- `player.py`, `humanplayer.py`, `aiplayer.py`: ownership do tanque e origem do input.
- `shell.py`, `missile.py`, `mirv.py`, `machinegunround.py`: balistica.
- `menu.py` e menus derivados: UI e fluxo de partida.
- `font.py`: atlas de fonte via textura.
- `sounds.py` e `soundentity.py`: audio.

##### Componentes herdados do design em C++

O port preserva fortemente a estrutura original:

- `Game` replica `cGame` como orquestrador central.
- `Tank` replica `cTank` com regras, armas, input e HUD.
- `Landscape` preserva o modelo em slices/chunks.
- o fluxo de menus segue objetos com `update()`/`draw()`.
- a lista unica de entidades reproduz `list<cEntity *>`.
- texturas e sons sao acessados por IDs inteiros.
- varios comentarios e decisoes de API foram transpostos quase literalmente do C++.

##### Padroes inadequados para um jogo Python moderno

- codigo flat em `src/`, sem pacotes por dominio;
- forte acoplamento a `Game`;
- simulacao, render, input e UI misturados;
- assets hardcoded por caminho e ID magico;
- ausencia de tick fixo;
- ausencia de serializacao de estado;
- ausencia de fronteira entre cliente visual e servidor futuro.

#### 2. Diagnostico tecnico

<details>
<summary>Expandir diagnóstico completo</summary>

##### Achados principais

1. `Game` e um god object. Ele centraliza bootstrap, recursos, estados, menus, landscape, players, entidades e explosoes.
2. A simulacao esta acoplada ao relogio real. `Game.loop_once()` usa `time.time()`, e os projetis usam `launch_time` absoluto + `game.get_time()`.
3. O port divergiu de partes importantes do C++. No C++, `cGame` chama `readSettings()` para armas, quake, trail, blast, mirv e missile; no Python esses metodos existem, mas nao sao chamados.
4. Ha configuracao parcialmente morta. `Graphics.ShowFPS` existe no INI e no C++, mas nao e respeitado no port atual.
5. O pipeline de render esta espalhado. Varios modulos chamam `pygame.draw.*`, `pygame.transform.*`, `pygame.Surface(...)` e acessam `._window` diretamente.
6. Tanques sao desenhados duas vezes. Eles estao em `self._players[i].get_tank()` e tambem em `self._entity_list`; `Game._draw_round()` desenha ambos.
7. Ha bugs fora da cobertura atual. `ShopMenu` e `WinnerMenu` chamam `get_command(...)` sem o segundo parametro exigido por `HumanPlayer`.
8. O bootstrap atual cria `Landscape` no construtor. No C++ o landscape so nasce ao iniciar o round; no port atual ele existe mesmo quando o jogo esta parado em menu.
9. `Font` recarrega `fonts.tga`. `Game` ja registra a textura 3 e `Font` carrega o mesmo arquivo outra vez, duplicando I/O e responsabilidades.
10. Ha risco visual em `ROUND_STARTING`. `loop_once()` chama `start_draw()` no inicio do frame e chama `start_draw()` outra vez antes do texto de "Get Ready", o que pode limpar a cena recem-desenhada.

##### Code smells

- classes grandes: `Game`, `Tank`, `Landscape`, `Font`, `PlayerMenu`, `ShopMenu`;
- comentarios de raciocinio incompleto e placeholders no codigo de producao;
- uso extensivo de atributos internos de outros objetos;
- destruidores `__del__` para recursos criticos (`Sound`, `Interface`, `Game`, `Quake`);
- parsers custom de configuracao e controles;
- `sys.path.append(...)` no entrypoint.

##### Acoplamento excessivo

Os acoplamentos mais perigosos sao:

- `Game` <-> todos os subsistemas;
- gameplay <-> renderer;
- input <-> simulacao;
- menus <-> dados internos de jogador, tanque, round e economia.

##### Duplicacao de codigo

Duplicacoes relevantes:

- `_draw_transparent_poly()` repetido em quase todos os menus e em `tank.py`;
- fluxo de projetil repetido entre shell, MIRV, missile e machine gun;
- tratamento visual de scale/rotate/blit repetido em efeitos, botoes e score menu;
- mapeamento de assets espalhado entre `Game`, `Font`, `Weapon`, `Menu` e scripts.

##### Responsabilidades mal distribuidas

- `Tank.draw()` desenha tanque e HUD.
- `Game.explosion()` mistura terreno, efeito visual, audio e dano.
- `ShopMenu` aplica compras diretamente.
- `Player.end_round()` calcula score e dinheiro sem um servico de regras.
- `Font` tambem age como loader de asset.

##### Riscos arquiteturais

- refatorar `Game`, `Tank` ou `Landscape` afeta boa parte do projeto;
- nao existe estado de mundo serializavel;
- nao existem IDs estaveis de entidades;
- nao existe event bus;
- o uso de tempo real inviabiliza rede robusta e replays confiaveis;
- o subsistema de recursos nao separa source asset, runtime asset e cache.

##### Limitacoes para multiplayer

Bloqueios atuais:

- sem tick fixo;
- sem command buffer;
- sem protocolo, sessao ou discovery;
- sem cliente/servidor separado;
- sem serializacao de estado;
- sem snapshots ou deltas;
- sem modo headless.

##### Limitacoes do pipeline grafico e de assets

O projeto usa 12 `.tga` em runtime e 2 deles tambem em script auxiliar de docs. O carregamento atual faz `pygame.image.load(...)` por caminho hardcoded e expoe superficies cruas por ID inteiro. Isso e suficiente para um port preservacionista, mas nao para um pipeline moderno reproduzivel.

Todos os `.tga` atuais sao TGA RLE (`image_type=10`) em 24 ou 32 bpp. O formato e historico e valido, mas pouco atraente para 2026 em Pygame por:

- toolchain mais estreita;
- menor ergonomia em conversores e validadores;
- potencial confusao de orientacao/origin;
- nenhuma vantagem operacional significativa frente a PNG nesta base.

</details>

#### 3. Avaliacao de prontidao para 2026

<details>
<summary>Expandir avaliação completa</summary>

##### O que falta

- pacote modular por dominio;
- simulacao pura e deterministica;
- asset pipeline reproduzivel;
- layer de rede;
- modo headless;
- automacao de qualidade;
- observabilidade minima;
- infraestrutura de replays/profiling.

##### Praticas esperadas em 2026

- nucleo de simulacao separado de renderer;
- tick fixo com render interpolado;
- assets com manifest e validacao;
- cliente/servidor com protocolo versionado;
- testes em unidade, integracao, rede e regressao visual;
- build tooling e CI padronizados.

##### O que esta obsoleto

- `.tga` como formato primario de runtime;
- IDs inteiros de textura/som;
- relogio de parede como base da simulacao;
- render imediatista espalhado;
- acesso a `._window` e atributos internos como API informal.

##### O que deve ser refeito

- loop principal;
- subsistema de assets;
- camada de render;
- camada de input;
- fluxo de menus/UI;
- organizacao do codigo;
- serializacao de estado;
- arquitetura de rede.

##### O que pode ser aproveitado

- formulas balisticas;
- modelo de terreno destrutivel;
- regras de dano, score e economia;
- testes atuais como contrato de comportamento;
- estrutura conceitual de armas, tanques e rounds;
- referencia historica com o C++.

</details>

#### 4. Proposta de nova arquitetura

##### Organizacao modular sugerida

```text
src/groundfire/
|- app/
|- core/
|- sim/
|- gameplay/
|- render/
|- assets/
|- input/
|- audio/
|- ui/
|- network/
`- tools/
```

##### Separacao de responsabilidades

| Módulo | Responsabilidade |
|:---|:---|
| `core` | Config, IDs, clock, logging e eventos |
| `sim` | Mundo, entidades, terreno, armas e sistemas |
| `gameplay` | Round flow, scoring, economia e turn ownership |
| `render` | Adaptador visual do estado |
| `assets` | Manifest, loader, cache e validacao |
| `input` | Mapeamento de hardware para comandos |
| `audio` | Sound bank e consumo de eventos |
| `ui` | Menus, HUD e presenters |
| `network` | Discovery, sessao, protocolo, client, server e replication |

##### Modelo de execucao recomendado

- Simulacao em tick fixo, por exemplo 60 Hz
- Render independente com interpolacao
- Input local convertido em `PlayerCommand`
- Mundo atualizado apenas por comandos e eventos
- Renderer e audio consumindo snapshots/eventos, nao chamando regras diretamente

##### Arquitetura cliente/servidor proposta

- Servidor dedicado autoritativo
- Cliente responsavel por render, UI, audio e input local
- Comandos do jogador enviados ao servidor
- Terreno, score, economia e round decididos apenas no servidor
- Entidades com IDs de rede e snapshots/eventos versionados

#### 5. Plano especifico para rede

<details>
<summary>Expandir plano de rede</summary>

Modelo recomendado, inspirado no classico cliente/servidor de jogos como CS 1.6, mas adaptado ao genero do Groundfire:

- servidor autoritativo;
- cliente manda comandos, nao estado canonico;
- snapshots e eventos mantem a visao do cliente;
- predicao local limitada onde fizer sentido;
- reconciliacao leve para missiles guiados;
- turn-lock no servidor para impedir comandos fora da vez.

Pre-requisitos antes de implementar rede de fato:

- tick fixo;
- RNG controlado pela partida;
- mundo serializavel;
- IDs estaveis de entidades;
- event bus;
- modo headless.

##### Suporte LAN e servidores remotos

- descoberta LAN via UDP broadcast ou multicast;
- conexao direta por `host:port` para servidores dedicados;
- handshake com versao de protocolo, seed da partida e token de sessao.

##### Serializacao e sincronizacao de estado

- snapshots para tanques e estado de partida;
- eventos explicitos para spawn, explosao, compra e fim de round;
- seed inicial + deltas de terreno quando necessario;
- comandos pequenos para aim/fire e stream de controle para missile guiado.

</details>

#### 6. Plano de substituicao dos arquivos `.tga`

<details>
<summary>Expandir plano de migração de assets</summary>

##### Onde `.tga` e usado

- `src/game.py`: mapa principal de texturas.
- `src/font.py`: `fonts.tga`.
- `scripts/generate_readme_art.py`: `menuback.tga` e `logo.tga`.

##### Formato alvo recomendado

- **`PNG`** lossless como formato canonico de runtime e source asset.
- Futuro opcional: `KTX2/BasisU`, apenas se o renderer migrar para uma pilha realmente GPU-centric.

##### Estrategia de migracao

1. Converter `.tga` para `.png` em arvore paralela
2. Validar dimensoes, alpha e orientacao
3. Gerar manifest origem → destino
4. Trocar runtime para resolver assets por nome semantico
5. Eliminar IDs magicos e dupla carga da fonte
6. So depois remover referencias a `.tga`

##### Utilitario entregue

`scripts/convert_legacy_tga_assets.py` — não altera originais, gera `.png` em pasta separada, cria manifesto JSON e valida o resultado.

</details>

#### 7. Conclusao tecnica

O projeto atual e um port funcional e valioso como preservacao, mas ainda nao e uma base adequada para expansao multiplayer, LAN, servidor dedicado e pipeline moderno de assets. A melhor estrategia nao e reescrever tudo de uma vez; e extrair um nucleo puro de simulacao, desacoplar render/input/audio, modernizar assets e so entao ligar a camada de rede.

</details>

---

<details>
<summary><h3>🗺️ Roadmap de Refatoração 2026</h3></summary>

<a id="roadmap-de-refatoracao-2026"></a>

> **Status desta entrega:** Este roadmap descreve a execucao sugerida da modernizacao. A refatoracao principal ainda nao foi iniciada nesta etapa.

#### Premissas

- Preservar a jogabilidade protegida pelos testes existentes
- Nao quebrar o jogo atual sem trilha de migracao
- Priorizar isolamento de simulacao, assets e estado antes de rede
- Manter o runtime jogavel ao fim de cada fase

#### Fases do Roadmap

| Fase | Objetivo | Dependências |
|:---:|:---|:---|
| **0** | Auditoria e mapeamento do codigo | Nenhuma |
| **1** | Hardening mínimo antes da reorganização | Fase 0 |
| **2** | Isolamento de módulos críticos | Fase 1 |
| **3** | Reorganização arquitetural | Fase 2 |
| **4** | Modernização do pipeline de assets | Utilitário de conversão validado |
| **5** | Refatoração para tick fixo | Fases 2, 3 e 4 |
| **6** | Preparação para multiplayer | Fase 5 |
| **7** | Protótipo LAN e servidor dedicado | Fase 6 |
| **8** | Testes, profiling e hardening | Fases anteriores |

<details>
<summary>Expandir detalhes de cada fase</summary>

##### Fase 0 — Auditoria e mapeamento do codigo

- **Objetivo:** consolidar inventario de modulos, assets, estados, dependencias e hotspots.
- **Afetados:** `src/*`, `tests/*`, `conf/*`, `data/*`
- **Riscos:** subestimar acoplamentos escondidos; ignorar divergencias com o C++.
- **Critérios:** inventario fechado; mapa de riscos aprovado; baseline documentada.

##### Fase 1 — Hardening minimo

- **Objetivo:** corrigir desvios estruturais que atrapalham a extracao do nucleo.
- **Afetados:** `game.py`, `shopmenu.py`, `winnermenu.py`, `font.py`, `weapons_impl.py`, `missile.py`, `mirv.py`, `quake.py`, `blast.py`, `trail.py`
- **Riscos:** regressao de fidelidade se faltar cobertura em UI e render.
- **Critérios:** `read_settings()` corretamente chamado; input humano sem quebras; duplicacao de desenho saneada.

##### Fase 2 — Isolamento de modulos criticos

- **Objetivo:** separar simulacao de infraestrutura.
- **Afetados:** `game.py`, `tank.py`, `player.py`, `humanplayer.py`, `aiplayer.py`, `weapon.py`, `weapons_impl.py`, `shell.py`, `missile.py`, `mirv.py`, `machinegunround.py`, `landscape.py`
- **Riscos:** circularidades temporarias; regressao na ordem de update.
- **Critérios:** gameplay sem depender de `pygame` diretamente; input vira comando; entidades reduzem dependencia de `Game`.

##### Fase 3 — Reorganizacao arquitetural

- **Objetivo:** mover o projeto para pacotes por dominio com interfaces claras.
- **Riscos:** grande volume de mudancas de imports; conflitos se feito em patch grande.
- **Critérios:** pacote `groundfire/` estabelecido; imports limpos; fronteiras claras entre módulos.

##### Fase 4 — Modernizacao do pipeline de assets

- **Objetivo:** substituir `.tga`, introduzir manifest e separar source/runtime assets.
- **Riscos:** inversao visual por orientacao; perda de alpha; regressao em paths hardcoded.
- **Critérios:** assets `.png` convertidos e validados; runtime resolve por manifest; `.tga` sai da trilha principal.

##### Fase 5 — Tick fixo

- **Objetivo:** tornar a simulacao deterministica para rede, replays e servidor dedicado.
- **Riscos:** maior chance de regressao de gameplay; mudancas em trajetorias.
- **Critérios:** loop usa tick fixo; RNG explicito; projetis sem `time.time()`; testes de balistica passam.

##### Fase 6 — Preparacao para multiplayer

- **Objetivo:** introduzir contratos internos de rede sem ligar a stack completa.
- **Riscos:** schema de mensagens ruim pode engessar implementacao futura.
- **Critérios:** entidades com IDs estaveis; comandos serializaveis; eventos de dominio definidos.

##### Fase 7 — Prototipo LAN e servidor dedicado

- **Objetivo:** provar a arquitetura de rede em ambiente controlado.
- **Riscos:** sincronizacao de terreno e missiles guiados; bugs de sessao.
- **Critérios:** servidor headless funcional; cliente lista partidas LAN; round simples entre dois clientes.

##### Fase 8 — Testes, profiling e hardening

- **Objetivo:** estabilizar o sistema para evolucao continuada.
- **Critérios:** suite por camada; testes de rede; benchmarks; CI funcionando.

</details>

#### Roadmap de rede

| Marco | Objetivo | Entregas-chave |
|:---:|:---|:---|
| **N1** | Contratos de comando e evento | Schema versionado, IDs estáveis, eventos de round/disparo/dano |
| **N2** | Descoberta LAN e handshake | Beacon UDP, browser LAN, handshake com versão/seed/token |
| **N3** | Servidor autoritativo mínimo | Servidor dedicado, replicação básica, sync de score/turnos |
| **N4** | Latência e reconciliação | Interpolação, predição local, métricas de rede |

#### Prioridades executivas

| Prazo | Fases | Foco |
|:---|:---:|:---|
| 🔴 Curto prazo | 1 — 2 | Corrigir bugs estruturais e extrair simulação |
| 🟡 Médio prazo | 3 — 5 | Reorganizar projeto, assets e tick fixo |
| 🟢 Longo prazo | 6 — 8 | Rede, servidor dedicado e hardening |

</details>

---

<details>
<summary><h3>🔐 Modo Online Seguro</h3></summary>

<a id="modo-online-seguro"></a>

The online client/server path now uses `mpgameserver` as the secure transport layer. This keeps the existing Groundfire match logic and interface flow, but moves the network transport to an authenticated and encrypted UDP connection.

#### Key Files

| Arquivo | Propósito |
|:---|:---|
| `conf/network/server_root_private.pem` | Chave privada do servidor |
| `conf/network/server_root_public.pem` | Chave pública do servidor |

When the server starts, it creates the private/public key pair automatically if the files do not exist.

#### Start The Server

```powershell
python -m src.groundfire.server
```

Custom key paths are also supported:

```powershell
python -m src.groundfire.server --server-private-key custom/private.pem --server-public-key custom/public.pem
```

#### Connect A Client

```powershell
python -m src.groundfire.client --connect 127.0.0.1:27015 --server-public-key conf/network/server_root_public.pem
```

#### Security Notes

- 🔒 The server private key stays on the server.
- 🔑 The client uses the server public key to authenticate the secure handshake.
- ⛔ If the trusted public key file is missing, the client refuses the connection instead of falling back to insecure mode.

</details>

---

<details>
<summary><h3>🎮 Playtest do Controle Clássico</h3></summary>

<a id="playtest-do-controle-classico"></a>

Use this checklist to validate the classic local menu flow on real hardware without changing the classic UI.

#### Launch

```powershell
python -m src.groundfire.client --canonical-local --player-name "Controller Test"
```

#### Keyboard 2

1. Open `Start Game`.
2. Leave exactly one human player enabled.
3. Change the controller selector to `Keyboard2`.
4. Start a round.
5. Confirm the tank responds only to the `Keyboard2` bindings from `conf/controls.ini`.

#### Joysticks

1. Repeat the same setup with `Joystick1`.
2. Press `Fire` on an unassigned joystick from the player-select screen and confirm it auto-joins the next free player row.
3. Start a round and confirm movement, aiming, weapon switching, and fire all route through the selected joystick.
4. Repeat for any additional joystick layouts you want to certify.

#### Legacy Fallback

1. Enable two human players in `Start Game`.
2. Assign different controllers, for example `Keyboard1` and `Keyboard2` or `Keyboard1` and `Joystick1`.
3. Start the match.
4. Confirm the game hands off to the legacy local loop and begins the round with both players configured.

#### Regression Notes

If any step fails, capture:

- Which controller label was selected in the classic menu
- Whether the player was added by click or by pressing `Fire`
- Whether the failure happened before the round, during the round, or during the legacy fallback handoff

</details>

---

<a id="testes-automatizados-e-qa"></a>

## 🧪 Testes automatizados e QA

### Rodar a suite completa

```bash
python -m unittest discover -s tests -p "test_*.py"
```

### Rodar verificações de qualidade

```bash
python scripts/run_quality_checks.py
```

Esse script executa:

| Verificação | O que faz |
|:---|:---|
| `compileall` | Valida sintaxe importável em `src`, `tests`, `scripts` e `groundfire` |
| `unittest` | Roda a suite automatizada |
| `ruff` | Roda lint quando a ferramenta está disponível |
| `mypy` | Roda tipagem quando a ferramenta está disponível |

<details>
<summary>🔽 Testes direcionados e áreas cobertas</summary>

### Testes direcionados úteis

```bash
python -m unittest tests.test_port_fidelity
python -m unittest tests.test_fuzz_gameplay
python -m unittest tests.test_landscape_fidelity
python -m unittest tests.test_groundfire_entrypoints
python -m unittest tests.test_lan_discovery
```

### Áreas cobertas pela suite

| Área | Exemplos de testes |
|:---|:---|
| Fidelidade do port | `test_port_fidelity`, `test_replicated_scene` |
| Terreno e simulação | `test_landscape_fidelity`, `test_gamesimulation`, `test_fixedstep` |
| Fluxo de jogo | `test_gameflow`, `test_gamesession`, `test_match_controller` |
| Renderização e HUD | `test_gamerenderer`, `test_gamehudrenderer`, `test_gamegraphics` |
| Entrada e comandos | `test_commandintents`, `test_canonical_local_menu` |
| Rede | `test_networkprotocol`, `test_networkstate`, `test_groundfire_codec`, `test_lan_discovery` |
| Portabilidade | `test_portability`, `test_runtime_portability` |

</details>

---

<a id="solucao-de-problemas-frequentes"></a>

## 🔧 Solução de problemas frequentes

<details>
<summary><b>🖥️ O Pygame não abre janela</b></summary>

- Confirme que você está em uma sessão gráfica
- Em WSL, confirme que há suporte a WSLg ou servidor X configurado
- Em Linux mínimo, instale bibliotecas do SDL/Pygame pelo gerenciador do sistema

</details>

<details>
<summary><b>🐍 O script diz que o Python é incompatível</b></summary>

Use Python 3.10, 3.11, 3.12 ou 3.13. Os scripts procuram automaticamente por:

```text
python3.13, python3.12, python3.11, python3.10, python3, python
```

</details>

<details>
<summary><b>📁 A .venv ficou quebrada</b></summary>

Execute novamente o script do seu sistema:

```bash
./run_game.sh        # Linux / macOS / WSL
run_game.bat         # Windows CMD
.\run_game.ps1       # Windows PowerShell
```

O inicializador tenta reparar ou recriar o ambiente quando detecta incompatibilidade.

</details>

<details>
<summary><b>⚙️ O jogo abre em um modo local inesperado</b></summary>

Verifique a chave em [`conf/options.ini`](conf/options.ini):

```ini
[Interface]
LocalMenuMode=classic
```

Você também pode forçar pela linha de comando:

```bash
python -m groundfire.client --classic-local
python -m groundfire.client --canonical-local
```

</details>

<details>
<summary><b>🌐 O servidor não conecta</b></summary>

- Confirme host e porta usados no servidor
- Rode cliente e servidor na mesma máquina com `127.0.0.1` para isolar problema de rede
- Verifique firewall local
- Confira se o servidor terminou a criação das chaves em `conf/network/`

</details>

---

<a id="creditos-e-preservacao-historica"></a>

## 🏆 Créditos e preservação histórica

> Esta seção é destacada porque o jogo original merece atribuição clara.

| | Crédito |
|:---|:---|
| 🎮 Jogo original, design, programação e código C++ | **Tom Russell** |
| 📦 Projeto original | **Groundfire v0.25** |
| 🌐 Site histórico oficial | [groundfire.net](http://www.groundfire.net/) |
| 📅 Timeline histórica | `v0.25` publicada em `15 May 2004`, atualizada em `20 Apr 2006` |
| 📧 Contato histórico | `tom@groundfire.net` |
| 🐍 Port Python e preservação | [p19091985](https://github.com/p19091985) |

> O site histórico descreve Groundfire como um jogo livre e open-source para Windows/Linux, criado por Tom Russell e inspirado em *Death Tank*, do Sega Saturn.

<p align="center">
  <a href="http://www.groundfire.net/" title="Visitar o site histórico do Groundfire">
    <img src="media/img/siteTom.png" alt="Captura do site histórico do Groundfire criado por Tom Russell" width="800">
  </a>
  <br>
  <sub>Site histórico oficial do Groundfire, criado por Tom Russell.</sub>
</p>

<p align="center"><em>Se você chegou até aqui porque gostava do Groundfire original, este repositório existe porque esse trabalho vale a preservação.</em></p>

---

<a id="licenca"></a>

## 📄 Licença

Este repositório é distribuído sob a licença **MIT**. Consulte [`LICENSE`](LICENSE) para o texto completo.

---

<p align="center">
  <strong>🔥 Groundfire vive aqui como memória jogável: um clássico de artilharia preservado em Python. 🔥</strong>
</p>

---

<br>

<h1 align="center">
<p align="center">
  <kbd><a href="#portugues">🇧🇷 Português</a></kbd>&nbsp;&nbsp;
  <kbd><a href="#english">🇬🇧 English</a></kbd>
</p>
</h1>

<a id="english"></a>

<h2 align="center">🇬🇧 English</h2>

<p align="center"><strong>A Python/Pygame port of Groundfire v0.25, focused on preservation, classic gameplay, and modern compatibility.</strong></p>

<p align="center"><code>Current package version: 0.25.0</code></p>

<p align="center"><em>Groundfire is a classic artillery tank game with destructible terrain, ballistic combat, between-round economy, special weapons, AI opponents, and local or client/server execution.</em></p>

> [!NOTE]
> GitHub READMEs do not run JavaScript, so the language buttons above work as navigation anchors between the Portuguese and English sections.

---

### 📑 Table Of Contents

| | Section | | Section |
|---|---|---|---|
| 🎯 | [What Is This Project?](#what-is-this-project) | 🎮 | [Gameplay](#gameplay-en) |
| 🖼️ | [Game Art And Screenshots](#game-art-and-screenshots) | 🕹️ | [Default Controls](#default-controls) |
| 💻 | [Hardware And Software Requirements](#hardware-and-software-requirements) | ⚙️ | [Game Configuration](#game-configuration) |
| 📦 | [Step-By-Step Installation](#step-by-step-installation) | 🌐 | [Local And Online Modes](#local-and-online-modes) |
| ▶️ | [How To Start The Game](#how-to-start-the-game) | 📂 | [Repository Layout](#repository-layout) |
| 📜 | [Launch Scripts](#launch-scripts) | 🏗️ | [Maintenance Architecture](#maintenance-architecture) |
| 📖 | [Incorporated Technical Documentation](#incorporated-technical-documentation-en) | 🧪 | [Automated Tests And QA](#automated-tests-and-qa) |
| 🔧 | [Troubleshooting](#troubleshooting) | 🏆 | [Credits And Historical Preservation](#credits-and-historical-preservation) |
| 📄 | [License](#license-en) | | |

---

<a id="what-is-this-project"></a>

## 🎯 What Is This Project?

**Groundfire — Python Port** is a Python/Pygame adaptation of **Groundfire v0.25**, originally created by **Tom Russell**. This repository keeps the spirit of the original game alive in a codebase that is easier to run, inspect, test, and evolve on modern Python environments.

The game places tanks on deformable terrain. Each player controls angle, power, movement, shield, jump fuel, and weapon selection. Between rounds, the economy lets players buy ammunition and upgrades.

### Goal

Provide a modern, verifiable version of Groundfire for:

- 🎮 Playing local matches with the classic presentation
- 🔬 Preserving the behavior, rhythm, and feel of the original game
- 🐍 Porting systems gradually to Python instead of turning the game into a loose remake
- ✅ Keeping automated coverage for mechanics, rendering, network code, terrain, and fidelity
- 📚 Studying a 2D Pygame game architecture

### Main Capabilities

| Capability | Description |
|---|---|
| 💥 Destructible terrain | Crater formation and collapses |
| 🎯 Artillery combat | Angle, power, gravity, and area damage |
| 🚀 Full-featured tanks | Movement, jump jets, shield, and round lifecycle |
| 🔫 Varied arsenal | Shell, Missile, MIRV, Nuke, and Machine Gun |
| 🤖 AI opponents | Computer-controlled players |
| 🛒 Between-round shop | Weapon and upgrade purchasing |
| 🖥️ Modern runtime | Classic local entry point + headless server |
| 🧪 Regression tests | Fidelity checks to keep the port under control |

### Current Scope

> [!IMPORTANT]
> This project is still in development. The goal is not only to make a similar game run in Python; the goal is to preserve the Groundfire experience with as much practical fidelity as possible while reorganizing the codebase for modern maintenance.

| Area | Status | Notes |
|:---|:---:|:---|
| Local game | 🟢 active | Main playable flow through the classic menu |
| Canonical runtime | 🟢 active | Modern entry point used by the `groundfire` wrappers |
| Local AI | 🟢 active | Computer-controlled players are implemented |
| Destructible terrain | 🟢 active | Craters, terrain falling, and effects have dedicated tests |
| Between-round shop | 🟢 active | Weapon and jump jet purchasing |
| Network | 🟡 evolving | Client, headless server, LAN discovery, and secure transport |
| Historical fidelity | 🟡 evolving | Tests and recorded output help compare behavior |

---

<a id="game-art-and-screenshots"></a>

## 🖼️ Game Art And Screenshots

The images below were generated from assets already stored in this repository.

<table align="center">
  <tr>
    <td align="center">
      <img src="media/img/readme-hero.png" alt="Groundfire hero art" width="420"><br>
      <sub><b>Groundfire hero art</b></sub>
    </td>
    <td align="center">
      <img src="media/img/readme-showcase.png" alt="Groundfire visual showcase" width="420"><br>
      <sub><b>Game and shop visual showcase</b></sub>
    </td>
  </tr>
</table>

---

<a id="hardware-and-software-requirements"></a>

## 💻 Hardware And Software Requirements

### Software Requirements

| Item | Requirement |
|:---|:---|
| 🐍 Python | 3.10, 3.11, 3.12, or 3.13 |
| 🖥️ Graphics | Environment capable of opening a Pygame window |
| 📦 Main dependencies | `pygame`, `msgpack`, `mpgameserver` |
| 🖧 Operating system | Windows, Linux, macOS, or WSL with graphics support |
| 📄 License | MIT |

### Current Dependencies

Dependencies are declared in [`requirements.txt`](requirements.txt) and [`pyproject.toml`](pyproject.toml):

| Package | Version | Purpose |
|:---|:---:|:---|
| `pygame` | `2.6.1` | Windowing, input, 2D rendering, and audio |
| `msgpack` | `1.1.2` | Message serialization |
| `mpgameserver` | `0.2.4` | Client/server transport infrastructure |
| `ruff` | `0.15.7` | Linting and import organization during development |
| `mypy` | `1.19.1` | Optional static typing checks during development |

### Practical Hardware Requirements

| Resource | Practical Minimum | Recommended | Notes |
|:---|:---:|:---:|:---|
| CPU | 2 cores | 4+ cores | Pygame and 2D simulation run well on common machines |
| RAM | 2 GB | 4+ GB | Enough for local play and tests |
| Storage | 500 MB free | 1 GB free | Includes `.venv`, dependencies, and assets |
| GPU | Not required | Basic acceleration | Depends on local SDL/Pygame support |
| Display | 1024 × 768 | 1280 × 720+ | The current default uses 1024 × 768 |

> [!NOTE]
> On Linux, minimal environments may need system SDL/Pygame libraries before the window can open.

---

<a id="step-by-step-installation"></a>

## 📦 Step-By-Step Installation

> [!NOTE]
> The easiest way to run the project is to use one of the `run_game.*` scripts. They search for a compatible Python version, create or repair `.venv`, upgrade `pip`, install dependencies, and start the game.

### 1️⃣ Clone The Repository

```bash
git clone https://github.com/p19091985/port-groundfire-for-python.git
cd port-groundfire-for-python
```

### 2️⃣ Recommended Automatic Setup

<table>
<tr>
<td><b>🪟 Windows CMD</b></td>
<td><b>🪟 Windows PowerShell</b></td>
<td><b>🐧 Linux / 🍎 macOS / WSL</b></td>
</tr>
<tr>
<td>

```bat
run_game.bat
```

</td>
<td>

```powershell
.\run_game.ps1
```

</td>
<td>

```bash
./run_game.sh
```

</td>
</tr>
</table>

The automatic flow:

1. Searches for Python 3.10 to 3.13
2. Creates `.venv` when needed
3. Recreates `.venv` if the Python version is incompatible
4. Upgrades `pip`
5. Installs [`requirements.txt`](requirements.txt)
6. Starts the game through the local entry point

### 3️⃣ Manual Setup

<details>
<summary>🔽 Expand manual installation instructions</summary>

#### Create virtual environment

```bash
python -m venv .venv
```

#### Activate the environment

```bash
# Linux / macOS / WSL
source .venv/bin/activate

# Windows CMD
.venv\Scripts\activate.bat

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

#### Install the package

```bash
python -m pip install --upgrade pip
pip install -e .
```

#### Start it

```bash
groundfire
```

Equivalent options:

```bash
python -m groundfire.client
python src/main.py
```

</details>

---

<a id="how-to-start-the-game"></a>

## ▶️ How To Start The Game

| Mode | Command |
|:---|:---|
| **Recommended local start** | `groundfire` |
| Force classic local flow | `python -m groundfire.client --classic-local` |
| Force canonical local runtime | `python -m groundfire.client --canonical-local` |
| With player name and AI players | `python -m groundfire.client --player-name Player --ai-players 2` |
| Smoke test (single frame) | `python -m groundfire.client --once` |

---

<a id="launch-scripts"></a>

## 📜 Launch Scripts

| File | Purpose | When To Use |
|:---|:---|:---|
| [`run_game.sh`](run_game.sh) | Prepares `.venv`, installs deps, and starts the game | 🐧 Linux / 🍎 macOS / WSL |
| [`run_game.bat`](run_game.bat) | Prepares `.venv`, installs deps, and starts the game | 🪟 Windows CMD |
| [`run_game.ps1`](run_game.ps1) | Prepares `.venv`, installs deps, and starts the game | 🪟 Windows PowerShell |
| [`scripts/run_quality_checks.py`](scripts/run_quality_checks.py) | Compile, test, lint, and type checks | Validation before publishing |
| [`scripts/profile_round_simulation.py`](scripts/profile_round_simulation.py) | Profiles round simulation performance | Performance diagnostics |
| [`scripts/generate_readme_art.py`](scripts/generate_readme_art.py) | Generates README artwork into `media/img/` | Documentation image maintenance |
| [`scripts/convert_legacy_tga_assets.py`](scripts/convert_legacy_tga_assets.py) | Helps convert historical assets | Asset maintenance |

---

<a id="gameplay-en"></a>

## 🎮 Gameplay

### Core Mechanics

- 🎯 Artillery aiming with angle and power
- 🌍 Gravity-influenced projectile trajectories
- 💥 Destructible terrain with craters and collapses
- 🚀 Tank movement and jump jets
- 🛡️ Area damage, shield, smoke, trails, and explosion effects
- 💰 Score and economy across rounds
- 🛒 Between-round weapon and upgrade purchasing
- 🤖 AI-controlled opponents

### Available Weapons

| Weapon | Icon | Role |
|:---|:---:|:---|
| `Shell` | 💣 | Default explosive projectile |
| `Machine Gun` | 🔫 | Rapid burst weapon with low per-shot damage |
| `MIRV` | 🎆 | Projectile that splits into sub-projectiles |
| `Missile` | 🚀 | Guided projectile |
| `Nuke` | ☢️ | Large-radius, high-impact explosion |

### Recommended Match Flow

```
1. 🏁 Start through the classic local menu
2. 👥 Configure human players and AI opponents
3. 🎯 Adjust angle and power
4. 💥 Fire while watching terrain, distance, and trajectory
5. 🛡️ Use movement, jump jets, and shields to survive
6. 🛒 Buy weapons and upgrades between rounds
7. 🏆 Repeat until a winner is decided
```

---

<a id="default-controls"></a>

## 🕹️ Default Controls

Controls can be edited in [`conf/controls.ini`](conf/controls.ini) or through the in-game control menus.

| Action | Player 1 Default Key |
|:---|:---:|
| 🔥 Fire | `Space` |
| ⬆️ Gun up | `W` |
| ⬇️ Gun down | `S` |
| ⬅️ Gun left | `A` |
| ➡️ Gun right | `D` |
| ◀️ Move tank left | `J` |
| ▶️ Move tank right | `L` |
| 🚀 Jump jets | `I` |
| 🛡️ Shield | `K` |
| 🔄 Next weapon | `O` |
| 🔄 Previous weapon | `U` |

> [`conf/controls.ini`](conf/controls.ini) also contains joystick layouts for up to **eight players**. Codes follow the mapping used by Pygame/SDL on the local machine.

---

<a id="game-configuration"></a>

## ⚙️ Game Configuration

Main settings live in [`conf/options.ini`](conf/options.ini).

| Section | Controls |
|:---|:---|
| `[Graphics]` | Width, height, color depth, visible FPS, and fullscreen |
| `[Effects]` | Blast fade, whiteout, and trail fade |
| `[Terrain]` | Terrain slices, width, and falling behavior |
| `[Quake]` | Duration, interval, amplitude, and earthquake frequency |
| `[Shell]` `[Nuke]` `[Missile]` `[Mirv]` `[MachineGun]` | Damage, cooldown, radius, speed, and weapon-specific values |
| `[Tank]` | Speed, size, angle, power, gravity, boost, and fuel usage |
| `[Price]` | Weapon and upgrade prices |
| `[Colours]` | Tank colors |
| `[Interface]` | Local menu mode, such as `classic` or the canonical runtime |

> [!TIP]
> To experiment with balance, edit `conf/options.ini` and restart the game. Gameplay changes that are meant to be contributed should be backed by tests.

---

<a id="local-and-online-modes"></a>

## 🌐 Local And Online Modes

### 🖥️ Local Game

Local play is the main current usage path:

```bash
groundfire
```

`LocalMenuMode=classic` in [`conf/options.ini`](conf/options.ini) makes the game open with the classic presentation by default.

### 🖧 Headless Server

The project also includes an authoritative headless server:

```bash
groundfire-server --server-name "Groundfire Server"
```

Or without console scripts:

```bash
python -m groundfire.server --host 0.0.0.0 --port 45000
```

### 🔗 Connected Client

To connect to a server:

```bash
groundfire --connect 127.0.0.1:45000 --player-name Player
```

If the port is omitted, the client uses the default protocol port.

### 🔑 Secure Transport Keys

The server uses default paths under `conf/network/` for private and public keys. When needed, those files are created by the server flow.

> [!IMPORTANT]
> Network mode exists for development and testing. For the smoothest gameplay, prefer local mode until the online experience is fully stabilized.

---

<a id="repository-layout"></a>

## 📂 Repository Layout

```
port-groundfire-for-python/
├── 📁 conf/                game options, controls, and asset mapping
├── 📁 data/                game images, sounds, font, and sprites
├── 📁 media/
│   └── 📁 img/             generated screenshots and images
├── 📁 groundfire/          public wrappers for package execution
├── 📁 scripts/             QA, artwork, asset, and profiling tools
├── 📁 src/                 main Python port code
│   └── 📁 groundfire/      canonical runtime organized by domain
├── 📁 tests/               automated tests
├── 🦇 run_game.bat         Windows CMD launcher
├── ⚡ run_game.ps1         Windows PowerShell launcher
├── 🐧 run_game.sh          Linux/macOS/WSL launcher
├── 📋 pyproject.toml       project metadata, scripts, and tool config
└── 📋 requirements.txt     runtime and development dependencies
```

### Incorporated Technical Content

| Content | Where It Lives Now |
|:---|:---|
| [`cpp_output.txt`](cpp_output.txt) | Execution log used as historical comparison material |
| Architecture assessment 2026 | [Technical Documentation ↓](#incorporated-technical-documentation-en) |
| Refactoring roadmap 2026 | [Technical Documentation ↓](#incorporated-technical-documentation-en) |
| Secure online mode | [Technical Documentation ↓](#incorporated-technical-documentation-en) |
| Classic controller playtest | [Technical Documentation ↓](#incorporated-technical-documentation-en) |

---

<a id="maintenance-architecture"></a>

## 🏗️ Maintenance Architecture

The project currently has two important layers:

- **Historical compatibility layer** in [`src/`](src) — preserves names and organization close to the initial port
- **Canonical layer** in [`src/groundfire/`](src/groundfire) — separates application, simulation, network, rendering, input, and gameplay

### Main Modules

| Path | Responsibility |
|:---|:---|
| [`src/main.py`](src/main.py) | Compatibility local entry point |
| [`groundfire/client.py`](groundfire/client.py) | Public client wrapper |
| [`groundfire/server.py`](groundfire/server.py) | Public server wrapper |
| [`src/groundfire/client.py`](src/groundfire/client.py) | Canonical client parser and orchestration |
| [`src/groundfire/server.py`](src/groundfire/server.py) | Headless server parser and orchestration |
| [`src/groundfire/app/`](src/groundfire/app) | Local, client, server, and frontend application flows |
| [`src/groundfire/sim/`](src/groundfire/sim) | World, terrain, registry, and simulated match |
| [`src/groundfire/gameplay/`](src/groundfire/gameplay) | Match controller and gameplay constants |
| [`src/groundfire/network/`](src/groundfire/network) | Messages, codec, LAN, client state, and backend |
| [`src/groundfire/render/`](src/groundfire/render) | Terrain, scene, HUD, primitives, and entity visuals |
| [`src/groundfire/input/`](src/groundfire/input) | Commands and controls |
| [`src/game.py`](src/game.py) | Classic flow loop and state transitions |
| [`src/tank.py`](src/tank.py) | Tank movement, damage, firing, and lifecycle |
| [`src/aiplayer.py`](src/aiplayer.py) | AI targeting and aiming behavior |
| [`src/weapons_impl.py`](src/weapons_impl.py) | Concrete weapon implementations |
| [`src/shopmenu.py`](src/shopmenu.py) | Between-round purchasing |

### Maintenance Principles

- 🔒 Preserve names and behavior when it helps comparison with the original game
- 📦 Move shared rules into `src/groundfire/` when there is a clear benefit
- 🧱 Keep rendering, simulation, input, and networking separated
- ✅ Cover behavior changes with automated tests
- ⚠️ Avoid large refactors without a verifiable reason

---

<a id="incorporated-technical-documentation-en"></a>

## 📖 Incorporated Technical Documentation

> [!NOTE]
> The Portuguese section above contains the complete original technical notes that were merged from the former Markdown files. This English section provides condensed summaries. Click to expand each section.

---

<details>
<summary><h3>📐 Architecture Assessment 2026</h3></summary>

<a id="architecture-assessment-2026"></a>

The assessment identifies the port as a functional and valuable preservation effort, but not yet a fully modern base for multiplayer, LAN play, dedicated servers, replay tooling, or a modern asset pipeline.

**Key findings:**

- `Game` acts as a god object and owns bootstrap, resources, state, menus, landscape, players, entities, and explosions.
- Simulation is still coupled to wall-clock time.
- Some configuration values and C++ parity hooks were not fully connected in the earlier port stage.
- Rendering, input, simulation, and UI responsibilities are mixed across modules.
- The project needs stable entity IDs, command buffers, serializable state, fixed ticks, and headless execution before robust multiplayer can be treated as complete.

**Recommended architecture:**

```text
src/groundfire/
|-- app/
|-- core/
|-- sim/
|-- gameplay/
|-- render/
|-- assets/
|-- input/
|-- audio/
|-- ui/
|-- network/
`-- tools/
```

**Recommended execution model:**

- Fixed-tick simulation, for example 60 Hz
- Independent rendering with interpolation
- Local input converted to `PlayerCommand`
- World updates driven only by commands and events
- Renderer and audio consuming snapshots/events instead of calling game rules directly

**Recommended network model:**

- Authoritative dedicated server
- Client responsible for rendering, UI, audio, and local input
- Player commands sent to the server
- Terrain, score, economy, and round ownership decided server-side
- Versioned network entity IDs, snapshots, and events

**Asset pipeline recommendation:**

- Migrate `.tga` runtime assets to lossless `.png`
- Validate dimensions, alpha, and orientation
- Introduce a manifest
- Replace magic numeric texture IDs with semantic resource names
- Keep conversion tooling isolated until runtime migration is safe

</details>

---

<details>
<summary><h3>🗺️ Refactoring Roadmap 2026</h3></summary>

<a id="refactoring-roadmap-2026"></a>

The roadmap proposes gradual modernization while keeping the game playable after each phase.

| Phase | Goal |
|:---:|:---|
| **0** | Audit modules, assets, states, dependencies, and hotspots |
| **1** | Harden structural issues before extracting the core |
| **2** | Isolate critical simulation modules from infrastructure |
| **3** | Reorganize the project into domain packages |
| **4** | Modernize the asset pipeline and move toward PNG/manifest-based resources |
| **5** | Move game logic to a fixed-tick simulation |
| **6** | Prepare network contracts for commands, events, snapshots, and IDs |
| **7** | Prototype LAN play and a dedicated server |
| **8** | Strengthen tests, profiling, CI, integration checks, and visual regressions |

**Network milestones:**

| Milestone | Goal | Key Deliverables |
|:---:|:---|:---|
| **N1** | Command and event contracts | Versioned schema, stable IDs, round/fire/damage events |
| **N2** | LAN discovery and handshake | UDP beacon, LAN browser, protocol/seed/token handshake |
| **N3** | Minimal authoritative server | Dedicated server, basic replication, score/turn sync |
| **N4** | Latency and reconciliation | Interpolation, local prediction, network metrics |

**Priorities:**

| Timeframe | Phases | Focus |
|:---|:---:|:---|
| 🔴 Short term | 1 — 2 | Fix structural bugs and extract simulation |
| 🟡 Medium term | 3 — 5 | Reorganize project, assets, and fixed tick |
| 🟢 Long term | 6 — 8 | Network, dedicated server, and hardening |

**Recommended next steps:**

1. Approve the target architecture and Phase 1 scope
2. Decide the final package layout
3. Define how strict compatibility with the C++ original should be
4. Record visual and behavior baselines before major fixes
5. Run the first `.png` asset migration in a parallel tree before switching runtime assets

</details>

---

<details>
<summary><h3>🔐 Secure Online Mode</h3></summary>

<a id="secure-online-mode-en"></a>

The online client/server path uses `mpgameserver` as the secure transport layer. It keeps the existing Groundfire match logic and interface flow while moving transport to an authenticated and encrypted UDP connection.

| File | Purpose |
|:---|:---|
| `conf/network/server_root_private.pem` | Server private key |
| `conf/network/server_root_public.pem` | Server public key |

When the server starts, it creates the private/public key pair automatically if the files do not exist.

**Start the server:**

```powershell
python -m src.groundfire.server
```

**Use custom key paths:**

```powershell
python -m src.groundfire.server --server-private-key custom/private.pem --server-public-key custom/public.pem
```

**Connect a client:**

```powershell
python -m src.groundfire.client --connect 127.0.0.1:27015 --server-public-key conf/network/server_root_public.pem
```

**Security notes:**

- 🔒 The server private key stays on the server
- 🔑 The client uses the server public key to authenticate the secure handshake
- ⛔ If the trusted public key file is missing, the client refuses the connection instead of falling back to insecure mode

</details>

---

<details>
<summary><h3>🎮 Classic Controller Playtest</h3></summary>

<a id="classic-controller-playtest-en"></a>

Use this checklist to validate the classic local menu flow on real hardware without changing the classic UI.

**Launch:**

```powershell
python -m src.groundfire.client --canonical-local --player-name "Controller Test"
```

**Keyboard 2:**

1. Open `Start Game`
2. Leave exactly one human player enabled
3. Change the controller selector to `Keyboard2`
4. Start a round
5. Confirm the tank responds only to the `Keyboard2` bindings from `conf/controls.ini`

**Joysticks:**

1. Repeat the same setup with `Joystick1`
2. Press `Fire` on an unassigned joystick from the player-select screen and confirm it auto-joins the next free player row
3. Start a round and confirm movement, aiming, weapon switching, and fire all route through the selected joystick
4. Repeat for any additional joystick layouts you want to certify

**Legacy fallback:**

1. Enable two human players in `Start Game`
2. Assign different controllers, for example `Keyboard1` and `Keyboard2` or `Keyboard1` and `Joystick1`
3. Start the match
4. Confirm the game hands off to the legacy local loop and begins the round with both players configured

**If a step fails, capture:**

- Which controller label was selected in the classic menu
- Whether the player was added by click or by pressing `Fire`
- Whether the failure happened before the round, during the round, or during the legacy fallback handoff

</details>

---

<a id="automated-tests-and-qa"></a>

## 🧪 Automated Tests And QA

### Run the full suite

```bash
python -m unittest discover -s tests -p "test_*.py"
```

### Run quality checks

```bash
python scripts/run_quality_checks.py
```

The quality script runs:

| Check | Purpose |
|:---|:---|
| `compileall` | Validates importable syntax in `src`, `tests`, `scripts`, and `groundfire` |
| `unittest` | Runs the automated suite |
| `ruff` | Runs linting when available |
| `mypy` | Runs type checks when available |

<details>
<summary>🔽 Targeted tests and covered areas</summary>

### Useful targeted tests

```bash
python -m unittest tests.test_port_fidelity
python -m unittest tests.test_fuzz_gameplay
python -m unittest tests.test_landscape_fidelity
python -m unittest tests.test_groundfire_entrypoints
python -m unittest tests.test_lan_discovery
```

### Covered areas

| Area | Example Tests |
|:---|:---|
| Port fidelity | `test_port_fidelity`, `test_replicated_scene` |
| Terrain and simulation | `test_landscape_fidelity`, `test_gamesimulation`, `test_fixedstep` |
| Game flow | `test_gameflow`, `test_gamesession`, `test_match_controller` |
| Rendering and HUD | `test_gamerenderer`, `test_gamehudrenderer`, `test_gamegraphics` |
| Input and commands | `test_commandintents`, `test_canonical_local_menu` |
| Network | `test_networkprotocol`, `test_networkstate`, `test_groundfire_codec`, `test_lan_discovery` |
| Portability | `test_portability`, `test_runtime_portability` |

</details>

---

<a id="troubleshooting"></a>

## 🔧 Troubleshooting

<details>
<summary><b>🖥️ Pygame does not open a window</b></summary>

- Confirm you are running in a graphical session
- On WSL, confirm WSLg or an X server is configured
- On minimal Linux environments, install the SDL/Pygame system libraries

</details>

<details>
<summary><b>🐍 The script says Python is incompatible</b></summary>

Use Python 3.10, 3.11, 3.12, or 3.13. The scripts automatically search for:

```text
python3.13, python3.12, python3.11, python3.10, python3, python
```

</details>

<details>
<summary><b>📁 `.venv` is broken</b></summary>

Run the launcher again:

```bash
./run_game.sh        # Linux / macOS / WSL
run_game.bat         # Windows CMD
.\run_game.ps1       # Windows PowerShell
```

The launcher attempts to repair or recreate the environment when it detects an incompatibility.

</details>

<details>
<summary><b>⚙️ The game opens in an unexpected local mode</b></summary>

Check [`conf/options.ini`](conf/options.ini):

```ini
[Interface]
LocalMenuMode=classic
```

You can also force the mode from the command line:

```bash
python -m groundfire.client --classic-local
python -m groundfire.client --canonical-local
```

</details>

<details>
<summary><b>🌐 The server does not connect</b></summary>

- Confirm the host and port used by the server
- Run client and server on the same machine with `127.0.0.1` to isolate network issues
- Check the local firewall
- Confirm the server finished creating the keys under `conf/network/`

</details>

---

<a id="credits-and-historical-preservation"></a>

## 🏆 Credits And Historical Preservation

> This section is prominent because the original game deserves clear attribution.

| | Credit |
|:---|:---|
| 🎮 Original game, design, programming, and C++ code | **Tom Russell** |
| 📦 Original project | **Groundfire v0.25** |
| 🌐 Historical official website | [groundfire.net](http://www.groundfire.net/) |
| 📅 Historical timeline | `v0.25` released on `15 May 2004`, updated on `20 Apr 2006` |
| 📧 Historical contact | `tom@groundfire.net` |
| 🐍 Python port and preservation | [p19091985](https://github.com/p19091985) |

> The historical site describes Groundfire as a free and open-source Windows/Linux game created by Tom Russell and inspired by *Death Tank* for the Sega Saturn.

<p align="center">
  <a href="http://www.groundfire.net/" title="Visit the historical Groundfire website">
    <img src="media/img/siteTom.png" alt="Screenshot of the historical Groundfire website created by Tom Russell" width="800">
  </a>
  <br>
  <sub>Historical official Groundfire website, created by Tom Russell.</sub>
</p>

<p align="center"><em>If you are here because you loved the original Groundfire, this repository exists because that work is worth preserving.</em></p>

---

<a id="license-en"></a>

## 📄 License

This repository is distributed under the **MIT License**. See [`LICENSE`](LICENSE) for the full text.

---

<p align="center">
  <strong>🔥 Groundfire lives here as playable memory: a classic artillery game preserved in Python. 🔥</strong>
</p>
