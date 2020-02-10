
import numpy as np
import pygame
import math

import parameters as p
import utils
import pathfinding as pf
import perlin
import life
import console

class Simulation(object):
    """docstring for Simulation"""
    def __init__(self, w, h, nb_ent, nb_food, nb_river):
        super(Simulation, self).__init__()
        self.nb_entities, self.nb_food, self.nb_river = nb_ent, nb_food, nb_river
        self.grid = Grid(w, h, self)

        self.entities = []
        self.foods = []
        self.trees = []
        self.buildings = []

        self.grid.generate_map_with_perlin(nb_river=nb_river)

        for i in range(nb_ent):
            life.Entity.spawn_randomly(self)
        for i in range(nb_food):
            life.Food.spawn_randomly(self, ["GRASS"])
        for i in range(int(nb_food/3)):
            life.Food.spawn_randomly(self, ["HILL"])

        life.Entity.randomise_state_and_family_all(self.entities)
        self.print_families()

        self.nb_dead  = 0
        self.nb_birth = 0

        self.date = 0


    def reset(self):
        self.foods = []
        self.entities = []
        self.trees = []
        self.buildings = []
        
        self.grid.rivers_path = []
        self.grid.river_tiles = []
        self.grid.shallow_water_tiles = []

        self.date = 0

        for x in range(self.grid.width):
            for y in range(self.grid.height):
                self.grid.grid[x][y].reset()

        self.grid.generate_map_with_perlin(nb_river=self.nb_river)

        self.entities = []
        for i in range(self.nb_entities):
            life.Entity.spawn_randomly(self)
        self.foods = []
        for i in range(self.nb_food):
            life.Food.spawn_randomly(self, ["GRASS"])
        for i in range(int(self.nb_food/3)):
            life.Food.spawn_randomly(self, ["HILL"])

        life.Entity.randomise_state_and_family_all(self.entities)
        self.print_families()

    def update(self):
        self.date += 1

        for b in self.buildings:
            b.update()
        for e in self.entities:
            e.update()
        for f in self.foods:
            f.update()
        for t in self.trees:
            t.update()

        # print(len(self.buildings))

        self.nb_dead += len([x for x in self.entities if x.dead])

        self.entities = [x for x in self.entities if not x.dead]
        self.foods = [x for x in self.foods if not x.dead]
        self.trees = [x for x in self.trees if not x.dead]
        self.buildings = [x for x in self.buildings if x.tile != None]

    def add_entity(self, e):
        self.entities.append(e)
        if e.parents != (None, None):
            console.console.print("{} is born !".format(e.name))
            console.console.print("{} and {} are now parents !".format(e.parents[0].name if e.parents[0] != None else "None", e.parents[1].name if e.parents[1] != None else "None"))
            print("{} and {} are now parents ! {} is born !".format(e.parents[0].name if e.parents[0] != None else "None", e.parents[1].name if e.parents[1] != None else "None", e.name))

    def add_food(self, f):
        self.foods.append(f)

    def add_building(self, b):
        self.buildings.append(b)

    def rm_building(self, b):
        self.buildings.remove(b)
        b.tile.set_building(None)

    def print_families(self):
        pass
        # for e in self.entities:
        #     print("{} ({}), {} days old ({})".format(e.name, e.sex, e.age, e))
        #     for c in e.children:
        #         print("     {} ({}), {} days old ({})".format(c.name, c.sex, c.age, e))



class Grid(object):
    """docstring for Grid"""
    def __init__(self, w, h, simu):
        super(Grid, self).__init__()
        self.width = w
        self.height = h
        self.simu = simu
        
        self.grid = []
        for x in range(w):
            tmp = []
            for y in range(h):
                tmp.append(Tile(x, y, self))
            self.grid.append(tmp)

        self.rivers_path = []
        self.river_tiles = []
        self.shallow_water_tiles = []

    def get_neighbours_of(self, tile, diag_neigh=False, restriction=[]):
        n = []
        if tile.x > 0:
            if self.grid[tile.x-1][tile.y].get_type() not in restriction:
                n.append(self.grid[tile.x-1][tile.y])
            if diag_neigh and tile.y > 0:
                if self.grid[tile.x-1][tile.y-1].get_type() not in restriction:
                    n.append(self.grid[tile.x-1][tile.y-1])
        if tile.x < self.width-1:
            if self.grid[tile.x+1][tile.y].get_type() not in restriction:
                n.append(self.grid[tile.x+1][tile.y])
            if diag_neigh and tile.y < self.height-1:
                if self.grid[tile.x+1][tile.y+1].get_type() not in restriction:
                    n.append(self.grid[tile.x+1][tile.y+1])
        if tile.y > 0:
            if self.grid[tile.x][tile.y-1].get_type() not in restriction:
                n.append(self.grid[tile.x][tile.y-1])
            if diag_neigh and tile.x < self.width-1:
                if self.grid[tile.x+1][tile.y-1].get_type() not in restriction:
                    n.append(self.grid[tile.x+1][tile.y-1])
        if tile.y < self.height-1:
            if self.grid[tile.x][tile.y+1].get_type() not in restriction:
                n.append(self.grid[tile.x][tile.y+1])
            if diag_neigh and tile.x > 0:
                if self.grid[tile.x-1][tile.y+1].get_type() not in restriction:
                    n.append(self.grid[tile.x-1][tile.y+1])

        return n

    def out_of_bound(self, *args):
        if len(args) == 1:
            return (args[0][0] >= self.width or args[0][0] < 0) or (args[0][1] >= self.height or args[0][1] < 0)
        elif len(args) == 2:
            return (args[0] >= self.width or args[0] < 0) or (args[1] >= self.height or args[1] < 0)
        else:
            return None

    def get(self, *args):
        if len(args) == 1:
            return self.grid[args[0][0]][args[0][1]]
        elif len(args) == 2:
            return self.grid[args[0]][args[1]]
        else:
            return None

    def get_random_border(self):
        if np.random.random() < 0.5:
            _x = np.random.choice([0, self.width-1])
            _y = np.random.randint(0, self.height)
        else:
            _x = np.random.randint(0, self.width)
            _y = np.random.choice([0, self.height-1])
        return self.grid[_x][_y]

    def get_opposite_border(self, t):
        _x, _y = 0, 0
        if t.x == 0:
            _x = self.width-1
        elif t.x == self.width-1:
            _x = 0
        else:
            _x = 2*int(self.width/2) - t.x

        if t.y == 0:
            _y = self.height-1
        elif t.y == self.height-1:
            _y = 0
        else:
            _y = 2*int(self.height/2) - t.y

        return self.grid[_x][_y]

    def get_tile_1D_list(self):
        res = []
        for x in range(self.width):
            for y in range(self.height):
                res.append(self.grid[x][y])
        return res

    def generate_rivers(self, river_nb=1, waypoint_nb=2):
        def random_tile_at_range(grid, start, radius, forbidden):
            vis = []
            for x in range(start.x - radius, start.x + radius):
                for y in range(start.y - radius, start.y + radius):
                    if not grid.out_of_bound(x, y):
                        t = grid.grid[x][y]
                        if t != start and abs(utils.distance2p((start.x, start.y), (t.x, t.y)) - radius) < 1 and t.get_type() not in forbidden:
                            vis.append(t)
            if vis == []:
                return None
            return np.random.choice(vis)

        for i in range(river_nb):
            start = self.get_random_border()
            while start.get_type() in ["HILL", "MOUNTAIN"]:
                start = self.get_random_border()

            waypoints = [start]

            for j in range(1, waypoint_nb+1):
                curr = waypoints[j-1]
                t = random_tile_at_range(self, curr, int(((self.width+self.height)/2)/waypoint_nb), ["MOUNTAIN"])
                if t == None:
                    break
                waypoints.append(t)

            waypoints.append(self.get_opposite_border(start))

            river = []

            for j in range(len(waypoints)-1):
                _start = waypoints[j]
                _goal = waypoints[j+1]
                way = pf.astar(_start, _goal, self)
                for w in way:
                    river.append(w)

            for r in river:
                r.set_type("SHALLOW_WATER")


    def generate_mountains(self, chain_nb=5, source_nb=12, mount_thresh=10, iteration=1000):
        changed = []
        for chain in range(chain_nb):
            start = np.random.choice(self.grid[np.random.randint(0, len(self.grid[0]))])
            points = [start]

            def random_tile_in_range(grid, start, radius):
                vis = []
                for x in range(start.x - radius, start.x + radius):
                    for y in range(start.y - radius, start.y + radius):
                        if not grid.out_of_bound(x, y):
                            t = grid.grid[x][y]
                            if t != start and utils.distance2p((start.x, start.y), (t.x, t.y)) < radius:
                                vis.append(t)
                return np.random.choice(vis)

            for i in range(1, source_nb):
                prev = points[i-1]
                points.append(random_tile_in_range(self, prev, 4))

            for i in range(len(points)):
                todo_list = [points[i]]
                j = 0

                while todo_list:
                    if j >= iteration:
                        break

                    curr = todo_list[0]
                    changed.append(curr)
                    todo_list = todo_list[1:]
                    n = self.get_neighbours_of(curr)

                    for x in n:
                        if x.get_type() not in ["HILL", "MOUNTAIN"]:
                            todo_list.append(x)
                    # if j < (iteration*0.1):
                    if j < mount_thresh:
                        curr.set_type("MOUNTAIN")
                    else:
                        curr.set_type("HILL")

                    j += 1
        for t in changed:
            n = self.get_neighbours_of(t)
            nb_mount = 0
            for _n in n:
                if _n.get_type() == "MOUNTAIN":
                    nb_mount += 1
            if nb_mount > 2:
                t.set_type("MOUNTAIN")
            elif nb_mount == 0:
                t.set_type("HILL")

    def generate_map_with_perlin(self,  start_tile=None, nb_river=1):
        self.generate_elevation(start_tile=start_tile)
        self.generate_river_simple(nb_river=nb_river)
        self.generate_forest(threshold=0.25, tree_chance=0.25)

    def generate_elevation(self, start_tile=None):
        noise = []
        for i in range(self.width):
            noise.append([])
            for j in range(self.height):
                noise[i].append(0)

        PNFactory = perlin.PerlinNoiseFactory(2, octaves=4, tile=(), unbias=True)

        for i in range(self.width):
            for j in range(self.height):
                noise[i][j] = PNFactory(i/self.width,j/self.height)

        noise1D = []
        for i in range(self.width):
            for j in range(self.height):
                noise1D.append(noise[i][j])

        _min = np.min(noise1D)
        _max = np.max(noise1D)

        for i in range(self.width):
            for j in range(self.height):
                self.grid[i][j].elevation_raw = utils.normalise(noise[i][j], _min, _max)
                self.grid[i][j].elevation = -3 + (self.grid[i][j].elevation_raw * 11)
                self.grid[i][j].set_type_from_elevation()
                if self.grid[i][j] == "SHALLOW_WATER":
                    self.shallow_water_tiles.append(self.grid[i][j])

        # close_list = []
        # for wt in self.shallow_water_tiles:
        #     if wt not in close_list:
        #         close_list.append(wt)


    def generate_forest(self, threshold=0.25, tree_chance=0.2):
        noise = []
        for i in range(self.width):
            noise.append([])
            for j in range(self.height):
                noise[i].append(0)
        
        PNFactory_forest = perlin.PerlinNoiseFactory(2, octaves=3, tile=(), unbias=False)

        for i in range(self.width):
            for j in range(self.height):
                noise[i][j] = PNFactory_forest(i/self.width,j/self.height)

        noise1D = []
        for i in range(self.width):
            for j in range(self.height):
                noise1D.append(noise[i][j])
        _min = np.min(noise1D)
        _max = np.max(noise1D)
        for i in range(self.width):
            for j in range(self.height):
                v = utils.normalise(noise[i][j], _min, _max)
                if v < threshold and self.grid[i][j].get_type() in life.Tree.get_good_tiles():
                    if self.grid[i][j].food == None and  not self.grid[i][j].is_river and np.random.random() < tree_chance:
                        self.grid[i][j].set_tree(life.Tree(self.simu, self.grid[i][j], randomness=True))




    def generate_river_simple(self, nb_river=1, waypoints_nb=3, _start=None, _end=None):
        if (_start == None or _end == None) and (len([t for t in self.get_tiles_1D() if t.get_type() in ["MOUNTAIN"]]) <= 0 or len([t for t in self.get_tiles_1D() if t.get_type() in ["SHALLOW_WATER", "DEEP_WATER"]]) <= 0):
            return
        for i in range(nb_river):
            if _start == None:
                start = np.random.choice([t for t in self.get_tiles_1D() if t.get_type() in ["MOUNTAIN"]])
            else:
                start = _start

            if _end == None:
                end = np.random.choice([t for t in self.get_tiles_1D() if t.get_type() in ["SHALLOW_WATER", "DEEP_WATER"]])
            else:
                end = _end

            # river_path_length = pf.getPathLength(start, end, self, cost_dict=p.type2cost_river, dn=True)
            # print(river_path_length)


            # waypoints = []

            # start_to_end_dir  = utils.angle_from_points((start.x, start.y), (end.x, end.y))
            # start_to_end_dist = utils.distance2p((start.x, start.y), (end.x, end.y))
            
            # waypoints.append(utils.point_from_direction((start.x, start.y), 5, utils.random_angle_in_direction(start_to_end_dir, 45), as_int=True))

            # _pass = 0
            # while utils.distance2p(waypoints[-1], (end.x, end.y)) > start_to_end_dist*0.1 and _pass<10:
            #     _pass += 1
            #     start_to_end_dir = utils.angle_from_points(waypoints[-1], (end.x, end.y))
            #     print(utils.distance2p(waypoints[-1], (end.x, end.y)), start_to_end_dir)
            #     waypoints.append(utils.point_from_direction(waypoints[-1], start_to_end_dist*0.1, utils.random_angle_in_direction(start_to_end_dir, 45), as_int=True))

            # print(waypoints, (end.x, end.y))

            river_path = pf.astar(start, end, self, cost_dict=p.type2cost_river, dn=True)

            for i, r in enumerate(river_path):
                if r.get_type() in ["SHALLOW_WATER", "DEEP_WATER"] or r.is_river:
                    break
                r.is_river = True
            self.rivers_path.append(river_path[:i+1])
        
        self.river_tiles = utils.flatten(self.rivers_path)

    def get_tiles_1D(self):
        array1D = []
        for x in range(self.width):
            for y in range(self.height):
                array1D.append(self.grid[x][y])
        return array1D



class Tile(object):
    """docstring for Tile"""
    def __init__(self, x, y, grid):
        super(Tile, self).__init__()
        self.x = x
        self.y = y
        self.grid = grid

        mainw_width, mainw_height = p.parameters["MAIN_WIN_WH"], p.parameters["SCREEN_HEIGHT"]

        topleft = ((x * (mainw_width/self.grid.width)), (y * (mainw_height/self.grid.height)))
        self.rect = pygame.Rect(topleft, (math.ceil(mainw_width/self.grid.width), math.ceil(mainw_height/self.grid.height)))
        bottomright = (topleft[0] + (mainw_width/self.grid.width), topleft[1] + (mainw_height/self.grid.height))
        self.middle = tuple(round(x/2) for x in tuple(x + y for x, y in zip(topleft, bottomright)))

        self.entities = []
        self.food = None

        self.is_river = False

        self.tree  = None
        self.is_forest = False

        self.is_field = False

        self.type = "GRASS"

        self.elevation_raw = 0
        self.elevation = 0

        self.building = None

        self.redraw = True

    def getXY(self):
        return (self.x, self.y)

    def get_color(self):
        if self.is_river:
            return p.type2color["SHALLOW_WATER"]
        elif self.tree != None:
            return p.type2color["TREE"]
        elif self.is_forest:
            return p.type2color["FOREST"]
        elif self.is_field:
            return p.type2color["FIELD"]
        return p.type2color[self.type]

    def get_cost(self, cost_dict=p.type2cost):
        return (cost_dict[self.type]
                + (1.0 if self.food!=None else 0) 
                + (2.0 if self.is_river else 0) 
                + (cost_dict["TREE"] if self.tree != None else 0)
                + (cost_dict["FOREST"] if self.is_forest else 0)
            )

    def get_type(self):
        return self.type

    def set_type(self, nt):
        self.type = nt
        self.redraw = True

    def set_type_from_elevation(self):
        if self.elevation < -2:
            self.type = "DEEP_WATER"
        elif self.elevation < 0:
            self.type = "SHALLOW_WATER"
        elif self.elevation < 0.8:
            self.type = "SAND"
        elif self.elevation < 5:
            self.type = "GRASS"
        elif self.elevation < 7:
            self.type = "HILL"
        elif self.elevation >= 7:
            self.type = "MOUNTAIN"

    def add_entity(self, e):
        self.entities.append(e)
        self.redraw = True

    def rm_entity(self, e):
        self.entities.remove(e)
        self.redraw = True

    def set_food(self, f):
        if f == None:
            self.is_field = False
        self.food = f
        self.redraw = True

    def set_building(self, b):
        if b == None:
            if self.building != None:
                self.building.tile = None
        self.building = b
        self.redraw = True

    def set_tree(self, t):
        self.tree = t
        if t != None:
            self.is_forest = True
            for n in self.get_neighbours():
                if n.get_type() in life.Tree.get_good_tiles():
                    n.is_forest = True
        else:
            self.is_forest = False
            for n in self.get_neighbours():
                if n.is_forest and n.tree == None:
                    n.is_forest = False
        self.redraw = True

    def get_neighbours(self, dn=False, restriction=[]):
        return self.grid.get_neighbours_of(self, diag_neigh=dn, restriction=[])

    def reset(self):
        self.entities = []
        self.food = None
        self.type = "GRASS"
        self.is_river = False
        self.redraw = True
        self.tree = None
        self.is_forest = False
        self.is_field = False


if __name__ == '__main__':
    s = Simulation(p.parameters["GRID_W"], p.parameters["GRID_H"], nb_ent=1, nb_food=15, nb_river=2)

    # for n in s.grid.get_neighbours_of(s.grid.grid[20][20]):
    #     print(n)