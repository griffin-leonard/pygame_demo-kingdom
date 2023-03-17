# Author: Griffin Leonard
# Created: 11/6/22

import json
import pygame

def save_json(name, data):
    ''' Save data json. Returns nothing '''
    with open(name+'.txt','w') as file:
        json.dump(data,file)

def load_json(name):
    ''' Load json and return datastructure '''
    with open(name+'.txt') as file:
        data = json.load(file)
        return data

def load_image(name):
    ''' Load pygame Image from png and scale 
    Name must end in .png '''
    return pygame.image.load(name).convert_alpha()

def zoom_scale(zoom, pos):
    ''' Scale an object's position by the current screen zoom.
    args:
        zoom - scale factor, current zoom of screen
        pos - tuple (x, y), pixel position on screen
    Returns scaled x and y values as a tuple (x,y) '''
    from main import SCREEN_WIDTH, GROUND_Y
    if zoom >= 1: return (pos[0] +(SCREEN_WIDTH//2 -pos[0])*(1 -1/2**(zoom-1)), pos[1] +(GROUND_Y -pos[1])*(1 -1/2**(zoom-1)))
    else: return (pos[0] +(SCREEN_WIDTH//2 -pos[0])*(1 -2**abs(zoom-1)), pos[1] +(GROUND_Y -pos[1])*(1 -2**abs(zoom-1)))
    # TODO: fix scaling when zoom <1

def zoom_transform(surf_size, pos):
    ''' Center position of object on new screen size (does not scale object)
    args:
        surf_size - tuple (width, height), size of surface (in pixels) used for drawing (before scaling to normal screen size)
        pos - tuple (x, y), pixel position on screen
    Returns scaled x and y values as a tuple (x,y) '''
    from main import SCREEN_HEIGHT, SCREEN_WIDTH
    return (surf_size[0]//2 +(pos[0] -SCREEN_WIDTH//2), surf_size[1]*3//4 +(pos[1] -SCREEN_HEIGHT*3//4))

def flip_img(img, axis=0):
    ''' axis - x=0, y=1, x&y=2 '''
    if axis == 0: return pygame.transform.flip(img,1,0)
    elif axis == 1: return pygame.transform.flip(img,0,1)
    return pygame.transform.flip(img,1,1)   