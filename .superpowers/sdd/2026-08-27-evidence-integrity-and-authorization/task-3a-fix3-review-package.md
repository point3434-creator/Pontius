# Review package: 4b72588b9e24dfa934a59fc58cb54c330ed7606f..9041ba52f4304fc90b453299d8174fb180162d18

## Commits
9041ba5 fix(evidence): reject symbolic import targets

## Files changed
 tests/test_evidence_manifest_generation.py | 55 ++++++++++++++++++
 tools/generate_evidence_manifests.py       | 93 +++++++++++++++++++++++++-----
 2 files changed, 133 insertions(+), 15 deletions(-)

## Diff
diff --git a/tests/test_evidence_manifest_generation.py b/tests/test_evidence_manifest_generation.py
index 57eda43..46a164c 100644
--- a/tests/test_evidence_manifest_generation.py
+++ b/tests/test_evidence_manifest_generation.py
@@ -389,20 +389,75 @@ class Selected:
             program = f"value={str(root)!r}; import pontius.alpha"
             subprocess.run([python, "-c", program])
 '''
         self.assertEqual(
             GENERATOR._dynamic_program_imports(
                 ast.parse(source), "tests/t.py", {"src/pontius/alpha.py"}
             ),
             {"src/pontius/alpha.py"},
         )
 
+    def test_dynamic_dash_c_rejects_symbolic_import_targets(self) -> None:
+        programs = (
+            'program = f"import {MODULE}"',
+            'program = f"from {MODULE} import runner"',
+            'program = f"import importlib; importlib.import_module({MODULE!r})"',
+            'program = f"__import__({MODULE!r})"',
+            'program = f"import {MODULE:.1}"',
+        )
+        tracked = {"src/pontius/alpha.py"}
+        for assignment in programs:
+            source = f'''\
+from pathlib import Path
+MODULE = Path("pontius.alpha").name
+class Selected:
+    def probe(self):
+        {assignment}
+        subprocess.run([python, "-c", program])
+'''
+            with self.subTest(assignment=assignment), self.assertRaises(
+                GENERATOR.GenerationError
+            ):
+                GENERATOR._dynamic_program_imports(ast.parse(source), "tests/t.py", tracked)
+
+    def test_dynamic_dash_c_resolves_exact_builtin_import_target(self) -> None:
+        source = '''
+MODULE = "pontius.alpha"
+class Selected:
+    def probe(self):
+        program = f"__import__({MODULE!r})"
+        subprocess.run([python, "-c", program])
+'''
+        self.assertEqual(
+            GENERATOR._dynamic_program_imports(
+                ast.parse(source), "tests/t.py", {"src/pontius/alpha.py"}
+            ),
+            {"src/pontius/alpha.py"},
+        )
+
+    def test_dynamic_dash_c_symbolic_nonimport_context_cannot_collide_with_marker(self) -> None:
+        source = '''
+from pathlib import Path
+MODULE = "pontius.alpha"
+LAUNCHER = Path("run-selected.py").name
+class Selected:
+    def probe(self):
+        program = f"sentinel='__pontius_fixed_value__'; launch={LAUNCHER!r}; import a__pontius_symbolic__; import b__pontius_symbolic__; import {MODULE}"
+        subprocess.run([python, "-c", program])
+'''
+        self.assertEqual(
+            GENERATOR._dynamic_program_imports(
+                ast.parse(source), "tests/t.py", {"src/pontius/alpha.py"}
+            ),
+            {"src/pontius/alpha.py"},
+        )
+
     def test_dynamic_dash_c_rejects_ambiguous_dynamic_reassigned_and_branch_values(self) -> None:
         cases = (
             '''
 class Selected:
     def dynamic(self, module):
         program = f"import pontius.{module}"
         subprocess.run([python, "-c", program])
 ''',
             '''
 class Selected:
diff --git a/tools/generate_evidence_manifests.py b/tools/generate_evidence_manifests.py
index dbb5ba0..7d4200e 100644
--- a/tools/generate_evidence_manifests.py
+++ b/tools/generate_evidence_manifests.py
@@ -650,29 +650,32 @@ def _literal_paths(tree: ast.AST, text: str, tracked: set[str]) -> set[str]:
                         candidates.add(normalized[position:])
         if isinstance(node, ast.Constant) and type(node.value) is str:
             value = node.value.replace("\\", "/")
             if value in tracked:
                 candidates.add(value)
     allowed = ("experiments/configs/", "docs/decisions/")
     return {_relative_path(path) for path in candidates if path in tracked and path.startswith(allowed)}
 
 
 class _StaticValue:
-    __slots__ = ("kind", "value")
+    __slots__ = ("alternate", "kind", "value")
 
-    def __init__(self, kind: str, value: object = None) -> None:
+    def __init__(self, kind: str, value: object = None, alternate: object = None) -> None:
         self.kind = kind
         self.value = value
+        self.alternate = value if alternate is None else alternate
 
 
 _UNRESOLVED_STATIC = _StaticValue("unresolved")
 _SYMBOLIC_STATIC = _StaticValue("symbolic")
+_SYMBOLIC_PRIMARY_TEXT = "a__pontius_symbolic__"
+_SYMBOLIC_ALTERNATE_TEXT = "b__pontius_symbolic__"
 
 
 def _target_names(target: ast.AST) -> set[str]:
     return {
         node.id for node in ast.walk(target)
         if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
     }
 
 
 class _AssignmentInventory(ast.NodeVisitor):
@@ -751,71 +754,99 @@ def _static_expression(node: ast.AST, environment: Mapping[str, _StaticValue]) -
         return environment.get(node.id, _UNRESOLVED_STATIC)
     if isinstance(node, (ast.List, ast.Tuple)):
         return _StaticValue("sequence", tuple(_static_expression(item, environment) for item in node.elts))
     if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
         left = _static_expression(node.left, environment)
         right = _static_expression(node.right, environment)
         if "unresolved" in (left.kind, right.kind):
             return _UNRESOLVED_STATIC
         if left.kind == right.kind == "exact":
             try:
-                return _StaticValue("exact", left.value + right.value)  # type: ignore[operator]
+                return _StaticValue(
+                    "exact",
+                    left.value + right.value,  # type: ignore[operator]
+                    left.alternate + right.alternate,  # type: ignore[operator]
+                )
             except (TypeError, ValueError):
                 return _UNRESOLVED_STATIC
         if left.kind == right.kind == "sequence":
             return _StaticValue("sequence", tuple(left.value) + tuple(right.value))  # type: ignore[arg-type]
         return _SYMBOLIC_STATIC
     if isinstance(node, ast.BinOp):
         left = _static_expression(node.left, environment)
         right = _static_expression(node.right, environment)
         return (
             _UNRESOLVED_STATIC
             if "unresolved" in (left.kind, right.kind)
             else _SYMBOLIC_STATIC
         )
     if isinstance(node, ast.JoinedStr):
         pieces: list[str] = []
+        alternate_pieces: list[str] = []
         for part in node.values:
             if isinstance(part, ast.Constant) and type(part.value) is str:
                 pieces.append(part.value)
+                alternate_pieces.append(part.value)
                 continue
             if not isinstance(part, ast.FormattedValue):
                 return _UNRESOLVED_STATIC
             value = _static_expression(part.value, environment)
             if value.kind == "unresolved":
                 return _UNRESOLVED_STATIC
             if value.kind == "exact":
                 rendered: object = value.value
+                alternate_rendered: object = value.alternate
                 if part.conversion == ord("r"):
                     rendered = repr(rendered)
+                    alternate_rendered = repr(alternate_rendered)
                 elif part.conversion == ord("s"):
                     rendered = str(rendered)
+                    alternate_rendered = str(alternate_rendered)
                 elif part.conversion == ord("a"):
                     rendered = ascii(rendered)
+                    alternate_rendered = ascii(alternate_rendered)
                 elif part.conversion not in (-1, None):
                     return _UNRESOLVED_STATIC
                 if part.format_spec is not None:
                     spec = _static_expression(part.format_spec, environment)
                     if spec.kind != "exact" or type(spec.value) is not str:
                         return _UNRESOLVED_STATIC
                     try:
                         rendered = format(rendered, spec.value)
+                        alternate_rendered = format(alternate_rendered, spec.alternate)
                     except (TypeError, ValueError):
                         return _UNRESOLVED_STATIC
                 pieces.append(str(rendered))
+                alternate_pieces.append(str(alternate_rendered))
             else:
-                pieces.append(
-                    repr("__pontius_fixed_value__")
-                    if part.conversion in (ord("r"), ord("a"))
-                    else "__pontius_fixed_value__"
-                )
-        return _StaticValue("exact", "".join(pieces))
+                primary: object = _SYMBOLIC_PRIMARY_TEXT
+                alternate: object = _SYMBOLIC_ALTERNATE_TEXT
+                if part.conversion == ord("r"):
+                    primary, alternate = repr(primary), repr(alternate)
+                elif part.conversion == ord("s"):
+                    primary, alternate = str(primary), str(alternate)
+                elif part.conversion == ord("a"):
+                    primary, alternate = ascii(primary), ascii(alternate)
+                elif part.conversion not in (-1, None):
+                    return _UNRESOLVED_STATIC
+                if part.format_spec is not None:
+                    spec = _static_expression(part.format_spec, environment)
+                    if spec.kind != "exact" or type(spec.value) is not str:
+                        return _UNRESOLVED_STATIC
+                    try:
+                        primary = format(primary, spec.value)
+                        alternate = format(alternate, spec.alternate)
+                    except (TypeError, ValueError):
+                        return _UNRESOLVED_STATIC
+                pieces.append(str(primary))
+                alternate_pieces.append(str(alternate))
+        return _StaticValue("exact", "".join(pieces), "".join(alternate_pieces))
     if isinstance(node, ast.UnaryOp):
         operand = _static_expression(node.operand, environment)
         if operand.kind != "exact":
             return operand
         try:
             if isinstance(node.op, ast.USub):
                 return _StaticValue("exact", -operand.value)  # type: ignore[operator]
             if isinstance(node.op, ast.UAdd):
                 return _StaticValue("exact", +operand.value)  # type: ignore[operator]
             if isinstance(node.op, ast.Not):
@@ -830,21 +861,25 @@ def _static_expression(node: ast.AST, environment: Mapping[str, _StaticValue]) -
         arguments.extend(
             _static_expression(keyword.value, environment)
             for keyword in node.keywords
             if keyword.arg is not None
         )
         if any(argument.kind == "unresolved" for argument in arguments):
             return _UNRESOLVED_STATIC
         if isinstance(node.func, ast.Name) and node.func.id in {"str", "repr", "ascii"} and len(arguments) == 1:
             if arguments[0].kind == "exact":
                 function = {"str": str, "repr": repr, "ascii": ascii}[node.func.id]
-                return _StaticValue("exact", function(arguments[0].value))
+                return _StaticValue(
+                    "exact",
+                    function(arguments[0].value),
+                    function(arguments[0].alternate),
+                )
             return _SYMBOLIC_STATIC
         callee = _static_expression(node.func, environment)
         return _UNRESOLVED_STATIC if callee.kind == "unresolved" else _SYMBOLIC_STATIC
     if isinstance(node, (ast.Dict, ast.Set)):
         values = list(node.values) if isinstance(node, ast.Dict) else list(node.elts)
         fixed = [_static_expression(value, environment) for value in values]
         return _UNRESOLVED_STATIC if any(value.kind == "unresolved" for value in fixed) else _SYMBOLIC_STATIC
     return _UNRESOLVED_STATIC
 
 
@@ -871,32 +906,58 @@ def _mentions_dash_c(
     for node in ast.walk(expression):
         if isinstance(node, ast.Constant) and node.value == "-c":
             return True
         if isinstance(node, ast.Name) and node.id not in seen:
             seen.add(node.id)
             if any(_mentions_dash_c(item, definitions, seen) for item in definitions.get(node.id, ())):
                 return True
     return False
 
 
+def _dynamic_import_targets(program: ast.AST, current_path: str) -> tuple[object, ...]:
+    targets: list[object] = []
+    for node in ast.walk(program):
+        if isinstance(node, ast.Import):
+            targets.append(("import", tuple(alias.name for alias in node.names)))
+        elif isinstance(node, ast.ImportFrom):
+            targets.append(
+                ("from", node.level, node.module, tuple(alias.name for alias in node.names))
+            )
+        elif isinstance(node, ast.Call):
+            is_import_module = isinstance(node.func, ast.Attribute) and node.func.attr == "import_module"
+            is_builtin_import = isinstance(node.func, ast.Name) and node.func.id == "__import__"
+            if not (is_import_module or is_builtin_import) or not node.args:
+                continue
+            module = _static_expression(node.args[0], {})
+            if module.kind != "exact" or type(module.value) is not str:
+                raise GenerationError(f"dynamic import target is not fixed in {current_path}")
+            targets.append(("call", "import_module" if is_import_module else "__import__", module.value))
+    return tuple(targets)
+
+
 def _process_dynamic_program(
-    source: str, current_path: str, tracked: set[str], result: set[str]
+    source: str, alternate_source: str, current_path: str, tracked: set[str], result: set[str]
 ) -> None:
     try:
         program = ast.parse(source, filename=f"{current_path}::<dynamic-c>")
+        alternate_program = ast.parse(alternate_source, filename=f"{current_path}::<dynamic-c>")
     except SyntaxError as error:
         raise GenerationError(f"dynamic -c program cannot be parsed: {current_path}") from error
+    if _dynamic_import_targets(program, current_path) != _dynamic_import_targets(
+        alternate_program, current_path
+    ):
+        raise GenerationError(f"dynamic import target is not fixed in {current_path}")
     result.update(_import_paths(program, current_path, tracked))
     for call in (node for node in ast.walk(program) if isinstance(node, ast.Call)):
-        if not (
-            isinstance(call.func, ast.Attribute) and call.func.attr == "import_module" and call.args
-        ):
+        is_import_module = isinstance(call.func, ast.Attribute) and call.func.attr == "import_module"
+        is_builtin_import = isinstance(call.func, ast.Name) and call.func.id == "__import__"
+        if not (is_import_module or is_builtin_import) or not call.args:
             continue
         module = _static_expression(call.args[0], {})
         if module.kind != "exact" or type(module.value) is not str:
             raise GenerationError(f"dynamic import target is not fixed in {current_path}")
         if not module.value.startswith("pontius"):
             continue
         path = _module_path(module.value, tracked)
         if path is None:
             raise GenerationError(f"unresolved dynamic local import {module.value!r} in {current_path}")
         result.add(path)
@@ -928,21 +989,23 @@ def _inspect_dynamic_call(
         ]
         if not indexes:
             if _mentions_dash_c(expression, inventory.definitions):
                 raise GenerationError(f"dynamic -c argv is ambiguous in {current_path}")
             continue
         if len(indexes) != 1 or indexes[0] + 1 >= len(values):
             raise GenerationError(f"dynamic -c argv is malformed in {current_path}")
         program = values[indexes[0] + 1]
         if program.kind != "exact" or type(program.value) is not str:
             raise GenerationError(f"dynamic -c program is not statically fixed in {current_path}")
-        _process_dynamic_program(program.value, current_path, tracked, result)
+        _process_dynamic_program(
+            program.value, program.alternate, current_path, tracked, result
+        )
 
 
 class _CallInspector(ast.NodeVisitor):
     def __init__(
         self, environment: Mapping[str, _StaticValue], inventory: _AssignmentInventory,
         current_path: str, tracked: set[str], result: set[str],
     ) -> None:
         self.environment = environment
         self.inventory = inventory
         self.current_path = current_path
