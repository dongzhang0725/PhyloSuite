import matplotlib as mpl

from phytreeviz.treeviz import TreeViz
from phytreeviz.utils import load_example_tree_file

__version__ = "0.2.0"

__all__ = [
    "TreeViz",
    "load_example_tree_file",
]

# Setting matplotlib rc(runtime configuration) parameters
# https://matplotlib.org/stable/tutorials/introductory/customizing.html
mpl_rc_params = {
    # SVG
    "svg.fonttype": "none",
    "savefig.bbox": "tight",
}
mpl.rcParams.update(mpl_rc_params)
