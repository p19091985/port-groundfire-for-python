# Groundfire V0.25

Groundfire is a 2D artillery game where players command tanks to destroy opponents on a destructible terrain. It features various weapons, AI opponents, and a shop system.

This version has been ported to run on modern Linux systems.

## Features

*   **Destructible Terrain**: The landscape can be destroyed by explosions, creating craters and changing the battlefield.
*   **Multiple Weapons**: Includes standard Shells, Nukes, MIRVs (Multiple Independent Reentry Vehicles), Missiles, and Machine Guns.
*   **AI Opponents**: Computer-controlled tanks with basic intelligence.
*   **Shop System**: Purchase weapons and upgrades (like Jump Jets) between rounds.
*   **Physics-based Gameplay**: Projectile trajectories, gravity, and tank movement.
*   **Customizable**: Extensive configuration via INI files.

## Installation

### Linux (Debian/Ubuntu)

Use `apt-get` to install the required development libraries:

```bash
sudo apt-get update
sudo apt-get install build-essential libopenal-dev libalut-dev libglfw3-dev mesa-common-dev libglu1-mesa-dev
```

**Compilation:**

```bash
make
./groundfire
```

### Windows (via MSYS2)

The recommended way to compile on Windows is using [MSYS2](https://www.msys2.org/).

1.  Install MSYS2.
2.  Open the **MSYS2 MinGW 64-bit** terminal.
3.  Install dependencies using `pacman`:

```bash
pacman -S mingw-w64-x86_64-toolchain mingw-w64-x86_64-glfw mingw-w64-x86_64-openal mingw-w64-x86_64-freealut
```

**Compilation:**

```bash
make
./groundfire.exe
```

## Controls

Default controls for Player 1 (Keyboard 1):

*   **Fire**: `Space`
*   **Aim Turret**: `W` (Up) / `S` (Down)
*   **Rotate Turret**: `A` (Left) / `D` (Right)
*   **Move Tank**: `J` (Left) / `L` (Right)
*   **Jump Jets**: `I`
*   **Shield**: `K`
*   **Change Weapon**: `O` (Next) / `U` (Prev)

*Note: Controls can be customized in `conf/controls.ini` or via the in-game "Set Controls" menu.*

## Configuration

You can customize game settings in `conf/options.ini`:

*   **Graphics**: Resolution (`ScreenWidth`, `ScreenHeight`), Fullscreen mode.
*   **Gameplay**: Weapon damage, cooldowns, terrain properties.
*   **Colors**: Custom tank colors.

## License & Credits

*   **Original Author**: Tom Russell (`tom@groundfire.net`)
*   **License**: MIT License (See `COPYING` file)
*   **Original Website**: www.groundfire.net (Historical)

*Project ported to modern Linux/C++ standards.*
