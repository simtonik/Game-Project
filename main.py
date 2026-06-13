import pygame as pg
import math
from map import WORLD_MAP, MAP_W, MAP_H
from enemy import Enemy
from menu import draw_menu, menu_events


PLAYER_RADIUS = 8
WIDTH, HEIGHT = 800, 600
FPS = 60
MOUSE_SENS = 0.003
#game_status = "menu"


TILE_SIZE = min(WIDTH // MAP_W, HEIGHT // MAP_H)
offset_x = (WIDTH - MAP_W * TILE_SIZE) // 2
offset_y = (HEIGHT - MAP_H * TILE_SIZE) // 2

heavy_door_open = False
server_door_open = False


def is_blocking_cell(cell: str) -> bool:
    if cell == "H":
        return not heavy_door_open

    return cell in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "S", "W", "E", "P", "D")


def is_wall_at_pixel(px: float, py: float) -> bool:
    mx = int((px - offset_x) // TILE_SIZE)
    my = int((py - offset_y) // TILE_SIZE)

    if mx < 0 or my < 0 or mx >= MAP_W or my >= MAP_H:
        return True
    
    return is_blocking_cell(WORLD_MAP[my][mx])


def get_map_cell_at_pixel(px: float, py: float) -> str:
    mx = int((px - offset_x) // TILE_SIZE)
    my = int((py - offset_y) // TILE_SIZE)

    if mx < 0 or my < 0 or mx >= MAP_W or my >= MAP_H:
        return "1"

    return WORLD_MAP[my][mx]


def cell_center(col, row):
    return offset_x + (col + 0.5) * TILE_SIZE, offset_y + (row + 0.5) * TILE_SIZE


def can_stand_on_cell(col, row):
    if col < 0 or row < 0 or col >= MAP_W or row >= MAP_H:
        return False

    return not is_blocking_cell(WORLD_MAP[row][col])


def get_near_door(player_x, player_y, door_symbol):
    max_distance = TILE_SIZE * 1.2
    nearest_door = None
    nearest_distance = max_distance

    for row_idx, row in enumerate(WORLD_MAP):
        for col_idx, cell in enumerate(row):
            if cell != door_symbol:
                continue

            door_x, door_y = cell_center(col_idx, row_idx)
            distance = math.hypot(player_x - door_x, player_y - door_y)
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_door = (col_idx, row_idx)

    return nearest_door


def get_near_security_door(player_x, player_y):
    return get_near_door(player_x, player_y, "D")


def get_near_laboratory_door(player_x, player_y):
    return get_near_door(player_x, player_y, "8")


def get_near_server_door(player_x, player_y):
    return get_near_door(player_x, player_y, "P")


def teleport_through_door(player_x, player_y, door_symbol):
    door = get_near_door(player_x, player_y, door_symbol)
    if door is None:
        return player_x, player_y

    door_col, door_row = door
    door_sides = [
        ((door_col - 1, door_row), (door_col + 1, door_row)),
        ((door_col, door_row - 1), (door_col, door_row + 1))
    ]

    for first_cell, second_cell in door_sides:
        if not can_stand_on_cell(*first_cell) or not can_stand_on_cell(*second_cell):
            continue

        first_x, first_y = cell_center(*first_cell)
        second_x, second_y = cell_center(*second_cell)
        first_distance = math.hypot(player_x - first_x, player_y - first_y)
        second_distance = math.hypot(player_x - second_x, player_y - second_y)

        if first_distance < second_distance:
            return second_x, second_y
        return first_x, first_y

    return player_x, player_y


def teleport_through_security_door(player_x, player_y):
    return teleport_through_door(player_x, player_y, "D")


def teleport_through_laboratory_door(player_x, player_y):
    return teleport_through_door(player_x, player_y, "8")


def teleport_through_server_door(player_x, player_y):
    return teleport_through_door(player_x, player_y, "P")

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
    return ray_x, ray_y, depth, get_map_cell_at_pixel(ray_x, ray_y)


def get_texture_x(ray_x, ray_y, texture_width):
    hit_x = (ray_x - offset_x) % TILE_SIZE
    hit_y = (ray_y - offset_y) % TILE_SIZE

    if hit_x < 2 or hit_x > TILE_SIZE - 2:
        texture_pos = hit_y / TILE_SIZE
    else:
        texture_pos = hit_x / TILE_SIZE

    return int(texture_pos * (texture_width - 1))


def make_door_texture(left_panel, right_panel):
    width = left_panel.get_width() + right_panel.get_width()
    height = max(left_panel.get_height(), right_panel.get_height())
    door_texture = pg.Surface((width, height), pg.SRCALPHA)
    door_texture.blit(left_panel, (0, height - left_panel.get_height()))
    door_texture.blit(right_panel, (left_panel.get_width(), height - right_panel.get_height()))
    return door_texture


def apply_flashlight(brightness, target_angle, angle, flashlight_on, flashlight_cone, flashlight_power):
    if not flashlight_on:
        return brightness

    ray_offset = abs(normalize_angle(target_angle - angle))
    flashlight_strength = max(0, 1 - ray_offset / flashlight_cone)
    brightness += int((255 - brightness) * flashlight_strength * flashlight_power)
    return min(255, brightness)


def draw_floor_casting(screen, texture, player_x, player_y, angle, fov, wall_const, current_fog, min_brightness, flashlight_on, flashlight_cone, flashlight_power):
    render_scale = 3
    floor_width = WIDTH // render_scale
    floor_height = (HEIGHT // 2) // render_scale
    floor_surface = pg.Surface((floor_width, floor_height))
    texture_width = texture.get_width()
    texture_height = texture.get_height()
    left_angle = angle - fov / 2
    right_angle = angle + fov / 2
    left_dir_x = math.cos(left_angle)
    left_dir_y = math.sin(left_angle)
    right_dir_x = math.cos(right_angle)
    right_dir_y = math.sin(right_angle)

    for y in range(floor_height):
        screen_y = HEIGHT // 2 + (y + 1) * render_scale
        row_depth = (wall_const / 2) / (screen_y - HEIGHT / 2)
        floor_x = player_x + left_dir_x * row_depth
        floor_y = player_y + left_dir_y * row_depth
        step_x = (right_dir_x - left_dir_x) * row_depth / floor_width
        step_y = (right_dir_y - left_dir_y) * row_depth / floor_width

        for x in range(floor_width):
            point_angle = math.atan2(floor_y - player_y, floor_x - player_x)
            brightness = int(255 / (1 + row_depth * current_fog))
            brightness = max(min_brightness, min(255, brightness))
            brightness = apply_flashlight(brightness, point_angle, angle, flashlight_on, flashlight_cone, flashlight_power)
            texture_x = int(((floor_x - offset_x) % TILE_SIZE) / TILE_SIZE * texture_width)
            texture_y = int(((floor_y - offset_y) % TILE_SIZE) / TILE_SIZE * texture_height)
            color = texture.get_at((texture_x, texture_y))
            floor_surface.set_at(
                (x, y),
                (
                    color.r * brightness // 255,
                    color.g * brightness // 255,
                    color.b * brightness // 255
                )
            )
            floor_x += step_x
            floor_y += step_y

    floor_surface = pg.transform.scale(floor_surface, (WIDTH, HEIGHT // 2))
    screen.blit(floor_surface, (0, HEIGHT // 2))


def draw_ceiling_casting(screen, texture, player_x, player_y, angle, fov, wall_const, current_fog, min_brightness, flashlight_on, flashlight_cone, flashlight_power):
    render_scale = 3
    ceiling_width = WIDTH // render_scale
    ceiling_height = (HEIGHT // 2) // render_scale
    ceiling_surface = pg.Surface((ceiling_width, ceiling_height))
    texture_width = texture.get_width()
    texture_height = texture.get_height()
    left_angle = angle - fov / 2
    right_angle = angle + fov / 2
    left_dir_x = math.cos(left_angle)
    left_dir_y = math.sin(left_angle)
    right_dir_x = math.cos(right_angle)
    right_dir_y = math.sin(right_angle)

    for y in range(ceiling_height):
        screen_y = y * render_scale
        row_depth = (wall_const / 2) / (HEIGHT / 2 - screen_y)
        ceiling_x = player_x + left_dir_x * row_depth
        ceiling_y = player_y + left_dir_y * row_depth
        step_x = (right_dir_x - left_dir_x) * row_depth / ceiling_width
        step_y = (right_dir_y - left_dir_y) * row_depth / ceiling_width

        for x in range(ceiling_width):
            point_angle = math.atan2(ceiling_y - player_y, ceiling_x - player_x)
            brightness = int(255 / (1 + row_depth * current_fog))
            brightness = max(min_brightness, min(255, brightness))
            brightness = apply_flashlight(brightness, point_angle, angle, flashlight_on, flashlight_cone, flashlight_power)
            texture_x = int(((ceiling_x - offset_x) % TILE_SIZE) / TILE_SIZE * texture_width)
            texture_y = int(((ceiling_y - offset_y) % TILE_SIZE) / TILE_SIZE * texture_height)
            color = texture.get_at((texture_x, texture_y))
            ceiling_surface.set_at(
                (x, y),
                (
                    color.r * brightness // 255,
                    color.g * brightness // 255,
                    color.b * brightness // 255
                )
            )
            ceiling_x += step_x
            ceiling_y += step_y

    ceiling_surface = pg.transform.scale(ceiling_surface, (WIDTH, HEIGHT // 2))
    screen.blit(ceiling_surface, (0, 0))


def normalize_angle(angle):
    return (angle + math.pi) % (math.pi * 2) - math.pi


def draw_enemy_sprite(screen, enemy, player_x, player_y, angle, fov, wall_const, z_buffer, strip_width, current_fog, min_brightness, flashlight_on, flashlight_cone, flashlight_power):
    if not enemy.alive:
        return

    dx = enemy.x - player_x
    dy = enemy.y - player_y
    distance = math.hypot(dx, dy)
    angle_to_enemy = math.atan2(dy, dx)
    angle_offset = normalize_angle(angle_to_enemy - angle)

    if abs(angle_offset) > fov / 2:
        return

    corrected_distance = distance * math.cos(angle_offset)
    if corrected_distance <= 1:
        return

    sprite = enemy.get_current_sprite(player_x, player_y)

    sprite_height = max(1, int(wall_const / corrected_distance * 1.2))
    sprite_width = max(1, int(sprite.get_width() * sprite_height / sprite.get_height()))
    screen_x = int((angle_offset + fov / 2) / fov * WIDTH)
    x_left = screen_x - sprite_width // 2
    y_top = HEIGHT // 2 - sprite_height // 2
    scaled_sprite = pg.transform.scale(sprite, (sprite_width, sprite_height))

    brightness = int(255 / (1 + corrected_distance * current_fog))
    brightness = max(min_brightness, min(255, brightness))
    brightness = apply_flashlight(brightness, angle_to_enemy, angle, flashlight_on, flashlight_cone, flashlight_power)
    scaled_sprite.fill((brightness, brightness, brightness), special_flags=pg.BLEND_MULT)

    for x in range(sprite_width):
        screen_column = x_left + x
        if screen_column < 0 or screen_column >= WIDTH:
            continue

        buffer_index = screen_column // strip_width
        if buffer_index >= len(z_buffer) or corrected_distance >= z_buffer[buffer_index]:
            continue

        column = scaled_sprite.subsurface((x, 0, 1, sprite_height))
        screen.blit(column, (screen_column, y_top))


def create_panels(panel_texture):
    panels = []
    for row_idx, row in enumerate(WORLD_MAP):
        for col_idx, cell in enumerate(row):
            if cell == "T":
                panels.append({
                    "x": offset_x + (col_idx + 0.5) * TILE_SIZE,
                    "y": offset_y + (row_idx + 0.5) * TILE_SIZE,
                    "sprite": panel_texture,
                    "height_scale": 0.5
                })

    return panels


def get_near_panel(player_x, player_y, panels):
    max_distance = TILE_SIZE * 1.2
    nearest_panel = None
    nearest_distance = max_distance

    for panel in panels:
        distance = math.hypot(player_x - panel["x"], player_y - panel["y"])
        if distance < nearest_distance:
            nearest_distance = distance
            nearest_panel = panel

    return nearest_panel


def draw_object_sprite(screen, obj, player_x, player_y, angle, fov, wall_const, z_buffer, strip_width, current_fog, min_brightness, flashlight_on, flashlight_cone, flashlight_power):
    dx = obj["x"] - player_x
    dy = obj["y"] - player_y
    distance = math.hypot(dx, dy)
    angle_to_object = math.atan2(dy, dx)
    angle_offset = normalize_angle(angle_to_object - angle)

    if abs(angle_offset) > fov / 2:
        return

    corrected_distance = distance * math.cos(angle_offset)
    if corrected_distance <= 1:
        return

    sprite = obj["sprite"]
    full_wall_height = wall_const / corrected_distance
    sprite_height = max(1, int(full_wall_height * obj["height_scale"]))
    sprite_width = max(1, int(sprite.get_width() * sprite_height / sprite.get_height()))
    screen_x = int((angle_offset + fov / 2) / fov * WIDTH)
    x_left = screen_x - sprite_width // 2
    floor_y = HEIGHT // 2 + full_wall_height // 2
    y_top = floor_y - sprite_height
    scaled_sprite = pg.transform.scale(sprite, (sprite_width, sprite_height))

    brightness = int(255 / (1 + corrected_distance * current_fog))
    brightness = max(min_brightness, min(255, brightness))
    brightness = apply_flashlight(brightness, angle_to_object, angle, flashlight_on, flashlight_cone, flashlight_power)
    scaled_sprite.fill((brightness, brightness, brightness), special_flags=pg.BLEND_MULT)

    for x in range(sprite_width):
        screen_column = x_left + x
        if screen_column < 0 or screen_column >= WIDTH:
            continue

        buffer_index = screen_column // strip_width
        if buffer_index >= len(z_buffer) or corrected_distance >= z_buffer[buffer_index]:
            continue

        column = scaled_sprite.subsurface((x, 0, 1, sprite_height))
        screen.blit(column, (screen_column, y_top))


def draw_code_lock(screen, font, small_font, entered_code, has_error):
    panel_rect = pg.Rect(0, 0, 280, 130)
    panel_rect.center = (WIDTH // 2, HEIGHT // 2)
    pg.draw.rect(screen, (18, 18, 18), panel_rect)
    pg.draw.rect(screen, (170, 170, 170), panel_rect, 2)

    code_text = font.render(" ".join(entered_code.ljust(4, "_")), True, (230, 230, 230))

    screen.blit(code_text, code_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 10)))

    if has_error:
        error_text = small_font.render("неверный код", True, (220, 70, 70))
        screen.blit(error_text, error_text.get_rect(center=(WIDTH // 2, panel_rect.bottom - 25)))
         
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
    global heavy_door_open, server_door_open

    pg.init()
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    pg.event.set_grab(False)
    pg.mouse.set_visible(True)
    pg.mouse.set_pos(WIDTH // 2, HEIGHT // 2)
    pg.mouse.get_rel()
    pg.display.set_caption("Pygame basics")
    clock = pg.time.Clock()
    wall_texture = pg.image.load("assets/textures/Wall_2.png").convert()
    sec_wall_texture = pg.image.load("assets/textures/sec_wall_2.png").convert()
    sec_window_texture = pg.image.load("assets/textures/sec_wall.png").convert()
    panel_texture = pg.image.load("assets/objects/sec_panel.png").convert_alpha()
    sec_door_texture = pg.image.load("assets/textures/Door_sec.png").convert()
    lab_wall_texture = pg.image.load("assets/laboratory/lab_wall.png").convert()
    lab_table_texture = pg.image.load("assets/laboratory/Table_wall.png").convert()
    lab_wardrobe_texture = pg.image.load("assets/laboratory/wardrobe_wall.png").convert()
    lab_wardrobe_2_texture = pg.image.load("assets/laboratory/lab_wardrobe_2.png").convert()
    lab_hanger_texture = pg.image.load("assets/laboratory/hanger_wall.png").convert()
    lab_door_texture = pg.image.load("assets/textures/Door_2.png").convert()
    server_wall_texture = pg.image.load("assets/servers/serv_wall.png").convert()
    server_wall_1_texture = pg.image.load("assets/servers/serv_wall_1.png").convert()
    server_shield_texture = pg.image.load("assets/servers/serv_shild.png").convert()
    server_door_texture = pg.image.load("assets/servers/serv_door.png").convert()
    door_left_texture = pg.image.load("assets/textures/Door_L.png").convert_alpha()
    door_right_texture = pg.image.load("assets/textures/Door_R.png").convert_alpha()
    heavy_door_texture = make_door_texture(door_left_texture, door_right_texture)
    wall_textures = {
        "1": wall_texture,
        "2": sec_wall_texture,
        "3": sec_window_texture,
        "4": lab_wall_texture,
        "5": lab_table_texture,
        "6": lab_wardrobe_texture,
        "7": lab_hanger_texture,
        "8": lab_door_texture,
        "9": lab_wardrobe_2_texture,
        "S": server_wall_texture,
        "W": server_wall_1_texture,
        "E": server_shield_texture,
        "P": server_door_texture,
        "D": sec_door_texture,
        "H": heavy_door_texture
    }
    floor_texture = pg.image.load("assets/textures/Floor_1.png").convert()
    ceiling_texture = pg.image.load("assets/textures/ceiling_1.png").convert()
    panels = create_panels(panel_texture)

    angle = 0.0
    rot_speed = 2.5

    player_x = offset_x + 1.5 * TILE_SIZE
    player_y = offset_y + 4.5 * TILE_SIZE
    speed = 250
    enemy = Enemy(offset_x + 18.5 * TILE_SIZE, offset_y + 3.5 * TILE_SIZE, math.pi)


    game_status = "menu"
    running = True
    mouse_captured = False
    #переменные для обзора
    night_vision_max_charge = 20.0
    night_vision_charge = night_vision_max_charge
    night_vision_drain = 1.0
    flashlight_on = False
    flashlight_max_charge = 20.0
    flashlight_charge = flashlight_max_charge
    flashlight_drain = 1.0
    server_pin_code = "0472"
    server_pin_entered = ""
    server_pin_active = False
    server_pin_error_timer = 0.0

    font = pg.font.SysFont(None, 48)
    interact_font = pg.font.SysFont("arial", 28)

    start_buton = pg.Rect(WIDTH // 2 - 100, 250, 200, 60)
    exit_buton = pg.Rect(WIDTH // 2 - 100, 330, 200, 60)

    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pg.event.get():

            if game_status == "menu":
                action = menu_events(event, start_buton, exit_buton)

                if action == "start":
                    game_status = "game"
                    mouse_captured = True
                    pg.event.set_grab(True)
                    pg.mouse.set_visible(False)
                    pg.mouse.get_rel()

                if action == "exit":
                    running = False

            if event.type == pg.QUIT:
                running = False
            #Тут я решил сделать обработку ESC
            if event.type == pg.KEYDOWN:
                if server_pin_active:
                    if event.key == pg.K_ESCAPE or event.key == pg.K_e:
                        server_pin_active = False
                        server_pin_entered = ""
                    elif event.key == pg.K_BACKSPACE:
                        server_pin_entered = server_pin_entered[:-1]
                    elif event.key == pg.K_RETURN:
                        if server_pin_entered == server_pin_code:
                            server_door_open = True
                            server_pin_active = False
                            server_pin_entered = ""
                        else:
                            server_pin_entered = ""
                            server_pin_error_timer = 1.0
                    elif event.unicode.isdigit() and len(server_pin_entered) < 4:
                        server_pin_entered += event.unicode
                        server_pin_error_timer = 0.0
                        if len(server_pin_entered) == 4:
                            if server_pin_entered == server_pin_code:
                                server_door_open = True
                                server_pin_active = False
                                server_pin_entered = ""
                            else:
                                server_pin_entered = ""
                                server_pin_error_timer = 1.0
                    continue

                if event.key == pg.K_ESCAPE:
                    mouse_captured = not mouse_captured
                    pg.event.set_grab(mouse_captured)
                    pg.mouse.set_visible(not mouse_captured)
                    pg.mouse.get_rel()
                if game_status == "game" and event.key == pg.K_e:
                    if get_near_panel(player_x, player_y, panels) is not None:
                        heavy_door_open = True
                    elif get_near_server_door(player_x, player_y) is not None:
                        if not server_door_open:
                            server_pin_active = True
                            server_pin_entered = ""
                            server_pin_error_timer = 0.0
                        else:
                            player_x, player_y = teleport_through_server_door(player_x, player_y)
                    elif get_near_laboratory_door(player_x, player_y) is not None:
                        player_x, player_y = teleport_through_laboratory_door(player_x, player_y)
                    else:
                        player_x, player_y = teleport_through_security_door(player_x, player_y)
                if event.key == pg.K_f and flashlight_charge > 0:
                    flashlight_on = not flashlight_on

        #обработка клавиш
        if server_pin_error_timer > 0:
            server_pin_error_timer = max(0.0, server_pin_error_timer - dt)

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

        enemy.update(player_x, player_y, dt, collides_circle, is_wall_at_pixel)
        #ночное видение
        if night_vision_charge > 0:
            night_vision_charge -= night_vision_drain * dt
            current_fog = 0.003
            min_brightness = 20
        else:
            night_vision_charge = 0
            current_fog = 0.09
            min_brightness = 7

        if flashlight_on:
            flashlight_charge -= flashlight_drain * dt
            if flashlight_charge <= 0:
                flashlight_charge = 0
                flashlight_on = False
        ###
        screen.fill((30, 30, 30))
        '''
        for row_idx, row in enumerate(WORLD_MAP):
            for col_idx, cell in enumerate(row):
                cell_x = offset_x + col_idx * TILE_SIZE
                cell_y = offset_y + row_idx * TILE_SIZE
                if cell == "1":
                    pg.draw.rect(screen, (100, 100, 100),
                                 (cell_x, cell_y, TILE_SIZE, TILE_SIZE))
        '''
        # рисую игрока
        #pg.draw.circle(screen, (220, 220, 220), (int(player_x), int(player_y)), PLAYER_RADIUS)
        if game_status == "menu":
            draw_menu(screen, font, start_buton, exit_buton)
            pg.display.flip()
            continue

        #рисую лучи
        num_ray = WIDTH // 2
        FOV = math.pi / 3 #Угол обзора игрока
        WALL_CONST = 20000
        FLASHLIGHT_CONE = FOV / 4
        FLASHLIGHT_POWER = 0.5
        draw_ceiling_casting(screen, ceiling_texture, player_x, player_y, angle, FOV, WALL_CONST, current_fog, min_brightness, flashlight_on, FLASHLIGHT_CONE, FLASHLIGHT_POWER)
        draw_floor_casting(screen, floor_texture, player_x, player_y, angle, FOV, WALL_CONST, current_fog, min_brightness, flashlight_on, FLASHLIGHT_CONE, FLASHLIGHT_POWER)
        z_buffer = []

        start_angle = angle - FOV / 2

        for i in range(num_ray):
            ray_angle = start_angle + FOV * i / (num_ray - 1)
            ray_x, ray_y, depth, hit_cell = cast_ray(player_x, player_y, ray_angle)
            anti_fish_depth = depth * math.cos(ray_angle - angle)
            z_buffer.append(anti_fish_depth)
            wall_height = max(1, int(WALL_CONST / anti_fish_depth))
            brightness = int(255 / (1 + anti_fish_depth * current_fog))
            brightness = max(min_brightness, min(255, brightness))
            brightness = apply_flashlight(brightness, ray_angle, angle, flashlight_on, FLASHLIGHT_CONE, FLASHLIGHT_POWER)
            strip_width = 2
            x_wall = i * strip_width
            y_wall = HEIGHT / 2 - wall_height / 2
            current_texture = wall_textures.get(hit_cell, wall_texture)
            current_texture_width = current_texture.get_width()
            current_texture_height = current_texture.get_height()
            texture_x = get_texture_x(ray_x, ray_y, current_texture_width)
            texture_column = current_texture.subsurface((texture_x, 0, 1, current_texture_height))
            wall_column = pg.transform.scale(texture_column, (strip_width, wall_height))
            wall_column.fill((brightness, brightness, brightness), special_flags=pg.BLEND_MULT)
            screen.blit(wall_column, (x_wall, y_wall))
            
        for panel in panels: #Панель на посту охрану в самом начале
            draw_object_sprite(
                screen,
                panel,
                player_x,
                player_y,
                angle,
                FOV,
                WALL_CONST,
                z_buffer,
                strip_width,
                current_fog,
                min_brightness,
                flashlight_on,
                FLASHLIGHT_CONE,
                FLASHLIGHT_POWER
            )

        #отрисовка спрайта дуры
        draw_enemy_sprite(
            screen,
            enemy,
            player_x,
            player_y,
            angle,
            FOV,
            WALL_CONST,
            z_buffer,
            strip_width,
            current_fog,
            min_brightness,
            flashlight_on,
            FLASHLIGHT_CONE,
            FLASHLIGHT_POWER
        )

        interact_label = None
        if get_near_panel(player_x, player_y, panels) is not None:
            interact_label = "открыть дверь"
        elif get_near_server_door(player_x, player_y) is not None:
            if server_door_open:
                interact_label = "серверная"
            else:
                interact_label = "ввести код"
        elif get_near_laboratory_door(player_x, player_y) is not None:
            interact_label = "лаборатория"
        elif get_near_security_door(player_x, player_y) is not None:
            interact_label = "охрана"

        if interact_label is not None:
            interact_text = font.render("E", True, (230, 230, 230))
            label_text = interact_font.render(interact_label, True, (230, 230, 230))
            screen.blit(interact_text, interact_text.get_rect(center=(WIDTH // 2, HEIGHT - 95)))
            screen.blit(label_text, label_text.get_rect(center=(WIDTH // 2, HEIGHT - 60)))

        if server_pin_active:
            draw_code_lock(screen, font, interact_font, server_pin_entered, server_pin_error_timer > 0)

        pg.display.flip()
        
    pg.quit()

if __name__ == "__main__":
    main()
