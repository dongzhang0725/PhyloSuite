# from __future__ import annotations

from pathlib import Path


def load_example_tree_file(filename: str) -> Path:
    """Load example phylogenetic tree file

    List of example tree filename

    - `small_example.nwk` (7 species)
    - `medium_example.nwk` (21 species)
    - `large_example.nwk` (190 species)

    Parameters
    ----------
    filename : str
        Target filename

    Returns
    -------
    tree_file : Path
        Tree file (Newick format)
    """
    example_data_dir = Path(__file__).parent / "example_data"
    example_files = example_data_dir.glob("*.nwk")
    available_filenames = [f.name for f in example_files]
    if filename not in available_filenames:
        raise ValueError(f"{filename} is invalid.\n{available_filenames})")
    target_file = example_data_dir / filename
    return target_file
