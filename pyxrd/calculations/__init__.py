# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

"""
This module contains the basic implementation of the matrix formalism as
detailed in Drits and Tchoubar (1990) and Plançon (2001).

It was chosen to implement this using 'loose' function calls. The disadvantage
of this approach is that the functions are no longer bound to class instances,
which makes them less intuitive to use. The advantage is we can more easily
call these functions asynchronously (e.g. using :py:class:`~multiprocessing.Pool`) 

Despite all this, most function calls in this module do expect to be passed a
:class:`~pyxrd.calculations.DataObject` sub-class, which wraps all the data in a single object. 
These :class:`~pyxrd.calculations.DataObject` s map onto the different models used. As such this 
module is also largely independent from the MVC framework used.
  
Drits, V.A., and Tchoubar, C., 1990. X-Ray Diffraction by Disordered Lamellar Structures: Theory and Applications to Microdivided Silicates and Carbons. Springer-Verlag, Berlin, Germany.
Plançon, A., 2001. Order-disorder in clay mineral structures. Clay Miner 36, 1–14.

"""