"""Wireframe D20 dice roller animation.

This script uses pygame to draw and animate a classic wireframe-style
icosahedron (D20 die). Press the space bar to trigger a fresh roll.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

import pygame


Vector3 = Tuple[float, float, float]
Vector2 = Tuple[int, int]


@dataclass(frozen=True)
class Face:
    vertices: Tuple[int, int, int]

    def edges(self) -> Iterable[Tuple[int, int]]:
        a, b, c = self.vertices
        return ((a, b), (b, c), (c, a))


# Golden ratio for an icosahedron definition
PHI = (1 + math.sqrt(5)) / 2

# Raw vertex positions for a unit icosahedron
VERTICES: Tuple[Vector3, ...] = (
    (-1, PHI, 0),
    (1, PHI, 0),
    (-1, -PHI, 0),
    (1, -PHI, 0),
    (0, -1, PHI),
    (0, 1, PHI),
    (0, -1, -PHI),
    (0, 1, -PHI),
    (PHI, 0, -1),
    (PHI, 0, 1),
    (-PHI, 0, -1),
    (-PHI, 0, 1),
)

# Triangular faces of the icosahedron. We map them to the 20 D20 results.
FACES: Tuple[Face, ...] = tuple(
    Face(face)
    for face in (
        (0, 11, 5),
        (0, 5, 1),
        (0, 1, 7),
        (0, 7, 10),
        (0, 10, 11),
        (1, 5, 9),
        (5, 11, 4),
        (11, 10, 2),
        (10, 7, 6),
        (7, 1, 8),
        (3, 9, 4),
        (3, 4, 2),
        (3, 2, 6),
        (3, 6, 8),
        (3, 8, 9),
        (4, 9, 5),
        (2, 4, 11),
        (6, 2, 10),
        (8, 6, 7),
        (9, 8, 1),
    )
)


# Pre-compute the unique edge list once.
def build_edge_list(faces: Sequence[Face]) -> List[Tuple[int, int]]:
    edge_set = set()
    for face in faces:
        for edge in face.edges():
            a, b = edge
            if a > b:
                a, b = b, a
            edge_set.add((a, b))
    return sorted(edge_set)


EDGES = build_edge_list(FACES)


@dataclass
class Rotation:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def update(self, dt: float, speed: float = 0.7) -> None:
        self.x += speed * dt * 0.6
        self.y += speed * dt
        self.z += speed * dt * 0.5


class D20Renderer:
    def __init__(self, size: Tuple[int, int]) -> None:
        self.width, self.height = size
        self.scale = min(self.width, self.height) / 5
        self.rotation = Rotation()

    def rotate_vertex(self, vertex: Vector3) -> Vector3:
        x, y, z = vertex
        rx, ry, rz = self.rotation.x, self.rotation.y, self.rotation.z

        # Rotation around X axis
        cosx, sinx = math.cos(rx), math.sin(rx)
        y, z = y * cosx - z * sinx, y * sinx + z * cosx

        # Rotation around Y axis
        cosy, siny = math.cos(ry), math.sin(ry)
        x, z = x * cosy + z * siny, -x * siny + z * cosy

        # Rotation around Z axis
        cosz, sinz = math.cos(rz), math.sin(rz)
        x, y = x * cosz - y * sinz, x * sinz + y * cosz

        return (x, y, z)

    def project(self, vertex: Vector3) -> Vector2:
        x, y, z = vertex
        # Simple perspective projection
        distance = 4.0
        factor = distance / (distance + z)
        px = int(self.width / 2 + x * self.scale * factor)
        py = int(self.height / 2 - y * self.scale * factor)
        return (px, py)

    def transformed_vertices(self) -> List[Vector2]:
        return [self.project(self.rotate_vertex(v)) for v in VERTICES]

    def update(self, dt: float) -> None:
        self.rotation.update(dt)


class DiceRoller:
    def __init__(self) -> None:
        self.current_face = 0
        self.result = 1
        self.rolling = False
        self.roll_duration = 2.0
        self.next_face_swap = 0.0
        self.roll_elapsed = 0.0

    def trigger_roll(self) -> None:
        self.result = random.randint(1, len(FACES))
        self.rolling = True
        self.roll_elapsed = 0.0
        self.next_face_swap = 0.0

    def update(self, dt: float) -> None:
        if not self.rolling:
            return
        self.roll_elapsed += dt
        if self.roll_elapsed >= self.roll_duration:
            self.rolling = False
            self.current_face = self.result - 1
            return
        if self.roll_elapsed >= self.next_face_swap:
            self.current_face = random.randrange(len(FACES))
            # Decrease interval as the roll progresses to simulate slowing
            remaining = max(self.roll_duration - self.roll_elapsed, 0.1)
            self.next_face_swap = self.roll_elapsed + random.uniform(0.05, 0.12) * (remaining / self.roll_duration * 2)


class App:
    BACKGROUND = (5, 10, 20)
    LINE_COLOR = (0, 255, 120)
    HIGHLIGHT = (255, 220, 40)

    def __init__(self, size: Tuple[int, int] = (800, 600)) -> None:
        pygame.init()
        pygame.display.set_caption("Wireframe D20 Roller")
        self.screen = pygame.display.set_mode(size)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Consolas", 28, bold=True)
        self.small_font = pygame.font.SysFont("Consolas", 18)
        self.renderer = D20Renderer(size)
        self.roller = DiceRoller()
        self.roller.trigger_roll()

    def draw_edges(self, vertices: Sequence[Vector2]) -> None:
        for a, b in EDGES:
            pygame.draw.line(self.screen, self.LINE_COLOR, vertices[a], vertices[b], 1)

    def draw_highlight(self, vertices: Sequence[Vector2], face_index: int) -> None:
        face = FACES[face_index]
        for a, b in face.edges():
            pygame.draw.line(self.screen, self.HIGHLIGHT, vertices[a], vertices[b], 3)

    def draw_labels(self, result: int, rolling: bool) -> None:
        if rolling:
            text = self.font.render("Rolling...", True, self.HIGHLIGHT)
        else:
            text = self.font.render(f"Result: {result}", True, self.HIGHLIGHT)
        info = self.small_font.render("Press SPACE to roll again", True, (120, 200, 255))
        self.screen.blit(text, (20, 20))
        self.screen.blit(info, (20, 60))

    def run(self) -> None:
        running = True
        while running:
            dt = self.clock.tick(60) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.roller.trigger_roll()

            self.renderer.update(dt)
            self.roller.update(dt)
            verts = self.renderer.transformed_vertices()

            self.screen.fill(self.BACKGROUND)
            self.draw_edges(verts)
            self.draw_highlight(verts, self.roller.current_face)
            self.draw_labels(self.roller.result, self.roller.rolling)
            pygame.display.flip()

        pygame.quit()


def main() -> None:
    App().run()


if __name__ == "__main__":
    main()
