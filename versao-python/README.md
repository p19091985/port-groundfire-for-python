# Groundfire — Edição Python (standalone)

Pasta independente. Copie **esta pasta inteira** (`versao-python/`) para uma
máquina compatível e abra o jogo pelos launchers abaixo, sem a raiz do
repositório nem a outra edição (`versao-godot/`).

## Fluxo completo (fonte isolada)

Pré-requisitos (desenvolvimento de fonte): Python 3.10–3.14.

```sh
# Linux/macOS
./run_game.sh

# Windows CMD
run_game.bat

# Windows PowerShell
./run_game.ps1
```

Os launchers criam `.venv/` **dentro desta pasta**, instalam com
`pip install -e .` (nunca `pip -e ..`) e guardam dados em `userdata/`.
Se `userdata/` não for gravável, o launcher mostra erro claro e sai.

## LAN local (sem internet)

```sh
./iniciar-server.sh -A
./iniciar-clientes.sh -4
./iniciar-all.sh -A
```

No Windows, use os equivalentes `.bat`/`.ps1` (mesmo nome, sem Git Bash).
`PYTHONPATH` é sempre `esta-pasta:esta-pasta/src`; nenhum passo lê `../`,
`groundfire_net/` da raiz, `.venv` de outra pasta ou a edição Godot.

## Pacote portátil (sem Python/pip/rede)

`runtime/windows/` (e `runtime/linux/` após o build em Linux) contém
`Groundfire`, `groundfire-server`, `groundfire-master`,
`groundfire-web-gateway` e `groundfire-directory` com bibliotecas
compartilhadas em `_internal/`. Assets e configuração ficam na própria
pasta, em caminhos relativos. `run_game.*` e `iniciar-*` executam o
binário interno automaticamente; `GROUNDFIRE_FORCE_SOURCE=1` força o
modo fonte. O build usa PyInstaller e não faz cross-compile: rode na
plataforma de destino, com a `.venv` local instalada:

```sh
pip install pyinstaller
python scripts/build_portable.py --platform windows   # ou linux
python scripts/generate_runtime_manifest.py
```

Distribuição: ZIP com `versao-python/` como pasta superior; extrair e
abrir `run_game.*` é o fluxo completo. Verificação:

```sh
python scripts/generate_runtime_manifest.py
python scripts/vendor_groundfire_net.py --check
```

## Dados portáteis

`userdata/` guarda preferências, favoritos, histórico, logs e saves.
Mover a pasta preserva configurações; execução offline não cria dados
fora dela. Internet gerenciada (`servico-externo/`) é serviço remoto
independente e nunca bloqueia menu, partida local ou LAN.
