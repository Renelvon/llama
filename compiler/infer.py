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
from collections import namedtuple, deque

from compiler import ast, error


class AbstractTypeError(Exception):

    """
    Exception thrown on detecting an abstract type after inference.
    """

    _err_level = 'error: '

    def __init__(self, type1):
        """Create a new exception carrying the offending type and size."""
        self.type1 = type1

    def __str__(self):
        """Format and return the exception's message."""
        return '{0}{1}Cannot infer concrete instance for type {2}.'.format(
            self.type1.pos_to_str(),
            self._err_level,
            str(self.type1)
        )


class ArrayDimensionError(Exception):

    """
    Exception thrown on detecting an array of insufficient dimensions.
    """

    _err_level = 'error: '

    def __init__(self, type1, size):
        """Create a new exception carrying the offending type and size."""
        self.type1 = type1
        self.size = size

    def __str__(self):
        """Format and return the exception's message."""
        return '{0}{1}Type {2} has less than {3} dimensions.'.format(
            self.type1.pos_to_str(),
            self._err_level,
            str(self.type1),
            self.size
        )


class BadSetTypeError(Exception):

    """Exception thrown on detecting a type outside a specified set."""

    _err_level = 'error: '

    def __init__(self, type1, bad_set):
        """
        Create a new exception carrying the offending type and the
        expected set.
        """
        self.type1 = type1
        self.bad_set = bad_set

    def __str__(self):
        """Format and return the exception's message."""
        return '{0}{1}Type {2} is outside allowed set ({3})'.format(
            self.type1.pos_to_str(),
            self._err_level,
            str(self.type1),
            ','.join(str(t) for t in self.bad_set)
        )


class IncompatibleTypesError(Exception):

    """Exception thrown on detecting two types than cannot be unified."""

    _err_level = 'error: '

    def __init__(self, type1, type2):
        """
        Create a new exception carrying the offending type and the
        expected set.
        """
        self.type1 = type1
        self.type2 = type2

    def __str__(self):
        """Format and return the exception's message."""
        return '{0}{1}Type {2} cannot be unified with {3}'.format(
            self.type1.pos_to_str(),
            self._err_level,
            str(self.type1),
            str(self.type2),
        )


class IncompatibleArrayDimError(Exception):

    """Exception thrown on two arrays of incompatible dimensions."""

    _err_level = 'error: '

    def __init__(self, type1, type2):
        """
        Create a new exception carrying the offending type and the
        expected set.
        """
        self.type1 = type1
        self.type2 = type2

    def __str__(self):
        """Format and return the exception's message."""
        return '{0}{1}Dimension mismatch: cannot unify {2} with {3}'.format(
            self.type1.pos_to_str(),
            self._err_level,
            str(self.type1),
            str(self.type2),
        )


class OccursInError(Exception):

    """Exception thrown on detecting occurs-check violation."""

    _err_level = 'error: '

    def __init__(self, type1, type2):
        """
        Create a new exception carrying the offending type and the
        expected set.
        """
        self.type1 = type1
        self.type2 = type2

    def __str__(self):
        """Format and return the exception's message."""
        return '{0}{1}Infinite type: {2} cannot be unified with {3}'.format(
            self.type1.pos_to_str(),
            self._err_level,
            str(self.type1),
            str(self.type2),
        )


class TypeIsArrayError(Exception):

    """Exception thrown on detecting a forbidden array type."""

    _err_level = 'error: '

    def __init__(self, type1):
        """Create a new exception carrying the offending type."""
        self.type1 = type1

    def __str__(self):
        """Format and return the exception's message."""
        return '{0}{1}Array type is forbidden for respective node.'.format(
            self.type1.pos_to_str(),
            self._err_level,
        )


class TypeIsFunctionError(Exception):

    """Exception thrown on detecting a forbidden function type."""

    _err_level = 'error: '

    def __init__(self, type1):
        """Create a new exception carrying the offending type."""
        self.type1 = type1

    def __str__(self):
        """Format and return the exception's message."""
        return '{0}{1}Function type is forbidden for respective node.'.format(
            self.type1.pos_to_str(),
            self._err_level,
        )


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


class Inferer:

    """
    The type inference engine.

    Designed for a Hindley-Milner-ish type system that includes
    a couple of extensions for imperative programming, such
    as references and arrays.
    """

    # == CONSTRAINTS ==

    # A constraint enforcing two PartialTypes to unify.
    EquConstraint = namedtuple('EquConstraint', ('type1', 'type2'))

    # A constraint enforcing a PartialType to unify with one type
    # from a set of concrete types.
    # Note: This is actually only used in comparison operators.
    SetConstraint = namedtuple('SetConstraint', ('type1', 'good_set'))

    # A constraint forbidding a PartialType from unifying with an
    # array type.
    NotArrayConstraint = namedtuple('NotArrayConstraint', ('type1',))

    # A constraint forbidding a PartialType from unifying with a
    # function type.
    NotFuncConstraint = namedtuple('NotFuncConstraint', ('type1',))

    # A lower-bound constraint for the dimensions of an array.
    ArrayDimConstraint = namedtuple(
        'ArrayDimConstraint',
        ('type1', 'dimension')
    )

    # A tuple for the Union-Find engine.
    UFTuple = namedtuple('UFTuple', ('type', 'size'))

    def __init__(self, type_table, logger=None):
        self._type_table = type_table
        if logger is None:
            self.logger = error.Logger()
        else:
            self.logger = logger

        self._type_map = {}
        self._constructive_constraints = deque()
        self._set_constraints = []
        self._not_func_constraints = []
        self._not_array_constraints = []
        self._array_dimensions_constraints = []

    # == CONSTRAINT GENERATION ==

    def constrain_nodes_equtyped(self, node1, node2):
        self._constructive_constraints.append(
            EquConstraint(
                self.get_type_handle(node1),
                self.get_type_handle(node2)
            )
        )

    def constrain_node_having_type(self, node, concrete_type):
        self._constructive_constraints.append(
            EquConstraint(self.get_type_handle(node), concrete_type)
        )

    def constrain_node_having_one_of_types(self, node, concrete_types):
        self._set_constraints.append(
            SetConstraint(self.get_type_handle(node), concrete_types)
        )

    def constrain_node_being_array_of_dimensions_at_least(self, node, n):
        self._array_dimensions_constraints.append(
            ArrayDimConstraint(self.get_type_handle(node), n)
        )

    def constrain_node_not_being_function(self, node):
        self._not_func_constraints.append(
            NotFuncConstraint(self.get_type_handle(node))
        )

    def constrain_node_not_being_array(self, node):
        self._not_array_constraints.append(
            NotArrayConstraint(self.get_type_handle(node))
        )





