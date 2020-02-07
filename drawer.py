import pygame
import parameters as p
import math
import numpy as np
import utils

# mainw_width, mainw_height = p.parameters["MAINW_WIDTH"], p.parameters["MAINW_HEIGHT"]
DEBUG = False
DEBUG_SWITCHED = False

def draw_grid(grid, surface, alphasurf):
    global DEBUG_SWITCHED
    global DEBUG
    rdr = False
    for x in range(grid.width):
        for y in range(grid.height):
            t = grid.grid[x][y]

            # if (t.redraw or DEBUG) or DEBUG_SWITCHED:
            #     if DEBUG_SWITCHED and not DEBUG:
            #         DEBUG_SWITCHED = False
            if t.redraw:
                # if t.is_river or any([_t.is_river for _t in grid.get_neighbours_of(t, diag_neigh=True)]):
                #     rdr = True
                pygame.draw.rect(surface, t.get_color(), t.rect, 0)
                pygame.draw.rect(alphasurf, (0,0,0,0), t.rect, 0)
                # if t.tree != None:
                    # pygame.draw.circle(surface, 
                    #     (139,69,19,255),
                    #     # p.type2color["FOREST"],
                    #     t.middle, 
                    #     min(int(t.rect.w/2)-1, int(t.rect.h/2)-1),
                    #     0)
                for n in grid.get_neighbours_of(t, diag_neigh=True):
                    if not n.entities:
                        pygame.draw.rect(surface, n.get_color(), n.rect, 0)
                        pygame.draw.rect(alphasurf, (0,0,0,0), n.rect, 0)
                    # if n.is_forest:
                    #     # pygame.draw.rect(surface, p.type2color["FOREST"], n.rect, 0)
                    #     if n.tree != None:
                    #         pygame.draw.circle(surface, 
                    #             (139,69,19,255),
                    #             # p.type2color["FOREST"],
                    #             n.middle, 
                    #             min(int(n.rect.w/2)-1, int(n.rect.h/2)-1),
                    #             0)

                t.redraw = False

    # if rdr:
    # for rp in grid.rivers:
    #     pygame.draw.lines(surface, p.type2color["SHALLOW_WATER"], False, [t.middle for t in rp], 4)

def draw_healthbar(value, max_value, topleft, size, surface, c1=(255,0,0,255), c2=(0,255,0,255), min_value=0):
    factor = utils.normalise(value, min_value, max_value)

    pygame.draw.rect(surface, c1, pygame.Rect(topleft, size))
    if int(size[0]*factor) != 0:
        pygame.draw.rect(surface, c2, pygame.Rect(topleft, (int(size[0]*factor), size[1])))


def draw_food(food, surface):
    pygame.draw.circle(surface, 
                        food.color if food.available else (161,40,48,255), 
                        food.tile.middle, 
                        min(int(food.tile.rect.w/2)-1, int(food.tile.rect.h/2)-1),
                        0)

    draw_healthbar(food.resource_qtt, food.resource_max,
                    (food.tile.middle[0] - food.tile.rect.width/2, food.tile.middle[1] + food.tile.rect.height/2),
                    (food.tile.rect.width/2*2 + 1, 2),
                    surface)


def draw_foods(foods, surface):
    for f in foods:
        draw_food(f,surface)

def draw_building(buildings, surface):
    for b in buildings:
        if b.image != None:
            surface.blit(pygame.transform.scale(b.image, b.tile.rect.size), b.tile.rect.topleft)

def draw_entity(entity, surface, selected, alphasurf, draw_hb=False):
    global DEBUG

    pygame.draw.circle(surface, 
                        entity.color, 
                        entity.tile.middle, 
                        min(int(entity.tile.rect.w/2)-1, int(entity.tile.rect.h/2)-1),
                        0)

    if entity == selected or draw_hb:
        draw_healthbar(entity.nutrition, entity.nutrition_max,
                        (entity.tile.middle[0] - entity.tile.rect.width/4 - 1, entity.tile.middle[1] - entity.tile.rect.height/1.5),
                        (entity.tile.rect.width/4*2, 2),
                        surface,
                        c1=(0,0,0,255),
                        c2=(255,0,0,255))

        draw_healthbar(entity.nutrition, entity.nutrition_max,
                        (entity.tile.rect.width/2 + entity.tile.middle[0] - entity.tile.rect.width/4 - 1, entity.tile.middle[1] - entity.tile.rect.height/1.5),
                        (entity.tile.rect.width/4*2, 2),
                        surface,
                        c1=(0,0,0,255),
                        c2=(0,0,255,255))

        draw_healthbar(entity.health, entity.health_max,
                        (entity.tile.middle[0] - entity.tile.rect.width/2, entity.tile.middle[1] - entity.tile.rect.height),
                        (entity.tile.rect.width + 1, 2),
                        surface)

    # for t in entity.grow_food_tile:
    #     pygame.draw.rect(surface, (255,255,255,255), t.rect, 2)
    
    if entity == selected:
        pygame.draw.circle(surface, 
                        (255,255,255,255), 
                        entity.tile.middle, 
                        min(int(entity.tile.rect.w/2)-1, int(entity.tile.rect.h/2)-1),
                        1)
        for t in selected.known_tiles:
            t.redraw = True
            pygame.draw.rect(alphasurf, (255, 255, 255, 64), t.rect, 1)

        for f in selected.friends:
            pygame.draw.line(surface, (0,255,0,255), entity.tile.middle, f.tile.middle, 1)

            #Bottom right
            if entity.tile.middle[0] > f.tile.middle[0] and entity.tile.middle[1] > f.tile.middle[1]:
                r = pygame.Rect(f.tile.middle, ((entity.tile.middle[0]-f.tile.middle[0]), (entity.tile.middle[1]-f.tile.middle[1])))
            #Bottom left
            elif entity.tile.middle[0] <= f.tile.middle[0] and entity.tile.middle[1] > f.tile.middle[1]:
                r = pygame.Rect((entity.tile.middle[0], f.tile.middle[1]), ((f.tile.middle[0]-entity.tile.middle[0]), (entity.tile.middle[1]-f.tile.middle[1])))
            #Top left
            elif entity.tile.middle[0] <= f.tile.middle[0] and entity.tile.middle[1] <= f.tile.middle[1]:
                r = pygame.Rect(entity.tile.middle, ((f.tile.middle[0]-entity.tile.middle[0]), (f.tile.middle[1]-entity.tile.middle[1])))
            #Top right
            elif entity.tile.middle[0] > f.tile.middle[0] and entity.tile.middle[1] <= f.tile.middle[1]:
                r = pygame.Rect((f.tile.middle[0], entity.tile.middle[1]), ((entity.tile.middle[0]-f.tile.middle[0]), (f.tile.middle[1]-entity.tile.middle[1])))
            else:
                r = pygame.Rect((0,0),(0,0))

            list1d=entity.grid.get_tile_1D_list()
            lres = r.collidelistall(list1d)
            for i in lres:
                # print("REDRAW")
                list1d[i].redraw = True

        for f in selected.foes:
            pygame.draw.line(surface, (255,0,0,255), entity.tile.middle, f.tile.middle, 1)

            #Bottom right
            if entity.tile.middle[0] > f.tile.middle[0] and entity.tile.middle[1] > f.tile.middle[1]:
                r = pygame.Rect(f.tile.middle, ((entity.tile.middle[0]-f.tile.middle[0]), (entity.tile.middle[1]-f.tile.middle[1])))
            #Bottom left
            elif entity.tile.middle[0] <= f.tile.middle[0] and entity.tile.middle[1] > f.tile.middle[1]:
                r = pygame.Rect((entity.tile.middle[0], f.tile.middle[1]), ((f.tile.middle[0]-entity.tile.middle[0]), (entity.tile.middle[1]-f.tile.middle[1])))
            #Top left
            elif entity.tile.middle[0] <= f.tile.middle[0] and entity.tile.middle[1] <= f.tile.middle[1]:
                r = pygame.Rect(entity.tile.middle, ((f.tile.middle[0]-entity.tile.middle[0]), (f.tile.middle[1]-entity.tile.middle[1])))
            #Top right
            elif entity.tile.middle[0] > f.tile.middle[0] and entity.tile.middle[1] <= f.tile.middle[1]:
                r = pygame.Rect((f.tile.middle[0], entity.tile.middle[1]), ((entity.tile.middle[0]-f.tile.middle[0]), (f.tile.middle[1]-entity.tile.middle[1])))
            else:
                r = pygame.Rect((0,0),(0,0))

            list1d=entity.grid.get_tile_1D_list()
            lres = r.collidelistall(list1d)
            for i in lres:
                # print("REDRAW")
                list1d[i].redraw = True

    if DEBUG:

        # for f in [x.tile for x in entity.food_memory] + entity.water_memory:
        #     pygame.draw.line(surface, (255,255,255,255), entity.tile.middle, f.middle, 1)

        #     #Bottom right
        #     if entity.tile.middle[0] > f.middle[0] and entity.tile.middle[1] > f.middle[1]:
        #         r = pygame.Rect(f.middle, ((entity.tile.middle[0]-f.middle[0]), (entity.tile.middle[1]-f.middle[1])))
        #     #Bottom left
        #     elif entity.tile.middle[0] <= f.middle[0] and entity.tile.middle[1] > f.middle[1]:
        #         r = pygame.Rect((entity.tile.middle[0], f.middle[1]), ((f.middle[0]-entity.tile.middle[0]), (entity.tile.middle[1]-f.middle[1])))
        #     #Top left
        #     elif entity.tile.middle[0] <= f.middle[0] and entity.tile.middle[1] <= f.middle[1]:
        #         r = pygame.Rect(entity.tile.middle, ((f.middle[0]-entity.tile.middle[0]), (f.middle[1]-entity.tile.middle[1])))
        #     #Top right
        #     elif entity.tile.middle[0] > f.middle[0] and entity.tile.middle[1] <= f.middle[1]:
        #         r = pygame.Rect((f.middle[0], entity.tile.middle[1]), ((entity.tile.middle[0]-f.middle[0]), (f.middle[1]-entity.tile.middle[1])))
        #     else:
        #         r = pygame.Rect((0,0),(0,0))

        #     list1d=entity.grid.get_tile_1D_list()
        #     lres = r.collidelistall(list1d)
        #     for i in lres:
        #         # print("REDRAW")
        #         list1d[i].redraw = True

        # for vt in entity.get_visible_tiles(0):
        #     pygame.draw.circle(surface, (0, 0, 255, 255), vt.middle, 1, 0)
        #     vt.redraw=True

        if entity.path:
            draw_path(entity.tile, entity.path, entity.grid, surface)

def draw_entities(entities, surface, selected, alphasurf):
    for e in entities:
        draw_entity(e, surface, selected, alphasurf)

def draw_path(start, path, grid, surface):
    points = [start.middle]
    for i in range(len(path)):
        _curr = path[i]
        _curr.redraw = True

        points.append(_curr.middle)

    pygame.draw.lines(surface, (64, 64, 64, 255), False, points, 1)

def draw_text(text, font, fontsize, surface, shift, x=10):
    displ_text = font.render(text, True, (0,0,0))
    surface.blit(displ_text, (x, fontsize*1.2 + shift))
    return shift + fontsize*1.2