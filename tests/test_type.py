import unittest

from compiler import ast, error, type
from tests import parser_db


class TestTypeAPI(unittest.TestCase, parser_db.ParserDB):
    """Test the API of the type module."""

    def test_bad_type_error(self):
        try:
            raise type.LlamaBadTypeError()
            self.fail()
        except type.LlamaBadTypeError:
            pass

    def test_array_of_array_error(self):
        try:
            node = ast.Array(ast.Array(ast.Int()))
            node.lineno, node.lexpos = 1, 2
            raise type.LlamaArrayofArrayError(node)
            self.fail()
        except type.LlamaArrayofArrayError as e:
            e.should.be.a(type.LlamaInvalidTypeError)
            e.should.have.property("node").being(node)

    def test_array_return_error(self):
        try:
            node = ast.Function(ast.Int(), ast.Array(ast.Int()))
            node.lineno, node.lexpos = 1, 2
            raise type.LlamaArrayReturnError(node)
            self.fail()
        except type.LlamaArrayReturnError as e:
            e.should.be.a(type.LlamaInvalidTypeError)
            e.should.have.property("node").being(node)

    def test_ref_of_array_error(self):
        try:
            node = ast.Ref(ast.Array(ast.Int()))
            node.lineno, node.lexpos = 1, 2
            raise type.LlamaRefofArrayError(node)
            self.fail()
        except type.LlamaRefofArrayError as e:
            e.should.be.a(type.LlamaInvalidTypeError)
            e.should.have.property("node").being(node)

    @staticmethod
    def test_table_init():
        t1 = type.Table()

        logger = error.LoggerMock()
        t2 = type.Table(logger=logger)
        t2.should.have.property("logger").being(logger)

    @staticmethod
    def test_validator_init():
        t1 = type.Validator()


class TestTable(unittest.TestCase, parser_db.ParserDB):
    """Test the Table's processing of type definitions."""

    @classmethod
    def _process_typedef(cls, typedefListList):
        mock = error.LoggerMock()
        typeTable = type.Table(logger=mock)
        for typedefList in typedefListList:
            typeTable.process(typedefList)
        return typeTable.logger.success

    def test_type_process(self):
        proc = self._process_typedef
        error = type.LlamaBadTypeError

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
            """
            -- No constructor reuse
            type dup = ConDup | ConDup
            """,
            """
            -- No reference to undefined type
            type what = What of undeftype
            """,
            """
            -- No type redefinition
            type same = Foo1
            type same = Foo2
            """,
            """
            -- No constructor sharing
            type one = Con
            type two = Con
            """,
            """
            -- No redefinition of builtin types
            type bool = BoolCon
            type char = CharCon
            type float = FloatCon
            type int = IntCon
            type unit = UnitCon
            """
        )

        for case in wrong_testcases:
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
        error = type.LlamaInvalidTypeError

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
                ),
                type.LlamaArrayofArrayError
            ),
            (
                (
                    "(array of int) ref",
                    "array of ((array of int) ref)"
                ),
                type.LlamaRefofArrayError
            ),
            (
                (
                    "(int -> array of int) ref",
                    "int -> array of int",
                    "int -> (int -> array of int)"
                ),
                type.LlamaArrayReturnError
            ),
        )

        for cases, error in wrong_testcases:
            for case in cases:
                tree = self._parse(case, "type")
                proc.when.called_with(tree).should.throw(error)
