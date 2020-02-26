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

import threading

class ThreadSimulation(threading.Thread):
    """docstring for ThreadSimulation"""
    def __init__(self, simu, freq):
        super(ThreadSimulation, self).__init__()
        self.simu = simu
        self.freq = freq

        self._pause = False
        self._stop  = False

        self.tick_second   = 0
        self.loop_times    = []
        self.max_loop_time = 10

    def run(self):
        # super(ThreadSimulation, self).run()
        while not self._stop:
            _time = time.time()
            
            if not self._pause:
                self.simu.update()
            _wait_time = (self.freq / 1000.0) - (time.time() - _time)
            if _wait_time > 0:
                time.sleep(_wait_time)

            _div = time.time() - _time if time.time() - _time > 0 else 0.00001
            self.loop_times.append(1.0 / _div)
            if len(self.loop_times) > self.max_loop_time:
                self.loop_times = self.loop_times[1:]
            self.tick_second = np.mean(self.loop_times)

    def pause(self):
        self._pause = not self._pause

    def stop(self):
        self._stop = True

def main():

    pygame.init()
    monitor = get_monitors()[0]
    clock = pygame.time.Clock()

    if ( p.parameters["SCREEN_PERCENT"] > 0.0 and p.parameters["SCREEN_PERCENT"] <= 1.0 ):
        p.parameters["SCREEN_WIDTH"]  = int(monitor.width  * p.parameters["SCREEN_PERCENT"])
        p.parameters["SCREEN_HEIGHT"] = int(monitor.height * p.parameters["SCREEN_PERCENT"])

    if ( p.parameters["MAIN_WIN_RATIO"] <= 0.0 or p.parameters["MAIN_WIN_RATIO"] > 1.0 ):
        p.parameters["MAIN_WIN_RATIO"]  = 0.625

    p.parameters["MAIN_WIN_WH"] = int(p.parameters["MAIN_WIN_RATIO"] * p.parameters["SCREEN_WIDTH"])

    screen_width, screen_height = p.parameters["SCREEN_WIDTH"], p.parameters["SCREEN_HEIGHT"]
    #TODO Calculate automatically surfaces size from SCREEN_W/H and remove it from hardcoded values in parameters
    main_surface_width, main_surface_height = p.parameters["MAIN_WIN_WH"], p.parameters["SCREEN_HEIGHT"]

    info_surface_width, info_surface_height = p.parameters["SCREEN_WIDTH"] - p.parameters["MAIN_WIN_WH"], p.parameters["SCREEN_HEIGHT"]

    """
    "SCREEN_WIDTH"     : 1440,
    "SCREEN_HEIGHT"    : 900,
    "MAINW_WIDTH"      : 900, # "SCREEN_HEIGHT"
    "MAINW_HEIGHT"     : 900, # "SCREEN_HEIGHT"
    "INFO_SURF_WIDTH"  : 1440-900, # "SCREEN_WIDTH" - "SCREEN_HEIGHT"
    "INFO_SURF_HEIGHT" : 900, # "SCREEN_HEIGHT"
    "GRID_W"           : 100,
    "GRID_H"           : 100
    """

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

    thread_simu = ThreadSimulation(simu, p.sim_params["ACTION_TICK"])

    #VARS
    run = True
    started = True
    pause = False
    fast = False
    displ_all_ents = False

    refresh_counter_txt     = 0
    refresh_counter_txt_max = 10
    refresh_counter_drw     = 0
    refresh_counter_drw_max = 30
    refresh_counter_blt     = 0
    refresh_counter_blt_max = 30

    txt_lines = []
    for i in range(100):
        txt_lines.append("")

    fps_redraw_counter = 0
    fps_mean = []
    max_fps_buffer = 60

    selected = None

    print("LAUNCH COLONY LIFE SIMULATION v2.0, Welcome !")
    t = time.time()

    thread_simu.start()

    while run:
        clock.tick(120)

        console.console.update(thread_simu.simu.date)

        #PYGAME EVENTS
        for event in pygame.event.get():
            if event.type == pygame.QUIT :
                    run = False
            elif event.type == pygame.KEYDOWN:
                if event.key == K_ESCAPE:
                    run = False
                if event.key == K_SPACE:
                    pause = not pause
                    thread_simu.pause()
                if event.key == K_F12:
                    drawer.DEBUG = not drawer.DEBUG
                if event.key == K_F1:
                    np.random.shuffle(thread_simu.simu.entities)
                    drawer.DEBUG_SWITCHED = True
                if event.key == K_f:
                    fast = not fast
                if event.key == K_l:
                    txt_lines = []
                    for i in range(100):
                        txt_lines.append("")
                    displ_all_ents = not displ_all_ents
                if event.key == K_RIGHT:
                    p.sim_params["ACTION_TICK"] = utils.clamp(p.sim_params["ACTION_TICK"]-25, 0, 1000)
                    thread_simu.freq = p.sim_params["ACTION_TICK"]

                if event.key == K_LEFT:
                    p.sim_params["ACTION_TICK"] = utils.clamp(p.sim_params["ACTION_TICK"]+25, 0, 1000)
                    thread_simu.freq = p.sim_params["ACTION_TICK"]

                if event.key == K_e:
                    if started:
                        life.Entity.spawn_randomly(thread_simu.simu)
                if event.key == K_s:
                    if not started:
                        started = True
                if event.key == K_r:
                    started = True
                    selected = None
                    tick = 0
                    thread_simu.simu.reset()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                #LMB
                if event.button == 1 and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    pass
                elif event.button == 1:
                    for x in range(thread_simu.simu.grid.width):
                        for y in range(thread_simu.simu.grid.height):
                            tile = thread_simu.simu.grid.grid[x][y]
                            if tile.rect.collidepoint(pygame.mouse.get_pos()):
                                if tile.entities != []:
                                    selected = thread_simu.simu.grid.grid[x][y].entities[0]
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
                    # for x in range(thread_simu.simu.grid.width):
                    #     for y in range(thread_simu.simu.grid.height):
                    #         tile = thread_simu.simu.grid.grid[x][y]
                    #         if tile.rect.collidepoint(pygame.mouse.get_pos()):
                    #             if tile.building == None:
                    #                 thread_simu.simu.add_building(life.GatheringPlace(None, tile))
                    #             else:
                    #                 thread_simu.simu.rm_building(tile.building)
                    pass

        #DRAW
        if not fast:
            drawer.draw_grid(thread_simu.simu.grid, main_surface, main_surface_alpha)
            drawer.draw_foods(thread_simu.simu.foods, main_surface)
            drawer.draw_building(thread_simu.simu.buildings, main_surface)
            drawer.draw_entities(thread_simu.simu.entities, main_surface, selected, main_surface_alpha)
            refresh_counter_drw = 0
        else:
            if refresh_counter_drw % refresh_counter_drw_max == 0:
                drawer.draw_grid(thread_simu.simu.grid, main_surface, main_surface_alpha)
                drawer.draw_foods(thread_simu.simu.foods, main_surface)
                drawer.draw_building(thread_simu.simu.buildings, main_surface)
                drawer.draw_entities(thread_simu.simu.entities, main_surface, selected, main_surface_alpha)
                refresh_counter_drw = 0
            refresh_counter_drw += 1

        #TEXTS  
        info_surface.fill((196, 196, 196, 255))

        shift = 0
        changed = False
        index = 0

        # minutes = thread_simu.simu.date*10
        minutes = (thread_simu.simu.date*10)%60
        hours = math.floor((thread_simu.simu.date*10)/60)%24
        days = math.floor(math.floor((thread_simu.simu.date*10)/60)/24)
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

        # try:
        #     ticksecond = round( 1.0 / (p.sim_params["ACTION_TICK"]/1000.0) , 2)
        # except ZeroDivisionError:
        #     ticksecond = "MAX"
        # param_txt = "SimSpeed = {} tick/sec".format(ticksecond)
        param_txt = "SimSpeed ({}ms/tck): {} tick/sec".format(p.sim_params["ACTION_TICK"], round(thread_simu.tick_second, 1))
        # param_txt += " (MIN)" if p.sim_params["ACTION_TICK"]==1000 else ""
        # param_txt += " (MAX)" if p.sim_params["ACTION_TICK"]==0 else ""
        if txt_lines[index] != param_txt:
            changed = True
            txt_lines[index] = param_txt
        index += 1

        if len(thread_simu.simu.entities) > 0:
            nb_ent_txt = "Number of life form : {} ({}%M/{}%F)".format(len(thread_simu.simu.entities), 
                                                                    round(len([x for x in thread_simu.simu.entities if x.sex=="M"])/len(thread_simu.simu.entities)*100, 1),
                                                                    round(len([x for x in thread_simu.simu.entities if x.sex=="F"])/len(thread_simu.simu.entities)*100, 1))
        else:
            nb_ent_txt = "Number of life form : {} ({}%M/{}%F)".format(len(thread_simu.simu.entities), "N/A", "N/A")

        if txt_lines[index] != nb_ent_txt:
            changed = True
            txt_lines[index] = nb_ent_txt
        index += 1

        if selected != None:

            ent_txt0 = "{} ({}/{}), {} days old".format(selected.name, 
                                                selected.sex, 
                                                round(selected.libido) if not selected.pregnant else "P{}".format(round(selected.gestation/240)),
                                                selected.age)

            nb_ent_txt = "Selected: {}".format(ent_txt0)
            if txt_lines[index] != nb_ent_txt:
                changed = True
                txt_lines[index] = nb_ent_txt
            index += 1

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

            ent_txt5 = ""
        else:
            # ent_txt0 = ""
            ent_txt_social = ""
            ent_txt1 = ""
            ent_txt2 = ""
            ent_txt3 = ""
            ent_txt4 = ""
            ent_txt5 = ""

        # if txt_lines[index] != ent_txt0:
        #     changed = True
        #     txt_lines[index] = ent_txt0
        # index += 1
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
        if txt_lines[index] != ent_txt5:
            changed = True
            txt_lines[index] = ent_txt5
        index += 1

        if displ_all_ents:

            all_ents = "All Entities (5 max display):"
            if txt_lines[index] != all_ents:
                changed = True
                txt_lines[index] = all_ents
            index += 1

            for i in range(0, 5):
                if i < len(thread_simu.simu.entities):
                    ent_txt_tmp0 = "{} ({}/{}), {} days old".format(thread_simu.simu.entities[i].name, 
                                                thread_simu.simu.entities[i].sex, 
                                                round(thread_simu.simu.entities[i].libido) if not thread_simu.simu.entities[i].pregnant else "P{}".format(round(thread_simu.simu.entities[i].gestation/240)),
                                                thread_simu.simu.entities[i].age)
                    ent_txt_tmp1 = "HP {}%, Food {}%, Thrist {}% {}".format(round(thread_simu.simu.entities[i].health/thread_simu.simu.entities[i].health_max*100, 1),
                                                                        round(thread_simu.simu.entities[i].nutrition/thread_simu.simu.entities[i].nutrition_max*100, 1),
                                                                        round(thread_simu.simu.entities[i].thirst/thread_simu.simu.entities[i].thirst_max*100, 1),
                                                                        thread_simu.simu.entities[i].state)
                    if len(thread_simu.simu.entities[i].inventory) > 0:
                        ent_txt_tmp2 = "   "
                    else:
                        ent_txt_tmp2 = ""
                    for k in thread_simu.simu.entities[i].inventory:
                        if k == "FOOD":
                            ent_txt_tmp2 += "{}:x{} ".format(k, round(thread_simu.simu.entities[i].inventory[k]/thread_simu.simu.entities[i].nutrition_max, 2))
                        elif k=="WATER":
                            ent_txt_tmp2 += "{}:x{} ".format(k, round(thread_simu.simu.entities[i].inventory[k]/thread_simu.simu.entities[i].thirst_max, 2))
                        else:
                            ent_txt_tmp2 += "{}:{} ".format(k, thread_simu.simu.entities[i].inventory[k])

                    ent_txt_tmp3 = "   Frds: {} Foes: {}".format(len(thread_simu.simu.entities[i].friends), len(thread_simu.simu.entities[i].foes))
                    ent_txt_tmp4 = "Expl. Satisfaction: {}%".format(round((len(thread_simu.simu.entities[i].known_tiles)/thread_simu.simu.entities[i].exploration_satistaction)*100, 1))
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
        elif len(thread_simu.simu.entities) > 0:

            _txt = "Average information:"
            if txt_lines[index] != _txt:
                changed = True
                txt_lines[index] = _txt
            index += 1

            _txt = "{} entities alive, {} birth, {} death".format(len(thread_simu.simu.entities), thread_simu.simu.nb_birth, thread_simu.simu.nb_dead)
            if txt_lines[index] != _txt:
                changed = True
                txt_lines[index] = _txt
            index += 1

            _txt = "Average Age: {} days old, Friends: {}; Foes: {}".format(round(np.mean([e.age for e in thread_simu.simu.entities]), 1), round(np.mean([len(e.friends) for e in thread_simu.simu.entities]), 1), round(np.mean([len(e.foes) for e in thread_simu.simu.entities]), 1))
            if txt_lines[index] != _txt:
                changed = True
                txt_lines[index] = _txt
            index += 1

            _txt = "Average Exploration: {}%".format(
                                            round(np.mean([(len(e.known_tiles)/e.total_tiles)*100 for e in thread_simu.simu.entities]), 1)
                                                    )
            if txt_lines[index] != _txt:
                changed = True
                txt_lines[index] = _txt
            index += 1

            _txt = "With child: {}, due in {} days".format(len([e for e in thread_simu.simu.entities if e.pregnant]), np.sort([round(e.gestation/240,1) for e in thread_simu.simu.entities if e.pregnant]))
            if txt_lines[index] != _txt:
                changed = True
                txt_lines[index] = _txt
            index += 1

            avgh = round((np.mean([e.health/e.health_max for e in thread_simu.simu.entities]))*100, 1)
            avgn = round((np.mean([e.nutrition/e.nutrition_max for e in thread_simu.simu.entities]))*100, 1)
            avgt = round((np.mean([e.thirst/e.thirst_max for e in thread_simu.simu.entities]))*100, 1)
            _txt = "Average health: {}%, nutrition: {}%, thirst: {}%".format(avgh, avgn, avgt)
            if txt_lines[index] != _txt:
                changed = True
                txt_lines[index] = _txt
            index += 1

            d = {}
            for e in thread_simu.simu.entities:
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
                _txt = ""
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

        _max_line_size = np.max([len(t) for t in txt_lines])

        # info_surface_width
        # fontsize = int(info_surface_height*0.016)
        # fontsize = int(_max_line_size * (1.0/3.0))
        fontsize = int( info_surface_width / _max_line_size ) * 2
        font = pygame.font.SysFont('Sans', fontsize)

        if changed:
            for i, l in enumerate(txt_lines):
                if l != "":
                    shift = drawer.draw_text(l, font, fontsize, info_surface, shift)
                    # txt_lines[i] = ""
            if not fast:
                window.blit(info_surface, (main_surface.get_width(),0))
                refresh_counter_txt = 0
            else:
                if refresh_counter_txt % refresh_counter_txt_max == 0:
                    window.blit(info_surface, (main_surface.get_width(),0))
                    refresh_counter_txt = 0
                refresh_counter_txt += 1


        #BLIT SURFACES
        if not fast:
            window.blit(main_surface, (0,0))
            window.blit(main_surface_alpha, (0,0))
            refresh_counter_blt = 0
            
        else:
            if refresh_counter_blt % refresh_counter_blt_max == 0:
                window.blit(main_surface, (0,0))
                window.blit(main_surface_alpha, (0,0))
                
                #UPDATE DISPLAY
                # pygame.display.update()
                refresh_counter_blt = 0

            refresh_counter_blt += 1

        #UPDATE DISPLAY
        pygame.display.update()
        # print("Avg friends: {} Avg Foes: {}\r".format(round(np.mean([len(e.friends) for e in thread_simu.simu.entities])/len(thread_simu.simu.entities), 2), round(np.mean([len(e.foes) for e in thread_simu.simu.entities])/len(thread_simu.simu.entities), 2)), end='', flush=True)

    thread_simu.stop()


    print("END OF COLONY LIFE SIMULATION ! Ended in approx. {} hours".format( round((time.time() - t)/60/24, 2) ))

    pygame.display.quit()
    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()