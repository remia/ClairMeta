import ast
import json
import importlib
from inspect import getmembers, getsource, isfunction
import textwrap
from clairmeta.settings import DCP_CHECK_SETTINGS


def extract_error_msg(func):
    errors = []

    ast_func = ast.parse(textwrap.dedent(getsource(func)))
    for node in ast.walk(ast_func.body[0]):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            else:
                func_name = node.func.id

            if func_name in ["error", "fatal_error"]:
                if isinstance(node.args[0], ast.Constant):
                    errors += [node.args[0].value]
                elif isinstance(node.args[0], ast.Call):
                    errors += [node.args[0].func.value.value]

    return errors


all_checks = {}

prefix = DCP_CHECK_SETTINGS["module_prefix"]
for k, v in DCP_CHECK_SETTINGS["modules"].items():
    try:
        module_path = "clairmeta." + prefix + k
        module = importlib.import_module(module_path)
        funcs = getmembers(module.Checker, isfunction)
        funcs = [f for f in funcs if f[0].startswith("check_")]
        checks = [(f[0], f[1].__doc__, extract_error_msg(f[1])) for f in funcs]

        all_checks[module.__name__] = checks
    except Exception as e:
        print(str(e))

with open("result.json", "w") as fp:
    json.dump(all_checks, fp, sort_keys=True, indent=2)
