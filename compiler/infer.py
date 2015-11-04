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

    # pylint: disable=too-many-instance-attributes
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

    # == CONSTRAINT RESOLUTION ==

    def resolve(self):
        self._resolve_constructive_constraints()
        self._ensure_concrete_mappings()
        self._resolve_nonconstructive_constraints()
        self._write_back()

    def _resolve_constructive_constraints(self):
        while self._constructive_constraints:
            c = self._constructive_constraints.popleft()
            self._unify(c.type1, c.type2)

    def _unify(self, type1, type2):
        ftype1, ftype2 = self._find(type1), self._find(type2)
        if isinstance(ftype1, PartialType):
            if isinstance(ftype2, PartialType):
                self._unify_partial_partial(ftype1, ftype2)
            else:
                self._unify_partial_concrete(ftype1, ftype2)
        elif isinstance(ftype2, PartialType):
            self._unify_partial_concrete(ftype2, ftype1)
        else:
            self._unify_concrete_concrete(ftype1, ftype1)

    def _unify_partial_partial(self, type1, type2):
        if type1 != type2:
            self._link_to(type1, type2)

    def _unify_partial_concrete(self, type1, type2):
        if self._occurs_in(type1, type2):
            err = OccursInError(
                self._find(type1),
                self._upgrade_to_reps(type2)
            )
            self.logger.error(str(err))
        else:
            self._type_map[type1] = UFTuple(type2, 1)

    def _unify_concrete_concrete(self, type1, type2):
        if not isinstance(type1, type2):
            err = IncompatibleTypesError(type1, type2)
            self.logger.error(str(err))
        elif isinstance(type1, ast.Array):
            self._unify_array(type1, type2)
        elif isinstance(type1, ast.Function):
            self._unify_function(type1, type2)
        elif isinstance(type1, ast.Ref):
            self._unify_ref(type1, type2)
        else:
            self._unify_builtin(type1, type2)

    def _unify_array(self, type1, type2):
        if type1.dimensions != type2.dimensions:
            err = IncompatibleArrayDimError(type1, type2)
            self.logger.error(str(err))
        else:
            self._constructive_constraints.appendleft(
                EquConstraint(type1.type, type2.type)
            )

    def _unify_builtin(self, type1, type2):
        if type1.name != type2.name:
            err = IncompatibleTypesError(type1, type2)
            self.logger.error(str(err))

    def _unify_function(self, type1, type2):
        self._constructive_constraints.appendleft(
            EquConstraint(type1.fromType, type2.fromType)
        )
        self._constructive_constraints.appendleft(
            EquConstraint(type1.toType, type2.toType)
        )

    def _unify_ref(self, type1, type2):
        self._constructive_constraints.appendleft(
            EquConstraint(type1.type, type2.type)
        )

    def _ensure_concrete_mappings(self):
        for t, m in self._type_map.items():
            mtype = m.type
            if mtype is None or isinstance(mtype, PartialType):
                err = AbstractTypeError(t)
                self.logger.error(str(err))

    def _resolve_nonconstructive_constraints(self):
        self._resolve_set_constraints()
        self._resolve_not_func_constraints()
        self._resolve_not_array_constraints()
        self._resolve_array_dimensions_constraints()

    def _resolve_set_constraints(self):
        for c in self._set_constraints:
            if not isinstance(c.type1, c.good_set):
                err = BadSetTypeError(c.type1, c.good_set)
                self.logger.error(str(err))

    def _resolve_not_func_constraints(self):
        for c in self._not_func_constraints:
            if isinstance(c.type1, ast.Function):
                err = TypeIsFunctionError(c.type1)
                self.logger.error(str(err))

    def _resolve_not_array_constraints(self):
        for c in self._not_array_constraints:
            if isinstance(c.type1, ast.Array):
                err = TypeIsArrayError(c.type1)
                self.logger.error(str(err))

    def _resolve_array_dimensions_constraints(self):
        for c in self._array_dimensions_constraints:
            if not (
                self._type_table.is_array(c.type1)
                and (c.type1.dimensions >= c.size)
            ):
                err = ArrayDimensionError(c.type1, c.size)
                self.logger.error(str(err))

    def _write_back(self):
        for t, m in self._type_map.items():
            mtype = m.type
            try:
                self._type_table.validate(mtype)
            except typesem.InvalidTypeError as err:
                self.logger.error(str(err))
            else:
                if t.node is not None:
                    t.node.type = mtype

    # == TYPE MANAGEMENT ==

    def get_type_handle(self, node):
        if not isinstance(node.type, PartialType):
            new_type = self.make_new_type_referencing(node)
            new_type.node = node
        return node.type

    def make_new_type_referencing(self, node):
        new_pt = PartialType()
        new_pt.copy_pos(node)
        self._type_map[new_pt] = UFTuple(node.type, 1)
        return new_pt

    # == AUXILIARY METHODS ==

    def _find(self, base_type):
        # Optimize: Path compression
        children = []
        while isinstance(base_type, PartialType):
            next_type = self._type_map[base_type].type
            if next_type is None:
                break
            else:
                children.append(base_type)
                base_type = next_type
        for c in children:
            self._link_to(c, base_type)
        return base_type

    def _link_to(self, type1, type2):
        sz1, sz2 = self._type_map[type1].size, self._type_map[type2].size
        if sz1 <= sz2:  # Weighted-Union
            self._type_map[type1] = UFTuple(type2, sz1)
            self._type_map[type2] = UFTuple(None, sz1 + sz2)
        else:
            self._type_map[type2] = UFTuple(type1, sz2)
            self._type_map[type1] = UFTuple(None, sz1 + sz2)

    def _occurs_in(self, type1, type2):
        assert isinstance(type1, PartialType), 'Bad logic'
        free_types2 = self._get_free_types(type2)
        ftype1 = self._find(type1)
        return any(ftype1 == self._find(ft) for ft in free_types2)

    def _get_free_types(self, ttype):
        # TODO: Optimize
        if isinstance(ttype, PartialType):
            return [ttype]
        elif isinstance(ttype, ast.Function):
            free1 = self._get_free_types(ttype.fromType)
            free2 = self._get_free_types(ttype.toType)
            return free1 + free2
        elif isinstance(ttype, (ast.Ref, ast.Array)):
            return self._get_free_types(ttype.type)
        else:
            return []

    def _upgrade_to_reps(self, ttype):
        if isinstance(ttype, PartialType):
            return self._find(ttype)
        elif isinstance(ttype, ast.Function):
            new_type = ast.Function(
                self._upgrade_to_reps(ttype.fromType),
                self._upgrade_to_reps(ttype.toType)
            )
            new_type.copy_pos(ttype)
            return new_type
        elif isinstance(ttype, ast.Ref):
            new_type = ast.Ref(self._upgrade_to_reps(ttype.type))
            new_type.copy_pos(ttype)
            return new_type
        elif isinstance(ttype, ast.Array):
            new_type = ast.Array(
                self._upgrade_to_reps(ttype.type),
                ttype.dimensions
            )
            new_type.copy_pos(ttype)
            return new_type
        else:
            return ttype
