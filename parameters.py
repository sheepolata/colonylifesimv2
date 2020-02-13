parameters = {
    "SCREEN_WIDTH"     : 1440,
    "SCREEN_HEIGHT"    : 900,
    "SCREEN_PERCENT"   : 0.7,
    "MAIN_WIN_RATIO"   : 0.625,
    "MAIN_WIN_WH"      : -1,
    "GRID_W"           : 100,
    "GRID_H"           : 100
}

initial_params = {
    "nb_ent"    : 20, 
    "nb_food"   : 20,
     "nb_river" : 2
}

sim_params = {
    "ACTION_TICK"      : 200,
    "ACTION_TICK_BASE" : 200,
    "SOCIAL_FEATURES"  : 4,
    "FRIEND_FOE_TRESH" : 1
}

behaviour_params = {
    "SOCIAL_INTERACTION_CHANCE"                       : 0.05,
    "SOCIAL_INTERACTION_POSITIVE_REENFORCMENT_CHANCE" : 0.8,
    "SOCIAL_INTERACTION_NEUTRAL_REENFORCMENT_CHANCE"  : 0.5
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

social_feats_factors = {
    "if_equal"    : 1.0,
    "if_closeto"  : 0.75,
    "if_awayfrom" : -1.75/2,
    "if_random"   : 0.25
}

all_dict = {
    "parameters"           : [parameters          , "num"  ],
    "initial_params"       : [initial_params      , "num"  ],
    "behaviour_params"     : [behaviour_params    , "num"  ],
    "sim_params"           : [sim_params          , "num"  ],
    "type2cost"            : [type2cost           , "num"  ],
    "type2cost_river"      : [type2cost_river     , "num"  ],
    "type2color"           : [type2color          , "color"],
    "social_feats_factors" : [social_feats_factors, "num"  ]
}

import numpy as np

class SocialFeature(object):
    """docstring for SocialFeature"""
    def __init__(self, feature, close_to, away_from):
        super(SocialFeature, self).__init__()
        self.feature = feature
        self.close_to = close_to
        self.away_from = away_from

    def similarity(self, social_feature):
        if social_feature.feature == self.feature:
            return social_feats_factors["if_equal"]
        elif social_feature.feature in self.close_to:
            return social_feats_factors["if_closeto"]
        elif social_feature.feature in self.away_from:
            return social_feats_factors["if_awayfrom"]
        else:
            return np.random.choice([-social_feats_factors["if_random"], social_feats_factors["if_random"]])

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

    SocialFeature("APATHY", ["GREED", "NEGLECT", "INDIFFERENCE"], ["DILIGENCE", "PATIENCE", "AGITATION", "UNDERSTANDING", "CURIOSITY"])

]