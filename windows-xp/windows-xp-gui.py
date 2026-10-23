#!/usr/bin/env python3
"""Interface ttk para configurar e executar o windows-xpify.sh."""

from __future__ import annotations

import shlex
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except ImportError as exc:
    print(
        "Tkinter não está instalado. Instale python3-tk (Debian/Ubuntu), "
        "python3-tkinter (Fedora) ou tk (Arch Linux).",
        file=sys.stderr,
    )
    raise SystemExit(1) from exc


APP_DIR = Path(__file__).resolve().parent
SCRIPT_PATH = APP_DIR / "windows-xpify.sh"
README_PATH = APP_DIR / "README.md"

VARIANTS = (
    "Classic",
    "Luna",
    "Homestead",
    "Metallic",
    "Royale",
    "Royale-Dark",
    "Embedded",
    "Zune",
)
FILE_PANES = {
    "Árvore de pastas (Tree)": "tree",
    "Atalhos": "shortcuts",
}
TASKBAR_POSITIONS = {
    "Embaixo": "bottom",
    "Em cima": "top",
}


class XpifyApp(ttk.Frame):
    """Janela principal do configurador."""

    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master, padding=14)
        self.master = master
        self.variant = tk.StringVar(value="Classic")
        self.start_label = tk.StringVar(value="iniciar")
        self.file_pane = tk.StringVar(value="Árvore de pastas (Tree)")
        self.taskbar_position = tk.StringVar(value="Embaixo")
        self.taskbar_size = tk.IntVar(value=28)
        self.install_packages = tk.BooleanVar(value=True)
        self.command_preview = tk.StringVar()
        self.status = tk.StringVar(value="Escolha as opções e clique em Instalar / configurar.")

        self._build_ui()
        self._bind_preview_updates()
        self._update_preview()

    def _build_ui(self) -> None:
        self.grid(sticky="nsew")
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        ttk.Label(
            self,
            text="Windows XP Classic para Linux",
            font=("TkDefaultFont", 15, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        ttk.Label(
            self,
            text="Configure o XFCE com aparência e comportamento semelhantes ao Windows XP.",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 14))

        options = ttk.LabelFrame(self, text="Opções visuais", padding=12)
        options.grid(row=2, column=0, columnspan=2, sticky="nsew")
        options.columnconfigure(1, weight=1)

        self._add_combo(options, 0, "Tema:", self.variant, VARIANTS)
        self._add_entry(options, 1, "Texto do botão Iniciar:", self.start_label)
        self._add_combo(options, 2, "Painel do gerenciador:", self.file_pane, tuple(FILE_PANES))
        self._add_combo(
            options,
            3,
            "Posição da barra de tarefas:",
            self.taskbar_position,
            tuple(TASKBAR_POSITIONS),
        )

        ttk.Label(options, text="Altura da barra:").grid(
            row=4, column=0, sticky="w", padx=(0, 12), pady=6
        )
        ttk.Spinbox(
            options,
            from_=20,
            to=80,
            increment=1,
            textvariable=self.taskbar_size,
            width=8,
        ).grid(row=4, column=1, sticky="w", pady=6)
        ttk.Label(options, text="pixels (28 é o padrão clássico)").grid(
            row=4, column=1, sticky="w", padx=(75, 0), pady=6
        )

        ttk.Checkbutton(
            options,
            text="Instalar automaticamente o XFCE e as dependências",
            variable=self.install_packages,
        ).grid(row=5, column=0, columnspan=2, sticky="w", pady=(8, 2))

        preview_frame = ttk.LabelFrame(self, text="Comando que será executado", padding=10)
        preview_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        preview_frame.columnconfigure(0, weight=1)
        ttk.Entry(
            preview_frame,
            textvariable=self.command_preview,
            state="readonly",
        ).grid(row=0, column=0, sticky="ew")
        ttk.Button(preview_frame, text="Copiar", command=self._copy_command).grid(
            row=0, column=1, padx=(8, 0)
        )

        buttons = ttk.Frame(self)
        buttons.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        ttk.Button(
            buttons,
            text="Instalar / configurar",
            command=lambda: self._run_action("install"),
        ).pack(side="left")
        ttk.Button(
            buttons,
            text="Apenas aplicar",
            command=lambda: self._run_action("apply"),
        ).pack(side="left", padx=(8, 0))
        ttk.Button(
            buttons,
            text="Restaurar backup",
            command=lambda: self._run_action("restore"),
        ).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="Listar backups", command=self._list_backups).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(buttons, text="Documentação", command=self._open_docs).pack(
            side="right"
        )

        ttk.Separator(self).grid(row=5, column=0, columnspan=2, sticky="ew", pady=14)
        ttk.Label(self, textvariable=self.status, wraplength=690).grid(
            row=6, column=0, columnspan=2, sticky="w"
        )

    @staticmethod
    def _add_combo(
        parent: ttk.LabelFrame,
        row: int,
        label: str,
        variable: tk.StringVar,
        values: tuple[str, ...],
    ) -> None:
        ttk.Label(parent, text=label).grid(
            row=row, column=0, sticky="w", padx=(0, 12), pady=6
        )
        ttk.Combobox(
            parent,
            textvariable=variable,
            values=values,
            state="readonly",
        ).grid(row=row, column=1, sticky="ew", pady=6)

    @staticmethod
    def _add_entry(
        parent: ttk.LabelFrame,
        row: int,
        label: str,
        variable: tk.StringVar,
    ) -> None:
        ttk.Label(parent, text=label).grid(
            row=row, column=0, sticky="w", padx=(0, 12), pady=6
        )
        ttk.Entry(parent, textvariable=variable).grid(
            row=row, column=1, sticky="ew", pady=6
        )

    def _bind_preview_updates(self) -> None:
        for variable in (
            self.variant,
            self.start_label,
            self.file_pane,
            self.taskbar_position,
            self.taskbar_size,
            self.install_packages,
        ):
            variable.trace_add("write", self._update_preview)

    def _selected_arguments(self) -> list[str]:
        label = self.start_label.get().strip()
        if not label:
            raise ValueError("Digite o texto do botão Iniciar.")

        try:
            size = int(self.taskbar_size.get())
        except (tk.TclError, ValueError) as exc:
            raise ValueError("A altura da barra deve ser um número.") from exc
        if not 20 <= size <= 80:
            raise ValueError("A altura da barra deve estar entre 20 e 80 pixels.")

        return [
            "--variant",
            self.variant.get(),
            "--start-label",
            label,
            "--file-pane",
            FILE_PANES[self.file_pane.get()],
            "--taskbar-position",
            TASKBAR_POSITIONS[self.taskbar_position.get()],
            "--taskbar-size",
            str(size),
        ]

    def _build_command(self, action: str) -> list[str]:
        if not SCRIPT_PATH.is_file():
            raise FileNotFoundError(f"Script não encontrado: {SCRIPT_PATH}")

        command = [str(SCRIPT_PATH)]
        if action == "restore":
            return command + ["--restore"]
        if action == "list-backups":
            return command + ["--list-backups"]

        command.extend(self._selected_arguments())
        if action == "apply":
            command.append("--apply-only")
        elif not self.install_packages.get():
            command.append("--no-packages")
        return command

    def _update_preview(self, *_unused: object) -> None:
        try:
            self.command_preview.set(shlex.join(self._build_command("install")))
        except (ValueError, FileNotFoundError, tk.TclError):
            self.command_preview.set("Ajuste os parâmetros para gerar o comando.")

    def _copy_command(self) -> None:
        command = self.command_preview.get()
        self.master.clipboard_clear()
        self.master.clipboard_append(command)
        self.status.set("Comando copiado para a área de transferência.")

    def _run_action(self, action: str) -> None:
        try:
            command = self._build_command(action)
            terminal_command = self._terminal_command(command)
        except (ValueError, FileNotFoundError) as exc:
            messagebox.showerror("Não foi possível executar", str(exc), parent=self.master)
            return

        if terminal_command is None:
            self._copy_specific_command(command)
            messagebox.showwarning(
                "Terminal não encontrado",
                "Nenhum terminal compatível foi encontrado. O comando foi copiado; "
                "cole-o em um terminal para executar.",
                parent=self.master,
            )
            return

        try:
            subprocess.Popen(terminal_command, start_new_session=True)
        except OSError as exc:
            messagebox.showerror("Falha ao abrir o terminal", str(exc), parent=self.master)
            return
        self.status.set("Comando aberto em um terminal. Acompanhe a execução nessa janela.")

    @staticmethod
    def _terminal_command(command: list[str]) -> list[str] | None:
        command_text = shlex.join(command)
        wrapped = (
            f"{command_text}; status=$?; printf '\\n'; "
            "if [ $status -eq 0 ]; then echo 'Operação concluída.'; "
            "else echo \"A operação terminou com erro ($status).\"; fi; "
            "printf 'Pressione Enter para fechar...'; read -r _; exit $status"
        )
        shell_command = shlex.join(["bash", "-lc", wrapped])

        terminals: tuple[tuple[str, list[str]], ...] = (
            ("xfce4-terminal", ["--hold", "--command", shell_command]),
            ("gnome-terminal", ["--", "bash", "-lc", wrapped]),
            ("konsole", ["--hold", "-e", "bash", "-lc", wrapped]),
            ("mate-terminal", ["--", "bash", "-lc", wrapped]),
            ("kitty", ["--hold", "bash", "-lc", wrapped]),
            ("xterm", ["-hold", "-e", "bash", "-lc", wrapped]),
        )
        for executable, arguments in terminals:
            path = shutil.which(executable)
            if path:
                return [path, *arguments]
        return None

    def _copy_specific_command(self, command: list[str]) -> None:
        command_text = shlex.join(command)
        self.master.clipboard_clear()
        self.master.clipboard_append(command_text)
        self.command_preview.set(command_text)
        self.status.set("Comando copiado para a área de transferência.")

    def _list_backups(self) -> None:
        try:
            result = subprocess.run(
                self._build_command("list-backups"),
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            messagebox.showerror("Erro ao listar backups", str(exc), parent=self.master)
            return

        output = (result.stdout + result.stderr).strip()
        messagebox.showinfo(
            "Backups disponíveis",
            output or "Nenhum backup encontrado.",
            parent=self.master,
        )

    @staticmethod
    def _open_docs() -> None:
        if README_PATH.is_file():
            webbrowser.open(README_PATH.as_uri())


def main() -> int:
    if not SCRIPT_PATH.is_file():
        print(f"Script não encontrado: {SCRIPT_PATH}", file=sys.stderr)
        return 1

    root = tk.Tk()
    root.title("Configurar visual Windows XP")
    root.geometry("760x560")
    root.minsize(700, 520)
    XpifyApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
