#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import os, sys, string

import numpy as np
import xml.etree.ElementTree as ET

from project.models import Project
from phases.models import Phase
from atoms.models import Atom

def save_float(num):
    return float(num.replace(",", "."))

def run(args):
    #generates a project file containing the phases as described by the Sybilla XML output:
    if args and args.filename!="":
        tree = ET.parse(args.filename)
        root = tree.getroot()
        
        # create the project:        #TODO add name/...?
        project = Project()
        
        for child in root:
            if child.tag == "mixture":
                for xmlPhase in child:
                    name = xmlPhase.attrib['name']
                    sigma = xmlPhase.attrib['sigma_star']
                    csds = save_float(xmlPhase.find('distribution').attrib['Tmean'])
                    G = 1
                    R = 0
                    W = [1.0,]
                    if xmlPhase.attrib['type'] != 'mono':
                        prob = xmlPhase.find('probability')
                        G = int(prob.attrib['no_of_comp'])
                        R = int(prob.attrib['R'])
                        
                    #create phase and add to project:
                    phase = Phase(name=name, sigma_star=sigma, G=G, R=R, mean_CSDS=csds, parent=project)
                    project.phases.append(phase)
                    
                    #set probability:
                    if R==0 and G!=1:
                        xmlW = prob.find('W')
                        W = np.array([ float(int(save_float(xmlW.attrib[string.ascii_lowercase[i]])*1000))/1000. for i in range(G) ])
                        for i in range(G-1):
                            setattr(phase.probabilities, "F%d"%i, W[i] / np.sum(W[i:]))
                            
                    #parse components:
                    for i, layer in enumerate(xmlPhase.findall("./layer_and_edge/layer")):
                    
                        component = phase.components.get_user_data_from_index(i)
                        component.name = layer.attrib['name']
                        
                        component.d001 = save_float(layer.attrib['d_spacing'])/10.0
                        component.default_c = save_float(layer.attrib['d_spacing'])/10.0
                        component.delta_c = save_float(layer.attrib['d_spacing_delta'])/10.0

                        component.ucp_b.value = 0.9
                        
                        component.ucp_a.factor = 0.57735
                        component.ucp_a.prop = (component, 'cell_b')
                        component.ucp_a.enabled = True     

                        
                        atom_type_map = {
                            #"NH4": "FIXME"
                            "K": "K1+",
                            "O": "O1-",
                            "Si": "Si2+",
                            "OH": "OH1-",
                            "Fe": "Fe1.5+",
                            "Al": "Al1.5+",
                            "Mg": "Mg2+", #FIXME
                            "H2O": "H2O",
                            "Glycol": "Glycol", #TODO CHECK!
                            "Ca": "Ca2+",    
                        }
                        
                        #add atoms:
                        for atom in layer.findall("atom"):
                            atom_type_name = atom_type_map.get(atom.attrib['type'], None)
                            if atom_type_name:
                                atom = Atom(
                                    name=atom.attrib['type'], 
                                    default_z=save_float(atom.attrib['position'])/10.0,
                                    pn=save_float(atom.attrib['content']),
                                    atom_type_name=atom_type_name,
                                    parent=component
                                )
                                component.layer_atoms.append(atom)
                                atom.resolve_json_references()
                            
        #save this:
        project_filename = "%s/%s" % (os.path.dirname(args.filename), os.path.basename(args.filename).replace(".xml", ".pyxrd", 1))          
        project.save_object(project_filename)
        
        #relaunch process
        args = [sys.argv[0], project_filename,]
        args.insert(0, sys.executable)
        if sys.platform == 'win32':
            args = ['"%s"' % arg for arg in args]                
        os.execv(sys.executable, args)
        sys.exit(0)

