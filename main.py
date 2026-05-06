import pygame as pg
import math
from map import WORLD_MAP, MAP_W, MAP_H

PLAYER_RADIUS = 12
WIDTH, HEIGHT = 800, 600
FPS = 60
MOUSE_SENS = 0.003

TILE_SIZE = min(WIDTH // MAP_W, HEIGHT // MAP_H)
offset_x = (WIDTH - MAP_W * TILE_SIZE) // 2
offset_y = (HEIGHT - MAP_H * TILE_SIZE) // 2


def is_wall_at_pixel(px: float, py: float) -> bool:
    mx = int((px - offset_x) // TILE_SIZE)
    my = int((py - offset_y) // TILE_SIZE)

    if mx < 0 or my < 0 or mx >= MAP_W or my >= MAP_H:
        return True
    
    return WORLD_MAP[my][mx] == "1"

def cast_ray(player_x, player_y, angle):
    depth = 0
    step = 2
    max_depth = 1000

    while depth < max_depth:
        depth += step
        ray_x = player_x + math.cos(angle) * depth
        ray_y = player_y + math.sin(angle) * depth

        if is_wall_at_pixel(ray_x, ray_y) == True:
            break
    return ray_x, ray_y, depth
        
def collides_circle(px: float, py: float, r: float) -> bool:
    points = [
        (px + r, py),
        (px - r, py),
        (px, py + r),
        (px, py - r),
        (px + 0.707 * r, py + 0.707 * r),
        (px - 0.707 * r, py + 0.707 * r),
        (px + 0.707 * r, py - 0.707 * r),
        (px - 0.707 * r, py - 0.707 * r)
    ]
    return any(is_wall_at_pixel(x,y) for x, y in points)


def main():
    pg.init()
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    pg.event.set_grab(True)
    pg.mouse.set_visible(False)
    pg.mouse.get_rel()
    pg.display.set_caption("Pygame basics")
    clock = pg.time.Clock()

    angle = 0.0
    rot_speed = 2.5

    player_x = offset_x + 1.5 * TILE_SIZE
    player_y = offset_y + 1.5 * TILE_SIZE
    speed = 250

    running = True
    mouse_captured = True

    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            #Тут я решил сделать обработку ESC
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    mouse_captured = not mouse_captured
                    pg.event.set_grab(mouse_captured)
                    pg.mouse.set_visible(not mouse_captured)
                    pg.mouse.get_rel()

        #обработка клавиш
        keys = pg.key.get_pressed()
        dir_x = math.cos(angle)
        dir_y = math.sin(angle)
        right_x = -dir_y
        right_y = dir_x
        forward = 0
        straf = 0


        if keys[pg.K_w] or keys[pg.K_UP]:
            dy += dir_y * speed * dt
            dx += dir_x * speed * dt
            forward += 1

        if keys[pg.K_s] or keys[pg.K_DOWN]:
            dy += -dir_y * speed * dt
            dx += -dir_x * speed * dt
            forward -= 1

        if keys[pg.K_a] or keys[pg.K_LEFT]:
            dx += math.cos(angle-(math.pi/2)) * speed * dt
            dy += math.sin(angle-(math.pi/2)) * speed * dt
            straf -= 1

        if keys[pg.K_d] or keys[pg.K_RIGHT]:
            dx += math.cos(angle+(math.pi/2)) * speed * dt
            dy += math.sin(angle+(math.pi/2)) * speed * dt
            straf += 1

        dx = (dir_x * forward + right_x * straf) * speed * dt
        dy = (dir_y * forward + right_y * straf) * speed * dt

        if forward != 0 and straf != 0:
            dx *= 0.707
            dy *= 0.707

        if keys[pg.K_q]:
            angle -= rot_speed * dt
        if keys[pg.K_e]:
            angle += rot_speed * dt


        if dx != 0 and dy != 0:
            inv = 0.70710678
            dx *= inv
            dy *= inv

        #поворот мышью

        mouse_x, mouse_y = pg.mouse.get_rel()
        angle += mouse_x * MOUSE_SENS

        nx = player_x + dx
        if not collides_circle(nx, player_y, PLAYER_RADIUS):
            player_x = nx

        ny = player_y + dy
        if not collides_circle(player_x, ny, PLAYER_RADIUS):
            player_y = ny     
        ###
        screen.fill((30, 30, 30))

        for row_idx, row in enumerate(WORLD_MAP):
            for col_idx, cell in enumerate(row):
                cell_x = offset_x + col_idx * TILE_SIZE
                cell_y = offset_y + row_idx * TILE_SIZE
                if cell == "1":
                    pg.draw.rect(screen, (100, 100, 100),
                                 (cell_x, cell_y, TILE_SIZE, TILE_SIZE))

        # рисую игрока
        pg.draw.circle(screen, (220, 220, 220), (int(player_x), int(player_y)), PLAYER_RADIUS)

        line_length = 40
        dx = line_length * pg.math.Vector2(1, 0).rotate_rad(angle).x
        dy = line_length * pg.math.Vector2(1, 0).rotate_rad(angle).y 

        #рисую лучи
        num_ray = 40
        FOV = math.pi / 3
        WALL_CONST = 20000

        start_angle = angle - FOV / 2

        for i in range(num_ray):
            ray_angle = start_angle + FOV * i / (num_ray - 1)
            ray_x, ray_y, depth = cast_ray(player_x, player_y, ray_angle)
            wall_height = int(WALL_CONST / depth)
            strip_width = int(WIDTH / num_ray)
            x_wall = i * strip_width
            y_wall = HEIGHT / 2 - wall_height / 2

            pg.draw.rect(
            screen,
            (255, 50, 50),
            (x_wall, y_wall, strip_width ,wall_height)
            )

            pg.draw.line(
                screen,
                (255, 50, 50),
                (int(player_x), int(player_y)),
                (int(ray_x), int(ray_y)),
                2
            )
        pg.display.flip()
        
    pg.quit()

if __name__ == "__main__":
    main()
