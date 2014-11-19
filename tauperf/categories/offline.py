from rootpy.tree import Cut

from .base import Category
# All basic cut definitions are here

L1_TAUCLUS = Cut('l1_tauclus>=12000')
OFFLINE_L1_MATCHED = Cut('l1_matched_to_offline != -1')
OFFLINE_HLT_MATCHED = Cut('hlt_matched_to_offline != -1')

ONEPRONG = Cut('off_ntracks == 1')
TWOPRONG = Cut('off_ntracks == 2')
THREEPRONG = Cut('off_ntracks == 3')
MULTIPRONG = Cut('off_ntracks > 1')


# common preselection cuts
PRESELECTION = (
    OFFLINE_L1_MATCHED
    & OFFLINE_HLT_MATCHED
    & L1_TAUCLUS
)

class Category_Preselection(Category):
    name = 'inclusive'
    label = '#tau_{had}'
    common_cuts = PRESELECTION


class Category_1P(Category_Preselection):
    name = '1prong'
    label = '#tau_{had} (1P)'
    common_cuts = Category_Preselection.common_cuts
    cuts = ONEPRONG

class Category_2P(Category_Preselection):
    name = '2prongs'
    label = '#tau_{had} (2P)'
    common_cuts = Category_Preselection.common_cuts
    cuts = TWOPRONG

class Category_3P(Category_Preselection):
    name = '3prongs'
    label = '#tau_{had} (3P)'
    common_cuts = Category_Preselection.common_cuts
    cuts = THREEPRONG

class Category_MP(Category_Preselection):
    name = 'mulitprongs'
    label = '#tau_{had} (MP)'
    common_cuts = Category_Preselection.common_cuts
    cuts = MULTIPRONG
