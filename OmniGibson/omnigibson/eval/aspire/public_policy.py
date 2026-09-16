"""Accidental privileged-access guard, NOT a hardened Python security sandbox."""

import ast
import builtins

from omnigibson.eval.aspire.code_policy_executor import AspireCodePolicyExecutor


ALLOWED_IMPORTS = {"numpy", "math", "scipy.spatial.transform"}
FORBIDDEN_NAMES = {
    "execute_reference_skill", "env", "evaluator", "robot", "og", "sim", "open", "eval", "exec",
    "compile", "getattr", "setattr", "globals", "locals", "vars", "__import__", "breakpoint",
}
FORBIDDEN_ATTRIBUTES = {
    "object_scope", "object_registry", "states", "aabb_center", "aabb_extent", "task", "success",
    "visual_marker", "load", "save", "savez", "savez_compressed", "loadtxt", "savetxt", "fromfile",
    "tofile", "memmap", "ctypes", "f2py", "lib", "testing", "distutils", "DataSource",
}


def validate_policy(source: str) -> None:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name not in ALLOWED_IMPORTS for alias in node.names):
                raise ValueError("Policy imports are restricted to numpy, math and scipy.spatial.transform")
        if isinstance(node, ast.ImportFrom):
            if node.level or node.module not in ALLOWED_IMPORTS or any(alias.name == "*" for alias in node.names):
                raise ValueError("Unsupported policy import")
            if any(alias.name.startswith("_") or alias.name in FORBIDDEN_ATTRIBUTES | FORBIDDEN_NAMES for alias in node.names):
                raise ValueError("Forbidden policy import member")
        if isinstance(node, ast.Name) and (node.id in FORBIDDEN_NAMES or (node.id.startswith("_") and node.id != "_")):
            raise ValueError(f"Forbidden policy name: {node.id}")
        if isinstance(node, ast.Attribute) and (node.attr.startswith("_") or node.attr in FORBIDDEN_ATTRIBUTES):
            raise ValueError(f"Forbidden policy attribute: {node.attr}")


def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    if level or name not in ALLOWED_IMPORTS:
        raise ImportError(f"Unsupported policy import: {name}")
    return builtins.__import__(name, globals, locals, fromlist, level)


class PublicPolicyExecutor(AspireCodePolicyExecutor):
    def reset(self, inputs=None):
        super().reset(inputs)
        names = ("print", "len", "range", "enumerate", "zip", "min", "max", "abs", "sum", "all", "any",
                 "sorted", "round", "float", "int", "bool", "str", "list", "tuple", "dict", "set",
                 "isinstance", "Exception", "RuntimeError", "ValueError", "AssertionError")
        self._globals["__builtins__"] = {name: getattr(builtins, name) for name in names if hasattr(builtins, name)}
        self._globals["__builtins__"]["__import__"] = safe_import

    def run_source(self, source, *, observation=None):
        validate_policy(source)
        return super().run_source(source, observation=observation)
