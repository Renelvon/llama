import unittest

from compiler import ast, type
from tests import parser_db


class TestTypeAPI(unittest.TestCase, parser_db.ParserDB):
    """Test the API of the type module."""

    def test_array_of_array_error(self):
        try:
            node = ast.Array(ast.Array(ast.Int()))
            node.lineno, node.lexpos = 1, 2
            raise type.ArrayOfArrayError(node)
            self.fail()
        except type.ArrayOfArrayError as e:
            e.should.be.a(type.InvalidTypeError)
            e.should.have.property("node").being(node)

    def test_array_return_error(self):
        try:
            node = ast.Function(ast.Int(), ast.Array(ast.Int()))
            node.lineno, node.lexpos = 1, 2
            raise type.ArrayReturnError(node)
            self.fail()
        except type.ArrayReturnError as e:
            e.should.be.a(type.InvalidTypeError)
            e.should.have.property("node").being(node)

    def test_ref_of_array_error(self):
        try:
            node = ast.Ref(ast.Array(ast.Int()))
            node.lineno, node.lexpos = 1, 2
            raise type.RefofArrayError(node)
            self.fail()
        except type.RefofArrayError as e:
            e.should.be.a(type.InvalidTypeError)
            e.should.have.property("node").being(node)

    @staticmethod
    def test_validator_init():
        t1 = type.Validator()

    def test_redef_builtin_type_error(self):
        try:
            node = ast.Int()
            node.lineno, node.lexpos = 1, 2
            raise type.RedefBuiltinTypeError(node)
            self.fail()
        except type.RedefBuiltinTypeError as e:
            e.should.be.a(type.BadTypeDefError)
            e.should.have.property("node").being(node)

    def test_redef_constructor_error(self):
        try:
            node = ast.Constructor("Red")
            node.lineno, node.lexpos = 1, 2
            prev = ast.Constructor("Red")
            prev.lineno, prev.lexpos = 3, 4
            raise type.RedefConstructorError(node, prev)
            self.fail()
        except type.RedefConstructorError as e:
            e.should.be.a(type.BadTypeDefError)
            e.should.have.property("node").being(node)
            e.should.have.property("prev").being(prev)

    def test_redef_user_type_error(self):
        try:
            node = ast.User("foo")
            node.lineno, node.lexpos = 1, 2
            prev = ast.User("foo")
            prev.lineno, prev.lexpos = 3, 4
            raise type.RedefUserTypeError(node, prev)
            self.fail()
        except type.RedefUserTypeError as e:
            e.should.be.a(type.BadTypeDefError)
            e.should.have.property("node").being(node)
            e.should.have.property("prev").being(prev)

    def test_undef_type_error(self):
        try:
            node = ast.User("foo")
            node.lineno, node.lexpos = 1, 2
            raise type.UndefTypeError(node)
            self.fail()
        except type.UndefTypeError as e:
            e.should.be.a(type.BadTypeDefError)
            e.should.have.property("node").being(node)

    @staticmethod
    def test_table_init():
        t1 = type.Table()


class TestTable(unittest.TestCase, parser_db.ParserDB):
    """Test the Table's processing of type definitions."""

    @classmethod
    def _process_typedef(cls, typedefListList):
        typeTable = type.Table()
        for typedefList in typedefListList:
            typeTable.process(typedefList)

    def test_type_process(self):
        proc = self._process_typedef
        error = type.BadTypeDefError

        right_testcases = (
            "type color = Red | Green | Blue",
            "type list = Nil | Cons of int list",
            """
            type number = Integer of int | Real of float
                        | Complex of float float
            """,
            """
            type tree = Leaf | Node of int forest
            and  forest = Empty | NonEmpty of tree forest
            """
        )

        for case in right_testcases:
            tree = self._parse(case)
            proc.when.called_with(tree).shouldnt.throw(error)

        wrong_testcases = (
            (
                (
                    "type bool = BoolCon",
                    "type char = CharCon",
                    "type float = FloatCon",
                    "type int = IntCon",
                    "type unit = UnitCon",
                ),
                type.RedefBuiltinTypeError
            ),
            (
                (
                    "type dup = ConDup | ConDup",
                    """
                    type one = Con
                    type two = Con
                    """,
                ),
                type.RedefConstructorError
            ),
            (
                (
                    """
                    type same = Foo1
                    type same = Foo2
                    """,
                ),
                type.RedefUserTypeError
            ),
            (
                (
                    "type what = What of undeftype",
                ),
                type.UndefTypeError
            )
        )

        for cases, error in wrong_testcases:
            for case in cases:
                tree = self._parse(case)
                proc.when.called_with(tree).should.throw(error)


class TestValidator(unittest.TestCase, parser_db.ParserDB):
    """Test the Validator's functionality."""

    @staticmethod
    def _is_array(t):
        return type.Validator.is_array(t)

    def test_isarray(self):
        for typecon in ast.builtin_types_map.values():
            self._is_array(typecon()).should.be.false

        right_testcases = (
            "array of int",
            "array of foo",
            "array [*, *] of int"
        )

        for case in right_testcases:
            tree = self._parse(case, 'type')
            self._is_array(tree).should.be.true

        wrong_testcases = (
            "foo",
            "int ref",
            "int -> int",
        )

        for case in wrong_testcases:
            tree = self._parse(case, 'type')
            self._is_array(tree).should.be.false

    def test_validate(self):
        proc = type.Validator().validate
        error = type.InvalidTypeError

        for typecon in ast.builtin_types_map.values():
            proc.when.called_with(typecon()).shouldnt.throw(error)

        right_testcases = (
            "foo",

            "int ref",
            "foo ref",
            "(int -> int) ref",
            "(int ref) ref",

            "array of int",
            "array of foo",
            "array of (int ref)",
            "array of (foo ref)",
            "array [*, *] of int",

            "int -> int",
            "foo -> int",
            "int -> foo",
            "int ref -> int",
            "int -> (int ref)",
            "(array of int) -> int",
            "int -> (array of int -> int)",
            "(int -> int) -> int"
        )

        for case in right_testcases:
            tree = self._parse(case, 'type')
            proc.when.called_with(tree).shouldnt.throw(error)

        wrong_testcases = (
            (
                (
                    "array of (array of int)",
                    "(array of (array of int)) -> int",
                    "((array of (array of int)) -> int) ref",
                ),
                type.ArrayOfArrayError
            ),
            (
                (
                    "(array of int) ref",
                    "((array of int) ref) -> int",
                    "array of ((array of int) ref)",
                ),
                type.RefofArrayError
            ),
            (
                (
                    "int -> array of int",
                    "int -> (int -> array of int)",
                    "(int -> array of int) ref",
                ),
                type.ArrayReturnError
            ),
        )

        for cases, error in wrong_testcases:
            for case in cases:
                tree = self._parse(case, "type")
                proc.when.called_with(tree).should.throw(error)
