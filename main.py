import pygame, sys
from button import Button

pygame.init()

screen_width = 1024
screen_height = 720
screen = pygame.display.set_mode((screen_width, screen_height))

pygame.display.set_caption("Brain Cheeser")

background = pygame.image.load("assets/images/cheese_BG.jpeg")
menu_music = pygame.mixer.Sound("assets/sounds/menu_music.mp3")

def get_font(size):
    return pygame.font.Font("assets/fonts/font.ttf", size)

def main_menu():
    menu_music.play()
    while True:
        screen.blit(background, (0, 0))

        mouse_pos = pygame.mouse.get_pos()

        menu_text = get_font(50).render("Brain cheeser", True, "#ffcc00")
        menu_rect = menu_text.get_rect(center=(screen_width/2, 45))

        play_button = Button(image=pygame.image.load("assets/images/play_BG.png"), pos=(512, 250),
                             text_input="PLAY", font=get_font(75), base_color="#ffcc00", hovering_color="White")
        options_button = Button(image=pygame.image.load("assets/images/options_BG.png"), pos=(512, 400),
                                text_input="SETTINGS", font=get_font(75), base_color="#ffcc00", hovering_color="White")
        quit_button = Button(image=pygame.image.load("assets/images/quit_BG.png"), pos=(512, 550),
                             text_input="QUIT", font=get_font(75), base_color="#ffcc00", hovering_color="White")

        screen.blit(menu_text, menu_rect)

        for button in [play_button, options_button, quit_button]:
            button.changeColor(mouse_pos)
            button.update(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_button.checkForInput(mouse_pos):
                    play()
                if options_button.checkForInput(mouse_pos):
                    options()
                if quit_button.checkForInput(mouse_pos):
                    pygame.quit()
                    sys.exit()

        pygame.display.update()

def play():
    menu_music.stop()
    # Pálya paraméterek
    grid_size = 4  # 4x4-es rács
    cell_size = 80
    cheese_rows, cheese_cols = 1, 2  # Sajtlap méret: 1 sor magas, 2 oszlop széles
    grid_origin = (screen_width//2 - (grid_size*cell_size)//2, screen_height//2 - (grid_size*cell_size)//2)
    # Egerek fix pozícióban (pl. 3 egér)
    # 4x4-es pályán az egerek a rács metszéspontjain (csomópontokon) vannak
    # Pl. 5x5 csomópont, az egérpozíciók (sor, oszlop) 0-4-ig
    # Egerek a kockák közötti éleken (vízszintes vagy függőleges):
    # Minden egér: ((r1, c1), (r2, c2))
    mice = [
        # sor, oszlop indexelés 1-től 4-ig
        # vízszintes élek
        ((1,1), (1,2)), ((1,2), (1,3)), ((1,3), (1,4)),
        ((2,1), (2,2)), ((2,2), (2,3)), ((2,3), (2,4)),
        ((3,1), (3,2)), ((3,2), (3,3)), ((3,3), (3,4)),
        ((4,1), (4,2)), ((4,2), (4,3)), ((4,3), (4,4)),
        # függőleges élek
        ((1,1), (2,1)), ((1,2), (2,2)), ((1,3), (2,3)), ((1,4), (2,4)),
        ((2,1), (3,1)), ((2,2), (3,2)), ((2,3), (3,3)), ((2,4), (3,4)),
        ((3,1), (4,1)), ((3,2), (4,2)), ((3,3), (4,3)), ((3,4), (4,4)),
    ]
    # Sajtlap képek betöltése és átméretezése cellaméretre
    cheese_imgs = []
    cheese_rects = []
    cheese_angles = []  # forgatási szög minden sajtlaphoz (bal oldaliak)
    num_cheese = 7
    cheese_oversize = -2  # nagyon picivel kisebb csak
    for i in range(1, num_cheese + 1):
        img = pygame.image.load(f"assets/images/cheese/SAJTLAP{i}.png").convert_alpha()
        img = pygame.transform.smoothscale(
            img,
            (cheese_cols*cell_size + cheese_oversize, cheese_rows*cell_size + cheese_oversize)
        )
        cheese_imgs.append(img)
        # A bal oldali készletben is igazítsuk középre a nagyobb képet
        cheese_rects.append(img.get_rect(topleft=(30, 100 + (i-1)*70 - cheese_oversize//2)))
        cheese_angles.append(0)
    dragging_idx = None  # Bal oldali sajtlap indexe, ha azt húzzuk
    dragging_placed_idx = None  # Pályán lévő sajtlap indexe, ha azt húzzuk
    offset = (0, 0)

    # placed_cheese: list of dict: {img, rect, angle}
    placed_cheese = []

    while True:
        PLAY_MOUSE_POS = pygame.mouse.get_pos()
        # Háttér kirajzolása minden frame-ben
        screen.blit(background, (0, 0))
        # Pálya rács kirajzolása
        for row in range(grid_size):
            for col in range(grid_size):
                rect = pygame.Rect(
                    grid_origin[0] + col*cell_size,
                    grid_origin[1] + row*cell_size,
                    cell_size, cell_size)
                pygame.draw.rect(screen, "#fff8dc", rect)
                pygame.draw.rect(screen, "#b8860b", rect, 2)

        # Egérkép betöltése
        mouse_img = pygame.image.load("assets/images/mouse.png").convert_alpha()
        mouse_img = pygame.transform.smoothscale(mouse_img, (36, 36))
        for (cell1, cell2) in mice:
            r1, c1 = cell1
            r2, c2 = cell2
            # Átlagoljuk a két cella középpontját
            x1 = grid_origin[0] + (c1-1)*cell_size + cell_size//2
            y1 = grid_origin[1] + (r1-1)*cell_size + cell_size//2
            x2 = grid_origin[0] + (c2-1)*cell_size + cell_size//2
            y2 = grid_origin[1] + (r2-1)*cell_size + cell_size//2
            center = ((x1 + x2)//2, (y1 + y2)//2)
            rect = mouse_img.get_rect(center=center)
            screen.blit(mouse_img, rect)

        # Elhelyezett sajtlapok kirajzolása
        for idx, pc in enumerate(placed_cheese):
            draw_img = pygame.transform.rotate(pc['img'], pc['angle'])
            # Mindig a bal felső sarokhoz igazítunk
            draw_rect = draw_img.get_rect(topleft=pc['rect'].topleft)
            # Ha ezt húzzuk, az egérnél jelenjen meg
            if dragging_placed_idx == idx:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                draw_rect.topleft = (mouse_x - offset[0], mouse_y - offset[1])
            screen.blit(draw_img, draw_rect)
            pc['rect'] = draw_rect.copy()

        # Sajtlap képek bal oldalon (húzhatóak)
        for i, img in enumerate(cheese_imgs):
            draw_img = pygame.transform.rotate(img, cheese_angles[i])
            draw_rect = draw_img.get_rect(topleft=cheese_rects[i].topleft)
            # Ha ezt húzzuk, az egérnél jelenjen meg
            if dragging_idx == i:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                draw_rect.topleft = (mouse_x - offset[0], mouse_y - offset[1])
            screen.blit(draw_img, draw_rect)
            cheese_rects[i] = draw_rect.copy()

        # Vissza gomb
        PLAY_BACK = Button(image=None, pos=(screen_width/2, screen_height-60),
                            text_input="BACK", font=get_font(50), base_color="#ffcc00", hovering_color="white")
        PLAY_BACK.changeColor(PLAY_MOUSE_POS)
        PLAY_BACK.update(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if PLAY_BACK.checkForInput(PLAY_MOUSE_POS):
                    main_menu()
                # Bal egérgomb: húzás kezdete (csak egyet lehet)
                if event.button == 1 and dragging_idx is None and dragging_placed_idx is None:
                    # Először nézzük a pályán lévő sajtlapokat (fordított sorrend, hogy a legfelsőt kapjuk el)
                    for idx in reversed(range(len(placed_cheese))):
                        pc = placed_cheese[idx]
                        if pc['rect'].collidepoint(event.pos):
                            dragging_placed_idx = idx
                            offset = (event.pos[0] - pc['rect'].x, event.pos[1] - pc['rect'].y)
                            break
                    else:
                        # Ha nem a pályán, akkor bal oldali készletből
                        for i, rect in enumerate(cheese_rects):
                            if rect.collidepoint(event.pos):
                                dragging_idx = i
                                offset = (event.pos[0] - rect.x, event.pos[1] - rect.y)
                                break
                # Jobb egérgomb: forgatás bal oldali sajtlapokon
                if event.button == 3:
                    for i, rect in enumerate(cheese_rects):
                        if rect.collidepoint(event.pos):
                            cheese_angles[i] = (cheese_angles[i] - 90) % 360
                            break
                    # Forgatás a pályán lévő sajtlapokon
                    for pc in placed_cheese:
                        if pc['rect'].collidepoint(event.pos):
                            pc['angle'] = (pc['angle'] - 90) % 360
                            break
            if event.type == pygame.MOUSEBUTTONUP:
                # Bal oldali sajtlap húzás vége
                if dragging_idx is not None:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    img = cheese_imgs[dragging_idx]
                    angle = cheese_angles[dragging_idx]
                    # Sajtlap orientációja: vízszintes (0/180) vagy álló (90/270)
                    if angle % 180 == 0:
                        w, h = cheese_cols, cheese_rows  # 2x1
                    else:
                        w, h = cheese_rows, cheese_cols  # 1x2
                    grid_x = (mouse_x - grid_origin[0]) // cell_size
                    grid_y = (mouse_y - grid_origin[1]) // cell_size
                    if 0 <= grid_x <= grid_size - w and 0 <= grid_y <= grid_size - h:
                        snap_x = grid_origin[0] + grid_x * cell_size
                        snap_y = grid_origin[1] + grid_y * cell_size
                        # Forgatott kép mérete
                        draw_img = pygame.transform.rotate(img, angle)
                        new_rect = draw_img.get_rect(topleft=(snap_x, snap_y))
                        placed_cheese.append({'img': img, 'rect': new_rect.copy(), 'angle': angle})
                    cheese_rects[dragging_idx].topleft = (30, 100 + dragging_idx*70)
                    dragging_idx = None
                # Pályán lévő sajtlap húzás vége
                if dragging_placed_idx is not None:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    pc = placed_cheese[dragging_placed_idx]
                    img = pc['img']
                    angle = pc['angle']
                    if angle % 180 == 0:
                        w, h = cheese_cols, cheese_rows  # 2x1
                    else:
                        w, h = cheese_rows, cheese_cols  # 1x2
                    grid_x = (mouse_x - grid_origin[0]) // cell_size
                    grid_y = (mouse_y - grid_origin[1]) // cell_size
                    if 0 <= grid_x <= grid_size - w and 0 <= grid_y <= grid_size - h:
                        snap_x = grid_origin[0] + grid_x * cell_size
                        snap_y = grid_origin[1] + grid_y * cell_size
                        draw_img = pygame.transform.rotate(img, angle)
                        new_rect = draw_img.get_rect(topleft=(snap_x, snap_y))
                        placed_cheese[dragging_placed_idx]['rect'] = new_rect.copy()
                    else:
                        # Ha nem a pályán engeded el, töröljük a pályáról
                        placed_cheese.pop(dragging_placed_idx)
                    dragging_placed_idx = None
            if event.type == pygame.MOUSEMOTION:
                if dragging_idx is not None:
                    mouse_x, mouse_y = event.pos
                    cheese_rects[dragging_idx].topleft = (mouse_x - offset[0], mouse_y - offset[1])
                if dragging_placed_idx is not None:
                    mouse_x, mouse_y = event.pos
                    placed_cheese[dragging_placed_idx]['rect'].topleft = (mouse_x - offset[0], mouse_y - offset[1])

        pygame.display.update()
    
def options():
    menu_music.stop()
    while True:
        OPTIONS_MOUSE_POS = pygame.mouse.get_pos()

        screen.fill("black")

        OPTIONS_TEXT = get_font(20).render("Ez a beállítások kijelző.", True, "#ffcc00")
        OPTIONS_RECT = OPTIONS_TEXT.get_rect(center=(screen_width/2, 260))
        screen.blit(OPTIONS_TEXT, OPTIONS_RECT)

        OPTIONS_BACK = Button(image=None, pos=(screen_width/2, 460),
                            text_input="BACK", font=get_font(75), base_color="#ffcc00", hovering_color="white")

        OPTIONS_BACK.changeColor(OPTIONS_MOUSE_POS)
        OPTIONS_BACK.update(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if OPTIONS_BACK.checkForInput(OPTIONS_MOUSE_POS):
                    main_menu()

        pygame.display.update()

if __name__ == '__main__':
    main_menu()