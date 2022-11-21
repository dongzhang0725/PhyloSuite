import random
from ete3 import Tree, TreeStyle, NodeStyle, faces, AttrFace, TreeFace, TextFace

# Tree Style used to render small trees used as leaf faces
small_ts = TreeStyle()
small_ts.show_leaf_name = True
small_ts.scale = 10

def get_example_tree():
    # Random tree
    t = Tree()
    t.populate(20, random_branches=True)

    # Some random features in all nodes
    for n in t.traverse():
        n.add_features(weight=random.randint(0, 50))

    # Create an empty TreeStyle
    ts = TreeStyle()

    # Draw a tree
    ts.mode = "r"

    # We will add node names manually
    ts.show_leaf_name = False
    # Show branch data
    ts.show_branch_length = True
    ts.show_branch_support = True
    ts.show_scale = False
    return t, ts

if __name__ == "__main__":
    t1, ts1 = get_example_tree()
    ts1.legend.add_face(TextFace("Tree 1"), column=0)
    ts1.legend_position = 1
    ts1.margin_bottom = 40
    ts1.margin_right = 100

    t2, ts2 = get_example_tree()
    ts2.legend.add_face(TextFace("Tree 2"), column=0)
    ts2.legend_position = 2
    ts2.margin_bottom = 40

    # Trying to reproduce this
    #
    #  t1  |  t2

    # The order in which the faces are added matter here

    # add t2 to the right of t1
    face2 = TreeFace(t2, ts2)
    ts1.aligned_treeface_hz.add_face(face2, column=0)
    ts2.orientation = 1

    # t1.render("tree_stacking.png", w=600, dpi=300, tree_style=ts1)
    t1.show(tree_style=ts1)