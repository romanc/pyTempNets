# -*- coding: utf-8 -*-
"""
Created on Fri May  8 12:35:22 2015
@author: Ingo Scholtes

(c) Copyright ETH Zürich, Chair of Systems Design, 2015
"""

import numpy as np
import igraph

from pyTempNet import Utilities
    
def RWDiffusion(g, samples = 5, epsilon=0.01, max_iterations=100000):
    """Computes the average number of steps requires by a random walk process
    to fall below a total variation distance below epsilon (TVD computed between the momentary 
    visitation probabilities \pi^t and the stationary distribution \pi = \pi^{\infty}. This time can be 
    used to measure diffusion speed in a given (weighted and directed) network."""
    avg_speed = 0
    
    T = Utilities.RWTransitionMatrix(g)
    pi = Utilities.StationaryDistribution(T)
    
    n = len(g.vs())
    for s in range(samples):
        x = np.zeros(n)
        seed = np.random.randint(n)
        x[seed] = 1
        while Utilities.TVD(x,pi)>epsilon:
            avg_speed += 1
            # NOTE x * T = (T^T * x^T)^T
            # NOTE T is already transposed to get the left EV
            x = (T.dot(x.transpose())).transpose()
            if avg_speed > max_iterations:
              print("  x[0:10] = ", x[0:10])
              print(" pi[0:10] = ", pi[0:10])
              raise RuntimeError("Failed to converge within maximal number of iterations. Start of current x and pi are printed above")

    return avg_speed/samples
    

def exportDiffusionMovieFrames(g, file_prefix='diffusion', visual_style = None, steps=100, initial_index=-1):
    """Exports an animation showing the evolution of a diffusion
           process on the network"""

    T = Utilities.RWTransitionMatrix(g)

    if visual_style == None:
            visual_style = {}
            visual_style["vertex_color"] = "lightblue"
            visual_style["vertex_label"] = g.vs["name"]
            visual_style["edge_curved"] = .5
            visual_style["vertex_size"] = 30

    # lambda expression for the coloring of nodes according to some quantity p \in [0,1]
    # p = 1 ==> color red 
    # p = 0 ==> color white
    color_p = lambda p: "rgb(255,"+str(int((1-p)*255))+","+str(int((1-p)*255))+")"

    # Initial state of random walker
    if initial_index<0:
        initial_index = np.random.randint(0, len(g.vs()))

    x = np.zeros(len(g.vs()))
    x[initial_index] = 1

    # compute stationary state
    pi = Utilities.StationaryDistribution(T)

    scale = np.mean(np.abs(x-pi))

    # Plot network (useful as poster frame of video)
    igraph.plot(g, file_prefix + "_network.pdf", **visual_style)

    # Create frames
    for i in range(0,steps):
        visual_style["vertex_color"] = [color_p(p**0.1) for p in x]
        igraph.plot(g, file_prefix + "_frame_" + str(i).zfill(3) +".png", **visual_style)
        if i % 10 == 0:
            print('Step',i, ' TVD =', Utilities.TVD(x,pi))
        # NOTE x * T = (T^T * x^T)^T
        # NOTE T is already transposed to get the left EV
        x = (T.dot(x.transpose())).transpose()


def exportDiffusionComparisonVideo(t, output_file, visual_style = None, steps = 100, initial_index=-1, delay=10):
    """Exports an mp4 file containing a side-by-side comparison of a diffusion process in a Markovian (left) and a non-Markovian temporal network"""
    prefix_1 = str(np.random.randint(0, 10000))
    prefix_2 = str(np.random.randint(0, 10000))
    prefix_3 = str(np.random.randint(0, 10000))

    print('Calculating diffusion dynamics in non-Markovian temporal network')
    exportDiffusionMovieFramesFirstOrder(t, file_prefix='frames\\' + prefix_1, visual_style=visual_style, steps=steps, initial_index=initial_index, model='SECOND')

    print('Calculating diffusion dynamics in Markovian temporal network')
    exportDiffusionMovieFramesFirstOrder(t, file_prefix='frames\\' + prefix_2, visual_style=visual_style, steps=steps, initial_index=initial_index, model='NULL')

    print('Stitching video frames')
    from subprocess import call
    for i in range(200):
        x = call("convert frames\\" + prefix_1 + "_frame_" + str(i).zfill(3)+ ".png frames\\"+prefix_2+"_frame_" + str(i).zfill(3) + ".png +append " + "frames\\"+prefix_3+"_frame_" + str(i).zfill(3) + ".png", shell=True) 
    
    print('Encoding video')
    x = call("convert -delay " + str(delay) +" frames\\"+prefix_3+"_frame_* "+output_file, shell=True) 


def exportDiffusionVideo(t, output_file, visual_style = None, steps = 100, initial_index=-1, delay=10, model='SECOND'):
    prefix = str(np.random.randint(0, 10000))

    if model == 'SECOND':
        print('Calculating diffusion dynamics in non-Markovian temporal network')
    else:
        print('Calculating diffusion dynamics in Markovian temporal network')
    exportDiffusionMovieFramesFirstOrder(t, file_prefix='frames\\' + prefix, visual_style=visual_style, steps=steps, initial_index=initial_index, model=model)

    from subprocess import call
    print('Encoding video')
    x = call("convert -delay " + str(delay) +" frames\\"+prefix+"_frame_* "+output_file, shell=True) 


def exportDiffusionMovieFramesFirstOrder(t, file_prefix='diffusion', visual_style = None, steps=100, initial_index=-1, model='SECOND'):
    """Exports an animation showing the evolution of a diffusion
           process on the first-order aggregate network, where random walk dynamics 
           either follows a first-order (mode='NULL') or second-order (model='SECOND') Markov 
           model"""
    assert model == 'SECOND' or model =='NULL'

    g1 = t.igraphFirstOrder()

    if model == 'SECOND':
        g2 = t.igraphSecondOrder()
    elif model == 'NULL':
        g2 = t.igraphSecondOrderNull()

    T = Utilities.RWTransitionMatrix(g2)

    # visual style is for *first-order* aggregate network
    if visual_style == None:
            visual_style = {}
            visual_style["vertex_color"] = "lightblue"
            visual_style["vertex_label"] = g1.vs["name"]
            visual_style["edge_curved"] = .5
            visual_style["vertex_size"] = 30

    # Initial state of random walker
    if initial_index<0:
        initial_index = np.random.randint(0, len(g2.vs()))

    x = np.zeros(len(g2.vs()))
    x[initial_index] = 1

    # This index allows to quickly map node names to indices in the first-order network
    map_name_to_id = {}
    for i in range(len(g1.vs())):
        map_name_to_id[g1.vs()['name'][i]] = i
    
    # Index to quickly map second-order node indices to first-order node indices
    map_2_to_1 = {}
    for j in range(len(g2.vs())):
        # j is index of node in *second-order* network
        # we first get the name of the *target* of the underlying edge
        node = g2.vs()["name"][j].split(t.separator)[1]

        # we map the target of second-order node j to the index of the *first-order* node
        map_2_to_1[j] = map_name_to_id[node]

    # compute stationary state of random walk process
    pi = Utilities.StationaryDistribution(T)

    scale = np.mean(np.abs(x-pi))

    # Plot first-order aggregate network (particularly useful as poster frame of video)
    igraph.plot(g1, file_prefix + "_network.pdf", **visual_style)

    # lambda expression for the coloring of nodes according to some quantity p \in [0,1]
    # p = 1 ==> color red 
    # p = 0 ==> color white
    color_p = lambda p: "rgb(255,"+str(int((1-p)*255))+","+str(int((1-p)*255))+")"

    # Create video frames
    for i in range(0,steps):
        # based on visitation probabilities in *second-order* aggregate network, 
        # we need to compute visitation probabilities of nodes in the *first-order* 
        # aggregate network
        x_firstorder = np.zeros(len(g1.vs()))
        
        # j is the index of nodes in the *second-order* network, which we need to map 
        # to nodes in the *first-order* network
        for j in range(len(x)):
            if x[j] > 0:
                x_firstorder[map_2_to_1[j]] = x_firstorder[map_2_to_1[j]] + x[j]

        visual_style["vertex_color"] = [color_p(np.power((p-min(x))/(max(x)-min(x)),1/1.3)) for p in x_firstorder]
        igraph.plot(g1, file_prefix + "_frame_" + str(i).zfill(int(np.ceil(np.log10(steps)))) +".png", **visual_style)
        if i % 50 == 0:
            print('Step',i, ' TVD =', Utilities.TVD(x,pi))
        # NOTE x * T = (T^T * x^T)^T
        # NOTE T is already transposed to get the left EV
        x = (T.dot(x.transpose())).transpose()