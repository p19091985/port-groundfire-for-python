# Visual de Windows XP para Linux

Esta pasta contém um script que instala e configura uma sessão XFCE para ficar
parecida com o Windows XP. Ele modifica apenas a aparência e as preferências do
ambiente gráfico; o sistema continua sendo Linux.

## Instalação

Abra um terminal na raiz do projeto e execute como usuário normal, sem `sudo`:

```bash
./windows-xp/windows-xpify.sh
```

O script pedirá a senha administrativa somente quando precisar instalar os
pacotes do XFCE. Depois da instalação, encerre a sessão, escolha **Xfce Session**
na tela de login e entre novamente. A configuração será aplicada automaticamente.

## Interface gráfica com Tkinter/ttk

Para escolher os parâmetros por uma janela gráfica, execute:

```bash
python3 windows-xp/windows-xp-gui.py
```

Também é possível abrir diretamente o arquivo `windows-xp-gui.py` pelo
gerenciador de arquivos. A interface permite escolher:

- tema visual;
- texto do botão Iniciar;
- painel de arquivos Tree ou atalhos;
- barra de tarefas embaixo ou em cima;
- altura da barra de tarefas;
- instalação automática dos pacotes;
- instalação, reaplicação e restauração de backups.

As operações são abertas em uma janela de terminal para permitir a digitação da
senha administrativa quando ela for necessária.

Se a interface não abrir por falta do Tkinter, instale o pacote correspondente:

```bash
# Debian ou Ubuntu
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch Linux
sudo pacman -S tk
```

O visual padrão é o **Windows XP Classic**, com controles cinza, barras de título
azuis, painel inferior, botão **iniciar**, ícones, cursores, fonte compacta e o
fundo azul clássico. Sombras e transparências modernas são desativadas.

O gerenciador de arquivos abre com um painel **Tree** à esquerda, linhas de
hierarquia, barra de endereço, barra de menus e barra de status, semelhante ao
Windows Explorer clássico. A barra de tarefas permanece fixa embaixo da tela.

## Painel Tree e barra de tarefas

Essas configurações já são o padrão. Para declará-las explicitamente:

```bash
./windows-xp/windows-xpify.sh \
  --file-pane tree \
  --taskbar-position bottom \
  --taskbar-size 28
```

Para usar a lista de atalhos no lugar da árvore de diretórios:

```bash
./windows-xp/windows-xpify.sh --file-pane shortcuts
```

Também é possível colocar a barra no topo ou mudar sua altura:

```bash
./windows-xp/windows-xpify.sh --taskbar-position top --taskbar-size 32
```

## Outras variantes

```bash
./windows-xp/windows-xpify.sh --variant Classic
./windows-xp/windows-xpify.sh --variant Zune
./windows-xp/windows-xpify.sh --variant Royale
./windows-xp/windows-xpify.sh --variant Metallic
./windows-xp/windows-xpify.sh --variant Homestead
```

As variantes disponíveis são `Classic` (padrão), `Luna`, `Homestead`,
`Metallic`, `Royale`, `Royale-Dark`, `Embedded` e `Zune`.

Para mudar o texto do botão Iniciar:

```bash
./windows-xp/windows-xpify.sh --start-label "Iniciar"
```

## Restaurar a aparência anterior

O script salva automaticamente as configurações antigas antes de aplicar o
tema. Para restaurar o backup mais recente:

```bash
~/.local/bin/xpify-linux --restore
```

Para listar todos os backups:

```bash
~/.local/bin/xpify-linux --list-backups
```

Se algum detalhe visual permanecer depois da restauração, encerre a sessão e
entre novamente.

## Opções úteis

```text
--variant NOME      Escolhe Classic, Luna, Royale e outras variantes
--start-label TEXTO Altera o texto do botão Iniciar
--file-pane TIPO    Usa tree ou shortcuts no painel do gerenciador
--taskbar-position  Usa bottom ou top para posicionar a barra
--taskbar-size PX   Define a altura da barra entre 20 e 80 pixels
--no-packages       Não instala pacotes do sistema
--apply-only        Apenas reaplica a configuração já instalada
--restore [PASTA]   Restaura um backup específico ou o mais recente
--list-backups      Lista os backups disponíveis
--help              Mostra a ajuda completa
```

## Compatibilidade

A instalação automática de pacotes reconhece:

- Debian e Ubuntu;
- Fedora;
- Arch Linux;
- openSUSE.

Em outra distribuição, instale manualmente o XFCE, `git` e `curl`, e execute:

```bash
./windows-xp/windows-xpify.sh --no-packages
```

## Projetos utilizados

- [B00merang Windows Classic](https://github.com/B00merang-Project/Windows-Classic)
- [B00merang Windows XP](https://github.com/B00merang-Project/Windows-XP)
- [B00merang Windows XP Icons](https://github.com/B00merang-Artwork/Windows-XP)
- [ModernXP Cursor Theme](https://github.com/na0miluv/modernXP-cursor-theme)

