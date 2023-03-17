# Author: Griffin Leonard
# Created: 11/6/22

import random
import numpy
import pygame
import utility
import obj

# for world generation
WORLD_SIZE = 1200 # number of chunks
OCEAN_CHUNKS = WORLD_SIZE//3 # islands and icebergs don't count toward this number 
POLE_SIZE = WORLD_SIZE//2//6 # number of chunks for each pole (artic and antartic)
CONTINENT_VAR = (WORLD_SIZE-OCEAN_CHUNKS)//50 # number of chunks by which the size of each continent can vary
OCEAN_VAR = OCEAN_CHUNKS//10 # number of chunks by which the size of each ocean can vary
REGION_TO_CONTINENTS = {'pole': 'antartica',
            'northwest': ('north_america', 'europe'), 
            'northeast': ('europe', 'asia'),
            'southwest': ('south_america', 'africa'),
            'southeast': ('africa', 'india')} 
CONTINENTS = {'antartica': 'pole',
            'north_america': ('north','west'),  # continents must be in west to east order
            'europe': ('north', 'west', 'east'),# supports adding more continent choices
            'asia': ('north', 'east'),
            'south_america': ('south', 'west'),
            'africa': ('south', 'west', 'east'),
            'india': ('south', 'east')}
OCEANS = {'pole': 'artic',
        'northwest': 'atlantic', 
        'northeast': 'indian',
        'southwest': 'pacific',
        'southeast': 'antartic'} 

# for chunk generation
SMALL_ANIMALS_PER_CHUNK = 2
ANIMAL_PROB = .2
STARTING_CAMP_SIZE = 2 # number of chunks
OAK_TREE_PROB = .4
ROCK_PROB = .1

# for object creation
LIGHT_SOURCES = ['campfire']
HAS_INV = ['cave_entrance','log_cabin']
STRUCT_INVENTORY_SIZE = 10
CLOUDS_PER_CHUNK = 2
CLOUD_PROB = .4
ITEM_TO_TAGS = {'axe':['item','wood'], 'hammer':['item','build']}
ITEM_ID_TO_VARIANTS = { # maps object to number of variants (for getting images and creating objects)
                        'cloud':3, 'grass':2, 'rock':2, 'person':2, 'spruce_tree':3}


def get_var(var):
    ''' get random variance (for generating world) '''
    return random.randint(-var//2,var//2)

def generate_world():
    ''' Generates a new game world.
    Specifies sizes for continents and oceans 
    and calls helper functions to generate the biomes and chunk data.
    Returns a dict {chunk_number : {<chunk data>}} mapping chunk number (int) to a dict 
    containing biome and object data for that chunk. 
    Keys for each chunk:
            biome - string, biome from BIOMES
            tiles, trees, grass, rocks - list of strings (png name for each tile); len = TILES_PER_CHUNK  (DEFAULT: [''*TILES_PER_CHUNK])
            animals, structures, people, items - list of tuples ('name', x_pos) representing objects (DEFAULT: [])
    '''
    chunk_data = {}

    # assign number of chunks for each OCEAN 
    global ocean_sizes
    ocean_sizes = {OCEANS['pole']: POLE_SIZE +get_var(OCEAN_VAR)}
    ocean_chunks = OCEAN_CHUNKS//2 -ocean_sizes[OCEANS['pole']]//2 # for a each hemisphere
    # western OCEANS
    ocean_sizes[OCEANS['southwest']] = ocean_chunks//2 +get_var(OCEAN_VAR) # south
    ocean_sizes[OCEANS['northwest']] = ocean_chunks -ocean_sizes[OCEANS['southwest']] # north
    # eastern OCEANS
    ocean_sizes[OCEANS['southeast']] = ocean_chunks//2 +get_var(OCEAN_VAR) # south
    ocean_sizes[OCEANS['northeast']] = ocean_chunks -ocean_sizes[OCEANS['southeast']] # north

    # assign number of chunks for each CONTINENT
    global continent_sizes
    continent_sizes = {REGION_TO_CONTINENTS['pole']: POLE_SIZE +get_var(CONTINENT_VAR)}
    land_chunks = WORLD_SIZE//2 -ocean_chunks -continent_sizes[REGION_TO_CONTINENTS['pole']]//2 # for a each hemisphere
    # nothern CONTINENTS
    north_continents = [c for c in CONTINENTS.keys() if 'north' in CONTINENTS[c]]
    north_continents.pop(random.randint(0,len(north_continents)-1))
    continent_sizes[north_continents[0]] = land_chunks//4 +get_var(CONTINENT_VAR) # west 
    continent_sizes[north_continents[-1]] = land_chunks//4 +get_var(CONTINENT_VAR) # east 
    # southern CONTINENTS
    south_continents = [c for c in CONTINENTS.keys() if 'south' in CONTINENTS[c]]
    south_continents.pop(random.randint(0,len(south_continents)-1))
    continent_sizes[south_continents[0]] = land_chunks//2 -continent_sizes[north_continents[0]] # west
    continent_sizes[south_continents[-1]] = land_chunks//2 -continent_sizes[north_continents[-1]] # east
    
    # generate starting continent
    for c in continent_sizes.keys():
        if 'north' in CONTINENTS[c] and 'west' in CONTINENTS[c]:
            chunk_data = generate_continent(c)
    
    return chunk_data

def generate_ocean(ocean):
    ''' Generates chunks for a new ocean
    Gets correct bounds for chunk range of ocean being generated, then calls generate_chunk
    possible oceans:
            artic, atlantic, pacific, indian, antartic 
    Returns chunk_data 
    Specifies a biome for each chunk and uses generate_chunk to generate object data. 
    Returns a dict {chunk_number : {<chunk data>}} mapping chunk number (int) to a dict 
    containing biome and object data for that chunk. 
    Keys for each chunk:
            biome - string, biome from BIOMES
            tiles, trees, grass, rocks - list of strings (png name for each tile); len = TILES_PER_CHUNK  (DEFAULT: [''*TILES_PER_CHUNK])
            animals, structures, people, items - list of tuples ('name', x_pos) representing objects (DEFAULT: [])
        '''
    # get correct bounds for chunk range being generated
    # noth pole
    if ocean == OCEANS['pole']:
        lower = WORLD_SIZE//4 -ocean_sizes[OCEANS['pole']]//2
        upper = WORLD_SIZE//4 +ocean_sizes[OCEANS['pole']]//2
    # north
    elif ocean == OCEANS['northwest']:
        for continent in continent_sizes.keys():
            if 'north' in CONTINENTS[continent] and 'west' in CONTINENTS[continent]:
                continent_size = continent_sizes[continent]
        lower = WORLD_SIZE//4 -ocean_sizes[OCEANS['pole']]//2 -continent_size -ocean_sizes[OCEANS['northwest']]
        upper = WORLD_SIZE//4 -ocean_sizes[OCEANS['pole']]//2 -continent_size
    elif ocean == OCEANS['northeast']:
        for continent in continent_sizes.keys():
            if 'north' in CONTINENTS[continent] and 'east' in CONTINENTS[continent]:
                continent_size = continent_sizes[continent]
        lower = WORLD_SIZE//4 +ocean_sizes[OCEANS['pole']]//2 +continent_size 
        upper = WORLD_SIZE//4 +ocean_sizes[OCEANS['pole']]//2 -continent_size +ocean_sizes[OCEANS['northeast']]
        if upper >= WORLD_SIZE//2: upper -= WORLD_SIZE # ocean passes eastern equator
    # south
    elif ocean == OCEANS['southwest']:
        lower = -WORLD_SIZE//4 +continent_sizes[REGION_TO_CONTINENTS['pole']]//2 
        upper = -WORLD_SIZE//4 +continent_sizes[REGION_TO_CONTINENTS['pole']]//2 +ocean_sizes[OCEANS[OCEANS['southwest']]]//2 
    elif ocean == OCEANS['southeast']:
        lower = -WORLD_SIZE//4 -continent_sizes[REGION_TO_CONTINENTS['pole']]//2 -ocean_sizes[OCEANS[OCEANS['southeast']]]//2 
        upper = -WORLD_SIZE//4 -continent_sizes[REGION_TO_CONTINENTS['pole']]//2  

    # generate chunks
    if lower < upper:
        return {i: {
            'biome':'ocean', # initialize chunks as empty ocean
            'trees':[], 'grass':[], 'rocks':[], 
            'animals':[], 'structures':[]} 
            for i in range(lower, upper)} 
    else: raise NotImplementedError #TODO

def generate_continent(continent):
    ''' Generates chunks for a new continent
    Gets correct bounds for chunk range of continent being generated, selects biomes, then calls generate_chunk
    possible continents:
        north_america, europe, asia, south_america, africa, india, antartica 
        Returns chunk_data 
    Specifies a biome for each chunk and uses generate_chunk to generate object data. 
    Returns a dict {chunk_number : {<chunk data>}} mapping chunk number (int) to a dict 
    containing biome and object data for that chunk. 
    Keys for each chunk:
            biome - string, biome from BIOMES
            tiles, trees, grass, rocks - list of strings (png name for each tile); len = TILES_PER_CHUNK  (DEFAULT: [''*TILES_PER_CHUNK])
            animals, structures, people, items - list of tuples ('name', x_pos) representing objects (DEFAULT: [])
        '''
    # get correct bounds for chunk range being generated
    # south pole
    if continent == REGION_TO_CONTINENTS['pole']:
        lower = -WORLD_SIZE//4 -continent_sizes[REGION_TO_CONTINENTS['pole']]//2
        upper = -WORLD_SIZE//4 +continent_sizes[REGION_TO_CONTINENTS['pole']]//2
    # north
    elif 'north' in CONTINENTS[continent]:
        if 'west' in CONTINENTS[continent]:
            lower = WORLD_SIZE//4 -ocean_sizes[OCEANS['pole']]//2 -continent_sizes[continent]
            upper = WORLD_SIZE//4 -ocean_sizes[OCEANS['pole']]//2 
        elif 'east' in CONTINENTS[continent]:
            lower = WORLD_SIZE//4 +ocean_sizes[OCEANS['pole']]//2
            upper = WORLD_SIZE//4 +ocean_sizes[OCEANS['pole']]//2 +continent_sizes[continent] 
    # south
    elif 'south' in CONTINENTS[continent]:
        if 'west' in CONTINENTS[continent]:
            lower = -WORLD_SIZE//4 +continent_sizes[REGION_TO_CONTINENTS['pole']]//2 +ocean_sizes[OCEANS['southwest']] 
            upper = -WORLD_SIZE//4 +continent_sizes[REGION_TO_CONTINENTS['pole']]//2 +ocean_sizes[OCEANS['southwest']] +continent_sizes[continent]
        elif 'east' in CONTINENTS[continent]:
            lower = -WORLD_SIZE//4 -continent_sizes[REGION_TO_CONTINENTS['pole']]//2 -ocean_sizes[OCEANS['southeast']] -continent_sizes[continent]
            upper = -WORLD_SIZE//4 -continent_sizes[REGION_TO_CONTINENTS['pole']]//2 -ocean_sizes[OCEANS['southeast']] 
            if lower < -WORLD_SIZE//2: lower += WORLD_SIZE # if continent passes eastern equator

    # select biomes and generate chunks
    chunk_data = {}    
    if lower < upper:
        for chunk in range(lower,upper):
            if chunk in range(upper -(upper-lower)//2 -STARTING_CAMP_SIZE//2, upper -(upper-lower)//2 +STARTING_CAMP_SIZE//2):
                world = generate_chunk(chunk, 'camp')
            else:
                world = generate_chunk(chunk, 'forest')
            chunk_data[chunk] = world
    else: raise NotImplementedError #TODO
    return chunk_data

def generate_chunk(chunk_num, biome):
    ''' generates 1 chunk (16 tiles) for a particular biome. 
    Returns a dict containing data for one newly generated chunk of a particular biome
    Keys for each chunk:
            biome - str, chunk's biome (used for generation, weather, etc.)
            tiles, trees, grass, rocks - list of strings (png name for each tile); len = TILES_PER_CHUNK  (DEFAULT: [''*TILES_PER_CHUNK])
            animals, structures, people, items - list of tuples ('name', x_pos) representing objects (DEFAULT: [])
'''
    from main import TILES_PER_CHUNK, PIXELS_PER_TILE, CHUNK_SIZE
    chunk = {'biome':biome}
    tiles, grass, trees, rocks = [], [], [], [] # str (png name) for each tile
    animals, structures, people, items = [], [], [], [] # tup ('name', x_pos) for each object

    if biome == 'camp':
        for i in range(TILES_PER_CHUNK):
            #tiles
            tiles.append('dirt')
            # grass
            if i not in (0,1,2,13,14,15):
                grass_type = random.randint(0,ITEM_ID_TO_VARIANTS['grass']-1)
                grass.append(f'grass{grass_type}')
            else: grass.append('')
            # trees
            trees.append('')
            # rocks
            if random.random() < ROCK_PROB//2:
                rock_type = random.randint(0,ITEM_ID_TO_VARIANTS['rock']-1)
                rocks.append(f'rock{rock_type}')
            else: rocks.append('')

        # only for one chunk of staring camp
        for c,size in continent_sizes.items():
            if 'north' in CONTINENTS[c] and 'west' in CONTINENTS[c]: continent_size = size 
        if chunk_num == WORLD_SIZE//4 -ocean_sizes['artic']//2 -continent_size//2:
            # structures
            structures.append(('cave_entrance', chunk_num*CHUNK_SIZE))
            structures.append(('campfire', chunk_num*CHUNK_SIZE))
            # people
            people.append(('person0', chunk_num*CHUNK_SIZE -100))
            #items
            items.append(('hammer',chunk_num*CHUNK_SIZE +50))

    elif biome == 'forest':
        for i in range(TILES_PER_CHUNK):
            #tiles
            tiles.append('dirt')
            # grass
            grass.append('')
            # trees
            if i%2 == 0 and random.random() < OAK_TREE_PROB:
                tree_type = random.randint(0,ITEM_ID_TO_VARIANTS['spruce_tree']-1)
                trees.append(f'spruce_tree{tree_type}')
            else: trees.append('')
            # rocks
            if random.random() < ROCK_PROB:
                rock_type = random.randint(0,ITEM_ID_TO_VARIANTS['rock']-1)
                rocks.append(f'rock{rock_type}')
            else: rocks.append('')
        # animals
        for i in range(SMALL_ANIMALS_PER_CHUNK):
            if random.random() < ANIMAL_PROB:
                pixel = random.randint(i*TILES_PER_CHUNK//SMALL_ANIMALS_PER_CHUNK*PIXELS_PER_TILE, (i+1)*TILES_PER_CHUNK//SMALL_ANIMALS_PER_CHUNK*PIXELS_PER_TILE)
                animals.append(('bunny', chunk_num*TILES_PER_CHUNK*PIXELS_PER_TILE +numpy.sign(chunk_num)*pixel))
    
    chunk.update({'tiles':tiles,'trees':trees,'grass':grass,'rocks':rocks,
        'animals':animals,'structures':structures,'people':people,'items':items})
    return chunk

def create_item(item_id, x, path='img/item/', obj_class='object'):
    ''' create a new item (Item for held item or Object for inventory item)
    possible obj_class (class to use when creating objet): 'item', 'object' '''
    from main import ANIMATION_DATABASE, GROUND_Y, FILENAME_TO_IMGS
    
    # default y position is resting on ground
    w, h = ANIMATION_DATABASE[item_id]
    
    # set y position 
    y = GROUND_Y-h 
    if 'rock' in item_id:
        y = GROUND_Y -h//2

    # randomize variante (if item has variants)
    try: item_str = item_id+str(random.randint(0,ITEM_ID_TO_VARIANTS[item_id]-1)) 
    except: item_str = item_id

    # if image has not already been loaded and saved, load it
    if item_str not in FILENAME_TO_IMGS.keys(): FILENAME_TO_IMGS[item_str] = utility.load_image(path+item_str+'.png')
    img = FILENAME_TO_IMGS[item_str]

    if random.random() < .5: img = utility.flip_img(img) # randomize facing direction

    # create object
    try: tags = ITEM_TO_TAGS[item_id]
    except: tags = ['item']
    if obj_class == 'item':
        sheet = utility.load_image(f'img/item/{item_id}_sheet.png')
        return obj.Item(x, y, w, h, img, sheet, ANIMATION_DATABASE[f'{item_id}_sheet'], id=item_id, tags=tags)
    return obj.Object(x, y, w, h, img, id=item_id, tags=tags)

def create_structure(name, x, inventory={}, built=1):
    ''' create a new Structure object
    args:
        name - string, filename for Structure image
        x - x value of the CENTER of the the Structure
    returns Structure object'''
    from main import ANIMATION_DATABASE, GROUND_Y, FILENAME_TO_IMGS
    if name not in FILENAME_TO_IMGS.keys():
        FILENAME_TO_IMGS[name] = utility.load_image(f'img/structure/{name}.png')
    img = FILENAME_TO_IMGS[name]
    w, h = ANIMATION_DATABASE[name]
    tags = []
    if name in LIGHT_SOURCES: 
        tags.append('light')
        structure = obj.Structure(x -w//2, GROUND_Y -h, w, h, img, animated=True, frames=5, \
            tags=tags, built=built)
    elif name in HAS_INV: 
        structure = obj.Structure(x -w//2, GROUND_Y -h, w, h, img, \
            tags=tags, inventory=inventory, inventory_space=STRUCT_INVENTORY_SIZE, built=built)
    else: structure = obj.Structure(x -w//2, GROUND_Y -h, w, h, img, tags=tags)
    return structure

def create_objects(chunk_data, scroll):
    ''' Creates objects from chunk data.
    Returns 5 lists of objects (background objects, interactable background objects, 
    playable objects, foreground objects, and interactable foreground objects) '''
    from main import ANIMATION_DATABASE, CHUNK_SIZE, RENDER_DISTANCE, TILE_SIZE, SCREEN_HEIGHT, PIXEL_SIZE, FILENAME_TO_IMGS
    bg_objs = [] # not interactable (e.g., cloud), drawn before people, in background
    interactable_bg_objs = [] # interactiable objects (e.g., trees), drawn before people, in background
    fg_objs = [] # not interactable (e.g., grass), drawn after people, in foreground
    interactable_fg_objs = [] # interactiable objects (e.g., rocks), drawn after people, in foreground
    playable_objs = [] # Person objects (people)
    curr_chunk = scroll//CHUNK_SIZE # covert scroll (pixels) to chunk number
    chunk_range = range(curr_chunk-RENDER_DISTANCE//2, curr_chunk+RENDER_DISTANCE//2 +1)

    for chunk in chunk_range:
    # background (not interactable)
        # clouds
        for i in range(CLOUDS_PER_CHUNK):
            if random.random() < CLOUD_PROB:
                pixel = random.randint(i*CHUNK_SIZE, (i+1)*CHUNK_SIZE)
                cloud_type = random.randint(0,2)
                cloud = f'cloud{cloud_type}'
                if cloud not in FILENAME_TO_IMGS.keys():
                    FILENAME_TO_IMGS[cloud] = utility.load_image(f'img/envir/{cloud}.png')
                cloud_height = random.randint(TILE_SIZE,SCREEN_HEIGHT//2)
                w, h = ANIMATION_DATABASE['cloud']
                if random.random() < .5:
                    cloud = obj.Object(chunk*CHUNK_SIZE +pixel -w//2, \
                        cloud_height, w, h, FILENAME_TO_IMGS[cloud], tags=['cloud'])
                else:
                    cloud = obj.Object(chunk*CHUNK_SIZE +pixel -w//2, \
                        cloud_height, w, h, utility.flip_img(FILENAME_TO_IMGS[cloud]), tags=['cloud'])
                bg_objs.append(cloud)
        
    # interactable background
        # structures
        for tup in chunk_data[chunk]['structures']:
            struct,x = tup
            interactable_bg_objs.append(create_structure(struct,x))
        # trees
        w, h = ANIMATION_DATABASE['spruce_tree']
        for tile,plant in enumerate(chunk_data[chunk]['trees']):
            if plant: 
                if plant not in FILENAME_TO_IMGS.keys():
                    FILENAME_TO_IMGS[plant] = utility.load_image(f'img/envir/flora/{plant}.png')
                if random.random() < .5:
                    tree = obj.Object(chunk*CHUNK_SIZE +tile*TILE_SIZE +TILE_SIZE//2 -w//2, \
                        SCREEN_HEIGHT*3/4 -h, w, h, FILENAME_TO_IMGS[plant], loot=['log'], tags=['wood'])
                else:
                    tree = obj.Object(chunk*CHUNK_SIZE +tile*TILE_SIZE +TILE_SIZE//2 -w//2, \
                        SCREEN_HEIGHT*3/4 -h, w, h, utility.flip_img(FILENAME_TO_IMGS[plant]), loot=['log'], tags=['wood'])
                interactable_bg_objs.append(tree)

    # people
        w, h = ANIMATION_DATABASE['person'] # 36x80 pixels
        for tup in chunk_data[chunk]['people']:
            img_name, x = tup
            img = utility.load_image(f'img/char/{img_name}.png')
            person = obj.Person(x, SCREEN_HEIGHT*3/4 - h, w, h, img, facing='left')
            playable_objs.append(person)

    # foreground (not interactable)
        # grass
        w, h = ANIMATION_DATABASE['grass']
        for tile,g in enumerate(chunk_data[chunk]['grass']):
            if g: 
                if g not in FILENAME_TO_IMGS.keys():
                    FILENAME_TO_IMGS[g] = utility.load_image(f'img/envir/{g}.png')
                if random.random() < .5:
                    grass = obj.Object(chunk*CHUNK_SIZE +tile*TILE_SIZE, \
                        SCREEN_HEIGHT*3/4 -h +PIXEL_SIZE//2, w, h, FILENAME_TO_IMGS[g])
                else:
                    grass = obj.Object(chunk*CHUNK_SIZE +tile*TILE_SIZE, \
                        SCREEN_HEIGHT*3/4 -h +PIXEL_SIZE//2, w, h, utility.flip_img(FILENAME_TO_IMGS[g]))
                fg_objs.append(grass)

    # interactable foreground 
        # animals
        for tup in chunk_data[chunk]['animals']:
            animal,x = tup
            img = utility.load_image(f'img/envir/fauna/{animal}.png')
            w, h = ANIMATION_DATABASE[animal]
            if random.random() < .5:
                animal = obj.Animal(x -w//2, SCREEN_HEIGHT*3//4 -h, w, h, img, tags=['fearful'])
            else:
                animal = obj.Animal(x -w//2, SCREEN_HEIGHT*3//4 -h, w, h, img, facing='left', tags=['fearful'])
            interactable_fg_objs.append(animal)
        # items
        for tup in chunk_data[chunk]['items']:
            img_name, x = tup
            interactable_fg_objs.append(create_item(img_name, x, obj_class='item'))
        # rocks
        w, h = ANIMATION_DATABASE['rock']
        for tile,r in enumerate(chunk_data[chunk]['rocks']):
            if r: 
                if r not in FILENAME_TO_IMGS.keys():
                    FILENAME_TO_IMGS[r] = utility.load_image(f'img/envir/{r}.png')
                img = FILENAME_TO_IMGS[r] 
                if random.random() < .5: img = utility.flip_img(img)
                rock = obj.Object(chunk*CHUNK_SIZE +tile*TILE_SIZE +TILE_SIZE//2 -w//2, \
                    SCREEN_HEIGHT*3/4 -h/2, w, h, img, id='rock', tags=['item'])
                interactable_fg_objs.append(rock)
    
    # fill inventory in DEBUG mode
    from main import DEBUG
    if DEBUG:
        wood = utility.load_image('img/item/log.png')
        for i in range(2):
            w, h = ANIMATION_DATABASE['rock']
            rock = create_item('rock', 0, path='img/envir/')
            person.pick_up(rock) 
            w, h = ANIMATION_DATABASE['log'] 
            person.pick_up(obj.Object(0, 0, w, h, wood, id='log', tags=['item']))
        person.inventory.update({})
    
    return bg_objs, interactable_bg_objs, playable_objs, fg_objs, interactable_fg_objs

