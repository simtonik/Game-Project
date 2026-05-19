import math


def angle_diff(a, b):
    return (a - b + math.pi) % (math.pi * 2) - math.pi


class Enemy:
    def __init__(self, x, y, angle=0):
        self.x = x
        self.y = y
        self.angle = angle
        self.radius = 12
        self.hp = 100
        self.speed = 60
        self.damage = 10
        self.vision_range = 350
        self.fov = math.pi / 2
        self.attack_range = 28
        self.alive = True

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

        next_y = self.y + dy
        if not collides_circle(self.x, next_y, self.radius):
            self.y = next_y

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def draw_debug(self, screen, pygame):
        if self.alive:
            pygame.draw.circle(screen, (180, 30, 30), (int(self.x), int(self.y)), self.radius)
