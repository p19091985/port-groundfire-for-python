<p align="center">
  <img src="docs/media/readme-hero.png" alt="Groundfire — hero art built from the game's own assets" width="720" />
</p>

<h1 align="center">🔥 Groundfire — Python Port</h1>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.25-0d6efd?style=for-the-badge" alt="version" />
  <img src="https://img.shields.io/badge/status-in%20development-bd3b3b?style=for-the-badge" alt="status" />
  <img src="https://img.shields.io/badge/license-MIT-292929?style=for-the-badge" alt="License" />
</p>
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%20—%203.13-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Pygame-2.6.1-1f6f43?style=flat-square" alt="Pygame" />
</p>

<p align="center">
  <kbd><a href="#english">🇬🇧 English</a></kbd>&nbsp;&nbsp;
  <kbd><a href="#portugues">🇧🇷 Português</a></kbd>
</p>

---

<!-- ═══════════════════════════════════════════════════════════ -->
<!-- ██████████████████   ENGLISH SECTION   ██████████████████ -->
<!-- ═══════════════════════════════════════════════════════════ -->

<a id="english"></a>

<h2 align="center">🇬🇧 English</h2>

<p align="center"><strong>A preservation-focused Python/Pygame port of the original Groundfire v0.25</strong></p>

<p align="center"><em>Groundfire is a classic artillery tank game with destructible terrain, ballistic combat,<br />weapon shopping between rounds, and computer-controlled opponents.</em></p>

<p align="center"><strong>Original Groundfire created by Tom Russell. This port exists to preserve and modernize that work.</strong></p>

---

### 📑 Table of Contents

| | Section | | Section |
|:---|:---|:---|:---|
| 🎯 | [Why This Project Exists](#why-this-project-exists) | 🕹️ | [Controls](#controls) |
| ✨ | [Highlights](#highlights) | ⚙️ | [Configuration](#configuration) |
| 🖼️ | [Visual Showcase](#visual-showcase) | 📂 | [Repository Tour](#repository-tour) |
| 🚀 | [Quick Start](#quick-start) | 🏗️ | [Architecture at a Glance](#architecture-at-a-glance) |
| 🔧 | [Manual Setup](#manual-setup) | 🧪 | [Running Tests](#running-tests) |
| 💻 | [Requirements](#requirements) | 📜 | [Preservation Notes](#preservation-notes) |
| 🎮 | [Gameplay Snapshot](#gameplay-snapshot) | 🏆 | [Credits](#credits) |
| 📄 | [License](#license-en) | | |

---

<a id="why-this-project-exists"></a>

## 🎯 Why This Project Exists

This port is both a **technical exercise** and a **preservation effort**.

<table>
  <tr>
    <td align="center" width="25%">🎮<br /><strong>PLAY</strong><br /><sub>Ballistic tank duels, destructible terrain, splash damage, round economy, and fast restarts.</sub></td>
    <td align="center" width="25%">🔬<br /><strong>PRESERVE</strong><br /><sub>The original C++ source is included in the repo so the Python port can be compared against the real thing.</sub></td>
    <td align="center" width="25%">🐍<br /><strong>PORT</strong><br /><sub>Systems are migrated carefully with automated tests instead of being replaced by a loose remake.</sub></td>
    <td align="center" width="25%">📚<br /><strong>STUDY</strong><br /><sub>Makes the game easier to run, inspect, and extend on modern Python setups.</sub></td>
  </tr>
</table>

- It keeps the original `groundfire-0.25/` source tree in the repository as a live reference
- It ports gameplay systems one piece at a time instead of rewriting the game from scratch
- It uses automated tests to protect behavior while the port continues to evolve
- It aims to make the game easier to run, inspect, and extend on modern Python setups

---

<a id="highlights"></a>

## ✨ Highlights

| Feature | Description |
|:---|:---|
| 💥 Destructible terrain | Changes the battlefield after every explosion |
| 🎯 Ballistic combat | Turn-based artillery with angle, power, gravity, and splash damage |
| 🔫 Multiple weapons | Shells, Missiles, MIRVs, Nukes, and Machine Gun |
| 🤖 AI players | Choose targets, estimate aim, and adjust shots |
| 🛒 Between-round shop | Ammo and jump jet upgrades |
| 📦 Original C++ included | Side-by-side comparison and reference |
| 🌐 Network layer preview | Server browser UI, LAN discovery, and dedicated server panel |

---

<a id="visual-showcase"></a>

## 🖼️ Visual Showcase

<p align="center">
  <img src="docs/media/readme-showcase.png" alt="Groundfire showcase — battlefield and shop styling" width="720" />
</p>

---

<a id="quick-start"></a>

## 🚀 Quick Start

The launcher scripts are the easiest way to run the game. If the project is not installed yet, they will:

1. 🔍 Find a compatible Python version
2. 📁 Create or repair `.venv`
3. ⬆️ Upgrade `pip`
4. 📦 Install dependencies
5. ▶️ Start the game

### 🎮 Start the Game

<table>
<tr>
<td align="center"><b>🪟 Windows CMD</b></td>
<td align="center"><b>🪟 Windows PowerShell</b></td>
<td align="center"><b>🐧 Linux / 🍎 macOS / WSL</b></td>
</tr>
<tr>
<td>

```bat
run_game.bat
```

</td>
<td>

```powershell
./run_game.ps1
```

</td>
<td>

```bash
./run_game.sh
```

</td>
</tr>
</table>

### 🖧 Start the Dedicated Server

<table>
<tr>
<td align="center"><b>🪟 Windows CMD</b></td>
<td align="center"><b>🪟 Windows PowerShell</b></td>
<td align="center"><b>🐧 Linux / 🍎 macOS / WSL</b></td>
</tr>
<tr>
<td>

```bat
run_server.bat
```

</td>
<td>

```powershell
./run_server.ps1
```

</td>
<td>

```bash
./run_server.sh
```

</td>
</tr>
</table>

---

<a id="manual-setup"></a>

## 🔧 Manual Setup

<details>
<summary>🔽 Expand manual installation instructions</summary>

If you prefer to manage the environment yourself:

### 1. Clone and create the virtual environment

```bash
git clone https://github.com/p19091985/port-groundfire-for-python.git
cd port-groundfire-for-python
python -m venv .venv
```

### 2. Activate the virtual environment

```bash
# Linux / macOS / WSL
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows CMD
.venv\Scripts\activate.bat
```

### 3. Install and run

```bash
pip install -r requirements.txt
python src/main.py
```

</details>

---

<a id="requirements"></a>

## 💻 Requirements

| Item | Requirement |
|:---|:---|
| 🐍 Python | 3.10, 3.11, 3.12, or 3.13 |
| 📦 Dependencies | `pygame==2.6.1` |
| 🖥️ Graphics | Environment capable of opening a Pygame window |
| 🖧 OS | Windows, Linux, macOS, or WSL with graphics support |

---

<a id="gameplay-snapshot"></a>

## 🎮 Gameplay Snapshot

### Core Mechanics

- 🎯 Artillery aiming with gun angle and shot power
- 💥 Destructible landscape with crater formation
- 🚀 Tank movement, jump jets, and terrain interaction
- 💰 Scoring and economy across multiple rounds
- 🛒 Shopping between rounds for stronger weapons and mobility

### Available Weapons

| Weapon | Icon | Role |
|:---|:---:|:---|
| Shell | 💣 | Default explosive projectile |
| Machine Gun | 🔫 | Rapid-fire burst weapon |
| MIRV | 🎆 | Splits into multiple sub-projectiles |
| Missile | 🚀 | Guided projectile |
| Nuke | ☢️ | Large-radius high-impact explosion |

---

<a id="controls"></a>

## 🕹️ Controls

Default keyboard controls for **Player 1**:

| Action | Key |
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

> Controls can be adjusted in [`conf/controls.ini`](conf/controls.ini) or through the in-game control menus.

---

<a id="configuration"></a>

## ⚙️ Configuration

| File | What it controls |
|:---|:---|
| [`conf/options.ini`](conf/options.ini) | Graphics, terrain, tank tuning, and gameplay values |
| [`conf/controls.ini`](conf/controls.ini) | Controller and keyboard mappings |

---

<a id="repository-tour"></a>

## 📂 Repository Tour

```
port-groundfire-for-python/
├── 📁 src/                  Python port source code (42 modules)
├── 📁 interface_net/        Network integration layer (server browser, LAN, sessions)
├── 📁 groundfire-0.25/      Original C++ source used as reference
├── 📁 data/                 Textures, sounds, and game assets
├── 📁 conf/                 Game options and control mappings
├── 📁 tests/                Automated regression and fidelity tests
├── 📁 docs/media/           README images and artwork
├── 📁 scripts/              Art generation and tooling
├── 🦇 run_game.bat          Windows CMD launcher (auto-install)
├── ⚡ run_game.ps1          Windows PowerShell launcher (auto-install)
├── 🐧 run_game.sh           Unix launcher (auto-install)
├── 🦇 run_server.bat        Windows CMD server launcher
├── ⚡ run_server.ps1        Windows PowerShell server launcher
├── 🐧 run_server.sh         Unix server launcher
└── 📋 requirements.txt      Python dependencies
```

---

<a id="architecture-at-a-glance"></a>

## 🏗️ Architecture at a Glance

```
Game
├── Landscape
├── Entity List
│   ├── Projectiles (Shell, Missile, MIRV, MachineGun)
│   ├── Effects (Blast, Smoke, Trail, Quake)
│   └── Sound entities
└── Players
    ├── HumanPlayer
    └── AIPlayer
        └── Tank
            └── Weapons
```

### Key Modules

| Module | Responsibility |
|:---|:---|
| [`src/main.py`](src/main.py) | Entry point |
| [`src/game.py`](src/game.py) | Game loop and state transitions |
| [`src/tank.py`](src/tank.py) | Tank movement, damage, firing, and round lifecycle |
| [`src/aiplayer.py`](src/aiplayer.py) | AI targeting and aiming |
| [`src/landscape.py`](src/landscape.py) | Terrain generation, explosions, and collisions |
| [`src/weapons_impl.py`](src/weapons_impl.py) | Concrete weapon implementations |
| [`src/shopmenu.py`](src/shopmenu.py) | Between-round purchasing flow |
| [`interface_net/`](interface_net/) | Network layer: sessions, LAN, server browser |

---

<a id="running-tests"></a>

## 🧪 Running Tests

### Full suite

```bash
python -m unittest discover -s tests -p "test_*.py"
```

### Targeted runs

```bash
python -m unittest tests.test_port_fidelity
python -m unittest tests.test_fuzz_gameplay
python -m unittest tests.test_landscape_fidelity
python -m unittest tests.test_lan_connection
python -m unittest tests.test_network_integration
```

### Covered areas

| Area | Tests |
|:---|:---|
| Port fidelity | `test_port_fidelity` |
| Gameplay fuzzing | `test_fuzz_gameplay`, `test_exhaustive_simulation` |
| Terrain | `test_landscape_fidelity` |
| Network & LAN | `test_lan_connection`, `test_network_integration`, `test_client_interface` |
| Server | `test_dedicated_server_ui`, `test_server_browser_ui`, `test_server_launchers` |
| UI | `test_find_servers_menu` |

---

<a id="project-status"></a>

## 📊 Project Status

This is still an **active port**, not a final release.

| Area | Status |
|:---|:---:|
| Core gameplay systems | 🟢 Playable |
| Fidelity to original C++ | 🟢 Active goal |
| Test coverage | 🟢 12 test modules |
| Network layer | 🟡 In development |
| Dedicated server | 🟡 Preview available |
| LAN multiplayer | 🟡 In progress |

> *The goal is not just to make Groundfire run in Python. The goal is to make it still **feel** like Groundfire.*

---

<a id="preservation-notes"></a>

## 📜 Preservation Notes

The original Groundfire C++ source is intentionally kept in this repository under [`groundfire-0.25/`](groundfire-0.25/). That directory is not just archival material — it is part of the workflow for **verifying behavior and port fidelity**.

---

<a id="credits"></a>

## 🏆 Credits

> This section is intentionally prominent because the original game deserves clear attribution.

| | Credit |
|:---|:---|
| 🎮 Original game, design, programming, and C++ code | **Tom Russell** |
| 📦 Original project | **Groundfire v0.25** |
| 🌐 Historical official website | [groundfire.net](http://www.groundfire.net/) |
| 📅 Timeline | `v0.25` released on `15 May 2004`, updated on `20 Apr 2006` |
| 📧 Historical contact | `tom@groundfire.net` |
| 🐍 Python port and preservation | [p19091985](https://github.com/p19091985) |

> The official site describes Groundfire as a free, open-source Windows/Linux project designed and programmed entirely by Tom Russell, inspired by Sega Saturn's *Death Tank*.

<p align="center">
  <a href="http://www.groundfire.net/" title="Visit the original Groundfire website">
    <img src="docs/media/siteTom.png" alt="Screenshot of Tom Russell's original Groundfire website" width="800" />
  </a>
  <br />
  <sub>Historical official Groundfire website, created by Tom Russell.</sub>
</p>

<p align="center"><em>If you are here because you loved the original game, this repository exists because that work was worth preserving.</em></p>

---

<a id="license-en"></a>

## 📄 License

This repository is distributed under the **MIT License**. See [`LICENSE`](LICENSE) for the full text.

---

<p align="center">
  <strong>🔥 Groundfire lives here in two forms: the original C++ game and a modern Python port, side by side. 🔥</strong>
</p>

---

<br />

<!-- ═══════════════════════════════════════════════════════════ -->
<!-- █████████████████   SEÇÃO EM PORTUGUÊS   █████████████████ -->
<!-- ═══════════════════════════════════════════════════════════ -->

<p align="center">
  <kbd><a href="#english">🇬🇧 English</a></kbd>&nbsp;&nbsp;
  <kbd><a href="#portugues">🇧🇷 Português</a></kbd>
</p>

<a id="portugues"></a>

<h2 align="center">🇧🇷 Português</h2>

<p align="center"><strong>Port em Python/Pygame do Groundfire v0.25, com foco em preservação, jogabilidade clássica e compatibilidade moderna.</strong></p>

<p align="center"><em>Groundfire é um jogo clássico de artilharia entre tanques, com terreno destrutível, combate balístico,<br />loja de armas entre rodadas e oponentes controlados por IA.</em></p>

<p align="center"><strong>Groundfire original criado por Tom Russell. Este port existe para preservar e modernizar esse trabalho.</strong></p>

---

### 📑 Índice

| | Seção | | Seção |
|:---|:---|:---|:---|
| 🎯 | [Por que este projeto existe?](#por-que-este-projeto-existe) | 🕹️ | [Controles](#controles) |
| ✨ | [Destaques](#destaques) | ⚙️ | [Configuração](#configuracao) |
| 🖼️ | [Showcase Visual](#showcase-visual) | 📂 | [Estrutura do Repositório](#estrutura-do-repositorio) |
| 🚀 | [Início Rápido](#inicio-rapido) | 🏗️ | [Arquitetura Resumida](#arquitetura-resumida) |
| 🔧 | [Instalação Manual](#instalacao-manual) | 🧪 | [Executando Testes](#executando-testes) |
| 💻 | [Requisitos](#requisitos) | 📜 | [Notas de Preservação](#notas-de-preservacao) |
| 🎮 | [Jogabilidade](#jogabilidade) | 🏆 | [Créditos](#creditos) |
| 📄 | [Licença](#licenca) | | |

---

<a id="por-que-este-projeto-existe"></a>

## 🎯 Por que este projeto existe?

Este port é tanto um **exercício técnico** quanto um **esforço de preservação**.

<table>
  <tr>
    <td align="center" width="25%">🎮<br /><strong>JOGAR</strong><br /><sub>Duelos de tanques com artilharia, terreno destrutível, dano em área, economia entre rodadas e reinício rápido.</sub></td>
    <td align="center" width="25%">🔬<br /><strong>PRESERVAR</strong><br /><sub>O código-fonte C++ original está incluído no repositório para que o port em Python possa ser comparado com o jogo real.</sub></td>
    <td align="center" width="25%">🐍<br /><strong>PORTAR</strong><br /><sub>Os sistemas são migrados cuidadosamente com testes automatizados, em vez de serem substituídos por um remake solto.</sub></td>
    <td align="center" width="25%">📚<br /><strong>ESTUDAR</strong><br /><sub>Torna o jogo mais fácil de executar, inspecionar e estender em ambientes Python modernos.</sub></td>
  </tr>
</table>

- Mantém a árvore original `groundfire-0.25/` no repositório como referência viva
- Porta os sistemas de gameplay um por um, em vez de reescrever o jogo do zero
- Usa testes automatizados para proteger o comportamento enquanto o port evolui
- Visa tornar o jogo mais fácil de rodar, inspecionar e estender em ambientes Python modernos

---

<a id="destaques"></a>

## ✨ Destaques

| Funcionalidade | Descrição |
|:---|:---|
| 💥 Terreno destrutível | Muda o campo de batalha após cada explosão |
| 🎯 Combate balístico | Artilharia por turnos com ângulo, potência, gravidade e dano em área |
| 🔫 Arsenal variado | Shells, Missiles, MIRVs, Nukes e Machine Gun |
| 🤖 IA adversária | Escolhe alvos, estima mira e ajusta após cada disparo |
| 🛒 Loja entre rodadas | Munição e upgrades de jump jets |
| 📦 C++ original incluído | Comparação lado a lado e referência |
| 🌐 Camada de rede (preview) | Browser de servidores, descoberta LAN e painel de servidor dedicado |

---

<a id="showcase-visual"></a>

## 🖼️ Showcase Visual

<p align="center">
  <img src="docs/media/readme-showcase.png" alt="Groundfire showcase — campo de batalha e loja" width="720" />
</p>

---

<a id="inicio-rapido"></a>

## 🚀 Início Rápido

Os scripts de inicialização são a forma mais fácil de rodar o jogo. Se o projeto ainda não estiver instalado, eles vão:

1. 🔍 Procurar uma versão compatível do Python
2. 📁 Criar ou reparar `.venv`
3. ⬆️ Atualizar o `pip`
4. 📦 Instalar dependências
5. ▶️ Iniciar o jogo

### 🎮 Iniciar o Jogo

<table>
<tr>
<td align="center"><b>🪟 Windows CMD</b></td>
<td align="center"><b>🪟 Windows PowerShell</b></td>
<td align="center"><b>🐧 Linux / 🍎 macOS / WSL</b></td>
</tr>
<tr>
<td>

```bat
run_game.bat
```

</td>
<td>

```powershell
./run_game.ps1
```

</td>
<td>

```bash
./run_game.sh
```

</td>
</tr>
</table>

### 🖧 Iniciar o Servidor Dedicado

<table>
<tr>
<td align="center"><b>🪟 Windows CMD</b></td>
<td align="center"><b>🪟 Windows PowerShell</b></td>
<td align="center"><b>🐧 Linux / 🍎 macOS / WSL</b></td>
</tr>
<tr>
<td>

```bat
run_server.bat
```

</td>
<td>

```powershell
./run_server.ps1
```

</td>
<td>

```bash
./run_server.sh
```

</td>
</tr>
</table>

---

<a id="instalacao-manual"></a>

## 🔧 Instalação Manual

<details>
<summary>🔽 Expandir instruções de instalação manual</summary>

Se você prefere gerenciar o ambiente manualmente:

### 1. Clonar e criar o ambiente virtual

```bash
git clone https://github.com/p19091985/port-groundfire-for-python.git
cd port-groundfire-for-python
python -m venv .venv
```

### 2. Ativar o ambiente virtual

```bash
# Linux / macOS / WSL
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows CMD
.venv\Scripts\activate.bat
```

### 3. Instalar e executar

```bash
pip install -r requirements.txt
python src/main.py
```

</details>

---

<a id="requisitos"></a>

## 💻 Requisitos

| Item | Requisito |
|:---|:---|
| 🐍 Python | 3.10, 3.11, 3.12 ou 3.13 |
| 📦 Dependências | `pygame==2.6.1` |
| 🖥️ Interface gráfica | Ambiente com suporte a janela Pygame |
| 🖧 Sistema operacional | Windows, Linux, macOS ou WSL com suporte gráfico |

---

<a id="jogabilidade"></a>

## 🎮 Jogabilidade

### Mecânicas Centrais

- 🎯 Mira de artilharia com ângulo do canhão e potência do disparo
- 💥 Paisagem destrutível com formação de crateras
- 🚀 Movimentação de tanques, jump jets e interação com terreno
- 💰 Pontuação e economia ao longo de múltiplas rodadas
- 🛒 Compra de armas e melhorias entre rodadas

### Armas Disponíveis no Port

| Arma | Ícone | Papel |
|:---|:---:|:---|
| Shell | 💣 | Projétil explosivo padrão |
| Machine Gun | 🔫 | Arma de rajada rápida |
| MIRV | 🎆 | Se divide em múltiplos subprojéteis |
| Missile | 🚀 | Projétil guiado |
| Nuke | ☢️ | Explosão de grande raio e alto impacto |

---

<a id="controles"></a>

## 🕹️ Controles

Controles padrão de teclado para o **Jogador 1**:

| Ação | Tecla |
|:---|:---:|
| 🔥 Atirar | `Space` |
| ⬆️ Subir canhão | `W` |
| ⬇️ Descer canhão | `S` |
| ⬅️ Canhão para esquerda | `A` |
| ➡️ Canhão para direita | `D` |
| ◀️ Mover tanque para esquerda | `J` |
| ▶️ Mover tanque para direita | `L` |
| 🚀 Jump jets | `I` |
| 🛡️ Escudo | `K` |
| 🔄 Próxima arma | `O` |
| 🔄 Arma anterior | `U` |

> Os controles podem ser ajustados em [`conf/controls.ini`](conf/controls.ini) ou pelos menus de controle dentro do jogo.

---

<a id="configuracao"></a>

## ⚙️ Configuração

| Arquivo | O que controla |
|:---|:---|
| [`conf/options.ini`](conf/options.ini) | Gráficos, terreno, calibragem dos tanques e valores de gameplay |
| [`conf/controls.ini`](conf/controls.ini) | Mapeamento de controles e teclado |

---

<a id="estrutura-do-repositorio"></a>

## 📂 Estrutura do Repositório

```
port-groundfire-for-python/
├── 📁 src/                  Código-fonte do port Python (42 módulos)
├── 📁 interface_net/        Camada de integração de rede (browser, LAN, sessões)
├── 📁 groundfire-0.25/      Código-fonte C++ original usado como referência
├── 📁 data/                 Texturas, sons e assets do jogo
├── 📁 conf/                 Configurações de jogo e mapeamento de controles
├── 📁 tests/                Testes automatizados de regressão e fidelidade
├── 📁 docs/media/           Imagens e arte do README
├── 📁 scripts/              Geração de arte e ferramentas auxiliares
├── 🦇 run_game.bat          Inicializador Windows CMD (auto-install)
├── ⚡ run_game.ps1          Inicializador Windows PowerShell (auto-install)
├── 🐧 run_game.sh           Inicializador Unix (auto-install)
├── 🦇 run_server.bat        Inicializador do servidor — Windows CMD
├── ⚡ run_server.ps1        Inicializador do servidor — Windows PowerShell
├── 🐧 run_server.sh         Inicializador do servidor — Unix
└── 📋 requirements.txt      Dependências Python
```

---

<a id="arquitetura-resumida"></a>

## 🏗️ Arquitetura Resumida

```
Game
├── Landscape
├── Lista de Entidades
│   ├── Projéteis (Shell, Missile, MIRV, MachineGun)
│   ├── Efeitos (Blast, Smoke, Trail, Quake)
│   └── Entidades de som
└── Jogadores
    ├── HumanPlayer
    └── AIPlayer
        └── Tank
            └── Weapons
```

### Módulos Principais

| Módulo | Responsabilidade |
|:---|:---|
| [`src/main.py`](src/main.py) | Ponto de entrada |
| [`src/game.py`](src/game.py) | Loop do jogo e transições de estado |
| [`src/tank.py`](src/tank.py) | Movimentação, dano, disparo e ciclo de vida do tanque |
| [`src/aiplayer.py`](src/aiplayer.py) | Mira e escolha de alvo da IA |
| [`src/landscape.py`](src/landscape.py) | Geração de terreno, explosões e colisões |
| [`src/weapons_impl.py`](src/weapons_impl.py) | Implementações concretas de armas |
| [`src/shopmenu.py`](src/shopmenu.py) | Fluxo de compra entre rodadas |
| [`interface_net/`](interface_net/) | Camada de rede: sessões, LAN, browser de servidores |

---

<a id="executando-testes"></a>

## 🧪 Executando Testes

### Suite completa

```bash
python -m unittest discover -s tests -p "test_*.py"
```

### Execuções direcionadas

```bash
python -m unittest tests.test_port_fidelity
python -m unittest tests.test_fuzz_gameplay
python -m unittest tests.test_landscape_fidelity
python -m unittest tests.test_lan_connection
python -m unittest tests.test_network_integration
```

### Áreas cobertas

| Área | Testes |
|:---|:---|
| Fidelidade do port | `test_port_fidelity` |
| Gameplay e simulação | `test_fuzz_gameplay`, `test_exhaustive_simulation` |
| Terreno | `test_landscape_fidelity` |
| Rede e LAN | `test_lan_connection`, `test_network_integration`, `test_client_interface` |
| Servidor | `test_dedicated_server_ui`, `test_server_browser_ui`, `test_server_launchers` |
| Interface | `test_find_servers_menu` |

---

<a id="status-do-projeto"></a>

## 📊 Estado do Projeto

Este é um **port em desenvolvimento ativo**, não um release final.

| Área | Estado |
|:---|:---:|
| Sistemas de gameplay | 🟢 Jogável |
| Fidelidade ao C++ original | 🟢 Objetivo ativo |
| Cobertura de testes | 🟢 12 módulos de teste |
| Camada de rede | 🟡 Em desenvolvimento |
| Servidor dedicado | 🟡 Preview disponível |
| Multiplayer LAN | 🟡 Em progresso |

> *O objetivo não é apenas fazer o Groundfire rodar em Python. O objetivo é fazer com que ele ainda **pareça** Groundfire.*

---

<a id="notas-de-preservacao"></a>

## 📜 Notas de Preservação

O código-fonte C++ original do Groundfire é intencionalmente mantido neste repositório em [`groundfire-0.25/`](groundfire-0.25/). Esse diretório não é apenas material de arquivo — ele faz parte do fluxo de trabalho para **verificar comportamento e fidelidade do port**.

---

<a id="creditos"></a>

## 🏆 Créditos

> Esta seção é intencionalmente destacada porque o jogo original merece atribuição clara.

| | Crédito |
|:---|:---|
| 🎮 Jogo original, design, programação e código C++ | **Tom Russell** |
| 📦 Projeto original | **Groundfire v0.25** |
| 🌐 Site histórico oficial | [groundfire.net](http://www.groundfire.net/) |
| 📅 Timeline histórica | `v0.25` publicada em `15 May 2004`, atualizada em `20 Apr 2006` |
| 📧 Contato histórico | `tom@groundfire.net` |
| 🐍 Port Python e preservação | [p19091985](https://github.com/p19091985) |

> O site oficial descreve o Groundfire como um projeto livre e open-source para Windows/Linux, projetado e programado inteiramente por Tom Russell, inspirado em *Death Tank* do Sega Saturn.

<p align="center">
  <a href="http://www.groundfire.net/" title="Visitar o site original do Groundfire">
    <img src="docs/media/siteTom.png" alt="Captura do site histórico do Groundfire criado por Tom Russell" width="800" />
  </a>
  <br />
  <sub>Site histórico oficial do Groundfire, criado por Tom Russell.</sub>
</p>

<p align="center"><em>Se você está aqui porque gostava do Groundfire original, este repositório existe porque esse trabalho vale a pena ser preservado.</em></p>

---

<a id="licenca"></a>

## 📄 Licença

Este repositório é distribuído sob a **Licença MIT**. Consulte [`LICENSE`](LICENSE) para o texto completo.

---

<p align="center">
  <strong>🔥 Groundfire vive aqui em duas formas: o jogo original em C++ e um port moderno em Python, lado a lado. 🔥</strong>
</p>
