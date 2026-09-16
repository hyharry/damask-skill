#!/usr/bin/env python
# coding: utf-8

# # Create Texture for a Dual-Phase Microstructure
# * Contributor: Martin Diehl (https://martin-diehl.net) and Philip Eisenlohr (eisenlohr@egr.msu.edu)
# * DAMASK version: 3.1.0

# In[1]:


import damask
import numpy as np


# In[2]:


rng = np.random.default_rng(20191102)
rnd = damask.Rotation.from_random(7,rng_seed=rng)
fbr = damask.Rotation.from_fiber_component(crystal=[1,0],sample=[1,0],
                                           sigma=5.0,shape=5,degrees=True,rng_seed=rng)
sph = damask.Rotation.from_spherical_component(center=damask.Rotation(),
                                               sigma=7.5,shape=3,degrees=True,rng_seed=rng)


# In[3]:


config = damask.ConfigMaterial()\
               .material_add(O=rnd,phase='phase_A',homogenization='SX')\
               .material_add(O=fbr,phase='phase_A',homogenization='SX')\
               .material_add(O=sph,phase='phase_B',homogenization='SX')


# In[4]:


print(f'configuration is{" " if config.is_valid else " not "}valid\n')

config.save('material.yaml')
config

