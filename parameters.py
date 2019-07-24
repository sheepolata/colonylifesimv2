parameters = {
    "SCREEN_WIDTH"     : 1440,
    "SCREEN_HEIGHT"    : 900,
    "MAINW_WIDTH"      : 900,
    "MAINW_HEIGHT"     : 900,
    "INFO_SURF_WIDTH"  : 1440-900,
    "INFO_SURF_HEIGHT" : 900,
    "GRID_W"           : 100,
    "GRID_H"           : 100
}

sim_params = {
    "ACTION_TICK"      : 5,
    "ACTION_TICK_BASE" : 5,
    "SOCIAL_FEATURES"  : 4,
    "FRIEND_FOE_TRESH" : 1
}

type2cost = {
    "GRASS"        : 0.0,
    "SAND"         : 0.5,
    "FOREST"       : 1.2,
    "TREE"         : 2.4,
    "HILL"         : 0.8,
    "MOUNTAIN"     : 4.0,
    "SHALLOW_WATER": 3.0,
    "DEEP_WATER"   : 10.0
}

type2cost_river = {
    "GRASS"         : 0.2 * 10,
    "SAND"          : 0.18 * 10,
    "FOREST"        : 0.8 * 10,
    "HILL"          : 1.8 * 10,
    "MOUNTAIN"      : 3.5 * 10,
    "SHALLOW_WATER" : 0.0 * 10,
    "DEEP_WATER"    : 0.0 * 10
}

type2color = {
    "GRASS"         : (65,152,10,255),
    "SAND"          : (219, 209, 180, 255),
    "FOREST"        : (0,102,51,255),
    "TREE"          : (79, 36, 18,255),
    "HILL"          : (165,113,78,255),
    "MOUNTAIN"      : (87,65,47,255),
    "SHALLOW_WATER" : (110,255,255,255),
    "DEEP_WATER"    : (47,86,233,255),
    "FIELD"         : (255,255,0,255)
}

ENTITY_BASIC_COLOR = (255, 208, 42, 255)

COMMUNITY_COLOR_INDEX = 0
COMMUNITY_COLORS = [
    (0, 255, 0, 255),
    (0, 0, 255, 255),
    (255, 140, 0, 255),
    (255, 255, 240, 255),
    (255, 20, 147, 255)
]

import numpy as np

np.random.shuffle(COMMUNITY_COLORS)

def get_next_community_color():
    global COMMUNITY_COLOR_INDEX
    c = COMMUNITY_COLORS[COMMUNITY_COLOR_INDEX]
    COMMUNITY_COLOR_INDEX = (COMMUNITY_COLOR_INDEX+1)%len(COMMUNITY_COLORS)
    return c

class SocialFeature(object):
    """docstring for SocialFeature"""
    def __init__(self, feature, close_to, away_from):
        super(SocialFeature, self).__init__()
        self.feature = feature
        self.close_to = close_to
        self.away_from = away_from

    def similarity(self, social_feature):
        if social_feature.feature == self.feature:
            return 1.0
        elif social_feature.feature in self.close_to:
            return 0.75
        elif social_feature.feature in self.away_from:
            return -1.75/2
        else:
            return np.random.choice([-0.25, 0.25])

    @staticmethod
    def list_similatiry(l1, l2):
        res = []
        for ft1 in l1:
            for ft2 in l2:
                res.append(ft1.similarity(ft2))
        return round(np.mean(res), 2)

social_features_list = [
    SocialFeature("HOSPITALITY", ["TOLERANCE", "KINDNESS", "AWARENESS", "UNDERSTANDING"], ["INDIFFERENCE", "GREED", "NEGLECT"]),

    SocialFeature("GREED", ["NEGLECT", "INDIFFERENCE", "APATHY"], ["DILIGENCE", "HOSPITALITY", "PATIENCE", "UNDERSTANDING"]),

    SocialFeature("TOLERANCE", ["HOSPITALITY", "KINDNESS", "PATIENCE", "AWARENESS", "UNDERSTANDING"], ["NARROW-MINDEDNESS", "GREED"]),

    SocialFeature("NARROW-MINDEDNESS", ["GREED", "IGNORANCE", "INDIFFERENCE"], ["TOLERANCE", "AGITATION", "AWARENESS", "UNDERSTANDING", "CURIOSITY"]),

    SocialFeature("KINDNESS", ["HOSPITALITY", "TOLERANCE", "AGITATION", "AWARENESS", "UNDERSTANDING"], ["INDIFFERENCE", "HATRED", "GREED", "NEGLECT"]),

    SocialFeature("HATRED", ["GREED", "NARROW-MINDEDNESS", "IGNORANCE", "INDIFFERENCE"], ["KINDNESS", "HOSPITALITY", "TOLERANCE", "UNDERSTANDING"]),

    SocialFeature("PATIENCE", ["TOLERANCE", "KINDNESS", "UNDERSTANDING", "APATHY"], ["AGITATION", "INDIFFERENCE", "DILIGENCE"]),

    SocialFeature("AGITATION", ["NEGLECT", "DILIGENCE"], ["APATHY", "PATIENCE"]),

    SocialFeature("AWARENESS", ["KINDNESS", "UNDERSTANDING", "CURIOSITY"], ["INDIFFERENCE", "NEGLECT", "NARROW-MINDEDNESS", "IGNORANCE"]),

    SocialFeature("NEGLECT", ["GREED", "NARROW-MINDEDNESS", "AGITATION", "INDIFFERENCE", "APATHY"], ["DILIGENCE", "AWARENESS", "HOSPITALITY", "PATIENCE"]),

    SocialFeature("IGNORANCE", ["GREED", "NARROW-MINDEDNESS"], ["INDIFFERENCE", "UNDERSTANDING", "KINDNESS", "AWARENESS", "CURIOSITY"]),

    SocialFeature("UNDERSTANDING", ["HOSPITALITY", "TOLERANCE", "KINDNESS", "PATIENCE", "AWARENESS", "CURIOSITY"], ["INDIFFERENCE", "IGNORANCE", "NARROW-MINDEDNESS"]),

    SocialFeature("CURIOSITY", ["KINDNESS", "AGITATION", "AWARENESS", "UNDERSTANDING"], ["APATHY", "INDIFFERENCE", "NARROW-MINDEDNESS", "PATIENCE", "NEGLECT", "IGNORANCE"]),

    SocialFeature("INDIFFERENCE", ["GREED", "NEGLECT", "IGNORANCE"], ["UNDERSTANDING", "CURIOSITY", "HOSPITALITY", "TOLERANCE", "KINDNESS", "AWARENESS"]),

    SocialFeature("DILIGENCE", ["HOSPITALITY", "AGITATION"], ["APATHY", "TOLERANCE", "PATIENCE", "   INDIFFERENCE"]),

    SocialFeature("APATHY", ["GREED", "NEGLECT", "INDIFFERENCE"], ["DILIGENCE", "PATIENCE", "AGITATION", "UNDERSTANDING", "CURIOSITY"]),
]

all_traits = {
    "LEADERSHIP"   : (["LEADER", "FOLLOWER"], [0.3, 0.7]),
    "CURIOSITY"    : (["CURIOUS", "AVERAGE", "INDIFFERENT"], [0.25, 0.6, 0.15]),
    "STRENGTH"     : (["STRONG", "AVERAGE", "WEAK"], [0.3, 0.4, 0.3]),
    "INTELLIGENCE" : (["SMART", "AVERAGE", "DUMB"], [0.15, 0.7, 0.15])
}