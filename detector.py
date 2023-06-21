"""Pydise - Detector."""
import argparse
import ast
import os
import logging
from pydise.exceptions import PydiseSideEffects

PATTERN_SIDE_EFFECTS = (ast.Expr, ast.Raise, ast.Assert)
dict_assign = dict()
dict_functions = dict()


class RewriteName(ast.NodeTransformer):
    """Class for Rewrite some nodes in an AST Tree."""

    def visit_Name(self, node):
        """Replace ast.Name to an ast value."""
        return dict_assign.get(node.id, node)


class PyDise(object):
    """Main class."""

    def __init__(self, filename=None, file=None, ast_tree=None, on_error="logger"):
        """Init."""
        if filename:
            self.filename = filename
            self.load_from_filename(filename)
        elif file:
            self.filename = None
            self.load_from_file(file)
        elif ast_tree:
            self.filename = None
            self.load_from_ast(ast_tree)
        else:
            self.filename = None
            self.ast_module = None

        self.on_error = on_error
        self.side_effects = {"warnings": list(), "errors": list()}

    def load_from_filename(self, filename):
        """Load a file from a filename, and set an ast_module."""
        self.filename = filename
        if not os.path.isfile(self.filename):
            print("'{}' isn't a file.")
        with open(self.filename, "rb") as file:
            self.ast_module = ast.parse(file.read(), filename=self.filename)

    def load_from_file(self, file):
        """Load a file, and set an ast_module."""
        self.ast_module = ast.parse(file.read())

    def load_from_ast(self, ast_tree):
        """Load an ast module."""
        self.ast_module = ast_tree

    def save_variables(self, ast_assign):
        """Save variables into a dictionnary."""
        if not isinstance(ast_assign, ast.Assign):
            logging.error("Not an AST Assign.")

        for target in ast_assign.targets:
            if hasattr(target, "id"):
                dict_assign[target.id] = ast_assign.value

    def save_functions(self, ast_function_def):
        """Save functions to a dictionnary."""
        # TODO : Improve this method to retrieve sub function
        if not isinstance(ast_function_def, ast.FunctionDef):
            logging.error("Not an AST FunctionDef.")
        dict_functions[ast_function_def.name] = ast_function_def

    def _notify(self, tree_element, level=logging.ERROR, on_error=None):
        """Notifying assertion."""
        try:
            message = f"{tree_element.value.__dict__.get('func').id} at line '{tree_element.lineno}'"
        except Exception:
            message = f"Notif -> {tree_element}"

        if on_error == "logger":
            logging.log(level, message)
        elif on_error == "raise":
            raise PydiseSideEffects(message)
        else:
            pass

    def notify(self, on_error=None):
        """Use to notify user."""
        if on_error is None:
            on_error = self.on_error
        side_effects_warnings = list(set(self.side_effects.get("warnings", list())))
        side_effects_errors = list(set(self.side_effects.get("errors", list())))

        for side_effect in side_effects_warnings:
            self._notify(side_effect, level=logging.WARNING, on_error=on_error)

        for side_effect in side_effects_errors:
            self._notify(side_effect, level=logging.ERROR, on_error=on_error)

    def analyze(self, ast_module=None):
        """Analyze the AST Module and return a list of AST node that will be executed when imported."""
        if ast_module is None:
            ast_module = self.ast_module
        if not isinstance(ast_module, ast.Module):
            logging.error("Not an AST Module.")
        else:
            tree_elements = ast_module.body
            # print(tree_elements)

            for tree_element in tree_elements:
                tree_element = RewriteName().visit(tree_element)
                self.get_side_effects(tree_element)
        return self.side_effects

    def is_side_effects(self, node):
        """Check if the ast node could generate a side effect."""
        if isinstance(node, PATTERN_SIDE_EFFECTS):
            # When ast.Expr(value=ast.Constant) assuming it's a docstring -> Ignored
            if hasattr(node, "value") and isinstance(node.value, ast.Constant):
                return False
            # print(inspect.getsourcefile())
            return True

    def get_side_effects(self, tree_element, recursive=False):
        """Recursively dig into an ast tree and found side effects."""
        if self.is_side_effects(tree_element):
            self.side_effects["errors"].append(tree_element)

        # Get the first level functions / variables.
        if isinstance(tree_element, ast.FunctionDef):
            self.save_functions(tree_element)

        if recursive:
            # For several type of statement like for/while/try/if/with/raise etc...
            if hasattr(tree_element, "body"):
                for sub_element in tree_element.body:
                    self.get_side_effects(sub_element)

            # For object Assign()
            if hasattr(tree_element, "targets"):
                function_name = tree_element.value.func.id
                if dict_functions.get(function_name):
                    self.get_side_effects(dict_functions.get(function_name))
        else:
            if isinstance(tree_element, ast.Call):
                if hasattr(tree_element, "func") and hasattr(tree_element.func, "id"):
                    dest_call = dict_functions.get(tree_element.func.id)
                    self.get_side_effects(dest_call, recursive=True)

            if isinstance(tree_element, ast.Assign):
                for child in list(ast.iter_child_nodes(tree_element)):
                    # catch dynamic assignment like "a = foo()" and check if this functions could generate a side effects
                    if isinstance(child, ast.Call):
                        self.get_side_effects(child)
                else:
                    self.save_variables(tree_element)

            if isinstance(tree_element, (ast.ClassDef, ast.Try, ast.With)):
                self.get_side_effects(tree_element, recursive=True)

            if isinstance(tree_element, ast.If):
                # Skip test when it's a function / object
                if isinstance(tree_element.test, ast.Call):
                    self.side_effects["warnings"].append(
                        f"Possible side-effect - {tree_element.lineno}"
                    )
                else:
                    unparse_code = ast.unparse(tree_element.test)
                    try:
                        eval_code = eval(unparse_code)
                    except Exception:
                        eval_code = False

                    if "__main__" not in unparse_code:
                        if eval_code:
                            self.get_side_effects(tree_element, recursive=True)
                        else:
                            if tree_element.orelse:
                                for sub_condition in tree_element.orelse:
                                    self.get_side_effects(sub_condition)

        return self.side_effects


def main(filename, on_error="logger"):
    """Script main entry point."""
    pydise_object = PyDise(filename=filename, on_error=on_error)

    pydise_object.analyze()
    pydise_object.notify()

    return pydise_object.side_effects


def run():
    """Run."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--filename", help="file to check")
    args = parser.parse_args()

    main(filename=args.filename)


if __name__ == "__main__":
    run()
