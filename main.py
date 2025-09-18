import pygame, sys, json, os
from assets.button import Button

pygame.init()

SAVE_DIR = "saves"
os.makedirs(SAVE_DIR, exist_ok=True)

screen_width = 1024
screen_height = 720
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Brain Cheeser")

background = pygame.image.load("assets/images/cheese_BG.jpeg")
menu_music = pygame.mixer.Sound("assets/sounds/menu_music.mp3")

# ---------------- CONFIGURÁCIÓ (Kezdő mód) -----------------
LEVEL_LOCKED_PIECES = {
    1: [
        { 'img_index': 1, 'row': 1, 'col': 1, 'angle': 0,   'flip': True  },
        { 'img_index': 3, 'row': 1, 'col': 3, 'angle': 0,   'flip': False },
        { 'img_index': 6, 'row': 2, 'col': 1, 'angle': 90,  'flip': False },
        { 'img_index': 5, 'row': 4, 'col': 1, 'angle': 0,   'flip': False },
        { 'img_index': 2, 'row': 4, 'col': 3, 'angle': 180, 'flip': False },
        { 'img_index': 4, 'row': 2, 'col': 4, 'angle': 270, 'flip': False },
    ],
    2: [],
    3: [],
    4: [],
    5: [],
}

LEVEL_COMPLETION_TARGETS = {
    1: [
        { 'img_index': 3, 'cells': [(3,2),(3,3)], 'angle': 'any-horizontal', 'flip': None },
        { 'img_index': 1, 'cells': [(2,2),(2,3)], 'angle': 180, 'flip': True },
    ],
    2: [],
    3: [],
    4: [],
    5: [],
}

def get_font(size:int):
    return pygame.font.Font("assets/fonts/font.ttf", size)

def get_locked_pieces_for_level(level:int):
    return LEVEL_LOCKED_PIECES.get(level, [])

def get_completion_targets_for_level(level:int):
    return LEVEL_COMPLETION_TARGETS.get(level, [])

def apply_locked_pieces(level:int, placed_cheese:list, cheese_imgs:list, grid_origin, cell_size):
    specs = get_locked_pieces_for_level(level)
    if not cheese_imgs:
        return
    for spec in specs:
        idx = spec['img_index']
        if not (0 <= idx < len(cheese_imgs)):
            continue
        base_img = cheese_imgs[idx]
        row = spec['row']; col = spec['col']
        angle = spec['angle']; flip = spec['flip']
        top_left = (grid_origin[0] + (col-1)*cell_size, grid_origin[1] + (row-1)*cell_size)
        disp_img = base_img
        if flip:
            disp_img = pygame.transform.flip(disp_img, True, False)
        disp_img = pygame.transform.rotate(disp_img, angle)
        rect = disp_img.get_rect(topleft=top_left)
        # Nézzük meg, hogy már van-e ilyen lockolt darab ugyanazon a rács pozíción (topleft alapján)
        exists = False
        for pc in placed_cheese:
            if pc.get('lock') and pc['rect'].topleft == rect.topleft:
                # Frissítjük a paramétereket (ha esetleg változtattunk a konfiguráción)
                pc['img'] = base_img
                pc['angle'] = angle
                pc['flip'] = flip
                exists = True
                break
        if not exists:
            placed_cheese.append({'img': base_img, 'rect': rect, 'angle': angle, 'flip': flip, 'lock': True})

def beginner_mode_with_level(level:int):
    # Játék paraméterek
    grid_size = 4
    cell_size = 80
    cheese_rows, cheese_cols = 1, 2
    grid_origin = (350, screen_height//2 - (grid_size*cell_size)//2)
    mice = get_beginner_level_mice(level)

    # Sajtlap készlet
    cheese_imgs = []
    cheese_rects = []
    cheese_angles = []
    cheese_flips = []
    num_cheese = 7
    oversize = -2
    for i in range(1, num_cheese+1):
        img = pygame.image.load(f"assets/images/cheese/SAJTLAP{i}.png").convert_alpha()
        img = pygame.transform.smoothscale(img, (cheese_cols*cell_size + oversize, cheese_rows*cell_size + oversize))
        cheese_imgs.append(img)
        cheese_rects.append(img.get_rect(topleft=(30, 100 + (i-1)*70 - oversize//2)))
        cheese_angles.append(0)
        cheese_flips.append(False)

    dragging_idx = None
    dragging_placed_idx = None
    offset = (0,0)

    placed_cheese = load_beginner_level(level, cheese_imgs)
    apply_locked_pieces(level, placed_cheese, cheese_imgs, grid_origin, cell_size)

    def piece_cells(rect, angle):
        rel_x = rect.x - grid_origin[0]
        rel_y = rect.y - grid_origin[1]
        col = rel_x // cell_size + 1
        row = rel_y // cell_size + 1
        if angle % 180 == 0:
            return {(row,col), (row, col+1)}
        return {(row,col), (row+1, col)}

    def build_occupied(exclude_idx=None):
        occ=set()
        for idx, pc in enumerate(placed_cheese):
            if exclude_idx is not None and idx == exclude_idx:
                continue
            occ |= piece_cells(pc['rect'], pc['angle'])
        return occ

    level_completed = False

    # Generic completion using LEVEL_COMPLETION_TARGETS
    targets = get_completion_targets_for_level(level)

    def img_index(img):
        for i, im in enumerate(cheese_imgs):
            if im == img:
                return i
        return -1

    def matches_angle(req, ang):
        if isinstance(req, int):
            return (ang % 360) == (req % 360)
        if req == 'any-horizontal':
            return ang % 180 == 0
        if req == 'any-vertical':
            return ang % 180 == 90
        return False

    def check_completion():
        if not targets:
            return False
        satisfied = [False]*len(targets)
        for pc in placed_cheese:
            idx = img_index(pc['img'])
            pc_cells = piece_cells(pc['rect'], pc['angle'])
            for ti, t in enumerate(targets):
                if satisfied[ti]:
                    continue
                if idx != t['img_index']:
                    continue
                if set(t['cells']) != pc_cells:
                    continue
                if t['flip'] is not None and pc.get('flip', False) != t['flip']:
                    continue
                if not matches_angle(t['angle'], pc['angle']):
                    continue
                satisfied[ti] = True
        return all(satisfied)

    while True:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill("black")
        # Draw grid
        for r in range(grid_size):
            for c in range(grid_size):
                rect = pygame.Rect(grid_origin[0] + c*cell_size, grid_origin[1] + r*cell_size, cell_size, cell_size)
                pygame.draw.rect(screen, "#fff8dc", rect)
                pygame.draw.rect(screen, "#b8860b", rect, 2)
        # Level text
        lvl_text = get_font(40).render(f"LEVEL {level}  |  MICE: {len(mice)}", True, "#ffcc00")
        screen.blit(lvl_text, lvl_text.get_rect(center=(screen_width/2,40)))
        if not level_completed:
            level_completed = check_completion()
        # Mice
        mouse_img = pygame.image.load("assets/images/mouse.png").convert_alpha()
        mouse_img = pygame.transform.smoothscale(mouse_img, (40,40))
        for (a,b) in mice:
            (r1,c1),(r2,c2)=a,b
            x1 = grid_origin[0] + (c1-1)*cell_size + cell_size//2
            y1 = grid_origin[1] + (r1-1)*cell_size + cell_size//2
            x2 = grid_origin[0] + (c2-1)*cell_size + cell_size//2
            y2 = grid_origin[1] + (r2-1)*cell_size + cell_size//2
            center = ((x1+x2)//2, (y1+y2)//2)
            screen.blit(mouse_img, mouse_img.get_rect(center=center))
        # Placed pieces
        for idx, pc in enumerate(placed_cheese):
            base = pc['img']
            if pc.get('flip'): base = pygame.transform.flip(base, True, False)
            draw = pygame.transform.rotate(base, pc['angle'])
            rect = draw.get_rect(topleft=pc['rect'].topleft)
            if dragging_placed_idx == idx:
                mx,my = mouse_pos
                rect.topleft = (mx - offset[0], my - offset[1])
            screen.blit(draw, rect)
            pc['rect'] = rect.copy()
        # Inventory pieces
        for i, img in enumerate(cheese_imgs):
            base = img
            if cheese_flips[i]: base = pygame.transform.flip(base, True, False)
            draw = pygame.transform.rotate(base, cheese_angles[i])
            rect = draw.get_rect(topleft=cheese_rects[i].topleft)
            if dragging_idx == i:
                mx,my = mouse_pos
                rect.topleft = (mx - offset[0], my - offset[1])
            screen.blit(draw, rect)
            cheese_rects[i] = rect.copy()
        back_btn = Button(image=None, pos=(screen_width/2, screen_height-60), text_input="BACK", font=get_font(50), base_color="#ffcc00", hovering_color="white")
        back_btn.changeColor(mouse_pos); back_btn.update(screen)
        if level_completed:
            comp = get_font(70).render("COMPLETED!", True, (50,200,50))
            screen.blit(comp, comp.get_rect(center=(screen_width/2, screen_height//2)))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if level_completed:
                    if back_btn.checkForInput(mouse_pos):
                        save_beginner_level(level, placed_cheese, cheese_imgs)
                        beginner_levels_menu()
                    continue
                if back_btn.checkForInput(mouse_pos):
                    save_beginner_level(level, placed_cheese, cheese_imgs)
                    beginner_levels_menu()
                if event.button == 1 and dragging_idx is None and dragging_placed_idx is None:
                    # placed pieces topmost first
                    for idx in reversed(range(len(placed_cheese))):
                        pc = placed_cheese[idx]
                        if pc['rect'].collidepoint(event.pos):
                            if not pc.get('lock'):
                                dragging_placed_idx = idx
                                offset = (event.pos[0]-pc['rect'].x, event.pos[1]-pc['rect'].y)
                            break
                    else:
                        for i, r in enumerate(cheese_rects):
                            if r.collidepoint(event.pos):
                                dragging_idx = i
                                offset = (event.pos[0]-r.x, event.pos[1]-r.y)
                                break
                if event.button == 3: # rotate
                    rotated=False
                    for i, r in enumerate(cheese_rects):
                        if r.collidepoint(event.pos):
                            cheese_angles[i] = (cheese_angles[i]-90)%360
                            rotated=True; break
                    if not rotated:
                        for idx, pc in enumerate(placed_cheese):
                            if pc['rect'].collidepoint(event.pos) and not pc.get('lock'):
                                old=pc['angle']; pc['angle']=(pc['angle']-90)%360
                                occ=build_occupied(exclude_idx=idx)
                                cells=piece_cells(pc['rect'], pc['angle'])
                                if any(r<1 or c<1 or r>grid_size or c>grid_size for (r,c) in cells) or cells & occ:
                                    pc['angle']=old
                                break
                if event.button == 2: # flip
                    flipped=False
                    for i,r in enumerate(cheese_rects):
                        if r.collidepoint(event.pos): cheese_flips[i]=not cheese_flips[i]; flipped=True; break
                    if not flipped:
                        for pc in placed_cheese:
                            if pc['rect'].collidepoint(event.pos) and not pc.get('lock'):
                                pc['flip']=not pc.get('flip', False); break
            if event.type == pygame.KEYDOWN and not level_completed:
                if event.key == pygame.K_f:
                    pos = pygame.mouse.get_pos(); flipped=False
                    for i,r in enumerate(cheese_rects):
                        if r.collidepoint(pos): cheese_flips[i]=not cheese_flips[i]; flipped=True; break
                    if not flipped:
                        for pc in placed_cheese:
                            if pc['rect'].collidepoint(pos) and not pc.get('lock'):
                                pc['flip']=not pc.get('flip', False); break
            if event.type == pygame.MOUSEBUTTONUP and not level_completed:
                if dragging_idx is not None:
                    mx,my = pygame.mouse.get_pos()
                    ang = cheese_angles[dragging_idx]
                    w,h = (cheese_cols, cheese_rows) if ang % 180 == 0 else (cheese_rows, cheese_cols)
                    gx = (mx - grid_origin[0]) // cell_size
                    gy = (my - grid_origin[1]) // cell_size
                    if 0 <= gx <= grid_size - w and 0 <= gy <= grid_size - h:
                        sx = grid_origin[0] + gx*cell_size
                        sy = grid_origin[1] + gy*cell_size
                        draw = pygame.transform.rotate(cheese_imgs[dragging_idx], ang)
                        new_rect = draw.get_rect(topleft=(sx,sy))
                        cells = piece_cells(new_rect, ang)
                        occ = build_occupied()
                        if not (cells & occ) and all(1<=r<=grid_size and 1<=c<=grid_size for (r,c) in cells):
                            placed_cheese.append({'img': cheese_imgs[dragging_idx], 'rect': new_rect.copy(), 'angle': ang, 'flip': cheese_flips[dragging_idx]})
                    cheese_rects[dragging_idx].topleft = (30, 100 + dragging_idx*70)
                    dragging_idx = None
                if dragging_placed_idx is not None:
                    mx,my = pygame.mouse.get_pos()
                    pc = placed_cheese[dragging_placed_idx]
                    ang = pc['angle']
                    w,h = (cheese_cols, cheese_rows) if ang % 180 == 0 else (cheese_rows, cheese_cols)
                    gx = (mx - grid_origin[0]) // cell_size
                    gy = (my - grid_origin[1]) // cell_size
                    if 0 <= gx <= grid_size - w and 0 <= gy <= grid_size - h:
                        sx = grid_origin[0] + gx*cell_size
                        sy = grid_origin[1] + gy*cell_size
                        draw = pygame.transform.rotate(pc['img'], ang)
                        new_rect = draw.get_rect(topleft=(sx,sy))
                        cells = piece_cells(new_rect, ang)
                        occ = build_occupied(exclude_idx=dragging_placed_idx)
                        if not (cells & occ) and all(1<=r<=grid_size and 1<=c<=grid_size for (r,c) in cells):
                            placed_cheese[dragging_placed_idx]['rect'] = new_rect.copy()
                    else:
                        if not pc.get('lock'):
                            placed_cheese.pop(dragging_placed_idx)
                    dragging_placed_idx = None
            if event.type == pygame.MOUSEMOTION and not level_completed:
                if dragging_idx is not None:
                    mx,my = event.pos
                    cheese_rects[dragging_idx].topleft = (mx - offset[0], my - offset[1])
                if dragging_placed_idx is not None:
                    mx,my = event.pos
                    placed_cheese[dragging_placed_idx]['rect'].topleft = (mx - offset[0], my - offset[1])
        pygame.display.update()

    def piece_cells(rect, angle):
        """Visszaadja a sajtlap által elfoglalt rács cella koordinátákat (row,col) 1-alapú.
        A sajtlap 2x1 vagy 1x2 méretű az angle alapján. rect bal felső sarkát rácshoz igazítjuk.
        """
        rel_x = rect.x - grid_origin[0]
        rel_y = rect.y - grid_origin[1]
        col = rel_x // cell_size + 1
        row = rel_y // cell_size + 1
        if angle % 180 == 0:  # vízszintes: 2 széles
            return {(row, col), (row, col+1)}
        else:  # álló: 2 magas
            return {(row, col), (row+1, col)}

    def build_occupied(exclude_idx=None):
        occ = set()
        for idx, pc in enumerate(placed_cheese):
            if exclude_idx is not None and idx == exclude_idx:
                continue
            occ |= piece_cells(pc['rect'], pc['angle'])
        return occ

    # --- Győzelmi feltétel változók (Level specifikus) ---
    level_completed = False

    def get_img_index(img):
        for i, im in enumerate(cheese_imgs):
            if im == img:
                return i
        return -1

    def cells_for_rect(rect, angle):
        return piece_cells(rect, angle)

    def check_completion():
        """Ellenőrzi, hogy a játékos lerakta-e a szükséges 2 darabot:
        - SAJTLAP4 (index 3, 0-alapú) vízszintesen a (3,2)-(3,3) cellákon
        - SAJTLAP2 (index 1, 0-alapú) vízszintesen TÜKRÖZVE és PONTOSAN 180° forgatással a (2,2)-(2,3) cellákon
        (Tehát az angle == 180, nem elég a 0.)
        """
        need_sajtlap4 = False
        need_sajtlap2 = False
        target_cells_s4 = {(3,2),(3,3)}
        target_cells_s2 = {(2,2),(2,3)}
        for pc in placed_cheese:
            idx = get_img_index(pc['img'])
            if idx == 3:  # SAJTLAP4
                if pc['angle'] % 180 == 0 and cells_for_rect(pc['rect'], pc['angle']) == target_cells_s4:
                    need_sajtlap4 = True
            elif idx == 1:  # SAJTLAP2
                # Követelmény: flip True és szög pontosan 180
                if pc.get('flip', False) and (pc['angle'] % 360 == 180) and cells_for_rect(pc['rect'], pc['angle']) == target_cells_s2:
                    need_sajtlap2 = True
        return need_sajtlap4 and need_sajtlap2

    while True:
        PLAY_MOUSE_POS = pygame.mouse.get_pos()
        # Háttér kirajzolása minden frame-ben
        screen.fill("black")
        # Pálya rács kirajzolása
        for row in range(grid_size):
            for col in range(grid_size):
                rect = pygame.Rect(
                    grid_origin[0] + col*cell_size,
                    grid_origin[1] + row*cell_size,
                    cell_size, cell_size)
                pygame.draw.rect(screen, "#fff8dc", rect)
                pygame.draw.rect(screen, "#b8860b", rect, 2)

        # Szint kiírása
        level_text = get_font(40).render(f"LEVEL {level}  |  MICE: {len(mice)}", True, "#ffcc00")
        level_rect = level_text.get_rect(center=(screen_width/2, 40))
        screen.blit(level_text, level_rect)

        # Győzelem ellenőrzés (ha még nem teljesült)
        if not level_completed:
            level_completed = check_completion()

        # Egérkép betöltése
        mouse_img = pygame.image.load("assets/images/mouse.png").convert_alpha()
        mouse_img = pygame.transform.smoothscale(mouse_img, (40, 40))
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
            base_img = pc['img']
            if pc.get('flip', False):
                base_img = pygame.transform.flip(base_img, True, False)
            draw_img = pygame.transform.rotate(base_img, pc['angle'])
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
            base_img = img
            if cheese_flips[i]:
                base_img = pygame.transform.flip(base_img, True, False)
            draw_img = pygame.transform.rotate(base_img, cheese_angles[i])
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

        # Ha teljesítve, írjuk ki a közepére
        if level_completed:
            comp_text = get_font(70).render("COMPLETED!", True, (50,200,50))
            comp_rect = comp_text.get_rect(center=(screen_width/2, screen_height//2))
            screen.blit(comp_text, comp_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Ha teljesítve, csak a BACK gomb működjön
                if level_completed:
                    if PLAY_BACK.checkForInput(PLAY_MOUSE_POS):
                        save_beginner_level(level, placed_cheese, cheese_imgs)
                        beginner_levels_menu()
                    continue
                if PLAY_BACK.checkForInput(PLAY_MOUSE_POS):
                    save_beginner_level(level, placed_cheese, cheese_imgs)
                    beginner_levels_menu()
                # Bal egérgomb: húzás kezdete (csak egyet lehet)
                if event.button == 1 and dragging_idx is None and dragging_placed_idx is None:
                    # Először nézzük a pályán lévő sajtlapokat (fordított sorrend, hogy a legfelsőt kapjuk el)
                    for idx in reversed(range(len(placed_cheese))):
                        pc = placed_cheese[idx]
                        if pc['rect'].collidepoint(event.pos):
                            if pc.get('lock'):
                                dragging_placed_idx = None
                            else:
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
                # Jobb egérgomb: forgatás bal oldali és pályán lévő sajtlapokon
                if event.button == 3:
                    # Forgatás bal oldali készletben (engedélyezett külön ellenőrzés nélkül)
                    rotated_inventory = False
                    for i, rect in enumerate(cheese_rects):
                        if rect.collidepoint(event.pos):
                            cheese_angles[i] = (cheese_angles[i] - 90) % 360
                            rotated_inventory = True
                            break
                    if not rotated_inventory:
                        # Forgatás a pályán: csak ha nem ütközik
                        for idx, pc in enumerate(placed_cheese):
                            if pc['rect'].collidepoint(event.pos):
                                if pc.get('lock'):
                                    pass
                                else:
                                    old_angle = pc['angle']
                                    pc['angle'] = (pc['angle'] - 90) % 360
                                    occ = build_occupied(exclude_idx=idx)
                                    cells = piece_cells(pc['rect'], pc['angle'])
                                    if any(r < 1 or c < 1 or r > grid_size or c > grid_size for (r,c) in cells) or cells & occ:
                                        pc['angle'] = old_angle
                                break
                # Középső egérgomb (button 2): tükrözés (flip)
                if event.button == 2:
                    flipped = False
                    for i, rect in enumerate(cheese_rects):
                        if rect.collidepoint(event.pos):
                            cheese_flips[i] = not cheese_flips[i]
                            flipped = True
                            break
                    if not flipped:
                        for pc in placed_cheese:
                            if pc['rect'].collidepoint(event.pos):
                                if not pc.get('lock'):
                                    pc['flip'] = not pc.get('flip', False)
                                break
            if event.type == pygame.KEYDOWN:
                if level_completed:
                    continue  # Nincs több interakció
                # F billentyű: tükrözés a kijelölt / egér alatti sajtlapon (inventory előnyt élvez)
                if event.key == pygame.K_f:
                    pos = pygame.mouse.get_pos()
                    flipped = False
                    for i, rect in enumerate(cheese_rects):
                        if rect.collidepoint(pos):
                            cheese_flips[i] = not cheese_flips[i]
                            flipped = True
                            break
                    if not flipped:
                        for pc in placed_cheese:
                            if pc['rect'].collidepoint(pos):
                                if not pc.get('lock'):
                                    pc['flip'] = not pc.get('flip', False)
                                break
            if event.type == pygame.MOUSEBUTTONUP:
                if level_completed:
                    continue  # Nincs több interakció
                # Bal oldali sajtlap húzás vége
                if dragging_idx is not None:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    img = cheese_imgs[dragging_idx]
                    angle = cheese_angles[dragging_idx]
                    if angle % 180 == 0:
                        w, h = cheese_cols, cheese_rows
                    else:
                        w, h = cheese_rows, cheese_cols
                    grid_x = (mouse_x - grid_origin[0]) // cell_size
                    grid_y = (mouse_y - grid_origin[1]) // cell_size
                    if 0 <= grid_x <= grid_size - w and 0 <= grid_y <= grid_size - h:
                        snap_x = grid_origin[0] + grid_x * cell_size
                        snap_y = grid_origin[1] + grid_y * cell_size
                        draw_img = pygame.transform.rotate(img, angle)
                        new_rect = draw_img.get_rect(topleft=(snap_x, snap_y))
                        cells = piece_cells(new_rect, angle)
                        occ = build_occupied()
                        if not (cells & occ) and all(1 <= r <= grid_size and 1 <= c <= grid_size for (r,c) in cells):
                            placed_cheese.append({'img': img, 'rect': new_rect.copy(), 'angle': angle, 'flip': cheese_flips[dragging_idx]})
                    cheese_rects[dragging_idx].topleft = (30, 100 + dragging_idx*70)
                    dragging_idx = None
                # Pályán lévő sajtlap húzás vége
                if dragging_placed_idx is not None:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    pc = placed_cheese[dragging_placed_idx]
                    img = pc['img']
                    angle = pc['angle']
                    if angle % 180 == 0:
                        w, h = cheese_cols, cheese_rows
                    else:
                        w, h = cheese_rows, cheese_cols
                    grid_x = (mouse_x - grid_origin[0]) // cell_size
                    grid_y = (mouse_y - grid_origin[1]) // cell_size
                    if 0 <= grid_x <= grid_size - w and 0 <= grid_y <= grid_size - h:
                        snap_x = grid_origin[0] + grid_x * cell_size
                        snap_y = grid_origin[1] + grid_y * cell_size
                        draw_img = pygame.transform.rotate(img, angle)
                        new_rect = draw_img.get_rect(topleft=(snap_x, snap_y))
                        cells = piece_cells(new_rect, angle)
                        occ = build_occupied(exclude_idx=dragging_placed_idx)
                        if not (cells & occ) and all(1 <= r <= grid_size and 1 <= c <= grid_size for (r,c) in cells):
                            placed_cheese[dragging_placed_idx]['rect'] = new_rect.copy()
                        else:
                            # visszaugrik eredeti helyére (már ott van a rect-ben, semmi teendő)
                            pass
                    else:
                        # Ha nem a pályán engeded el és nem lockolt -> törlés, lockolt -> marad
                        if not pc.get('lock'):
                            placed_cheese.pop(dragging_placed_idx)
                    dragging_placed_idx = None
            if event.type == pygame.MOUSEMOTION:
                if level_completed:
                    continue
                if dragging_idx is not None:
                    mouse_x, mouse_y = event.pos
                    cheese_rects[dragging_idx].topleft = (mouse_x - offset[0], mouse_y - offset[1])
                if dragging_placed_idx is not None:
                    mouse_x, mouse_y = event.pos
                    placed_cheese[dragging_placed_idx]['rect'].topleft = (mouse_x - offset[0], mouse_y - offset[1])

        pygame.display.update()

def beginner_levels_menu():
    # A szint választó menü a menü zenét használja, csak akkor indítsuk ha nem szól
    if not pygame.mixer.get_busy():
        menu_music.play(-1)
    while True:
        screen.blit(background, (0,0))
        mouse_pos = pygame.mouse.get_pos()

        title_text = get_font(60).render("BEGINNER LEVELS", True, "#ffcc00")
        title_rect = title_text.get_rect(center=(screen_width/2, 80))
        screen.blit(title_text, title_rect)

        # 5 szint gombok
        level_buttons = []
        start_y = 200
        spacing = 90
        for i in range(5):
            btn = Button(image=pygame.image.load("assets/images/play_BG.png"),
                         pos=(screen_width/2, start_y + i*spacing),
                         text_input=f"LEVEL {i+1}", font=get_font(50), base_color="#ffcc00", hovering_color="White")
            level_buttons.append(btn)

        back_button = Button(image=pygame.image.load("assets/images/quit_BG.png"), pos=(screen_width/2, start_y + 5*spacing),
                              text_input="BACK", font=get_font(50), base_color="#ffcc00", hovering_color="Red")

        for btn in level_buttons + [back_button]:
            btn.changeColor(mouse_pos)
            btn.update(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for idx, btn in enumerate(level_buttons):
                    if btn.checkForInput(mouse_pos):
                        beginner_mode_with_level(idx+1)
                if back_button.checkForInput(mouse_pos):
                    main_menu()

        pygame.display.update()

def get_beginner_level_mice(level:int):
    """Szintenként eltérő egér (él) elhelyezések.
    Minden elem egy él: ((r1,c1),(r2,c2)) ahol 1..4 a cella index a 4x4 rácson.
    Lehet fokozatosan növelni a nehézséget: kevés egér -> több egér -> stratégiai elhelyezés.
    """
    edges = base_beginner_edges()
    # Level 1: 3., 5., 16., 18. él (emberi index) – user specifikáció
    lvl1_indices = [3,5,16,18]
    level1 = [edges[i-1] for i in lvl1_indices if 1 <= i <= len(edges)]

    # Level 2: Level1 + további strukturális élek (6,8,20)
    lvl2_extra = [6,8,20]
    level2 = level1 + [edges[i-1] for i in lvl2_extra]

    # Level 3: Több felső kontroll – 1..6 + 13..16 + 18
    lvl3_indices = list(range(1,7)) + [13,14,15,16,18]
    level3 = [edges[i-1] for i in lvl3_indices]

    # Level 4: Hozzáadjuk a 3. vízszintes sort és pár középső függőlegest: +7,8,9,17,19,20
    lvl4_indices = lvl3_indices + [7,8,9,17,19,20]
    seen=set(); level4=[]
    for i in lvl4_indices:
        if i not in seen:
            seen.add(i); level4.append(edges[i-1])

    # Level 5: Teljes lista
    level5 = edges[:]

    mapping = {1: level1, 2: level2, 3: level3, 4: level4, 5: level5}
    return mapping.get(level, level1)

def base_beginner_edges():
    """Felhasználó által megadott 24 él sorrend (1..24) a 4x4 cellás rácson.
    Sorrend (emberi index -> él):
    1:  (1,1)-(1,2)
    2:  (1,2)-(1,3)
    3:  (1,3)-(1,4)
    4:  (1,1)-(2,1)
    5:  (1,2)-(2,2)
    6:  (1,3)-(2,3)
    7:  (1,4)-(2,4)
    8:  (2,1)-(2,2)
    9:  (2,2)-(2,3)
    10: (2,3)-(2,4)
    11: (2,1)-(3,1)
    12: (2,2)-(3,2)
    13: (2,3)-(3,3)
    14: (2,4)-(3,4)
    15: (3,1)-(3,2)
    16: (3,2)-(3,3)
    17: (3,3)-(3,4)
    18: (3,1)-(4,1)
    19: (3,2)-(4,2)
    20: (3,3)-(4,3)
    21: (3,4)-(4,4)
    22: (4,1)-(4,2)
    23: (4,2)-(4,3)
    24: (4,3)-(4,4)
    """
    return [
        ((1,1),(1,2)), ((1,2),(1,3)), ((1,3),(1,4)),
        ((1,1),(2,1)), ((1,2),(2,2)), ((1,3),(2,3)), ((1,4),(2,4)),
        ((2,1),(2,2)), ((2,2),(2,3)), ((2,3),(2,4)),
        ((2,1),(3,1)), ((2,2),(3,2)), ((2,3),(3,3)), ((2,4),(3,4)),
        ((3,1),(3,2)), ((3,2),(3,3)), ((3,3),(3,4)),
        ((3,1),(4,1)), ((3,2),(4,2)), ((3,3),(4,3)), ((3,4),(4,4)),
        ((4,1),(4,2)), ((4,2),(4,3)), ((4,3),(4,4))
    ]

def edge_index_mapping():
    """Visszaad egy dict-et: index (1-alapú) -> él tuple.
    Segítség debughoz vagy pálya szerkesztőhöz.
    """
    edges = base_beginner_edges()
    return {i+1: e for i, e in enumerate(edges)}

def save_beginner_level(level:int, placed_cheese:list, cheese_imgs:list):
    """Beginner mód adott szintjének mentése JSON formátumban.
    Formátum: {"pieces": [{"x": int, "y": int, "angle": int, "flip": bool, "img_index": int, "lock": bool}]}.
    img_index: a cheese_imgs listában lévő index (0-alapú), így visszaállítható az eredeti grafika.
    lock: True esetén a darab nem törölhető / nem mozgatható / nem forgatható.
    """
    data = []
    for pc in placed_cheese:
        # Meghatározzuk melyik indexű az adott img
        img_index = 0
        for idx, im in enumerate(cheese_imgs):
            if im == pc['img']:
                img_index = idx
                break
        data.append({
            'x': pc['rect'].x,
            'y': pc['rect'].y,
            'angle': pc.get('angle', 0),
            'flip': pc.get('flip', False),
            'img_index': img_index,
            'lock': pc.get('lock', False)
        })
    path = os.path.join(SAVE_DIR, f"beginner_level_{level}.json")
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'pieces': data}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[SAVE ERROR] {e}")

def load_beginner_level(level:int, cheese_imgs:list):
    """Betölti a beginner szint elmentett állapotát, ha létezik.
    Ha nem létezik, üres listát ad vissza.
    lock mező támogatott (alapértelmezés False).
    """
    path = os.path.join(SAVE_DIR, f"beginner_level_{level}.json")
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        pieces = []
        for entry in raw.get('pieces', []):
            idx = entry.get('img_index', 0)
            if 0 <= idx < len(cheese_imgs):
                base_img = cheese_imgs[idx]
            else:
                base_img = cheese_imgs[0] if cheese_imgs else None
            if base_img is None:
                continue
            angle = entry.get('angle', 0)
            flip = entry.get('flip', False)
            # Rekonstruáljuk a megjelenített rect-et a forgatás és flip után is ugyanazzal a topleft-tel
            draw_img = base_img
            if flip:
                draw_img = pygame.transform.flip(draw_img, True, False)
            draw_img = pygame.transform.rotate(draw_img, angle)
            rect = draw_img.get_rect(topleft=(entry.get('x',0), entry.get('y',0)))
            pieces.append({'img': base_img, 'rect': rect, 'angle': angle, 'flip': flip, 'lock': entry.get('lock', False)})
        return pieces
    except Exception as e:
        print(f"[LOAD ERROR] {e}")
        return []

def expert_mode():
    menu_music.stop()
    # Pálya paraméterek
    grid_size = 4  # 4x4-es rács
    cell_size = 80
    cheese_rows, cheese_cols = 1, 2  # Sajtlap méret: 1 sor magas, 2 oszlop széles
    # Tábla jobbra tolva, de nem teljesen a szélre
    grid_origin = (350, screen_height//2 - (grid_size*cell_size)//2)
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
    cheese_flips = []   # horizontális tükrözés állapota
    num_cheese = 7
    cheese_oversize = -2  # nagyon picivel kisebb csak
    cheese_start_y_offset = 100
    for i in range(1, num_cheese + 1):
        img = pygame.image.load(f"assets/images/cheese/SAJTLAP{i}.png").convert_alpha()
        img = pygame.transform.smoothscale(
            img,
            (cheese_cols*cell_size + cheese_oversize, cheese_rows*cell_size + cheese_oversize)
        )
        cheese_imgs.append(img)
        # A bal oldali készletben egymás alatt
        cheese_rects.append(img.get_rect(topleft=(30, 100 + (i-1)*70 - cheese_oversize//2)))
        cheese_angles.append(0)
        cheese_flips.append(False)
    dragging_idx = None  # Bal oldali sajtlap indexe, ha azt húzzuk
    dragging_placed_idx = None  # Pályán lévő sajtlap indexe, ha azt húzzuk
    offset = (0, 0)

    # placed_cheese: list of dict: {img, rect, angle}
    placed_cheese = []

    def piece_cells(rect, angle):
        """Visszaadja a sajtlap által elfoglalt rács cellákat (row,col), 1-alapú index. angle dönti el 2x1 vagy 1x2."""
        rel_x = rect.x - grid_origin[0]
        rel_y = rect.y - grid_origin[1]
        col = rel_x // cell_size + 1
        row = rel_y // cell_size + 1
        if angle % 180 == 0:
            return {(row, col), (row, col+1)}
        else:
            return {(row, col), (row+1, col)}

    def build_occupied(exclude_idx=None):
        occ = set()
        for idx, pc in enumerate(placed_cheese):
            if exclude_idx is not None and idx == exclude_idx:
                continue
            occ |= piece_cells(pc['rect'], pc['angle'])
        return occ

    while True:
        PLAY_MOUSE_POS = pygame.mouse.get_pos()
        # Háttér kirajzolása minden frame-ben
        screen.fill("black")
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
        mouse_img = pygame.transform.smoothscale(mouse_img, (40, 40))
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
            base_img = pc['img']
            if pc.get('flip', False):
                base_img = pygame.transform.flip(base_img, True, False)
            draw_img = pygame.transform.rotate(base_img, pc['angle'])
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
            base_img = img
            if cheese_flips[i]:
                base_img = pygame.transform.flip(base_img, True, False)
            draw_img = pygame.transform.rotate(base_img, cheese_angles[i])
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
                # Jobb egérgomb: forgatás (inventory vagy pályán collision ellenőrzéssel)
                if event.button == 3:
                    rotated_inventory = False
                    for i, rect in enumerate(cheese_rects):
                        if rect.collidepoint(event.pos):
                            cheese_angles[i] = (cheese_angles[i] - 90) % 360
                            rotated_inventory = True
                            break
                    if not rotated_inventory:
                        for idx, pc in enumerate(placed_cheese):
                            if pc['rect'].collidepoint(event.pos):
                                old_angle = pc['angle']
                                pc['angle'] = (pc['angle'] - 90) % 360
                                occ = build_occupied(exclude_idx=idx)
                                cells = piece_cells(pc['rect'], pc['angle'])
                                if any(r < 1 or c < 1 or r > grid_size or c > grid_size for (r,c) in cells) or cells & occ:
                                    pc['angle'] = old_angle
                                break
                # Középső egérgomb (button 2): tükrözés
                if event.button == 2:
                    flipped = False
                    for i, rect in enumerate(cheese_rects):
                        if rect.collidepoint(event.pos):
                            cheese_flips[i] = not cheese_flips[i]
                            flipped = True
                            break
                    if not flipped:
                        for pc in placed_cheese:
                            if pc['rect'].collidepoint(event.pos):
                                pc['flip'] = not pc.get('flip', False)
                                break
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:
                    pos = pygame.mouse.get_pos()
                    flipped = False
                    for i, rect in enumerate(cheese_rects):
                        if rect.collidepoint(pos):
                            cheese_flips[i] = not cheese_flips[i]
                            flipped = True
                            break
                    if not flipped:
                        for pc in placed_cheese:
                            if pc['rect'].collidepoint(pos):
                                pc['flip'] = not pc.get('flip', False)
                                break
            if event.type == pygame.MOUSEBUTTONUP:
                # Bal oldali sajtlap húzás vége
                if dragging_idx is not None:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    img = cheese_imgs[dragging_idx]
                    angle = cheese_angles[dragging_idx]
                    if angle % 180 == 0:
                        w, h = cheese_cols, cheese_rows
                    else:
                        w, h = cheese_rows, cheese_cols
                    grid_x = (mouse_x - grid_origin[0]) // cell_size
                    grid_y = (mouse_y - grid_origin[1]) // cell_size
                    if 0 <= grid_x <= grid_size - w and 0 <= grid_y <= grid_size - h:
                        snap_x = grid_origin[0] + grid_x * cell_size
                        snap_y = grid_origin[1] + grid_y * cell_size
                        draw_img = pygame.transform.rotate(img, angle)
                        new_rect = draw_img.get_rect(topleft=(snap_x, snap_y))
                        cells = piece_cells(new_rect, angle)
                        occ = build_occupied()
                        if not (cells & occ) and all(1 <= r <= grid_size and 1 <= c <= grid_size for (r,c) in cells):
                            placed_cheese.append({'img': img, 'rect': new_rect.copy(), 'angle': angle, 'flip': cheese_flips[dragging_idx]})
                    cheese_rects[dragging_idx].topleft = (30, 100 + dragging_idx*70)
                    dragging_idx = None
                # Pályán lévő sajtlap húzás vége
                if dragging_placed_idx is not None:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    pc = placed_cheese[dragging_placed_idx]
                    img = pc['img']
                    angle = pc['angle']
                    if angle % 180 == 0:
                        w, h = cheese_cols, cheese_rows
                    else:
                        w, h = cheese_rows, cheese_cols
                    grid_x = (mouse_x - grid_origin[0]) // cell_size
                    grid_y = (mouse_y - grid_origin[1]) // cell_size
                    if 0 <= grid_x <= grid_size - w and 0 <= grid_y <= grid_size - h:
                        snap_x = grid_origin[0] + grid_x * cell_size
                        snap_y = grid_origin[1] + grid_y * cell_size
                        draw_img = pygame.transform.rotate(img, angle)
                        new_rect = draw_img.get_rect(topleft=(snap_x, snap_y))
                        cells = piece_cells(new_rect, angle)
                        occ = build_occupied(exclude_idx=dragging_placed_idx)
                        if not (cells & occ) and all(1 <= r <= grid_size and 1 <= c <= grid_size for (r,c) in cells):
                            placed_cheese[dragging_placed_idx]['rect'] = new_rect.copy()
                        else:
                            # marad az eredeti helyén
                            pass
                    else:
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

def main_menu():
    # Főmenü: Start Beginner, Start Expert, Quit
    if not pygame.mixer.get_busy():
        menu_music.play(-1)
    while True:
        screen.blit(background, (0,0))
        mouse_pos = pygame.mouse.get_pos()
        title = get_font(80).render("BRAIN CHEESER", True, "#ffcc00")
        screen.blit(title, title.get_rect(center=(screen_width/2, 120)))
        beginner_btn = Button(image=pygame.image.load("assets/images/play_BG.png"), pos=(screen_width/2, 300), text_input="BEGINNER", font=get_font(50), base_color="#ffcc00", hovering_color="white")
        expert_btn   = Button(image=pygame.image.load("assets/images/play_BG.png"), pos=(screen_width/2, 400), text_input="EXPERT", font=get_font(50), base_color="#ffcc00", hovering_color="white")
        quit_btn     = Button(image=pygame.image.load("assets/images/quit_BG.png"), pos=(screen_width/2, 500), text_input="QUIT", font=get_font(50), base_color="#ffcc00", hovering_color="red")
        for b in (beginner_btn, expert_btn, quit_btn):
            b.changeColor(mouse_pos); b.update(screen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if beginner_btn.checkForInput(mouse_pos):
                    beginner_levels_menu()
                if expert_btn.checkForInput(mouse_pos):
                    expert_mode()
                if quit_btn.checkForInput(mouse_pos):
                    pygame.quit(); sys.exit()
        pygame.display.update()

if __name__ == '__main__':
    main_menu()