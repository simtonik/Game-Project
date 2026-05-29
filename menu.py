import pygame as pg

def draw_menu(screen, font, start_buton, exit_buton):
    screen.fill((10,10,10))

    title = font.render("OBJECT51", True,(220,220,220))
    screen.blit(title,(300,120))

    pg.draw.rect(screen, (70,70,70), start_buton)
    pg.draw.rect(screen, (70,70,70), exit_buton)

    start_text = font.render("Старт", True, (230,230,230))
    exit_text = font.render("Выход", True, (230,230,230))
    
    screen.blit(start_text, start_text.get_rect(center=start_buton.center))
    screen.blit(exit_text, exit_text.get_rect(center=exit_buton.center))

def menu_events(event, start_buton, exit_buton):
    if event.type == pg.MOUSEBUTTONDOWN:
        if start_buton.collidepoint(event.pos):
            return "start"
        if exit_buton.collidepoint(event.pos):
            return "exit"
    return None
