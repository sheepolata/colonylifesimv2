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
import buildings

class Community(object):
    """docstring for Community"""
    def __init__(self, simu, name, chief):
        super(Community, self).__init__()
        self.simu = simu
        self.simu.communities.append(self)
        self.name = name
        self.chief = chief

        self.color = p.get_next_community_color()
        
        self.members = [self.chief]

        self.fields = []


    def update(self):
        if self.chief.dead:
            self.chief = None
        self.members = [x for x in self.members if not x.dead]

        if self.chief == None:
            self.chief = np.random.choice(self.members)

    def add_member(self, m):
        m.grow_food_tile = self.fields
        m.community = self
        self.members.append(m)

    def add_members(self, m_list):
        for m in m_list:
            self.add_member(m)

    def update_fields(self, new_fields):
        self.fields = new_fields
        for m in self.members:
            m.grow_food_tile = self.fields

    def add_fields(self, new_fields):
        for f in new_fields:
            if f not in self.fields:
                self.fields.append(f)

    def rm_member(self, m):
        if m in self.members:
            m.grow_food_tile = []
            self.members.remove(m)
        else:
            print("DEBUG: Community.rm_member(self, m): m ({}} is not a member".format(m.name))

    def set_chief(self, nc):
        if nc in self.members:
            self.chief = nc
        else:
            print("DEBUG: Community.set_chief(self, nc): nc ({}} is not a member".format(nc.name))



class Entity(object):
    """docstring for Entity"""
    def __init__(self, simulation, tile=None, name=("Ent", "", "Basename")):
        super(Entity, self).__init__()
        self.simu = simulation
        self.grid = self.simu.grid

        self.forbidden_tiles = Entity.get_forbidden_tiles_base()

        self.social_vector = np.random.choice(p.social_features_list, p.sim_params["SOCIAL_FEATURES"], replace=False)

        self.traits = {}
        for k in p.all_traits:
            self.traits[k] = np.random.choice(p.all_traits[k][0], p=p.all_traits[k][1])

        # print(self.traits)

        self.stats_raw = {}
        self.stats_norm = {}
        self.stats_bonus = {}

        self.set_stat("STRENGTH"    , np.random.randint(8, 15))
        if self.traits["STRENGTH"] == "STRONG":
            self.set_stat("STRENGTH", self.stats_raw["STRENGTH"] + 2)
        elif self.traits["STRENGTH"] == "WEAK":
            self.set_stat("STRENGTH", self.stats_raw["STRENGTH"] - 2)

        self.set_stat("CONSTITUTION", np.random.randint(8, 15))
        self.set_stat("DEXTERITY", np.random.randint(8, 15))

        self.all_names = name
        self.name = self.all_names[0] + " " + (self.all_names[1][0] + ". " if self.all_names[1] != "" else "") + self.all_names[2]

        self.goto_tile = None
        self.explore_goal = None
        self.goto_plant_tile = None
        self.path = []

        self.known_tiles = []
        self.total_tiles = len(self.simu.grid.get_tile_1D_list())
        # self.total_reachable_tiles = len([t for t in self.simu.grid.get_tile_1D_list() if t.get_type() not in self.forbidden_tiles])
        self.total_reachable_tiles = len([t for t in self.simu.grid.get_tile_1D_list() if t.get_type() not in self.forbidden_tiles+["SHALLOW_WATER"]])
        self.exploration_satistaction = int(self.total_reachable_tiles * (0.25 + (np.random.random() * 0.25)))
        
        # if "CURIOSITY" in [x.feature for x in self.social_vector]:
        if self.traits["CURIOSITY"] == "CURIOUS":
            self.exploration_satistaction = min(self.exploration_satistaction*1.25, self.total_reachable_tiles)
        
        self.visible_tiles = [[], [], [], [], []]

        if tile != None:
            self.tile = tile
        else:
            self.tile = np.random.choice(self.grid.grid[np.random.randint(0, len(self.grid.grid[0]))])
        self.tile.add_entity(self)

        self.act_tck_cnt = 0
        self.chck_surrounding_tmr = 0
        self.action_cooldown = 0

        self.state = "NONE"
        self.state_short = "NA"

        self.work_left = 0

        #Vision in tile
        self.vision_radius = 8

        self.dead = False

        self.health_max = int(round(np.random.randint(90, 111) * self.stats_bonus["CONSTITUTION"]))
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
        self.max_food_inventory_factor = 2 * self.stats_bonus["STRENGTH"]
        self.max_food_inventory  = round(self.nutrition_max * self.max_food_inventory_factor)
        self.has_to_harvest_food = False

        self.food_eaten_per_tick = (self.nutrition_max/6.0)
        self.max_food_harvested  = (self.nutrition_max/20.0)
        self.has_to_eat = False

        self.food_memory = []
        self.food_memory_max = -1
        self.planted_food_list = []

        self.grow_food_tile = []

        self.thirst_max  = 720 #3 days, 1 day == 240
        self.thirst      = self.thirst_max
        self.thirst_rate = 0.8+(np.random.random()*0.4)
        self.max_water_inventory_factor = 3 * self.stats_bonus["STRENGTH"]
        self.max_water_inventory = round(self.thirst_max*self.max_water_inventory_factor)
        self.has_to_collect_water = False

        self.water_drank_per_tick = (self.thirst_max/3.0)
        self.max_water_harvested  = (self.thirst_max/1.5)
        self.has_to_drink = False

        self.water_memory = []
        self.water_memory_max = 1

        #Social
        self.friends = []
        self.foes    = []
        self.relations = {}

        # print(self.all_names, [f.feature for f in self.social_vector])

        self.buildings       = []
        self.owned_buildings = []
        self.community = None

        self.job = BasicJob(self)

    def update(self):
        if self.act_tck_cnt >= p.sim_params["ACTION_TICK"]:
            self.act_tck_cnt = 0

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

                for b in self.job.behaviours_by_priority:#self.behaviours_by_priority:
                    if b():
                        break

                if self.chck_surrounding_tmr >= 5:
                    self.chck_surrounding_tmr = 0
                    self.check_surrounding()
                else:
                    self.chck_surrounding_tmr += 1

                for n in self.grid.get_neighbours_of(self.tile) + [self.tile]:
                    if n not in self.known_tiles:
                        self.known_tiles.append(n)

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


        else:
            self.act_tck_cnt += 1

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

        for k in self.relations:
            if self.relations[k] > 0 and self.relations[k] < p.sim_params["FRIEND_FOE_TRESH"]:
                self.relations[k] -= p.sim_params["FRIEND_FOE_TRESH"]/100
            elif self.relations[k] < 0 and self.relations[k] > -p.sim_params["FRIEND_FOE_TRESH"]:
                self.relations[k] += p.sim_params["FRIEND_FOE_TRESH"]/100


        ent_sorted = self.get_closest_entities(self.get_visible_tiles(1))
        for e in ent_sorted:
            if e == self:
                continue
            if e not in self.relations:
                self.relations[e] = 0.0
            simil = p.SocialFeature.list_similatiry(self.social_vector, e.social_vector)
            self.relations[e] += simil
            self.relations[e] = utils.clamp(self.relations[e], -p.sim_params["FRIEND_FOE_TRESH"]*2, p.sim_params["FRIEND_FOE_TRESH"]*2)

        for e in self.friends:
            for fr in e.friends:
                if e == self:
                    continue
                if fr not in self.relations:
                    self.relations[fr] = p.sim_params["FRIEND_FOE_TRESH"]/100
                self.relations[fr] += p.sim_params["FRIEND_FOE_TRESH"]/100
            for fr in e.foes:
                if e == self:
                    continue
                if fr not in self.relations:
                    self.relations[fr] = -p.sim_params["FRIEND_FOE_TRESH"]/100
                self.relations[fr] -= p.sim_params["FRIEND_FOE_TRESH"]/100
        for e in self.foes:
            for fr in e.friends:
                if e == self:
                    continue
                if fr not in self.relations:
                    self.relations[fr] = -p.sim_params["FRIEND_FOE_TRESH"]/100
                self.relations[fr] -= p.sim_params["FRIEND_FOE_TRESH"]/100
            for fr in e.foes:
                if e == self:
                    continue
                if fr not in self.relations:
                    self.relations[fr] = p.sim_params["FRIEND_FOE_TRESH"]/100
                self.relations[fr] += p.sim_params["FRIEND_FOE_TRESH"]/100

        for e in self.relations:
            if e not in self.friends and e not in self.foes:
                if self.relations[e] > p.sim_params["FRIEND_FOE_TRESH"]:
                    self.friends.append(e)
                    console.console.print("{} and {} are friends!".format(self.name, e.name))
                elif self.relations[e] < -p.sim_params["FRIEND_FOE_TRESH"]:
                    self.foes.append(e)
                    console.console.print("{} and {} are foes!".format(self.name, e.name))
            elif e in self.friends and self.relations[e] <= p.sim_params["FRIEND_FOE_TRESH"]:
                self.friends.remove(e)
                console.console.print("{} and {} are not friends anymore!".format(self.name, e.name))
            elif e in self.foes and self.relations[e] >= -p.sim_params["FRIEND_FOE_TRESH"]:
                self.foes.remove(e)
                console.console.print("{} and {} are not foes anymore!".format(self.name, e.name))

        self.friends = [x for x in self.friends if not x.dead]
        self.foes = [x for x in self.foes if not x.dead]

        # if self.friends or self.foes:
        #     print("{}\nFriends : {}\nFoes    : {}".format(self.name, [e.name for e in self.friends], [e.name for e in self.foes]))

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

        def key(e):
            return utils.distance2p(center.getXY(), e.getXY())
        of_type.sort(key=key)

        return [e for tile in of_type for e in tile.entities]

    def get_distance_to_closest_friend(self):
        if not self.friends:
            return float('inf')
        to_sort = [f.tile.getXY() for f in self.friends]
        def key(e):
            return utils.distance2p(self.tile.getXY(), e)
        to_sort.sort(key=key)

        return key(to_sort[0])

    def get_distance_to_closest_foe(self):
        if not self.foes:
            return float('inf')
        to_sort = [f.tile.getXY() for f in self.foes]
        def key(e):
            return utils.distance2p(self.tile.getXY(), e)
        to_sort.sort(key=key)

        return key(to_sort[0])

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
            if self.tile == _tile or self.path == []:
            # if self.tile in _tile.get_neighbours() or self.tile == _tile or self.path == []:
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
        self.state = "IDLE"
        self.state_short = "I"
        gath_places = [b for b in self.buildings if isinstance(b, buildings.GatheringPlace)]
        if gath_places and utils.distance2p(self.tile.getXY(), gath_places[0].tile.getXY()) > 25:
            self.goto_position(gath_places[0], state="BACKTOCAMP", state_short="GTGatPl")
        else:
            if self.goto_tile != None and self.goto_tile != self.tile:
                self.goto_position(self.goto_tile, state=self.state, state_short=self.state_short)
            else:
                #choose random tile in friends direction, foes opposite direction or random
                ok = False
                if self.friends and self.get_distance_to_closest_friend() > self.vision_radius:
                    choices = []
                    for i in range(len(self.friends)):
                        direction = utils.angle_from_points(self.tile.getXY(), np.random.choice(self.friends).tile.getXY())
                        direction = utils.random_angle_in_direction(direction, 45)
                        coord = utils.point_from_direction(self.tile.getXY(),
                                                    np.random.randint(1, self.vision_radius/2),
                                                    direction,
                                                    as_int = True
                                                )
                        if not self.grid.out_of_bound(coord):
                            # print("GT FRIEND", coord)
                            if self.grid.get(coord).get_type() not in self.forbidden_tiles:
                                choices.append( self.grid.get(coord) )
                    if choices:
                        ok = True
                        self.goto_tile = np.random.choice(choices)
                elif self.foes and self.get_distance_to_closest_foe() < self.vision_radius:
                    choices = []
                    for i in range(len(self.foes)):
                        direction = utils.angle_from_points(np.random.choice(self.foes).tile.getXY(), self.tile.getXY())
                        direction = utils.random_angle_in_direction(direction, 45)
                        coord = utils.point_from_direction(self.tile.getXY(),
                                                    np.random.randint(1, self.vision_radius/2),
                                                    direction,
                                                    as_int = True
                                                )
                        if not self.grid.out_of_bound(coord):
                            # print("GT FOE", coord)
                            if self.grid.get(coord).get_type() not in self.forbidden_tiles:
                                choices.append( self.grid.get(coord) )
                    if choices:
                        ok = True
                        self.goto_tile = np.random.choice(choices)
                if not ok:
                    _tiles = self.get_visible_tiles(3)
                    if _tiles:
                        self.goto_tile = np.random.choice( _tiles )

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

        if other not in self.relations:
            self.relations[other] = 1.0
        else:
            self.relations[other] += 1.0
    
        if self not in other.relations:
            other.relations[self] = 1.0
        else:
            other.relations[self] += 1.0

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
        child.parents[0].relations[child] = p.sim_params["FRIEND_FOE_TRESH"]*1.1
        child.parents[1].relations[child] = p.sim_params["FRIEND_FOE_TRESH"]*1.1

        self.pregnant = False

        self.children.append(child)
        self.child_other_parent.children.append(child)

        if np.random.random() < 0.5:
            child.grow_food_tile = child.parents[0].grow_food_tile
        else:
            child.grow_food_tile = child.parents[1].grow_food_tile

        if np.random.random() < 0.5:
            child.set_stat("STRENGTH", child.parents[0].stats_raw["STRENGTH"])
        else:
            child.set_stat("STRENGTH", child.parents[1].stats_raw["STRENGTH"])
        if np.random.random() < 0.05:
            child.set_stat("STRENGTH", child.stats_raw["STRENGTH"] + np.random.choice([-1, 1]))

        if np.random.random() < 0.5:
            child.set_stat("CONSTITUTION", child.parents[0].stats_raw["CONSTITUTION"])
        else:
            child.set_stat("CONSTITUTION", child.parents[1].stats_raw["CONSTITUTION"])
        if np.random.random() < 0.05:
            child.set_stat("CONSTITUTION", child.stats_raw["CONSTITUTION"] + np.random.choice([-1, 1]))
        
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
        if "WATER" not in self.inventory or self.inventory["WATER"] < (self.max_water_inventory/self.max_water_inventory_factor) or self.has_to_collect_water:
            self.has_to_collect_water = True
            if "WATER" not in self.inventory:
                self.inventory["WATER"] = 0
            if self.inventory["WATER"] == self.max_water_inventory:
                self.has_to_collect_water = False
                return False
            t = self.near_water()
            if t != None:
                self.collect_water()
                self.work_left = 1
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
        if "FOOD" not in self.inventory or self.inventory["FOOD"] < (self.max_food_inventory/self.max_food_inventory_factor) or self.has_to_harvest_food:
            self.has_to_harvest_food = True
            if "FOOD" not in self.inventory:
                self.inventory["FOOD"] = 0
            if self.inventory["FOOD"] == self.max_food_inventory:
                self.has_to_harvest_food = False
                return False
            f = self.near_food()
            if f != None:
                self.harvest_food(f)
                self.work_left = 1
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
        else:
            return False

    def b_idle(self):
        self.random_walk()
        return True

    def b_dig_well(self):
        pass

    def b_choose_field(self):
        if (not self.grow_food_tile 
            and len(self.known_tiles) > self.exploration_satistaction
            # and len(self.food_memory) < 6
            # and not (closest_mem_food and utils.distance2p(self.tile, closest_mem_food[0].tile) < 15)
            and len(self.friends) > 3
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
                    # for fr in self.friends:
                    #     if fr.grow_food_tile == []:
                    #         fr.grow_food_tile = self.grow_food_tile
                    console.console.print("{} chose {} field!".format(self.name, "her" if self.sex=="F" else "his"))
                    return True
            else:
                return False
        else:
            return False


    def b_plant_food(self):
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

    def b_invite_friend_to_field(self):
        friends_without_field = [x for x in self.friends if x.grow_food_tile == []]
        if friends_without_field and self.grow_food_tile != []:
            f = friends_without_field[0]
            if f in self.tile.entities + utils.flatten([x.entities for x in self.tile.get_neighbours()]):
                if f.grow_food_tile == []:
                    f.grow_food_tile = self.grow_food_tile
                    console.console.print("{} shared field with {}".format(self.name, f.name))
                    return True
                else:
                    return False
            else:
                self.goto_position(f.tile, state="GOTO FRIEND", state_short="GTFr")
                return True
        else:
            return False

    def b_form_community(self):
        if self.traits["LEADERSHIP"] == "LEADER" and self.community == None:
            friends_without_community = [x for x in self.friends if x.community == None]
            if len(friends_without_community) > 1:
                total_fields = utils.flatten([x.grow_food_tile for x in friends_without_community])
                self.community = Community(self.simu, "{}\'s community".format(self.name), self)
                # self.community.update_fields(total_fields)

                console.console.print("{} formed a community,\n{}!".format(self.name, self.community.name))

                return True
            else:
                return False
        else:
            return False

    def b_invite_to_community(self):
        if self.community == None:
            return False
        else:
            friends_without_community = [x for x in self.friends if x.community == None]
            if friends_without_community:
                f = friends_without_community[0]
                if f in self.tile.entities + utils.flatten([x.entities for x in self.tile.get_neighbours()]):
                    if f.community == None:
                        self.community.add_member(f)
                        console.console.print("{} invited {} to {} community,\n{}".format(self.name, f.name, "her" if self.sex=="F" else "his", self.community.name))
                        return True
                    else:
                        return False
                else:
                    self.goto_position(f.tile, state="GOTO FRIEND", state_short="GTFr")
                    return True

    def b_join_community(self):
        pass

    def set_name(self, name):
        self.all_names = name
        self.name = self.all_names[0] + " " + (self.all_names[1][0] + ". " if self.all_names[1] != "" else "") + self.all_names[2]

    def set_stat(self, stat, value):
        self.stats_raw[stat] = value
        self.stats_norm[stat] = utils.normalise(self.stats_raw[stat], 0, 20)
        self.stats_bonus[stat] = self.stats_norm[stat]*2.0

    def get_color(self):
        if self.community == None:
            return p.ENTITY_BASIC_COLOR
        else:
            return self.community.color

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

class Job(object):
    """docstring for Job"""
    def __init__(self, entity):
        super(Job, self).__init__()
        self.entity = entity
        self.name = "JOB"
        self.behaviours_by_priority = []

class BasicJob(Job):
    """docstring for BasicJob"""
    def __init__(self, entity):
        super(BasicJob, self).__init__(entity)
        self.name = "BASIC JOB"

        self.behaviours_by_priority = []

        self.behaviours_by_priority.append(self.entity.b_drink)
        self.behaviours_by_priority.append(self.entity.b_eat)
        self.behaviours_by_priority.append(self.entity.b_collect_water)
        self.behaviours_by_priority.append(self.entity.b_harvest_food)
        self.behaviours_by_priority.append(self.entity.b_search_and_mate)
        self.behaviours_by_priority.append(self.entity.b_choose_field)
        self.behaviours_by_priority.append(self.entity.b_invite_friend_to_field)
        self.behaviours_by_priority.append(self.entity.b_form_community)
        self.behaviours_by_priority.append(self.entity.b_invite_to_community)
        self.behaviours_by_priority.append(self.entity.b_plant_food)
        self.behaviours_by_priority.append(self.entity.b_explore)
        self.behaviours_by_priority.append(self.entity.b_idle)
        


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
            self.resource_max = np.random.randint(8, 12) * 240 + np.random.randint(0, 240)
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
        if self.act_tck_cnt >= p.sim_params["ACTION_TICK"]:
            self.act_tck_cnt = 0

            if self.resource_qtt <= 0:
                self.available = False
                self.dead = True

            if self.dead:
                self.resource_qtt = 0
                self.available = False
                self.dead = True
                self.tile.set_food(None)
                if isinstance(self, PlantedFood):
                    self.creator.planted_food_list.remove(self)

            self.lifespan -= 1
            if self.lifespan > 0:
                self.resource_qtt = min(self.resource_max, self.resource_qtt+self.regrow_rate)
            else:
                self.resource_qtt = min(self.resource_max, self.resource_qtt-(self.regrow_rate/2))

            if not self.available and self.resource_qtt > self.resource_max*0.95:
                self.available = True
        else:
            self.act_tck_cnt += 1

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

        self.resource_max = np.random.randint(2, 3) * 240 + np.random.randint(0, 240)
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

        self.lifespan = 240 * np.random.randint(4, 10) + np.random.randint(1, 240)*np.random.randint(1, 30)

        self.available = False




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
        if self.act_tck_cnt >= p.sim_params["ACTION_TICK"]:
            self.act_tck_cnt = 0
            
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


        else:
            self.act_tck_cnt += 1
        

    @staticmethod
    def get_good_tiles():
        return ["GRASS", "MOUNTAIN", "HILL", "SAND"]

        
        
if __name__ == '__main__':
    e = Entity(env.Grid(p.parameters["GRID_W"], p.parameters["GRID_H"]))

    vt = e.get_visible_tiles(0)
    print(e.tile.x, e.tile.y)
    for v in vt:
        print(v.x, v.y)