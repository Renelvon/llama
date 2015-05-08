"""
# ----------------------------------------------------------------------
# ast.py
#
# AST constructors for the Llama language
# http://courses.softlab.ntua.gr/compilers/2012a/llama2012.pdf
#
# Authors: Dionysis Zindros <dionyziz@gmail.com>
#          Nick Korasidis <renelvon@gmail.com>
#
# ----------------------------------------------------------------------
"""

import abc
import collections.abc

# pylint: disable=redefined-builtin
# == INTERFACES OF AST NODES ==


class Node(metaclass=abc.ABCMeta):
    lineno = None
    lexpos = None

    @abc.abstractmethod
    def __init__(self):
        return

    def __eq__(self, other):
        """
        Two nodes are equal if they are of the same type
        and have all attributes equal. Override as needed.
        """
        # pylint: disable=unidiomatic-typecheck
        return type(self) == type(other) and all(
            getattr(self, attr) == getattr(other, attr)
            for attr in self.__dict__.keys()
            if attr not in ('lineno', 'lexpos')
        )

    def copy_pos(self, node):
        """Copy line info from another AST node."""
        self.lineno = node.lineno
        self.lexpos = node.lexpos

    def pos_to_str(self):
        """Return node position as a string."""
        if self.lineno is None:
            return ""

        if self.lexpos is None:
            return "%d:" % self.lineno

        return "%d:%d:" % (self.lineno, self.lexpos)

    def __repr__(self):
        attrs = [attr for attr in dir(self) if attr[0] != '_']
        values = [getattr(self, attr) for attr in attrs]
        safe_values = []
        for value in values:
            displayable_types = (int, float, bool, str, list, Type, Expression)
            if isinstance(value, displayable_types) or value is None:
                safe_values.append(str(value).replace("\n", "\n\t"))
            else:
                safe_values.append(
                    '(non-scalar of type %s)' % value.__class__.__name__
                )
        pairs = (
            "%s = '%s'" % (attr, value)
            for (attr, value) in zip(attrs, safe_values)
        )
        return "ASTNode:%s with attributes:\n\t* %s" \
               % (self.__class__.__name__, "\n\t* ".join(pairs))


class DataNode(Node):

    """A node to which a definite type can and should be assigned."""

    type = None


class Expression(DataNode):

    """An expression that can be evaluated."""

    pass


class NameNode(collections.abc.Hashable, Node):

    """
    A node with a user-defined name.

    Possibly requires scope-aware disambiguation or checking.
    Provides basic hashing functionality.
    """

    name = None

    def __hash__(self):
        """Simple hash. Override as needed."""
        return hash(self.name)


class Def(NameNode):

    """Definition of a new name."""

    pass


class ArgumentNode(collections.abc.Sequence, Node):

    """
    A node that contains a list of arguments, whose count matters.

    The node may contain other stuff as well.
    """

    arguments = None

    def __getitem__(self, idx):
        return self.arguments[idx]

    def __len__(self):
        return len(self.arguments)


class ListNode(collections.abc.Sequence, Node):

    """
    A node that is in essence just a list of elements.

    The node may not contain other stuff except minor annotations.
    """

    list = None

    def __getitem__(self, idx):
        return self.list[idx]

    def __len__(self):
        return len(self.list)


class Type(Node):

    """A node representing a type."""

    pass


class Builtin(Type, NameNode):

    """One of the builtin types."""

    def __init__(self):
        self.name = self.__class__.__name__.lower()

# == AST REPRESENTATION OF PROGRAM ELEMENTS ==


class Program(ListNode):
    def __init__(self, definitions):
        self.list = definitions


class LetDef(ListNode):
    def __init__(self, definitions, isRec=False):
        self.list = definitions
        self.isRec = isRec


class ConstantDef(Def):
    def __init__(self, name, body, type=None):
        self.name = name
        self.body = body
        self.type = type


class FunctionDef(ArgumentNode, Def):
    def __init__(self, name, arguments, body, type=None):
        self.name = name
        self.arguments = arguments
        self.body = body
        self.type = type


class Param(DataNode, NameNode):
    def __init__(self, name, type=None):
        self.name = name
        self.type = type


class BinaryExpression(Expression):
    def __init__(self, leftOperand, operator, rightOperand):
        self.leftOperand = leftOperand
        self.operator = operator
        self.rightOperand = rightOperand
        self.type = None


class UnaryExpression(Expression):
    def __init__(self, operator, operand):
        self.operator = operator
        self.operand = operand
        self.type = None


class ConstructorCallExpression(ArgumentNode, Expression, NameNode):
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments
        self.type = None


class ArrayExpression(ArgumentNode, Expression, NameNode):
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments
        self.type = None


class ConstExpression(Expression):
    def __init__(self, value, type):
        self.value = value
        self.type = type


class ConidExpression(Expression, NameNode):
    def __init__(self, name):
        self.name = name
        self.type = None


class GenidExpression(Expression, NameNode):
    def __init__(self, name):
        self.name = name
        self.type = None


class DeleteExpression(Expression):
    def __init__(self, expr):
        self.expr = expr
        self.type = None


class DimExpression(Expression, NameNode):
    def __init__(self, name, dimension=1):
        self.name = name
        self.dimension = dimension
        self.type = None


class ForExpression(Expression):
    def __init__(self, counter, startExpr, stopExpr, body, isDown=False):
        self.counter = counter
        self.startExpr = startExpr
        self.stopExpr = stopExpr
        self.body = body
        self.isDown = isDown
        self.type = None


class FunctionCallExpression(ArgumentNode, Expression, NameNode):
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments
        self.type = None


class LetInExpression(Expression):
    def __init__(self, letdef, expr):
        self.letdef = letdef
        self.expr = expr
        self.type = None


class IfExpression(Expression):
    def __init__(self, condition, thenExpr, elseExpr=None):
        self.condition = condition
        self.thenExpr = thenExpr
        self.elseExpr = elseExpr
        self.type = None


class MatchExpression(Expression):
    def __init__(self, expr, clauses):
        self.expr = expr
        self.clauses = clauses
        self.type = None


class Clause(Node):
    def __init__(self, pattern, expr):
        self.pattern = pattern
        self.expr = expr


class Pattern(ArgumentNode, NameNode):
    def __init__(self, name, arguments=None):
        self.name = name
        self.arguments = arguments or []


class GenidPattern(NameNode):
    def __init__(self, name):
        self.name = name


class NewExpression(Expression):
    def __init__(self, type):
        self.type = type


class WhileExpression(Expression):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body
        self.type = None


class VariableDef(Def):
    def __init__(self, name, type=None):
        self.name = name
        self.type = type


class ArrayVariableDef(VariableDef):
    def __init__(self, name, dimensions, type=None):
        self.name = name
        self.dimensions = dimensions
        self.type = type


class TDef(ArgumentNode):
    def __init__(self, type, arguments):
        self.type = type
        self.arguments = arguments


class Constructor(ArgumentNode, NameNode):
    def __init__(self, name, arguments=None):
        self.name = name
        self.arguments = arguments or []

# == REPRESENTATION OF TYPES AS AST NODES ==


class Bool(Builtin):
    pass


class Char(Builtin):
    pass


class Float(Builtin):
    pass


class Int(Builtin):
    pass


class Unit(Builtin):
    pass


builtin_types_map = {
    "bool": Bool,
    "char": Char,
    "float": Float,
    "int": Int,
    "unit": Unit,
}


class User(Type, NameNode):

    """A user-defined type."""

    def __init__(self, name):
        self.name = name


class Ref(Type):
    def __init__(self, type):
        self.type = type


class Array(Type):
    def __init__(self, type, dimensions=1):
        self.type = type
        self.dimensions = dimensions


def String():
    """Factory method to alias (internally) String type to Array of char."""
    return Array(Char(), 1)


class Function(Type):
    def __init__(self, fromType, toType):
        self.fromType = fromType
        self.toType = toType


# == BASE ERROR CLASS ==

class NodeError(Exception):

    """
    Exception thrown on detecting a (semantic) error on an AST node.

    This class is only meant as an ABC. Only specific subclasses
    should be instantiated.
    """

    _node_error_msg = "Bad node"
    _prev_error_msg = ""
    _err_level = "error: "
    _prev_prefix = "\n-> "

    def __init__(self, node, prev=None):
        """Create a new exception carrying the offending node(s)."""
        self.node = node
        self.prev = prev

    def __str__(self):
        """Format and return the exception's message."""
        node_msg = "".join((
            self.node.pos_to_str(),
            self._err_level,
            self._node_error_msg
        ))

        if self.prev is not None:
            prev_msg = "".join((
                self._prev_prefix,
                self.prev.pos_to_str(),
                self._prev_error_msg
            ))
        else:
            prev_msg = ""

        return "%s%s" % (node_msg, prev_msg)
