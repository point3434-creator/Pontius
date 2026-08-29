# Review package: 9041ba52f4304fc90b453299d8174fb180162d18..e0d29dd86bafcea21dbd99336914ee5197572af4

## Commits
e0d29dd fix(evidence): bind dynamic import call contracts

## Files changed
 tests/test_evidence_manifest_generation.py | 123 +++++++++++++++++
 tools/generate_evidence_manifests.py       | 210 +++++++++++++++++++++++++----
 2 files changed, 308 insertions(+), 25 deletions(-)

## Diff
diff --git a/tests/test_evidence_manifest_generation.py b/tests/test_evidence_manifest_generation.py
index 46a164c..25e4c18 100644
--- a/tests/test_evidence_manifest_generation.py
+++ b/tests/test_evidence_manifest_generation.py
@@ -427,20 +427,143 @@ class Selected:
         program = f"__import__({MODULE!r})"
         subprocess.run([python, "-c", program])
 '''
         self.assertEqual(
             GENERATOR._dynamic_program_imports(
                 ast.parse(source), "tests/t.py", {"src/pontius/alpha.py"}
             ),
             {"src/pontius/alpha.py"},
         )
 
+    def test_dynamic_dash_c_import_module_binds_name_and_package(self) -> None:
+        tracked = {"src/pontius/alpha.py", "src/pontius/beta.py"}
+        cases = (
+            ("import importlib; importlib.import_module(name='pontius.alpha')", {"src/pontius/alpha.py"}),
+            ("import importlib; importlib.import_module('.alpha', 'pontius')", {"src/pontius/alpha.py"}),
+            ("import importlib; importlib.import_module(name='.beta', package='pontius')", {"src/pontius/beta.py"}),
+            ("import importlib; importlib.import_module('.alpha', package='pontius')", {"src/pontius/alpha.py"}),
+            ("import importlib; importlib.import_module('..beta', package='pontius.pkg')", {"src/pontius/beta.py"}),
+        )
+        for program, expected in cases:
+            source = f"subprocess.run([python, '-c', {program!r}])"
+            with self.subTest(program=program):
+                self.assertEqual(
+                    GENERATOR._dynamic_program_imports(ast.parse(source), "tests/t.py", tracked),
+                    expected,
+                )
+
+    def test_dynamic_dash_c_import_module_rejects_bad_binding_and_symbolic_resolution(self) -> None:
+        programs = (
+            "import importlib; importlib.import_module('.alpha')",
+            "import importlib; importlib.import_module('pontius.alpha', name='pontius.beta')",
+            "import importlib; importlib.import_module(name='pontius.alpha', unknown='value')",
+            "import importlib; importlib.import_module(*('pontius.alpha',))",
+            "import importlib; importlib.import_module(**{'name': 'pontius.alpha'})",
+            "import importlib; importlib.import_module('pontius.alpha', 'pontius', 'extra')",
+            "import importlib; importlib.import_module(name=NAME)",
+            "import importlib; importlib.import_module('.alpha', package=PACKAGE)",
+        )
+        tracked = {"src/pontius/alpha.py", "src/pontius/beta.py"}
+        for program in programs:
+            source = f"subprocess.run([python, '-c', {program!r}])"
+            with self.subTest(program=program), self.assertRaises(GENERATOR.GenerationError):
+                GENERATOR._dynamic_program_imports(ast.parse(source), "tests/t.py", tracked)
+
+        tainted_programs = (
+            "program = f\"import importlib; importlib.import_module(name={NAME!r}, package='pontius')\"",
+            "program = f\"import importlib; importlib.import_module('.alpha', package={PACKAGE!r})\"",
+            "program = f\"import importlib; importlib.import_module(name='pontius.alpha', package={PACKAGE:.1})\"",
+        )
+        for assignment in tainted_programs:
+            source = f'''\
+from pathlib import Path
+NAME = Path("alpha").name
+PACKAGE = Path("pontius").name
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
+    def test_dynamic_dash_c_builtin_import_binds_fromlist_and_keywords(self) -> None:
+        tracked = {
+            "src/pontius/__init__.py",
+            "src/pontius/alpha.py",
+            "src/pontius/pkg/__init__.py",
+            "src/pontius/pkg/beta.py",
+        }
+        cases = (
+            ("__import__(name='pontius.alpha')", {"src/pontius/alpha.py"}),
+            (
+                "__import__('pontius', fromlist=('alpha',))",
+                {"src/pontius/__init__.py", "src/pontius/alpha.py"},
+            ),
+            (
+                "__import__('pontius.pkg', globals(), locals(), fromlist=['beta'], level=0)",
+                {"src/pontius/pkg/__init__.py", "src/pontius/pkg/beta.py"},
+            ),
+            (
+                "__import__(name='pontius', globals=None, locals=None, fromlist=('alpha',), level=0)",
+                {"src/pontius/__init__.py", "src/pontius/alpha.py"},
+            ),
+        )
+        for program, expected in cases:
+            source = f"subprocess.run([python, '-c', {program!r}])"
+            with self.subTest(program=program):
+                self.assertEqual(
+                    GENERATOR._dynamic_program_imports(ast.parse(source), "tests/t.py", tracked),
+                    expected,
+                )
+
+    def test_dynamic_dash_c_builtin_import_rejects_bad_binding_and_symbolic_context(self) -> None:
+        programs = (
+            "__import__(name=NAME)",
+            "__import__('pontius', fromlist=FROMLIST)",
+            "__import__('pontius', fromlist=('*',))",
+            "__import__('pontius', level=LEVEL)",
+            "__import__('alpha', globals={'__package__': 'pontius'}, fromlist=('beta',), level=1)",
+            "__import__('alpha', globals(), locals(), ('beta',), 1)",
+            "__import__('pontius.alpha', name='pontius.beta')",
+            "__import__('pontius.alpha', mystery=1)",
+            "__import__(*ARGS)",
+            "__import__(**KWARGS)",
+            "__import__('pontius.alpha', None, None, (), 0, 'extra')",
+        )
+        tracked = {"src/pontius/__init__.py", "src/pontius/alpha.py"}
+        for program in programs:
+            source = f"subprocess.run([python, '-c', {program!r}])"
+            with self.subTest(program=program), self.assertRaises(GENERATOR.GenerationError):
+                GENERATOR._dynamic_program_imports(ast.parse(source), "tests/t.py", tracked)
+
+        tainted_programs = (
+            "program = f\"__import__('pontius', fromlist=({FROMLIST!r},))\"",
+            "program = f\"__import__('pontius', level={LEVEL!r})\"",
+        )
+        for assignment in tainted_programs:
+            source = f'''
+from pathlib import Path
+FROMLIST = Path("alpha").name
+LEVEL = Path("1").name
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
     def test_dynamic_dash_c_symbolic_nonimport_context_cannot_collide_with_marker(self) -> None:
         source = '''
 from pathlib import Path
 MODULE = "pontius.alpha"
 LAUNCHER = Path("run-selected.py").name
 class Selected:
     def probe(self):
         program = f"sentinel='__pontius_fixed_value__'; launch={LAUNCHER!r}; import a__pontius_symbolic__; import b__pontius_symbolic__; import {MODULE}"
         subprocess.run([python, "-c", program])
 '''
diff --git a/tools/generate_evidence_manifests.py b/tools/generate_evidence_manifests.py
index 7d4200e..ff2c850 100644
--- a/tools/generate_evidence_manifests.py
+++ b/tools/generate_evidence_manifests.py
@@ -906,68 +906,228 @@ def _mentions_dash_c(
     for node in ast.walk(expression):
         if isinstance(node, ast.Constant) and node.value == "-c":
             return True
         if isinstance(node, ast.Name) and node.id not in seen:
             seen.add(node.id)
             if any(_mentions_dash_c(item, definitions, seen) for item in definitions.get(node.id, ())):
                 return True
     return False
 
 
+_IMPORT_CALL_CONTRACTS = {
+    "importlib.import_module": (
+        ("name", "package"),
+        {"package": None},
+    ),
+    "__import__": (
+        ("name", "globals", "locals", "fromlist", "level"),
+        {"globals": None, "locals": None, "fromlist": (), "level": 0},
+    ),
+}
+
+
+def _import_callable_name(call: ast.Call) -> str | None:
+    if isinstance(call.func, ast.Name) and call.func.id == "__import__":
+        return "__import__"
+    if isinstance(call.func, ast.Attribute) and call.func.attr == "import_module":
+        return "importlib.import_module"
+    return None
+
+
+def _bind_import_call(
+    call: ast.Call, callable_name: str, current_path: str
+) -> dict[str, ast.AST]:
+    parameters, defaults = _IMPORT_CALL_CONTRACTS[callable_name]
+    if any(isinstance(argument, ast.Starred) for argument in call.args):
+        raise GenerationError(
+            f"dynamic {callable_name} arguments are not statically bound in {current_path}"
+        )
+    if len(call.args) > len(parameters):
+        raise GenerationError(
+            f"dynamic {callable_name} has too many positional arguments in {current_path}"
+        )
+    bound = dict(zip(parameters, call.args, strict=False))
+    for keyword in call.keywords:
+        if keyword.arg is None:
+            raise GenerationError(
+                f"dynamic {callable_name} keyword expansion is not statically bound in {current_path}"
+            )
+        if keyword.arg not in parameters:
+            raise GenerationError(
+                f"dynamic {callable_name} has unknown argument {keyword.arg!r} in {current_path}"
+            )
+        if keyword.arg in bound:
+            raise GenerationError(
+                f"dynamic {callable_name} duplicates argument {keyword.arg!r} in {current_path}"
+            )
+        bound[keyword.arg] = keyword.value
+    required = [parameter for parameter in parameters if parameter not in defaults]
+    missing = [parameter for parameter in required if parameter not in bound]
+    if missing:
+        raise GenerationError(
+            f"dynamic {callable_name} is missing argument {missing[0]!r} in {current_path}"
+        )
+    return bound
+
+
+def _exact_import_argument(
+    bound: Mapping[str, ast.AST], name: str, default: object, callable_name: str,
+    current_path: str,
+) -> object:
+    if name not in bound:
+        return default
+    value = _static_expression(bound[name], {})
+    if value.kind != "exact":
+        raise GenerationError(
+            f"dynamic {callable_name} argument {name!r} is not fixed in {current_path}"
+        )
+    return value.value
+
+
+def _exact_fromlist(
+    bound: Mapping[str, ast.AST], callable_name: str, current_path: str
+) -> tuple[str, ...]:
+    if "fromlist" not in bound:
+        return ()
+    value = _static_expression(bound["fromlist"], {})
+    if value.kind != "sequence":
+        raise GenerationError(
+            f"dynamic {callable_name} argument 'fromlist' is not fixed in {current_path}"
+        )
+    result: list[str] = []
+    for item in value.value:  # type: ignore[union-attr]
+        if item.kind != "exact" or type(item.value) is not str:
+            raise GenerationError(
+                f"dynamic {callable_name} argument 'fromlist' is not fixed in {current_path}"
+            )
+        result.append(item.value)
+    return tuple(result)
+
+
+def _resolve_import_module_name(name: str, package: object, current_path: str) -> str:
+    if not name:
+        raise GenerationError(f"dynamic import module name is empty in {current_path}")
+    if not name.startswith("."):
+        return name
+    if type(package) is not str or not package or package.startswith("."):
+        raise GenerationError(
+            f"dynamic relative import package is not fixed in {current_path}"
+        )
+    level = len(name) - len(name.lstrip("."))
+    package_parts = package.rsplit(".", level - 1)
+    if len(package_parts) < level or not package_parts[0]:
+        raise GenerationError(
+            f"dynamic relative import escapes its package in {current_path}"
+        )
+    suffix = name[level:]
+    return f"{package_parts[0]}.{suffix}" if suffix else package_parts[0]
+
+
+def _import_call_target(call: ast.Call, current_path: str) -> tuple[object, ...] | None:
+    callable_name = _import_callable_name(call)
+    if callable_name is None:
+        return None
+    bound = _bind_import_call(call, callable_name, current_path)
+    name = _exact_import_argument(bound, "name", None, callable_name, current_path)
+    if type(name) is not str or not name:
+        raise GenerationError(
+            f"dynamic {callable_name} argument 'name' is not a fixed string in {current_path}"
+        )
+    if callable_name == "importlib.import_module":
+        package = _exact_import_argument(
+            bound, "package", None, callable_name, current_path
+        )
+        if package is not None and type(package) is not str:
+            raise GenerationError(
+                f"dynamic {callable_name} argument 'package' is not a fixed string in {current_path}"
+            )
+        resolved = _resolve_import_module_name(name, package, current_path)
+        return ("call", callable_name, resolved, package)
+
+    fromlist = _exact_fromlist(bound, callable_name, current_path)
+    if "*" in fromlist:
+        raise GenerationError(
+            f"dynamic {callable_name} wildcard fromlist is not statically resolved in {current_path}"
+        )
+    level = _exact_import_argument(bound, "level", 0, callable_name, current_path)
+    if type(level) is not int or level < 0:
+        raise GenerationError(
+            f"dynamic {callable_name} argument 'level' is not a fixed nonnegative integer in {current_path}"
+        )
+    if level != 0 or name.startswith("."):
+        raise GenerationError(
+            f"dynamic relative {callable_name} context is not fixed in {current_path}"
+        )
+    return ("call", callable_name, name, fromlist, level)
+
+
 def _dynamic_import_targets(program: ast.AST, current_path: str) -> tuple[object, ...]:
     targets: list[object] = []
     for node in ast.walk(program):
         if isinstance(node, ast.Import):
             targets.append(("import", tuple(alias.name for alias in node.names)))
         elif isinstance(node, ast.ImportFrom):
             targets.append(
                 ("from", node.level, node.module, tuple(alias.name for alias in node.names))
             )
         elif isinstance(node, ast.Call):
-            is_import_module = isinstance(node.func, ast.Attribute) and node.func.attr == "import_module"
-            is_builtin_import = isinstance(node.func, ast.Name) and node.func.id == "__import__"
-            if not (is_import_module or is_builtin_import) or not node.args:
-                continue
-            module = _static_expression(node.args[0], {})
-            if module.kind != "exact" or type(module.value) is not str:
-                raise GenerationError(f"dynamic import target is not fixed in {current_path}")
-            targets.append(("call", "import_module" if is_import_module else "__import__", module.value))
+            target = _import_call_target(node, current_path)
+            if target is not None:
+                targets.append(target)
     return tuple(targets)
 
 
+def _dynamic_import_call_paths(
+    targets: Sequence[object], current_path: str, tracked: set[str]
+) -> set[str]:
+    result: set[str] = set()
+    for target in targets:
+        if not isinstance(target, tuple) or not target or target[0] != "call":
+            continue
+        callable_name = target[1]
+        module = target[2]
+        if type(module) is not str:
+            raise GenerationError(f"dynamic import target is malformed in {current_path}")
+        path = _module_path(module, tracked)
+        if path is not None:
+            result.add(path)
+        elif module == "pontius" or module.startswith("pontius."):
+            raise GenerationError(
+                f"unresolved dynamic local import {module!r} in {current_path}"
+            )
+        if callable_name != "__import__":
+            continue
+        fromlist = target[3]
+        if not isinstance(fromlist, tuple):
+            raise GenerationError(f"dynamic import fromlist is malformed in {current_path}")
+        for member in fromlist:
+            candidate = f"{module}.{member}"
+            candidate_path = _module_path(candidate, tracked)
+            if candidate_path is not None:
+                result.add(candidate_path)
+    return result
+
+
 def _process_dynamic_program(
     source: str, alternate_source: str, current_path: str, tracked: set[str], result: set[str]
 ) -> None:
     try:
         program = ast.parse(source, filename=f"{current_path}::<dynamic-c>")
         alternate_program = ast.parse(alternate_source, filename=f"{current_path}::<dynamic-c>")
     except SyntaxError as error:
         raise GenerationError(f"dynamic -c program cannot be parsed: {current_path}") from error
-    if _dynamic_import_targets(program, current_path) != _dynamic_import_targets(
-        alternate_program, current_path
-    ):
+    targets = _dynamic_import_targets(program, current_path)
+    alternate_targets = _dynamic_import_targets(alternate_program, current_path)
+    if targets != alternate_targets:
         raise GenerationError(f"dynamic import target is not fixed in {current_path}")
     result.update(_import_paths(program, current_path, tracked))
-    for call in (node for node in ast.walk(program) if isinstance(node, ast.Call)):
-        is_import_module = isinstance(call.func, ast.Attribute) and call.func.attr == "import_module"
-        is_builtin_import = isinstance(call.func, ast.Name) and call.func.id == "__import__"
-        if not (is_import_module or is_builtin_import) or not call.args:
-            continue
-        module = _static_expression(call.args[0], {})
-        if module.kind != "exact" or type(module.value) is not str:
-            raise GenerationError(f"dynamic import target is not fixed in {current_path}")
-        if not module.value.startswith("pontius"):
-            continue
-        path = _module_path(module.value, tracked)
-        if path is None:
-            raise GenerationError(f"unresolved dynamic local import {module.value!r} in {current_path}")
-        result.add(path)
+    result.update(_dynamic_import_call_paths(targets, current_path, tracked))
 
 
 def _inspect_dynamic_call(
     call: ast.Call, environment: Mapping[str, _StaticValue], inventory: _AssignmentInventory,
     current_path: str, tracked: set[str], result: set[str],
 ) -> None:
     if not (
         isinstance(call.func, ast.Attribute)
         and isinstance(call.func.value, ast.Name)
         and call.func.value.id == "subprocess"
