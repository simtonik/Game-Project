import pygame

pygame.init()

pygame.display.set_mode((800,600))

run = True
while run:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            run = False
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_UP or e.key == pygame.K_w:
                print(f"Движение вверх. Клавиша: {pygame.key.name(e.key)}")
            if e.key == pygame.K_DOWN or e.key == pygame.K_s:
                print(f"Движение вниз. Клавиша: {pygame.key.name(e.key)}")
            if e.key == pygame.K_RIGHT or e.key == pygame.K_d:
                print(f"Движение вправо. Клавиша: {pygame.key.name(e.key)}")
            if e.key == pygame.K_LEFT or e.key == pygame.K_a:
                print(f"Движение влево. Клавиша: {pygame.key.name(e.key)}")
pygame.quit()