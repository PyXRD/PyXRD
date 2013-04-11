#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os, sys
import settings

from pprint import pprint

from project.models import Project
from phases.models import Component, Phase

def run(args):

    """ 
    ### Setup:
    """
    code_length = 4
    aliases = {
        'K   ': '%sKaolinite.cmp',
        'I   ': '%sIllite.cmp',
        'Se  ': '%sSerpentine.cmp',
        'T   ': '%sTalc.cmp',
        'dS2w': '%sDi-Smectite/Di-Smectite - Ca 2WAT.cmp',
        'dS1w': '%sDi-Smectite/Di-Smectite - Ca 1WAT.cmp',
        'dS0w': '%sDi-Smectite/Di-Smectite - Ca Dehydr.cmp',
        'dS2g': '%sDi-Smectite/Di-Smectite - Ca 2GLY.cmp',
        'dS1g': '%sDi-Smectite/Di-Smectite - Ca 1GLY.cmp',
        'dSht': '%sDi-Smectite/Di-Smectite - Ca Heated.cmp',
        'tS2w': '%sTri-Smectite/Tri-Smectite - Ca 2WAT.cmp',
        'tS1w': '%sTri-Smectite/Tri-Smectite - Ca 1WAT.cmp',
        'tS0w': '%sTri-Smectite/Tri-Smectite - Ca Dehydr.cmp',
        'tS2g': '%sTri-Smectite/Tri-Smectite - Ca 2GLY.cmp',
        'tS1g': '%sTri-Smectite/Tri-Smectite - Ca 1GLY.cmp',
        'tSht': '%sTri-Smectite/Tri-Smectite - Ca Heated.cmp',
        'C   ': '%sChlorite/Chlorite 100%%.cmp',
        'C100': '%sChlorite/Chlorite 100%%.cmp',
        'C80 ': '%sChlorite/Chlorite 80%%.cmp',
        'C60 ': '%sChlorite/Chlorite 60%%.cmp',
        'C50 ': '%sChlorite/Chlorite 50%%.cmp',
        'C40 ': '%sChlorite/Chlorite 40%%.cmp',
        'C20 ': '%sChlorite/Chlorite 20%%.cmp',
    }
    default_phases = []

    """ 
    ### Commonly used inherit flag dicts:
    """
    inherit_S = dict(
        inherit_ucp_a=True,
        inherit_ucp_b=True,
        inherit_delta_c=True,
        inherit_layer_atoms=True,
    )
    
    inherit_all = dict(
        inherit_d001=True,
        inherit_default_c=True,
        inherit_interlayer_atoms=True,
        inherit_atom_relations=True,
        **inherit_S
    )

    inherit_phase = dict(
        inherit_display_color=True,
        inherit_sigma_star=True,
        inherit_CSDS_distribution=True, 
        inherit_probabilities=True
    )

    """ 
    ### Single-layer phases:
    """
    default_phases += [
        ( '%sKaolinite.phs', [( dict(R=0, name='Kaolinite'), 'K   ', {} ),] ),
        ( '%sIllite.phs', [( dict(R=0, name='Illite'), 'I   ', {} )] ),
        ( '%sSerpentine.phs', [( dict(R=0, name='Serpentine'), 'Se  ', {} )] ),
        ( '%sTalc.phs', [( dict(R=0, name='Talc'), 'T   ', {} )] ),
        ( '%sChlorite.phs', [( dict(R=0, name='Chlorite'), 'C   ', {} )] ),
    ]

    """      
    ### Dioctahedral smectites:
    """
    S_code_AD = 'dS2w'
    S_code_EG = 'dS2g'
    S_inh_comp_args = {
        'dS2g': dict(linked_with='dS2w', **inherit_S),
    }
    
    SS_code_AD = S_code_AD + 'dS1w'
    SS_code_EG = S_code_EG + 'dS1g'
    SS_inh_comp_args = dict(S_inh_comp_args)
    SS_inh_comp_args.update({
        'dS1g': dict(linked_with='dS1w', **inherit_S),
    })
    
    SSS_code_AD = SS_code_AD + 'dS0w'
    SSS_code_EG = SS_code_EG + 'dS0w'
    SSS_inh_comp_args = dict(S_inh_comp_args)
    SSS_inh_comp_args.update({
        'dS0w': dict(linked_with='dS0w', **inherit_S),
    })

    default_phases += [
        ( '%sSmectites/Di-Smectite Ca.phs', [
                ( dict(R=0, name='S R0 Ca-AD'), S_code_AD, {} ),
                ( dict(R=0, name='S R0 Ca-EG', based_on='S R0 Ca-AD', **inherit_phase), S_code_EG, S_inh_comp_args )
        ]),
        
        ( '%sSmectites/SS/Di-SS R0 Ca.phs', [
                ( dict(R=0, name='SS R0 Ca-AD'), SS_code_AD, {} ),
                ( dict(R=0, name='SS R0 Ca-EG', based_on='SS R0 Ca-AD', **inherit_phase), SS_code_EG, SS_inh_comp_args )
        ]),
        ( '%sSmectites/SS/Di-SS R1 Ca.phs', [
                ( dict(R=1, name='SS R1 Ca-AD'), SS_code_AD, {} ),
                ( dict(R=1, name='SS R1 Ca-EG', based_on='SS R1 Ca-AD', **inherit_phase), SS_code_EG, SS_inh_comp_args )
        ]),
        ( '%sSmectites/SS/Di-SS R2 Ca.phs', [
                ( dict(R=2, name='SS R2 Ca-AD'), SS_code_AD, {} ),
                ( dict(R=2, name='SS R2 Ca-EG', based_on='SS R2 Ca-AD', **inherit_phase), SS_code_EG, SS_inh_comp_args )
        ]),
        ( '%sSmectites/SS/Di-SS R3 Ca.phs', [
                ( dict(R=3, name='SS R3 Ca-AD'), SS_code_AD, {} ),
                ( dict(R=3, name='SS R3 Ca-EG', based_on='SS R3 Ca-AD', **inherit_phase), SS_code_EG, SS_inh_comp_args )
        ]),
        
        ( '%sSmectites/SSS/Di-SSS R0 Ca.phs', [
                ( dict(R=0, name='SSS R0 Ca-AD'), SSS_code_AD, {} ),
                ( dict(R=0, name='SSS R0 Ca-EG', based_on='SSS R0 Ca-AD', **inherit_phase), SSS_code_EG, SSS_inh_comp_args )
        ]),
        ( '%sSmectites/SSS/Di-SSS R1 Ca.phs', [
                ( dict(R=1, name='SSS R1 Ca-AD'), SSS_code_AD, {} ),
                ( dict(R=1, name='SSS R1 Ca-EG', based_on='SSS R1 Ca-AD', **inherit_phase), SSS_code_EG, SSS_inh_comp_args )
        ]),
        ( '%sSmectites/SSS/Di-SSS R2 Ca.phs', [
                ( dict(R=2, name='SSS R2 Ca-AD'), SSS_code_AD, {} ),
                ( dict(R=2, name='SSS R2 Ca-EG', based_on='SSS R2 Ca-AD', **inherit_phase), SSS_code_EG, SSS_inh_comp_args )
        ]),
    ]

    """      
    ### Trioctahedral smectites:
    """
    tS_code_AD = 'tS2w'
    tS_code_EG = 'tS2g'
    tS_inh_comp_args = {
        'tS2g': dict(linked_with='tS2w', **inherit_S),
    }
    
    tSS_code_AD = S_code_AD + 'tS1w'
    tSS_code_EG = S_code_EG + 'tS1g'
    tSS_inh_comp_args = dict(S_inh_comp_args)
    tSS_inh_comp_args.update({
        'tS1g': dict(linked_with='tS1w', **inherit_S),
    })
    
    tSSS_code_AD = SS_code_AD + 'tS0w'
    tSSS_code_EG = SS_code_EG + 'tS0w'
    tSSS_inh_comp_args = dict(S_inh_comp_args)
    tSSS_inh_comp_args.update({
        'tS0w': dict(linked_with='tS0w', **inherit_S),
    })

    default_phases += [
        ( '%sSmectites/Tri-Smectite Ca.phs', [
                ( dict(R=0, name='S R0 Ca-AD'), tS_code_AD, {} ),
                ( dict(R=0, name='S R0 Ca-EG', based_on='S R0 Ca-AD', **inherit_phase), tS_code_EG, tS_inh_comp_args )
        ]),
        
        ( '%sSmectites/SS/Tri-SS R0 Ca.phs', [
                ( dict(R=0, name='SS R0 Ca-AD'), tSS_code_AD, {} ),
                ( dict(R=0, name='SS R0 Ca-EG', based_on='SS R0 Ca-AD', **inherit_phase), tSS_code_EG, tSS_inh_comp_args )
        ]),
        ( '%sSmectites/SS/Tri-SS R1 Ca.phs', [
                ( dict(R=1, name='SS R1 Ca-AD'), tSS_code_AD, {} ),
                ( dict(R=1, name='SS R1 Ca-EG', based_on='SS R1 Ca-AD', **inherit_phase), tSS_code_EG, tSS_inh_comp_args )
        ]),
        ( '%sSmectites/SS/Tri-SS R2 Ca.phs', [
                ( dict(R=2, name='SS R2 Ca-AD'), tSS_code_AD, {} ),
                ( dict(R=2, name='SS R2 Ca-EG', based_on='SS R2 Ca-AD', **inherit_phase), tSS_code_EG, tSS_inh_comp_args )
        ]),
        ( '%sSmectites/SS/Tri-SS R3 Ca.phs', [
                ( dict(R=3, name='SS R3 Ca-AD'), tSS_code_AD, {} ),
                ( dict(R=3, name='SS R3 Ca-EG', based_on='SS R3 Ca-AD', **inherit_phase), tSS_code_EG, tSS_inh_comp_args )
        ]),
        
        ( '%sSmectites/SSS/Tri-SSS R0 Ca.phs', [
                ( dict(R=0, name='SSS R0 Ca-AD'), tSSS_code_AD, {} ),
                ( dict(R=0, name='SSS R0 Ca-EG', based_on='SSS R0 Ca-AD', **inherit_phase), tSSS_code_EG, tSSS_inh_comp_args )
        ]),
        ( '%sSmectites/SSS/Tri-SSS R1 Ca.phs', [
                ( dict(R=1, name='SSS R1 Ca-AD'), tSSS_code_AD, {} ),
                ( dict(R=1, name='SSS R1 Ca-EG', based_on='SSS R1 Ca-AD', **inherit_phase), tSSS_code_EG, tSSS_inh_comp_args )
        ]),
        ( '%sSmectites/SSS/Tri-SSS R2 Ca.phs', [
                ( dict(R=2, name='SSS R2 Ca-AD'), tSSS_code_AD, {} ),
                ( dict(R=2, name='SSS R2 Ca-EG', based_on='SSS R2 Ca-AD', **inherit_phase), tSSS_code_EG, tSSS_inh_comp_args )
        ]),
    ]
    """      
    ### Kaolinite - Smectites:
    """
    K_code = 'K   '
    K_inh_comp_args = {
        'K   ': dict(linked_with='K   ', **inherit_all),
    }
    
    KS_code_AD = K_code + S_code_AD
    KS_code_EG = K_code + S_code_EG
    KS_inh_comp_args = dict(S_inh_comp_args)
    KS_inh_comp_args.update(K_inh_comp_args)

    KSS_code_AD = K_code + SS_code_AD
    KSS_code_EG = K_code + SS_code_EG
    KSS_inh_comp_args = dict(SS_inh_comp_args)
    KSS_inh_comp_args.update(K_inh_comp_args)
    
    KSSS_code_AD = K_code + SSS_code_AD
    KSSS_code_EG = K_code + SSS_code_EG
    KSSS_inh_comp_args = dict(SSS_inh_comp_args)
    KSSS_inh_comp_args.update(K_inh_comp_args)
    
    default_phases += [
        ( '%sKaolinite-Smectites/KS/KS R0 Ca.phs', [
                ( dict(R=0, name='KS R0 Ca-AD'), KS_code_AD, {} ),
                ( dict(R=0, name='KS R0 Ca-EG', based_on='KS R0 Ca-AD', **inherit_phase), KS_code_EG, KS_inh_comp_args )
        ]),
        ( '%sKaolinite-Smectites/KS/KS R1 Ca.phs', [
                ( dict(R=1, name='KS R1 Ca-AD'), KS_code_AD, {} ),
                ( dict(R=1, name='KS R1 Ca-EG', based_on='KS R1 Ca-AD', **inherit_phase), KS_code_EG, KS_inh_comp_args )
        ]),
        ( '%sKaolinite-Smectites/KS/KS R2 Ca.phs', [
                ( dict(R=2, name='KS R2 Ca-AD'), KS_code_AD, {} ),
                ( dict(R=2, name='KS R2 Ca-EG', based_on='KS R2 Ca-AD', **inherit_phase), KS_code_EG, KS_inh_comp_args )
        ]),
        ( '%sKaolinite-Smectites/KS/KS R3 Ca.phs', [
                ( dict(R=3, name='KS R2 Ca-AD'), KS_code_AD, {} ),
                ( dict(R=3, name='KS R2 Ca-EG', based_on='KS R3 Ca-AD', **inherit_phase), KS_code_EG, KS_inh_comp_args )
        ]),
        
        ( '%sKaolinite-Smectites/KSS/KSS R0 Ca.phs', [
                ( dict(R=0, name='KSS R0 Ca-AD'), KSS_code_AD, {} ),
                ( dict(R=0, name='KSS R0 Ca-EG', based_on='KSS R0 Ca-AD', **inherit_phase), KSS_code_EG, KSS_inh_comp_args )
        ]),
        ( '%sKaolinite-Smectites/KSS/KSS R1 Ca.phs', [
                ( dict(R=1, name='KSS R1 Ca-AD'), KSS_code_AD, {} ),
                ( dict(R=1, name='KSS R1 Ca-EG', based_on='KSS R1 Ca-AD', **inherit_phase), KSS_code_EG, KSS_inh_comp_args )
        ]),
        ( '%sKaolinite-Smectites/KSS/KSS R2 Ca.phs', [
                ( dict(R=2, name='KSS R2 Ca-AD'), KSS_code_AD, {} ),
                ( dict(R=2, name='KSS R2 Ca-EG', based_on='KSS R2 Ca-AD', **inherit_phase), KSS_code_EG, KSS_inh_comp_args )
        ]),
        
        ( '%sKaolinite-Smectites/KSSS/KSSS R0 Ca.phs', [
                ( dict(R=0, name='KSSS R0 Ca-AD'), KSSS_code_AD, {} ),
                ( dict(R=0, name='KSSS R0 Ca-EG', based_on='KSSS R0 Ca-AD', **inherit_phase), KSSS_code_EG, KSSS_inh_comp_args )
        ]),
        ( '%sKaolinite-Smectites/KSSS/KSSS R1 Ca.phs', [
                ( dict(R=1, name='KSSS R1 Ca-AD'), KSSS_code_AD, {} ),
                ( dict(R=1, name='KSSS R1 Ca-EG', based_on='KSSS R1 Ca-AD', **inherit_phase), KSSS_code_EG, KSSS_inh_comp_args )
        ]),
    ]
    
    """       
    ### Illite - Smectites:
    """
    I_code = 'I   '
    I_inh_comp_args = {
        'I   ': dict(linked_with='I   ', **inherit_all),
    }
    
    IS_code_AD = I_code + S_code_AD
    IS_code_EG = I_code + S_code_EG
    IS_inh_comp_args = dict(S_inh_comp_args)
    IS_inh_comp_args.update(I_inh_comp_args)
    
    ISS_code_AD = I_code + SS_code_AD
    ISS_code_EG = I_code + SS_code_EG
    ISS_inh_comp_args = dict(SS_inh_comp_args)
    ISS_inh_comp_args.update(I_inh_comp_args)
    
    ISSS_code_AD = I_code + SSS_code_AD
    ISSS_code_EG = I_code + SSS_code_EG
    ISSS_inh_comp_args = dict(SSS_inh_comp_args)
    ISSS_inh_comp_args.update(I_inh_comp_args)
    
    default_phases += [
        ( '%sIllite-Smectites/IS/IS R0 Ca.phs', [
                ( dict(R=0, name='IS R0 Ca-AD'), IS_code_AD, {} ),
                ( dict(R=0, name='IS R0 Ca-EG', based_on='IS R0 Ca-AD', **inherit_phase), IS_code_EG, IS_inh_comp_args )
        ]),
        ( '%sIllite-Smectites/IS/IS R1 Ca.phs', [
                ( dict(R=1, name='IS R1 Ca-AD'), IS_code_AD, {} ),
                ( dict(R=1, name='IS R1 Ca-EG', based_on='IS R1 Ca-AD', **inherit_phase), IS_code_EG, IS_inh_comp_args )
        ]),
        ( '%sIllite-Smectites/IS/IS R2 Ca.phs', [
                ( dict(R=2, name='IS R2 Ca-AD'), IS_code_AD, {} ),
                ( dict(R=2, name='IS R2 Ca-EG', based_on='IS R2 Ca-AD', **inherit_phase), IS_code_EG, IS_inh_comp_args )
        ]),
        ( '%sIllite-Smectites/IS/IS R3 Ca.phs', [
                ( dict(R=3, name='IS R2 Ca-AD'), IS_code_AD, {} ),
                ( dict(R=3, name='IS R2 Ca-EG', based_on='IS R3 Ca-AD', **inherit_phase), IS_code_EG, IS_inh_comp_args )
        ]),
        
        ( '%sIllite-Smectites/ISS/ISS R0 Ca.phs', [
                ( dict(R=0, name='ISS R0 Ca-AD'), ISS_code_AD, {} ),
                ( dict(R=0, name='ISS R0 Ca-EG', based_on='ISS R0 Ca-AD', **inherit_phase), ISS_code_EG, ISS_inh_comp_args )
        ]),
        ( '%sIllite-Smectites/ISS/ISS R1 Ca.phs', [
                ( dict(R=1, name='ISS R1 Ca-AD'), ISS_code_AD, {} ),
                ( dict(R=1, name='ISS R1 Ca-EG', based_on='ISS R1 Ca-AD', **inherit_phase), ISS_code_EG, ISS_inh_comp_args )
        ]),
        ( '%sIllite-Smectites/ISS/ISS R2 Ca.phs', [
                ( dict(R=2, name='ISS R2 Ca-AD'), ISS_code_AD, {} ),
                ( dict(R=2, name='ISS R2 Ca-EG', based_on='ISS R2 Ca-AD', **inherit_phase), ISS_code_EG, ISS_inh_comp_args )
        ]),
        
        ( '%sIllite-Smectites/ISSS/ISSS R0 Ca.phs', [
                ( dict(R=0, name='ISSS R0 Ca-AD'), ISSS_code_AD, {} ),
                ( dict(R=0, name='ISSS R0 Ca-EG', based_on='ISSS R0 Ca-AD', **inherit_phase), ISSS_code_EG, ISSS_inh_comp_args )
        ]),
        ( '%sIllite-Smectites/ISSS/ISSS R1 Ca.phs', [
                ( dict(R=1, name='ISSS R1 Ca-AD'), ISSS_code_AD, {} ),
                ( dict(R=1, name='ISSS R1 Ca-EG', based_on='ISSS R1 Ca-AD', **inherit_phase), ISSS_code_EG, ISSS_inh_comp_args )
        ]),
    ]
    
    """        
    ### Chlorite - Smectites:
    """
    C_code = 'C   '
    C_inh_comp_args = {
        'C   ': dict(linked_with='C   ', **inherit_all),
    }
    
    CS_code_AD = C_code + S_code_AD
    CS_code_EG = C_code + S_code_EG
    CS_inh_comp_args = dict(S_inh_comp_args)
    CS_inh_comp_args.update(C_inh_comp_args)
    
    CSS_code_AD = C_code + SS_code_AD
    CSS_code_EG = C_code + SS_code_EG
    CSS_inh_comp_args = dict(SS_inh_comp_args)
    CSS_inh_comp_args.update(C_inh_comp_args)
    
    CSSS_code_AD = C_code + SSS_code_AD
    CSSS_code_EG = C_code + SSS_code_EG
    CSSS_inh_comp_args = dict(SSS_inh_comp_args)
    CSSS_inh_comp_args.update(C_inh_comp_args)
    
    default_phases += [

        ( '%sChlorite-Smectites/CS/CS R0 Ca.phs', [
                ( dict(R=0, name='CS R0 Ca-AD'), CS_code_AD, {} ),
                ( dict(R=0, name='CS R0 Ca-EG', based_on='CS R0 Ca-AD', **inherit_phase), CS_code_EG, CS_inh_comp_args )
        ]),
        ( '%sChlorite-Smectites/CS/CS R1 Ca.phs', [
                ( dict(R=1, name='CS R1 Ca-AD'), CS_code_AD, {} ),
                ( dict(R=1, name='CS R1 Ca-EG', based_on='CS R1 Ca-AD', **inherit_phase), CS_code_EG, CS_inh_comp_args )
        ]),
        ( '%sChlorite-Smectites/CS/CS R2 Ca.phs', [
                ( dict(R=2, name='CS R2 Ca-AD'), CS_code_AD, {} ),
                ( dict(R=2, name='CS R2 Ca-EG', based_on='CS R2 Ca-AD', **inherit_phase), CS_code_EG, CS_inh_comp_args )
        ]),
        ( '%sChlorite-Smectites/CS/CS R3 Ca.phs', [
                ( dict(R=3, name='CS R2 Ca-AD'), CS_code_AD, {} ),
                ( dict(R=3, name='CS R2 Ca-EG', based_on='CS R3 Ca-AD', **inherit_phase), CS_code_EG, CS_inh_comp_args )
        ]),
        
        ( '%sChlorite-Smectites/CSS/CSS R0 Ca.phs', [
                ( dict(R=0, name='CSS R0 Ca-AD'), CSS_code_AD, {} ),
                ( dict(R=0, name='CSS R0 Ca-EG', based_on='CSS R0 Ca-AD', **inherit_phase), CSS_code_EG, CSS_inh_comp_args )
        ]),
        ( '%sChlorite-Smectites/CSS/CSS R1 Ca.phs', [
                ( dict(R=1, name='CSS R1 Ca-AD'), CSS_code_AD, {} ),
                ( dict(R=1, name='CSS R1 Ca-EG', based_on='CSS R1 Ca-AD', **inherit_phase), CSS_code_EG, CSS_inh_comp_args )
        ]),
        ( '%sChlorite-Smectites/CSS/CSS R2 Ca.phs', [
                ( dict(R=2, name='CSS R2 Ca-AD'), CSS_code_AD, {} ),
                ( dict(R=2, name='CSS R2 Ca-EG', based_on='CSS R2 Ca-AD', **inherit_phase), CSS_code_EG, CSS_inh_comp_args )
        ]),
        
        ( '%sChlorite-Smectites/CSSS/CSSS R0 Ca.phs', [
                ( dict(R=0, name='CSSS R0 Ca-AD'), CSSS_code_AD, {} ),
                ( dict(R=0, name='CSSS R0 Ca-EG', based_on='CSSS R0 Ca-AD', **inherit_phase), CSSS_code_EG, CSSS_inh_comp_args )
        ]),
        ( '%sChlorite-Smectites/CSSS/CSSS R1 Ca.phs', [
                ( dict(R=1, name='CSSS R1 Ca-AD'), CSSS_code_AD, {} ),
                ( dict(R=1, name='CSSS R1 Ca-EG', based_on='CSSS R1 Ca-AD', **inherit_phase), CSSS_code_EG, CSSS_inh_comp_args )
        ]),
    ]
    
    """      
    ### Talc - Smectites:
    """
    T_code = 'T   '
    T_inh_comp_args = {
        'T   ': dict(linked_with='T   ', **inherit_all),
    }
    
    TS_code_AD = T_code + S_code_AD
    TS_code_EG = T_code + S_code_EG
    TS_inh_comp_args = dict(S_inh_comp_args)
    TS_inh_comp_args.update(T_inh_comp_args)
    
    TSS_code_AD = T_code + SS_code_AD
    TSS_code_EG = T_code + SS_code_EG
    TSS_inh_comp_args = dict(SS_inh_comp_args)
    TSS_inh_comp_args.update(T_inh_comp_args)
    
    TSSS_code_AD = T_code + SSS_code_AD
    TSSS_code_EG = T_code + SSS_code_EG
    TSSS_inh_comp_args = dict(SSS_inh_comp_args)
    TSSS_inh_comp_args.update(T_inh_comp_args)

    default_phases += [
        ( '%sTalc-Smectites/TS/TS R0 Ca.phs', [
                ( dict(R=0, name='TS R0 Ca-AD'), TS_code_AD, {} ),
                ( dict(R=0, name='TS R0 Ca-EG', based_on='TS R0 Ca-AD', **inherit_phase), TS_code_EG, TS_inh_comp_args )
        ]),
        ( '%sTalc-Smectites/TS/TS R1 Ca.phs', [
                ( dict(R=1, name='TS R1 Ca-AD'), TS_code_AD, {} ),
                ( dict(R=1, name='TS R1 Ca-EG', based_on='TS R1 Ca-AD', **inherit_phase), TS_code_EG, TS_inh_comp_args )
        ]),
        ( '%sTalc-Smectites/TS/TS R2 Ca.phs', [
                ( dict(R=2, name='TS R2 Ca-AD'), TS_code_AD, {} ),
                ( dict(R=2, name='TS R2 Ca-EG', based_on='TS R2 Ca-AD', **inherit_phase), TS_code_EG, TS_inh_comp_args )
        ]),
        ( '%sTalc-Smectites/TS/TS R3 Ca.phs', [
                ( dict(R=3, name='TS R2 Ca-AD'), TS_code_AD, {} ),
                ( dict(R=3, name='TS R2 Ca-EG', based_on='TS R3 Ca-AD', **inherit_phase), TS_code_EG, TS_inh_comp_args )
        ]),
        
        ( '%sTalc-Smectites/TSS/TSS R0 Ca.phs', [
                ( dict(R=0, name='TSS R0 Ca-AD'), TSS_code_AD, {} ),
                ( dict(R=0, name='TSS R0 Ca-EG', based_on='TSS R0 Ca-AD', **inherit_phase), TSS_code_EG, TSS_inh_comp_args )
        ]),
        ( '%sTalc-Smectites/TSS/TSS R1 Ca.phs', [
                ( dict(R=1, name='TSS R1 Ca-AD'), TSS_code_AD, {} ),
                ( dict(R=1, name='TSS R1 Ca-EG', based_on='TSS R1 Ca-AD', **inherit_phase), TSS_code_EG, TSS_inh_comp_args )
        ]),
        ( '%sTalc-Smectites/TSS/TSS R2 Ca.phs', [
                ( dict(R=2, name='TSS R2 Ca-AD'), TSS_code_AD, {} ),
                ( dict(R=2, name='TSS R2 Ca-EG', based_on='TSS R2 Ca-AD', **inherit_phase), TSS_code_EG, TSS_inh_comp_args )
        ]),
        
        ( '%sTalc-Smectites/TSSS/TSSS R0 Ca.phs', [
                ( dict(R=0, name='TSSS R0 Ca-AD'), TSSS_code_AD, {} ),
                ( dict(R=0, name='TSSS R0 Ca-EG', based_on='TSSS R0 Ca-AD', **inherit_phase), TSSS_code_EG, TSSS_inh_comp_args )
        ]),
        ( '%sTalc-Smectites/TSSS/TSSS R1 Ca.phs', [
                ( dict(R=1, name='TSSS R1 Ca-AD'), TSSS_code_AD, {} ),
                ( dict(R=1, name='TSSS R1 Ca-EG', based_on='TSSS R1 Ca-AD', **inherit_phase), TSSS_code_EG, TSSS_inh_comp_args )
        ]),
    ]
    
    """        
    ### Illite - Chlorite - Smectites:
    """
    IC_code = I_code + C_code
    IC_inh_comp_args = dict(I_inh_comp_args)
    IC_inh_comp_args.update(C_inh_comp_args)
    
    ICS_code_AD = IC_code + S_code_AD
    ICS_code_EG = IC_code + S_code_EG
    ICS_inh_comp_args = dict(S_inh_comp_args)
    ICS_inh_comp_args.update(IC_inh_comp_args)
    
    ICSS_code_AD = IC_code + SS_code_AD
    ICSS_code_EG = IC_code + SS_code_EG
    ICSS_inh_comp_args = dict(SS_inh_comp_args)
    ICSS_inh_comp_args.update(IC_inh_comp_args)
    
    ICSSS_code_AD = IC_code + SSS_code_AD
    ICSSS_code_EG = IC_code + SSS_code_EG
    ICSSS_inh_comp_args = dict(SSS_inh_comp_args)
    ICSSS_inh_comp_args.update(IC_inh_comp_args)
    
    default_phases += [
        ( '%sIllite-Chlorite-Smectites/ICS/ICS R0 Ca.phs', [
                ( dict(R=0, name='ICS R0 Ca-AD'), ICS_code_AD, {} ),
                ( dict(R=0, name='ICS R0 Ca-EG', based_on='ICS R0 Ca-AD', **inherit_phase), ICS_code_EG, ICS_inh_comp_args )
        ]),
        ( '%sIllite-Chlorite-Smectites/ICS/ICS R1 Ca.phs', [
                ( dict(R=1, name='ICS R1 Ca-AD'), ICS_code_AD, {} ),
                ( dict(R=1, name='ICS R1 Ca-EG', based_on='ICS R1 Ca-AD', **inherit_phase), ICS_code_EG, ICS_inh_comp_args )
        ]),
        ( '%sIllite-Chlorite-Smectites/ICS/ICS R2 Ca.phs', [
                ( dict(R=2, name='ICS R2 Ca-AD'), ICS_code_AD, {} ),
                ( dict(R=2, name='ICS R2 Ca-EG', based_on='ICS R2 Ca-AD', **inherit_phase), ICS_code_EG, ICS_inh_comp_args )
        ]),
        
        ( '%sIllite-Chlorite-Smectites/ICSS/ICSS R0 Ca.phs', [
                ( dict(R=0, name='ICSS R0 Ca-AD'), ICSS_code_AD, {} ),
                ( dict(R=0, name='ICSS R0 Ca-EG', based_on='ICSS R0 Ca-AD', **inherit_phase), ICSS_code_EG, ICSS_inh_comp_args )
        ]),
        ( '%sIllite-Chlorite-Smectites/ICSS/ICSS R1 Ca.phs', [
                ( dict(R=1, name='ICSS R1 Ca-AD'), ICSS_code_AD, {} ),
                ( dict(R=1, name='ICSS R1 Ca-EG', based_on='ICSS R1 Ca-AD', **inherit_phase), ICSS_code_EG, ICSS_inh_comp_args )
        ]),
        
        ( '%sIllite-Chlorite-Smectites/ICSSS/ICSSS R0 Ca.phs', [
                ( dict(R=0, name='ICSSS R0 Ca-AD'), ICSSS_code_AD, {} ),
                ( dict(R=0, name='ICSSS R0 Ca-EG', based_on='ICSSS R0 Ca-AD', **inherit_phase), ICSSS_code_EG, ICSSS_inh_comp_args )
        ]),
    ]
    
    """        
    ### Kaolinite - Chlorite - Smectites:
    """
    KC_code = I_code + C_code
    KC_inh_comp_args = dict(I_inh_comp_args)
    KC_inh_comp_args.update(C_inh_comp_args)
    
    KCS_code_AD = KC_code + S_code_AD
    KCS_code_EG = KC_code + S_code_EG
    KCS_inh_comp_args = dict(S_inh_comp_args)
    KCS_inh_comp_args.update(KC_inh_comp_args)
    
    KCSS_code_AD = KC_code + SS_code_AD
    KCSS_code_EG = KC_code + SS_code_EG
    KCSS_inh_comp_args = dict(SS_inh_comp_args)
    KCSS_inh_comp_args.update(KC_inh_comp_args)
    
    KCSSS_code_AD = KC_code + SSS_code_AD
    KCSSS_code_EG = KC_code + SSS_code_EG
    KCSSS_inh_comp_args = dict(SSS_inh_comp_args)
    KCSSS_inh_comp_args.update(KC_inh_comp_args)
    
    default_phases += [
        ( '%sKaolinite-Chlorite-Smectites/KCS/KCS R0 Ca.phs', [
                ( dict(R=0, name='KCS R0 Ca-AD'), KCS_code_AD, {} ),
                ( dict(R=0, name='KCS R0 Ca-EG', based_on='KCS R0 Ca-AD', **inherit_phase), KCS_code_EG, KCS_inh_comp_args )
        ]),
        ( '%sKaolinite-Chlorite-Smectites/KCS/KCS R1 Ca.phs', [
                ( dict(R=1, name='KCS R1 Ca-AD'), KCS_code_AD, {} ),
                ( dict(R=1, name='KCS R1 Ca-EG', based_on='KCS R1 Ca-AD', **inherit_phase), KCS_code_EG, KCS_inh_comp_args )
        ]),
        ( '%sKaolinite-Chlorite-Smectites/KCS/KCS R2 Ca.phs', [
                ( dict(R=2, name='KCS R2 Ca-AD'), KCS_code_AD, {} ),
                ( dict(R=2, name='KCS R2 Ca-EG', based_on='KCS R2 Ca-AD', **inherit_phase), KCS_code_EG, KCS_inh_comp_args )
        ]),
        
        ( '%sKaolinite-Chlorite-Smectites/KCSS/KCSS R0 Ca.phs', [
                ( dict(R=0, name='KCSS R0 Ca-AD'), KCSS_code_AD, {} ),
                ( dict(R=0, name='KCSS R0 Ca-EG', based_on='KCSS R0 Ca-AD', **inherit_phase), KCSS_code_EG, KCSS_inh_comp_args )
        ]),
        ( '%sKaolinite-Chlorite-Smectites/KCSS/KCSS R1 Ca.phs', [
                ( dict(R=1, name='KCSS R1 Ca-AD'), KCSS_code_AD, {} ),
                ( dict(R=1, name='KCSS R1 Ca-EG', based_on='KCSS R1 Ca-AD', **inherit_phase), KCSS_code_EG, KCSS_inh_comp_args )
        ]),
        
        ( '%sKaolinite-Chlorite-Smectites/KCSSS/KCSSS R0 Ca.phs', [
                ( dict(R=0, name='KCSSS R0 Ca-AD'), KCSSS_code_AD, {} ),
                ( dict(R=0, name='KCSSS R0 Ca-EG', based_on='KCSSS R0 Ca-AD', **inherit_phase), KCSSS_code_EG, KCSSS_inh_comp_args )
        ]),
    ]
    
    """
    ### Actual object generation routine:
    """
    project = Project()
    for phases_path, phase_descr in default_phases:
        
        phase_lookup = {}
        component_lookup = {}
        
        for phase_kwargs, code, comp_props in phase_descr:

            # create phase:
            G = len(code) / code_length
            based_on = None
            if "based_on" in phase_kwargs:
                based_on = phase_lookup.get(phase_kwargs.pop("based_on"), None)
            phase = Phase(G=G, parent=project, **phase_kwargs)
            phase.based_on = based_on
            phase_lookup[phase.name] = phase
            print "Phase %s created" % phase
            
            # derive upper and lower limits for the codes using code lengths:
            limits = zip(
                range(0, len(code), code_length),
                range(code_length, len(code)+1, code_length)
            )
            
            # create components:
            phase.components.clear()
            for ll, ul in limits:
                part = code[ll: ul]
                for component in Component.load_components(aliases[part] % settings.DEFAULT_COMPONENTS_DIR, parent=phase):
                    component.resolve_json_references()
                    phase.components.append(component)
                    props = comp_props.get(part, {})
                    for prop, value in props.iteritems():
                        if prop=='linked_with':
                            value = component_lookup[value]
                        setattr(component, prop, value)

                    component_lookup[part] = component
                    print "     component %s added" % component

        #save phases:
        phases_path = phases_path % settings.DEFAULT_PHASES_DIR
        create_dir_recursive(phases_path)
        Phase.save_phases(phase_lookup.values(), phases_path)
    pass #end of run
    
def create_dir_recursive(path):
    to_create = []
    while not os.path.exists(path):
        to_create.insert(0, path)
        path = os.path.dirname(path)
    for path in to_create[:-1]:
        os.mkdir(path)
