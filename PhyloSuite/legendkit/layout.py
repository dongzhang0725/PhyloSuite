from functools import partial
from typing import List, Dict

from matplotlib.artist import Artist
from matplotlib.legend import Legend
from matplotlib.offsetbox import VPacker, HPacker, AnchoredOffsetbox, TextArea
from matplotlib.patches import FancyBboxPatch

from ._colorart import ColorArt
from ._locs import Locs


def _create_children(artists: List[Artist]):
    children = []
    for art in artists:
        if isinstance(art, Legend):
            c1, c2 = art.get_children()
            if isinstance(c1, FancyBboxPatch):
                children.append(c2)
            else:
                children.append(c1)
        elif isinstance(art, AnchoredOffsetbox):
            children += art.get_children()
        elif isinstance(art, ColorArt):
            children += art.get_children().get_children()
        elif isinstance(art, Artist):
            children.append(art)
        else:
            raise TypeError(
                f"Cannot parse object {str(art)} with type {type(art)}")
        try:
            # remove artist from the canvas to avoid rendering overlay
            art.remove()
        except Exception:
            pass
    return children


def stack(legends,
          ax=None,
          orientation: str = "vertical",
          spacing=2,
          padding=2,
          align="baseline",
          mode="fixed",
          loc="lower left",
          frameon=False,
          bbox_to_anchor=None,
          bbox_transform=None,
          deviation=0.05,
          title: str = None,
          title_loc: str = "top",
          titlepad=0,
          alignment: str = "center",
          title_fontproperties: Dict = None
          ):
    """Stack multiple artists together

    Parameters
    ----------
    legends : list of legends or artists
    ax : The axes to draw upon
    orientation : {'vertical', 'horizontal'}
    spacing : float
        The space between legends
    padding : float
        The space around the legends
    align : str
    mode
    loc
    frameon
    bbox_to_anchor
    bbox_transform
    deviation : float
        The space that deviate from axes
    title : str
        The text of title
    title_loc : {'top', 'bottom', 'left', 'right'}
        The location of title
    titlepad : float
        The space between title and legend entries
    alignment : {'left', 'center', 'right'}
        The alignment of the elements inside box
    title_fontproperties : dict
        The font dict that configurate title

    Examples
    --------

    Horizontal stack

    .. plot::
        :context: close-figs

        >>> from legendkit import cat_legend, hstack
        >>> _, ax = plt.subplots(figsize=(3, 1)); ax.set_axis_off()
        >>> args = dict(colors = ["#A7D2CB", "#F2D388"],
        ...             labels = ["Item 1", "Item 2"])
        >>> legs = [cat_legend(**args, title=f"Legend {i+1}") for i in range(3)]
        >>> hstack(legs, title="Horizontal Stack", loc="center", spacing=10, ax=ax)

    .. plot::
        :context: close-figs

        >>> from legendkit import cat_legend, vstack
        >>> _, ax = plt.subplots(figsize=(3, 3)); ax.set_axis_off()
        >>> args = dict(colors = ["#A7D2CB", "#F2D388"],
        ...             labels = ["Item 1", "Item 2"])
        >>> legs = [cat_legend(**args, title=f"Legend {i+1}") for i in range(3)]
        >>> vstack(legs, title="Vertical Stack", loc="center", spacing=10, ax=ax)


    """
    children = _create_children(legends)
    # Call different layout helper depends on orientation
    packer = VPacker if orientation == "vertical" else HPacker

    children_pack = packer(pad=0,
                           sep=spacing,
                           align=align,
                           mode=mode,
                           children=children
                           )
    if title is not None:
        if title_fontproperties is None:
            title_fontproperties = {'weight': 'bold'}
        title_box = TextArea(title, textprops=title_fontproperties)

        content = [title_box, children_pack]
        packer = HPacker
        if title_loc in ["top", "bottom"]:
            packer = VPacker
        else:
            content = content[::-1]
        pack = packer(pad=titlepad, sep=spacing / 2, align=alignment,
                      mode=mode, children=content)
    else:
        pack = children_pack
    # If user supply the ax
    # The legend box will be rendered on the axes
    # So user don't have to call ax.add_artist()
    if ax is not None:
        loc, bbox_to_anchor, bbox_transform = \
            Locs().transform(ax, loc, bbox_to_anchor=bbox_to_anchor,
                             bbox_transform=bbox_transform,
                             deviation=deviation)
    legend_box = AnchoredOffsetbox(child=pack,
                                   loc=loc,
                                   pad=padding,
                                   borderpad=0,
                                   prop=None,
                                   frameon=frameon,
                                   bbox_to_anchor=bbox_to_anchor,
                                   bbox_transform=bbox_transform, )
    if ax is not None:
        if ax.legend_ is None:
            ax.legend_ = legend_box
        else:
            ax.add_artist(legend_box)
    return legend_box


# Create two helper function
vstack = partial(stack, orientation="vertical")
hstack = partial(stack, orientation="horizontal")
