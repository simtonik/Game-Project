import math
from pathlib import Path

import pygame as pg


def trim_sprite(sprite):
    width = sprite.get_width()
    height = sprite.get_height()
    y_values = []
    x_values = []
    for y in range(height):
        for x in range(width):
            if sprite.get_at((x, y)).a > 10:
                y_values.append(y)
                x_values.append(x)

    x1 = max(0, min(x_values) - 2)
    x2 = min(width - 1, max(x_values) + 2)
    y1 = max(0, min(y_values) - 2)
    y2 = min(height - 1, max(y_values) + 2)
    return sprite.subsurface((x1, y1, x2 - x1 + 1, y2 - y1 + 1)).copy()


def load_sprite_strip(path, frame_count):
    sprite_sheet = pg.image.load(path).convert_alpha()
    width = sprite_sheet.get_width()
    height = sprite_sheet.get_height()
    frame_width = width // frame_count
    sprites = []

    for frame in range(frame_count):
        frame_surface = sprite_sheet.subsurface((frame * frame_width, 0, frame_width, height))
        sprites.append(trim_sprite(frame_surface))

    return sprites


def angle_diff(a, b):
    return (a - b + math.pi) % (math.pi * 2) - math.pi


class Enemy:
    def __init__(self, x, y, angle=0):
        self.x = x
        self.y = y
        self.angle = angle
        self.radius = 12
        self.hp = 100
        self.speed = 45
        self.damage = 10
        self.vision_range = 350
        self.fov = math.pi / 2
        self.attack_range = 28
        self.alive = True
        self.is_moving = False
        self.animation_time = 0
        self.idle_sprites = load_sprite_strip(Path("assets/cheremshha/cheremsha_pokoy.png"), 8)
        self.back_walk_sprites = load_sprite_strip(Path("assets/cheremshha/cheremsha_wallk_bac.png"), 2)
        self.front_walk_sprites = load_sprite_strip(Path("assets/cheremshha/cheremsha_wallk_front.png"), 2)

    def distance_to(self, target_x, target_y):
        return math.hypot(target_x - self.x, target_y - self.y)

    def can_see_player(self, player_x, player_y, is_wall_at_pixel):
        distance = self.distance_to(player_x, player_y)
        if distance > self.vision_range:
            return False

        angle_to_player = math.atan2(player_y - self.y, player_x - self.x)
        if abs(angle_diff(angle_to_player, self.angle)) > self.fov / 2:
            return False

        step = 4
        depth = 0
        while depth < distance:
            depth += step
            check_x = self.x + math.cos(angle_to_player) * depth
            check_y = self.y + math.sin(angle_to_player) * depth
            if is_wall_at_pixel(check_x, check_y):
                return False

        return True

    def update(self, player_x, player_y, dt, collides_circle, is_wall_at_pixel):
        self.is_moving = False
        if not self.alive:
            return

        distance = self.distance_to(player_x, player_y)
        if distance <= self.attack_range:
            return

        if not self.can_see_player(player_x, player_y, is_wall_at_pixel):
            return

        self.angle = math.atan2(player_y - self.y, player_x - self.x)
        dir_x = (player_x - self.x) / distance
        dir_y = (player_y - self.y) / distance
        dx = dir_x * self.speed * dt
        dy = dir_y * self.speed * dt

        next_x = self.x + dx
        if not collides_circle(next_x, self.y, self.radius):
            self.x = next_x
            self.is_moving = True

        next_y = self.y + dy
        if not collides_circle(self.x, next_y, self.radius):
            self.y = next_y
            self.is_moving = True

        if self.is_moving:
            self.animation_time += dt

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def get_current_sprite(self, player_x, player_y):
        enemy_to_player_angle = math.atan2(player_y - self.y, player_x - self.x)
        sprite_angle = angle_diff(enemy_to_player_angle, self.angle)
        sprite_index = int(round(-sprite_angle / (math.pi * 2) * 8)) % 8
        sprite = self.idle_sprites[sprite_index]

        if self.is_moving and sprite_index == 4:
            walk_frame = int(self.animation_time * 3) % len(self.back_walk_sprites)
            sprite = self.back_walk_sprites[walk_frame]

        if self.is_moving and sprite_index == 0:
            walk_frame = int(self.animation_time * 3) % len(self.front_walk_sprites)
            sprite = self.front_walk_sprites[walk_frame]

        return sprite

    def draw_debug(self, screen, pygame):
        if self.alive:
            pygame.draw.circle(screen, (180, 30, 30), (int(self.x), int(self.y)), self.radius)
