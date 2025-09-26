"""
Reusable Hanldes for Legend
===========================

Examples
--------

.. plot::
    :context: close-figs

    >>> from legendkit import legend
    >>> from legendkit.handles import SquareItem, CircleItem, RectItem, LineItem, BoxplotItem
    >>> _, ax = plt.subplots(figsize=(1, 1.5)); ax.set_axis_off()
    >>> legend(ax, handles=[SquareItem(), CircleItem(),
    ...                     RectItem(), LineItem(), BoxplotItem()],
    ...        labels=['Square', 'Circle', 'Rect', 'Line', 'Boxplot'])


"""
from abc import ABC

from matplotlib.collections import Collection
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


class SquareItem(Patch, ABC):
    """Ensure render as square"""
    pass


class RectItem(Patch, ABC):
    """Ensure render as rectangle"""
    pass


class CircleItem(Patch, ABC):
    """Create circle for legend handles"""
    pass


class LineItem(Line2D, ABC):
    """Create line for legend handles"""

    def __init__(self, *args, **kwargs):
        super().__init__([], [], *args, **kwargs)


class BoxplotItem(Collection, ABC):
    """Create boxplot for legend handles"""

    def __init__(self, *args, **kwargs):
        user_ec = kwargs.get('ec')
        user_edgecolor = kwargs.get('edgecolor')
        if (user_ec is None) & (user_edgecolor is None):
            kwargs['ec'] = "black"
        super().__init__(*args, **kwargs)
