from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "docs" / "media"

HERO_SIZE = (1600, 900)
SHOWCASE_SIZE = (1600, 900)


def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    candidates = ["bahnschrift", "trebuchetms", "verdana", "consolas"]
    for name in candidates:
        font = pygame.font.SysFont(name, size, bold=bold)
        if font:
            return font
    return pygame.font.Font(None, size)


def load_image(name: str) -> pygame.Surface:
    candidate = DATA_DIR / name
    return pygame.image.load(str(candidate)).convert_alpha()


def make_tiled_background(size: tuple[int, int], tile: pygame.Surface) -> pygame.Surface:
    surface = pygame.Surface(size).convert_alpha()
    tile_w, tile_h = tile.get_size()
    for y in range(0, size[1], tile_h):
        for x in range(0, size[0], tile_w):
            surface.blit(tile, (x, y))
    return surface


def add_vertical_gradient(surface: pygame.Surface, top: tuple[int, int, int, int], bottom: tuple[int, int, int, int]) -> None:
    width, height = surface.get_size()
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    for y in range(height):
        ratio = y / max(height - 1, 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * ratio) for i in range(4))
        pygame.draw.line(overlay, color, (0, y), (width, y))
    surface.blit(overlay, (0, 0))


def draw_shadow_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    pos: tuple[int, int],
    *,
    center: bool = True,
) -> pygame.Rect:
    shadow = font.render(text, True, (5, 10, 18))
    img = font.render(text, True, color)
    rect = img.get_rect()
    shadow_rect = shadow.get_rect()
    if center:
        rect.center = pos
        shadow_rect.center = (pos[0] + 3, pos[1] + 3)
    else:
        rect.topleft = pos
        shadow_rect.topleft = (pos[0] + 3, pos[1] + 3)
    surface.blit(shadow, shadow_rect)
    surface.blit(img, rect)
    return rect


def wrap_lines(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_card(
    surface: pygame.Surface,
    rect: pygame.Rect,
    title: str,
    body: str,
    accent: tuple[int, int, int],
) -> None:
    card = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(card, (9, 20, 34, 185), card.get_rect(), border_radius=28)
    pygame.draw.rect(card, (*accent, 255), pygame.Rect(0, 0, rect.width, 10), border_radius=28)
    pygame.draw.rect(card, (255, 255, 255, 32), card.get_rect(), width=2, border_radius=28)

    title_font = get_font(38, bold=True)
    body_font = get_font(25)

    draw_shadow_text(card, title, title_font, (246, 248, 252), (28, 30), center=False)

    y = 96
    for line in wrap_lines(body, body_font, rect.width - 56):
        draw_shadow_text(card, line, body_font, (210, 224, 238), (28, y), center=False)
        y += 34

    surface.blit(card, rect.topleft)


def draw_badge(surface: pygame.Surface, text: str, pos: tuple[int, int], accent: tuple[int, int, int]) -> None:
    font = get_font(28, bold=True)
    text_img = font.render(text, True, (245, 247, 250))
    padding_x = 22
    padding_y = 10
    badge = pygame.Rect(pos[0], pos[1], text_img.get_width() + padding_x * 2, text_img.get_height() + padding_y * 2)
    chip = pygame.Surface(badge.size, pygame.SRCALPHA)
    pygame.draw.rect(chip, (*accent, 230), chip.get_rect(), border_radius=999)
    pygame.draw.rect(chip, (255, 255, 255, 30), chip.get_rect(), width=2, border_radius=999)
    chip.blit(text_img, (padding_x, padding_y))
    surface.blit(chip, badge.topleft)


def make_hero() -> None:
    background_tile = load_image("menuback.png")
    logo = load_image("logo.png")

    surface = make_tiled_background(HERO_SIZE, background_tile)
    add_vertical_gradient(surface, (4, 18, 35, 70), (3, 10, 18, 200))

    for center, radius, color in [
        ((250, 150), 220, (34, 112, 181, 44)),
        ((1330, 180), 200, (255, 105, 65, 34)),
        ((760, 720), 340, (16, 62, 96, 64)),
    ]:
        glow = pygame.Surface(HERO_SIZE, pygame.SRCALPHA)
        pygame.draw.circle(glow, color, center, radius)
        surface.blit(glow, (0, 0))

    draw_badge(surface, "GROUNDFIRE V0.25 / PYTHON PORT", (72, 52), (187, 59, 59))

    scaled_logo = pygame.transform.smoothscale(logo, (1100, 275))
    surface.blit(scaled_logo, scaled_logo.get_rect(center=(800, 255)))

    subtitle_font = get_font(36, bold=True)
    body_font = get_font(30)
    draw_shadow_text(
        surface,
        "Destructible terrain. Ballistic combat. AI tank warfare.",
        subtitle_font,
        (245, 248, 252),
        (800, 430),
    )
    draw_shadow_text(
        surface,
        "A modern Python/Pygame preservation port built side by side with the original C++ source.",
        body_font,
        (210, 224, 238),
        (800, 485),
    )

    cards = [
        (
            pygame.Rect(84, 600, 440, 220),
            "DESTRUCTIBLE WORLD",
            "Explosions carve the landscape, alter sight lines, and force new tactics every round.",
            (255, 119, 66),
        ),
        (
            pygame.Rect(580, 600, 440, 220),
            "ARTILLERY FEEL",
            "Angle, power, gravity, splash damage, and round-to-round economy all shape the match.",
            (43, 176, 221),
        ),
        (
            pygame.Rect(1076, 600, 440, 220),
            "PRESERVATION PORT",
            "Python gameplay code evolves with tests while the original Groundfire source remains in the repo.",
            (227, 77, 145),
        ),
    ]

    for rect, title, body, accent in cards:
        draw_card(surface, rect, title, body, accent)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surface, str(OUT_DIR / "readme-hero.png"))


def draw_tank(surface: pygame.Surface, x: int, y: int, color: tuple[int, int, int], facing_left: bool) -> None:
    body = [(x - 64, y + 28), (x - 28, y - 28), (x + 28, y - 28), (x + 64, y + 28)]
    pygame.draw.polygon(surface, color, body)
    turret_dir = -1 if facing_left else 1
    pygame.draw.line(surface, (236, 240, 245), (x, y - 10), (x + turret_dir * 115, y - 78), 10)


def make_showcase() -> None:
    background_tile = load_image("menuback.png")
    logo = load_image("logo.png")

    surface = make_tiled_background(SHOWCASE_SIZE, background_tile)
    add_vertical_gradient(surface, (10, 30, 52, 90), (4, 12, 22, 220))

    title_font = get_font(38, bold=True)
    label_font = get_font(26, bold=True)
    body_font = get_font(24)

    draw_badge(surface, "VISUAL SHOWCASE", (72, 52), (35, 160, 213))
    draw_shadow_text(surface, "Battlefield + shop moodboard built from in-repo assets", body_font, (219, 231, 242), (800, 124))

    left_panel = pygame.Rect(72, 170, 930, 650)
    right_panel = pygame.Rect(1042, 170, 486, 650)

    for rect, accent in [(left_panel, (231, 83, 149)), (right_panel, (255, 127, 63))]:
        card = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(card, (6, 14, 26, 185), card.get_rect(), border_radius=32)
        pygame.draw.rect(card, (*accent, 255), pygame.Rect(0, 0, rect.width, 8), border_radius=32)
        pygame.draw.rect(card, (255, 255, 255, 30), card.get_rect(), width=2, border_radius=32)
        surface.blit(card, rect.topleft)

    battle_area = pygame.Surface((left_panel.width - 40, left_panel.height - 80), pygame.SRCALPHA)
    battle_area.fill((0, 0, 0, 0))

    terrain_points = [(0, 470), (90, 420), (220, 450), (360, 360), (520, 400), (700, 310), (890, 430), (890, 570), (0, 570)]
    pygame.draw.polygon(battle_area, (43, 71, 57), terrain_points)
    pygame.draw.polygon(battle_area, (66, 104, 81), [(x, y - 16) for x, y in terrain_points[:-2]] + [(890, 554), (0, 554)])

    pygame.draw.circle(battle_area, (252, 210, 86), (675, 184), 58)
    pygame.draw.circle(battle_area, (255, 245, 208), (675, 184), 24)

    draw_tank(battle_area, 190, 428, (242, 32, 228), facing_left=False)
    draw_tank(battle_area, 704, 320, (255, 138, 31), facing_left=True)

    arc_points = [(250, 330), (340, 250), (430, 205), (520, 194), (605, 217)]
    pygame.draw.lines(battle_area, (220, 236, 246), False, arc_points, 5)
    pygame.draw.circle(battle_area, (255, 255, 255), arc_points[-1], 10)
    pygame.draw.circle(battle_area, (255, 145, 64), (632, 236), 48)
    pygame.draw.circle(battle_area, (255, 216, 104), (632, 236), 24)

    pygame.draw.rect(battle_area, (0, 0, 0, 85), pygame.Rect(0, 0, 890, 90), border_radius=26)
    draw_shadow_text(battle_area, "ROUND 2 OF 5", title_font, (243, 246, 250), (445, 44))

    surface.blit(battle_area, (left_panel.x + 20, left_panel.y + 60))

    draw_shadow_text(surface, "LIVE BATTLEFIELD", label_font, (245, 247, 250), (left_panel.x + 36, left_panel.y + 22), center=False)
    draw_shadow_text(surface, "SHOP + SYSTEMS", label_font, (245, 247, 250), (right_panel.x + 28, right_panel.y + 22), center=False)

    shop = pygame.Surface((right_panel.width - 36, right_panel.height - 52), pygame.SRCALPHA)
    pygame.draw.rect(shop, (11, 23, 38, 125), shop.get_rect(), border_radius=24)

    small_logo = pygame.transform.smoothscale(logo, (300, 75))
    shop.blit(small_logo, small_logo.get_rect(center=(shop.get_width() // 2, 78)))

    labels = [
        ("Machine Gun", "$50"),
        ("Jump Jet", "$50"),
        ("MIRVs", "$50"),
        ("Missiles", "$50"),
        ("Nukes", "$50"),
    ]

    y = 178
    for name, price in labels:
        row = pygame.Rect(28, y, shop.get_width() - 56, 52)
        pygame.draw.rect(shop, (255, 255, 255, 18), row, border_radius=18)
        draw_shadow_text(shop, name, body_font, (240, 244, 248), (row.x + 18, row.y + 10), center=False)
        draw_shadow_text(shop, price, body_font, (255, 169, 102), (row.right - 90, row.y + 10), center=False)
        y += 62

    info_rows = [
        ("AUTO-INSTALL", "BAT / PS1 / SH"),
        ("AI FLOW", "ROUND -> SHOP -> NEXT ROUND"),
    ]

    info_y = 494
    for title, value in info_rows:
        box = pygame.Rect(28, info_y, shop.get_width() - 56, 46)
        pygame.draw.rect(shop, (255, 255, 255, 14), box, border_radius=18)
        draw_shadow_text(shop, title, get_font(19, bold=True), (255, 165, 105), (box.x + 18, box.y + 8), center=False)
        draw_shadow_text(shop, value, get_font(20, bold=True), (244, 247, 251), (box.x + 18, box.y + 20), center=False)
        info_y += 56

    surface.blit(shop, (right_panel.x + 18, right_panel.y + 18))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surface, str(OUT_DIR / "readme-showcase.png"))


def main() -> None:
    pygame.init()
    pygame.font.init()
    pygame.display.init()
    pygame.display.set_mode((1, 1))
    make_hero()
    make_showcase()
    pygame.quit()


if __name__ == "__main__":
    main()
