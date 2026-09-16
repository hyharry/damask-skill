#!/usr/bin/env python
# coding: utf-8

# # Store data in an ASCII Table
# * Contributor: Tapashree Pradhan ([GitHub profile](https://github.com/tapashreepradhan))
# * DAMASK version: 3.1.0

# In[1]:


import numpy as np
import damask


# ## Introduction
# This tutorial will demonstrate the use of DAMASK's Table class to store and manage structured data.
# For this, we create a table with deformation gradient ($F$), second Piola–Kirchhoff stress ($P$), and orientation ($O$) information, then save it to file and load it back into memory.
# 
# One of the key benefits of using DAMASK's Table class is that it preserves the dimension of the data, e.g. the information that $F$ is a tensor of shape (3,3).
# This ensures that complex data such as tensors remain well-organized and can be retrieved without requiring reshaping or additional processing.

# ## Getting data
# Load data from the last increment of a DADF5 file:
# - `F`: A 4096x3x3 array representing 4096 3x3 deformation gradient tensors
# - `P`: A 4096x3x3 array representing 4096 3x3 second Piola-Kirchhoff stress tensors
# - `O`: A 4096x4 array representing 4096 orientations as quaternions

# In[2]:


r = damask.Result('table_class/20grains16x16x16_tensionX.hdf5').view(increments=-1)
F = r.place('F')
P = r.place('P')
O = r.place('O')


# ## Creating an initial Table
# We initialize an empty `Table` object and add $F$ and $O$ to that.

# In[3]:


t = damask.Table().set('F', F).set('O', O)
print(f'The table has columns {t.labels} with shapes {t.shapes} and contains\n{t}')


# In[4]:


# Check that the stored `F` values match the original `F` array.
print(f'shape F {F.shape}')
assert (F == t.get('F')).all()


# ## Adding additional data
# Using the `set` method again, we add the stress tensor `P` to the existing table.

# In[5]:


t = t.set('P', P)


# ## Save to file
# The resulting Table object can be directly saved to a text file with its `save` method.
# In below example, we use `output.txt` as filename.

# In[6]:


t.save('output.txt')


# ## Load from file
# Existing ASCII Tables can be loaded from file.
# As a simple demonstration, let's load the just saved Table into a new object and interrogate its deformation gradient (`F`) data.
# Note that the deformation gradient retains its original 3x3 shape.

# In[7]:


t_loaded = damask.Table.load('output.txt')
F_loaded = t_loaded.get('F')
print(f'shape F (loaded) {F_loaded.shape}')


# In[8]:


# Storing data in ASCII format might lead to rounding errors.
print(f'exactly equal: {(F == F_loaded).all()}')
print(f'close: {np.allclose(F,F_loaded)}')

