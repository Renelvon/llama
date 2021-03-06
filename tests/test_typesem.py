import unittest

from compiler import ast, parse, typesem

# pylint: disable=no-member


class TestTypeAPI(unittest.TestCase):
    """Test the API of the type module."""

    def test_is_array(self):
        self.assertTrue(typesem.is_array(ast.Array(ast.Int())))

    def test_array_of_array_error(self):
        exc = typesem.ArrayOfArrayError
        self.assertTrue(issubclass(exc, typesem.InvalidTypeError))

    def test_array_return_error(self):
        exc = typesem.ArrayReturnError
        self.assertTrue(issubclass(exc, typesem.InvalidTypeError))

    def test_ref_of_array_error(self):
        exc = typesem.RefOfArrayError
        self.assertTrue(issubclass(exc, typesem.InvalidTypeError))

    def test_redef_builtin_type_error(self):
        exc = typesem.RedefBuiltinTypeError
        self.assertTrue(issubclass(exc, typesem.InvalidTypeError))

    def test_redef_constructor_error(self):
        exc = typesem.RedefConstructorError
        self.assertTrue(issubclass(exc, typesem.InvalidTypeError))

    def test_redef_user_type_error(self):
        exc = typesem.RedefUserTypeError
        self.assertTrue(issubclass(exc, typesem.InvalidTypeError))

    def test_undef_type_error(self):
        exc = typesem.UndefTypeError
        self.assertTrue(issubclass(exc, typesem.InvalidTypeError))

    def test_undef_constructor_error(self):
        exc = typesem.UndefConstructorError
        self.assertTrue(issubclass(exc, typesem.InvalidTypeError))

    def test_table_init(self):
        typesem.Table()

    def test_table_process(self):
        tree = parse.quiet_parse("type foo = Foo of int", "typedef")
        typesem.Table().process(tree)

    def test_table_validate(self):
        typesem.Table().validate(ast.Int())


class TestAux(unittest.TestCase):
    """Test auxiliary functions."""

    def test_is_array(self):
        for typecon in ast.builtin_types_map.values():
            self.assertFalse(typesem.is_array(typecon()))

        right_testcases = (
            "array of int",
            "array of foo",
            "array [*, *] of int"
        )

        for case in right_testcases:
            tree = parse.quiet_parse(case, "type")
            self.assertTrue(typesem.is_array(tree))

        wrong_testcases = (
            "foo",
            "int ref",
            "int -> int",
        )

        for case in wrong_testcases:
            tree = parse.quiet_parse(case, "type")
            self.assertFalse(typesem.is_array(tree))


class TestTable(unittest.TestCase):
    """Test the Table's functionality."""

    def _assert_node_lineinfo(self, node):
        node.should.have.property("lineno")
        node.lineno.shouldnt.be(None)
        node.should.have.property("lexpos")
        node.lexpos.shouldnt.be(None)

    def test_process(self):
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

        table = typesem.Table()
        proc = table.process
        for case in right_testcases:
            tree = parse.quiet_parse(case, "typedef")
            proc.when.called_with(tree).shouldnt.throw(
                typesem.InvalidTypeError
            )

        wrong_testcases = (
            (
                (
                    "type bool = BoolCon",
                    "type char = CharCon",
                    "type float = FloatCon",
                    "type int = IntCon",
                    "type unit = UnitCon",
                ),
                typesem.RedefBuiltinTypeError,
                1
            ),
            (
                (
                    "type dup = ConDup | ConDup",
                    """
                    type one = Con
                    type two = Con
                    """,
                ),
                typesem.RedefConstructorError,
                2
            ),
            (
                (
                    """
                    type same = Foo1
                    type same = Foo2
                    """,
                ),
                typesem.RedefUserTypeError,
                2
            ),
            (
                (
                    "type what = What of undeftype",
                ),
                typesem.UndefTypeError,
                1
            ),
            (
                (
                    "type invalid = Foo of (array of int) ref",
                ),
                typesem.RefOfArrayError,
                1
            )
        )

        for cases, error, exc_node_count in wrong_testcases:
            for case in cases:
                table = typesem.Table()
                tree = parse.quiet_parse(case)
                with self.assertRaises(error) as context:
                    for typeDefList in tree:
                        table.process(typeDefList)

                exc = context.exception
                exc.should.have.property("node")
                self._assert_node_lineinfo(exc.node)
                if exc_node_count == 2:
                    exc.should.have.property("prev")
                    exc.prev.shouldnt.be(exc.node)
                    self._assert_node_lineinfo(exc.prev)

    def test_validate(self):
        """Test the validating of types."""
        table = typesem.Table()
        foo_tree = parse.quiet_parse("type foo = Foo")
        for typeDefList in foo_tree:
            table.process(typeDefList)

        proc = table.validate
        error = typesem.InvalidTypeError

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
            tree = parse.quiet_parse(case, "type")
            proc.when.called_with(tree).shouldnt.throw(error)

        wrong_testcases = (
            (
                (
                    "array of (array of int)",
                    "(array of (array of int)) -> int",
                    "((array of (array of int)) -> int) ref",
                ),
                typesem.ArrayOfArrayError
            ),
            (
                (
                    "(array of int) ref",
                    "((array of int) ref) -> int",
                    "array of ((array of int) ref)",
                ),
                typesem.RefOfArrayError
            ),
            (
                (
                    "int -> array of int",
                    "int -> (int -> array of int)",
                    "(int -> array of int) ref",
                ),
                typesem.ArrayReturnError
            ),
            (
                (
                    "undeftype",
                ),
                typesem.UndefTypeError
            )
        )

        for cases, error in wrong_testcases:
            for case in cases:
                tree = parse.quiet_parse(case, "type")
                with self.assertRaises(error) as context:
                    proc(tree)
                exc = context.exception
                exc.should.have.property("node")

                self._assert_node_lineinfo(exc.node)
