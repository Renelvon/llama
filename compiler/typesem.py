"""
# ----------------------------------------------------------------------
# type.py
#
# Semantic analysis of types
# http://courses.softlab.ntua.gr/compilers/2012a/llama2012.pdf
#
# Authors: Nick Korasidis <renelvon@gmail.com>
#          Dimitris Koutsoukos <dim.kou.shmmy@gmail.com>
#          Dionysis Zindros <dionyziz@gmail.com>
# ----------------------------------------------------------------------
"""

from compiler import ast

# == INVALID TYPE ERRORS ==


class InvalidTypeError(ast.NodeError):
    """
    Exception thrown on detecting an invalid type or
    a bad type declaration.
    This class is only meant as an ABC.
    Only specific subclasses should be instantiated.
    """
    _node_error_msg = "Invalid type"


class ArrayOfArrayError(InvalidTypeError):
    """Exception thrown on detecting an array of arrays."""
    _node_error_msg = "Invalid type: array of array"


class ArrayReturnError(InvalidTypeError):
    """Exception thrown on detecting a function returning an array."""
    _node_error_msg = "Invalid type: function returning array"


class RefOfArrayError(InvalidTypeError):
    """Exception thrown on detecting a ref to an array."""
    _node_error_msg = "Invalid type: ref of array"


class RedefBuiltinTypeError(InvalidTypeError):
    """Exception thrown on detecting redefinition of builtin type."""
    @property
    def _node_error_msg(self):
        return "Redefining builtin type %s" % self.node.name


class UndefConstructorError(InvalidTypeError):
    """Exception thrown on detecting reference to undefined constructor."""
    @property
    def _node_error_msg(self):
        return "Undefined constructor: %s" % self.node.name


class RedefConstructorError(InvalidTypeError):
    """Exception thrown on detecting redefinition of constructor."""
    @property
    def _node_error_msg(self):
        return "Redefining constructor %s" % self.node.name

    _prev_error_msg = " previous definition"


class RedefUserTypeError(InvalidTypeError):
    """Exception thrown on detecting redefinition of user type."""
    @property
    def _node_error_msg(self):
        return "Redefining user type %s" % self.node.name

    _prev_error_msg = " previous definition"


class UndefTypeError(InvalidTypeError):
    """Exception thrown on detecting reference to undefined type."""
    @property
    def _node_error_msg(self):
        return "Undefined type: %s" % self.node.name

# == TYPE VALIDATION & USER-TYPE STORAGE/PROCESSING ==


def is_array(t):
    """Check if a type is an array type."""
    return isinstance(t, ast.Array)


class Table:
    """
    Database of all the program's types. Enables semantic checking
    of user defined types and more.
    """

    def __init__(self):
        """Initialize a new Table."""
        # Dictionary of types seen so far. Builtin types always available.
        # Keys  : names of types
        # Values: (definition node, constructors list)
        self._known_types = dict()
        for typecon in ast.builtin_types_map.values():
            type_instance = typecon()
            self._known_types[type_instance.name] = (type_instance, [])

        # Dictionary of constructors encountered so far.
        # Keys : Name of constructor
        # Value: (definition node, produced type)
        self._known_constructors = dict()

        # Bulk-add dispatching for builtin types.
        self._dispatcher = {
            typecon: self._validate_builtin
            for typecon in ast.builtin_types_map.values()
        }

        # Add dispatching for other types.
        self._dispatcher.update((
            (ast.Array, self._validate_array),
            (ast.Function, self._validate_function),
            (ast.Ref, self._validate_ref),
            (ast.User, self._validate_user)
        ))

    def _validate_array(self, t):
        """An 'array of T' type is valid iff T is a valid, non-array type."""
        basetype = t.type
        if is_array(basetype):
            raise ArrayOfArrayError(t)
        self.validate(basetype)

    def _validate_builtin(self, _):
        """A builtin type is always valid."""
        return

    def _validate_function(self, t):
        """
        A 'T1 -> T2' type is valid iff T1 is a valid type and T2 is a
        valid, non-array type.
        """
        t1, t2 = t.fromType, t.toType
        if is_array(t2):
            raise ArrayReturnError(t)
        self.validate(t1)
        self.validate(t2)

    def _validate_ref(self, t):
        """A 'ref T' type is valid iff T is a valid, non-array type."""
        basetype = t.type
        if is_array(basetype):
            raise RefOfArrayError(t)
        self.validate(basetype)

    def _validate_user(self, t):
        """A user-defined type is valid, unless referencing an unknown type."""
        if t.name not in self._known_types:
            raise UndefTypeError(t)

    def validate(self, t):
        """
        Verify that a type is a valid type, i.e. ensures type structure
        and semantics follow language spec.
        """
        return self._dispatcher[type(t)](t)

    def _insert_new_type(self, new_type):
        """
        Insert newly defined type in Table. Signal error on redefinition.
        """
        existing_type, _ = self._known_types.get(new_type.name, (None, []))
        if existing_type is None:
            self._known_types[new_type.name] = (new_type, [])
            return

        if isinstance(existing_type, ast.Builtin):
            raise RedefBuiltinTypeError(new_type)
        else:
            raise RedefUserTypeError(new_type, existing_type)

    def _insert_new_constructor(self, new_type, new_constructor):
        """
        Insert new constructor in Table. Signal error if constructor is reused
        or arguments are invalid types.
        """
        existing_constructor, _ = self._known_constructors.get(
            new_constructor.name, (None, None)
        )
        if existing_constructor is None:
            self._known_types[new_type.name][1].append(new_constructor)
            self._known_constructors[new_constructor.name] = (
                new_constructor, new_type
            )

            for argType in new_constructor:
                self.validate(argType)
        else:
            raise RedefConstructorError(new_constructor, existing_constructor)

    def process(self, type_defs):
        """
        Analyse a user-defined type. Perform semantic checks
        and insert type in the TypeTable.
        """
        # First, insert all newly-defined types.
        for tdef in type_defs:
            self._insert_new_type(tdef.type)

        # Then, process each constructor and its arguments.
        for tdef in type_defs:
            new_type = tdef.type
            for constructor in tdef:
                self._insert_new_constructor(new_type, constructor)

        # TODO: Emit warnings when typenames clash with definition names.

    def lookup_type(self, name):
        """
        Lookup the type named and retrieve stored info.

        If the type is found, a tuple is returned. The tuple contains
        the definition node of that type and a list of defined constructors,
        in that order. If the type doesn't exist, None is returned.
        """
        return self._known_types.get(name)

    def lookup_constructor(self, name):
        """
        Lookup the constructor named and retrieve stored info.

        If the constructor is found, a tuple is returned. The tuple
        contains the definition node of that constructor and a the node
        of the produced type, in that order. If the constructor doesn't
        exist, None is returned.
        """
        return self._known_constructors.get(name)
