#!/usr/bin/env python
# coding: utf-8

# # Generate a Three-Step Load Case for the Grid Solver
# * Contributor: Martin Diehl (https://martin-diehl.net) and Philip Eisenlohr (eisenlohr@egr.msu.edu)
# * DAMASK version: 3.1.0

# In[1]:


import damask


# In[2]:


def inversion(l,fill=0):
    return [inversion(i,fill) if isinstance(i,list) else\
            fill if i == 'x' else 'x' for i in l]


# In[3]:


load_case = damask.LoadcaseGrid(solver={'mechanical':'spectral_basic'})


# In[4]:


F = [[1.05, 0 , 0 ],
     [   0,'x', 0 ],
     [   0, 0 ,'x']]

loadstep = {'boundary_conditions':{'mechanical':{'F':F,
                                                 'P':inversion(F)}},
                                   'discretization':{'t':10.,'N':40},'f_out':4}
load_case['loadstep'].append(loadstep)


# In[5]:


dot_P = [[ 0 ,'x','x'],
         ['x','x','x'],
         ['x','x','x']]

loadstep = {'boundary_conditions':{'mechanical':{'dot_P':dot_P,
                                                 'dot_F':inversion(dot_P)}},
                                   'discretization':{'t':10.,'N':20}}
load_case['loadstep'].append(loadstep)


# In[6]:


P = [[ 0 ,'x','x'],
     ['x', 0 ,'x'],
     ['x','x', 0 ]]

loadstep = {'boundary_conditions':{'mechanical':{'P':P,
                                                 'dot_F':inversion(P)}},                      
                                   'discretization':{'t':10.,'N':20}}
load_case['loadstep'].append(loadstep)


# In[7]:


load_case.save('tension-hold-unload.yaml')
load_case

