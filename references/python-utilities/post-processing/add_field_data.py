#!/usr/bin/env python
# coding: utf-8

# # Add Derived Field Data
# * Contributor: Martin Diehl (https://martin-diehl.net)
# * DAMASK version: 3.1.0
# * Prerequisites (data): DADF5 file with first Piola-Kirchhoff stress ('P') and deformation gradient ('F')

# In[1]:


import damask


# In[2]:


# adjust to your situation, file needs to exist
result_file = 'add_field_data/20grains16x16x16_tensionX.hdf5'


# In[3]:


result = damask.Result(result_file)
result.view(increments=0)


# ## First Round

# In[4]:


result.add_stress_Cauchy()
result.add_strain()

# list data (undeformed configuration)
result.view(increments=0)


# ## Second Round

# In[5]:


result.add_equivalent_Mises('sigma')
result.add_equivalent_Mises('epsilon_V^0.0(F)')

# list data (undeformed configuration)
result.view(increments=0)

