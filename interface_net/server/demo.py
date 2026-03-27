from __future__ import annotations

import pygame

from .dedicated_server_ui import DedicatedServerUI


def run_dedicated_server_demo(window_size=(1100, 760)) -> int:
    pygame.init()
    if hasattr(pygame, "font") and hasattr(pygame.font, "init"):
        pygame.font.init()

    flags = getattr(pygame, "RESIZABLE", 0)
    window = pygame.display.set_mode(window_size, flags)
    pygame.display.set_caption("Groundfire Dedicated Server Preview")

    ui = DedicatedServerUI(*window_size)
    clock = pygame.time.Clock() if hasattr(pygame, "time") and hasattr(pygame.time, "Clock") else None
    running = True

    while running:
        dt = 1.0 / 60.0
        if clock is not None:
            dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if getattr(event, "type", None) == getattr(pygame, "QUIT", 256):
                running = False
                continue
            ui.handle_event(event)

        ui.update(dt)
        ui.draw(window)
        pygame.display.flip()

    ui.shutdown()
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(run_dedicated_server_demo())
