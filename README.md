# Parameter Discretization

Framework for the HiWi to work on.
This section details the different tasks that are necessary to get the whole pipeline for parameter discretization testing up and running.

It is comprised of several sections.
Each section refers to one software module.
Objectives, function and interface are specified.

![Overview](img/Overview.png)

### Terminology 

The following terminology is used in this file.

#### Parameter combination

The set of parameters required to unambiguously define one concrete scenario.
Each parameter has exactly one concrete value.

#### Parameter space

The set of all parameter combinations.
The parameter space can either be continous or discrete.
The continous parameter space contains all possible or plausible parameter combinations.

The discrete parameter space contains a subset of the continous parameter space obtained by introducing a discrete step for each parameter.
The discrete parameter space will also be referred to as grid.


## Discretizer

The discretizer receives the continous parameter space as input and generates a discrete parameter space. 

It should be able to do the following things:
- Refine an existing discrete parameter space with a constant factor
- iterative refinement based on grid evaluation
- Create a discrete parameter space from scratch which may be viewed as starting with the edges of the parameter space and refining from there
- (r-adaptation of an existing discrete parameter space)

The data format of the discrete parameter space is specified.
It includes the discrete parameter space and metadata regarding the grid refinement. 
The metadata includes the corresponding two previous coarser grids and the refinement factor. 
The parameter space is saved in the specified data format.

![Discretizer](img/Discretizer.png)

## Simulation Runner

Takes the discrete parameter space specifying a set of concrete scenarios and outputs simulation results.
The results are saved.

### Scenario

The scenario will be an already implemented simple scenario.
Initially, it is assumed that a simple static scenario is sufficient.
Only few or even one parameter are varied in the beginning. 
This is later expanded to dynamic and more complex scenarios. 

### Simulation Orchestration and Execution

For simplicity, it is decoupled from the SuT and the rest of the evalution procedure.
CarMaker is used for the simulation environment. 
The input is a discrete parameter space. 

Orchestration takes the discrete parameter space and extracts the parameter combinations.
Results for a given parameter combination are loaded from previously computed data if existent.

Otherwise, execution means running a concrete scenario for the given parameter combination in CarMaker. 

CarMaker offers options for combining orchestration and execution, which are investigated. 
If necessary, utility scripts are written to perform customized orchestration and trigger the execution in CarMaker.

### Results and Saving

The results are output as image files in jpg or png format which can be ingested by any object detector. 
IPG movie may directly allow outputting these, otherwise utility scripts are needed to output and sort files in a suitable format. 

The saved results are associated with a parameter combination. 
Previously computed results are accessible and can be retrieved with the parameter combination instead of recomputing. 


## SuT Mockup

The system under test mockup receives scenario execution outputs to generate SuT output. 
It includes the full complexity of a deep neural network in order to be representative.
For simplicity the SuT Mock-up is fully decoupled from the simulation execution.

The SuT mockup is realized as a perception system with a deep neural network.
The output is an object list consisting of 2D or 3D bounding boxes. 
An off-the-shelf pre-trained detector is sufficient. 
Cars and people are detected since they are highly relevant for traffic.
The detection performance is sufficiently high to yield some results which can be used for evaluation.


## Evaluation

The evaluation consists of a safety score for the SuT mockup, interpolating over the whole continous parameter space and evaluating the grid.

### Safety score

An evaluation metric which evaluates the object list with regard to safety is constructed.
The metric generates a single score for one concrete scenario.

Common perception metrics do not fulfil this function, making it necessary to construct a custom function.
The metric correlates positively with safety and considers existence, classification, confidence and localization error.

### Interpolation

The safety score is only known for the discrete parameter space.
Interpolation is used to construct the safety score for a more fine-grain grid or even the continous parameter space.
The interpolation is a substitute for orchestration, execution, SuT Mockup and the safety score.
It allows to directly generate a safety score for an arbitrary parameter combination or discrete parameter space. 

The interpolation is realized as simple piecewise linear interpolation between the known points of the grid.

![Safety_Interpolation](img/Safety_Interpolation.png)

### Grid Evaluation

The grid is evaluated to assure the interpolation approximates the safety of the SuT sufficiently well for the continous parameter space. 
The result is a decision if the grid is sufficiently fine-grained.

#### Asymptotic Range 

Asymptotic range is required for a reliable grid evaluation.
The interpolation results only reliable within the asymtotic range.
Asymptotic range is achieved if the theoretical and observed order of accuracy match.

- The theoretical order of accuracy is second order accuracy if piecewise linear interpolation between results is used.
- The observed order for the finest grid is calculated from results on three grids.
[p = ln\[(f_3-f_2)/(f_2-f_1)\]/ln(r)]
For confirmation this order is calculated twice using four grids overall.

This module requires the discrete parameter space including the metadata regarding the grid refinement.
Additionally, the corresponding interpolation results for each grid are required.
It outputs if asymptotic range is achieved for a single grid. 

If asymptotic range is not achieved the grid is too coarse.

#### Grid criterion

Roache's Grid Converge Index is applied to estimate accuracy. 
GCI = F_s/(r^p-1) * | (f_h-f_rh)/f_h | 

The input are two solutions for the finer grid, one using the fine grid, the other using the coarse grid and interpolation. 
Asymptotic range for both grids is checked. 

If the CGI is above a decision threshold the grid is too coarse. 

![Grid_Evaluation](img/Grid_Evaluation.png)



