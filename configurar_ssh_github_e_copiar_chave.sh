#!/usr/bin/env bash

set -Eeuo pipefail

github_email="plp.19.09.1985@gmail.com"
ssh_directory="${HOME}/.ssh"
private_key_path="${ssh_directory}/id_ed25519"
public_key_path="${private_key_path}.pub"

mkdir -p "${ssh_directory}"
chmod 700 "${ssh_directory}"

if [[ -f "${private_key_path}" && -f "${public_key_path}" ]]; then
    printf 'Uma chave SSH existente foi encontrada e sera reutilizada:\n%s\n\n' "${public_key_path}"
elif [[ -f "${private_key_path}" ]]; then
    printf 'A chave publica nao foi encontrada. Gerando-a novamente a partir da chave privada...\n'
    ssh-keygen -y -f "${private_key_path}" > "${public_key_path}"
elif [[ -f "${public_key_path}" ]]; then
    printf 'ERRO: existe uma chave publica, mas a chave privada correspondente nao foi encontrada:\n%s\n' "${public_key_path}" >&2
    printf 'O arquivo existente nao foi alterado.\n' >&2
    exit 1
else
    printf 'Criando uma nova chave SSH para %s.\n' "${github_email}"
    printf 'Quando solicitado, informe uma senha para proteger a chave ou pressione Enter para nao usar senha.\n\n'
    ssh-keygen -t ed25519 -C "${github_email}" -f "${private_key_path}"
fi

chmod 600 "${private_key_path}"
chmod 644 "${public_key_path}"

copy_public_key() {
    if command -v wl-copy >/dev/null 2>&1; then
        wl-copy < "${public_key_path}"
        return 0
    fi

    if command -v xclip >/dev/null 2>&1; then
        xclip -selection clipboard < "${public_key_path}"
        return 0
    fi

    if command -v xsel >/dev/null 2>&1; then
        xsel --clipboard --input < "${public_key_path}"
        return 0
    fi

    if command -v python3 >/dev/null 2>&1 && [[ -n "${DISPLAY:-}" ]]; then
        python3 - "${public_key_path}" <<'PY' >/dev/null 2>&1 &
import pathlib
import sys
import tkinter as tk

public_key = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8").strip()
window = tk.Tk()
window.withdraw()
window.clipboard_clear()
window.clipboard_append(public_key)
window.update()

# No X11, o processo precisa manter a selecao por algum tempo.
window.after(600_000, window.destroy)
window.mainloop()
PY
        clipboard_process_id=$!
        sleep 0.5

        if kill -0 "${clipboard_process_id}" 2>/dev/null; then
            printf 'O clipboard sera mantido por ate 10 minutos para voce colar a chave no GitHub.\n'
            return 0
        fi
    fi

    return 1
}

if copy_public_key; then
    printf '\nChave publica copiada para o clipboard com sucesso.\n'
    printf 'Agora abra: https://github.com/settings/ssh/new\n'
    printf 'Escolha "Authentication Key" e cole a chave no campo "Key".\n'
else
    printf '\nNao foi possivel acessar o clipboard automaticamente.\n' >&2
    printf 'Instale um utilitario de clipboard, por exemplo: sudo apt install xclip\n' >&2
    printf 'Depois execute este script novamente. Sua chave foi preservada em:\n%s\n' "${public_key_path}" >&2
    exit 1
fi
