"""Pydise - Detector."""
import argparse
import ast
import copy
import os
import logging
import linecache
from glob import glob

# TODO : An ast.Expr may not generate a side effect, but it's hard to distinguish, so
#        by default an ast.Expr will be defined as a possible side-effect generator.
PATTERNS_SIDE_EFFECTS = (ast.Expr, ast.Raise, ast.Assert, ast.Delete)
PATTERNS_IGNORED = ["# no-pydise", "# no_pydise"]
dict_assign = dict()
dict_functions = dict()


class PydiseSideEffects(Exception):
    """Pydise Exception."""

    def __init__(self, message=""):
        """Init exception message."""
        self.message = message
        super().__init__(self.message)


class RewriteName(ast.NodeTransformer):
    """Class for Rewrite some nodes in an AST Tree."""

    def visit_Name(self, node):
        """Replace ast.Name to an ast value."""
        return dict_assign.get(node.id, node)


class PyDiseLoader(object):
    """Class used to define strategy to load a data and return an ast_module."""

    def __init__(
        self,
        filename=None,
        file=None,
        ast_tree=None,
    ):
        """Init data to load, based on filename / file or an ast_tree."""
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


class PyDise(object):
    """Main class."""

    def __init__(
        self,
        filename=None,
        file=None,
        ast_tree=None,
        patterns_ignored=None,
        on_error="logger",
    ):
        """Init."""
        pydise_loader_obj = PyDiseLoader(
            filename=filename, file=file, ast_tree=ast_tree
        )
        self.filename = pydise_loader_obj.filename
        self.ast_module = pydise_loader_obj.ast_module
        self.on_error = on_error
        self.patterns_ignored = copy.copy(PATTERNS_IGNORED)
        if isinstance(patterns_ignored, list):
            self.patterns_ignored.extend(patterns_ignored)

        self.side_effects = {"warnings": list(), "errors": list()}

    def save_variables(self, ast_assign):
        """Save variables into a dictionnary."""
        if not isinstance(ast_assign, ast.Assign):
            logging.error("Not an AST Assign.")

        for target in ast_assign.targets:
            if hasattr(target, "id"):
                dict_assign[target.id] = ast_assign.value

    def save_functions(self, ast_def):
        """Save functions / class to a dictionnary."""
        # TODO : Improve this method to retrieve sub function
        if not isinstance(ast_def, (ast.FunctionDef, ast.ClassDef)):
            logging.error("Not an AST FunctionDef or ClassDef.")
        dict_functions[ast_def.name] = ast_def

    def _notify(self, tree_element, level=logging.ERROR, on_error=None):
        """Notifying assertion."""
        message = f"{self.filename}:{tree_element.lineno} -> Side effects detected : "
        try:
            message += f"{tree_element.value.__dict__.get('func').id}"
        except Exception:
            try:
                message += f"{list(ast.iter_child_nodes(tree_element))}"
            except Exception:
                message += f"{tree_element}"

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
        """Analyze the AST Module.

        Return a dict with errors of the AST nodes that will be executed during import.
        """
        if ast_module is None:
            ast_module = self.ast_module
        if not isinstance(ast_module, ast.Module):
            logging.error("Not an AST Module.")
        else:
            tree_elements = ast_module.body

            for tree_element in tree_elements:
                tree_element = RewriteName().visit(tree_element)
                self.get_side_effects(tree_element)
        return self.side_effects

    def is_side_effects(self, node):
        """Check if the ast node could generate a side effect."""
        if isinstance(node, PATTERNS_SIDE_EFFECTS):
            # When ast.Expr(value=ast.Constant) assuming it's a docstring -> Ignored
            if hasattr(node, "value") and isinstance(node.value, ast.Constant):
                return False

            # Exclusion based on a line pattern
            raw_line = linecache.getline(
                self.filename, node.lineno, module_globals=None
            )
            for pattern_ignored in self.patterns_ignored:
                if pattern_ignored in raw_line:
                    return False
            return True

    def get_side_effects(self, tree_element, recursive=False):
        """Recursively dig into an ast tree and found side effects."""
        # TODO : Add "try/finally"
        # TODO : Add "match"

        if self.is_side_effects(tree_element):
            self.side_effects["errors"].append(tree_element)

        # Save the first level functions / class.
        if isinstance(tree_element, (ast.FunctionDef, ast.ClassDef)):
            self.save_functions(tree_element)

        if isinstance(tree_element, ast.FunctionDef):
            self.get_side_effects(tree_element.args)

        if isinstance(tree_element, ast.arguments):
            for default in tree_element.defaults:
                self.get_side_effects(default)

            for kw_default in tree_element.kw_defaults:
                self.get_side_effects(kw_default)

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
                    if isinstance(dest_call, ast.ClassDef):
                        for body_data in dest_call.body:
                            if hasattr(body_data, "name") and body_data.name == "__init__":
                                self.get_side_effects(body_data, recursive=True)
                    else:
                        self.get_side_effects(dest_call, recursive=True)

            if isinstance(tree_element, ast.Assign):
                for child in list(ast.iter_child_nodes(tree_element)):
                    # catch dynamic assignment like "a = foo()" and check if this functions could generate a side effects
                    if isinstance(child, ast.Call):
                        self.get_side_effects(child)
                else:
                    self.save_variables(tree_element)

            # if isinstance(tree_element, (ast.ClassDef, ast.Try, ast.With)):
            if isinstance(tree_element, (ast.Try, ast.With)):
                self.get_side_effects(tree_element, recursive=True)

            if isinstance(tree_element, ast.For):
                loop_var = ast.unparse(tree_element.target)
                loop_iter = ast.unparse(tree_element.iter)

                try:
                    eval_code = eval(f"[True for {loop_var} in {loop_iter}]")
                    eval_code = True if True in eval_code else False
                except Exception:
                    eval_code = False

                if eval_code:
                    self.get_side_effects(tree_element, recursive=True)
                    is_break = (
                        True
                        if True in [isinstance(x, ast.Break) for x in tree_element.body]
                        else False
                    )

                    if not is_break and tree_element.orelse:
                        for sub_condition in tree_element.orelse:
                            self.get_side_effects(sub_condition)
                else:
                    if tree_element.orelse:
                        for sub_condition in tree_element.orelse:
                            self.get_side_effects(sub_condition)

            if isinstance(tree_element, (ast.If, ast.While)):
                # Skip test when it's a function / object
                if isinstance(tree_element.test, ast.Call):
                    # self.side_effects["warnings"].append(f"Possible side-effect - {tree_element.lineno}")
                    self.side_effects["warnings"].append(tree_element.test)
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


def get_filenames(args):
    """Return a list of files based on args or by default, from the current directory."""
    list_files = list()
    if os.path.isdir(args.filename):
        for root, sub_directories, files in os.walk(args.filename):
            for filename in files:
                if str(filename).endswith(".py"):
                    list_files.append(os.path.join(root, filename))
    elif os.path.isfile(args.filename) and str(args.filename).endswith(".py"):
        list_files.append(args.filename)
    else:
        for file in glob(os.path.join(os.path.curdir, f"{args.filename}*.py")):
            list_files.append(file)
    return list_files


def main(filename, on_error="logger", pattern_ignored=None):
    """Script main entry point."""
    pydise_object = PyDise(
        filename=filename, on_error=on_error, patterns_ignored=pattern_ignored
    )

    pydise_object.analyze()
    pydise_object.notify()

    return pydise_object.side_effects


def run():
    """Run."""
    parser = argparse.ArgumentParser()
    # parser.add_argument("--filename", help="file to check")
    parser.add_argument(
        "filename", help="file to check (wildcard)", type=str, nargs="?", default="."
    )
    parser.add_argument(
        "--list-only",
        help="list the detected files without checking errors.",
        action="store_true",
    )
    parser.add_argument(
        "--pattern-ignored",
        help="ignore line containing the pattern, multiple patterns can be setted, "
        "the pattern is added to the default patterns.",
        action="append",
    )
    args = parser.parse_args()

    list_files = get_filenames(args)

    if args.list_only:
        print("Detected files : ")
        for file in list_files:
            print(f"* {file}")
        exit(0)

    for path in list_files:
        main(filename=path, pattern_ignored=args.pattern_ignored)


if __name__ == "__main__":
    run()
