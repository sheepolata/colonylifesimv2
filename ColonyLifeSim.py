import pygame
from pygame.locals import *
from screeninfo import get_monitors
import os
import numpy as np
import math
import time

import sys

import parameters as p
import environment as env
import drawer
import life
import utils
import console

def main():

    pygame.init()
    monitor = get_monitors()[0]
    clock = pygame.time.Clock()

    screen_width, screen_height = p.parameters["SCREEN_WIDTH"], p.parameters["SCREEN_HEIGHT"]
    main_surface_width, main_surface_height = p.parameters["MAINW_WIDTH"], p.parameters["MAINW_HEIGHT"]
    info_surface_width, info_surface_height = p.parameters["INFO_SURF_WIDTH"], p.parameters["INFO_SURF_HEIGHT"]

    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % ((monitor.width/2)-(screen_width/2),(monitor.height/2)-(screen_height/2))
    
    window = pygame.display.set_mode((screen_width, screen_height))
    # pygame.display.set_mode(caption)
    caption = "Colony Life Simulator V2"
    pygame.display.set_caption(caption)

    main_surface       = pygame.Surface((main_surface_width, main_surface_height))
    main_surface_alpha = pygame.Surface((main_surface_width, main_surface_height), pygame.SRCALPHA)
    # main_surface_alpha.set_alpha(128)
    # main_surface_alpha.fill((255, 255, 255, 0))
    info_surface       = pygame.Surface((info_surface_width, info_surface_height))

    #OBJECTS
    simu = env.Simulation(p.parameters["GRID_W"], p.parameters["GRID_H"], nb_ent=p.initial_params["nb_ent"], nb_food=p.initial_params["nb_food"], nb_river=p.initial_params["nb_river"])

    #VARS
    run = True
    started = True
    pause = False
    fast = False
    displ_all_ents = False

    txt_lines = []
    for i in range(100):
        txt_lines.append("")

    fps_redraw_counter = 0
    fps_mean = []
    max_fps_buffer = 60

    selected = None

    date = 0
    tick = 0

    print("LAUNCH COLONY LIFE SIMULATION v2.0, Welcome !")
    t = time.time()


    while run:
        clock.tick(120)

        console.console.update(date)

        #PYGAME EVENTS
        for event in pygame.event.get():
            if event.type == pygame.QUIT :
                    run = False
            elif event.type == pygame.KEYDOWN:
                if event.key == K_ESCAPE:
                    run = False
                if event.key == K_SPACE:
                    pause = not pause
                if event.key == K_F12:
                    drawer.DEBUG = not drawer.DEBUG
                if event.key == K_F1:
                    np.random.shuffle(simu.entities)
                    drawer.DEBUG_SWITCHED = True
                if event.key == K_f:
                    fast = not fast
                if event.key == K_l:
                    txt_lines = []
                    for i in range(100):
                        txt_lines.append("")
                    displ_all_ents = not displ_all_ents
                if event.key == K_RIGHT:
                    p.sim_params["ACTION_TICK"] = utils.clamp(p.sim_params["ACTION_TICK"]-1, 1, 30)
                if event.key == K_LEFT:
                    p.sim_params["ACTION_TICK"] = utils.clamp(p.sim_params["ACTION_TICK"]+1, 1, 30)
                if event.key == K_e:
                    if started:
                        life.Entity.spawn_randomly(simu)
                if event.key == K_s:
                    if not started:
                        started = True
                if event.key == K_r:
                    started = True
                    selected = None
                    date = 0
                    tick = 0
                    simu.reset()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                #LMB
                if event.button == 1 and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    pass
                elif event.button == 1:
                    for x in range(simu.grid.width):
                        for y in range(simu.grid.height):
                            tile = simu.grid.grid[x][y]
                            if tile.rect.collidepoint(pygame.mouse.get_pos()):
                                if tile.entities != []:
                                    selected = simu.grid.grid[x][y].entities[0]
                                else:
                                    selected = None
                                print("{}, {}".format(tile.get_type(), tile.building.name if tile.building != None else "None"))
                                if tile.food != None:
                                    print("{}/{} - {}".format(round(tile.food.resource_qtt, 1), tile.food.resource_max, tile.food.lifespan))
                                # print(tile.x, tile.y)
                                break
                #MMB
                if event.button == 2:
                    pass
                #RMB
                if event.button == 3 and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    pass
                if event.button == 3:
                    for x in range(simu.grid.width):
                        for y in range(simu.grid.height):
                            tile = simu.grid.grid[x][y]
                            if tile.rect.collidepoint(pygame.mouse.get_pos()):
                                if tile.building == None:
                                    simu.add_building(life.GatheringPlace(None, tile))
                                else:
                                    simu.rm_building(tile.building)
                    pass
        #UPDATE
        if not pause and started:
            if tick >= p.sim_params["ACTION_TICK"]:
                tick = 0
                date += 1
            else:
                tick += 1

            simu.update()

        #DRAW
        if not fast:
            drawer.draw_grid(simu.grid, main_surface, main_surface_alpha)
            drawer.draw_foods(simu.foods, main_surface)
            drawer.draw_building(simu.buildings, main_surface)
            drawer.draw_entities(simu.entities, main_surface, selected, main_surface_alpha)

        #TEXTS        
        fontsize = int(info_surface_height*0.016)
        font = pygame.font.SysFont('Sans', fontsize)

        info_surface.fill((196, 196, 196, 255))

        shift = 0
        changed = False
        index = 0

        # minutes = date*10
        minutes = (date*10)%60
        hours = math.floor((date*10)/60)%24
        days = math.floor(math.floor((date*10)/60)/24)
        date_txt = "Date : Day {}, {}:{}".format(days+1, "0"+str(hours) if hours<10 else hours, "00" if minutes==0 else minutes)
        if txt_lines[index] != date_txt:
            changed = True
            txt_lines[index] = date_txt
        index += 1

        pause_txt = ("PAUSED" if pause else "PLAYING") if started else "NOT STARTED"
        if fast:
            pause_txt += " (FAST)"
        if txt_lines[index] != pause_txt:
            changed = True
            txt_lines[index] = pause_txt
        index += 1

        fps_mean.append(clock.get_fps())
        if len(fps_mean) > max_fps_buffer:
            fps_mean = fps_mean[1:]
        fps_txt = str(round(np.mean(fps_mean))) + " FPS"
        if txt_lines[index] != fps_txt and fps_redraw_counter==0:
            changed = True
            txt_lines[index] = fps_txt
        index += 1
        fps_redraw_counter = (fps_redraw_counter+1)%20

        vars_txt = "R: reset; SPACE: Pause; L: Change info; F: Fast mode".format()
        if txt_lines[index] != vars_txt:
            changed = True
            txt_lines[index] = vars_txt
        index += 1

        param_txt = "SimSpeed = x{}".format(round(p.sim_params["ACTION_TICK_BASE"]/p.sim_params["ACTION_TICK"], 2))
        param_txt += " (MAX)" if p.sim_params["ACTION_TICK"]==1 else ""
        if txt_lines[index] != param_txt:
            changed = True
            txt_lines[index] = param_txt
        index += 1

        if len(simu.entities) > 0:
            nb_ent_txt = "Number of life form : {} ({}%M/{}%F)".format(len(simu.entities), 
                                                                    round(len([x for x in simu.entities if x.sex=="M"])/len(simu.entities)*100, 1),
                                                                    round(len([x for x in simu.entities if x.sex=="F"])/len(simu.entities)*100, 1))
        else:
            nb_ent_txt = "Number of life form : {} ({}%M/{}%F)".format(len(simu.entities), "N/A", "N/A")

        if txt_lines[index] != nb_ent_txt:
            changed = True
            txt_lines[index] = nb_ent_txt
        index += 1

        nb_ent_txt = "Selected:"
        if txt_lines[index] != nb_ent_txt:
            changed = True
            txt_lines[index] = nb_ent_txt
        index += 1

        if selected != None:
            ent_txt0 = "{} ({}/{}), {} days old".format(selected.name, 
                                                selected.sex, 
                                                round(selected.libido) if not selected.pregnant else "P{}".format(round(selected.gestation/240)),
                                                selected.age)

            ent_txt_social = "Social feats: "
            for i, sf in enumerate(selected.social_vector):
                ent_txt_social += sf.feature.lower() + (", " if i < len(selected.social_vector) else "")

            
            ent_txt1 = "HP {}%, Food {}%, Thrist {}% {}".format(round(selected.health/selected.health_max*100, 1),
                                                                round(selected.nutrition/selected.nutrition_max*100, 1),
                                                                round(selected.thirst/selected.thirst_max*100, 1),
                                                                selected.state)
            ent_txt2 = "   "
            for k in selected.inventory:
                ent_txt2 += "{}:{} ".format(k, selected.inventory[k])

            if selected.friends or selected.foes:
                ent_txt3 = "   Frds: {} Foes: {}".format(len(selected.friends), len(selected.foes))
            else:
                ent_txt3 = ""

            ent_txt4 = "Expl. Satisfaction: {}%".format(round((len(selected.known_tiles)/selected.exploration_satistaction)*100, 1))
        else:
            ent_txt0 = ""
            ent_txt_social = ""
            ent_txt1 = ""
            ent_txt2 = ""
            ent_txt3 = ""
            ent_txt4 = ""

        if txt_lines[index] != ent_txt0:
            changed = True
            txt_lines[index] = ent_txt0
        index += 1
        if txt_lines[index] != ent_txt_social:
            changed = True
            txt_lines[index] = ent_txt_social
        index += 1
        if txt_lines[index] != ent_txt1:
            changed = True
            txt_lines[index] = ent_txt1
        index += 1
        if txt_lines[index] != ent_txt2:
            changed = True
            txt_lines[index] = ent_txt2
        index += 1
        if txt_lines[index] != ent_txt3:
            changed = True
            txt_lines[index] = ent_txt3
        index += 1
        if txt_lines[index] != ent_txt4:
            changed = True
            txt_lines[index] = ent_txt4
        index += 1

        if displ_all_ents:

            all_ents = "All Entities (5 max display):"
            if txt_lines[index] != all_ents:
                changed = True
                txt_lines[index] = all_ents
            index += 1

            for i in range(0, 5):
                if i < len(simu.entities):
                    ent_txt_tmp0 = "{} ({}/{}), {} days old".format(simu.entities[i].name, 
                                                simu.entities[i].sex, 
                                                round(simu.entities[i].libido) if not simu.entities[i].pregnant else "P{}".format(round(simu.entities[i].gestation/240)),
                                                simu.entities[i].age)
                    ent_txt_tmp1 = "HP {}%, Food {}%, Thrist {}% {}".format(round(simu.entities[i].health/simu.entities[i].health_max*100, 1),
                                                                        round(simu.entities[i].nutrition/simu.entities[i].nutrition_max*100, 1),
                                                                        round(simu.entities[i].thirst/simu.entities[i].thirst_max*100, 1),
                                                                        simu.entities[i].state)
                    if len(simu.entities[i].inventory) > 0:
                        ent_txt_tmp2 = "   "
                    else:
                        ent_txt_tmp2 = ""
                    for k in simu.entities[i].inventory:
                        if k == "FOOD":
                            ent_txt_tmp2 += "{}:x{} ".format(k, round(simu.entities[i].inventory[k]/simu.entities[i].nutrition_max, 2))
                        elif k=="WATER":
                            ent_txt_tmp2 += "{}:x{} ".format(k, round(simu.entities[i].inventory[k]/simu.entities[i].thirst_max, 2))
                        else:
                            ent_txt_tmp2 += "{}:{} ".format(k, simu.entities[i].inventory[k])

                    ent_txt_tmp3 = "   Frds: {} Foes: {}".format(len(simu.entities[i].friends), len(simu.entities[i].foes))
                    ent_txt_tmp4 = "Expl. Satisfaction: {}%".format(round((len(simu.entities[i].known_tiles)/simu.entities[i].exploration_satistaction)*100, 1))
                else:
                    ent_txt_tmp0 = ""
                    ent_txt_tmp1 = ""
                    ent_txt_tmp2 = ""
                    ent_txt_tmp3 = ""
                    ent_txt_tmp4 = ""

                if txt_lines[index] != ent_txt_tmp0:
                    changed = True
                    txt_lines[index] = ent_txt_tmp0
                index += 1
                if txt_lines[index] != ent_txt_tmp1:
                    changed = True
                    txt_lines[index] = ent_txt_tmp1
                index += 1
                if txt_lines[index] != ent_txt_tmp2:
                    changed = True
                    txt_lines[index] = ent_txt_tmp2
                index += 1
                if txt_lines[index] != ent_txt_tmp3:
                    changed = True
                    txt_lines[index] = ent_txt_tmp3
                index += 1
                if txt_lines[index] != ent_txt_tmp4:
                    changed = True
                    txt_lines[index] = ent_txt_tmp4
                index += 1
        elif len(simu.entities) > 0:

            _txt = "Average information:"
            if txt_lines[index] != _txt:
                changed = True
                txt_lines[index] = _txt
            index += 1

            _txt = "{} entities alive, {} birth, {} death".format(len(simu.entities), simu.nb_birth, simu.nb_dead)
            if txt_lines[index] != _txt:
                changed = True
                txt_lines[index] = _txt
            index += 1

            _txt = "Average Age: {} days old, Friends: {}; Foes: {}; Libido: {}".format(round(np.mean([e.age for e in simu.entities]), 1), round(np.mean([len(e.friends) for e in simu.entities]), 1), round(np.mean([len(e.foes) for e in simu.entities]), 1), round(np.mean([e.libido for e in simu.entities]), 1))
            if txt_lines[index] != _txt:
                changed = True
                txt_lines[index] = _txt
            index += 1

            _txt = "Average Exploration: {}%".format(
                                            round(np.mean([(len(e.known_tiles)/e.total_tiles)*100 for e in simu.entities]), 1)
                                                    )
            if txt_lines[index] != _txt:
                changed = True
                txt_lines[index] = _txt
            index += 1

            _txt = "With child: {}, due in {} days".format(len([e for e in simu.entities if e.pregnant]), [round(e.gestation/240,1) for e in simu.entities if e.pregnant])
            if txt_lines[index] != _txt:
                changed = True
                txt_lines[index] = _txt
            index += 1

            avgh = round((np.mean([e.health/e.health_max for e in simu.entities]))*100, 1)
            avgn = round((np.mean([e.nutrition/e.nutrition_max for e in simu.entities]))*100, 1)
            avgt = round((np.mean([e.thirst/e.thirst_max for e in simu.entities]))*100, 1)
            _txt = "Average health: {}%, nutrition: {}%, thirst: {}%".format(avgh, avgn, avgt)
            if txt_lines[index] != _txt:
                changed = True
                txt_lines[index] = _txt
            index += 1

            d = {}
            for e in simu.entities:
                if e.state_short in d:
                    d[e.state_short] += 1
                else:
                    d[e.state_short] = 1
            _sum = sum(d.values())
            _txt = ""
            for k in d:
                _txt += ("{}:{}% ".format(k, round((d[k]/_sum)*100)))
            if txt_lines[index] != _txt:
                changed = True
                txt_lines[index] = _txt
            index += 1
        else:
            for i in range(7):
                _txt = " "
                if txt_lines[index] != _txt:
                    changed = True
                    txt_lines[index] = _txt
                index += 1




        if txt_lines[index] != " ":
            changed = True
            txt_lines[index] = " "
        index += 1
        if txt_lines[index] != "Update and Messages:":
            changed = True
            txt_lines[index] = "Update and Messages:"
        index += 1

        for cons in console.console.lines:
            txt_cons_line = cons
            if txt_lines[index] != txt_cons_line:
                changed = True
                txt_lines[index] = txt_cons_line
            index += 1

        if changed:
            for i, l in enumerate(txt_lines):
                # if l != "":
                shift = drawer.draw_text(l, font, fontsize, info_surface, shift)
                    # txt_lines[i] = ""
            window.blit(info_surface, (main_surface.get_width(),0))



        #BLIT SURFACES
        if not fast:
            window.blit(main_surface, (0,0))
            window.blit(main_surface_alpha, (0,0))


        #UPDATE DISPLAY
        # pygame.display.flip()
            pygame.display.update()
        else:
            if tick == 0:
                print(round(np.mean(fps_mean)))

        # print("Avg friends: {} Avg Foes: {}\r".format(round(np.mean([len(e.friends) for e in simu.entities])/len(simu.entities), 2), round(np.mean([len(e.foes) for e in simu.entities])/len(simu.entities), 2)), end='', flush=True)



    print("END OF COLONY LIFE SIMULATION ! Ended in approx. {} hours".format( round((time.time() - t)/60/24, 2) ))

    pygame.display.quit()
    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()