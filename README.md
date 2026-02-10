# 🎮 Groundfire — Port para Python

<p align="center">
  <strong>Um jogo de artilharia 2D com tanques, terreno destrutível e combate por turnos em tempo real.</strong><br>
  <em>Port do jogo original Groundfire v0.25 (C++/OpenGL) para Python/Pygame.</em>
</p>

---

> ⚠️ **PROJETO EM DESENVOLVIMENTO** — Este port está sendo portado ativamente do código-fonte original em C++ para Python. Algumas funcionalidades podem ainda não estar completas ou podem apresentar diferenças em relação à versão original.

---

## 📖 Sobre o Jogo

**Groundfire** é um jogo clássico de artilharia 2D, originalmente desenvolvido por **Tom Russell** em C++ com OpenGL. O jogo coloca jogadores no comando de tanques de guerra posicionados sobre um terreno destrutível, onde o objetivo é destruir os tanques adversários utilizando uma variedade de armas e estratégias.

O gameplay combina física de projéteis (gravidade, ângulo e potência), terreno que pode ser destruído por explosões, sistema de economia para compra de armamentos e inteligência artificial para oponentes controlados pelo computador.

### 🎯 Mecânicas Principais

- **Combate por Artilharia** — Ajuste o ângulo e a potência do canhão para atingir os inimigos
- **Terreno Destrutível** — Explosões criam crateras reais no terreno, mudando o campo de batalha
- **Física Realista** — Trajetórias de projéteis com gravidade, cálculos balísticos precisos
- **Terremotos** — Eventos periódicos que fazem o terreno baixar, forçando adaptação

## 🔫 Arsenal de Armas

| Arma | Descrição | Tipo |
|------|-----------|------|
| **Shell** (Projétil) | Arma padrão, disponível ilimitadamente. Dano e explosão moderados. | Padrão |
| **Missile** (Míssil) | Projétil guiado pelo jogador após o disparo. Combustível limitado. | Comprável |
| **MIRV** | Projétil que se divide em múltiplos fragmentos no ponto mais alto da trajetória. | Comprável |
| **Nuke** (Nuclear) | Explosão massiva com grande raio de destruição e efeito de "whiteout". | Comprável |
| **Machine Gun** (Metralhadora) | Disparo rápido de múltiplos projéteis de baixo dano. | Comprável |

## 🤖 Inteligência Artificial

Os jogadores controlados pelo computador (IA) possuem um sistema de decisão que inclui:

- **Seleção de alvo** — A IA escolhe o oponente mais próximo como alvo
- **Estimativa de mira** — Calcula ângulo e potência necessários para atingir o alvo
- **Ajuste iterativo** — Após cada tiro, a IA ajusta sua mira com base em onde o projétil caiu
- **Reação a eventos** — A IA reage quando seu tanque é atingido ou quando o alvo é destruído

## 🎮 Controles

### Jogador 1 (Teclado)

| Ação | Tecla |
|------|-------|
| Atirar | `Espaço` |
| Mirar canhão (cima) | `W` |
| Mirar canhão (baixo) | `S` |
| Rotacionar canhão (esquerda) | `A` |
| Rotacionar canhão (direita) | `D` |
| Mover tanque (esquerda) | `J` |
| Mover tanque (direita) | `L` |
| Jump Jets (saltar) | `I` |
| Escudo | `K` |
| Próxima arma | `O` |
| Arma anterior | `U` |

> **Nota:** Os controles podem ser personalizados em `conf/controls.ini` ou pelo menu do jogo "Set Controls".

## 🛒 Sistema de Loja

Entre as rodadas, os jogadores podem comprar armas e upgrades com o dinheiro ganho em combate:

- **Ganhos por eliminação:** +50 moedas por oponente destruído
- **Bônus por líder:** Pontos dobrados por matar o líder do placar
- **Sobrevivência:** +25 moedas por sobreviver à rodada
- **Renda fixa:** +10 moedas por rodada para todos os jogadores

## 🗂️ Estrutura do Projeto

```
port-groundfire-for-python/
├── src/                    # Código-fonte Python (port)
│   ├── main.py             # Ponto de entrada do jogo
│   ├── game.py             # Loop principal e gerenciamento de estado
│   ├── tank.py             # Lógica do tanque (movimento, dano, armas)
│   ├── player.py           # Classe base do jogador
│   ├── aiplayer.py         # Inteligência artificial
│   ├── humanplayer.py      # Jogador humano (controles)
│   ├── landscape.py        # Terreno destrutível
│   ├── entity.py           # Classe base para todas as entidades
│   ├── weapon.py           # Classe base de armas
│   ├── weapons_impl.py     # Implementações: Shell, Missile, MIRV, Nuke, MG
│   ├── shell.py            # Projétil de canhão
│   ├── missile.py          # Míssil guiado
│   ├── mirv.py             # Projétil MIRV
│   ├── machinegunround.py  # Projétil de metralhadora
│   ├── blast.py            # Efeito visual de explosão
│   ├── smoke.py            # Efeito visual de fumaça
│   ├── trail.py            # Rastro de projéteis
│   ├── quake.py            # Sistema de terremotos
│   ├── interface.py        # Interface gráfica (Pygame)
│   ├── font.py             # Renderização de texto
│   ├── sounds.py           # Sistema de áudio
│   ├── controls.py         # Mapeamento de controles
│   ├── common.py           # Funções matemáticas e constantes
│   ├── inifile.py          # Parser de arquivos INI
│   ├── menu.py             # Classe base de menus
│   ├── mainmenu.py         # Menu principal
│   ├── playermenu.py       # Menu de jogadores
│   ├── shopmenu.py         # Loja entre rodadas
│   ├── scoremenu.py        # Placar de pontuação
│   ├── optionmenu.py       # Menu de opções
│   ├── winnermenu.py       # Tela de vitória
│   └── ...                 # Outros módulos auxiliares
├── groundfire-0.25/        # Código-fonte original em C++ (referência)
│   ├── src/                # Implementações C++ (.cc)
│   └── src/includes/       # Headers C++ (.hh)
├── data/                   # Assets do jogo
│   ├── *.tga               # Texturas (explosões, fumaça, ícones, fontes)
│   └── *.wav               # Efeitos sonoros
├── conf/                   # Arquivos de configuração
│   ├── options.ini         # Configurações gerais do jogo
│   └── controls.ini        # Mapeamento de controles
├── tests/                  # Testes de fidelidade do port
│   └── test_port_fidelity.py  # 17 testes de consistência C++ ↔ Python
├── requirements.txt        # Dependências Python
├── run_game.sh             # Script para executar o jogo
└── LICENSE                 # Licença MIT
```

## 🚀 Instalação e Execução

### Pré-requisitos

- **Python** 3.10 ou superior
- **Pygame** 2.0.0 ou superior

### Passo a passo

```bash
# 1. Clone o repositório
git clone https://github.com/p19091985/port-groundfire-for-python.git
cd port-groundfire-for-python

# 2. Crie e ative o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute o jogo
python src/main.py
```

Ou utilize o script de execução:

```bash
./run_game.sh
```

## ⚙️ Configuração

### Opções do Jogo (`conf/options.ini`)

O arquivo de configuração permite ajustar diversos parâmetros:

- **Gráficos** — Resolução (`ScreenWidth`, `ScreenHeight`), modo tela cheia
- **Gameplay** — Dano das armas, tempo de recarga, propriedades do terreno
- **Tanque** — Velocidade de movimento, combustível dos Jump Jets, potência máxima
- **Terremotos** — Frequência, duração, intensidade
- **Efeitos** — Taxa de desvanecimento de explosões, trilhas e fumaça

### Controles (`conf/controls.ini`)

Mapeamento de teclas por jogador, suportando múltiplos esquemas de controle.

## 🔄 Status do Port (C++ → Python)

### ✅ Componentes Portados

| Componente | Arquivo C++ | Arquivo Python | Status |
|-----------|-------------|----------------|--------|
| Motor do Jogo | `game.cc/.hh` | `game.py` | ✅ Portado |
| Tanque | `tank.cc/.hh` | `tank.py` | ✅ Portado |
| Jogador | `player.cc/.hh` | `player.py` | ✅ Portado |
| Jogador IA | `aiplayer.cc/.hh` | `aiplayer.py` | ✅ Portado |
| Jogador Humano | `humanplayer.cc/.hh` | `humanplayer.py` | ✅ Portado |
| Terreno | `landscape.cc/.hh` | `landscape.py` | ✅ Portado |
| Entidade Base | `entity.cc/.hh` | `entity.py` | ✅ Portado |
| Arma Base | `weapon.cc/.hh` | `weapon.py` | ✅ Portado |
| Projétil Shell | `shell.cc/.hh` | `shell.py` | ✅ Portado |
| Míssil | `missile.cc/.hh` | `missile.py` | ✅ Portado |
| MIRV | `mirv.cc/.hh` | `mirv.py` | ✅ Portado |
| Metralhadora | `machinegunround.cc/.hh` | `machinegunround.py` | ✅ Portado |
| ShellWeapon | `shellweapon.cc/.hh` | `weapons_impl.py` | ✅ Portado |
| MissileWeapon | `missileweapon.cc/.hh` | `weapons_impl.py` | ✅ Portado |
| MirvWeapon | `mirvweapon.cc/.hh` | `weapons_impl.py` | ✅ Portado |
| NukeWeapon | `nukeweapon.cc/.hh` | `weapons_impl.py` | ✅ Portado |
| MachineGunWeapon | `machinegunweapon.cc/.hh` | `weapons_impl.py` | ✅ Portado |
| Explosão | `blast.cc/.hh` | `blast.py` | ✅ Portado |
| Fumaça | `smoke.cc/.hh` | `smoke.py` | ✅ Portado |
| Trilha | `trail.cc/.hh` | `trail.py` | ✅ Portado |
| Terremoto | `quake.cc/.hh` | `quake.py` | ✅ Portado |
| Interface | `interface.cc/.hh` | `interface.py` | ✅ Portado (Pygame) |
| Som | `sounds.cc/.hh` | `sounds.py` | ✅ Portado |
| Fontes | `font.cc/.hh` | `font.py` | ✅ Portado |
| Menus | `*menu.cc/.hh` | `*menu.py` | ✅ Portado |
| Controles | `controls.cc/.hh` | `controls.py` | ✅ Portado |
| Leitor INI | `inifile.cc/.hh` | `inifile.py` | ✅ Portado |
| Funções Comuns | `common.hh` | `common.py` | ✅ Portado |

### 🔧 Diferenças Técnicas entre C++ e Python

| Aspecto | C++ Original | Python Port |
|---------|-------------|-------------|
| **Gráficos** | OpenGL direto | Pygame (SDL2) |
| **Áudio** | OpenAL/ALUT | Pygame.mixer |
| **Janela** | GLFW | Pygame display |
| **Texturas** | TGA via OpenGL | TGA via Pygame Surface |
| **Compilação** | Makefile + g++ | Interpretado (Python 3) |
| **Armas** | Cada arma em arquivo separado | Consolidadas em `weapons_impl.py` |

### 🧪 Testes de Fidelidade

O projeto inclui uma suíte de **17 testes de fidelidade** (`tests/test_port_fidelity.py`) que verificam a consistência entre a implementação C++ original e o port Python:

1. **Funções matemáticas** — `PI`, `sqr`, `deg_sin`, `deg_cos`
2. **Parsing de INI** — Leitura correta de `groundfire.ini`
3. **Centro do tanque** — `Tank.get_centre()` retorna valores corretos
4. **Posição de lançamento** — Cálculos de posição do canhão
5. **Velocidade de lançamento** — Cálculos de velocidade dos projéteis
6. **Sistema de dano** — `Tank.do_damage()` com lógica fiel ao original
7. **Reset pré-rodada** — `Tank.do_pre_round()` reinicializa estados
8. **Dano de explosão** — Cálculos de dano por proximidade
9. **Pontuação** — `Player.end_round()` com scoring correto
10. **Comportamento da IA** — Lógica de decisão e mira
11. **Ciclo de vida de entidades** — `do_pre_round` / `do_post_round`
12. **Início de rodada** — `Game._start_round()` inicializa corretamente
13. **Fim de rodada** — `Game._end_round()` e limpeza de jogadores
14. **Integridade de métodos** — Sem duplicação acidental de código
15. **Sistema de combustão** — `Tank.burn()` com `_exhaust_time`
16. **Cadeia de update** — `Tank.update()` → `Player.update()` corretamente
17. **Explosão no terreno** — `Explosion` usa `make_hole` no landscape

Executar os testes:
```bash
python tests/test_port_fidelity.py
```

## 📋 Arquitetura do Sistema

```
┌──────────────────────────────────────────────┐
│                 Game (game.py)                │
│          Loop principal + Estado              │
├─────────┬─────────────┬──────────────────────┤
│         │             │                      │
│    Landscape     Entity List            Players
│  (landscape.py)  (entity.py)         (player.py)
│         │             │                  │
│   Terreno        Projéteis          ┌────┴────┐
│   destrutível    Explosões          │         │
│   Colisões       Fumaça         AIPlayer  HumanPlayer
│                  Trilhas        (aiplayer) (humanplayer)
│                                     │         │
│                                     └────┬────┘
│                                          │
│                                       Tank
│                                     (tank.py)
│                                        │
│                                     Weapons
│                                (weapon.py + weapons_impl.py)
└──────────────────────────────────────────────┘
```

### Fluxo do Loop Principal

1. **`Game.loop_once()`** — Chamado a cada frame
2. Calcula o tempo decorrido (`elapsed_time`)
3. Se em jogo → **`game_loop()`**: atualiza todas as entidades e verifica fim de rodada
4. Se em menu → **`menu_loop()`**: atualiza e desenha o menu atual
5. Desenha a interface e atualiza a tela

### Cadeia de Atualização dos Tanques

```
Tank.update(time)
  ├── move_tank(time)      → Movimento horizontal e Jump Jets
  ├── update_gun(time)     → Ângulo e potência do canhão
  ├── weapon.fire()        → Disparo de armas
  ├── weapon.update()      → Cooldown e estado das armas
  ├── player.update(time)  → IA pensa / Humano lê inputs
  └── burn(time)           → Fumaça se o tanque está destruído
```

> **Nota importante:** No C++ original, `Tank::update()` chama `Player::update()`, e **não** o contrário. A IA em `AIPlayer.update()` **não** chama `Tank.update()`, evitando recursão infinita. Esta arquitetura foi fielmente mantida no port Python.

## 🏆 Sistema de Pontuação

| Evento | Pontos | Moedas |
|--------|--------|--------|
| Destruir oponente | +100 | +50 |
| Destruir o líder | +200 | +50 |
| Destruir a si mesmo | -50 | +0 |
| Sobreviver à rodada | +100 | +25 |
| Cada rodada (todos) | — | +10 |

## 📜 Licença e Créditos

- **Autor original:** Tom Russell (`tom@groundfire.net`)
- **Port para Python:** [p19091985](https://github.com/p19091985)
- **Licença:** MIT License (ver arquivo `LICENSE`)
- **Website original:** www.groundfire.net (histórico)

---

<p align="center">
  <em>Este projeto é um port educacional e de preservação do jogo Groundfire v0.25.</em><br>
  <em>O código-fonte original em C++ está incluído no diretório <code>groundfire-0.25/</code> para referência.</em>
</p>