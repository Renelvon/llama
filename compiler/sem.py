"""
# ----------------------------------------------------------------------
# sem.py
#
# The Llama Semantic Analyzer
# http://courses.softlab.ntua.gr/compilers/2012a/llama2012.pdf
#
# Author: Nick Korasidis <renelvon@gmail.com>
# ----------------------------------------------------------------------
"""

from compiler import ast, error, infer, symbol, typesem


class Analyzer:
    """A semantic analyzer for Llama programs."""

    def __init__(self, logger=None):
        """Initialize a new Analyzer."""
        if logger is None:
            self.logger = error.Logger()
        else:
            self.logger = logger

        self._initialize_dispatchers()

        self.symbol_table = symbol.Table()
        self.type_table = typesem.Table()
        self.inferer = infer.Inferer(logger)

        self._dispatcher = None
        self._binop_dispatcher = None
        self._unop_dispatcher = None

    def _initialize_dispatchers(self):
        self._initialize_general_dispatcher()
        self._initialize_unop_dispatcher()
        self._initialize_binop_dispatcher()

    def _initialize_general_dispatcher(self):
        self._dispatcher = {
            ast.Program: self.analyze,
            ast.LetDef: self.analyze_letdef,
            ast.TypeDef: self.analyze_typedef,
            ast.ConstantDef: self.analyze_constant_def,
            ast.FunctionDef: self.analyze_function_def,
            ast.VariableDef: self.analyze_variable_def,
            ast.ArrayVariableDef: self.analyze_array_variable_def,
            ast.Param: self.analyze_param,
            ast.UnaryExpression: self.analyze_unary_expression,
            ast.BinaryExpression: self.analyze_binary_expression,
            ast.ConstructorCallExpression:
                self.analyze_constructor_call_expression,
            ast.ArrayExpression: self.analyze_array_expression,
            ast.ConstExpression: self.analyze_const_expression,
            ast.ConidExpression: self.analyze_conid_expression,
            ast.GenidExpression: self.analyze_genid_expression,
            ast.DeleteExpression: self.analyze_delete_expression,
            ast.DimExpression: self.analyze_dim_expression,
            ast.ForExpression: self.analyze_for_expression,
            ast.FunctionCallExpression:
                self.analyze_function_call_expression,
            ast.LetInExpression: self.analyze_let_in_expression,
            ast.IfExpression: self.analyze_if_expression,
            ast.MatchExpression: self.analyze_match_expression,
            ast.NewExpression: self.analyze_new_expression,
            ast.WhileExpression: self.analyze_while_expression,
            ast.Clause: self.analyze_clause,
            ast.Pattern: self.analyze_pattern,
            ast.GenidPattern: self.analyze_genid_pattern,

            # NOTE: Some ast nodes are omitted, as they are
            # processed elsewhere. These include type annotations as
            # well as type definitions.
        }

    def _initialize_unop_dispatcher(self):
        self._unop_dispatcher = {
            "!": self.analyze_bang_expression,

            "not": self.analyze_not_expression,

            "+": self.analyze_int_sign_expression,
            "-": self.analyze_int_sign_expression,

            "+.": self.analyze_float_sign_expression,
            "-.": self.analyze_float_sign_expression
        }

    def _initialize_binop_dispatcher(self):
        self._binop_dispatcher = {
            "+": self.analyze_int_binop_expression,
            "-": self.analyze_int_binop_expression,
            "*": self.analyze_int_binop_expression,
            "/": self.analyze_int_binop_expression,
            "mod": self.analyze_int_binop_expression,

            "+.": self.analyze_float_binop_expression,
            "-.": self.analyze_float_binop_expression,
            "*.": self.analyze_float_binop_expression,
            "/.": self.analyze_float_binop_expression,
            "**": self.analyze_float_binop_expression,

            "=": self.analyze_eq_binop_expression,
            "<>": self.analyze_eq_binop_expression,

            "==": self.analyze_nateq_binop_expression,
            "!=": self.analyze_nateq_binop_expression,

            "<": self.analyze_cmp_binop_expression,
            "<=": self.analyze_cmp_binop_expression,
            ">": self.analyze_cmp_binop_expression,
            ">=": self.analyze_cmp_binop_expression,

            "||": self.analyze_bool_binop_expression,
            "&&": self.analyze_bool_binop_expression,

            ";": self.analyze_semicolon_expression,
            ":=": self.analyze_assign_expression
        }

    def _dispatch(self, node):
        self._dispatcher[type(node)](node)

    def analyze(self, code_ast):
        self.analyze_program(code_ast)

    def analyze_program(self, program):
        for definition in program:
            self._dispatch(definition)

    def analyze_letdef(self, letdef):
        if letdef.isRec:
            self._analyze_rec_letdef(letdef)
        else:
            self._analyze_norec_letdef(letdef)

    def _analyze_rec_letdef(letdef):
        self._open_visible_scope()
        self._insert_symbols(letdef)
        for definition in letdef:
            self._dispatch(definition)

    def _analyze_norec_letdef(letdef):
        new_scope = self._open_invisible_scope()
        for definition in letdef:
            self._dispatch(definition)
        new_scope.visible = True
        self._insert_symbols(letdef)

    def _open_visible_scope(self):
        new_scope = self.symbol_table.open_scope()
        assert new_scope.visible, "New scope is invisible."
        return new_scope

    def _open_invisible_scope(self):
        new_scope = self.symbol_table.open_scope()
        new_scope.visible = False
        return new_scope

    def _close_scope(self):
        self.symbol_table.close_scope()

    def _insert_symbols(self, symbols):
        for sym in symbols:
            self._insert_symbol(sym)

    def _insert_symbol(self, sym):
        try:
            self.symbol_table.insert_symbol(sym)
        except symbol.SymbolError as e:
            self.logger.error(str(e))

    def analyze_typedef(self, typedef):
        try:
            self.type_table.process(typedef)
        except typesem.InvalidTypeError as e:
            self.logger.error(str(e))

    def analyze_constant_def(self, definition):
        self.inferer.constrain_nodes_equtyped(definition, definition.body)
        self._dispatch(definition.body)

    def analyze_function_def(self, definition):
        fun_type = self.inferer.get_type_handle(definition.body)
        for param in reversed(definition.arguments):
            fun_type = ast.Function(
                self.inferer.get_type_handle(param),
                fun_type
            )

        self.inferer.constrain_node_having_type(definition, fun_type)
        self.inferer.constrain_node_not_being_function(definition.body)

        self._open_visible_scope()
        self._insert_symbols(definition.arguments)
        for param in definition.arguments:
            self._dispatch(param)
        self._dispatch(definition.body)
        self._close_scope()

    def analyze_variable_def(self, definition):
        if definition.type is None:
            definition.type = ast.Ref(self.inferer.make_new_type())
        else:
            assert isinstance(definition.type, ast.Ref), 'Non-Ref variable'
        self.inferer.constrain_node_having_type(definition, definition.type)

    def analyze_array_variable_def(self, definition):
        if definition.type is None:
            definition.type = ast.Array(
                self.inferer.make_new_type(),
                definition.dimensions
            )
        else:
            assert isinstance(definition.type, ast.Array), 'Non-Array array'
        self.inferer.constrain_node_having_type(definition, definition.type)

    def analyze_param(self, param):
        # No additional type processing is needed than what takes place
        # while analyzing the function definition.
        return

    def analyze_unary_expression(self, expression):
        self._unop_dispatcher[expression.operator](expression)
        self._dispatch(expression.operand)

    def analyze_bang_expression(self, expression):
        self.inferer.constrain_node_having_type(
            expression.operand,
            ast.Ref(self.inferer.get_type_handle(expression))
        )

    def analyze_not_expression(self, expression):
        self._analyze_unop_expression_type1(expression, ast.Bool)

    def analyze_int_sign_expression(self, expression):
        self._analyze_unop_expression_type1(expression, ast.Int)

    def analyze_float_sign_expression(self, expression):
        self._analyze_unop_expression_type1(expression, ast.Float)

    def _analyze_unop_expression_type1(self, expression, type_factory):
        self.inferer.constrain_node_having_type(expression, type_factory())
        self.inferer.constrain_node_having_type(
            expression.operand,
            type_factory()
        )

    def analyze_binary_expression(self, expression):
        self._binop_dispatcher[expression.operator](expression)
        self._dispatch(expression.left_operand)
        self._dispatch(expression.right_operand)

    def analyze_int_binop_expression(self, expression):
        self._analyze_binop_expression_type1(expression, ast.Int)

    def analyze_float_binop_expression(self, expression):
        self._analyze_binop_expression_type1(expression, ast.Float)

    def analyze_bool_binop_expression(self, expression):
        self._analyze_binop_expression_type1(expression, ast.Bool)

    def analyze_eq_binop_expression(self, expression):
        self._analyze_binop_expression_type2(expression, ast.Bool)

    def analyze_nateq_binop_expression(self, expression):
        self._analyze_binop_expression_type2(expression, ast.Bool)

    def analyze_cmp_binop_expression(self, expression):
        self._analyze_binop_expression_type2(expression, ast.Bool)
        self.inferer.constrain_node_having_one_of_types(
            (ast.Char(), ast.Int(), ast.Float())
        )

    def _analyze_binop_expression_type1(self, expression, type_factory):
        self.inferer.constrain_node_having_type(expression, type_factory())
        for operand in (expression.left_operand, expression.right_operand):
            self.inferer.constrain_node_having_type(operand, type_factory())

    def _analyze_binop_expression_type2(self, expression, root_type_factory):
        self.inferer.constrain_node_having_type(expression, root_type_factory())
        self.inferer.constrain_nodes_equtyped(
            expression.left_operand,
            expression.right_operand
        )
        self.inferer.constrain_node_not_being_function(expression.left_operand)
        self.inferer.constrain_node_not_being_array(expression.left_operand)

    def analyze_semicolon_expression(self, expression):
        self.inferer.constrain_nodes_equtyped(
            expression,
            expression.right_operand
        )

    def analyze_assign_expression(self, expression):
        self.inferer.constrain_node_having_type(expression, ast.Unit())
        self.inferer.constrain_node_having_type(
            expression.left_operand,
            ast.Ref(self.inferer.get_type_handle(expression.right_operand))
        )

    def analyze_constructor_call_expression(self, expression):
        pass

    def analyze_array_expression(self, expression):
        pass

    def analyze_const_expression(self, expression):
        # Intentionally empty: the parser has already filled-in types.
        return

    def analyze_conid_expression(self, expression):
        pass

    def analyze_genid_expression(self, expression):
        pass

    def analyze_delete_expression(self, expression):
        self.inferer.constrain_node_having_type(
            expression.expr,
            ast.Ref(self.inferer.make_new_type())
        )
        self.inferer.constrain_node_having_type(expression, ast.Unit())

        self._dispatch(expression.expr)

    def analyze_dim_expression(self, expression):
        pass

    def analyze_for_expression(self, expression):
        pass

    def analyze_function_call_expression(self, expression):
        pass

    def analyze_let_in_expression(self, expression):
        pass

    def analyze_if_expression(self, expression):
        pass

    def analyze_match_expression(self, expression):
        pass

    def analyze_new_expression(self, expression):
        pass

    def analyze_while_expression(self, expression):
        pass

    def analyze_clause(self, clause):
        pass

    def analyze_pattern(self, pattern):
        pass

    def analyze_genid_pattern(self, pattern):
        pass


def analyze(program, logger=None):
    """
    Analyze the given AST. Resolve names, infer and verify types
    and check for semantic errors. Return the annotated AST.
    For customised error reporting, provide a 'logger'.
    """
    analyzer = Analyzer(logger=logger)
    return analyzer.analyze(program)


def quiet_analyze(program):
    """
    Analyze the given AST. Resolve names, infer and verify types
    and check for semantic errors. Return the annotated AST.
    Explicitly silence errors/warnings.
    """
    return analyze(program, logger=error.LoggerMock())
