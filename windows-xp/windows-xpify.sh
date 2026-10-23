#!/usr/bin/env bash
# Deixa uma sessao XFCE parecida com o Windows XP no tema Classic.
# Executar como usuario normal: ./windows-xp/windows-xpify.sh
#
# Temas usados:
#   https://github.com/B00merang-Project/Windows-Classic (GPL-3.0)
#   https://github.com/B00merang-Project/Windows-XP (GPL-3.0)
#   https://github.com/B00merang-Artwork/Windows-XP (GPL-2.0)
#   https://github.com/na0miluv/modernXP-cursor-theme (GPL-3.0),
#     binarios compilados distribuidos por omarchy-xp-theme.

set -Eeuo pipefail

PROGRAM_NAME="xpify-linux"
VERSION="1.3.0"
CLASSIC_THEME_REPO="https://github.com/B00merang-Project/Windows-Classic.git"
THEME_REPO="https://github.com/B00merang-Project/Windows-XP.git"
ICON_REPO="https://github.com/B00merang-Artwork/Windows-XP.git"
CURSOR_REPO="https://github.com/raccoon-overlord-dev/omarchy-xp-theme.git"

ACTION="install"
VARIANT="Classic"
START_LABEL="iniciar"
# Opcoes visuais padrao. Tambem podem ser alteradas pela linha de comando.
FILE_PANE="tree"
TASKBAR_POSITION="bottom"
TASKBAR_SIZE=28
INSTALL_PACKAGES=1
RESTORE_SOURCE=""
TEMP_DIR=""

STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/$PROGRAM_NAME"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}"
THEMES_DIR="$DATA_DIR/themes"
ICONS_DIR="$DATA_DIR/icons"
BACKGROUNDS_DIR="$DATA_DIR/backgrounds"
AUTOSTART_FILE="$CONFIG_DIR/autostart/xpify-first-login.desktop"
INSTALLED_SCRIPT="$HOME/.local/bin/$PROGRAM_NAME"
WALLPAPER="$BACKGROUNDS_DIR/windows-xp-wallpaper.svg"

log() { printf '\033[1;34m[xpify]\033[0m %s\n' "$*"; }
ok() { printf '\033[1;32m[xpify]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[xpify]\033[0m %s\n' "$*" >&2; }
die() { printf '\033[1;31m[xpify] Erro:\033[0m %s\n' "$*" >&2; exit 1; }

cleanup() {
    if [[ -n "$TEMP_DIR" && -d "$TEMP_DIR" ]]; then
        rm -rf -- "$TEMP_DIR"
    fi
}
trap cleanup EXIT

usage() {
    cat <<'EOF'
Uso:
  ./windows-xpify.sh [opcoes]
  ./windows-xpify.sh --restore [PASTA_DO_BACKUP]

Opcoes:
  --variant NOME       Classic, Luna, Homestead, Metallic, Royale,
                       Royale-Dark, Embedded ou Zune (padrao: Classic)
  --start-label TEXTO  Texto do botao Iniciar (padrao: iniciar)
  --file-pane TIPO     Painel lateral do gerenciador: tree ou shortcuts
                       (padrao: tree)
  --taskbar-position P Posicao da barra: bottom ou top (padrao: bottom)
  --taskbar-size PX    Altura da barra entre 20 e 80 (padrao: 28)
  --no-packages        Nao instala o XFCE nem dependencias do sistema
  --apply-only         Aplica a configuracao; nao baixa temas nem pacotes
  --restore [PASTA]    Restaura um backup (usa o mais recente se omitido)
  --list-backups       Lista os backups disponiveis
  -h, --help           Mostra esta ajuda

Execute como usuario normal, sem sudo. O script chama sudo apenas para instalar
pacotes. Se a sessao atual nao for XFCE, selecione "Xfce Session" na tela de
login; a aparencia sera aplicada automaticamente no primeiro acesso.
EOF
}

variant_theme_name() {
    case "${1,,}" in
        classic|classico|clássico) printf '%s' "Windows Classic" ;;
        luna)         printf '%s' "Windows XP Luna" ;;
        homestead|olive) printf '%s' "Windows XP Homestead" ;;
        metallic|silver) printf '%s' "Windows XP Metallic" ;;
        royale)       printf '%s' "Windows XP Royale" ;;
        royale-dark|royale_dark|noir) printf '%s' "Windows XP Royale Dark" ;;
        embedded)     printf '%s' "Windows XP Embedded" ;;
        zune)         printf '%s' "Windows XP Zune" ;;
        *) die "Variante desconhecida: $1" ;;
    esac
}

while (($#)); do
    case "$1" in
        --variant)
            (($# >= 2)) || die "--variant exige um nome"
            VARIANT="$2"
            shift 2
            ;;
        --start-label)
            (($# >= 2)) || die "--start-label exige um texto"
            START_LABEL="$2"
            shift 2
            ;;
        --file-pane)
            (($# >= 2)) || die "--file-pane exige tree ou shortcuts"
            FILE_PANE="$2"
            shift 2
            ;;
        --taskbar-position)
            (($# >= 2)) || die "--taskbar-position exige bottom ou top"
            TASKBAR_POSITION="$2"
            shift 2
            ;;
        --taskbar-size)
            (($# >= 2)) || die "--taskbar-size exige um numero"
            TASKBAR_SIZE="$2"
            shift 2
            ;;
        --no-packages)
            INSTALL_PACKAGES=0
            shift
            ;;
        --apply-only)
            ACTION="apply"
            INSTALL_PACKAGES=0
            shift
            ;;
        --restore)
            ACTION="restore"
            if (($# >= 2)) && [[ "$2" != -* ]]; then
                RESTORE_SOURCE="$2"
                shift 2
            else
                shift
            fi
            ;;
        --list-backups)
            ACTION="list-backups"
            shift
            ;;
        --from-autostart)
            shift
            ;;
        --version)
            printf '%s %s\n' "$PROGRAM_NAME" "$VERSION"
            exit 0
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *) die "Opcao desconhecida: $1 (use --help)" ;;
    esac
done

case "${FILE_PANE,,}" in
    tree|arvore|árvore) FILE_PANE="tree" ;;
    shortcuts|atalhos) FILE_PANE="shortcuts" ;;
    *) die "Painel de arquivos invalido: $FILE_PANE (use tree ou shortcuts)" ;;
esac

case "${TASKBAR_POSITION,,}" in
    bottom|baixo|embaixo) TASKBAR_POSITION="bottom" ;;
    top|cima|emcima) TASKBAR_POSITION="top" ;;
    *) die "Posicao da barra invalida: $TASKBAR_POSITION (use bottom ou top)" ;;
esac

[[ "$TASKBAR_SIZE" =~ ^[0-9]+$ ]] || die "O tamanho da barra deve ser numerico"
TASKBAR_SIZE=$((10#$TASKBAR_SIZE))
((TASKBAR_SIZE >= 20 && TASKBAR_SIZE <= 80)) || \
    die "O tamanho da barra deve estar entre 20 e 80 pixels"

THEME_NAME="$(variant_theme_name "$VARIANT")"

if ((EUID == 0)); then
    die "Nao execute com sudo. Rode como usuario normal: ./windows-xpify.sh"
fi

require_command() {
    command -v "$1" >/dev/null 2>&1 || die "Comando necessario nao encontrado: $1"
}

run_sudo() {
    command -v sudo >/dev/null 2>&1 || die "sudo nao encontrado; instale os pacotes manualmente"
    sudo "$@"
}

install_system_packages() {
    ((INSTALL_PACKAGES)) || return 0
    log "Detectando o gerenciador de pacotes e instalando o XFCE..."

    if command -v apt-get >/dev/null 2>&1; then
        run_sudo apt-get update
        run_sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y \
            xfce4 xfce4-goodies git curl ca-certificates fonts-liberation2 dbus-x11
    elif command -v dnf >/dev/null 2>&1; then
        run_sudo dnf install -y @xfce-desktop-environment \
            git curl ca-certificates liberation-sans-fonts
    elif command -v pacman >/dev/null 2>&1; then
        run_sudo pacman -Syu --needed --noconfirm \
            xfce4 xfce4-goodies git curl ca-certificates ttf-liberation
    elif command -v zypper >/dev/null 2>&1; then
        run_sudo zypper --non-interactive install \
            -t pattern xfce
        run_sudo zypper --non-interactive install \
            git curl ca-certificates liberation-fonts
    else
        die "Distribuicao nao suportada automaticamente. Use --no-packages apos instalar XFCE, git e curl."
    fi
}

make_backup() {
    local stamp backup
    stamp="$(date +'%Y%m%d-%H%M%S')"
    backup="$STATE_DIR/backups/$stamp"
    mkdir -p "$backup"

    if [[ -d "$CONFIG_DIR/xfce4" ]]; then
        cp -a "$CONFIG_DIR/xfce4" "$backup/xfce4"
        printf 'present\n' >"$backup/xfce4.status"
    else
        printf 'absent\n' >"$backup/xfce4.status"
    fi
    if [[ -f "$HOME/.gtkrc-2.0" ]]; then
        cp -a "$HOME/.gtkrc-2.0" "$backup/gtkrc-2.0"
        printf 'present\n' >"$backup/gtkrc-2.0.status"
    else
        printf 'absent\n' >"$backup/gtkrc-2.0.status"
    fi
    printf '%s\n' "$THEME_NAME" >"$backup/applied-theme"
    printf '%s\n' "$backup" >"$STATE_DIR/latest-backup"
    ok "Backup criado em $backup"
}

list_backups() {
    local found=0 path
    if [[ -d "$STATE_DIR/backups" ]]; then
        while IFS= read -r path; do
            printf '%s\n' "$path"
            found=1
        done < <(find "$STATE_DIR/backups" -mindepth 1 -maxdepth 1 -type d | sort -r)
    fi
    ((found)) || warn "Nenhum backup encontrado em $STATE_DIR/backups"
}

restore_backup() {
    local source="$RESTORE_SOURCE" stamp displaced
    if [[ -z "$source" && -f "$STATE_DIR/latest-backup" ]]; then
        source="$(<"$STATE_DIR/latest-backup")"
    fi
    [[ -n "$source" && -d "$source" ]] || die "Backup nao encontrado. Use --list-backups."

    stamp="$(date +'%Y%m%d-%H%M%S')"
    displaced="$STATE_DIR/before-restore/$stamp"
    mkdir -p "$displaced"

    if [[ -d "$CONFIG_DIR/xfce4" ]]; then
        mv "$CONFIG_DIR/xfce4" "$displaced/xfce4"
    fi
    if [[ -f "$HOME/.gtkrc-2.0" ]]; then
        mv "$HOME/.gtkrc-2.0" "$displaced/gtkrc-2.0"
    fi

    if [[ -d "$source/xfce4" ]]; then
        cp -a "$source/xfce4" "$CONFIG_DIR/xfce4"
    fi
    if [[ -f "$source/gtkrc-2.0" ]]; then
        cp -a "$source/gtkrc-2.0" "$HOME/.gtkrc-2.0"
    fi
    rm -f -- "$AUTOSTART_FILE"

    # O xfconfd mantem valores em memoria; reinicia-lo evita que a configuracao
    # antiga seja gravada novamente sobre os arquivos restaurados.
    if command -v pkill >/dev/null 2>&1; then
        pkill -u "$(id -u)" -x xfconfd >/dev/null 2>&1 || true
    fi
    if command -v xfce4-panel >/dev/null 2>&1 && [[ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]]; then
        xfce4-panel --restart >/dev/null 2>&1 || true
    fi
    ok "Backup restaurado: $source"
    log "A configuracao substituida foi preservada em $displaced"
    log "Se algum detalhe visual persistir, encerre a sessao e entre novamente."
}

preserve_existing() {
    local destination="$1" label="$2" stamp preserved
    [[ -e "$destination" ]] || return 0
    stamp="$(date +'%Y%m%d-%H%M%S')"
    preserved="$STATE_DIR/replaced-assets/$stamp/$label"
    mkdir -p "$(dirname "$preserved")"
    mv "$destination" "$preserved"
}

install_assets() {
    local source item cursor_source
    require_command git
    TEMP_DIR="$(mktemp -d)"
    mkdir -p "$THEMES_DIR" "$ICONS_DIR" "$BACKGROUNDS_DIR" "$STATE_DIR"

    log "Baixando os temas visuais do Windows XP..."
    git clone --depth 1 --quiet "$THEME_REPO" "$TEMP_DIR/themes"
    for source in "$TEMP_DIR/themes"/Windows\ XP\ *; do
        [[ -d "$source" ]] || continue
        item="$(basename "$source")"
        preserve_existing "$THEMES_DIR/$item" "themes/$item"
        cp -a "$source" "$THEMES_DIR/$item"
    done

    log "Baixando o tema Windows XP Classic..."
    git clone --depth 1 --quiet "$CLASSIC_THEME_REPO" "$TEMP_DIR/classic"
    preserve_existing "$THEMES_DIR/Windows Classic" "themes/Windows Classic"
    cp -a "$TEMP_DIR/classic" "$THEMES_DIR/Windows Classic"
    rm -rf -- "$THEMES_DIR/Windows Classic/.git"

    log "Baixando o conjunto de icones..."
    git clone --depth 1 --quiet "$ICON_REPO" "$TEMP_DIR/icons"
    preserve_existing "$ICONS_DIR/Windows XP" "icons/Windows XP"
    mkdir -p "$ICONS_DIR/Windows XP"
    cp -a "$TEMP_DIR/icons/." "$ICONS_DIR/Windows XP/"
    rm -rf -- "$ICONS_DIR/Windows XP/.git"

    log "Baixando os cursores no estilo XP..."
    git clone --depth 1 --quiet "$CURSOR_REPO" "$TEMP_DIR/cursors"
    cursor_source="$TEMP_DIR/cursors/cursors/ModernXP"
    [[ -f "$cursor_source/index.theme" ]] || die "Tema de cursor ModernXP nao encontrado"
    preserve_existing "$ICONS_DIR/ModernXP" "icons/ModernXP"
    cp -a "$cursor_source" "$ICONS_DIR/ModernXP"

    create_wallpaper
    gtk-update-icon-cache -f -t "$ICONS_DIR/Windows XP" >/dev/null 2>&1 || true
    ok "Temas instalados somente para o usuario $USER."
}

create_wallpaper() {
    if [[ "$THEME_NAME" == "Windows Classic" ]]; then
        # Cor de area de trabalho padrao da interface classica do Windows.
        cat >"$WALLPAPER" <<'SVG'
<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080">
  <rect width="100%" height="100%" fill="#3a6ea5"/>
</svg>
SVG
        return
    fi

    # Paisagem original inspirada na paleta do XP; nao e uma copia do Bliss.
    cat >"$WALLPAPER" <<'SVG'
<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">
  <defs>
    <linearGradient id="sky" x2="0" y2="1"><stop stop-color="#1884df"/><stop offset="1" stop-color="#8ed4ff"/></linearGradient>
    <linearGradient id="hill" x2="0" y2="1"><stop stop-color="#70c72f"/><stop offset="1" stop-color="#238a19"/></linearGradient>
    <filter id="soft"><feGaussianBlur stdDeviation="9"/></filter>
  </defs>
  <rect width="1920" height="1080" fill="url(#sky)"/>
  <g fill="#fff" opacity=".88" filter="url(#soft)">
    <ellipse cx="330" cy="250" rx="170" ry="49"/><ellipse cx="240" cy="240" rx="95" ry="68"/><ellipse cx="405" cy="225" rx="110" ry="79"/>
    <ellipse cx="1420" cy="180" rx="150" ry="43"/><ellipse cx="1340" cy="170" rx="80" ry="55"/><ellipse cx="1490" cy="155" rx="100" ry="68"/>
  </g>
  <path d="M0 680 C290 480 620 430 970 570 C1320 710 1550 520 1920 420 L1920 1080 L0 1080Z" fill="url(#hill)"/>
  <path d="M0 790 C350 630 700 650 1020 770 C1330 885 1650 760 1920 660 L1920 1080 L0 1080Z" fill="#4caf28" opacity=".82"/>
  <path d="M0 950 C430 780 840 850 1220 920 C1510 975 1710 900 1920 820 L1920 1080 L0 1080Z" fill="#2d941d" opacity=".55"/>
</svg>
SVG
}

xfset() {
    local channel="$1" property="$2" type="$3" value="$4"
    xfconf-query -c "$channel" -p "$property" -n -t "$type" -s "$value" >/dev/null
}

set_existing_or_create() {
    local channel="$1" property="$2" type="$3" value="$4"
    xfconf-query -c "$channel" -p "$property" -s "$value" >/dev/null 2>&1 || \
        xfset "$channel" "$property" "$type" "$value"
}

plugin_available() {
    local plugin="$1" file
    for file in \
        "/usr/share/xfce4/panel/plugins/$plugin.desktop" \
        "/usr/local/share/xfce4/panel/plugins/$plugin.desktop" \
        "$DATA_DIR/xfce4/panel/plugins/$plugin.desktop"; do
        [[ -f "$file" ]] && return 0
    done
    return 1
}

configure_panel() {
    local -a ids=()
    local next_id=1 plugin panel_position

    if [[ "$TASKBAR_POSITION" == "bottom" ]]; then
        panel_position="p=12;x=0;y=0"
    else
        panel_position="p=11;x=0;y=0"
    fi

    xfconf-query -c xfce4-panel -p /panels -r -R >/dev/null 2>&1 || true
    xfconf-query -c xfce4-panel -p /plugins -r -R >/dev/null 2>&1 || true
    xfconf-query -c xfce4-panel -p /panels -n -a -t int -s 1 >/dev/null
    xfset xfce4-panel /panels/panel-1/position string "$panel_position"
    xfset xfce4-panel /panels/panel-1/position-locked bool true
    xfset xfce4-panel /panels/panel-1/length uint 100
    xfset xfce4-panel /panels/panel-1/length-adjust bool false
    xfset xfce4-panel /panels/panel-1/mode uint 0
    xfset xfce4-panel /panels/panel-1/size uint "$TASKBAR_SIZE"
    xfset xfce4-panel /panels/panel-1/nrows uint 1
    xfset xfce4-panel /panels/panel-1/autohide-behavior uint 0
    xfset xfce4-panel /panels/panel-1/icon-size uint 16

    add_plugin() {
        plugin="$1"
        plugin_available "$plugin" || return 1
        ids+=("$next_id")
        xfset xfce4-panel "/plugins/plugin-$next_id" string "$plugin"
        ADDED_PLUGIN_ID="$next_id"
        ((next_id += 1))
    }

    add_plugin applicationsmenu || die "Plugin applicationsmenu do XFCE nao encontrado"
    local menu_id="${ADDED_PLUGIN_ID:-1}"
    xfset xfce4-panel "/plugins/plugin-$menu_id/show-button-title" bool true
    xfset xfce4-panel "/plugins/plugin-$menu_id/button-title" string "$START_LABEL"
    xfset xfce4-panel "/plugins/plugin-$menu_id/show-button-icon" bool true
    xfset xfce4-panel "/plugins/plugin-$menu_id/button-icon" string "start-here"

    add_plugin separator || die "Plugin separator do XFCE nao encontrado"
    local sep1="${ADDED_PLUGIN_ID:-2}"
    xfset xfce4-panel "/plugins/plugin-$sep1/expand" bool false
    xfset xfce4-panel "/plugins/plugin-$sep1/style" uint 0

    add_plugin tasklist || die "Plugin tasklist do XFCE nao encontrado"
    local task_id="${ADDED_PLUGIN_ID:-3}"
    xfset xfce4-panel "/plugins/plugin-$task_id/show-labels" bool true
    xfset xfce4-panel "/plugins/plugin-$task_id/flat-buttons" bool false
    xfset xfce4-panel "/plugins/plugin-$task_id/grouping" uint 0
    xfset xfce4-panel "/plugins/plugin-$task_id/sort-order" uint 1

    add_plugin separator || die "Plugin separator do XFCE nao encontrado"
    local expand_id="${ADDED_PLUGIN_ID:-4}"
    xfset xfce4-panel "/plugins/plugin-$expand_id/expand" bool true
    xfset xfce4-panel "/plugins/plugin-$expand_id/style" uint 0

    for plugin in statusnotifier pulseaudio power-manager-plugin notification-plugin systray; do
        add_plugin "$plugin" || true
    done
    add_plugin clock || die "Plugin clock do XFCE nao encontrado"
    local clock_id="${ADDED_PLUGIN_ID:-5}"
    xfset xfce4-panel "/plugins/plugin-$clock_id/digital-format" string "%H:%M"
    xfset xfce4-panel "/plugins/plugin-$clock_id/tooltip-format" string "%A, %d de %B de %Y"
    add_plugin showdesktop || warn "Plugin showdesktop do XFCE nao encontrado"

    ((${#ids[@]} > 0)) || die "Nenhum plugin de painel XFCE foi encontrado"
    local -a panel_args=(-c xfce4-panel -p /panels/panel-1/plugin-ids -n -a)
    local id
    for id in "${ids[@]}"; do
        panel_args+=(-t int -s "$id")
    done
    xfconf-query "${panel_args[@]}" >/dev/null
}

configure_wallpaper() {
    local -a properties=()
    local property
    mapfile -t properties < <(xfconf-query -c xfce4-desktop -l 2>/dev/null | grep -E '/(last-image|image-path)$' || true)
    if ((${#properties[@]} == 0)); then
        properties=("/backdrop/screen0/monitor0/workspace0/last-image")
    fi
    for property in "${properties[@]}"; do
        set_existing_or_create xfce4-desktop "$property" string "$WALLPAPER"
        set_existing_or_create xfce4-desktop "${property%/*}/image-style" int 5
    done
    set_existing_or_create xfce4-desktop /desktop-icons/icon-size uint 32
    set_existing_or_create xfce4-desktop /desktop-icons/font-size double 9.0
    set_existing_or_create xfce4-desktop /desktop-icons/show-tooltips bool true
    set_existing_or_create xfce4-desktop /desktop-icons/file-icons/show-home bool true
    set_existing_or_create xfce4-desktop /desktop-icons/file-icons/show-filesystem bool true
    set_existing_or_create xfce4-desktop /desktop-icons/file-icons/show-trash bool true
}

choose_font() {
    if command -v fc-match >/dev/null 2>&1 && fc-match Tahoma 2>/dev/null | grep -qi 'Tahoma'; then
        printf '%s' "Tahoma 8"
    else
        printf '%s' "Liberation Sans 8"
    fi
}

choose_title_font() {
    if command -v fc-match >/dev/null 2>&1 && fc-match Tahoma 2>/dev/null | grep -qi 'Tahoma'; then
        printf '%s' "Tahoma Bold 8"
    else
        printf '%s' "Liberation Sans Bold 8"
    fi
}

configure_xfce() {
    local ui_font title_font thunar_side_pane
    require_command xfconf-query
    [[ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]] || die "Nenhuma sessao grafica detectada"
    ui_font="$(choose_font)"
    title_font="$(choose_title_font)"
    if [[ "$FILE_PANE" == "tree" ]]; then
        thunar_side_pane="ThunarTreePane"
    else
        thunar_side_pane="ThunarShortcutsPane"
    fi

    log "Aplicando tema $THEME_NAME ao XFCE..."
    set_existing_or_create xsettings /Net/ThemeName string "$THEME_NAME"
    set_existing_or_create xsettings /Net/IconThemeName string "Windows XP"
    set_existing_or_create xsettings /Gtk/FontName string "$ui_font"
    set_existing_or_create xsettings /Gtk/MonospaceFontName string "Liberation Mono 10"
    set_existing_or_create xsettings /Gtk/CursorThemeName string "ModernXP"
    set_existing_or_create xsettings /Gtk/CursorThemeSize int 24
    set_existing_or_create xsettings /Gtk/ButtonImages bool true
    set_existing_or_create xsettings /Gtk/MenuImages bool true
    set_existing_or_create xsettings /Gtk/ToolbarStyle string "icons"
    set_existing_or_create xsettings /Net/DoubleClickTime int 500
    set_existing_or_create xsettings /Net/DoubleClickDistance int 5
    set_existing_or_create xsettings /Xft/Antialias int 1
    set_existing_or_create xsettings /Xft/Hinting int 1
    set_existing_or_create xsettings /Xft/HintStyle string "hintfull"
    set_existing_or_create xsettings /Xft/RGBA string "rgb"
    set_existing_or_create xsettings /Xft/DPI int 96

    set_existing_or_create xfwm4 /general/theme string "$THEME_NAME"
    set_existing_or_create xfwm4 /general/title_font string "$title_font"
    set_existing_or_create xfwm4 /general/title_alignment string "left"
    set_existing_or_create xfwm4 /general/button_layout string "O|HMC"
    set_existing_or_create xfwm4 /general/click_to_focus bool true
    set_existing_or_create xfwm4 /general/show_frame_shadow bool false
    set_existing_or_create xfwm4 /general/show_popup_shadow bool false
    set_existing_or_create xfwm4 /general/use_compositing bool false
    set_existing_or_create xfwm4 /general/raise_on_click bool true
    set_existing_or_create xfwm4 /general/raise_delay int 250
    set_existing_or_create xfwm4 /general/snap_to_border bool false
    set_existing_or_create xfwm4 /general/snap_to_windows bool false

    set_existing_or_create xfce4-keyboard-shortcuts /commands/custom/Super_L string "xfce4-popup-applicationsmenu"
    set_existing_or_create xfce4-desktop /desktop-menu/show bool true
    set_existing_or_create thunar /last-view string "ThunarIconView"
    set_existing_or_create thunar /last-side-pane string "$thunar_side_pane"
    set_existing_or_create thunar /last-location-bar string "ThunarLocationEntry"
    set_existing_or_create thunar /last-separator-position int 220
    set_existing_or_create thunar /last-menubar-visible bool true
    set_existing_or_create thunar /last-statusbar-visible bool true
    set_existing_or_create thunar /last-show-hidden bool false
    set_existing_or_create thunar /last-window-width int 900
    set_existing_or_create thunar /last-window-height int 650
    set_existing_or_create thunar /misc-single-click bool false
    set_existing_or_create thunar /misc-tree-lines-in-tree-sidepane bool true
    set_existing_or_create thunar /misc-use-csd bool false
    set_existing_or_create thunar /misc-remember-geometry bool true
    set_existing_or_create thunar /misc-full-path-in-title bool false
    set_existing_or_create thunar /misc-full-path-in-tab-title bool false
    set_existing_or_create xfwm4 /general/workspace_count int 1

    configure_panel
    configure_wallpaper

    mkdir -p "$CONFIG_DIR/gtk-3.0" "$CONFIG_DIR/gtk-4.0"
    cat >"$HOME/.gtkrc-2.0" <<EOF
gtk-theme-name="$THEME_NAME"
gtk-icon-theme-name="Windows XP"
gtk-font-name="$ui_font"
gtk-cursor-theme-name="ModernXP"
gtk-cursor-theme-size=24
EOF

    xfce4-panel --restart >/dev/null 2>&1 || true
    xfdesktop --reload >/dev/null 2>&1 || true
    rm -f -- "$AUTOSTART_FILE"
    ok "Visual do Windows XP aplicado."
}

is_xfce_session() {
    local current_desktop="${XDG_CURRENT_DESKTOP:-}" session="${DESKTOP_SESSION:-}"
    [[ "${current_desktop,,}" == *xfce* || "${session,,}" == *xfce* ]] && \
        [[ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]]
}

install_self_and_autostart() {
    local script_source exec_path escaped_variant escaped_label
    script_source="$(readlink -f "${BASH_SOURCE[0]}")"
    mkdir -p "$(dirname "$INSTALLED_SCRIPT")" "$(dirname "$AUTOSTART_FILE")"
    if [[ "$script_source" != "$INSTALLED_SCRIPT" ]]; then
        cp "$script_source" "$INSTALLED_SCRIPT"
        chmod 0755 "$INSTALLED_SCRIPT"
    fi
    exec_path="${INSTALLED_SCRIPT//\\/\\\\}"
    exec_path="${exec_path//\"/\\\"}"
    escaped_variant="${VARIANT//\\/\\\\}"
    escaped_variant="${escaped_variant//\"/\\\"}"
    escaped_label="${START_LABEL//\\/\\\\}"
    escaped_label="${escaped_label//\"/\\\"}"
    cat >"$AUTOSTART_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Aplicar visual Windows XP
Comment=Configura o XFCE automaticamente no primeiro login
Exec="$exec_path" --apply-only --from-autostart --variant "$escaped_variant" --start-label "$escaped_label" --file-pane "$FILE_PANE" --taskbar-position "$TASKBAR_POSITION" --taskbar-size "$TASKBAR_SIZE"
OnlyShowIn=XFCE;
Terminal=false
Hidden=false
X-GNOME-Autostart-enabled=true
EOF
    chmod 0600 "$AUTOSTART_FILE"
}

main() {
    case "$ACTION" in
        list-backups)
            list_backups
            ;;
        restore)
            restore_backup
            ;;
        install)
            install_system_packages
            install_assets
            install_self_and_autostart
            if is_xfce_session; then
                make_backup
                configure_xfce
            else
                ok "Instalacao concluida."
                log "Saia da sessao, escolha 'Xfce Session' na tela de login e entre novamente."
                log "O tema sera aplicado automaticamente nesse primeiro login."
            fi
            ;;
        apply)
            [[ -d "$THEMES_DIR/$THEME_NAME" ]] || die "Tema nao instalado. Execute primeiro sem --apply-only."
            [[ -d "$ICONS_DIR/Windows XP" ]] || die "Icones nao instalados. Execute primeiro sem --apply-only."
            make_backup
            configure_xfce
            ;;
    esac
}

main
