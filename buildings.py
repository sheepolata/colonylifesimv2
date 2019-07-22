

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