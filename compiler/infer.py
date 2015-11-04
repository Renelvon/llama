"""
# ----------------------------------------------------------------------
# infer.py
#
# Type inference for Llama
# http://courses.softlab.ntua.gr/compilers/2012a/llama2012.pdf
#
# Authors: Nick Korasidis <renelvon@gmail.com>
#          Dimitris Koutsoukos <dim.kou.shmmy@gmail.com>
# ----------------------------------------------------------------------
"""
from collections import namedtuple


class PartialType:

    """
    Special type denoting a not fully specified type.

    This type is only used during semantic analysis.
    """

    id_count = 0
    lineno = None
    lexpos = None

    def __init__(self, node=None):
        """
        Construct a new temporary type; the type may be optionally
        bound to an AST `node`.
        """
        if node is not None:
            assert isinstance(node, ast.DataNode), \
                'Cannot make PartialType for untyped AST node.'
            self.node = node

        self.type_id = self._get_next_id()

    def copy_pos(self, node):
        """Copy line info from another AST node."""
        self.lineno = node.lineno
        self.lexpos = node.lexpos

    def pos_to_str(self):
        """Return node position as a string."""
        if self.node is not None:
            return self.node.pos_to_str()
        elif self.lineno is None:
            return ''
        elif self.lexpos is None:
            return '%d:' % self.lineno
        else:
            return "%d:%d:" % (self.lineno, self.lexpos)

    @classmethod
    def _get_next_id(cls):
        cls.id_count += 1
        return cls.id_count

    def __str__(self):
        return '@' + self.type_id

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.type_id == other.type_id
        return False

    def __hash__(self):
        return hash(self.type_id)


# == CONSTRAINTS ==

# A constraint enforcing two PartialTypes to unify.
EquConstraint = namedtuple('EquConstraint', type1, type2)

# A constraint enforcing a PartialType to unify with one type
# from a set of concrete types.
# Note: This is actually only used in comparison operators.
SetConstraint = namedtuple('SetConstraint', type1, good_set)

# A constraint forbidding a PartialType from unifying with an
# array type.
NotArrayConstraint = namedtuple('NotArrayConstraint', type1)

# A constraint forbidding a PartialType from unifying with a
# function type.
NotFuncConstraint = namedtuple('NotFuncConstraint', type1)

# A lower-bound constraint for the dimensions of an array.
ArrayDimConstraint = namedtuple('ArrayDimConstraint', type1, dimension)
