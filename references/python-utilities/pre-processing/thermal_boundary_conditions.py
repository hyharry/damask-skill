#!/usr/bin/env python
# coding: utf-8

# # Prescribe Thermal Boundary Conditions for the Grid Solver
# * Contributor: Fotios Tsiolis (f.tsiolis@mpi-susmat.de)
# * DAMASK version: 3.1.0

# In[1]:


import numpy as np
import damask


# ## Geometry and material setup

# In[2]:


T_0 = 500.   # initial mean temperature [K]

g = damask.GeomGrid(np.zeros((2, 2, 2), dtype=int), np.ones(3) * 1e-6)
g.initial_conditions['T'] = T_0
g.save('cube')

mat = damask.ConfigMaterial(
    homogenization={
        'SX': {
            'N_constituents': 1,
            'mechanical': {'type': 'pass'},
            'thermal':    {'type': 'pass', 'output': ['T']},
        }
    },
    phase={
        'Al': {
            'lattice': 'cF',
            'rho':     2700.0,
            'mechanical': {
                'elastic': {'type': 'Hooke', 'C_11': 106.75e9, 'C_12': 60.41e9, 'C_44': 28.34e9}
            },
            'thermal': {'K_11': 0.0, 'K_33': 0.0, 'C_p': 900.0},
        }
    },
).material_add(phase='Al', O=[1, 0, 0, 0], homogenization='SX')

mat.save('material.yaml')

mech_free = {'F': [[1, 0, 0], [0, 1, 0], [0, 0, 1]]}

def make_lc(thermal_bc, t=100., N=20, f_out=1):
    return damask.LoadcaseGrid({
        'solver': {'mechanical': 'spectral_basic', 'thermal': 'spectral'},
        'loadstep': [{
            'boundary_conditions': {
                'mechanical': mech_free,
                'thermal': thermal_bc,
            },
            'discretization': {'t': t, 'N': N},
            'f_out': f_out,
        }]
    })

mat


# ## Prescribed target temperature

# In[3]:


lc_T = make_lc({'T': 700., 'thermostat': 'shift'})
lc_T.save('load_T.yaml')
lc_T


# ## Prescribed temperature rate

# In[4]:


lc_dot_T = make_lc({'dot_T': 2., 'thermostat': 'shift'})
lc_dot_T.save('load_dot_T.yaml')
lc_dot_T


# ## Multi-step load case

# In[5]:


lc_cycle = damask.LoadcaseGrid({
    'solver': {'mechanical': 'spectral_basic', 'thermal': 'spectral'},
    'loadstep': [
        {   # step 1: heat to 800 K
            'boundary_conditions': {
                'mechanical': mech_free,
                'thermal': {'T': 800., 'thermostat': 'shift'}
            },
            'discretization': {'t': 50., 'N': 10}, 'f_out': 1,
        },
        {   # step 2: hold (dot_T = 0)
            'boundary_conditions': {
                'mechanical': mech_free,
                'thermal': {'dot_T': 0., 'thermostat': 'shift'}
            },
            'discretization': {'t': 50., 'N': 10}, 'f_out': 1,
        },
        {   # step 3: cool to 300 K
            'boundary_conditions': {
                'mechanical': mech_free,
                'thermal': {'T': 300., 'thermostat': 'shift'}
            },
            'discretization': {'t': 50., 'N': 10}, 'f_out': 1,
        },
    ]
})
lc_cycle.save('load_cycle.yaml')

lc_cycle

