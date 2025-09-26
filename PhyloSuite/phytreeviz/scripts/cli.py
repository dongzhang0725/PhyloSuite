# from __future__ import annotations

import argparse
from pathlib import Path

import phytreeviz
from phytreeviz import TreeViz


def main():
    """Main function called from CLI"""
    args = get_args()
    run(**args.__dict__)


def run(
    intree: str | Path,
    outfile: Path,
    format: str = "newick",
    fig_height: float = 0.5,
    fig_width: float = 8.0,
    leaf_label_size: int = 12,
    ignore_branch_length: bool = False,
    align_leaf_label: bool = False,
    show_branch_length: bool = False,
    show_confidence: bool = False,
    dpi: int = 300,
):
    """Run phylogenetic tree plot"""
    tp = TreeViz(
        intree,
        format=format,
        height=fig_height,
        width=fig_width,
        leaf_label_size=leaf_label_size,
        ignore_branch_length=ignore_branch_length,
        align_leaf_label=align_leaf_label,
    )
    tp.show_scale_bar()
    if show_branch_length:
        tp.show_branch_length()
    if show_confidence:
        tp.show_confidence()
    tp.savefig(outfile, dpi=dpi)


def get_args() -> argparse.Namespace:
    """Get arguments

    Returns
    -------
    args : argparse.Namespace
        Argument parameters
    """

    class CustomHelpFormatter(argparse.RawTextHelpFormatter):
        def __init__(self, prog, indent_increment=2, max_help_position=40, width=None):
            super().__init__(prog, indent_increment, max_help_position, width)

    format_list = ["newick", "phyloxml", "nexus", "nexml", "cdao"]

    desc = "Simple phylogenetic tree visualization CLI tool"
    parser = argparse.ArgumentParser(
        description=desc,
        add_help=False,
        formatter_class=CustomHelpFormatter,
        epilog=f"Available Tree Format: {format_list}",
    )

    #######################################################
    # General options
    #######################################################
    general_opts = parser.add_argument_group("General Options")
    general_opts.add_argument(
        "-i",
        "--intree",
        type=str,
        help="Input phylogenetic tree file or text",
        required=True,
        metavar="IN",
    )
    general_opts.add_argument(
        "-o",
        "--outfile",
        type=Path,
        help="Output phylogenetic tree plot file [*.png|*.jpg|*.svg|*.pdf]",
        required=True,
        metavar="OUT",
    )
    default_tree_format = "newick"
    general_opts.add_argument(
        "--format",
        type=str,
        help=f"Input phylogenetic tree format (Default: '{default_tree_format}')",
        default=default_tree_format,
        choices=format_list,
        metavar="",
    )
    general_opts.add_argument(
        "-v",
        "--version",
        version=f"v{phytreeviz.__version__}",
        help="Print version information",
        action="version",
    )
    general_opts.add_argument(
        "-h",
        "--help",
        help="Show this help message and exit",
        action="help",
    )

    #######################################################
    # Figure appearence options
    #######################################################
    fig_opts = parser.add_argument_group("Figure Appearence Options")
    default_height = 0.5
    fig_opts.add_argument(
        "--fig_height",
        type=float,
        help=f"Figure height per leaf node of tree (Default: {default_height})",
        default=default_height,
        metavar="",
    )
    default_width = 8.0
    fig_opts.add_argument(
        "--fig_width",
        type=float,
        help=f"Figure width (Default: {default_width})",
        default=default_width,
        metavar="",
    )
    default_leaf_label_size = 12
    fig_opts.add_argument(
        "--leaf_label_size",
        type=int,
        help=f"Leaf label size (Default: {default_leaf_label_size})",
        default=default_leaf_label_size,
        metavar="",
    )
    fig_opts.add_argument(
        "--ignore_branch_length",
        help="Ignore branch length for plotting tree (Default: OFF)",
        action="store_true",
    )
    fig_opts.add_argument(
        "--align_leaf_label",
        help="Align leaf label position (Default: OFF)",
        action="store_true",
    )
    fig_opts.add_argument(
        "--show_branch_length",
        help="Show branch length (Default: OFF)",
        action="store_true",
    )
    fig_opts.add_argument(
        "--show_confidence",
        help="Show confidence (Default: OFF)",
        action="store_true",
    )
    default_dpi = 300
    fig_opts.add_argument(
        "--dpi",
        type=int,
        help=f"Figure DPI (Default: {default_dpi})",
        default=default_dpi,
        metavar="",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
