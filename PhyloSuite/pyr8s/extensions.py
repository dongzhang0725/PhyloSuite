#-----------------------------------------------------------------------------
# Pyr8s - Divergence Time Estimation
# Copyright (C) 2021  Patmanidis Stefanos
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#-----------------------------------------------------------------------------


"""
Extend dendropy trees with utility functions and attributes.
"""

import dendropy

##############################################################################
### Utility function definitions

class NodePlus(dendropy.Node):

    decorator = '[{}]'

    @property
    def label(self):
        if self.__label_frozen is not None:
            return self.__label_frozen
        try:
            return self.taxon.label
        except:
            if self.__label is not None and self.__label != '':
                return self.__label
            elif self.index is not None:
                return self.decorator.format(self.index)
            else:
                return self.decorator.format('?')

    @label.setter
    def label(self, value):
        self.__label = value
        self.__label_frozen = None

    @classmethod
    def extend(cls, node):
        """Convert from dendropy.Node"""
        node.__label_frozen = None
        node.__label = node.label
        node.__class__ = cls
        node.index = None
        node.order = None
        node.fix = None
        node.min = None
        node.max = None
        node.rate = None
        node.subs = None

    @classmethod
    def strip(cls, node):
        """Revert to dendropy.Node"""
        del node.index
        del node.order
        del node.fix
        del node.min
        del node.max
        del node.rate
        del node.subs
        node.__class__ = dendropy.Node
        node.label = node.__label
        del node.__label
        del node.__label_frozen

    def label_freeze(self):
        """Freeze current label"""
        self.__label_frozen = self.label

    def label_unfreeze(self):
        """Forget frozen label"""
        self.__label_frozen = None

    def child_node_reversed_iter(self, filter_fn=None):
        """Reversed order"""
        for node in reversed(self._child_nodes):
            if filter_fn is None or filter_fn(node):
                yield node

    def add_child_after(self, node, child):
        """Insert child in list of children immediately after node index"""
        assert child is not self, "Cannot add node as child of itself"
        assert self._parent_node is not child, "Cannot add a node's parent as its child: remove the node from its parent's child set first"
        index = self._child_nodes.index(node) + 1
        child._parent_node = self
        if child not in self._child_nodes:
            self._child_nodes.insert(index, child)
        return child

    def is_terminal_zero(self):
        """This special case is ignored by analysis array construction"""
        return self.subs == 0 and self.is_leaf()

    def all_children_terminal_zero(self):
        """Checks if all children are terminal zeros"""
        for node in self.child_node_iter():
            if not node.is_terminal_zero():
                return False
        return True


class TreePlus(dendropy.Tree):

    nameless = 'Nameless'

    @property
    def label(self):
        if self.__label is None:
            return self.nameless
        else:
            return self.__label

    @label.setter
    def label(self, value):
        self.__label = value

    @classmethod
    def extend(cls, tree):
        """Convert from dendropy.Tree"""
        tree.__label = tree.label
        tree.__class__ = cls
        for node in tree.nodes():
            NodePlus.extend(node)

    @classmethod
    def strip(cls, tree):
        """Revert to dendropy.Tree"""
        for node in tree.nodes():
            NodePlus.strip(node)
        tree.__class__ = dendropy.Tree
        tree.label = tree.__label
        del tree.__label

    def collapse(self, throw=False):
        """
        Remove edges with zero length.
        Prints warning or raises error depending on flag.
        """
        collapsed_constraints = self._collapse_inner()
        if collapsed_constraints != []:
            if not throw:
                print('WARNING: Collapsed nodes with constraints:')
                for n in collapsed_constraints:
                    print('* {0}: fix={1}, min={2}, max={3}'.
                        format(n.label, n.fix, n.min, n.max))
                print('')
            else:
                raise RuntimeError('Collapsed nodes with constraints: {}'.
                    format(collapsed_constraints))

    def _collapse_inner(self):
        """
        Remove edges with zero length. Must be called after calc_subs().
        Return a list with any constrained nodes that were pruned.
        """
        remove = []
        collapsed_constraints = []

        # Children before parent, ensures removal is done in proper order
        for node in self.postorder_node_iter_noroot():
            if node.is_terminal_zero():
                parent = node.parent_node
                if node.fix != 0:
                    raise RuntimeError('Terminal zero-length branches must have their node age fixed to 0: {}'.
                        format(node.label))
                elif parent.min is None:
                    parent.min = 0
            elif node.subs == 0:
                remove.append(node)
                if any([node.fix, node.min, node.max]):
                    if not node.all_children_terminal_zero():
                        collapsed_constraints.append(node)

        # Remove the nodes, parents inherit children
        for node in remove:
            # Constraints passed to parents and children
            if node.fix is not None:
                node.max = node.fix
                node.min = node.fix
            parent = node.parent_node
            for child in node.child_node_reversed_iter():
                parent.add_child_after(node, child)
                if node.max is not None:
                    if child.max is not None:
                        child.max = min(child.max, node.max)
                    if child.max is None and child.fix is None:
                        child.max = node.max
            if node.min is not None:
                if parent.min is not None:
                    parent.min = max(parent.min, node.min)
                if parent.min is None and parent.fix is None:
                    parent.min = node.min
            parent.remove_child(node)

        return collapsed_constraints

    def calc_subs(self, multiplier, doround):
        """
        Set substitutions for each node
        """
        for node in self.postorder_node_iter_noroot():
            length = node.edge_length
            if length is None:
                raise ValueError('Null length for node {0}'.
                    format(node.label))
            if length <= 0:
                length = 0
            if multiplier is not None:
                length *= multiplier
            if doround == True:
                length = round(length)
            node.subs = length

    def ground(self):
        """
        Fix leaf age to zero if no calibrations exist
        """
        for node in self.postorder_node_iter_noroot():
            if node.is_leaf() and not any([node.fix, node.max, node.min]):
                node.fix = 0

    def index(self, filter_fn=None):
        """Assign node indexes according to BF traversal order"""
        for count, node in enumerate(self.preorder_node_iter(filter_fn)):
            node.index = count
        self._indexed = True

    def order(self, filter_fn=None):
        """
        Assign order to each node of tree
        where order is the max distance from the leaves
        """

        def _order_recurse(node):
            """For each node, get max order of children + 1"""

            if node.is_leaf():
                node.order = 0
                return 0

            max_child_order = 0
            for child in node.child_node_iter(filter_fn):
                some_order = _order_recurse(child)
                max_child_order = max(max_child_order, some_order)
            max_child_order += 1
            node.order = max_child_order
            return max_child_order

        _order_recurse(self.seed_node)
        self._ordered = True

    def label_mrca(self,mrca,labels):
        """
        Rename most recent common ancestor of given nodes
        Nodes are given with their label
        If a single node is given, it is renamed
        Create the taxon if needed.
        """
        ancestor = self.mrca(taxon_labels=labels)
        if ancestor.taxon == None:
            ancestor.taxon = self.taxon_namespace.new_taxon(str(mrca))
        ancestor.taxon.label = str(mrca)
        ancestor.label = str(mrca)

    def persite(self, nsites, round_flag=False):
        """
        DEPRECATED
        Use this when branch lengths are in units of numbers of substitutions per site
        This will multiply each branch length, rounding by default
        """
        for node in self.preorder_node_iter():
            if node.edge_length != None:
                node.edge_length *= nsites
            if round_flag == True:
                node.edge_length = round(node.edge_length)

    def preorder_node_iter_noroot(self, filter_fn=None):
        """
        See Tree.preorder_node_iter, except this excludes root
        """
        stack = [n for n in reversed(self.seed_node._child_nodes)]
        while stack:
            node = stack.pop()
            if filter_fn is None or filter_fn(node):
                yield node
            stack.extend(n for n in reversed(node._child_nodes))

    def postorder_node_iter_noroot(self, filter_fn=None):
        """
        See Tree.postorder_node_iter, except this excludes root
        """
        stack = [(n, False) for n in reversed(self.seed_node._child_nodes)]
        while stack:
            node, state = stack.pop()
            if state:
                if filter_fn is None or filter_fn(node):
                    yield node
            else:
                stack.append((node, True))
                stack.extend([(n, False) for n in reversed(node._child_nodes)])

    def label_freeze(self):
        """Freeze labels for all nodes"""
        for node in self.preorder_node_iter():
            node.label_freeze()
