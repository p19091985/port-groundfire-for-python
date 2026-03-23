from __future__ import annotations

from typing import List, Tuple
import math
import random

import pygame

from .common import sqr
from .inifile import ReadIniFile
from .interface import Colour, Interface


MIN_LAND_HEIGHT = -7.0


class LandChunk:
    def __init__(self):
        self.max_height_1 = 0.0
        self.max_height_2 = 0.0
        self.min_height_1 = 0.0
        self.min_height_2 = 0.0

        self.max_colour_1 = Colour()
        self.max_colour_2 = Colour()
        self.min_colour_1 = Colour()
        self.min_colour_2 = Colour()

        self.linked_to_next = False
        self.falling_state = False
        self.wait_for_fall_time = 0.0
        self.falling_speed = 0.0

    def clone(self) -> "LandChunk":
        chunk = LandChunk()
        chunk.max_height_1 = self.max_height_1
        chunk.max_height_2 = self.max_height_2
        chunk.min_height_1 = self.min_height_1
        chunk.min_height_2 = self.min_height_2
        chunk.max_colour_1 = Colour(self.max_colour_1.r, self.max_colour_1.g, self.max_colour_1.b)
        chunk.max_colour_2 = Colour(self.max_colour_2.r, self.max_colour_2.g, self.max_colour_2.b)
        chunk.min_colour_1 = Colour(self.min_colour_1.r, self.min_colour_1.g, self.min_colour_1.b)
        chunk.min_colour_2 = Colour(self.min_colour_2.r, self.min_colour_2.g, self.min_colour_2.b)
        chunk.linked_to_next = self.linked_to_next
        chunk.falling_state = self.falling_state
        chunk.wait_for_fall_time = self.wait_for_fall_time
        chunk.falling_speed = self.falling_speed
        return chunk


class Landscape:
    def __init__(self, settings: ReadIniFile, seed: float):
        random.seed(int(seed * 1000.0))

        self._fall_pause = settings.get_float("Terrain", "FallPause", 0.1)
        self._fall_acceleration = settings.get_float("Terrain", "FallAcceleration", 5.0)
        self._num_of_slices = settings.get_int("Terrain", "Slices", 10)
        self._landscape_width = settings.get_float("Terrain", "Width", 11.0)
        self._slice_to_world_conversion = (self._num_of_slices / 2.0) / self._landscape_width
        self._land_chunks: List[List[LandChunk]] = [[] for _ in range(self._num_of_slices)]

        self.generate_terrain()

    def generate_terrain(self):
        heights = [-7.0] * (self._num_of_slices + 1)
        smoothed = [0.0] * (self._num_of_slices + 1)
        self._land_chunks = [[] for _ in range(self._num_of_slices)]

        for _ in range(18):
            centre = random.randrange((self._num_of_slices + 1) * 2) - ((self._num_of_slices + 1) // 2)
            height = random.randrange(1000) / 300.0
            width = random.randrange((self._num_of_slices + 1) // 2) + 3
            plateau = random.randrange(max(1, width // 3))

            for j in range(self._num_of_slices + 1):
                distance = abs(centre - j)
                if distance < plateau:
                    heights[j] += height
                elif distance < width:
                    heights[j] += ((width - (distance - plateau)) / float(width)) * height

                if heights[j] > 5.0:
                    heights[j] = 5.0

        for i in range(self._num_of_slices + 1):
            if 10 <= i < self._num_of_slices - 10:
                smoothed[i] = sum(heights[j] for j in range(i - 10, i + 11)) / 21.0
            else:
                smoothed[i] = heights[i]

        for i in range(self._num_of_slices):
            colour_chunk = LandChunk()
            colour_chunk.max_height_1 = smoothed[i]
            colour_chunk.max_height_2 = smoothed[i + 1]
            colour_chunk.max_colour_1 = Colour(0.4, 0.4, 0.0)
            colour_chunk.max_colour_2 = Colour(0.4, 0.4, 0.0)
            colour_chunk.min_height_1 = smoothed[i] - 1.0
            colour_chunk.min_height_2 = smoothed[i + 1] - 1.0
            colour_chunk.min_colour_1 = Colour(0.8, 0.8, 0.0)
            colour_chunk.min_colour_2 = Colour(0.8, 0.8, 0.0)
            colour_chunk.falling_state = False
            colour_chunk.wait_for_fall_time = 0.0
            colour_chunk.linked_to_next = False

            if colour_chunk.min_height_1 > -7.5 or colour_chunk.min_height_2 > -7.5:
                colour_chunk.linked_to_next = True

                base_chunk = LandChunk()
                base_chunk.max_height_1 = smoothed[i] - 1.0
                base_chunk.max_height_2 = smoothed[i + 1] - 1.0
                base_chunk.max_colour_1 = Colour(0.8, 0.8, 0.0)
                base_chunk.max_colour_2 = Colour(0.8, 0.8, 0.0)
                base_chunk.min_height_1 = -8.0
                base_chunk.min_height_2 = -8.0
                base_chunk.min_colour_1 = Colour(0.8, 0.8, 0.0)
                base_chunk.min_colour_2 = Colour(0.8, 0.8, 0.0)
                base_chunk.falling_state = False
                base_chunk.wait_for_fall_time = 0.0
                base_chunk.linked_to_next = False

                self._land_chunks[i].append(colour_chunk)
                self._land_chunks[i].append(base_chunk)
            else:
                self._land_chunks[i].append(colour_chunk)

    def update(self, time: float):
        for slice_idx in range(self._num_of_slices):
            chunks = self._land_chunks[slice_idx]
            idx = 0
            while idx < len(chunks):
                start_super_idx = idx
                end_super_idx = idx

                while end_super_idx < len(chunks) - 1 and chunks[end_super_idx].linked_to_next:
                    end_super_idx += 1

                if chunks[idx].falling_state:
                    if chunks[idx].wait_for_fall_time > 0.0:
                        chunks[idx].wait_for_fall_time -= time
                    else:
                        left_at_rest = False
                        right_at_rest = False
                        fall_amount = chunks[idx].falling_speed * time
                        left_fall_amount = fall_amount
                        right_fall_amount = fall_amount

                        chunks[idx].falling_speed += self._fall_acceleration * time

                        next_idx = end_super_idx + 1
                        if next_idx < len(chunks):
                            new_min_height_1 = chunks[end_super_idx].min_height_1 - fall_amount
                            new_min_height_2 = chunks[end_super_idx].min_height_2 - fall_amount

                            if chunks[next_idx].max_height_1 > new_min_height_1:
                                left_fall_amount = chunks[end_super_idx].min_height_1 - chunks[next_idx].max_height_1
                                left_at_rest = True

                            if chunks[next_idx].max_height_2 > new_min_height_2:
                                right_fall_amount = chunks[end_super_idx].min_height_2 - chunks[next_idx].max_height_2
                                right_at_rest = True

                        for move_idx in range(start_super_idx, min(end_super_idx + 1, len(chunks))):
                            chunks[move_idx].min_height_1 -= left_fall_amount
                            chunks[move_idx].min_height_2 -= right_fall_amount
                            chunks[move_idx].max_height_1 -= left_fall_amount
                            chunks[move_idx].max_height_2 -= right_fall_amount

                        if left_at_rest and right_at_rest and next_idx < len(chunks):
                            if (
                                chunks[end_super_idx].max_colour_1 == chunks[end_super_idx].min_colour_1
                                and chunks[end_super_idx].max_colour_2 == chunks[end_super_idx].min_colour_2
                            ):
                                chunks[next_idx].max_height_1 = chunks[end_super_idx].max_height_1
                                chunks[next_idx].max_height_2 = chunks[end_super_idx].max_height_2

                                if end_super_idx != start_super_idx:
                                    chunks[start_super_idx].falling_state = chunks[next_idx].falling_state
                                    chunks[start_super_idx].falling_speed = chunks[next_idx].falling_speed
                                    chunks[start_super_idx].wait_for_fall_time = chunks[next_idx].wait_for_fall_time

                                del chunks[end_super_idx]

                                idx = min(end_super_idx, len(chunks) - 1)
                                while idx < len(chunks) and chunks[idx].linked_to_next:
                                    idx += 1
                                idx += 1
                                continue

                            chunks[end_super_idx].linked_to_next = True
                            chunks[start_super_idx].falling_state = chunks[next_idx].falling_state
                            chunks[start_super_idx].falling_speed = chunks[next_idx].falling_speed
                            chunks[start_super_idx].wait_for_fall_time = chunks[next_idx].wait_for_fall_time

                            idx = start_super_idx
                            while idx < len(chunks) and chunks[idx].linked_to_next:
                                idx += 1
                            idx += 1
                            continue

                idx = end_super_idx + 1

    def draw(self):
        interface = Interface.current_interface
        if not interface:
            return

        width, height, _ = interface.get_window_settings()
        for band in range(24):
            ratio_top = band / 24.0
            ratio_bottom = (band + 1) / 24.0
            top_colour = (
                int((0.0 + (0.6 * ratio_top)) * 255),
                0,
                int(0.4 * 255),
            )
            bottom_y = int(height * ratio_bottom)
            top_y = int(height * ratio_top)
            pygame.draw.rect(interface._window, top_colour, (0, top_y, width, max(1, bottom_y - top_y)))

        for slice_idx in range(self._num_of_slices):
            x1 = self.get_world_x_from_slice(slice_idx)
            x2 = self.get_world_x_from_slice(slice_idx + 1)
            for chunk in self._land_chunks[slice_idx]:
                points = [
                    interface.game_to_screen(x1, chunk.min_height_1),
                    interface.game_to_screen(x1, chunk.max_height_1),
                    interface.game_to_screen(x2, chunk.max_height_2),
                    interface.game_to_screen(x2, chunk.min_height_2),
                ]

                avg_r = (chunk.min_colour_1.r + chunk.max_colour_1.r + chunk.max_colour_2.r + chunk.min_colour_2.r) / 4.0
                avg_g = (chunk.min_colour_1.g + chunk.max_colour_1.g + chunk.max_colour_2.g + chunk.min_colour_2.g) / 4.0
                avg_b = (chunk.min_colour_1.b + chunk.max_colour_1.b + chunk.max_colour_2.b + chunk.min_colour_2.b) / 4.0
                pygame.draw.polygon(interface._window, (int(avg_r * 255), int(avg_g * 255), int(avg_b * 255)), points)

    def make_hole(self, x, y, radius):
        min_slice = self.get_slice_from_world_x(x - radius)
        max_slice = self.get_slice_from_world_x(x + radius) + 1

        if min_slice < 0:
            min_slice = 0
        if max_slice >= self._num_of_slices:
            max_slice = self._num_of_slices - 1

        for slice_idx in range(min_slice, max_slice + 1):
            self.clip_slice(slice_idx, x, y, radius)

    def clip_slice(self, slice_idx: int, x: float, y: float, radius: float):
        chunks = self._land_chunks[slice_idx]
        idx = 0

        while idx < len(chunks):
            chunk = chunks[idx]
            x1 = self.get_world_x_from_slice(slice_idx)
            x2 = self.get_world_x_from_slice(slice_idx + 1)

            state1 = self.check_within_blast_range(x, y, radius, x1, chunk.max_height_1)
            state2 = self.check_within_blast_range(x, y, radius, x2, chunk.max_height_2)

            if chunk.min_height_1 > MIN_LAND_HEIGHT:
                state3 = self.check_within_blast_range(x, y, radius, x1, chunk.min_height_1)
                state4 = self.check_within_blast_range(x, y, radius, x2, chunk.min_height_2)
            else:
                state3 = 1
                state4 = 1

            was_linked_to_next = chunk.linked_to_next
            if was_linked_to_next:
                if ((state1 == 0 and state2 != 3 and state4 == 3) or (state2 == 0 and state1 != 3 and state3 == 3)):
                    while idx < len(chunks) and chunks[idx].linked_to_next:
                        idx += 1
                    idx += 1
                    continue

            need_split = 0
            superblock_idx = self.get_superblock(slice_idx, idx)

            top_code = (state2 << 2) | state1
            if top_code in (3, 6, 7):
                new_height = self.clip_height(x, y, radius, x1, False)
                self.calculate_colour(chunk.max_colour_1, chunk.min_colour_1, chunk.max_height_1, chunk.min_height_1, new_height, True)
                chunk.max_height_1 = new_height
            elif top_code in (9, 12, 13):
                new_height = self.clip_height(x, y, radius, x2, False)
                self.calculate_colour(chunk.max_colour_2, chunk.min_colour_2, chunk.max_height_2, chunk.min_height_2, new_height, True)
                chunk.max_height_2 = new_height
            elif top_code == 10:
                need_split += 1
            elif top_code in (11, 14, 15):
                new_height = self.clip_height(x, y, radius, x1, False)
                self.calculate_colour(chunk.max_colour_1, chunk.min_colour_1, chunk.max_height_1, chunk.min_height_1, new_height, True)
                chunk.max_height_1 = new_height

                new_height = self.clip_height(x, y, radius, x2, False)
                self.calculate_colour(chunk.max_colour_2, chunk.min_colour_2, chunk.max_height_2, chunk.min_height_2, new_height, True)
                chunk.max_height_2 = new_height

            bottom_code = (state4 << 2) | state3
            if bottom_code == 5:
                need_split += 1
            elif bottom_code in (6, 12, 14):
                new_height = self.clip_height(x, y, radius, x2, True)
                self.calculate_colour(chunk.max_colour_2, chunk.min_colour_2, chunk.max_height_2, chunk.min_height_2, new_height, False)
                chunk.min_height_2 = new_height

                if chunk.linked_to_next and idx + 1 < len(chunks):
                    if state3 == 2:
                        chunk.min_height_1 = self.clip_height(x, y, radius, x1, True)

                    chunks[idx + 1].falling_state = chunks[superblock_idx].falling_state
                    chunks[idx + 1].wait_for_fall_time = chunks[superblock_idx].wait_for_fall_time
                    chunks[idx + 1].falling_speed = chunks[superblock_idx].falling_speed

                chunk.linked_to_next = False
                if not chunks[superblock_idx].falling_state:
                    chunks[superblock_idx].falling_state = True
                    chunks[superblock_idx].wait_for_fall_time = self._fall_pause
                    chunks[superblock_idx].falling_speed = 0.0

            elif bottom_code in (7, 13, 15):
                new_height = self.clip_height(x, y, radius, x1, True)
                self.calculate_colour(chunk.max_colour_1, chunk.min_colour_1, chunk.max_height_1, chunk.min_height_1, new_height, False)
                chunk.min_height_1 = new_height

                new_height = self.clip_height(x, y, radius, x2, True)
                self.calculate_colour(chunk.max_colour_2, chunk.min_colour_2, chunk.max_height_2, chunk.min_height_2, new_height, False)
                chunk.min_height_2 = new_height

                if chunk.linked_to_next and idx + 1 < len(chunks):
                    chunks[idx + 1].falling_state = chunks[superblock_idx].falling_state
                    chunks[idx + 1].wait_for_fall_time = chunks[superblock_idx].wait_for_fall_time
                    chunks[idx + 1].falling_speed = chunks[superblock_idx].falling_speed

                chunk.linked_to_next = False
                if not chunks[superblock_idx].falling_state:
                    chunks[superblock_idx].falling_state = True
                    chunks[superblock_idx].wait_for_fall_time = self._fall_pause
                    chunks[superblock_idx].falling_speed = 0.0

            elif bottom_code in (3, 9, 11):
                new_height = self.clip_height(x, y, radius, x1, True)
                self.calculate_colour(chunk.max_colour_1, chunk.min_colour_1, chunk.max_height_1, chunk.min_height_1, new_height, False)
                chunk.min_height_1 = new_height

                if chunk.linked_to_next and idx + 1 < len(chunks):
                    if state4 == 2:
                        chunk.min_height_2 = self.clip_height(x, y, radius, x2, True)

                    chunks[idx + 1].falling_state = chunks[superblock_idx].falling_state
                    chunks[idx + 1].wait_for_fall_time = chunks[superblock_idx].wait_for_fall_time
                    chunks[idx + 1].falling_speed = chunks[superblock_idx].falling_speed

                chunk.linked_to_next = False
                if not chunks[superblock_idx].falling_state:
                    chunks[superblock_idx].falling_state = True
                    chunks[superblock_idx].wait_for_fall_time = self._fall_pause
                    chunks[superblock_idx].falling_speed = 0.0

            if need_split == 2:
                new_chunk = chunk.clone()
                new_chunk.max_height_1 = chunk.max_height_1
                new_chunk.max_height_2 = chunk.max_height_2

                new_height = self.clip_height(x, y, radius, x1, True)
                new_chunk.max_colour_1 = Colour(chunk.max_colour_1.r, chunk.max_colour_1.g, chunk.max_colour_1.b)
                new_chunk.min_colour_1 = Colour(chunk.min_colour_1.r, chunk.min_colour_1.g, chunk.min_colour_1.b)
                self.calculate_colour(new_chunk.max_colour_1, new_chunk.min_colour_1, chunk.max_height_1, chunk.min_height_1, new_height, False)
                new_chunk.min_height_1 = new_height

                new_height = self.clip_height(x, y, radius, x2, True)
                new_chunk.max_colour_2 = Colour(chunk.max_colour_2.r, chunk.max_colour_2.g, chunk.max_colour_2.b)
                new_chunk.min_colour_2 = Colour(chunk.min_colour_2.r, chunk.min_colour_2.g, chunk.min_colour_2.b)
                self.calculate_colour(new_chunk.max_colour_2, new_chunk.min_colour_2, chunk.max_height_2, chunk.min_height_2, new_height, False)
                new_chunk.min_height_2 = new_height

                new_height = self.clip_height(x, y, radius, x1, False)
                self.calculate_colour(chunk.max_colour_1, chunk.min_colour_1, chunk.max_height_1, chunk.min_height_1, new_height, True)
                chunk.max_height_1 = new_height

                new_height = self.clip_height(x, y, radius, x2, False)
                self.calculate_colour(chunk.max_colour_2, chunk.min_colour_2, chunk.max_height_2, chunk.min_height_2, new_height, True)
                chunk.max_height_2 = new_height

                new_chunk.linked_to_next = False
                new_chunk.falling_state = False
                new_chunk.wait_for_fall_time = 0.0
                new_chunk.falling_speed = 0.0

                old_idx = idx
                chunks.insert(old_idx, new_chunk)
                idx = old_idx + 1
                chunk = chunks[idx]

                if superblock_idx == old_idx:
                    superblock_idx = idx - 1

                if not chunks[superblock_idx].falling_state:
                    chunks[superblock_idx].falling_state = True
                    chunks[superblock_idx].wait_for_fall_time = self._fall_pause
                    chunks[superblock_idx].falling_speed = 0.0
                else:
                    chunk.falling_state = chunks[superblock_idx].falling_state
                    chunk.wait_for_fall_time = chunks[superblock_idx].wait_for_fall_time
                    chunk.falling_speed = chunks[superblock_idx].falling_speed

            if chunk.min_height_1 > chunk.max_height_1 or chunk.min_height_2 > chunk.max_height_2:
                if was_linked_to_next and idx + 1 < len(chunks):
                    chunks[idx + 1].max_height_1 = chunk.max_height_1
                    chunks[idx + 1].max_height_2 = chunk.max_height_2

                del chunks[idx]
            else:
                idx += 1

    def check_within_blast_range(self, blast_x: float, blast_y: float, radius: float, x: float, y: float) -> int:
        if x > (blast_x + radius) or x < (blast_x - radius):
            return 0

        if sqr(x - blast_x) + sqr(y - blast_y) < sqr(radius):
            return 3

        if blast_y > y:
            return 1
        return 2

    def clip_height(self, blast_x: float, blast_y: float, blast_radius: float, x: float, up: bool) -> float:
        root = math.sqrt(max(0.0, sqr(blast_radius) - sqr(x - blast_x)))
        if up:
            return blast_y + root

        new_y = blast_y - root
        if new_y < MIN_LAND_HEIGHT:
            return MIN_LAND_HEIGHT
        return new_y

    def move_to_ground(self, x: float, y: float) -> float:
        slice_idx = self.get_slice_from_world_x(x)
        if not (0 <= slice_idx < self._num_of_slices):
            return MIN_LAND_HEIGHT

        x_offset = self.get_slice_offset_from_world_x(x)
        height = 0.0
        old_height = -1000.0

        for chunk in self._land_chunks[slice_idx]:
            state = self.in_chunk(chunk, x_offset, y)
            if state != 2:
                height = (chunk.max_height_1 * (1.0 - x_offset)) + (chunk.max_height_2 * x_offset)
                if state == 0:
                    break

                if (y - height) < (y - old_height):
                    old_height = height
                else:
                    height = old_height

        return height

    def move_to_ground_at_angle(self, x_ref: float, y_ref: float, angle: float) -> Tuple[float, float]:
        slice_idx = self.get_slice_from_world_x(x_ref)
        x_offset = self.get_slice_offset_from_world_x(x_ref)
        x = x_ref
        y = y_ref
        done = False

        while not done and 0 <= slice_idx < self._num_of_slices:
            found = False
            for chunk in self._land_chunks[slice_idx]:
                state = self.in_chunk(chunk, x_offset, y)
                if state == 0:
                    found = True
                    if angle == 0.0:
                        y = (chunk.max_height_1 * (1.0 - x_offset)) + (chunk.max_height_2 * x_offset)
                        done = True
                    elif angle > 0.0:
                        new_y = y + x_offset / math.tan(angle)
                        if new_y > chunk.max_height_1:
                            collision_x, collision_y = self.find_top_chunk_intersect(chunk, 0.0, new_y, x_offset, y)
                            x = self.get_world_x_from_slice_x(collision_x + slice_idx)
                            y = collision_y
                            done = True
                        else:
                            x = self.get_world_x_from_slice(slice_idx)
                            y = new_y
                            x_offset = 1.0
                            slice_idx -= 1
                    else:
                        new_y = y + (1.0 - x_offset) / math.tan(-angle)
                        if new_y > chunk.max_height_2:
                            collision_x, collision_y = self.find_top_chunk_intersect(chunk, 1.0, new_y, x_offset, y)
                            x = self.get_world_x_from_slice_x(collision_x + slice_idx)
                            y = collision_y
                            done = True
                        else:
                            x = self.get_world_x_from_slice(slice_idx + 1)
                            y = new_y
                            x_offset = 0.0
                            slice_idx += 1
                    break

            if not found:
                done = True

        return x, y

    def in_chunk(self, chunk: LandChunk, x_offset: float, y: float) -> int:
        max_height = (chunk.max_height_1 * (1.0 - x_offset)) + (chunk.max_height_2 * x_offset)
        min_height = (chunk.min_height_1 * (1.0 - x_offset)) + (chunk.min_height_2 * x_offset)

        if y > max_height:
            return 1
        if y < min_height:
            return 2
        return 0

    def find_top_chunk_intersect(
        self, chunk: LandChunk, x_offset_1: float, y1: float, x_offset_2: float, y2: float
    ) -> Tuple[float, float]:
        dx = x_offset_2 - x_offset_1
        projectile_gradient = (y2 - y1) / dx if abs(dx) > 1.0e-9 else 1.0e10
        slice_gradient = chunk.max_height_2 - chunk.max_height_1

        if projectile_gradient > 1.0 or projectile_gradient < -1.0:
            collision_x = (((chunk.max_height_1 - y1) / projectile_gradient) + x_offset_1) / (
                1.0 - (slice_gradient / projectile_gradient)
            )
        else:
            collision_x = (chunk.max_height_1 - y1 + projectile_gradient * x_offset_1) / (
                projectile_gradient - slice_gradient
            )

        collision_y = (collision_x * slice_gradient) + chunk.max_height_1
        return collision_x, collision_y

    def find_bottom_chunk_intersect(
        self, chunk: LandChunk, x_offset_1: float, y1: float, x_offset_2: float, y2: float
    ) -> Tuple[float, float]:
        dx = x_offset_2 - x_offset_1
        projectile_gradient = (y2 - y1) / dx if abs(dx) > 1.0e-9 else 1.0e10
        slice_gradient = chunk.min_height_2 - chunk.min_height_1

        if projectile_gradient > 1.0 or projectile_gradient < -1.0:
            collision_x = (((chunk.min_height_1 - y1) / projectile_gradient) + x_offset_1) / (
                1.0 - (slice_gradient / projectile_gradient)
            )
        else:
            collision_x = (chunk.min_height_1 - y1 + projectile_gradient * x_offset_1) / (
                projectile_gradient - slice_gradient
            )

        collision_y = (collision_x * slice_gradient) + chunk.min_height_1
        return collision_x, collision_y

    def intersect_chunk(
        self, x_offset_1: float, y1: float, x_offset_2: float, y2: float, slice_idx: int
    ) -> Tuple[bool, float, float]:
        if not (0 <= slice_idx < self._num_of_slices):
            return False, 0.0, 0.0

        for chunk in self._land_chunks[slice_idx]:
            state1 = self.in_chunk(chunk, x_offset_1, y1)
            state2 = self.in_chunk(chunk, x_offset_2, y2)

            if state1 == 0:
                collision_x = self.get_world_x_from_slice_x(x_offset_1 + slice_idx)
                return True, collision_x, y1

            if state1 != state2:
                if state1 == 1:
                    collision_x, collision_y = self.find_top_chunk_intersect(chunk, x_offset_1, y1, x_offset_2, y2)
                else:
                    collision_x, collision_y = self.find_bottom_chunk_intersect(chunk, x_offset_1, y1, x_offset_2, y2)
                collision_x = self.get_world_x_from_slice_x(collision_x + slice_idx)
                return True, collision_x, collision_y

        return False, 0.0, 0.0

    def ground_collision(self, x1: float, y1: float, x2: float, y2: float) -> Tuple[bool, float, float]:
        index1 = self.get_slice_from_world_x(x1)
        index2 = self.get_slice_from_world_x(x2)

        if index1 < index2:
            length_x = x2 - x1
            length_y = y2 - y1
            if length_x == 0.0:
                return False, 0.0, 0.0

            x = self.get_world_x_from_slice(index1 + 1)
            y = y1 + (((x - x1) / length_x) * length_y)

            hit, collision_x, collision_y = self.intersect_chunk(
                self.get_slice_offset_from_world_x(x1), y1, 1.0, y, index1
            )
            if hit:
                return True, collision_x, collision_y

            for slice_idx in range(index1 + 1, index2):
                x += 1.0 / self._slice_to_world_conversion
                old_y = y
                y = y1 + (((x - x1) / length_x) * length_y)

                hit, collision_x, collision_y = self.intersect_chunk(0.0, old_y, 1.0, y, slice_idx)
                if hit:
                    return True, collision_x, collision_y

            return self.intersect_chunk(0.0, y, self.get_slice_offset_from_world_x(x2), y2, index2)

        if index2 < index1:
            length_x = x1 - x2
            length_y = y1 - y2
            if length_x == 0.0:
                return False, 0.0, 0.0

            x = self.get_world_x_from_slice(index1)
            y = y2 + (((x - x2) / length_x) * length_y)

            hit, collision_x, collision_y = self.intersect_chunk(
                self.get_slice_offset_from_world_x(x1), y1, 0.0, y, index1
            )
            if hit:
                return True, collision_x, collision_y

            for slice_idx in range(index1 - 1, index2, -1):
                x -= 1.0 / self._slice_to_world_conversion
                old_y = y
                y = y2 + (((x - x2) / length_x) * length_y)

                hit, collision_x, collision_y = self.intersect_chunk(1.0, old_y, 0.0, y, slice_idx)
                if hit:
                    return True, collision_x, collision_y

            return self.intersect_chunk(1.0, y, self.get_slice_offset_from_world_x(x2), y2, index2)

        return self.intersect_chunk(
            self.get_slice_offset_from_world_x(x1), y1, self.get_slice_offset_from_world_x(x2), y2, index1
        )

    def calculate_colour(self, top: Colour, bottom: Colour, max_x: float, min_x: float, x: float, calc_top: bool):
        denom = max_x - min_x
        ratio = 0.0 if abs(denom) < 1.0e-9 else (x - min_x) / denom

        if calc_top:
            top.r = bottom.r + (ratio * (top.r - bottom.r))
            top.g = bottom.g + (ratio * (top.g - bottom.g))
            top.b = bottom.b + (ratio * (top.b - bottom.b))
        else:
            bottom.r = bottom.r + (ratio * (top.r - bottom.r))
            bottom.g = bottom.g + (ratio * (top.g - bottom.g))
            bottom.b = bottom.b + (ratio * (top.b - bottom.b))

    def drop_terrain(self, amount: float):
        for chunks in self._land_chunks:
            for chunk in chunks:
                chunk.max_height_1 -= amount
                chunk.max_height_2 -= amount

                if chunk.max_height_1 < MIN_LAND_HEIGHT:
                    chunk.max_height_1 = MIN_LAND_HEIGHT
                if chunk.max_height_2 < MIN_LAND_HEIGHT:
                    chunk.max_height_2 = MIN_LAND_HEIGHT

                if chunk.max_height_1 > MIN_LAND_HEIGHT:
                    chunk.min_height_1 -= amount
                if chunk.max_height_1 > MIN_LAND_HEIGHT:
                    chunk.min_height_2 -= amount

    def get_superblock(self, slice_idx: int, block_idx: int) -> int:
        if block_idx == 0:
            return block_idx

        block_idx -= 1
        chunks = self._land_chunks[slice_idx]

        while block_idx != 0 and chunks[block_idx].linked_to_next:
            block_idx -= 1

        if block_idx == 0 and chunks[block_idx].linked_to_next:
            return block_idx

        return block_idx + 1

    def get_slice_x_from_world_x(self, x: float) -> float:
        return (x * self._slice_to_world_conversion) + (self._num_of_slices / 2.0)

    def get_world_x_from_slice_x(self, x: float) -> float:
        return (x - (self._num_of_slices / 2.0)) / self._slice_to_world_conversion

    def get_slice_from_world_x(self, x: float) -> int:
        return int((x * self._slice_to_world_conversion) + (self._num_of_slices / 2.0))

    def get_world_x_from_slice(self, slice_idx: float) -> float:
        return (slice_idx - (self._num_of_slices / 2.0)) / self._slice_to_world_conversion

    def get_slice_offset_from_world_x(self, x: float) -> float:
        slice_x = self.get_slice_x_from_world_x(x)
        return slice_x - math.floor(slice_x)

    def get_landscape_width(self) -> float:
        return self._landscape_width

    def get_landscape_height(self, x: float) -> float:
        return self.move_to_ground(x, 100.0)

    def explosion(self, x: float, y: float, size: float):
        self.make_hole(x, y, size)
