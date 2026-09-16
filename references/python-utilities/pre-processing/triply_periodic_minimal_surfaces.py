#!/usr/bin/env python
# coding: utf-8

# # Visualization of triply periodic minimal surfaces (TPMS)
# * Contributor: Philip Eisenlohr (eisenlohr@egr.msu.edu)
# * DAMASK version: 3.1.0
# * Prerequisites (Python): [pyvista](https://pypi.org/project/pyvista/), [ipywidgets](https://pypi.org/project/ipywidgets/)
# * Postrequisites (software): [ParaView](https://paraview.org) or other VTK renderer

# ## import supporting modules 

# In[1]:


import numpy as np
import pyvista as pv
import ipywidgets as widgets
import damask


# ## defining variable aspects of the resulting geometry

# In[2]:


surface = widgets.Dropdown(
    options=list(damask.GeomGrid._minimal_surface),
    description='Minimal Surface:',
    width=400,
    disabled=False,
    )
grid = widgets.IntSlider(
    value=64,
    min=16,
    max=256,
    step=2,
    description='Grid:',
    disabled=False,
    continuous_update=False,
    orientation='horizontal',
    readout=True,
    readout_format='d'
    )
periods = widgets.IntSlider(
    value=1,
    min=1,
    max=4,
    step=1,
    description='Periods:',
    disabled=False,
    continuous_update=False,
    orientation='horizontal',
    readout=True,
    readout_format='d'
    )
threshold = widgets.FloatSlider(
    value=0.0,
    min=-1,
    max=1,
    step=0.05,
    description='Threshold:',
    disabled=False,
    continuous_update=False,
    orientation='horizontal',
    readout=True,
    readout_format='.2f'
    )


# ## problem setup
# 
# Select which triply periodic minimal surface to visualize at what grid resolution and with how many periods in the filled volume.

# In[3]:


display(surface,grid,periods,threshold)


# ## generate resulting TPMS

# In[4]:


tpms = damask.GeomGrid.from_minimal_surface([grid.value]*3,np.ones(3),
                                             surface.value,
                                             threshold=threshold.value,
                                             periods=periods.value)


# In[5]:


# export VTK dataset

tpms.save(f'TPMS_{surface.value}_{threshold.value}_{grid.value}.vti')


# ## generate pyvista mesh for visualization

# In[6]:


# transform into pyvista mesh

mesh = pv.ImageData(dimensions=tpms.cells+1,
                    spacing=tpms.size/tpms.cells)
mesh['material'] = tpms.material.flatten(order='F')
mesh['interface'] = (tpms.vicinity_offset().material>1).astype(int).flatten(order='F')


# ## visualize TPMS with interface

# In[7]:


# generate an interactive visualization

pl = pv.Plotter()
pl.add_mesh(mesh,scalars='material',
            cmap='YlGn',
            opacity=0.4,
            show_scalar_bar=False)
pl.add_mesh(mesh.threshold(value=1,scalars='interface'),
            color="#a0a0a0",
            ambient=0.2,
            specular=0.5,
           )

pl.set_background('white')
pl.show()

