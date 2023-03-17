# Author: Griffin Leonard
# Created: 11/6/22

import pygame 
import math
import random
import numpy
import utility

DEF_FRAMES = 1 # default number of animation frames
DEF_ANIMATION_TIME_SCALE = .1 # default time scale of animations
DEF_HEALTH = 100 # default Object health
MAX_CLICK_SPEED = 15 # in frames, minimum time between registering clicks when interacting with UI
DEF_BUILD_TIME = 60 # in frames, time it takes to build a structure

class Controller(object):
    def __init__(self, scroll):
        ''' class for handle inputs when NOT playing as a specific character 
        states: scroll, player  '''
        from main import PIXEL_SIZE
        self.ZOOM_SPEED = 1.02
        self.PLAYER_ZOOM = 1.25
        self.scroll_speed = PIXEL_SIZE*2
        self.speed = self.scroll_speed
        self.x = scroll
        self.state = 'scroll'
        self.player = None # Person object player is controlling. (is set to None when not playing as particular person)        

        # for selections and selector animation
        self.selection = None
        self.sprite_sheet = utility.load_image('img/hud/selector.png')
        from main import ANIMATION_DATABASE
        self.width, self.height = ANIMATION_DATABASE['selector']
        self.frames = 6
        self.frame_num = 0
        self.animation_time_scale = .1
    
    def update(self, playable_objs, interactable_objs, scroll, zoom):
        ''' Returns new zoom value (for screen) '''
        if self.player != None and self.player.state != 'player':
            # set state back
            self.state = 'scroll'
            self.x = self.player.x
            self.player = None
        
        if self.state == 'player': 
            # if a player is being controlled
            return self.PLAYER_ZOOM

        # HANDLE MOUSE INPUTS
        mouse = pygame.mouse.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        mouse_pos = utility.zoom_scale(zoom, mouse_pos)
        if mouse[2]:
            # play as specific Person (right click)
            for obj in playable_objs:
                if mouse_pos[0]+scroll >= obj.x and mouse_pos[0]+scroll < obj.x + obj.width \
                    and mouse_pos[1] >= obj.y and mouse_pos[1] < obj.y + obj.height:
                    if type(obj) == Person:
                        if self.selection != None: self.deselect()
                        self.play_as(obj)
                        return self.PLAYER_ZOOM
        if mouse[0]:
            # select an object (left click)
            for obj in interactable_objs+playable_objs:
                if mouse_pos[0]+scroll >= obj.x and mouse_pos[0]+scroll < obj.x + obj.width \
                    and mouse_pos[1] >= obj.y and mouse_pos[1] < obj.y + obj.height:
                    if type(obj) == Person:
                        self.select(obj)
                        return zoom
                    # do an action with selected person
                    if self.selection != None and type(self.selection) == Person:
                        if (type(obj) == Item and self.selection.item == None) or \
                            ('item' in obj.tags and len(self.selection.inventory) < self.selection.inventory_space):
                            self.selection.task = 'pick_up'
                            self.selection.pursue(obj)
                            self.deselect()

        # HANDLE KEYBOARD INPUTS
        pressed = pygame.key.get_pressed()
        # exit selection
        if self.selection != None and pressed[pygame.K_ESCAPE]:
            self.deselect()

        # horizontal movement
        if pressed[pygame.K_a]:
            self.x -= self.speed
            if pressed[pygame.K_LSHIFT]:
                self.x -= self.speed
        if pressed[pygame.K_d]:
            self.x += self.speed
            if pressed[pygame.K_LSHIFT]:
                self.x += self.speed

        # zoom
        if pressed[pygame.K_w]:
            from main import MIN_ZOOM
            if zoom*(2-self.ZOOM_SPEED) > MIN_ZOOM: zoom *= (2-self.ZOOM_SPEED)
            else: zoom = MIN_ZOOM
        if pressed[pygame.K_s]:
            from main import MAX_ZOOM
            if zoom*self.ZOOM_SPEED < MAX_ZOOM: zoom *= self.ZOOM_SPEED
            else: zoom = MAX_ZOOM

        from main import clamp_scroll
        clamp_scroll(self) # set scroll to controller location
        return zoom # update zoom
    
    def deselect(self):
        self.selection.selected = False
        self.selection = None

    def select(self, obj):
        self.selection = obj
        self.selection.selected = True

    def play_as(self, obj):
        obj.state = 'player'
        self.state = 'player'
        self.player = obj

    def draw(self, surface, scroll, surf_size):
        if self.selection != None:
            self.update_frame()
            x, y = utility.zoom_transform(surf_size, (self.selection.x, self.selection.y))
            surface.blit(self.img, (x + self.selection.width//2 -self.width//2 -scroll, y - self.height))
        
    def draw_hud(self, surface):
        if self.selection != None or self.state == 'player':
            if self.state == 'player': self.player.draw_hud(surface) # playing as person
            else: self.selection.draw_hud(surface) # person is selected

    def update_frame(self):
        from main import SPRITESHEET_SPACING
        if math.ceil(self.frame_num) >= self.frames:
            self.frame_num = 0
        self.img = self.sprite_sheet.subsurface((math.ceil(self.frame_num)*(self.width+SPRITESHEET_SPACING),0,self.width,self.height))
        self.frame_num += self.animation_time_scale


class Object(object):
    ''' Basic object class
    Possible tags: 
        item (held items and inventory items)
        wood (made of/can cut wood)
        build (held item that can build structures)
        cloud (for cloud movement)
        fearful (animals that run from people)
    id attribute is for items which can be in a person's inventory '''
    def __init__(self,x,y,x_size,y_size,img, id='', health=DEF_HEALTH, loot=[], tags=[]):
        self.width = x_size
        self.height = y_size
        self.rect = pygame.Rect(x,y,self.width,self.height)
        #position of top left corner
        self.x = x 
        self.y = y
        self.img = img
        self.tags = tags
        self.max_health = health
        self.health = self.max_health
        self.loot = loot # list of item ids to be created as loot
        self.id = id

    def draw(self, surface, scroll, surf_size):
        x, y = utility.zoom_transform(surf_size, (self.x, self.y))
        if 'cloud' in self.tags:
            from main import FPS, PARALAX_FACTOR
            surface.blit(self.img, (x - scroll*PARALAX_FACTOR +pygame.time.get_ticks()//FPS, y))
        else:
            surface.blit(self.img, (x - scroll, y))

    def damage(self,strength=1):
        ''' returns objects to be destroyed/created '''
        data = {'create':[], 'destroy':[]}
        if self.health -strength <= 0: data = self.die()
        else: self.health -= strength
        return data

    def die(self):
        data = {'destroy': [self],'create': []} 
        # drop loot and die 
        for loot in self.loot:
            from generate import create_item
            data['create'].append((create_item(loot, self.x +self.width//2), 'bg')) 
        return data 


class Entity(Object):
    ''' Objects that are animated '''
    def __init__(self,x,y,x_size,y_size, sprite_sheet, id='', health=DEF_HEALTH, loot=[], tags=[], \
        animated=False, speed='DEF', state='idle',facing='right',\
        frames=DEF_FRAMES,animation_time_scale=DEF_ANIMATION_TIME_SCALE):
        super().__init__(x,y,x_size,y_size, sprite_sheet, id=id, health=health, loot=loot, tags=tags)
        if speed == 'DEF':
            from main import PIXEL_SIZE
            self.speed = PIXEL_SIZE*.75
        else: self.speed = speed

        self.sprite_sheet = sprite_sheet
        self.frames = frames
        self.frame_num = 0
        self.animation_time_scale = animation_time_scale
        self.facing = facing
        self.animated = animated
        self.state = state
        self.update_frame()

    def draw(self, surface, scroll, surf_size):
        self.update_frame()
        x, y = utility.zoom_transform(surf_size, (self.x, self.y))
        surface.blit(self.img, (x - scroll, y))
    
    def update_frame(self):
        from main import SPRITESHEET_SPACING
        if not self.animated or math.ceil(self.frame_num) >= self.frames:
            self.frame_num = 0
        self.img = self.sprite_sheet.subsurface((math.ceil(self.frame_num)*(self.width+SPRITESHEET_SPACING),0,self.width,self.height))
        self.frame_num += self.animation_time_scale
        if self.facing == 'left':
            self.img = pygame.transform.flip(self.img,1,0)


class Item(Entity):
    ''' Equipable item '''
    def __init__(self,x,y,x_size,y_size, ground_img, sprite_sheet, held_item_size, \
        id='', tags=[], on_ground=True, facing='right',frames=DEF_FRAMES,animation_time_scale=DEF_ANIMATION_TIME_SCALE):
        super().__init__(x,y,x_size,y_size, sprite_sheet, \
            id=id, tags=tags, facing=facing,frames=frames,animation_time_scale=animation_time_scale)
        self.on_ground = on_ground
        self.ground_img = ground_img
        self.held_item_size = held_item_size

    def draw(self, surface, scroll, surf_size):
        if self.on_ground:
            x, y = utility.zoom_transform(surf_size, (self.x, self.y))
            if self.facing == 'right': surface.blit(self.ground_img, (x - scroll, y))
            else: surface.blit(utility.flip_img(self.ground_img), (x - scroll, y))


class Animal(Entity):
    ''' Animal with various behaviors 
    possible tags: fearful
    possible states: idle, wander, flee
    '''
    def __init__(self,x,y,x_size,y_size, sprite_sheet, \
        tags=[], loot=[], speed='DEF', state='wander',facing='right',frames=DEF_FRAMES,animation_time_scale=DEF_ANIMATION_TIME_SCALE, health=DEF_HEALTH):
        super().__init__(x,y,x_size,y_size, sprite_sheet, health=health, loot=loot, tags=tags, \
            speed=speed, state=state, facing=facing, frames=frames,animation_time_scale=animation_time_scale)
        self.wander_time = 120
        self.wander_num = 0 
        self.flee_obj = None

    def update(self):
        if self.state == 'wander': self.wander()
        elif self.state == 'flee': 
            self.flee()

    def wander(self):
        # try to initiate wander
        if not self.animated:
            from main import FPS
            if pygame.time.get_ticks()%FPS == 0 and random.random() < .05:
                self.animated = True
                if random.random() < .5: self.facing = 'right'
                else: self.facing = 'left'

        # while actively wandering
        if self.animated:
            self.wander_num += random.randint(1,2)
            if self.wander_num >= self.wander_time: self.set_state('wander')
            if self.facing == 'right': self.x += self.speed
            else: self.x -= self.speed
            self.rect.x = self.x

    def set_state(self, state, obj=None):
        self.state = state
        if self.state == 'wander':
            self.wander_num = 0 
            self.animated = False
            self.flee_obj = None
        elif self.state == 'flee':
            self.flee_obj = obj
            self.animated = True

    def flee(self):
        direction = numpy.sign(self.flee_obj.x +self.flee_obj.width//2 - (self.x +self.width//2)) # direction of flee object relative to self
        # update direction for sprite
        if direction > 0: self.facing = 'left'
        else: self.facing = 'right'
        self.x -= direction*self.speed # run away!

        if abs(self.flee_obj.x +self.flee_obj.width//2 - (self.x +self.width//2)) > self.flee_obj.startle_dis: 
            # got away!
            from main import FPS
            if random.random() < (1-self.flee_obj.startle_prob)/FPS: self.set_state('wander')


class Person(Entity):
    ''' Basic playable character 
    possible states: player, idle, pursue, task
    possible tasks: pick_up, collect '''
    def __init__(self,x,y,x_size,y_size, sprite_sheet, \
        speed='DEF', state='idle',facing='right',frames=6,animation_time_scale=DEF_ANIMATION_TIME_SCALE, health=DEF_HEALTH):
        from main import PIXEL_SIZE, TILE_SIZE, FPS, FRAMES_PER_DAY
        # set speed (pixels per frame)
        if speed == 'DEF':
            from main import PIXEL_SIZE
            self.speed = PIXEL_SIZE*0.5
            self.run_speed = self.speed*2
        else: 
            self.speed = speed
            self.run_speed = self.speed*2
        self.def_animation_time_scale = animation_time_scale
        self.max_stamina = 20*FPS # frames of running
        self.stamina = self.max_stamina
        self.stamina_regen = {'idle': .5, 'walk': .2} # stamina regained each frame for various states
        self.max_hunger = FRAMES_PER_DAY*3 # frames before dying of hunger
        self.hunger = 0 # how hungry the Person is. Person dies at self.max_hunger frames
        self.health = health
        self.click_time = 0 # time left before next click is registered (for UI)

        self.selected = False # bool, True if person is currently selected by the controller
        self.task = None
        self.item = None
        self.inventory = {} # maps item ids to quantity
        self.inventory_space = 5
        self.recipes = {} # maps item ids to dict of materials needed
        self.dropped = False # whether an item has been dropped with the Q key
        self.struct = None # Structure to display inventory for
        self.valid_structures = {} # maps structure which are possible to build at the current x location to dict of materials needed
            
        super().__init__(x,y,x_size,y_size, sprite_sheet, \
            state=state, facing=facing, frames=frames,animation_time_scale=animation_time_scale)
        self.pursue_obj = None
        self.startle_dis = TILE_SIZE*10 # distance at which animals will notice person and flee (if fearful)
        self.startle_prob = .8 # probability animal is startled

    def update(self, interactable_bg_objs, interactable_fg_objs):
        ''' called every frame by main game loop
        returns objects to be destroyed/created or an empty dict '''
        data = {'destroy': [], 'create': []}
        
        # UPDATE STATS (e.g., health, hunger, stamina)
        if self.hunger < self.max_hunger: self.hunger += 1 # get more hungry (if still alive)
        else:  
            from main import FPS
            self.health -= (self.hunger-self.max_hunger-1)/FPS # decrease health by 1 each second at max hunger (quicker if walking or running)
        if self.health < 0: return self.die() # die if out of health

        if self.stamina > self.max_stamina: self.stamina = self.max_stamina # cap stamina at maximum (so we don't have to elsewhere)

        # ANIMAL INTERACTIONS
        for obj in interactable_fg_objs:
            if type(obj) == Animal and 'fearful' in obj.tags and abs(obj.x-self.x) <= self.startle_dis:
            # make animals flee if startled
                if random.random() < self.startle_prob: obj.set_state('flee', self)

        if self.state == 'pursue': self.pursue()
        elif self.state == 'task': data = self.do_task()
        
        # PLAYING AS PERSON
        elif self.state == 'player':
            pressed = pygame.key.get_pressed()
            if pressed[pygame.K_ESCAPE]:
            # go back to scrolling with Controller
                self.state = 'idle'
                return data

            # MOVEMENT INPUTS
            # moving state, stamina, hunger
            if not (pressed[pygame.K_a] or pressed[pygame.K_d]) \
                or (pressed[pygame.K_a] and pressed[pygame.K_d]):
                # idle
                self.animated = False
                self.stamina += self.stamina_regen['idle']
            else: 
                # moving
                self.animated = True
                self.hunger += 1 # hungry faster when walking
            # movement
            if pressed[pygame.K_a]:
                # run 
                if pressed[pygame.K_LSHIFT] and self.stamina -1 > 0:
                    # run
                    self.x -= self.run_speed
                    self.animation_time_scale = self.def_animation_time_scale*2
                    if self.animated:
                        self.stamina -= 1
                        self.hunger += 1 # hungry even faster when running
                else:
                    # walk
                    self.x -= self.speed
                    self.animation_time_scale = self.def_animation_time_scale
                if self.facing == 'right' and not pressed[pygame.K_d]: self.facing = 'left' # don't update direction if opposite key is still held
                if self.animated: self.stamina += self.stamina_regen['walk']
            if pressed[pygame.K_d]:
                if pressed[pygame.K_LSHIFT] and self.stamina -1 > 0:
                    # run
                    self.x += self.run_speed
                    self.animation_time_scale = self.def_animation_time_scale*2
                    if self.animated:
                        self.stamina -= 1
                        self.hunger += 1 # hungry even faster when running
                else:
                    # walk
                    self.x += self.speed
                    self.animation_time_scale = self.def_animation_time_scale
                if self.facing == 'left' and not pressed[pygame.K_a]: self.facing = 'right' # don't update direction if opposite key is still held
                if self.animated: self.stamina += self.stamina_regen['walk']
            
            # MOUSE DEPENDENT INPUTS
            mouse = pygame.mouse.get_pressed()
            mouse_x, mouse_y = pygame.mouse.get_pos()

            # update click time
            if self.click_time > 0: self.click_time -= 1 
            if sum(mouse) == 0: self.click_time = 0

            from main import INV_x, TILE_SIZE, ITEM_BORDER, HUD_y, HUD_spacing
            # Crafting UI
            if self.recipes:
                from main import CRAFTING_x
                for i,item_id in enumerate(self.recipes.keys()):
                    if mouse_x > CRAFTING_x and mouse_x < CRAFTING_x +TILE_SIZE +ITEM_BORDER \
                        and mouse_y > HUD_y +TILE_SIZE*(i+1) +HUD_spacing*i \
                        and mouse_y < HUD_y +TILE_SIZE*(i+2) +HUD_spacing*(i+1):
                    # mouse over crafting item
                        if mouse[0] and self.click_time == 0: # left click
                        # craft item
                            data.update(self.craft(item_id, self.recipes[item_id]))
                            break

            # Structure inventory UI
            self.struct = None
            transfered = False
            for obj in interactable_bg_objs:
                if transfered: break
                if type(obj) == Structure and obj.built == 1 and obj.inventory_space != 0 and self.rect.colliderect(obj.rect):
                    self.struct = obj
                    from main import STRUCT_INV_x
                    for i,item_id in enumerate(list(obj.inventory.keys()).copy()):
                        if mouse[0] and self.click_time == 0 \
                            and mouse_x > STRUCT_INV_x and mouse_x < STRUCT_INV_x +TILE_SIZE +ITEM_BORDER \
                            and mouse_y > HUD_y +TILE_SIZE*(i+1) +HUD_spacing*i \
                            and mouse_y < HUD_y +TILE_SIZE*(i+2) +HUD_spacing*(i+1) \
                            and self.get_num_items() < self.inventory_space:
                            # mouse over structure's inventory item AND left click
                            # transfer item to Person inventory
                            self.update_inv(item_id, 1)
                            obj.update_inv(item_id, -1)
                            self.click_time = MAX_CLICK_SPEED
                            transfered = True

            # Inventory UI
            for i,item_id in enumerate(self.inventory.keys()):
                if mouse_x > INV_x and mouse_x < INV_x +TILE_SIZE +ITEM_BORDER \
                    and mouse_y > HUD_y +TILE_SIZE*(i+1) +HUD_spacing*i \
                    and mouse_y < HUD_y +TILE_SIZE*(i+2) +HUD_spacing*(i+1):
                # mouse over inventory item
                    if self.struct != None and self.struct.built == 1 and mouse[0] and self.click_time == 0 \
                        and self.struct.get_num_items() < self.struct.inventory_space: # left click
                    # transfer item to Strutre inventory
                        self.update_inv(item_id, -1)
                        self.struct.update_inv(item_id, 1)
                        self.click_time = MAX_CLICK_SPEED
                        break
                    if mouse[2]: # right click
                    # use item
                        self.click_time = MAX_CLICK_SPEED
                        break
                    elif pressed[pygame.K_q]: 
                        if self.dropped == False:
                        # drop item
                            self.dropped = True
                            data.update(self.drop_inv_item(item_id))
                        self.clamp_scroll()
                        return data # don't drop held item!
                    else:
                        self.dropped = False # Q key is released, a new item can now be dropped

            # Build new structure UI
            if self.item != None and 'build' in self.item.tags:
                self.update_vaild_structures()
                from main import STRUCT_INV_x
                for i,name in enumerate(self.valid_structures.keys()):
                    if mouse_x > STRUCT_INV_x and mouse_x < STRUCT_INV_x +TILE_SIZE +ITEM_BORDER \
                        and mouse_y > HUD_y +TILE_SIZE*(i+1) +HUD_spacing*i \
                        and mouse_y < HUD_y +TILE_SIZE*(i+2) +HUD_spacing*(i+1):
                    # mouse over crafting item
                        if mouse[0] and self.click_time == 0: # left click
                        # create structure
                            data.update(self.create_structure(name, self.valid_structures[name]))
                            break

            # NON-MOVEMENT KEYBOARD INPUTS
            # pick up items
            self.rect.x = self.x # update rect position for collisions!
            if pressed[pygame.K_s]:
                objects = interactable_fg_objs+interactable_bg_objs
                objects.reverse() # reverse to pick up older items first
                for obj in objects: 
                    if self.rect.colliderect(obj.rect):
                        if 'item' in obj.tags:
                            new_data = self.pick_up(obj)
                            data.update(new_data)
                            break

            # use or drop held item
            if self.item != None:
                if pressed[pygame.K_q]:
                    # drop held item
                    self.drop_held_item()
                if pressed[pygame.K_SPACE]:
                    # use held item
                    for obj in interactable_fg_objs+interactable_bg_objs:
                        if self.rect.colliderect(obj.rect):
                        # person is touching an object
                            if type(obj) == Animal:
                                # damage an animal
                                data.update(obj.damage())
                            if 'wood' in obj.tags and 'wood' in self.item.tags:
                                # destroy wood objects with wood-breaking tool (e.g., axe)
                                data.update(obj.damage())
                                break
                            if 'build' in self.item.tags and type(obj) == Structure and obj.built < 1:
                                # build structure with building tool (e.g., hammer)
                                obj.build()
                                break

            self.clamp_scroll()
        return data # objects to be destroyed/created (dict {'destroy': [obj], 'create': [obj]})

    def clamp_scroll(self):
        ''' (for when playing as person)
        clamp the screen scroll and return data.
        used to end self.update '''
        from main import clamp_scroll
        clamp_scroll(self, type='player')

    def pick_up(self, obj):
        if 'item' in obj.tags:
            if type(obj) == Item:
                self.drop_held_item() # drop currently held item
                # pick up new held item
                self.item = obj
                obj.on_ground = False
            elif self.get_num_items() < self.inventory_space:
                # pick up inventory item
                self.update_inv(obj.id,1)
                return {'destroy':[obj],'create':[]}
        return {}

    def drop_held_item(self):
        if self.item != None:
            # drop currently held item
            self.item.on_ground = True
            self.item.facing = self.facing
            if self.facing == 'right': self.item.x = self.x + self.width
            else: self.item.x = self.x - self.item.width
            self.item.rect.x = self.item.x
            self.item = None

    def update_inv(self, item_id, change):
        if change >= 1:
            # add items to inventory
            try: self.inventory[item_id] += change
            except: self.inventory[item_id] = change
        else:
            # take items from iventory
            new_quantity = self.inventory[item_id] +change
            if new_quantity > 0: self.inventory[item_id] = new_quantity
            elif new_quantity == 0: del self.inventory[item_id]
            else: return
        self.recipes = self.get_recipes() # update items which can be crafted

    def drop_inv_item(self, item_id):
        ''' Returns dict with object to be created '''
        self.update_inv(item_id, -1)
        from generate import create_item
        item = create_item(item_id, self.x)
        layer = 'bg'
        if item_id == 'rock': layer = 'fg'
        return {'create':[(item,layer)], 'destroy':[]}

    def pursue(self, obj=None):
        if self.state != 'pursue':
            # initiate a pursuit
            self.state = 'pursue'
            self.pursue_obj = obj
            self.animated = True
        direction = numpy.sign(self.pursue_obj.x +self.pursue_obj.width//2 - (self.x +self.width//2))
        # update direction for sprite
        if direction > 0: self.facing = 'right'
        else: self.facing = 'left'
        self.x += direction*self.speed

        if direction != numpy.sign(self.pursue_obj.x +self.pursue_obj.width//2 - (self.x +self.width//2)):
            # target has been reached
            self.animated = False
            self.state = 'task' # initate intended task

    def do_task(self):
        data = {}
        if self.task == 'pick_up':
            data = self.pick_up(self.pursue_obj)
            self.state = 'idle'
            self.pursue_obj = None
        return data

    def die(self):
        # drop all items and die
        if self.item != None:
            self.drop_held_item()

        from main import TILE_SIZE
        spread_distance = int(len(self.inventory)/self.inventory_space *2*TILE_SIZE) # in pixels, max distance in each direction
        for obj in self.inventory:
            # scatter inventory TODO: creation of objects (since self.inventory was updated to a dict)
            # obj.on_ground = True
            # obj.x = self.x + numpy.random.normal()*random.randint(0, TILE_SIZE*spread_distance) # spread with normal distribution
            # obj.rect.x = obj.x
            # randomize object's facing direction
            # if random.random() < .5: obj.facing = 'right'
            # else: obj.facing = 'left'
            pass
        return {'destroy': [self],'create': []} #TODO: create skull on death

    def get_num_items(self):
        return sum(self.inventory.values())

    def craft(self, product_id, recipe): 
        ''' Returns dict with object to be created '''
        self.click_time = MAX_CLICK_SPEED     
        from generate import create_item
        return {'create':[(create_item(product_id, self.x, obj_class='item'), 'fg')], 'destroy':[]} 

    def create_structure(self, struct_name, recipe):
        ''' Returns dict with object to be created '''
        for item_id,quantity in recipe.items(): self.update_inv(item_id, -quantity)
        self.click_time = MAX_CLICK_SPEED     
        from generate import create_structure
        from main import TILE_SIZE, update_chunk_data
        struct = create_structure(struct_name, self.x -self.x%TILE_SIZE, built=0)
        update_chunk_data(struct_name,struct.x,'structures')
        return {'create':[(struct, 'bg')], 'destroy':[]}

    def get_recipes(self):
        ''' Returns a dict {'product_id': {'material_id': int, ...}, ...} for all
        items which can be crafted given the items currently in the inventory. '''
        from main import CRAFTING_RECIPES
        recipes = {}
        for item, recipe in CRAFTING_RECIPES.items():
            have_materials = True
            for id, num in recipe.items():
                if id not in self.inventory.keys() or self.inventory[id] < num:
                    have_materials = False
            if have_materials:
                recipes[item] = recipe
        return recipes

    def get_buildable_structures(self): 
        ''' Returns a dict {'struct_name': {'material_id': int, ...}, ...} for all
        structures which can be constructed given the items discovered. '''
        from main import STRUCTURE_RECIPES
        recipes = {}
        for struct, recipe in STRUCTURE_RECIPES.items():
            have_materials = True
            for id, num in recipe.items():
                if id not in self.inventory.keys() or self.inventory[id] < num:
                    have_materials = False
            if have_materials:
                recipes[struct] = recipe
        return recipes

    def update_vaild_structures(self):
        ''' update self.valid_structures (dict with repices for structures can be built at the player's location) '''
        self.valid_structures = {}
        from main import chunk_data, CHUNK_SIZE, TILE_SIZE, ANIMATION_DATABASE
        for struct,recipe in self.get_buildable_structures().items():
            valid = True
            for chunk in range(int(self.x//CHUNK_SIZE -1),int(self.x//CHUNK_SIZE +2)):
            # check chunk before and after current location as well
                for tup in chunk_data[chunk]['structures']:
                    if (self.x -self.x%TILE_SIZE +ANIMATION_DATABASE[struct][0]/2 > tup[1] -ANIMATION_DATABASE[tup[0]][0]/2  \
                        and self.x -self.x%TILE_SIZE +ANIMATION_DATABASE[struct][0]/2 < tup[1] +ANIMATION_DATABASE[tup[0]][0]/2) \
                        or (self.x -self.x%TILE_SIZE -ANIMATION_DATABASE[struct][0]/2 < tup[1] +ANIMATION_DATABASE[tup[0]][0]//2 \
                        and self.x -self.x%TILE_SIZE -ANIMATION_DATABASE[struct][0]/2 > tup[1] -ANIMATION_DATABASE[tup[0]][0]/2):
                    # structure is in an invalid location 
                        valid = False
            if valid: self.valid_structures.update({struct: recipe})
        print()

    def draw(self, surface, scroll, surf_size):
        self.update_frame() # update animation
        x, y = utility.zoom_transform(surf_size, (self.x, self.y))
        surface.blit(self.img, (x - scroll, y)) # draw person

        # draw held item
        if self.item != None:
            if self.facing == 'right':
                surface.blit(self.item.img, (x - scroll, y -(self.height - self.item.held_item_size[1])))
            else:
                surface.blit(self.item.img, (x -(self.item.held_item_size[0] -self.width) - scroll, \
                    y -(self.height -self.item.held_item_size[1])))

    def draw_hud(self, surface):
            from main import TILE_SIZE, INV_FONT_C, INV_FONT, PIXEL_SIZE, \
                HUD_x, HUD_y, INV_x, ITEM_BORDER, HUD_spacing, ITEM_ID_TO_HUD_IMG, \
                HEALTH_IMG, HUNGER_IMG, INV_BORDER_IMG, INV_BORDER_SELECTED_IMG

            # GENERAL HUD (displays when playing as or selecting a Person)
            txt_x = HUD_x +TILE_SIZE +PIXEL_SIZE
            # health
            surface.blit(HEALTH_IMG, (HUD_x, HUD_y)) # health image
            text = INV_FONT.render(str(self.health), True, INV_FONT_C)
            surface.blit(text, (txt_x +HUD_spacing//2, HUD_y +TILE_SIZE//2 -1.25*INV_FONT.size(str(round(self.health,0)))[1])) # health text
            pygame.draw.line(surface, INV_FONT_C, (txt_x +HUD_spacing//2, HUD_y +TILE_SIZE//2 -PIXEL_SIZE//2), \
                (txt_x +HUD_spacing//2 +INV_FONT.size(str(self.max_health))[0], HUD_y +TILE_SIZE//2), width=PIXEL_SIZE//2)
            text = INV_FONT.render(str(self.max_health), True, INV_FONT_C)
            surface.blit(text, (txt_x +HUD_spacing//2, HUD_y +TILE_SIZE//2 +.25*INV_FONT.size(str(self.max_health))[1])) # max health text
            # hunger
            surface.blit(HUNGER_IMG, (HUD_x, HUD_y +TILE_SIZE +HUD_spacing)) # hunger image
            hunger = int((self.max_hunger-self.hunger)/self.max_hunger*100)
            text = INV_FONT.render(str(hunger), True, INV_FONT_C)
            surface.blit(text, (txt_x +HUD_spacing//2, HUD_y +1.5*TILE_SIZE +HUD_spacing -1.25*INV_FONT.size(str(hunger))[1])) # hunger text
            pygame.draw.line(surface, INV_FONT_C, (txt_x +HUD_spacing//2, HUD_y +1.5*TILE_SIZE +HUD_spacing -PIXEL_SIZE//2), \
                (txt_x +HUD_spacing//2 +INV_FONT.size('100')[0], HUD_y +1.5*TILE_SIZE +HUD_spacing), width=PIXEL_SIZE//2)
            text = INV_FONT.render('100', True, INV_FONT_C)
            surface.blit(text, (txt_x +HUD_spacing//2, HUD_y +1.5*TILE_SIZE +HUD_spacing +.25*INV_FONT.size('100')[1])) # max hunger text
            # held item
            if self.item != None:
                surface.blit(ITEM_ID_TO_HUD_IMG[self.item.id], (HUD_x, HUD_y +TILE_SIZE*2 +HUD_spacing*2 +ITEM_BORDER//2)) # held item image
                surface.blit(INV_BORDER_IMG, (HUD_x, HUD_y +TILE_SIZE*2 +HUD_spacing*2)) # held item border

            # INVENTORY HUD (displays when playing as or selecting a Person)
            # inventory text
            text = INV_FONT.render('Inventory', True, INV_FONT_C)
            surface.blit(text, (INV_x, HUD_y)) # inventory text
            text = INV_FONT.render(f'{self.get_num_items()}/{self.inventory_space}', True, INV_FONT_C)
            surface.blit(text, (INV_x, HUD_y +TILE_SIZE//2)) # inventory capacity text

            mouse_x, mouse_y = pygame.mouse.get_pos()
            # inventory items
            for i,item_id in enumerate(self.inventory.keys()):
            # draw inventory border, item image, and number (text) for each item
                surface.blit(ITEM_ID_TO_HUD_IMG[item_id], (INV_x +ITEM_BORDER//2, \
                    HUD_y +TILE_SIZE*(i+1) +HUD_spacing*i +PIXEL_SIZE)) # item image
                surface.blit(INV_BORDER_IMG, (INV_x, \
                    HUD_y +TILE_SIZE*(i+1) +HUD_spacing*i)) # border
                text = INV_FONT.render(f'x{self.inventory[item_id]}', True, INV_FONT_C)
                surface.blit(text, (INV_x +TILE_SIZE +ITEM_BORDER, \
                    HUD_y +TILE_SIZE*(i+1.5) +HUD_spacing*i)) # number of items text
                
                if  self.state == 'player' and mouse_x > INV_x and mouse_x < INV_x +TILE_SIZE +ITEM_BORDER \
                    and mouse_y > HUD_y +TILE_SIZE*(i+1) +HUD_spacing*i and mouse_y < HUD_y +TILE_SIZE*(i+2) +HUD_spacing*(i+1):
                # mouse over inventory item
                    surface.blit(INV_BORDER_SELECTED_IMG, (INV_x, HUD_y +TILE_SIZE*(i+1) +HUD_spacing*i)) # selected border
            
            # HUDs that only display when playing as a Person
            if self.state == 'player':
                # CRAFTING HUD
                if self.recipes:
                    from main import CRAFTING_x
                    text = INV_FONT.render('Crafting', True, INV_FONT_C)
                    surface.blit(text, (CRAFTING_x, HUD_y)) # crafting text

                    for i,item_id in enumerate(self.recipes.keys()):
                        surface.blit(ITEM_ID_TO_HUD_IMG[item_id], (CRAFTING_x +ITEM_BORDER//2, \
                            HUD_y +TILE_SIZE*(i+1) +HUD_spacing*i +PIXEL_SIZE)) # item image
                        surface.blit(INV_BORDER_IMG, (CRAFTING_x, 
                            HUD_y +TILE_SIZE*(i+1) +HUD_spacing*i)) # border

                        if mouse_x > CRAFTING_x and mouse_x < CRAFTING_x +TILE_SIZE +ITEM_BORDER \
                            and mouse_y > HUD_y +TILE_SIZE*(i+1) +HUD_spacing*i \
                            and mouse_y < HUD_y +TILE_SIZE*(i+2) +HUD_spacing*(i+1):
                        # mouse over crafting item
                            surface.blit(INV_BORDER_SELECTED_IMG, (CRAFTING_x, \
                                HUD_y +TILE_SIZE*(i+1) +HUD_spacing*i)) # selected border

                # STRUCTURE INVENTORY HUD
                if self.struct != None: self.struct.draw_hud(surface)

                # BUILD STRUCTURE HUD
                if self.item != None and 'build' in self.item.tags and self.valid_structures:
                    from main import STRUCT_INV_x
                    text = INV_FONT.render('Build', True, INV_FONT_C)
                    surface.blit(text, (STRUCT_INV_x, HUD_y)) # Build text

                    for i,struct in enumerate(self.valid_structures.keys()):
                        surface.blit(ITEM_ID_TO_HUD_IMG[struct], (STRUCT_INV_x +ITEM_BORDER//2, \
                            HUD_y +TILE_SIZE*(i+1) +HUD_spacing*i +PIXEL_SIZE)) # item image
                        surface.blit(INV_BORDER_IMG, (STRUCT_INV_x, 
                            HUD_y +TILE_SIZE*(i+1) +HUD_spacing*i)) # border
                        
                        if mouse_x > STRUCT_INV_x and mouse_x < STRUCT_INV_x +TILE_SIZE +ITEM_BORDER \
                            and mouse_y > HUD_y +TILE_SIZE*(i+1) +HUD_spacing*i \
                            and mouse_y < HUD_y +TILE_SIZE*(i+2) +HUD_spacing*(i+1):
                        # mouse over structure image
                            surface.blit(INV_BORDER_SELECTED_IMG, (STRUCT_INV_x, \
                                HUD_y +TILE_SIZE*(i+1) +HUD_spacing*i)) # selected border

    def update_frame(self):
        # update animations for held items too (relevant lines commented)
        if self.item != None:
            from main import SPRITESHEET_SPACING
            if not self.animated or math.ceil(self.frame_num) >= self.frames:
                self.frame_num = 0
            self.img = self.sprite_sheet.subsurface((math.ceil(self.frame_num)*(self.width+SPRITESHEET_SPACING),0,self.width,self.height))
            self.item.img = self.item.sprite_sheet.subsurface((math.ceil(self.frame_num)*(self.item.held_item_size[0]+SPRITESHEET_SPACING),0,self.item.held_item_size[0],self.item.held_item_size[1])) # for held item
            if self.facing == 'left':
                self.img = pygame.transform.flip(self.img,1,0)
                self.item.img = pygame.transform.flip(self.item.img,1,0) # for held item
            self.frame_num += self.animation_time_scale
        else:
            super().update_frame() # if no held item, update animation frames normally


class Structure(Entity):
    ''' Sructures can store items (have inventory) and can be built
    possible tags: light '''
    def __init__(self,x,y,x_size,y_size, sprite_sheet, health=DEF_HEALTH, loot=[], tags=[], \
        animated=False, facing='right', frames=DEF_FRAMES,animation_time_scale=DEF_ANIMATION_TIME_SCALE, \
        inventory_space=0, inventory={}, built=1, build_time=DEF_BUILD_TIME):
        super().__init__(x,y,x_size,y_size, sprite_sheet, health=health, loot=loot, tags=tags, \
            animated=animated, facing=facing, frames=frames,animation_time_scale=animation_time_scale)
        self.inventory = inventory # maps item ids to number of items
        self.inventory_space = inventory_space
        self.built = built # percent of structure that's built
        if self.built != 1:
            from main import SCAFFOLDING_IMG
            self.scaffolding = pygame.transform.scale(SCAFFOLDING_IMG, (self.width, self.height))
        self.build_time = build_time # in frames 

    def get_num_items(self):
        return sum(self.inventory.values())

    def update_inv(self, item_id, change):
        if change >= 1:
            # add items to inventory
            try: self.inventory[item_id] += change
            except: self.inventory[item_id] = change
        else:
            # take items from iventory
            new_quantity = self.inventory[item_id] +change
            if new_quantity > 0: self.inventory[item_id] = new_quantity
            elif new_quantity == 0: del self.inventory[item_id]
            else: return
    
    def build(self, strength=1):
        if self.built < 1: self.built = min(1, self.built +strength/self.build_time)

    def draw(self, surface, scroll, surf_size):
        x, y = utility.zoom_transform(surf_size, (self.x, self.y))
        if self.built == 1: surface.blit(self.img, (x - scroll, y))
        else: surface.blit(self.scaffolding, (x - scroll, y))

    def draw_hud(self, surface):
        if self.built == 1 and self.inventory_space != 0:
            from main import INV_FONT, INV_FONT_C, HUD_y, STRUCT_INV_x, TILE_SIZE, ITEM_BORDER, PIXEL_SIZE, \
                HUD_spacing, ITEM_ID_TO_HUD_IMG, INV_BORDER_IMG, INV_BORDER_SELECTED_IMG
            
            text = INV_FONT.render('Inventory', True, INV_FONT_C)
            surface.blit(text, (STRUCT_INV_x, HUD_y)) # struct inventory text
            text = INV_FONT.render(f'{self.get_num_items()}/{self.inventory_space}', True, INV_FONT_C)
            surface.blit(text, (STRUCT_INV_x, HUD_y +TILE_SIZE//2)) # struct inventory capacity text

            mouse_x, mouse_y = pygame.mouse.get_pos()
            for i,item_id in enumerate(self.inventory.keys()):
                surface.blit(ITEM_ID_TO_HUD_IMG[item_id], (STRUCT_INV_x +ITEM_BORDER//2, \
                    HUD_y +TILE_SIZE*(i+1) +HUD_spacing*i +PIXEL_SIZE)) # item image
                surface.blit(INV_BORDER_IMG, (STRUCT_INV_x, \
                    HUD_y +TILE_SIZE*(i+1) +HUD_spacing*i)) # border
                
                text = INV_FONT.render(f'x{self.inventory[item_id]}', True, INV_FONT_C)
                surface.blit(text, (STRUCT_INV_x +TILE_SIZE +ITEM_BORDER, \
                    HUD_y +TILE_SIZE*(i+1.5) +HUD_spacing*i)) # number of items text


                if mouse_x > STRUCT_INV_x and mouse_x < STRUCT_INV_x +TILE_SIZE +ITEM_BORDER \
                    and mouse_y > HUD_y +TILE_SIZE*(i+1) +HUD_spacing*i \
                    and mouse_y < HUD_y +TILE_SIZE*(i+2) +HUD_spacing*(i+1):
                # mouse over crafting item
                    surface.blit(INV_BORDER_SELECTED_IMG, (STRUCT_INV_x, \
                        HUD_y +TILE_SIZE*(i+1) +HUD_spacing*i)) # selected border


