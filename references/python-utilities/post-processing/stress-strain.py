#!/usr/bin/env python
# coding: utf-8

# # Stress and Strain Measures
# * Contributor: Martin Diehl (https://martin-diehl.net)
# * DAMASK version: 3.1.0
# 
# DAMASK uses a large strain formulation and, hence, the output quantities are the deformation gradient ($\mathbf{F}$) and the second Piola–Kirchhoff stress ($\mathbf{P}$).
# These quantities can be used to calculate derived stress and strain quantities.
# The following quantities are computed
# - Euler–Almansi strain: $\boldsymbol{\varepsilon}_\mathrm{EA} := \left(\mathbf{I}-\mathbf{F}^{-\mathrm{T}}\mathbf{F}^{-1}\right)/2$
# - Green–Lagrange strain: $\boldsymbol{\varepsilon}_\mathrm{GL} := \left(\mathbf{F}^\mathrm{T}\mathbf{F} -\mathbf{I}\right)/2$
# - Cauchy stress: $\boldsymbol{\sigma} := \mathbf{P} \mathbf{F}^\mathrm{T}/\operatorname{det}(\mathbf{F})$
# - 2nd Piola–Kirchhoff stress: $\mathbf{S} := \mathbf{F}^{-1} \mathbf{P}$
# 
# These quantities are then used to compute the strain energy density under the assumption of monotonous elastic loading. 

# In[1]:


import damask
import numpy as np


# ## Uniaxial tension, isochoric
# A single pair of stress and strain tensors is generated such that the stress state is uniaxial tension and the deformation is isochoric, i.e. without a volume change.

# In[2]:


F = np.eye(3)
F[0,0]+=.3
F[1,1]=F[2,2]=1/np.sqrt(F[0,0])
print('determinant of F',np.linalg.det(F))

P = np.zeros((3,3))
P[0,0] = 400.e6


# In[3]:


epsilon_EulerAlmansi = damask.mechanics.strain(F,'V',-1)
epsilon_GreenLangrange = damask.mechanics.strain(F,'U',1)

sigma = damask.mechanics.stress_Cauchy(P=P,F=F)
S = damask.mechanics.stress_second_Piola_Kirchhoff(P=P,F=F)


# In[4]:


# check energy density (https://doi.org/10.1016/j.ijsolstr.2004.06.008)
print(np.tensordot(sigma,epsilon_EulerAlmansi)*np.linalg.det(F))
print(np.tensordot(S,epsilon_GreenLangrange))
print(np.tensordot(P,(F-np.linalg.inv(F.T))/2))


# ## Random
# A set of 5 stress and strain tensors is generated.
# Note that they are not connected by a valid constitutive law, hence some of the strain energy densities are negative.

# In[5]:


rng = np.random.default_rng(20191102)
F = (rng.random((5,3,3))-.5)*5e-1 + np.eye(3)
P = rng.random((5,3,3))*1e8


# In[6]:


epsilon_EulerAlmansi = damask.mechanics.strain(F,'V',-1)
epsilon_GreenLangrange = damask.mechanics.strain(F,'U',1)

sigma = damask.mechanics.stress_Cauchy(P=P,F=F)
S = damask.mechanics.stress_second_Piola_Kirchhoff(P=P,F=F)


# In[7]:


print(np.einsum('...ij,...ij',sigma,epsilon_EulerAlmansi)*np.linalg.det(F))
print(np.einsum('...ij,...ij',S,epsilon_GreenLangrange))
print(np.einsum('...ij,...ij',P,(F-np.linalg.inv(damask.tensor.transpose(F)))/2))

