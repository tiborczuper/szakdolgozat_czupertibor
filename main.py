import pygame, sys
from button import Button

pygame.init()

screen_width = 1024
screen_height = 720
screen = pygame.display.set_mode((screen_width, screen_height))

pygame.display.set_caption("Brain Cheeser")

background = pygame.image.load("assets/images/cheese_BG.jpeg")
menu_music = pygame.mixer.Sound("assets/sound/menu_music.mp3")

def get_font(size): # Returns Press-Start-2P in the desired size
    return pygame.font.Font("../szakdolgozat_czupertibor/assets/font.ttf", size)

def play():
    menu_music.stop()
    while True:
        PLAY_MOUSE_POS = pygame.mouse.get_pos()

        screen.fill("black")

        PLAY_TEXT = get_font(20).render("Ez a játékos kijelző.", True, "#ffcc00")
        PLAY_RECT = PLAY_TEXT.get_rect(center=(screen_width/2, 260))
        screen.blit(PLAY_TEXT, PLAY_RECT)

        PLAY_BACK = Button(image=None, pos=(screen_width/2, 460),
                            text_input="BACK", font=get_font(75), base_color="#ffcc00", hovering_color="white")

        PLAY_BACK.changeColor(PLAY_MOUSE_POS)
        PLAY_BACK.update(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if PLAY_BACK.checkForInput(PLAY_MOUSE_POS):
                    main_menu()

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

def main_menu():
    menu_music.play()
    while True:
        screen.blit(background, (0, 0))

        MENU_MOUSE_POS = pygame.mouse.get_pos()

        MENU_TEXT = get_font(50).render("Brain cheeser", True, "#ffcc00")
        MENU_RECT = MENU_TEXT.get_rect(center=(screen_width/2, 45))

        PLAY_BUTTON = Button(image=pygame.image.load("assets/images/play_BG.png"), pos=(512, 250),
                             text_input="PLAY", font=get_font(75), base_color="#ffcc00", hovering_color="White")
        OPTIONS_BUTTON = Button(image=pygame.image.load("assets/images/options_BG.png"), pos=(512, 400),
                                text_input="OPTIONS", font=get_font(75), base_color="#ffcc00", hovering_color="White")
        QUIT_BUTTON = Button(image=pygame.image.load("assets/images/quit_BG.png"), pos=(512, 550),
                             text_input="QUIT", font=get_font(75), base_color="#ffcc00", hovering_color="White")

        screen.blit(MENU_TEXT, MENU_RECT)

        for button in [PLAY_BUTTON, OPTIONS_BUTTON, QUIT_BUTTON]:
            button.changeColor(MENU_MOUSE_POS)
            button.update(screen)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if PLAY_BUTTON.checkForInput(MENU_MOUSE_POS):
                    play()
                if OPTIONS_BUTTON.checkForInput(MENU_MOUSE_POS):
                    options()
                if QUIT_BUTTON.checkForInput(MENU_MOUSE_POS):
                    pygame.quit()
                    sys.exit()

        pygame.display.update()

if __name__ == '__main__':
    main_menu()