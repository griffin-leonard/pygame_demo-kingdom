# Author: Griffin Leonard
# Created: 11/6/22

#1 IMPORTS
import pygame
import sys
import obj 
import generate
import utility
import math

#2 SETUP
# clock and time
pygame.init()
clock = pygame.time.Clock()
FPS = 60
SECONDS_PER_DAY = 300
FRAMES_PER_DAY = FPS*SECONDS_PER_DAY

# window
MAX_ZOOM = 2 # scale facor
MIN_ZOOM = 0.5 # scale facor
ASPECT_RATIO = 9/16
screen_info = pygame.display.Info()
window_size = (screen_info.current_w, round(screen_info.current_w*ASPECT_RATIO)) # 16:9 aspect ratio
SCREEN_WIDTH, SCREEN_HEIGHT = window_size[0], window_size[1]
screen = pygame.display.set_mode(window_size, flags=pygame.SCALED, vsync=1)
pygame.display.set_caption('kingdom') 

# sizing
GROUND_Y = SCREEN_HEIGHT*3//4 # should be 3/4 from top of screen
PIXEL_SIZE = 4 # in-game "pixel" size, measured in pixels (chunkiness of art)
SPRITESHEET_SPACING = 8 # in pixels
PIXELS_PER_TILE = 8
TILE_SIZE = PIXELS_PER_TILE*PIXEL_SIZE # in pixels
TILES_PER_CHUNK = 16 # in tiles
CHUNK_SIZE = TILES_PER_CHUNK*TILE_SIZE # in pixels
DEF_STRUCTURE_SIZE = CHUNK_SIZE//4 # in pixels
RENDER_DISTANCE = math.ceil(SCREEN_WIDTH/MIN_ZOOM/CHUNK_SIZE) # in chunks
CLAMP_WIDTH = TILE_SIZE*5 # for clamping scroll when playing as a Person

# databases
CRAFTING_RECIPES = { # maps product to recipe {material: quantity}
    'hammer': {'log':1, 'rock':2}, 'axe': {'log':1, 'rock':2}} 
STRUCTURE_RECIPES = { # maps structure names to recipe {material: quantity}
    'log_cabin': {'log':1}}
ANIMATION_DATABASE = { # maps object names to [width, height] of object (currently set up for TILE_SIZE = 32)
    "person": [36, 80], "spruce_tree": [128, 512], "grass":[32,8], "axe": [30, 18],
    "axe_sheet": [56,80], "hammer": [24,20], "hammer_sheet": [56,80], "campfire": [72, 78], 
    "cave_entrance": [320,320], "log": [60, 24], "rock": [16, 16], "bunny": [32, 32], "sun": [256, 256], 
    "cloud": [384, 192], "selector": [16,20], "moon":[204,204], "log_cabin": [288,192], "berry_bush": [64,64]}

# lighting
MAX_DARKNESS = 20 # darkest the screen will get at night
DEF_LIGHT_SCALE = 8 # size of lighted area relative to light source size
LIGHT_MASK = utility.load_image('img/envir/light_mask.png') # for objects which light up the night

# HUD
HUD_spacing = PIXEL_SIZE*4 # spacing between HUD elements 
HUD_y = GROUND_Y +TILE_SIZE # y position of the top of the HUD 
HUD_x = TILE_SIZE//2 # x position of the right of the HUD (where health and hunger are displayed)
HUD_x_spacing = TILE_SIZE*3 # spacing between different parts of UI
INV_x = HUD_x_spacing +HUD_spacing # x position of the inventory UI
CRAFTING_x = HUD_x +HUD_x_spacing*2 # x position of the crafting UI 
STRUCT_INV_x = HUD_x +HUD_x_spacing*3 # x position of Structure inventory UI
ITEM_BORDER = PIXEL_SIZE*2 # inventory item border pixels beyond TILE_SIZE 
INV_FONT = pygame.font.Font(None, 24)
INV_FONT_C = (115,115,115)
# create inventory item images (by scaling to TILE_SIZE)
ITEM_ID_TO_HUD_IMG = {} # item id/structure name to HUD-scaled image
ITEMS = ['log', 'rock', 'axe', 'hammer'] # items that need an inventory image
for item in ITEMS:
    # scale larger dimension of item image to TILE_SIZE 
    item_img = utility.load_image(f'img/item/{item}.png')
    inv_img = pygame.Surface((TILE_SIZE,TILE_SIZE), pygame.SRCALPHA)
    w, h = ANIMATION_DATABASE[item]
    if w > h: # width larger
        scale_factor = TILE_SIZE/w
        scaled_img = pygame.transform.scale(item_img, (TILE_SIZE, int(h*scale_factor)))
        inv_img.blit(scaled_img, (0, TILE_SIZE//2 -int(h*scale_factor)//2)) 
    else: # height larger
        scale_factor = TILE_SIZE/h
        scaled_img = pygame.transform.scale(item_img, (int(w*scale_factor), TILE_SIZE))
        inv_img.blit(scaled_img, (TILE_SIZE//2 -int(w*scale_factor)//2, 0))
    ITEM_ID_TO_HUD_IMG[item] = inv_img
for struct in STRUCTURE_RECIPES.keys():
    # scale larger dimension of structure image to TILE_SIZE 
    struct_img = utility.load_image(f'img/structure/{struct}.png')
    inv_img = pygame.Surface((TILE_SIZE,TILE_SIZE), pygame.SRCALPHA)
    w, h = ANIMATION_DATABASE[struct]
    if w > h: # width larger
        scale_factor = TILE_SIZE/w
        scaled_img = pygame.transform.scale(struct_img, (TILE_SIZE, int(h*scale_factor)))
        inv_img.blit(scaled_img, (0, TILE_SIZE//2 -int(h*scale_factor)//2)) 
    else: # height larger
        scale_factor = TILE_SIZE/h
        scaled_img = pygame.transform.scale(struct_img, (int(w*scale_factor), TILE_SIZE))
        inv_img.blit(scaled_img, (TILE_SIZE//2 -int(w*scale_factor)//2, 0))
    ITEM_ID_TO_HUD_IMG[struct] = inv_img
# for HUD health and hunger
HEALTH_IMG = utility.load_image('img/hud/health.png')
HUNGER_IMG = utility.load_image('img/hud/hunger.png')

# scale border size for inventory items
INV_BORDER_IMG = utility.load_image('img/hud/inv_border.png')
INV_BORDER_SELECTED_IMG = utility.load_image('img/hud/inv_border_selected.png')
if INV_BORDER_IMG.get_size() != (TILE_SIZE+ITEM_BORDER, TILE_SIZE+ITEM_BORDER): # scale images (if necessary, set up for 32px TILE_SIZE and 8px ITEM_BORDER)
    INV_BORDER_IMG = pygame.transform.scale(INV_BORDER_IMG, (TILE_SIZE+ITEM_BORDER, TILE_SIZE+ITEM_BORDER))
    INV_BORDER_SELECTED_IMG = pygame.transform.scale(INV_BORDER_SELECTED_IMG, (TILE_SIZE+ITEM_BORDER, TILE_SIZE+ITEM_BORDER))

# misc
DEBUG = False
PARALAX_FACTOR = .8
TILE_MASK = utility.load_image('img/envir/tiles/tile_mask.png') # gradient, tiles to black
SCAFFOLDING_IMG = utility.load_image('img/structure/scaffolding.png') # for structures in-progress

# helper functions that directly modify key game variables
def update_chunk_data(name,x,data_list,add=True): 
    ''' * currently only supports adding Structures, Animals, People, and Items * '''
    global chunk_data
    if add:
        if data_list in ['animals', 'structures', 'people', 'items']:
            chunk_data[int(x//CHUNK_SIZE)][data_list].append((name,int(x))) # update chunk data

def clamp_scroll(player, type='scroll'):
    ''' keeps scroll value within set range
    possible types: scroll, player
    modifies gloable var scroll (necessary when called by obj.py) '''
    global scroll
    if type == 'scroll':
        scroll = player.x - SCREEN_WIDTH//2

    elif type == 'player':
        if player.x > scroll+SCREEN_WIDTH//2 - player.width//2 + CLAMP_WIDTH//2:
            scroll += player.x - (scroll + SCREEN_WIDTH//2 - player.width//2 + CLAMP_WIDTH//2)
        elif player.x < scroll+SCREEN_WIDTH//2 - player.width//2 - CLAMP_WIDTH//2:
            scroll -= scroll + (SCREEN_WIDTH//2 - player.width//2 - CLAMP_WIDTH//2) - player.x

def draw_ground(surf,surf_size):
    ''' uses chunk_data to draw ground tiles '''
    width, height = surf_size
    fg = pygame.Rect(0,height*3//4,width,height//4+1)
    surf.fill((0,0,0),fg) 

    # DRAW TILES
    curr_chunk = int((scroll+SCREEN_WIDTH//2)/CHUNK_SIZE) # covert scroll (pixels) to chunk number
    chunk_range = range(curr_chunk -width//CHUNK_SIZE//2 -2, curr_chunk +width//CHUNK_SIZE//2 +2)
    for chunk in chunk_range:
        for i,tile in enumerate(chunk_data[chunk]['tiles']):
            if tile not in FILENAME_TO_IMGS.keys():
                FILENAME_TO_IMGS[tile] = utility.load_image(f'img/envir/tiles/{tile}.png')
            x, y = utility.zoom_transform(surf_size, (chunk*CHUNK_SIZE +TILE_SIZE*i,GROUND_Y))
            surf.blit(FILENAME_TO_IMGS[tile], (x-scroll, y))
            surf.blit(FILENAME_TO_IMGS[tile], (x-scroll, y+TILE_SIZE))
            surf.blit(TILE_MASK, (x-scroll, y+TILE_SIZE))

def draw_lighting(surf,surf_size):
    ''' handles lighting system for day/night cycle and light source objects '''
    # draw darkness for night 
    night = pygame.Surface(surf_size)
    c = (255-MAX_DARKNESS)/2*math.sin(2*math.pi*time/SECONDS_PER_DAY) +(255+MAX_DARKNESS)/2
    night.fill((c,c,c))
    # draw lighting for light sources
    for obj in interactable_bg_objs+interactable_fg_objs:
        if 'light' in obj.tags:
            light = pygame.transform.scale(LIGHT_MASK, (obj.width*DEF_LIGHT_SCALE, obj.height*DEF_LIGHT_SCALE))
            rect = light.get_rect()
            rect.center = obj.rect.center
            rect.x, rect.y = utility.zoom_transform(surf_size, (rect.x,rect.y))
            rect.x -= scroll
            night.blit(light, rect)
    surf.blit(night, (1-zoom,0), special_flags=pygame.BLEND_MULT)

def draw_level():
    ''' use object list to draw everthing to the screen '''
    surf_size = (int(SCREEN_WIDTH/zoom), int(SCREEN_HEIGHT/zoom))
    surf = pygame.Surface((surf_size[0], surf_size[1]))

    # draw background 
    surf.fill((155,205,240)) 
    # sun.x = int(SCREEN_WIDTH//2 - TILE_SIZE*2) 
    sun.x = time/(SECONDS_PER_DAY/2)*SCREEN_WIDTH
    sun.y = int(GROUND_Y -(SCREEN_HEIGHT+sun.height)*math.sin(2*math.pi*time/SECONDS_PER_DAY))
    x, y = utility.zoom_transform(surf_size, (sun.x,sun.y))
    surf.blit(sun.img, (x, y)) 

    draw_ground(surf,surf_size) # draw ground

    # draw objects
    for o in bg_objs+interactable_bg_objs+playable_objs+fg_objs+interactable_fg_objs: 
        o.draw(surf, scroll, surf_size)
    controller.draw(surf, scroll, surf_size)

    draw_lighting(surf,surf_size) # draw darkness for night 

    if DEBUG:  # TODO: constant sizing for hud when zooming
        # display chunk borders
        for chunk in range(int(controller.x//CHUNK_SIZE -RENDER_DISTANCE), int(controller.x//CHUNK_SIZE +RENDER_DISTANCE+1)):
            text = pygame.font.Font(None, 24).render(str(chunk), True, (0,0,0))
            x, y = utility.zoom_transform(surf_size, (chunk*CHUNK_SIZE -scroll +CHUNK_SIZE//2, 0)) # y unneeded
            surf.blit(text, (x,TILE_SIZE)) # chunk number text
            x, y = utility.zoom_transform(surf_size, (chunk*CHUNK_SIZE -scroll, 0)) # y unneeded
            pygame.draw.line(surf, (0,0,0), (x,0),(x,surf_size[1]))

    # scale screen by zoom factor
    scaled = pygame.transform.scale(surf, (SCREEN_WIDTH, SCREEN_HEIGHT))
    screen.blit(scaled, (0,0))

    # draw HUD
    controller.draw_hud(screen) # handles HUD for all possible states 
    if DEBUG:
        # display mouse position
        pos = pygame.mouse.get_pos()
        pos = utility.zoom_scale(zoom, pos)
        text = pygame.font.Font(None, 24).render(f'mouse pos: ({pos[0]+scroll}, {pos[1]})', True, (0,0,0))
        screen.blit(text, (TILE_SIZE, TILE_SIZE*2))
        # display scroll
        text = pygame.font.Font(None, 24).render(f'scroll: {scroll}', True, (0,0,0))
        screen.blit(text, (TILE_SIZE, TILE_SIZE*3))
        # display zoom
        text = pygame.font.Font(None, 24).render(f'zoom: {zoom}', True, (0,0,0))
        screen.blit(text, (TILE_SIZE, TILE_SIZE*4))
        if controller.player != None:
            # display stamina
            text = pygame.font.Font(None, 24).render(f'stamina: {round(controller.player.stamina,1)}', True, (0,0,0))
            screen.blit(text, (TILE_SIZE, TILE_SIZE*5))

#3 CREATE/LOAD WORLD
try:
    # LOAD WORLD
    utility.load_json('save')
    scroll = 0 # in pixels
    day = 0
    start_time = 0 # in seconds, resets each day
    zoom = 1
    chunk_data = {}

except:
    # GENERATE NEW WORLD
    chunk_data = generate.generate_world()
    # print(generate.continent_sizes)
    # print(generate.ocean_sizes)
    # print('total chunks',sum(generate.continent_sizes.values())+sum(generate.ocean_sizes.values()))

    # set scroll to starting camp location
    for c,size in generate.continent_sizes.items():
        if 'north' in generate.CONTINENTS[c] and 'west' in generate.CONTINENTS[c]: continent_size = size 
    scroll = (generate.WORLD_SIZE//4 -generate.ocean_sizes['artic']//2 -continent_size//2) *CHUNK_SIZE # in pixels
    day = 0
    start_time = 0 # in seconds, resets each day
    zoom = 1

#4 CREATE OBJECTS
# create sun
sun = utility.load_image('img/envir/sun.png')
w, h = sun.get_size()
sun = obj.Object(0, 0, w, h, sun)

# create world objects
FILENAME_TO_IMGS = {}
bg_objs, interactable_bg_objs, playable_objs, fg_objs, interactable_fg_objs = generate.create_objects(chunk_data, scroll)

#5 GAME     
controller = obj.Controller(scroll)
while 1:
    # update time
    clock.tick(FPS)
    time = pygame.time.get_ticks()/1000%SECONDS_PER_DAY +start_time
    day = pygame.time.get_ticks()/1000//SECONDS_PER_DAY
    for event in pygame.event.get(): 
        # toggle debug mode
        if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB: DEBUG = not DEBUG

    # update objects
    zoom = controller.update(playable_objs, interactable_fg_objs+interactable_bg_objs, scroll, zoom)
    data = {}
    for o in interactable_fg_objs:
        if type(o) == obj.Animal: # update Animals
            o.update()
    for p in playable_objs: # update Persons
        data.update(p.update(interactable_bg_objs, interactable_fg_objs))
    
    # create and destroy new objects as needed
    if data:
        for o in data['destroy']:  #TODO
            try: interactable_bg_objs.remove(o)
            except: interactable_fg_objs.remove(o)
        for l in data['create']: 
            o, layer = l
            if layer == 'bg': interactable_bg_objs.append(o)
            elif layer == 'fg': interactable_fg_objs.append(o)
            else: playable_objs.append(o)     

    # draw world
    draw_level()

    # quit
    if pygame.event.get(pygame.QUIT):
        pygame.quit()
        sys.exit()

    pygame.display.update() # Update screen 