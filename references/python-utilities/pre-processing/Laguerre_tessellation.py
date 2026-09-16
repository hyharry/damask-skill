#!/usr/bin/env python
# coding: utf-8

# # Create a Polycrystal with Laguerre Tessellation for the Grid Solver
# * Contributor: Martin Diehl (https://martin-diehl.net)
# * DAMASK version: 3.1.0

# In[1]:


get_ipython().run_line_magic('matplotlib', 'inline')


# In[2]:


import damask
import numpy as np
from matplotlib import pyplot as plt


# In[3]:


size = np.ones(3)*1e-5
cells = [64,64,64]
N_grains = 31


# In[4]:


seeds = damask.seeds.from_random(size,N_grains,cells,rng_seed=20191102)
weights = np.ones(seeds.shape[0])*1e-9
weights[:N_grains//2] += 3e-12
grid = damask.GeomGrid.from_Laguerre_tessellation(cells,size,seeds,weights)
grid.save(f'Polycystal_{N_grains}_{cells[0]}x{cells[1]}x{cells[2]}')
print(grid)


# In[5]:


fig, ax = plt.subplots()
ax.set_title('Grain size distribution')
ax.set_ylabel('# voxels')
ax.set_xlabel('material ID')
ax.hist(grid.material.flatten(),bins=31);
plt.show()


# In[6]:


fig, axes = plt.subplots(figsize=(8, 8),ncols=3)
planes = ['x','y','z']
for i, plane in enumerate(planes):
    selection = [slice(None)]*3
    selection[planes.index(plane)] = 1
    im = axes[i].imshow(grid.material[tuple(selection)].T,vmin=0,vmax=N_grains-1)
    axes[i].set_title(f'{plane}-plane')
cbar_location = fig.add_axes([.95, 0.38, 0.01, 0.2])
cbar = fig.colorbar(im, cax=cbar_location)
cbar.ax.set_ylabel('material ID', rotation=90)
plt.show()

