#!/usr/bin/env python
# coding: utf-8

# # Add IPF of the inital microstructure to the grid file 
# * Contributor: Sharan Roongta (s.roongta@mpie.de) and Philip Eisenlohr (eisenlohr@egr.msu.edu)
# * DAMASK version: 3.1.0
# * Prerequisites (data): Grid file with matching material.yaml
# * Postrequisites (software): [ParaView](https://paraview.org) or other VTK renderer

# In[1]:


import damask
import numpy as np


# In[2]:


geom = 'initial_IPF/20grains64x64x64.vti'        # path for geometry file
material_config = 'initial_IPF/material.yaml'    # path for material.yaml


# In[3]:


v = damask.VTK.load(geom)
material_ID = v.get(label='material').flatten()


# ## load the material file and assemble phase information
# 
# It is tacitly assumed that there is only one (the first) constituent present at each grid point.

# In[4]:


ma = damask.ConfigMaterial.load(material_config)

phases = list(ma['phase'].keys())
info = []

for m in ma['material']:
    c = m['constituents'][0]
    phase = c['phase']
    info.append({'phase':   phase,
                 'phaseID': phases.index(phase),
                 'lattice': ma['phase'][phase]['lattice'],
                 'O':       c['O'],
                })


# In[5]:


l = np.array([0,0,1])                            # lab frame direction for IPF

IPF = np.ones((len(material_ID),3),np.uint8)
for i,data in enumerate(info):
    IPF[np.where(material_ID==i)] = \
    np.uint8(damask.Orientation(data['O'],lattice=data['lattice']).IPF_color(l)*255)


# ## add IPF and phase information to grid file
# 
# The resulting `*.vti` file can, for instance, be visualized with ParaView.

# In[6]:


v = v.set(f'IPF_{l}',IPF)

p   = np.array([d['phase'] for d in info])
pid = np.array([d['phaseID'] for d in info])
v = v.set(label='phase',data=p[material_ID],info='phase name')
v = v.set(label='phaseID',data=pid[material_ID],info='phase ID')

v.save('20grains64x64x64_initial_IPF+phase')

