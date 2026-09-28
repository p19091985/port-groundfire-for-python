# Groundfire — Edição Godot (standalone)

Pasta independente. Copie **esta pasta inteira** (`versao-godot/`) para uma
máquina compatível e abra o jogo pelos launchers abaixo, sem a raiz do
repositório nem a outra edição (`versao-python/`).

## Fluxo completo (fonte isolada)

Pré-requisito (desenvolvimento de fonte): Godot 4 compatível com
`godot/project.godot` ou binário em `runtime/<plataforma>/`.

```sh
# Linux/macOS
./run_game.sh
./iniciar-server.sh -A --server-name "Groundfire Godot LAN"
./iniciar-clientes.sh -n 2
./iniciar-all.sh -n 2
```

No Windows (sem Git Bash):

```bat
run_game.bat
iniciar-server.bat -A
iniciar-clientes.bat -n 2
```

```powershell
./run_game.ps1
./iniciar-server.ps1 -A
```

O projeto abre após copiar apenas esta pasta. O export desktop usa o
binário Godot incluído em `runtime/`; nunca as ferramentas da raiz.
`export_presets.cfg` grava dentro de `runtime/` (nunca `../../build`).

## Servidor e gateway incluídos

`runtime/headless/` contém o companion versionado (servidor LAN
autoritativo + gateway/directory, sem pygame). `runtime/windows/`
traz o jogo exportado ao lado do companion congelado
(`groundfire-server`, `groundfire-web-gateway`); `runtime/linux/`
traz o jogo exportado e usa o companion fonte (o congelado Linux
exige o build do companion numa máquina Linux).
`iniciar-*` prefere o binário local e cai para o companion fonte com
o Python da máquina; nenhum launcher chama `../versao-python`. O menu
Godot resolve o gateway ao lado do executável no jogo exportado e em
`res://../runtime/` no editor — nunca um venv externo.

Companion e jogo recebem clientes Godot e Python compatíveis, com
espectador; a parada recolhe somente processos que criou. Para
reconstruir (Godot 4.6.2 + PyInstaller, na plataforma de destino):

```sh
python scripts/vendor_headless.py
python scripts/build_companion.py --platform windows   # ou linux
godot --headless --path godot --export-release "Windows Desktop"
godot --headless --path godot --export-release "Linux Desktop"
godot --headless --path godot --export-release "Web"
python scripts/generate_runtime_manifest.py
```

## Dados portáteis e web

`userdata/` guarda configurações; mover a pasta preserva tudo; offline
não cria dados fora dela. Web é alvo separado: `runtime/web/` servido
por HTTP(S) roda partida local sem serviço externo; UDP/LAN indisponíveis.

Distribuição: ZIP com `versao-godot/` como pasta superior; extrair e
abrir o launcher é o fluxo completo. Verificação:

```sh
python scripts/generate_runtime_manifest.py
```
