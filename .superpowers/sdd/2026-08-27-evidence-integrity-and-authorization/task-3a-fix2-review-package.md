# Review package: 49f6b8141ad3284c3e33d596a5cfd2155ec8709f..4b72588b9e24dfa934a59fc58cb54c330ed7606f

## Commits
4b72588 fix(evidence): resolve dynamic programs lexically

## Files changed
 tests/test_evidence_manifest_generation.py | 136 +++++++-
 tools/generate_evidence_manifests.py       | 504 ++++++++++++++++++++++++++---
 2 files changed, 590 insertions(+), 50 deletions(-)

## Diff
diff --git a/tests/test_evidence_manifest_generation.py b/tests/test_evidence_manifest_generation.py
index 37ffe24..57eda43 100644
--- a/tests/test_evidence_manifest_generation.py
+++ b/tests/test_evidence_manifest_generation.py
@@ -302,32 +302,166 @@ class Other:
             "src/pontius/pkg/__init__.py", "src/pontius/pkg/bar.py",
         }
         absolute = GENERATOR._import_paths(ast.parse("from pontius import foo"), "tests/t.py", tracked)
         relative = GENERATOR._import_paths(ast.parse("from . import bar"), "src/pontius/pkg/owner.py", tracked)
         self.assertEqual(absolute, {"src/pontius/__init__.py", "src/pontius/foo.py"})
         self.assertEqual(relative, {"src/pontius/pkg/__init__.py", "src/pontius/pkg/bar.py"})
 
     def test_dynamic_dash_c_programs_are_exact_and_fail_closed(self) -> None:
         tracked = {"src/pontius/runner.py"}
         direct = ast.parse("subprocess.run([python, '-c', \"from pontius import runner\"])")
-        named = ast.parse("program = f\"from pontius import runner; value={VALUE!r}\"\nsubprocess.run([python, '-c', program])")
+        named = ast.parse("VALUE = 1\nprogram = f\"from pontius import runner; value={VALUE!r}\"\nsubprocess.run([python, '-c', program])")
         self.assertEqual(GENERATOR._dynamic_program_imports(direct, "tests/t.py", tracked), tracked)
         self.assertEqual(GENERATOR._dynamic_program_imports(named, "tests/t.py", tracked), tracked)
         for source in (
             "subprocess.run([python, '-c', make_program()])",
             "program = 'from pontius import ' + name\nsubprocess.run([python, '-c', program])",
             "subprocess.run([python, '-c', 'from pontius import'])",
             "subprocess.run([python, '-c', 'import pontius.missing'])",
         ):
             with self.subTest(source=source), self.assertRaises(GENERATOR.GenerationError):
                 GENERATOR._dynamic_program_imports(ast.parse(source), "tests/t.py", tracked)
 
+    def test_dynamic_dash_c_resolution_is_lexical_and_accepts_named_argv(self) -> None:
+        source = '''
+class Selected:
+    def first(self):
+        program = "import pontius.alpha"
+        argv = [python, "-B", "-c", program]
+        subprocess.run(argv)
+    def second(self):
+        program = "import pontius.beta"
+        argv = (python, "-P", "-c", program)
+        subprocess.run(argv)
+'''
+        tracked = {"src/pontius/alpha.py", "src/pontius/beta.py"}
+        self.assertEqual(
+            GENERATOR._dynamic_program_imports(ast.parse(source), "tests/t.py", tracked),
+            tracked,
+        )
+
+    def test_dynamic_dash_c_resolves_fixed_fstrings_and_concatenation(self) -> None:
+        source = '''
+ALPHA = "alpha"
+PREFIX = "import pontius."
+class Selected:
+    def fstring_program(self):
+        program = f"import pontius.{ALPHA}"
+        subprocess.run([python, "-c", program])
+    def concatenated_program(self):
+        module = "beta"
+        program = PREFIX + module
+        argv = [python, "-c", program]
+        subprocess.run(argv)
+'''
+        tracked = {"src/pontius/alpha.py", "src/pontius/beta.py"}
+        self.assertEqual(
+            GENERATOR._dynamic_program_imports(ast.parse(source), "tests/t.py", tracked),
+            tracked,
+        )
+
+    def test_dynamic_dash_c_allows_fixed_enclosing_path_constants(self) -> None:
+        source = '''
+from pathlib import Path
+ROOT = Path(__file__).parents[1]
+LAUNCHER = ROOT / "run_selected.py"
+class Selected:
+    def probe(self):
+        program = f"import runpy; runpy.run_path({str(LAUNCHER)!r}); import pontius.alpha"
+        subprocess.run([python, "-c", program])
+'''
+        self.assertEqual(
+            GENERATOR._dynamic_program_imports(
+                ast.parse(source), "tests/t.py", {"src/pontius/alpha.py"}
+            ),
+            {"src/pontius/alpha.py"},
+        )
+
+    def test_dynamic_dash_c_allows_repeated_symbolic_context_targets(self) -> None:
+        source = '''
+from pathlib import Path
+import tempfile
+class Selected:
+    def probe(self):
+        with tempfile.TemporaryDirectory() as directory:
+            Path(directory)
+        with tempfile.TemporaryDirectory() as directory:
+            root = Path(directory)
+            program = f"value={str(root)!r}; import pontius.alpha"
+            subprocess.run([python, "-c", program])
+'''
+        self.assertEqual(
+            GENERATOR._dynamic_program_imports(
+                ast.parse(source), "tests/t.py", {"src/pontius/alpha.py"}
+            ),
+            {"src/pontius/alpha.py"},
+        )
+
+    def test_dynamic_dash_c_rejects_ambiguous_dynamic_reassigned_and_branch_values(self) -> None:
+        cases = (
+            '''
+class Selected:
+    def dynamic(self, module):
+        program = f"import pontius.{module}"
+        subprocess.run([python, "-c", program])
+''',
+            '''
+class Selected:
+    def reassigned_program(self):
+        program = "import pontius.alpha"
+        program = "import pontius.beta"
+        subprocess.run([python, "-c", program])
+''',
+            '''
+class Selected:
+    def reassigned_import_target(self):
+        module = "alpha"
+        module = "beta"
+        program = f"import pontius.{module}"
+        subprocess.run([python, "-c", program])
+''',
+            '''
+class Selected:
+    def branch_dependent(self, flag):
+        if flag:
+            program = "import pontius.alpha"
+        else:
+            program = "import pontius.beta"
+        subprocess.run([python, "-c", program])
+''',
+            '''
+class Selected:
+    def reassigned_argv(self):
+        program = "import pontius.alpha"
+        argv = [python, "-c", program]
+        argv = [python, "-c", "import pontius.beta"]
+        subprocess.run(argv)
+''',
+            '''
+class Selected:
+    def unresolved_named_argv(self):
+        program = "import pontius.alpha"
+        argv = make_argv("-c", program)
+        subprocess.run(argv)
+''',
+            '''
+class Selected:
+    def assigned_after_use(self):
+        subprocess.run(argv)
+        argv = [python, "-c", "import pontius.alpha"]
+''',
+        )
+        tracked = {"src/pontius/alpha.py", "src/pontius/beta.py"}
+        for source in cases:
+            with self.subTest(source=source), self.assertRaises(GENERATOR.GenerationError):
+                GENERATOR._dynamic_program_imports(ast.parse(source), "tests/t.py", tracked)
+
     def test_historical_identity_collisions_fail_closed(self) -> None:
         rows: list[dict[str, object]] = []
         identities: set[tuple[str, str]] = set()
         GENERATOR._append_unique_row(rows, identities, SAMPLE_ROW)
         with self.assertRaises(GENERATOR.GenerationError):
             GENERATOR._append_unique_row(rows, identities, dict(SAMPLE_ROW))
 
     def test_absent_check_and_invalid_write_approval_do_not_derive(self) -> None:
         with mock.patch.object(GENERATOR, "derive_manifest_state", side_effect=AssertionError("walked")):
             self.assertEqual(GENERATOR.main([]), 2)
diff --git a/tools/generate_evidence_manifests.py b/tools/generate_evidence_manifests.py
index 7b2cb96..dbb5ba0 100644
--- a/tools/generate_evidence_manifests.py
+++ b/tools/generate_evidence_manifests.py
@@ -649,73 +649,479 @@ def _literal_paths(tree: ast.AST, text: str, tracked: set[str]) -> set[str]:
                     if position >= 0:
                         candidates.add(normalized[position:])
         if isinstance(node, ast.Constant) and type(node.value) is str:
             value = node.value.replace("\\", "/")
             if value in tracked:
                 candidates.add(value)
     allowed = ("experiments/configs/", "docs/decisions/")
     return {_relative_path(path) for path in candidates if path in tracked and path.startswith(allowed)}
 
 
-def _dynamic_program_imports(tree: ast.AST, current_path: str, tracked: set[str]) -> set[str]:
-    bindings: dict[str, ast.AST] = {}
-    for node in ast.walk(tree):
-        if isinstance(node, (ast.Assign, ast.AnnAssign)):
-            value = node.value
-            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
-            for target in targets:
-                if isinstance(target, ast.Name):
-                    bindings[target.id] = value
-
-    def program_text(node: ast.AST) -> str:
-        if isinstance(node, ast.Name) and node.id in bindings:
-            return program_text(bindings[node.id])
-        if isinstance(node, ast.Constant) and type(node.value) is str:
-            return node.value
-        if isinstance(node, ast.JoinedStr):
-            parts: list[str] = []
-            for value in node.values:
-                if isinstance(value, ast.Constant) and type(value.value) is str:
-                    parts.append(value.value)
-                elif isinstance(value, ast.FormattedValue):
-                    parts.append(repr("__pontius_dynamic_value__"))
-                else:
-                    raise GenerationError(f"dynamic -c program is not fixed: {current_path}")
-            return "".join(parts)
-        raise GenerationError(f"dynamic -c program is not a fixed literal: {current_path}")
+class _StaticValue:
+    __slots__ = ("kind", "value")
 
-    result: set[str] = set()
-    programs: list[ast.AST] = []
-    for call in (node for node in ast.walk(tree) if isinstance(node, ast.Call)):
-        for argument in call.args:
-            if not isinstance(argument, (ast.List, ast.Tuple)):
+    def __init__(self, kind: str, value: object = None) -> None:
+        self.kind = kind
+        self.value = value
+
+
+_UNRESOLVED_STATIC = _StaticValue("unresolved")
+_SYMBOLIC_STATIC = _StaticValue("symbolic")
+
+
+def _target_names(target: ast.AST) -> set[str]:
+    return {
+        node.id for node in ast.walk(target)
+        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
+    }
+
+
+class _AssignmentInventory(ast.NodeVisitor):
+    def __init__(self) -> None:
+        self.counts: dict[str, int] = {}
+        self.definitions: dict[str, list[ast.AST]] = {}
+
+    def _record(self, target: ast.AST, value: ast.AST) -> None:
+        for name in _target_names(target):
+            self.counts[name] = self.counts.get(name, 0) + 1
+            self.definitions.setdefault(name, []).append(value)
+
+    def visit_Assign(self, node: ast.Assign) -> None:
+        for target in node.targets:
+            self._record(target, node.value)
+        self.visit(node.value)
+
+    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
+        self._record(node.target, node.value or ast.Constant(value=None))
+        if node.value is not None:
+            self.visit(node.value)
+
+    def visit_AugAssign(self, node: ast.AugAssign) -> None:
+        self._record(node.target, node.value)
+        self.visit(node.value)
+
+    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
+        self._record(node.target, node.value)
+        self.visit(node.value)
+
+    def visit_For(self, node: ast.For) -> None:
+        self._record(node.target, node.iter)
+        self.generic_visit(node)
+
+    visit_AsyncFor = visit_For
+
+    def visit_With(self, node: ast.With) -> None:
+        for item in node.items:
+            if item.optional_vars is not None:
+                self._record(item.optional_vars, item.context_expr)
+        self.generic_visit(node)
+
+    visit_AsyncWith = visit_With
+
+    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
+        if node.name is not None:
+            target = ast.Name(id=node.name, ctx=ast.Store())
+            self._record(target, node.type or ast.Constant(value=None))
+        self.generic_visit(node)
+
+    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
+        return None
+
+    visit_AsyncFunctionDef = visit_FunctionDef
+
+    def visit_ClassDef(self, node: ast.ClassDef) -> None:
+        return None
+
+    def visit_Lambda(self, node: ast.Lambda) -> None:
+        return None
+
+
+def _assignment_inventory(statements: Sequence[ast.stmt]) -> _AssignmentInventory:
+    inventory = _AssignmentInventory()
+    for statement in statements:
+        inventory.visit(statement)
+    return inventory
+
+
+def _static_expression(node: ast.AST, environment: Mapping[str, _StaticValue]) -> _StaticValue:
+    if isinstance(node, ast.Constant):
+        return _StaticValue("exact", node.value)
+    if isinstance(node, ast.Name):
+        if node.id == "__file__":
+            return _SYMBOLIC_STATIC
+        return environment.get(node.id, _UNRESOLVED_STATIC)
+    if isinstance(node, (ast.List, ast.Tuple)):
+        return _StaticValue("sequence", tuple(_static_expression(item, environment) for item in node.elts))
+    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
+        left = _static_expression(node.left, environment)
+        right = _static_expression(node.right, environment)
+        if "unresolved" in (left.kind, right.kind):
+            return _UNRESOLVED_STATIC
+        if left.kind == right.kind == "exact":
+            try:
+                return _StaticValue("exact", left.value + right.value)  # type: ignore[operator]
+            except (TypeError, ValueError):
+                return _UNRESOLVED_STATIC
+        if left.kind == right.kind == "sequence":
+            return _StaticValue("sequence", tuple(left.value) + tuple(right.value))  # type: ignore[arg-type]
+        return _SYMBOLIC_STATIC
+    if isinstance(node, ast.BinOp):
+        left = _static_expression(node.left, environment)
+        right = _static_expression(node.right, environment)
+        return (
+            _UNRESOLVED_STATIC
+            if "unresolved" in (left.kind, right.kind)
+            else _SYMBOLIC_STATIC
+        )
+    if isinstance(node, ast.JoinedStr):
+        pieces: list[str] = []
+        for part in node.values:
+            if isinstance(part, ast.Constant) and type(part.value) is str:
+                pieces.append(part.value)
                 continue
-            for index, item in enumerate(argument.elts[:-1]):
-                if isinstance(item, ast.Constant) and item.value == "-c":
-                    programs.append(argument.elts[index + 1])
-    for expression in programs:
-        source = program_text(expression)
+            if not isinstance(part, ast.FormattedValue):
+                return _UNRESOLVED_STATIC
+            value = _static_expression(part.value, environment)
+            if value.kind == "unresolved":
+                return _UNRESOLVED_STATIC
+            if value.kind == "exact":
+                rendered: object = value.value
+                if part.conversion == ord("r"):
+                    rendered = repr(rendered)
+                elif part.conversion == ord("s"):
+                    rendered = str(rendered)
+                elif part.conversion == ord("a"):
+                    rendered = ascii(rendered)
+                elif part.conversion not in (-1, None):
+                    return _UNRESOLVED_STATIC
+                if part.format_spec is not None:
+                    spec = _static_expression(part.format_spec, environment)
+                    if spec.kind != "exact" or type(spec.value) is not str:
+                        return _UNRESOLVED_STATIC
+                    try:
+                        rendered = format(rendered, spec.value)
+                    except (TypeError, ValueError):
+                        return _UNRESOLVED_STATIC
+                pieces.append(str(rendered))
+            else:
+                pieces.append(
+                    repr("__pontius_fixed_value__")
+                    if part.conversion in (ord("r"), ord("a"))
+                    else "__pontius_fixed_value__"
+                )
+        return _StaticValue("exact", "".join(pieces))
+    if isinstance(node, ast.UnaryOp):
+        operand = _static_expression(node.operand, environment)
+        if operand.kind != "exact":
+            return operand
         try:
-            program = ast.parse(source, filename=f"{current_path}::<dynamic-c>")
-        except SyntaxError as error:
-            raise GenerationError(f"dynamic -c program cannot be parsed: {current_path}") from error
-        result.update(_import_paths(program, current_path, tracked))
-        for call in (node for node in ast.walk(program) if isinstance(node, ast.Call)):
-            if (
-                isinstance(call.func, ast.Attribute) and call.func.attr == "import_module"
-                and call.args and isinstance(call.args[0], ast.Constant)
-                and type(call.args[0].value) is str and call.args[0].value.startswith("pontius")
+            if isinstance(node.op, ast.USub):
+                return _StaticValue("exact", -operand.value)  # type: ignore[operator]
+            if isinstance(node.op, ast.UAdd):
+                return _StaticValue("exact", +operand.value)  # type: ignore[operator]
+            if isinstance(node.op, ast.Not):
+                return _StaticValue("exact", not operand.value)
+        except (TypeError, ValueError):
+            return _UNRESOLVED_STATIC
+    if isinstance(node, (ast.Attribute, ast.Subscript)):
+        base = _static_expression(node.value, environment)
+        return _UNRESOLVED_STATIC if base.kind == "unresolved" else _SYMBOLIC_STATIC
+    if isinstance(node, ast.Call):
+        arguments = [_static_expression(argument, environment) for argument in node.args]
+        arguments.extend(
+            _static_expression(keyword.value, environment)
+            for keyword in node.keywords
+            if keyword.arg is not None
+        )
+        if any(argument.kind == "unresolved" for argument in arguments):
+            return _UNRESOLVED_STATIC
+        if isinstance(node.func, ast.Name) and node.func.id in {"str", "repr", "ascii"} and len(arguments) == 1:
+            if arguments[0].kind == "exact":
+                function = {"str": str, "repr": repr, "ascii": ascii}[node.func.id]
+                return _StaticValue("exact", function(arguments[0].value))
+            return _SYMBOLIC_STATIC
+        callee = _static_expression(node.func, environment)
+        return _UNRESOLVED_STATIC if callee.kind == "unresolved" else _SYMBOLIC_STATIC
+    if isinstance(node, (ast.Dict, ast.Set)):
+        values = list(node.values) if isinstance(node, ast.Dict) else list(node.elts)
+        fixed = [_static_expression(value, environment) for value in values]
+        return _UNRESOLVED_STATIC if any(value.kind == "unresolved" for value in fixed) else _SYMBOLIC_STATIC
+    return _UNRESOLVED_STATIC
+
+
+def _bind_static_target(
+    environment: dict[str, _StaticValue], target: ast.AST, value: _StaticValue,
+    inventory: _AssignmentInventory, *, conditional: bool,
+) -> None:
+    if isinstance(target, ast.Name):
+        environment[target.id] = (
+            value
+            if not conditional
+            and (inventory.counts.get(target.id) == 1 or value.kind == "symbolic")
+            else _UNRESOLVED_STATIC
+        )
+        return
+    for name in _target_names(target):
+        environment[name] = _UNRESOLVED_STATIC
+
+
+def _mentions_dash_c(
+    expression: ast.AST, definitions: Mapping[str, Sequence[ast.AST]], seen: set[str] | None = None
+) -> bool:
+    seen = set() if seen is None else seen
+    for node in ast.walk(expression):
+        if isinstance(node, ast.Constant) and node.value == "-c":
+            return True
+        if isinstance(node, ast.Name) and node.id not in seen:
+            seen.add(node.id)
+            if any(_mentions_dash_c(item, definitions, seen) for item in definitions.get(node.id, ())):
+                return True
+    return False
+
+
+def _process_dynamic_program(
+    source: str, current_path: str, tracked: set[str], result: set[str]
+) -> None:
+    try:
+        program = ast.parse(source, filename=f"{current_path}::<dynamic-c>")
+    except SyntaxError as error:
+        raise GenerationError(f"dynamic -c program cannot be parsed: {current_path}") from error
+    result.update(_import_paths(program, current_path, tracked))
+    for call in (node for node in ast.walk(program) if isinstance(node, ast.Call)):
+        if not (
+            isinstance(call.func, ast.Attribute) and call.func.attr == "import_module" and call.args
+        ):
+            continue
+        module = _static_expression(call.args[0], {})
+        if module.kind != "exact" or type(module.value) is not str:
+            raise GenerationError(f"dynamic import target is not fixed in {current_path}")
+        if not module.value.startswith("pontius"):
+            continue
+        path = _module_path(module.value, tracked)
+        if path is None:
+            raise GenerationError(f"unresolved dynamic local import {module.value!r} in {current_path}")
+        result.add(path)
+
+
+def _inspect_dynamic_call(
+    call: ast.Call, environment: Mapping[str, _StaticValue], inventory: _AssignmentInventory,
+    current_path: str, tracked: set[str], result: set[str],
+) -> None:
+    if not (
+        isinstance(call.func, ast.Attribute)
+        and isinstance(call.func.value, ast.Name)
+        and call.func.value.id == "subprocess"
+        and call.func.attr in {"run", "Popen", "call", "check_call", "check_output"}
+    ):
+        return
+    arguments = list(call.args[:1])
+    arguments.extend(keyword.value for keyword in call.keywords if keyword.arg == "args")
+    for expression in arguments:
+        argv = _static_expression(expression, environment)
+        if argv.kind != "sequence":
+            if _mentions_dash_c(expression, inventory.definitions):
+                raise GenerationError(f"dynamic -c argv is not fixed in {current_path}")
+            continue
+        values = tuple(argv.value)  # type: ignore[arg-type]
+        indexes = [
+            index for index, value in enumerate(values)
+            if value.kind == "exact" and value.value == "-c"
+        ]
+        if not indexes:
+            if _mentions_dash_c(expression, inventory.definitions):
+                raise GenerationError(f"dynamic -c argv is ambiguous in {current_path}")
+            continue
+        if len(indexes) != 1 or indexes[0] + 1 >= len(values):
+            raise GenerationError(f"dynamic -c argv is malformed in {current_path}")
+        program = values[indexes[0] + 1]
+        if program.kind != "exact" or type(program.value) is not str:
+            raise GenerationError(f"dynamic -c program is not statically fixed in {current_path}")
+        _process_dynamic_program(program.value, current_path, tracked, result)
+
+
+class _CallInspector(ast.NodeVisitor):
+    def __init__(
+        self, environment: Mapping[str, _StaticValue], inventory: _AssignmentInventory,
+        current_path: str, tracked: set[str], result: set[str],
+    ) -> None:
+        self.environment = environment
+        self.inventory = inventory
+        self.current_path = current_path
+        self.tracked = tracked
+        self.result = result
+
+    def visit_Call(self, node: ast.Call) -> None:
+        _inspect_dynamic_call(
+            node, self.environment, self.inventory, self.current_path, self.tracked, self.result
+        )
+        self.generic_visit(node)
+
+    def visit_Lambda(self, node: ast.Lambda) -> None:
+        return None
+
+
+def _inspect_expression_calls(
+    expression: ast.AST, environment: Mapping[str, _StaticValue],
+    inventory: _AssignmentInventory, current_path: str, tracked: set[str], result: set[str],
+) -> None:
+    _CallInspector(environment, inventory, current_path, tracked, result).visit(expression)
+
+
+def _analyze_dynamic_statements(
+    statements: Sequence[ast.stmt], environment: dict[str, _StaticValue],
+    inventory: _AssignmentInventory, current_path: str, tracked: set[str], result: set[str],
+    *, conditional: bool = False,
+) -> None:
+    for statement in statements:
+        if isinstance(statement, ast.Assign):
+            _inspect_expression_calls(statement.value, environment, inventory, current_path, tracked, result)
+            value = _static_expression(statement.value, environment)
+            for target in statement.targets:
+                _bind_static_target(environment, target, value, inventory, conditional=conditional)
+        elif isinstance(statement, ast.AnnAssign):
+            if statement.value is not None:
+                _inspect_expression_calls(statement.value, environment, inventory, current_path, tracked, result)
+                value = _static_expression(statement.value, environment)
+            else:
+                value = _UNRESOLVED_STATIC
+            _bind_static_target(environment, statement.target, value, inventory, conditional=conditional)
+        elif isinstance(statement, ast.AugAssign):
+            _inspect_expression_calls(statement.value, environment, inventory, current_path, tracked, result)
+            _bind_static_target(
+                environment, statement.target, _UNRESOLVED_STATIC, inventory, conditional=True
+            )
+        elif isinstance(statement, (ast.Expr, ast.Return, ast.Raise, ast.Assert)):
+            for value in (
+                getattr(statement, "value", None), getattr(statement, "exc", None),
+                getattr(statement, "test", None), getattr(statement, "msg", None),
             ):
-                path = _module_path(call.args[0].value, tracked)
-                if path is None:
-                    raise GenerationError(f"unresolved dynamic local import {call.args[0].value!r} in {current_path}")
-                result.add(path)
+                if isinstance(value, ast.AST):
+                    _inspect_expression_calls(value, environment, inventory, current_path, tracked, result)
+        elif isinstance(statement, (ast.With, ast.AsyncWith)):
+            for item in statement.items:
+                _inspect_expression_calls(item.context_expr, environment, inventory, current_path, tracked, result)
+                if item.optional_vars is not None:
+                    context = _static_expression(item.context_expr, environment)
+                    value = _UNRESOLVED_STATIC if context.kind == "unresolved" else _SYMBOLIC_STATIC
+                    _bind_static_target(
+                        environment, item.optional_vars, value, inventory, conditional=conditional
+                    )
+            _analyze_dynamic_statements(
+                statement.body, environment, inventory, current_path, tracked, result,
+                conditional=conditional,
+            )
+        elif isinstance(statement, ast.If):
+            _inspect_expression_calls(statement.test, environment, inventory, current_path, tracked, result)
+            _analyze_dynamic_statements(
+                statement.body, dict(environment), inventory, current_path, tracked, result,
+                conditional=True,
+            )
+            _analyze_dynamic_statements(
+                statement.orelse, dict(environment), inventory, current_path, tracked, result,
+                conditional=True,
+            )
+            for name, count in inventory.counts.items():
+                if count and any(name in _target_names(node) for node in ast.walk(statement)):
+                    environment[name] = _UNRESOLVED_STATIC
+        elif isinstance(statement, (ast.For, ast.AsyncFor, ast.While)):
+            expression = statement.iter if isinstance(statement, (ast.For, ast.AsyncFor)) else statement.test
+            _inspect_expression_calls(expression, environment, inventory, current_path, tracked, result)
+            branch_environment = dict(environment)
+            if isinstance(statement, (ast.For, ast.AsyncFor)):
+                _bind_static_target(
+                    branch_environment, statement.target, _UNRESOLVED_STATIC, inventory, conditional=True
+                )
+            _analyze_dynamic_statements(
+                statement.body, branch_environment, inventory, current_path, tracked, result,
+                conditional=True,
+            )
+            _analyze_dynamic_statements(
+                statement.orelse, dict(environment), inventory, current_path, tracked, result,
+                conditional=True,
+            )
+        elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
+            _analyze_dynamic_function(statement, environment, current_path, tracked, result)
+        elif isinstance(statement, ast.Try):
+            for branch in (statement.body, statement.orelse, statement.finalbody):
+                _analyze_dynamic_statements(
+                    branch, dict(environment), inventory, current_path, tracked, result,
+                    conditional=True,
+                )
+            for handler in statement.handlers:
+                _analyze_dynamic_statements(
+                    handler.body, dict(environment), inventory, current_path, tracked, result,
+                    conditional=True,
+                )
+
+
+def _analyze_dynamic_function(
+    function: ast.FunctionDef | ast.AsyncFunctionDef, enclosing: Mapping[str, _StaticValue],
+    current_path: str, tracked: set[str], result: set[str],
+) -> None:
+    inventory = _assignment_inventory(function.body)
+    environment = dict(enclosing)
+    arguments = (
+        list(function.args.posonlyargs) + list(function.args.args)
+        + list(function.args.kwonlyargs)
+    )
+    if function.args.vararg is not None:
+        arguments.append(function.args.vararg)
+    if function.args.kwarg is not None:
+        arguments.append(function.args.kwarg)
+    for argument in arguments:
+        environment[argument.arg] = _UNRESOLVED_STATIC
+    _analyze_dynamic_statements(
+        function.body, environment, inventory, current_path, tracked, result
+    )
+
+
+def _module_static_environment(tree: ast.Module) -> dict[str, _StaticValue]:
+    inventory = _assignment_inventory(tree.body)
+    environment: dict[str, _StaticValue] = {"__file__": _SYMBOLIC_STATIC}
+    for statement in tree.body:
+        if isinstance(statement, (ast.Import, ast.ImportFrom)):
+            for alias in statement.names:
+                environment[alias.asname or alias.name.split(".")[0]] = _SYMBOLIC_STATIC
+        elif isinstance(statement, ast.Assign):
+            value = _static_expression(statement.value, environment)
+            for target in statement.targets:
+                _bind_static_target(environment, target, value, inventory, conditional=False)
+        elif isinstance(statement, ast.AnnAssign):
+            value = (
+                _static_expression(statement.value, environment)
+                if statement.value is not None else _UNRESOLVED_STATIC
+            )
+            _bind_static_target(environment, statement.target, value, inventory, conditional=False)
+    return environment
+
+
+def _dynamic_program_imports(tree: ast.AST, current_path: str, tracked: set[str]) -> set[str]:
+    if not isinstance(tree, ast.Module):
+        raise GenerationError("dynamic program analysis requires a module")
+    enclosing = _module_static_environment(tree)
+    result: set[str] = set()
+    module_inventory = _assignment_inventory(tree.body)
+    module_environment: dict[str, _StaticValue] = {"__file__": _SYMBOLIC_STATIC}
+    for statement in tree.body:
+        if isinstance(statement, (ast.Import, ast.ImportFrom)):
+            for alias in statement.names:
+                module_environment[alias.asname or alias.name.split(".")[0]] = _SYMBOLIC_STATIC
+        elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
+            _analyze_dynamic_function(statement, enclosing, current_path, tracked, result)
+        elif isinstance(statement, ast.ClassDef):
+            for child in statement.body:
+                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
+                    _analyze_dynamic_function(child, enclosing, current_path, tracked, result)
+        else:
+            _analyze_dynamic_statements(
+                [statement], module_environment, module_inventory, current_path, tracked, result
+            )
     return result
 
 
 def _phase_paths(git: _Git, phase: Mapping[str, str]) -> tuple[str, ...]:
     commit = phase["commit"]
     tracked = set(git.tracked_paths(commit))
     selected_test = phase["selected_test"]
     decision_path = phase["decision_path"]
     for required in (selected_test, decision_path):
         if required not in tracked:
