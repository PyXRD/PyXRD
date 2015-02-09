#!/usr/bin/python
# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os
from pyxrd.data import settings

from pyxrd.project.models import Project
from pyxrd.phases.models import Component, Phase

def generate_expandables(
            filename_format, phase_name, maxR,
            phase_kwargs_AD, phase_kwargs_EG, phase_kwargs_350,
            code_AD, code_EG, code_350,
            comp_kwargs_AD, comp_kwargs_EG, comp_kwargs_350):
        """
            Generates a list of phase descriptions for a combination of an
            AD, EG and 350° Ca-saturated phase linked together
        """
        return [
            ('%s' + (filename_format % R), [
                    (dict(R=R, name=phase_name + (' R%d Ca-AD' % R), **phase_kwargs_AD), code_AD, comp_kwargs_AD),
                    (dict(R=R, name=phase_name + (' R%d Ca-EG' % R), based_on=phase_name + (' R%d Ca-AD' % R), **phase_kwargs_EG), code_EG, comp_kwargs_EG),
                    (dict(R=R, name=phase_name + (' R%d Ca-350' % R), based_on=phase_name + (' R%d Ca-AD' % R), **phase_kwargs_350), code_350, comp_kwargs_350)
            ]) for R in range(maxR)
        ]

def run(args=None, ui_callback=None):

    """ 
    How this script works:
    
     - 'code_length' is the length of the aliases keys (see below)
     - 'aliases' is a dictionary contain 4-character long keys describing a
        specific layer-type (or with other words: a Component object)
        E.g. dS2w stands for Di-octahedral Smectite with 2 layers of water.
        The values are file path formats, in which a single '%s' string placeholder
        will be filled with the absolute path to the default components folder.  
     - 'default_phases' is an initially empty list that will be filled with two-
        tuples. The first element in this tuple is the filename of the generated
        phases, the second element is describing what this phase contains. This
        second element is again a tuple, containing three parts:
            - A dictionary of key-word arguments passed on to the Phase
              constructor. If a 'based_on' keyword is defined, an attempt is
              made to translate it to an earlier generated phase. This way, it
              is possible to pass the name of an earlier generated phase, and
              the script will pass in the actual Phase object instead.
            - A component code (string) built by the keys of the 'aliases'
              dictionary. This string's length should be a multiple of 'code_length'.
              There is no separator, rather, the 'code_length' is used to split the
              code into its parts.   
            - Component keyword arguments dictionaries: this is a dictionary in
              which the keys match with the components code parts. The values are
              property-value dictionaries used to set Component properties after
              importing them. Similarly to the Phases' 'based_on' keyword, the
              value for the 'linked_with' key is translated to the actual
              Component named as such.   
     
    ### Setup:
    """
    code_length = 4
    aliases = {
        'C   ': '%sChlorite.cmp',
        'K   ': '%sKaolinite.cmp',
        'I   ': '%sIllite.cmp',
        'Se  ': '%sSerpentine.cmp',
        'T   ': '%sTalc.cmp',
        'Ma  ': '%sMargarite.cmp',
        'Pa  ': '%sParagonite.cmp',
        'L   ': '%sLeucophyllite.cmp',
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
        'dV2w': '%sDi-Vermiculite/Di-Vermiculite - Ca 2WAT.cmp',
        'dV1w': '%sDi-Vermiculite/Di-Vermiculite - Ca 1WAT.cmp',
        'dV0w': '%sDi-Vermiculite/Di-Vermiculite - Ca Dehydr.cmp',
        'dV2g': '%sDi-Vermiculite/Di-Vermiculite - Ca 2GLY.cmp',
        'dV1g': '%sDi-Vermiculite/Di-Vermiculite - Ca 1GLY.cmp',
        'dVht': '%sDi-Vermiculite/Di-Vermiculite - Ca Heated.cmp',
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
        ('%sKaolinite.phs', [(dict(R=0, name='Kaolinite'), 'K   ', {}), ]),
        ('%sIllite.phs', [(dict(R=0, name='Illite'), 'I   ', {})]),
        ('%sSerpentine.phs', [(dict(R=0, name='Serpentine'), 'Se  ', {})]),
        ('%sTalc.phs', [(dict(R=0, name='Talc'), 'T   ', {})]),
        ('%sChlorite.phs', [(dict(R=0, name='Chlorite'), 'C   ', {})]),
        ('%sMargarite.phs', [(dict(R=0, name='Margarite'), 'Ma  ', {})]),
        ('%sLeucophyllite.phs', [(dict(R=0, name='Leucophyllite'), 'L   ', {})]),
        ('%sParagonite.phs', [(dict(R=0, name='Paragonite'), 'Pa  ', {})]),
    ]

    """      
    ### Dioctahedral smectites:
    """
    S_code_AD = 'dS2w'
    S_code_EG = 'dS2g'
    S_code_350 = 'dSht'
    S_inh_comp_args = {
        'dS2g': dict(linked_with='dS2w', **inherit_S),
        'dSht': dict(linked_with='dS2w', **inherit_S),
    }

    SS_code_AD = S_code_AD + 'dS1w'
    SS_code_EG = S_code_EG + 'dS1g'
    SS_code_350 = S_code_350 + 'dS1g'
    SS_inh_comp_args = dict(S_inh_comp_args)
    SS_inh_comp_args.update({
        'dS1g': dict(linked_with='dS1w', **inherit_S),
    })


    SSS_code_AD = SS_code_AD + 'dS0w'
    SSS_code_EG = SS_code_EG + 'dS0w'
    SSS_code_350 = SS_code_350 + 'dS0w'
    SSS_inh_comp_args = dict(SS_inh_comp_args)
    SSS_inh_comp_args.update({
        'dS0w': dict(linked_with='dS0w', **inherit_S),
    })

    default_phases += [
        ('%sSmectites/Di-Smectite Ca.phs', [
                (dict(R=0, name='S R0 Ca-AD'), S_code_AD, {}),
                (dict(R=0, name='S R0 Ca-EG', based_on='S R0 Ca-AD', **inherit_phase), S_code_EG, S_inh_comp_args),
                (dict(R=0, name='S R0 Ca-350', based_on='S R0 Ca-AD', **inherit_phase), S_code_350, S_inh_comp_args)
        ]),
    ]
    default_phases += generate_expandables(
        'Smectites/SS/Di-SS R%d Ca.phs', 'SS', 4,
        {}, inherit_phase, inherit_phase,
        SS_code_AD, SS_code_EG, SS_code_350,
        {}, SS_inh_comp_args, SS_inh_comp_args,
    )
    default_phases += generate_expandables(
        'Smectites/SSS/Di-SSS R%d Ca.phs', 'SSS', 3,
        {}, inherit_phase, inherit_phase,
        SSS_code_AD, SSS_code_EG, SSS_code_350,
        {}, SSS_inh_comp_args, SSS_inh_comp_args,
    )

    """      
    ### Trioctahedral smectites:
    """
    tS_code_AD = 'tS2w'
    tS_code_EG = 'tS2g'
    tS_code_350 = 'tSht'
    tS_inh_comp_args = {
        'tS2g': dict(linked_with='tS2w', **inherit_S),
        'tSht': dict(linked_with='tS2w', **inherit_S),
    }

    tSS_code_AD = tS_code_AD + 'tS1w'
    tSS_code_EG = tS_code_EG + 'tS1g'
    tSS_code_350 = tS_code_EG + 'tS1g'
    tSS_inh_comp_args = dict(S_inh_comp_args)
    tSS_inh_comp_args.update({
        'tS1g': dict(linked_with='tS1w', **inherit_S),
    })

    tSSS_code_AD = tSS_code_AD + 'tS0w'
    tSSS_code_EG = tSS_code_EG + 'tS0w'
    tSSS_code_350 = tSS_code_EG + 'tS0w'
    tSSS_inh_comp_args = dict(SS_inh_comp_args)
    tSSS_inh_comp_args.update({
        'tS0w': dict(linked_with='tS0w', **inherit_S),
    })

    default_phases += [
        ('%sSmectites/Tri-Smectite Ca.phs', [
                (dict(R=0, name='S R0 Ca-AD'), tS_code_AD, {}),
                (dict(R=0, name='S R0 Ca-EG', based_on='S R0 Ca-AD', **inherit_phase), tS_code_EG, tS_inh_comp_args),
                (dict(R=0, name='S R0 Ca-350', based_on='S R0 Ca-AD', **inherit_phase), tS_code_350, tS_inh_comp_args)
        ]),
    ]
    default_phases += generate_expandables(
        'Smectites/SS/Tri-SS R%d Ca.phs', 'SS', 4,
        {}, inherit_phase, inherit_phase,
        tSS_code_AD, tSS_code_EG, tSS_code_350,
        {}, tSS_inh_comp_args, tSS_inh_comp_args,
    )
    default_phases += generate_expandables(
        'Smectites/SSS/Tri-SSS R%d Ca.phs', 'SSS', 3,
        {}, inherit_phase, inherit_phase,
        tSSS_code_AD, tSSS_code_EG, tSSS_code_350,
        {}, tSSS_inh_comp_args, tSSS_inh_comp_args,
    )

    """      
    ### Dioctahedral vermiculites:
    """
    V_code_AD = 'dV2w'
    V_code_EG = 'dV2g'
    V_code_350 = 'dVht'
    V_inh_comp_args = {
        'dV2g': dict(linked_with='dV2w', **inherit_S),
        'dVht': dict(linked_with='dV2w', **inherit_S),
    }

    VV_code_AD = V_code_AD + 'dV1w'
    VV_code_EG = V_code_EG + 'dV1g'
    VV_code_350 = V_code_350 + 'dV1g'
    VV_inh_comp_args = dict(V_inh_comp_args)
    VV_inh_comp_args.update({
        'dV1g': dict(linked_with='dV1w', **inherit_S),
    })


    VVV_code_AD = VV_code_AD + 'dV0w'
    VVV_code_EG = VV_code_EG + 'dV0w'
    VVV_code_350 = VV_code_350 + 'dV0w'
    VVV_inh_comp_args = dict(VV_inh_comp_args)
    VVV_inh_comp_args.update({
        'dV0w': dict(linked_with='dV0w', **inherit_S),
    })

    default_phases += [
        ('%sVermiculites/Di-Vermiculite Ca.phs', [
                (dict(R=0, name='V R0 Ca-AD'), V_code_AD, {}),
                (dict(R=0, name='V R0 Ca-EG', based_on='V R0 Ca-AD', **inherit_phase), V_code_EG, V_inh_comp_args),
                (dict(R=0, name='V R0 Ca-350', based_on='V R0 Ca-AD', **inherit_phase), V_code_350, V_inh_comp_args)
        ]),
    ]
    default_phases += generate_expandables(
        '%sVermiculites/VV/Di-VV R%d Ca.phs', 'VV', 4,
        {}, inherit_phase, inherit_phase,
        VV_code_AD, VV_code_EG, VV_code_350,
        {}, VV_inh_comp_args, VV_inh_comp_args,
    )
    default_phases += generate_expandables(
        '%sVermiculites/VVV/Di-VVV R%d Ca.phs', 'VVV', 3,
        {}, inherit_phase, inherit_phase,
        VVV_code_AD, VVV_code_EG, VVV_code_350,
        {}, VVV_inh_comp_args, VVV_inh_comp_args,
    )

    """      
    ### Kaolinite - Smectites:
    """
    K_code = 'K   '
    K_inh_comp_args = {
        'K   ': dict(linked_with='K   ', **inherit_all),
    }

    KS_code_AD = K_code + S_code_AD
    KS_code_EG = K_code + S_code_EG
    KS_code_350 = K_code + S_code_350
    KS_inh_comp_args = dict(S_inh_comp_args)
    KS_inh_comp_args.update(K_inh_comp_args)

    KSS_code_AD = K_code + SS_code_AD
    KSS_code_EG = K_code + SS_code_EG
    KSS_code_350 = K_code + SS_code_350
    KSS_inh_comp_args = dict(SS_inh_comp_args)
    KSS_inh_comp_args.update(K_inh_comp_args)

    KSSS_code_AD = K_code + SSS_code_AD
    KSSS_code_EG = K_code + SSS_code_EG
    KSSS_code_350 = K_code + SSS_code_350
    KSSS_inh_comp_args = dict(SSS_inh_comp_args)
    KSSS_inh_comp_args.update(K_inh_comp_args)

    default_phases += generate_expandables(
        'Kaolinite-Smectites/KS/KS R%d Ca.phs', 'KS', 4,
        {}, inherit_phase, inherit_phase,
        KS_code_AD, KS_code_EG, KS_code_350,
        {}, KS_inh_comp_args, KS_inh_comp_args,
    )
    default_phases += generate_expandables(
        'Kaolinite-Smectites/KSS/KSS R%d Ca.phs', 'KSS', 3,
        {}, inherit_phase, inherit_phase,
        KSS_code_AD, KSS_code_EG, KSS_code_350,
        {}, KSS_inh_comp_args, KSS_inh_comp_args,
    )
    default_phases += generate_expandables(
        'Kaolinite-Smectites/KSSS/KSSS R%d Ca.phs', 'KSSS', 2,
        {}, inherit_phase, inherit_phase,
        KSSS_code_AD, KSSS_code_EG, KSSS_code_350,
        {}, KSSS_inh_comp_args, KSSS_inh_comp_args,
    )

    """       
    ### Illite - Smectites:
    """
    I_code = 'I   '
    I_inh_comp_args = {
        'I   ': dict(linked_with='I   ', **inherit_all),
    }

    IS_code_AD = I_code + S_code_AD
    IS_code_EG = I_code + S_code_EG
    IS_code_350 = I_code + S_code_350
    IS_inh_comp_args = dict(S_inh_comp_args)
    IS_inh_comp_args.update(I_inh_comp_args)

    ISS_code_AD = I_code + SS_code_AD
    ISS_code_EG = I_code + SS_code_EG
    ISS_code_350 = I_code + SS_code_350
    ISS_inh_comp_args = dict(SS_inh_comp_args)
    ISS_inh_comp_args.update(I_inh_comp_args)

    ISSS_code_AD = I_code + SSS_code_AD
    ISSS_code_EG = I_code + SSS_code_EG
    ISSS_code_350 = I_code + SSS_code_350
    ISSS_inh_comp_args = dict(SSS_inh_comp_args)
    ISSS_inh_comp_args.update(I_inh_comp_args)

    default_phases += generate_expandables(
        'Illite-Smectites/IS/IS R%d Ca.phs', 'IS', 4,
        {}, inherit_phase, inherit_phase,
        IS_code_AD, IS_code_EG, IS_code_350,
        {}, IS_inh_comp_args, IS_inh_comp_args,
    )
    default_phases += generate_expandables(
        'Illite-Smectites/ISS/ISS R%d Ca.phs', 'ISS', 3,
        {}, inherit_phase, inherit_phase,
        ISS_code_AD, ISS_code_EG, ISS_code_350,
        {}, ISS_inh_comp_args, ISS_inh_comp_args,
    )
    default_phases += generate_expandables(
        'Illite-Smectites/ISSS/ISSS R%d Ca.phs', 'ISSS', 2,
        {}, inherit_phase, inherit_phase,
        ISSS_code_AD, ISSS_code_EG, ISSS_code_350,
        {}, ISSS_inh_comp_args, ISSS_inh_comp_args,
    )

    """        
    ### Chlorite - Smectites:
    """
    C_code = 'C   '
    C_inh_comp_args = {
        'C   ': dict(linked_with='C   ', **inherit_all),
    }

    CS_code_AD = C_code + tS_code_AD
    CS_code_EG = C_code + tS_code_EG
    CS_code_350 = C_code + tS_code_350
    CS_inh_comp_args = dict(tS_inh_comp_args)
    CS_inh_comp_args.update(C_inh_comp_args)

    CSS_code_AD = C_code + tSS_code_AD
    CSS_code_EG = C_code + tSS_code_EG
    CSS_code_350 = C_code + tSS_code_350
    CSS_inh_comp_args = dict(tSS_inh_comp_args)
    CSS_inh_comp_args.update(C_inh_comp_args)

    CSSS_code_AD = C_code + tSSS_code_AD
    CSSS_code_EG = C_code + tSSS_code_EG
    CSSS_code_350 = C_code + tSSS_code_350
    CSSS_inh_comp_args = dict(tSSS_inh_comp_args)
    CSSS_inh_comp_args.update(C_inh_comp_args)

    default_phases += generate_expandables(
        'Chlorite-Smectites/CS/CS R%d Ca.phs', 'CS', 4,
        {}, inherit_phase, inherit_phase,
        CS_code_AD, CS_code_EG, CS_code_350,
        {}, CS_inh_comp_args, CS_inh_comp_args,
    )
    default_phases += generate_expandables(
        'Chlorite-Smectites/CSS/CSS R%d Ca.phs', 'CSS', 3,
        {}, inherit_phase, inherit_phase,
        CSS_code_AD, CSS_code_EG, CSS_code_350,
        {}, CSS_inh_comp_args, CSS_inh_comp_args,
    )
    default_phases += generate_expandables(
        'Chlorite-Smectites/CSSS/CSSS R%d Ca.phs', 'CSSS', 2,
        {}, inherit_phase, inherit_phase,
        CSSS_code_AD, CSSS_code_EG, CSSS_code_350,
        {}, CSSS_inh_comp_args, CSSS_inh_comp_args,
    )

    """      
    ### Talc - Smectites:
    """
    T_code = 'T   '
    T_inh_comp_args = {
        'T   ': dict(linked_with='T   ', **inherit_all),
    }

    TS_code_AD = T_code + S_code_AD
    TS_code_EG = T_code + S_code_EG
    TS_code_350 = T_code + S_code_350
    TS_inh_comp_args = dict(S_inh_comp_args)
    TS_inh_comp_args.update(T_inh_comp_args)

    TSS_code_AD = T_code + SS_code_AD
    TSS_code_EG = T_code + SS_code_EG
    TSS_code_350 = T_code + SS_code_350
    TSS_inh_comp_args = dict(SS_inh_comp_args)
    TSS_inh_comp_args.update(T_inh_comp_args)

    TSSS_code_AD = T_code + SSS_code_AD
    TSSS_code_EG = T_code + SSS_code_EG
    TSSS_code_350 = T_code + SSS_code_350
    TSSS_inh_comp_args = dict(SSS_inh_comp_args)
    TSSS_inh_comp_args.update(T_inh_comp_args)

    default_phases += generate_expandables(
        'Talc-Smectites/TS/TS R%d Ca.phs', 'TS', 4,
        {}, inherit_phase, inherit_phase,
        TS_code_AD, TS_code_EG, TS_code_350,
        {}, TS_inh_comp_args, TS_inh_comp_args,
    )
    default_phases += generate_expandables(
        'Talc-Smectites/TSS/TSS R%d Ca.phs', 'TSS', 3,
        {}, inherit_phase, inherit_phase,
        TSS_code_AD, TSS_code_EG, TSS_code_350,
        {}, TSS_inh_comp_args, TSS_inh_comp_args,
    )
    default_phases += generate_expandables(
        'Talc-Smectites/TSSS/TSSS R%d Ca.phs', 'TSSS', 2,
        {}, inherit_phase, inherit_phase,
        TSSS_code_AD, TSSS_code_EG, TSSS_code_350,
        {}, TSSS_inh_comp_args, TSSS_inh_comp_args,
    )

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
        ('%sIllite-Chlorite-Smectites/ICS/ICS R0 Ca.phs', [
                (dict(R=0, name='ICS R0 Ca-AD'), ICS_code_AD, {}),
                (dict(R=0, name='ICS R0 Ca-EG', based_on='ICS R0 Ca-AD', **inherit_phase), ICS_code_EG, ICS_inh_comp_args)
        ]),
        ('%sIllite-Chlorite-Smectites/ICS/ICS R1 Ca.phs', [
                (dict(R=1, name='ICS R1 Ca-AD'), ICS_code_AD, {}),
                (dict(R=1, name='ICS R1 Ca-EG', based_on='ICS R1 Ca-AD', **inherit_phase), ICS_code_EG, ICS_inh_comp_args)
        ]),
        ('%sIllite-Chlorite-Smectites/ICS/ICS R2 Ca.phs', [
                (dict(R=2, name='ICS R2 Ca-AD'), ICS_code_AD, {}),
                (dict(R=2, name='ICS R2 Ca-EG', based_on='ICS R2 Ca-AD', **inherit_phase), ICS_code_EG, ICS_inh_comp_args)
        ]),

        ('%sIllite-Chlorite-Smectites/ICSS/ICSS R0 Ca.phs', [
                (dict(R=0, name='ICSS R0 Ca-AD'), ICSS_code_AD, {}),
                (dict(R=0, name='ICSS R0 Ca-EG', based_on='ICSS R0 Ca-AD', **inherit_phase), ICSS_code_EG, ICSS_inh_comp_args)
        ]),
        ('%sIllite-Chlorite-Smectites/ICSS/ICSS R1 Ca.phs', [
                (dict(R=1, name='ICSS R1 Ca-AD'), ICSS_code_AD, {}),
                (dict(R=1, name='ICSS R1 Ca-EG', based_on='ICSS R1 Ca-AD', **inherit_phase), ICSS_code_EG, ICSS_inh_comp_args)
        ]),

        ('%sIllite-Chlorite-Smectites/ICSSS/ICSSS R0 Ca.phs', [
                (dict(R=0, name='ICSSS R0 Ca-AD'), ICSSS_code_AD, {}),
                (dict(R=0, name='ICSSS R0 Ca-EG', based_on='ICSSS R0 Ca-AD', **inherit_phase), ICSSS_code_EG, ICSSS_inh_comp_args)
        ]),
    ]

    """        
    ### Kaolinite - Chlorite - Smectites:
    """
    KC_code = K_code + C_code
    KC_inh_comp_args = dict(K_inh_comp_args)
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
        ('%sKaolinite-Chlorite-Smectites/KCS/KCS R0 Ca.phs', [
                (dict(R=0, name='KCS R0 Ca-AD'), KCS_code_AD, {}),
                (dict(R=0, name='KCS R0 Ca-EG', based_on='KCS R0 Ca-AD', **inherit_phase), KCS_code_EG, KCS_inh_comp_args)
        ]),
        ('%sKaolinite-Chlorite-Smectites/KCS/KCS R1 Ca.phs', [
                (dict(R=1, name='KCS R1 Ca-AD'), KCS_code_AD, {}),
                (dict(R=1, name='KCS R1 Ca-EG', based_on='KCS R1 Ca-AD', **inherit_phase), KCS_code_EG, KCS_inh_comp_args)
        ]),
        ('%sKaolinite-Chlorite-Smectites/KCS/KCS R2 Ca.phs', [
                (dict(R=2, name='KCS R2 Ca-AD'), KCS_code_AD, {}),
                (dict(R=2, name='KCS R2 Ca-EG', based_on='KCS R2 Ca-AD', **inherit_phase), KCS_code_EG, KCS_inh_comp_args)
        ]),

        ('%sKaolinite-Chlorite-Smectites/KCSS/KCSS R0 Ca.phs', [
                (dict(R=0, name='KCSS R0 Ca-AD'), KCSS_code_AD, {}),
                (dict(R=0, name='KCSS R0 Ca-EG', based_on='KCSS R0 Ca-AD', **inherit_phase), KCSS_code_EG, KCSS_inh_comp_args)
        ]),
        ('%sKaolinite-Chlorite-Smectites/KCSS/KCSS R1 Ca.phs', [
                (dict(R=1, name='KCSS R1 Ca-AD'), KCSS_code_AD, {}),
                (dict(R=1, name='KCSS R1 Ca-EG', based_on='KCSS R1 Ca-AD', **inherit_phase), KCSS_code_EG, KCSS_inh_comp_args)
        ]),

        ('%sKaolinite-Chlorite-Smectites/KCSSS/KCSSS R0 Ca.phs', [
                (dict(R=0, name='KCSSS R0 Ca-AD'), KCSSS_code_AD, {}),
                (dict(R=0, name='KCSSS R0 Ca-EG', based_on='KCSSS R0 Ca-AD', **inherit_phase), KCSSS_code_EG, KCSSS_inh_comp_args)
        ]),
    ]

    """
    ### Actual object generation routine:
    """
    import Queue
    import threading

    def ioworker(in_queue, stop):
        """
            Saves Phase objects from the in_queue.
            If the Queue is empty this function will only stop
            if the 'stop' event is set.
        """
        while True:
            try:
                phases_path, phases = in_queue.get(timeout=0.5)
                create_dir_recursive(phases_path)
                Phase.save_phases(phases, phases_path)
                in_queue.task_done()
            except Queue.Empty:
                if not stop.is_set():
                    continue
                else:
                    return

    save_queue = Queue.Queue()
    io_stop = threading.Event()
    iothread = threading.Thread(target=ioworker, args=(save_queue, io_stop))
    iothread.start()

    def phaseworker(in_queue, save_queue, stop):
        """
            Parses Phase descriptions into actual objects and passes them
            to the save_queue.
            'stop' should be a threading.Event() that should be toggled
            once all elements have been Queued.
            This way, the worker will only stop once the Queue is really empty,
            and not when it's processing faster than the Queue can be filled. 
        """
        while True:
            try:
                phases_path, phase_descr = in_queue.get(timeout=0.5)
                project = Project()
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

                    # derive upper and lower limits for the codes using code lengths:
                    limits = zip(
                        range(0, len(code), code_length),
                        range(code_length, len(code) + 1, code_length)
                    )

                    # create components:
                    phase.components[:] = []
                    for ll, ul in limits:
                        part = code[ll: ul]
                        for component in Component.load_components(aliases[part] % (settings.DATA_REG.get_directory_path("DEFAULT_COMPONENTS") + "/"), parent=phase):
                            component.resolve_json_references()
                            phase.components.append(component)
                            props = comp_props.get(part, {})
                            for prop, value in props.iteritems():
                                if prop == 'linked_with':
                                    value = component_lookup[value]
                                setattr(component, prop, value)

                            component_lookup[part] = component

                # put phases on the save queue:
                phases_path = phases_path % (settings.DATA_REG.get_directory_path("DEFAULT_PHASES") + "/")
                save_queue.put((phases_path, phase_lookup.values()))
                # Flag this as finished
                in_queue.task_done()
            except Queue.Empty:
                if not stop.is_set():
                    continue
                else:
                    return

    phase_queue = Queue.Queue()
    phase_stop = threading.Event()
    phasethread = threading.Thread(target=phaseworker, args=(phase_queue, save_queue, phase_stop))
    phasethread.start()

    # Queue phases:
    for phases_path, phase_descr in default_phases:
        phase_queue.put((phases_path, phase_descr))

    # Signal phaseworker it can stop if the phase_queue is emptied:
    phase_stop.set()
    while phasethread.is_alive():
        # Try to join the thread, but don't block, inform the UI
        # of our progress if a callback is provided:
        phasethread.join(timeout=0.1)
        if callable(ui_callback):
            progress = float(len(default_phases) - phase_queue.qsize()) / float(len(default_phases))
            ui_callback(progress)

    if callable(ui_callback):
        ui_callback(1.0)

    # Signal the IO worker the phaseworker has stopped, so it can stop
    # if the save_queue is empty
    io_stop.set()
    while iothread.is_alive():
        # Try to join the thread, but don't block
        iothread.join(timeout=0.1)

    pass # end of run

def create_dir_recursive(path):
    """
        Creates the path 'path' recursively.
    """
    to_create = []
    while not os.path.exists(path):
        to_create.insert(0, path)
        path = os.path.dirname(path)
    for path in to_create[:-1]:
        os.mkdir(path)
