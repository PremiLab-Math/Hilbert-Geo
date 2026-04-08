# Copyright (C) 2022-2024 Hilbert-Geo Development Team
# Author: Xiaokai Zhang
# Contact: formalgeo@gmail.com

"""
'solver' invokes other modules to enable interactive problem-solving and automated problem-solving.
The automated problem-solving implements both forward search and backward search, allowing for the
configuration of various search strategies (breadth-first, depth-first, random, beam).
"""

__all__ = [
    "Interactor", "ForwardSearcher", "BackwardSearcher"
]

from hilbert_geo.solver.interactive import Interactor
from hilbert_geo.solver.forward_search import ForwardSearcher
from hilbert_geo.solver.backward_search import BackwardSearcher
