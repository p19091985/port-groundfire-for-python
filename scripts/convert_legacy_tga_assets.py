#!/usr/bin/env python3
"""
Converte assets TGA legados para PNG em uma arvore paralela.

Este utilitario foi criado para a fase de planejamento/preparacao da
refatoracao. Ele nao altera o runtime principal do jogo e nao sobrescreve os
assets originais por padrao.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class ConversionRecord:
    source: str
    destination: str
    backend: str
    dry_run: bool
    success: bool
    width: int | None = None
    height: int | None = None
    source_bytes: int | None = None
    destination_bytes: int | None = None
    error: str | None = None


class BackendBase:
    name = "unknown"

    def convert(self, source: Path, destination: Path) -> tuple[int, int]:
        raise NotImplementedError

    def validate(self, destination: Path) -> tuple[int, int]:
        raise NotImplementedError

    def close(self) -> None:
        return None


class PygameBackend(BackendBase):
    name = "pygame"

    def __init__(self) -> None:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        import pygame

        pygame.init()
        self._pygame = pygame

    def convert(self, source: Path, destination: Path) -> tuple[int, int]:
        surface = self._pygame.image.load(str(source))
        width, height = surface.get_size()
        self._pygame.image.save(surface, str(destination))
        return width, height

    def validate(self, destination: Path) -> tuple[int, int]:
        surface = self._pygame.image.load(str(destination))
        return surface.get_size()

    def close(self) -> None:
        self._pygame.quit()


class PillowBackend(BackendBase):
    name = "pillow"

    def __init__(self) -> None:
        from PIL import Image

        self._Image = Image

    def convert(self, source: Path, destination: Path) -> tuple[int, int]:
        with self._Image.open(source) as image:
            width, height = image.size
            image.save(destination, format="PNG", optimize=True)
        return width, height

    def validate(self, destination: Path) -> tuple[int, int]:
        with self._Image.open(destination) as image:
            return image.size


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Converte arquivos TGA legados para PNG em uma arvore paralela."
    )
    parser.add_argument(
        "--input-root",
        default="data",
        help="Raiz onde procurar arquivos .tga. Padrao: data",
    )
    parser.add_argument(
        "--output-root",
        default="build/converted_assets_png",
        help="Raiz de saida para os arquivos convertidos.",
    )
    parser.add_argument(
        "--backend",
        default="auto",
        choices=["auto", "pygame", "pillow"],
        help="Backend de conversao. Padrao: auto",
    )
    parser.add_argument(
        "--manifest-name",
        default="conversion_manifest.json",
        help="Nome do manifesto JSON na raiz de saida.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nao escreve arquivos; apenas simula a operacao.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Permite sobrescrever PNGs ja existentes na pasta de saida.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Exibe detalhes de cada arquivo processado.",
    )
    return parser.parse_args()


def choose_backend(preference: str) -> BackendBase:
    errors: list[str] = []

    def try_backend(name: str) -> BackendBase | None:
        try:
            if name == "pygame":
                return PygameBackend()
            if name == "pillow":
                return PillowBackend()
        except Exception as exc:  # pragma: no cover
            errors.append(f"{name}: {exc}")
        return None

    if preference == "pygame":
        backend = try_backend("pygame")
        if backend:
            return backend
    elif preference == "pillow":
        backend = try_backend("pillow")
        if backend:
            return backend
    else:
        for name in ("pygame", "pillow"):
            backend = try_backend(name)
            if backend:
                return backend

    detail = "; ".join(errors) if errors else "nenhum backend disponivel"
    raise RuntimeError(f"Falha ao selecionar backend: {detail}")


def iter_sources(input_root: Path) -> list[Path]:
    return sorted(input_root.rglob("*.tga"))


def convert_one(
    source: Path,
    input_root: Path,
    output_root: Path,
    backend: BackendBase,
    *,
    dry_run: bool,
    overwrite: bool,
) -> ConversionRecord:
    relative = source.relative_to(input_root)
    destination = output_root / relative.with_suffix(".png")

    record = ConversionRecord(
        source=str(source),
        destination=str(destination),
        backend=backend.name,
        dry_run=dry_run,
        success=False,
        source_bytes=source.stat().st_size,
    )

    try:
        if destination.exists() and not overwrite and not dry_run:
            raise FileExistsError(f"arquivo ja existe: {destination}")

        if dry_run:
            record.success = True
            return record

        destination.parent.mkdir(parents=True, exist_ok=True)

        width, height = backend.convert(source, destination)
        check_width, check_height = backend.validate(destination)

        if (width, height) != (check_width, check_height):
            raise ValueError(
                f"validacao falhou: {width}x{height} -> {check_width}x{check_height}"
            )

        record.width = width
        record.height = height
        record.destination_bytes = destination.stat().st_size
        record.success = True
        return record
    except Exception as exc:
        record.error = str(exc)
        return record


def write_manifest(
    output_root: Path,
    manifest_name: str,
    records: list[ConversionRecord],
    backend_name: str,
    dry_run: bool,
) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    manifest_path = output_root / manifest_name
    payload = {
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "backend": backend_name,
        "dry_run": dry_run,
        "records": [asdict(record) for record in records],
    }
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return manifest_path


def main() -> int:
    args = parse_args()

    input_root = Path(args.input_root).resolve()
    output_root = Path(args.output_root).resolve()

    if not input_root.exists():
        print(f"Diretorio de entrada nao encontrado: {input_root}", file=sys.stderr)
        return 2

    backend = choose_backend(args.backend)

    try:
        sources = iter_sources(input_root)
        records: list[ConversionRecord] = []

        for source in sources:
            record = convert_one(
                source,
                input_root,
                output_root,
                backend,
                dry_run=args.dry_run,
                overwrite=args.overwrite,
            )
            records.append(record)
            if args.verbose:
                status = "OK" if record.success else "FAIL"
                print(f"[{status}] {record.source} -> {record.destination}")
                if record.error:
                    print(f"       erro: {record.error}")

        manifest_path = write_manifest(
            output_root,
            args.manifest_name,
            records,
            backend.name,
            args.dry_run,
        )

        ok_count = sum(1 for record in records if record.success)
        fail_count = len(records) - ok_count

        print(f"Backend selecionado  : {backend.name}")
        print(f"Arquivos encontrados : {len(records)}")
        print(f"Convertidos com sucesso: {ok_count}")
        print(f"Falhas               : {fail_count}")
        print(f"Modo dry-run         : {args.dry_run}")
        print(f"Manifesto            : {manifest_path}")

        return 0 if fail_count == 0 else 1
    finally:
        backend.close()


if __name__ == "__main__":
    raise SystemExit(main())
