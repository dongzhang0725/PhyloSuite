from ete3 import Tree
from ete3 import Tree, TreeStyle, TextFace
t = Tree( "((((a,b),c), d), e);" )

def abc_layout(node):
    vowels = set(["a", "e", "i", "o", "u"])
    if node.name in vowels:

        # Note that node style are already initialized with the
        # default values

        node.img_style["size"] = 15
        node.img_style["bgcolor"] = "red"

# Basic tree style
ts = TreeStyle()
ts.show_leaf_name = True
ts.layout_fn = abc_layout
# Add two text faces to different columns
tf1 = TextFace("hola ")
setattr(tf1, "tt", "test tf1")
tf2 = TextFace("hola ")
setattr(tf2, "tt", "test tf2")
t.add_face(tf1, column=0, position = "float")
t.add_face(tf2, column=1, position = "float")
list_faces = []
for i in set(["branch-right", "branch-top", "branch-bottom", "float", "float-behind", "aligned"]):
    list_faces += list(getattr(t.faces, i).values())
print(list_faces)
getattr(t.faces, "float").pop(0)
# print(t.faces == t._faces)
t.show(tree_style=ts)