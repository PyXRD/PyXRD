Mixture module
==============

The mixture module contains a number of classes that manage 'mixtures'. Mixtures
combine multiple specimens and phases with each other. Mixtures are part of the
project, which also holds a reference to the phases and specimens 
(and possible others as well) in the mixture.

The combination of phases and specimens is achieved using a kind of combination
'matrix', in which rows are phases and columns are specimens. In other
words, each column gets a specimen asigned to it, and each slot in the matrix
gets a phase asigned to it. This way it is possible to have the same phase for
different specimens of your sample if that pĥase is believed to be 'immune' to
the treatments, or to have different (or at least partially different) phases
when it is believed to be affected by the treatment in some way. 

For an explanation on how to create and link phases see the documentation on
:doc:`phases`.

TODO: add example code on how to use mixtures, optimizers and refiners

Mixture
-------
.. module:: pyxrd.mixture.models
.. autoclass:: Mixture
   :members:

Optimizer
---------
.. module:: pyxrd.mixture.models.optimizers
.. autoclass:: Optimizer
   :members:

Refiner
-------
.. module:: pyxrd.mixture.models.refiner
.. autoclass:: Refiner
   :members:
   
RefineContext
-------------
.. module:: pyxrd.mixture.models.refiner
.. autoclass:: RefineContext
   :members: