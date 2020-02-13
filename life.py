import numpy as np
import pathfinding as pf
import utils
import pprint
import math

import pygame

import parameters as p
import environment as env
import ColonyLifeSim as _cls
import console

class Entity(object):
    """docstring for Entity"""
    def __init__(self, simulation, tile=None, name=("Ent", "", "Basename")):
        super(Entity, self).__init__()
        self.simu = simulation
        self.grid = self.simu.grid

        self.forbidden_tiles = Entity.get_forbidden_tiles_base()

        self.goto_tile = None
        self.explore_goal = None
        self.goto_plant_tile = None
        self.path = []

        self.known_tiles = []
        self.total_tiles = len(self.simu.grid.get_tile_1D_list())
        # self.total_reachable_tiles = len([t for t in self.simu.grid.get_tile_1D_list() if t.get_type() not in self.forbidden_tiles])
        self.total_reachable_tiles = len([t for t in self.simu.grid.get_tile_1D_list() if t.get_type() not in self.forbidden_tiles+["SHALLOW_WATER"]])
        self.exploration_satistaction = int(self.total_reachable_tiles * (0.15 + (np.random.random() * 0.25)))
        self.visible_tiles = [[], [], [], [], []]

        if tile != None:
            self.tile = tile
        else:
            self.tile = np.random.choice(self.grid.grid[np.random.randint(0, len(self.grid.grid[0]))])
        self.tile.add_entity(self)

        # self.all_names = name
        # self.name = self.all_names[0] + " " + (self.all_names[1][0] + ". " if self.all_names[1] != "" else "") + self.all_names[2]
        self.set_name(name)

        self.color = (255, 208, 42, 255)

        self.act_tck_cnt = 0
        self.chck_surrounding_tmr = 0
        self.action_cooldown = 0

        self.state = "NONE"
        self.state_short = "NA"

        self.work_left = 0

        #Vision in tile
        self.vision_radius = 8

        self.dead = False

        self.health_max = 100
        self.health = self.health_max

        self.parents = (None, None)
        self.children = []

        self.sex = np.random.choice(["M", "F"])
        self.libido = 0
        self.pregnant = False
        self.child_other_parent = None
        self.gestation = 0

        self.age_raw = 0
        self.age     = 0
        self.old_age_thresh = np.random.randint(6, 9)

        self.inventory = {}

        self.nutrition_max  = 2400 #10 days, 1 day == 240
        self.nutrition      = self.nutrition_max
        self.nutrition_rate = 0.8+(np.random.random()*0.4)
        self.max_food_inventory  = round(self.nutrition_max * (4.0/10.0))

        self.food_eaten_per_tick = (self.nutrition_max/10.0)/3.0
        self.max_food_harvested  = (self.nutrition_max/10.0)/2.0
        self.has_to_eat = False

        self.food_memory = []
        self.food_memory_max = -1
        self.planted_food_list = []

        self.grow_food_tile = []

        self.thirst_max  = 720 #3 days, 1 day == 240
        self.thirst      = self.thirst_max
        self.thirst_rate = 0.8+(np.random.random()*0.4)
        self.max_water_inventory = round(self.thirst_max)

        self.water_drank_per_tick = (self.thirst_max/3.0)
        self.max_water_harvested  = (self.thirst_max/3.0)*2
        self.has_to_drink = False

        self.water_memory = []
        self.water_memory_max = 1

        #Social
        self.friends = []
        self.foes    = []
        self.relations = {}
        mu, sigma = 0, 0.1
        # self.social_vector = utils.normalise_list([np.random.normal(mu, sigma) for i in range(p.sim_params["SOCIAL_FEATURES"])])
        # self.social_vector = [np.random.random() for i in range(p.sim_params["SOCIAL_FEATURES"])]
        self.social_vector = np.random.choice(p.social_features_list, p.sim_params["SOCIAL_FEATURES"], replace=False)

        # print(self.all_names, [f.feature for f in self.social_vector])

        self.buildings       = []
        self.owned_buildings = []

        self.behaviours_by_priority = []
        self.behaviours_by_priority.append(self.b_drink)
        self.behaviours_by_priority.append(self.b_eat)
        self.behaviours_by_priority.append(self.b_collect_water)
        self.behaviours_by_priority.append(self.b_harvest_food)
        self.behaviours_by_priority.append(self.b_search_and_mate)
        self.behaviours_by_priority.append(self.b_social_interaction)
        self.behaviours_by_priority.append(self.b_explore)
        self.behaviours_by_priority.append(self.b_plant_food)
        self.behaviours_by_priority.append(self.b_idle)

    def update(self):

        if self.health <= 0:
            print("{} died of bad health at {} days old".format(self.name, self.age))
            console.console.print("{} died of bad health at {} days old".format(self.name, self.age))
            self.dead = True
            self.tile.rm_entity(self)
        if self.thirst <= 0:
            self.health -= 100/(6*(np.random.randint(0, 3)+1))
            if self.health <= 0:
                print("{} died of thirst at {} days old".format(self.name, self.age))
                console.console.print("{} died of thirst at {} days old".format(self.name, self.age))
                self.dead = True
                self.tile.rm_entity(self)
        if self.nutrition <= 0:
            self.health -= 100/(6*(np.random.randint(11, 24)+1))
            if self.health <= 0:
                print("{} died of starvation at {} days old".format(self.name, self.age))
                console.console.print("{} died of starvation at {} days old".format(self.name, self.age))
                self.dead = True
                self.tile.rm_entity(self)
        if self.age >= 30 * self.old_age_thresh:
            if np.random.random() < (1 - ((self.age-(30 * self.old_age_thresh))/(30 * self.old_age_thresh))):
                print("{} died of old age at {} days old (death chance: {})".format(self.name, self.age, round(1 - ((self.age-(30 * self.old_age_thresh))/(30 * self.old_age_thresh)), 2)))
                console.console.print("{} died of old age at {} days old (death chance: {})".format(self.name, self.age, round(1 - ((self.age-(30 * self.old_age_thresh))/(30 * self.old_age_thresh)), 2)))
                self.dead = True
                self.tile.rm_entity(self)
        
        if self.dead:
            for e in self.simu.entities:
                if e != self and self in e.relations:
                    del e.relations[self]
            return

        if self.work_left <= 0:

            if self.chck_surrounding_tmr >= 6: #Every hour if not working
                self.chck_surrounding_tmr = 0
                self.check_surrounding()
            else:
                self.chck_surrounding_tmr += 1

            for b in self.behaviours_by_priority:
                if b():
                    break
            
            for n in self.grid.get_neighbours_of(self.tile) + [self.tile]:
                self.known_tiles.append(n)
            self.known_tiles = list(set(self.known_tiles))

            # print("{} ({})".format(len(self.known_tiles), self.exploration_satistaction))
        else:
            self.work_left -= 1

        self.nutrition = max(0, self.nutrition-self.nutrition_rate)
        self.thirst    = max(0, self.thirst-self.thirst_rate)
        if self.nutrition > self.nutrition_max*0.35 and self.thirst > self.thirst_max*0.35:
            self.health = min(self.health_max, self.health + np.mean([self.nutrition/self.nutrition_max, self.thirst/self.thirst_max])/100)


        if self.pregnant:
            self.libido = 0
            self.gestation -= 1
            if self.gestation <= 0:
                self.give_birth()
        else:
            self.libido = min(100, self.libido + (np.random.random()/4.0))

        self.age_raw += 1
        minutes = (self.age_raw*10)%60
        hours = math.floor((self.age_raw*10)/60)%24
        days = math.floor(math.floor((self.age_raw*10)/60)/24)
        self.age = round(days + (hours/24), 1)

        self.visible_tiles = [[], [], [], [], []]



    def move_to(self, dest):
        self.tile.rm_entity(self)
        dest.add_entity(self)
        self.work_left = int(round(dest.get_cost()))
        self.tile = dest

    def check_surrounding(self):

        # self.food_memory = [f for f in self.food_memory if (f.available and not f.dead)]
        food_sorted = self.get_closest_foods(self.get_visible_tiles(0))
        if food_sorted != []:
            _to_sort = self.food_memory + food_sorted
            def key(e):
                return utils.distance2p(self.tile.getXY(), e.tile.getXY())
            _to_sort.sort(key=key)

            self.food_memory = _to_sort

        sh_wa_tiles_sorted = self.get_closest_water(self.get_visible_tiles(0))
        if sh_wa_tiles_sorted != []:
            # self.water_memory = sh_wa_tiles_sorted[:min(len(sh_wa_tiles_sorted), self.water_memory_max)]
            _to_sort = self.water_memory + sh_wa_tiles_sorted
            def key(e):
                return utils.distance2p(self.tile.getXY(), e.getXY())
            _to_sort.sort(key=key)

            self.water_memory = _to_sort[:min(len(_to_sort), self.water_memory_max)]

        
    def update_relations(self):
        for e in self.relations:
            if e not in self.friends and e not in self.foes:
                if self.relations[e] > p.sim_params["FRIEND_FOE_TRESH"]:
                    self.friends.append(e)
                elif self.relations[e] < -p.sim_params["FRIEND_FOE_TRESH"]:
                    self.foes.append(e)
            elif e in self.friends and self.relations[e] <= p.sim_params["FRIEND_FOE_TRESH"]:
                self.friends.remove(e)
            elif e in self.foes and self.relations[e] >= -p.sim_params["FRIEND_FOE_TRESH"]:
                self.foes.remove(e)

        self.friends = [x for x in self.friends if not x.dead]
        self.foes = [x for x in self.foes if not x.dead]

    def form_relations_with_surroundings(self):
        ent_sorted = self.get_closest_entities(self.get_visible_tiles(1))
        for e in ent_sorted:
            if e == self:
                continue

            if e not in self.relations:
                self.relations[e] = 0.0

            simil = p.SocialFeature.list_similatiry(self.social_vector, e.social_vector)
            
            self.relations[e] += simil

            self.relations[e] = utils.clamp(self.relations[e], -p.sim_params["FRIEND_FOE_TRESH"]*2, p.sim_params["FRIEND_FOE_TRESH"]*2)

        self.update_relations()

    def get_closest_water(self, tile_list, center=None):
        if center == None:
            center = self.tile
        of_type = [t for t in tile_list if (t.get_type()=="SHALLOW_WATER" or t.is_river)]

        def key(e):
            return utils.distance2p(center.getXY(), e.getXY())
        of_type.sort(key=key)

        return of_type

    def get_closest_foods(self, tile_list, center=None):
        if center == None:
            center = self.tile
        of_type = [t for t in tile_list if (t.food!=None)]

        def key(e):
            return utils.distance2p(center.getXY(), e.getXY())
        of_type.sort(key=key)

        return [t.food for t in of_type]

    def get_closest_entities(self, tile_list, center=None):
        if center == None:
            center = self.tile
        of_type = [t for t in tile_list if (t.entities!=[])]

        def _sort_key(e):
            return utils.distance2p(center.getXY(), e.getXY())
        of_type.sort(key=_sort_key)

        return [e for tile in of_type for e in tile.entities]

    #return [include_self, exclude_self, unexplored_reachable_tiles, double_radius, double_radius_exclude]
    def compute_visible_tiles_step(self, index, costum=-1):
        if costum>=0:
            res = []
            current = [self.tile]
            for i in range(costum):
                new_current = []
                for c in current:
                    if c not in res:
                        res.append(c)
                    for n in self.grid.get_neighbours_of(c, diag_neigh=False):
                        if n not in res:
                            new_current.append(n)
                current = new_current
        if index == 0:
            res = []
            current = [self.tile]
            for i in range(self.vision_radius):
                new_current = []
                for c in current:
                    if c not in res:
                        res.append(c)
                    for n in self.grid.get_neighbours_of(c, diag_neigh=False):
                        if n not in res:
                            new_current.append(n)
                current = new_current
            self.visible_tiles[index] = res
        elif index == 1:
            res = []
            current = [self.tile]
            for i in range(self.vision_radius):
                new_current = []
                for c in current:
                    if c not in res:
                        res.append(c)
                    for n in self.grid.get_neighbours_of(c, diag_neigh=False):
                        if n not in res:
                            new_current.append(n)
                current = new_current
            res.remove(self.tile)
            self.visible_tiles[index] = res
        elif index == 2:
            res = []
            for i in range(20):
                p = utils.point_from_direction(self.tile.getXY(), np.random.randint(self.vision_radius, self.vision_radius*2), np.random.randint(0, 360))
                if not self.grid.out_of_bound(math.floor(p[0]), math.floor(p[1])) and self.grid.grid[math.floor(p[0])][math.floor(p[1])] not in self.known_tiles and self.grid.grid[math.floor(p[0])][math.floor(p[1])].get_type() not in self.forbidden_tiles:
                    res.append(self.grid.grid[math.floor(p[0])][math.floor(p[1])])
            
            self.visible_tiles[index] = res
        elif index == 3:
            res = []
            for i in range(20):
                p = utils.point_from_direction(self.tile.getXY(), np.random.randint(1, self.vision_radius), np.random.randint(0, 360))
                if not self.grid.out_of_bound(math.floor(p[0]), math.floor(p[1])) and self.grid.grid[math.floor(p[0])][math.floor(p[1])].get_type() not in self.forbidden_tiles:
                    res.append(self.grid.grid[math.floor(p[0])][math.floor(p[1])])
            
            self.visible_tiles[index] = res
        else:
            res = []
        return res

    #return [include_self, _exclude_self, unexplored_reachable_tiles, double_radius, double_radius_exclude]
    def get_visible_tiles(self, index, costum=-1):
        if costum != -1:
            return self.compute_visible_tiles_step(-1, costum=costum)
        if self.visible_tiles[index] == []:
            self.compute_visible_tiles_step(index, costum=costum)
        return self.visible_tiles[index]

    def eat_from_inventory(self):
        self.state = "EAT"
        self.state_short = "EAT"
        target = min(min(self.inventory["FOOD"], self.food_eaten_per_tick), self.nutrition_max-self.nutrition)
        self.inventory["FOOD"] -= target
        self.nutrition += target

        target_water_from_food = target*0.05
        self.thirst = min(self.thirst+target_water_from_food, self.thirst_max)

    def drink_from_inventory(self):
        self.state = "DRINK"
        self.state_short = "DRK"
        target = min(min(self.inventory["WATER"], self.water_drank_per_tick), self.thirst_max-self.thirst)
        self.inventory["WATER"] -= target
        self.thirst += target

        target_food_from_water = target*0.35
        self.nutrition = min(self.nutrition+target_food_from_water, self.nutrition_max)

    def near_food(self):
        if self.tile.food != None and self.tile.food.available and not self.tile.food.dead:
                return self.tile.food
        # for nt in self.grid.get_neighbours_of(self.tile):
        #     if nt.food != None and nt.food.available and not nt.food.dead:
        #         return nt.food
        #     elif nt in self.food_memory:
        #         self.food_memory = [f for f in self.food_memory if f != nt]
        return None

    def near_water(self):
        if self.tile.get_type() == "SHALLOW_WATER" or self.tile.is_river:
            return self.tile
        # for nt in self.grid.get_neighbours_of(self.tile):
        #     if nt.get_type() == "SHALLOW_WATER" or nt.is_river:
        #         return nt
        return None

    def near_other(self):
        self_tile_ent = [e for e in self.tile.entities if e != self]
        if self_tile_ent:
            return self_tile_ent[0]
        # for nt in self.grid.get_neighbours_of(self.tile):
        #     if nt.entities:
        #         return nt.entities[0]
        return None

    def harvest_food(self, food):
        self.state = "HARVEST FOOD"
        self.state_short = "HrvFD"
        
        target = self.max_food_harvested
        
        if food.resource_qtt < target:
            target = food.resource_qtt

        if "FOOD" not in self.inventory:
            self.inventory["FOOD"] = target
        else:
            self.inventory["FOOD"] = min(self.inventory["FOOD"]+target, self.max_food_inventory)
        food.resource_qtt -= target

    def collect_water(self):
        self.state = "COLLECT WATER"
        self.state_short = "ColWtR"
        
        target = self.max_water_harvested
        
        if "WATER" not in self.inventory:
            self.inventory["WATER"] = target
        else:
            self.inventory["WATER"] = min(self.inventory["WATER"]+target, self.max_water_inventory)

    def goto_food(self, food):
        return self.goto_position(food.tile, state="GOTO FOOD", state_short="GTFd")

    def goto_water(self, tile):
        return self.goto_position(tile, state="GOTO WATER", state_short="GTWtr")

    def goto_position(self, _tile, state="GOTO POSITION", state_short="GTPos"):
        self.state = state
        self.state_short = state_short
        if (self.goto_tile == _tile) and self.path != []:
            #Follow path
            self.move_to(self.path[0])
            self.path = self.path[1:]
            # if self.tile == _tile or self.path == []:
            if self.tile in _tile.get_neighbours() or self.tile == _tile or self.path == []:
                #destination reached
                self.reset_path()
                return True
        else:
            self.goto_tile = _tile
            self.path = pf.astar(self.tile, self.goto_tile, self.grid, forbidden=self.forbidden_tiles)
            if self.path == None:
                # self.reset_path()
                print(self.name, "NO PATH TO ", self.goto_tile.getXY())
                return False
            else:
                self.path = self.path[1:]
                return True

    def reset_path(self):
        self.goto_tile = None
        self.path = []

    def random_walk(self):
        # if self.goto_tile == self.tile:
        #     # print(self.name, str(self.goto_tile), str(self.tile))
        #     self.reset_path()
        gath_places = [b for b in self.buildings if isinstance(b, GatheringPlace)]
        if gath_places and utils.distance2p(self.tile.getXY(), gath_places[0].tile.getXY()) > 25:
            self.goto_position(gath_places[0], state="BACKTOCAMP", state_short="GTGatPl")
        else:
            if self.goto_tile != None and self.goto_tile != self.tile:
                self.state = "IDLE"
                self.state_short = "I"
                self.goto_position(self.goto_tile, state=self.state, state_short=self.state_short)
            else:
                self.state = "THINK"
                self.state_short = "Th"
                #choose random tile
                _tiles = self.get_visible_tiles(3)
                if _tiles:
                    self.goto_tile = np.random.choice( _tiles )
                    self.work_left = 1
                    # while self.goto_tile == self.tile and self.goto_tile.get_type() in self.forbidden_tiles:
                    #     self.goto_tile = np.random.choice( self.get_visible_tiles(3) )

    def explore(self, _tiles):
        self.state = "EXPLORE"
        self.state_short = "X"

        if self.explore_goal == None:
            self.explore_goal = np.random.choice(_tiles)

        self.goto_position(self.explore_goal, state=self.state, state_short=self.state_short)
    
        if self.tile == self.explore_goal:
            self.explore_goal = None
            #Scout
            for t in self.get_visible_tiles(1):
                if t not in self.known_tiles:
                    self.known_tiles.append(t)
                    if t.food != None:
                        _to_sort = self.food_memory + [t.food]
                        def key(e):
                            return utils.distance2p(self.tile.middle, e.tile.middle)
                        _to_sort.sort(key=key)
                        self.food_memory = _to_sort

                    if t.is_river or t.get_type() == "SHALLOW_WATER":
                        _to_sort = self.water_memory + [t]
                        def key(e):
                            return utils.distance2p(self.tile.middle, e.middle)
                        _to_sort.sort(key=key)
                        self.water_memory = _to_sort[:min(len(_to_sort), self.water_memory_max)]
            self.state = "SCOUT"
            self.state_short = "Sct"
            self.work_left = 9

    def mate(self, other, forced_pregnancy=False):
        print("{} ({}) mate with {} ({})".format(self.name, self.sex, other.name, other.sex))
        console.console.print("{} ({}) mate with {} ({})".format(self.name, self.sex, other.name, other.sex))
        self.state = "MATE"
        self.work_left = np.random.randint(1, 9)
        if self.sex != other.sex and (np.random.random() < 0.3 or forced_pregnancy):
            if self.sex == 'F' and not self.pregnant:
                print("{} got pregnant!".format(self.name))
                console.console.print("{} got pregnant!".format(self.name))
                self.pregnant = True
                self.gestation = 240 * (np.random.randint(20, 26)) + np.random.randint(0, 240)
                self.child_other_parent = other
            elif other.sex == 'F' and not other.pregnant:
                print("{} got pregnant!".format(other.name))
                console.console.print("{} got pregnant!".format(other.name))
                other.pregnant = True
                other.gestation = 240 * (np.random.randint(20, 26)) + np.random.randint(0, 240)
                other.child_other_parent = self
        self.libido  = 0
        other.libido = 0

    def give_birth(self):
        self.state = "GIVE BIRTH"

        child = Entity(self.simu, self.tile)

        if child.sex == "M":
            f = open("./data/files/namelist_male.txt", 'r')
            lines = f.readlines()
            first_name = np.random.choice(lines)[:-1]
            if np.random.random() < 0.25:
                middle_name = np.random.choice(lines)[:-1]
            else:
                middle_name = ""
        else:
            f = open("./data/files/namelist_female.txt", 'r')
            lines = f.readlines()
            first_name = np.random.choice(lines)[:-1]
            if np.random.random() < 0.25:
                middle_name = np.random.choice(lines)[:-1]
            else:
                middle_name = ""

        family_name = np.random.choice([self.all_names[2], self.child_other_parent.all_names[2]])

        name = [first_name, middle_name, family_name]

        child.set_name(name)

        child.parents = (self, self.child_other_parent)

        self.pregnant = False

        self.children.append(child)
        self.child_other_parent.children.append(child)

        if np.random.random() < 0.5:
            child.grow_food_tile = child.parents[0].grow_food_tile
        else:
            child.grow_food_tile = child.parents[1].grow_food_tile
        
        self.work_left = np.random.randint(6, 6*12)

        self.child_other_parent = None

        self.simu.add_entity(child)
        self.simu.nb_birth += 1

    #BEHAVIOURS

    def b_drink(self):
        if self.thirst < self.thirst_max*0.35 or self.has_to_drink:
            self.has_to_drink = True
            if self.thirst >= self.thirst_max * 0.95:
                self.has_to_drink = False
                return False
            elif "WATER" in self.inventory and self.inventory["WATER"] > 0:
                self.drink_from_inventory()
                return True
            else:
                return False
            return False

    def b_collect_water(self):
        if "WATER" not in self.inventory or self.inventory["WATER"] < self.max_water_inventory:
            t = self.near_water()
            if t != None:
                self.collect_water()
                self.reset_path()
                return True
            else:
                for _t in self.water_memory:
                    self.goto_water(_t)
                    return True
                return False
        else:
            return False

    def b_eat(self):
        if self.nutrition < self.nutrition_max*0.35 or self.has_to_eat:
            self.has_to_eat = True
            if self.nutrition >= self.nutrition_max * 0.95:
                self.has_to_eat = False
                return False
            elif "FOOD" in self.inventory and self.inventory["FOOD"] > 0:
                self.eat_from_inventory()
                return True
            else:
                return False
        else:
            return False

    def b_harvest_food(self):
        if "FOOD" not in self.inventory or self.inventory["FOOD"] < self.max_food_inventory:
            f = self.near_food()
            if f != None:
                self.harvest_food(f)
                self.reset_path()
                return True
            else:
                for _f in self.food_memory:
                    if _f.available:
                        self.goto_food(_f)
                        return True
                return
        else:
            return False

    def b_search_and_mate(self):
        if self.libido >= 100:
            closest_other = self.near_other()
            if closest_other != None and closest_other.libido >= 100 and closest_other not in self.foes and (closest_other in self.relations and self.relations[closest_other] > 0):
                self.mate(closest_other)
                self.reset_path()
                return True
            else:
                others = self.get_closest_entities(self.get_visible_tiles(1))
                if others:
                    for o in others:
                        if o.libido >= 100 and o not in self.foes and (o in self.relations and self.relations[o] > 0):
                            self.goto_position(o.tile, state="GOTO MATE", state_short="GTMate")
                            return True
                    return False
                else:
                    return False
        else:
            return False

    def b_social_interaction(self):

        self.form_relations_with_surroundings()

        if np.random.random() >= p.behaviour_params["SOCIAL_INTERACTION_CHANCE"]:
            return False

        self.state = "SOCIAL INTERACTION"
        self.state_short = "SocInt"

        _interactioninfo = ""

        others = self.get_closest_entities(self.get_visible_tiles(2))
        if others:
            _c = np.random.choice(others)
            _modif = 0.0
            if _c in self.friends:
                _interactioninfo = "friend"
                if np.random.random() >= p.behaviour_params["SOCIAL_INTERACTION_POSITIVE_REENFORCMENT_CHANCE"]:
                    _modif = self.subb_befriend(_c)
                else:
                    _modif = self.subb_insult(_c)
            elif _c in self.foes:
                _interactioninfo = "foe"
                if np.random.random() >= p.behaviour_params["SOCIAL_INTERACTION_POSITIVE_REENFORCMENT_CHANCE"]:
                    _modif = self.subb_insult(_c)
                else:
                    _modif = self.subb_befriend(_c)
            else:
                _interactioninfo = "neutral"
                if np.random.random() >= p.behaviour_params["SOCIAL_INTERACTION_NEUTRAL_REENFORCMENT_CHANCE"]:
                    _modif = self.subb_befriend(_c)
                else:
                    _modif = self.subb_insult(_c)

            console.console.print("{} interacted with {} ({}{}{})".format(self.name_short, _c.name_short, _interactioninfo, "+" if _modif>=0 else "",round(_modif*100.0, 1)))

            self.work_left = np.random.randint(1, 6);

            return True

        return False

    def subb_insult(self, _other):
        if not _other in self.relations.keys():
            self.relations[_other] = 0.0
        if not self in _other.relations.keys():
            _other.relations[self] = 0.0

        modif = -utils.random_range(0.001, 0.015)
        self.relations[_other] += modif
        _other.relations[self] += modif * 1.5

        return modif


    def subb_befriend(self, _other):
        if not _other in self.relations.keys():
            self.relations[_other] = 0.0
        if not self in _other.relations.keys():
            _other.relations[self] = 0.0

        modif = utils.random_range(0.001, 0.015)
        self.relations[_other] += modif
        _other.relations[self] += modif * 1.5

        return modif


    def b_explore(self):
        # print(self.name, str(self.goto_tile), str(self.tile))
        if len(self.food_memory) <= 0 or len(self.water_memory) <= 0 or len(self.known_tiles) < self.exploration_satistaction:
            radius_tiles = [t for t in self.get_visible_tiles(2) if t.get_type() != "SHALLOW_WATER"]
            # _tiles = [t for t in radius_tiles if (t not in self.known_tiles and t.get_type() not in self.forbidden_tiles)]
            if len(radius_tiles) <= 0 and self.explore_goal == None:
                return False
            else:
                self.explore(radius_tiles)
                return True

            # if len(radius_tiles) <= 0 and self.explore_goal == None:
            #     radius_tiles = [t for t in self.get_visible_tiles(2)]
            #     if len(radius_tiles) <= 0:
            #         return False
            #     else:
            #         self.explore(radius_tiles)
            #         return True
            # else:
            #     self.explore(radius_tiles)
            #     return True
        else:
            return False

    def b_idle(self):
        self.random_walk()
        return True

    def b_dig_well(self):
        pass

    def b_plant_food(self):
        # closest_mem_food = self.get_closest_foods([f.tile for f in self.food_memory])
        if (not self.grow_food_tile 
            and len(self.known_tiles) > self.exploration_satistaction
            # and len(self.food_memory) < 6
            # and not (closest_mem_food and utils.distance2p(self.tile, closest_mem_food[0].tile) < 15)
            and len(self.friends) > 2
            # and not [fr for fr in self.friends if fr.grow_food_tile]
            ):

            ts = [_t for _t in self.known_tiles if (_t.get_type()=="GRASS" and not _t.is_forest and not _t.is_river)]
            if len(ts) >= 4:
                _p = []
                tilelist = list(set().union(self.grid.shallow_water_tiles, self.grid.river_tiles))
                for _t in ts:
                    dist = utils.distance2p(_t.middle, self.get_closest_water(tilelist, center=_t)[0].middle)
                    _p.append(1/dist)
                _p = [__p/sum(_p) for __p in _p]
                ch = np.random.choice(ts, p=_p)
                ideal_tiles = [(ch.x, ch.y), (ch.x+1, ch.y), (ch.x, ch.y+1), (ch.x+1, ch.y+1), (ch.x+2, ch.y), (ch.x+2, ch.y+1), (ch.x+2, ch.y+2), (ch.x+1, ch.y+2), (ch.x, ch.y+2)]
                for _ch in ideal_tiles:
                    if not self.grid.out_of_bound(_ch) and self.grid.get(_ch).get_type() == "GRASS" and not self.grid.get(_ch).is_river and not self.grid.get(_ch).is_forest:
                        self.grow_food_tile.append(self.grid.get(_ch))
                if len(self.grow_food_tile) != len(ideal_tiles):
                    self.grow_food_tile = []
                    return False
                else:
                    for fr in self.friends:
                        if fr.grow_food_tile == []:
                            fr.grow_food_tile = self.grow_food_tile
                    console.console.print("{} chose {} field!".format(self.name, "her" if self.sex=="F" else "his"))
            else:
                return False
        if self.grow_food_tile and len(self.planted_food_list) <= len(self.grow_food_tile):
            if self.grow_food_tile:
                if self.goto_plant_tile != None:
                    if self.goto_plant_tile in self.tile.get_neighbours() or self.goto_plant_tile == self.tile:
                        self.planted_food_list.append(PlantedFood(self.simu, self.goto_plant_tile, self.goto_plant_tile.get_type(), self))
                        self.state       = "PLANT"
                        self.state_short = "Pl"
                        self.work_left = np.random.randint(6, 10)
                        self.goto_plant_tile = None
                        # self.reset_path()
                        return True
                    else:
                        self.goto_position(self.goto_plant_tile, state="GOTO PLANT", state_short="GTPl")
                        return True
                else:
                    grfd = [t for t in self.grow_food_tile if t.food == None]
                    if grfd:
                        self.goto_plant_tile = grfd[0]
                        self.goto_position(self.goto_plant_tile, state="GOTO PLANT", state_short="GTPl")
                        return True
                    else:
                        return False
            else:
                return False
        else:
            return False

    def set_name(self, names):
        self.all_names = names
        self.name = self.all_names[0] + " " + (self.all_names[1][0] + ". " if self.all_names[1] != "" else "") + self.all_names[2]
        self.name_short = self.all_names[0][0] + "." + (self.all_names[1][0] + ". " if self.all_names[1] != "" else "") + self.all_names[2]

    #GLOBALS
    @staticmethod
    def spawn_randomly(simu, name=None):
        t = simu.grid.get_random_border()
        while t.get_type() in Entity.get_forbidden_tiles_base() + ["SHALLOW_WATER"]:
            t = simu.grid.get_random_border()
        
        e = Entity(simu, t)

        if name == None:
            if e.sex == "M":
                f = open("./data/files/namelist_male.txt", 'r')
                lines = f.readlines()
                first_name = np.random.choice(lines)[:-1]
                if np.random.random() < 0.25:
                    middle_name = np.random.choice(lines)[:-1]
                else:
                    middle_name = ""
            else:
                f = open("./data/files/namelist_female.txt", 'r')
                lines = f.readlines()
                first_name = np.random.choice(lines)[:-1]
                if np.random.random() < 0.25:
                    middle_name = np.random.choice(lines)[:-1]
                else:
                    middle_name = ""

            f = open("./data/files/familynames.txt", 'r')
            family_name = np.random.choice(f.readlines())[:-1]
            f.close()

            name = [first_name, middle_name, family_name]

            e.set_name(name)

        simu.add_entity(e)

    @staticmethod
    def spawn_here(simu, x, y, name=None):
        if name == None:
            f = open("./data/files/namelist.txt", 'r')
            name = np.random.choice(f.readlines())[0] + '.'
            if np.random.random() < 0.5:
                f = open("./middlenames.txt", 'r')
                name += np.random.choice(f.readlines())[0] + '.'
            f = open("./data/files/familynames.txt", 'r')
            name += np.random.choice(f.readlines())[:-1]
            f.close()
        e = Entity(simu, simu.grid.grid[x][y], name)
        simu.add_entity(e)

    @staticmethod
    def get_forbidden_tiles_base():
        return ["DEEP_WATER"]

    @staticmethod
    def randomise_state(entity):
        entity.health  = (entity.health_max*0.5) + np.random.random()*(entity.health_max*0.5)
        
        entity.age_raw = np.random.randint(240*30, int(240*30*2.5))
        minutes = (entity.age_raw*10)%60
        hours = math.floor((entity.age_raw*10)/60)%24
        days = math.floor(math.floor((entity.age_raw*10)/60)/24)
        entity.age = round(days + (hours/24), 1)
        
        entity.inventory["FOOD"]  = entity.max_food_inventory*np.random.random()
        entity.inventory["WATER"] = entity.max_water_inventory*np.random.random()

        entity.nutrition = entity.nutrition_max*(0.5 + np.random.random()*0.5)
        entity.thirst    = entity.thirst_max*(0.5 + np.random.random()*0.5)

        entity.libido  = np.random.randint(0, 70)

    @staticmethod
    def randomise_family(e, ent_list):
        if np.random.random() < 0.25:
            choices = [_e for _e in ent_list if _e.age>=30 and _e != e and _e.children == []]
            if len(choices) >= 2:
                np.random.shuffle(choices)
                c1 = choices[0]
                second_choice = [c for c in choices if c.sex != choices[0].sex]
                if second_choice:
                    c2 = second_choice[0]
                    e.parents = (c1, c2)
                    e.parents[0].child_other_parent = e.parents[1]
                    e.parents[1].child_other_parent = e.parents[0]

                    e.age_raw = np.random.randint(240, int(240*30))
                    minutes = (e.age_raw*10)%60
                    hours = math.floor((e.age_raw*10)/60)%24
                    days = math.floor(math.floor((e.age_raw*10)/60)/24)
                    e.age = round(days + (hours/24), 1)


                    c1.children.append(e)
                    c2.children.append(e)

                    e.all_names[2] = np.random.choice([c1.all_names[2], c2.all_names[2]])

                    if np.random.random() < 0.3:
                        if c1.sex == "F":
                            c1.pregnant = True
                            c1.gestation = 240 * (np.random.randint(6, 26)) + np.random.randint(0, 240)
                            # c1.gestation /= 1000
                            c1.libido  = 0
                        elif c2.sex == "F":
                            c2.pregnant = True
                            c2.gestation = 240 * (np.random.randint(6, 26)) + np.random.randint(0, 240)
                            # c2.gestation /= 1000
                            c2.libido  = 0

                    c1.child_other_parent = c2
                    c2.child_other_parent = c1

                    # family = [e, e.parents[0], e.parents[1]]
                    #move_to; self.work_left = 0;

                    if np.random.random() < 0.5:
                        center = e.parents[0]
                        other  = e.parents[1]
                    else:
                        center = e.parents[1]
                        other  = e.parents[0]

                    for _e in [other, e]:
                        _t = center.tile.get_neighbours(restriction=_e.forbidden_tiles)
                        if _t:
                            _e.move_to(np.random.choice(_t))
                            _e.work_left = 0

    @staticmethod
    def randomise_state_and_family(e, ent_list):
        Entity.randomise_state(e)
        Entity.randomise_family(e, ent_list)

    @staticmethod
    def randomise_state_and_family_all(ent_list):
        for e in ent_list:
            Entity.randomise_state_and_family(e, ent_list)
            # print(e.age_raw, e)



class Food(object):
    """docstring for Food"""
    def __init__(self, simu, tile, biome="GRASS"):
        super(Food, self).__init__()
        self.tile = tile
        self.tile.set_food(self)
        self.simu = simu

        self.planted_food = False

        self.simu.add_food(self)

        self.color = (255, 8, 0, 255)

        self.biome = biome

        if self.biome in ["GRASS"]:
            self.resource_max = np.random.randint(4, 8) * 240 + np.random.randint(0, 240)
            self.resource_qtt = self.resource_max
            self.regrow_rate = (0.4 + np.random.random()*0.2)
        elif self.biome in ["HILL"]:
            self.resource_max = np.random.randint(8, 22) * 240 + np.random.randint(0, 240)
            self.resource_qtt = self.resource_max
            self.regrow_rate = (0.2 + np.random.random()*0.4)

        self.lifespan = 240 * 30 * np.random.randint(1, 3) + np.random.randint(1, 240)*np.random.randint(1, 30)
        # self.lifespan = 0

        self.available = True

        self.dead = False

        self.act_tck_cnt = 0

    def update(self):
        if self.resource_qtt <= 0:
            self.available = False
            self.dead = True

        if self.dead:
            self.resource_qtt = 0
            self.available = False
            self.dead = True
            self.tile.set_food(None)

        self.lifespan -= 1
        if self.lifespan > 0:
            self.resource_qtt = min(self.resource_max, self.resource_qtt+self.regrow_rate)
        else:
            self.resource_qtt = min(self.resource_max, self.resource_qtt-(self.regrow_rate/2))

        if not self.available and self.resource_qtt > self.resource_max*0.95:
            self.available = True

    @staticmethod
    def spawn_randomly(simu, biome):
        _try = 0
        t = np.random.choice([t for t in simu.grid.get_tile_1D_list() if t.get_type() in biome])
        # print(biome, t.get_type())
        
        while (t.food != None or t.get_type() not in biome or t.tree != None or t.is_river) and _try < 1000:
            _try += 1
            t = np.random.choice([t for t in simu.grid.get_tile_1D_list() if t.get_type() in biome])

        f = Food(simu, t, t.get_type())

    @staticmethod
    def get_good_tiles():
        return ["GRASS", "HILL"]

class ForestFood(Food):
    def __init__(self, simu, tile, biome):
        super(ForestFood, self).__init__(simu, tile, biome)

        self.resource_max = np.random.randint(0, 2) * 240 + np.random.randint(0, 240)
        self.resource_qtt = 1
        self.regrow_rate = (1.0 + np.random.random()*0.5)

        self.available = False

        self.lifespan = 240 * np.random.randint(4, 8) + np.random.randint(1, 240)*np.random.randint(1, 30)
        
    
class PlantedFood(Food):
    """docstring for PlantedFood"""
    def __init__(self, simu, tile, biome, creator):
        super(PlantedFood, self).__init__(simu, tile, biome)
        self.planted_food = True

        self.creator = creator

        self.tile.is_field = True

        self.resource_max = np.random.randint(3, 6) * 240 + np.random.randint(0, 240)
        self.resource_qtt = 1
        self.regrow_rate = (1.2 + np.random.random()*0.6)

        self.lifespan = 240 * np.random.randint(10, 16) + np.random.randint(1, 240)*np.random.randint(1, 30)

        self.available = False

    def update(self):

        if self.resource_qtt <= 0:
            self.available = False
            self.dead = True

        if self.dead:
            self.resource_qtt = 0
            self.available = False
            self.dead = True
            self.tile.set_food(None)
            self.creator.planted_food_list.remove(self)

        self.lifespan -= 1
        if self.lifespan > 0:
            self.resource_qtt = min(self.resource_max, self.resource_qtt+self.regrow_rate)
        else:
            self.resource_qtt = min(self.resource_max, self.resource_qtt-(self.regrow_rate/2))

        if not self.available and self.resource_qtt == self.resource_max:#> self.resource_max*0.95:
            self.available = True




class Tree(object):
    """docstring for Tree"""
    def __init__(self, simu, tile, randomness=False):
        super(Tree, self).__init__()
        self.simu = simu
        self.tile = tile
        self.simu.trees.append(self)

        self.act_tck_cnt = 0

        self.lifespan = 240 * 30 * np.random.randint(10, 16) + np.random.randint(1, 240)*np.random.randint(1, 30)
        # self.lifespan = int(self.lifespan/1000)
        self.cycle = 240 * np.random.randint(4, 10) + np.random.randint(0, 240)
        # self.cycle = int(self.cycle/1000)
        self.age = 0

        if randomness:
            self.age = np.random.randint(0, int(round(self.lifespan * 0.6)))

        # print(self.lifespan, self.cycle)

        self.dead = False

    def update(self):
        self.age += 1
        # if self.age > self.lifespan:
        #     if np.random.random() < 0.1:
        #         self.dead = True

        # if self.dead:
        #     self.tile.set_tree(None)
        #     return

        if self.age%(self.cycle) == 0:
            if np.random.random() < 0.1:
                av_n = [n for n in self.tile.get_neighbours(dn=True) if (n.food == None and not n.is_river and n.get_type() in Food.get_good_tiles())]
                if av_n:
                    prob = []
                    for n in av_n:
                        if n.get_type() in ["GRASS"]:
                            prob.append(3)
                        elif n.get_type() in ["HILL"]:
                            prob.append(2)
                        else:
                            prob.append(1)
                    prob = [_p/sum(prob) for _p in prob]

                    t = np.random.choice(av_n, p=prob)
                    if t.tree == None and t.food == None:
                        t.set_food(ForestFood(self.simu, t, t.get_type()))
            # elif np.random.random() < 0.3:
            #     av_n = [n for n in self.tile.get_neighbours(dn=True) if (not n.is_river and n.get_type() in Tree.get_good_tiles())]
            #     if av_n:
            #         prob = []
            #         for n in av_n:
            #             if n.get_type() in ["GRASS"]:
            #                 prob.append(3)
            #             elif n.get_type() in ["HILL", "SAND"]:
            #                 prob.append(2)
            #             elif n.get_type() in ["MOUNTAIN"]:
            #                 prob.append(1)
            #             else:
            #                 prob.append(1)
            #         prob = [_p/sum(prob) for _p in prob]

            #         t = np.random.choice(av_n, p=prob)
            #         if t.tree == None and t.food == None:
            #             t.set_tree(Tree(self.simu, t))


        

    @staticmethod
    def get_good_tiles():
        return ["GRASS", "MOUNTAIN", "HILL", "SAND"]

class Building(object):
    """docstring for Building"""
    def __init__(self, creator, tile):
        super(Building, self).__init__()
        self.creator = creator
        self.tile = tile
        self.tile.set_building(self)

        self.creator.buildings.append(self)
        self.creator.owned_buildings.append(self)
        
        self.name = "Building"

        self.image = None

    def get_image(self):
        return self.image

    def get_name(self):
        return self.name

    def update(self):
        pass

class GatheringPlace(Building):
    """docstring for GatheringPlace"""
    def __init__(self, creator, tile):
        super(GatheringPlace, self).__init__(creator, tile)

        self.name = "GatheringPlace"
        self.image = pygame.image.load("./data/images/fireplace.png")


if __name__ == '__main__':
    e = Entity(env.Grid(p.parameters["GRID_W"], p.parameters["GRID_H"]))

    vt = e.get_visible_tiles(0)
    print(e.tile.x, e.tile.y)
    for v in vt:
        print(v.x, v.y)