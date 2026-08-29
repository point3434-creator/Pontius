param(
    [Parameter(Mandatory = $true)][ValidatePattern('^[a-z0-9-]+$')][string]$Label,
    [Parameter(Mandatory = $true)][ValidateSet(
        'test_test_orchestration_configuration.py',
        'test_inventory_and_profiles.py',
        'test_h32_pre_bet_initial_row_cache_seed.py',
        'test_legal_river_quotient_compiled_global_separation_calibration_v7.py'
    )][string]$TestFile,
    [Parameter(Mandatory = $true)][int]$ExpectedExit
)

$ErrorActionPreference = 'Stop'
$source = (Resolve-Path -LiteralPath 'D:\Pontius-worktrees\orch-task2').Path
$python = (Resolve-Path -LiteralPath 'D:\Pontius-worktrees\evidence-test-stabilization\.venv\Scripts\python.exe').Path
$gitExe = (Resolve-Path -LiteralPath 'C:\Program Files\Git\cmd\git.exe').Path
$isV7Authorization = (
    $TestFile -eq 'test_legal_river_quotient_compiled_global_separation_calibration_v7.py'
)
$tempRoot = if ($isV7Authorization) {
    'D:\p17'
}
else {
    Join-Path (Split-Path -Parent $source) '.snapshots'
}
if (-not (Test-Path -LiteralPath $tempRoot -PathType Container)) {
    New-Item -ItemType Directory -Path $tempRoot | Out-Null
}
$tempRoot = [IO.Path]::GetFullPath($tempRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
$runLeaf = if ($isV7Authorization) {
    'ac-' + [guid]::NewGuid().ToString('N').Substring(0, 8)
}
else {
    "pontius-orch-task2-$Label-" + [guid]::NewGuid().ToString('N')
}
$runRoot = Join-Path $tempRoot $runLeaf
$harness = Join-Path $runRoot 'harness'
$gitHome = Join-Path $runRoot 'git-home'
$childTemp = Join-Path $runRoot 'child-temp'
$sourceHead = (& $gitExe -C $source rev-parse HEAD).Trim()
$checkoutCommit = if ($isV7Authorization) {
    'aaca2dda40e29be8ebd091d58e7853bce1c62fd8'
}
else {
    $sourceHead
}
$runFull = [IO.Path]::GetFullPath($runRoot)
$expectedLeaf = if ($isV7Authorization) {
    '^ac-[0-9a-f]{8}$'
}
else {
    "^pontius-orch-task2-$([regex]::Escape($Label))-[0-9a-f]{32}$"
}
if ($sourceHead -ne 'a2659766319900793d835c9abac8bb0f3cf173ba' -or
    -not $runFull.StartsWith($tempRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or
    (Split-Path -Leaf $runFull) -notmatch $expectedLeaf) {
    throw 'snapshot precondition failed'
}
New-Item -ItemType Directory -Path $gitHome, $childTemp | Out-Null

function Invoke-ExactGit([string[]]$Arguments) {
    $psi = [Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $gitExe
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.Environment.Clear()
    foreach ($pair in @{
        'SystemRoot' = $env:SystemRoot
        'WINDIR' = $env:WINDIR
        'ComSpec' = $env:ComSpec
        'PATHEXT' = $env:PATHEXT
        'PATH' = ('C:\Program Files\Git\cmd;' + $env:SystemRoot + '\System32')
        'TEMP' = $childTemp
        'TMP' = $childTemp
        'HOME' = $gitHome
        'USERPROFILE' = $gitHome
        'GIT_CONFIG_NOSYSTEM' = '1'
        'GIT_CONFIG_GLOBAL' = 'NUL'
        'GIT_NO_REPLACE_OBJECTS' = '1'
        'GIT_LITERAL_PATHSPECS' = '1'
    }.GetEnumerator()) {
        $psi.Environment[$pair.Key] = [string]$pair.Value
    }
    foreach ($argument in $Arguments) {
        [void]$psi.ArgumentList.Add($argument)
    }
    $process = [Diagnostics.Process]::Start($psi)
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $process.WaitForExit()
    $stdout = $stdoutTask.GetAwaiter().GetResult()
    $stderr = $stderrTask.GetAwaiter().GetResult()
    if ($process.ExitCode -ne 0) {
        throw "Git failed ($($process.ExitCode)): $stderr"
    }
    return $stdout
}

try {
    [void](Invoke-ExactGit @(
        '-c', 'core.autocrlf=false', '-c', 'core.eol=lf', 'clone', '--local',
        '--no-hardlinks', '--no-checkout', $source, $harness
    ))
    [void](Invoke-ExactGit @(
        '-C', $harness, '-c', 'core.autocrlf=false', '-c', 'core.eol=lf',
        'checkout', '--detach', $checkoutCommit
    ))
    if (Test-Path -LiteralPath (Join-Path $harness '.git\objects\info\alternates')) {
        throw 'clone has object alternates'
    }
    $overlay = @(
        'tools\test_orchestration\model.py',
        'tools\test_orchestration\configuration.py',
        'tests\test_test_orchestration_configuration.py',
        'tools\generate_test_inventory.py',
        'tests\test-inventory.json',
        'tests\test-profiles.toml',
        'tests\test_inventory_and_profiles.py',
        'tests\test_h32_pre_bet_initial_row_cache_seed.py',
        'src\pontius\legal_river_quotient_compiled_global_separation_calibration_v7_result.py',
        'src\pontius\legal_river_quotient_compiled_global_separation_calibration_v7_runner.py',
        'tests\test_legal_river_quotient_compiled_global_separation_calibration_v7.py'
    )
    $utf8 = [Text.UTF8Encoding]::new($false, $true)
    foreach ($relative in $overlay) {
        $sourcePath = Join-Path $source $relative
        if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
            continue
        }
        $destination = Join-Path $harness $relative
        $parent = Split-Path -Parent $destination
        if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
            New-Item -ItemType Directory -Path $parent | Out-Null
        }
        $text = $utf8.GetString([IO.File]::ReadAllBytes($sourcePath))
        $canonical = $text.Replace("`r`n", "`n").Replace("`r", "`n")
        [IO.File]::WriteAllBytes($destination, $utf8.GetBytes($canonical))
    }

    $psi = [Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $python
    $psi.WorkingDirectory = $harness
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.Environment.Clear()
    foreach ($pair in @{
        'SystemRoot' = $env:SystemRoot
        'WINDIR' = $env:WINDIR
        'ComSpec' = $env:ComSpec
        'PATHEXT' = $env:PATHEXT
        'PATH' = ((Split-Path -Parent $python) + ';' + $env:SystemRoot + '\System32')
        'TEMP' = $childTemp
        'TMP' = $childTemp
        'PYTHONPATH' = (Join-Path $harness 'src')
        'PONTIUS_GIT' = $gitExe
        'PYTHONDONTWRITEBYTECODE' = '1'
        'PYTHONSAFEPATH' = '1'
        'PYTHONNOUSERSITE' = '1'
        'PYTHONHASHSEED' = '0'
        'PYTHONUTF8' = '1'
    }.GetEnumerator()) {
        $psi.Environment[$pair.Key] = [string]$pair.Value
    }
    $pythonArguments = @('-B', '-P', ("tests/" + $TestFile))
    if (
        $TestFile -eq 'test_legal_river_quotient_compiled_global_separation_calibration_v7.py'
    ) {
        $testClass = 'CompiledGlobalSeparationCalibrationV7Tests'
        $pythonArguments += @(
            "$testClass.test_phase_crossovers_filesystem_types_blob_and_labels_reject",
            "$testClass.test_writer_and_reader_bindings_are_complete_restore_and_lock_v4_first",
            "$testClass.test_actual_layered_header_round_trips_and_matches_frozen_recovery_shape",
            "$testClass.test_authorization_parser_and_injected_git_proof_are_real_and_type_exact",
            "$testClass.test_real_checkout_executes_exactly_one_validated_phase_branch"
        )
    }
    $pythonArguments += '-v'
    foreach ($argument in $pythonArguments) {
        [void]$psi.ArgumentList.Add($argument)
    }
    $process = [Diagnostics.Process]::Start($psi)
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $process.WaitForExit()
    $stdout = $stdoutTask.GetAwaiter().GetResult()
    $stderr = $stderrTask.GetAwaiter().GetResult()
    $exitCode = $process.ExitCode
    "SNAPSHOT=$runRoot"
    'STDOUT_BEGIN'
    $stdout
    'STDOUT_END'
    'STDERR_BEGIN'
    $stderr
    'STDERR_END'
    "EXIT_STATUS=$exitCode"
    if ($exitCode -ne $ExpectedExit) {
        throw "expected exit $ExpectedExit, observed $exitCode"
    }
}
finally {
    if (Test-Path -LiteralPath $runRoot) {
        $resolvedRun = (Resolve-Path -LiteralPath $runRoot).Path
        if (-not $resolvedRun.StartsWith($tempRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or
            (Split-Path -Leaf $resolvedRun) -notmatch $expectedLeaf) {
            throw 'cleanup target validation failed'
        }
        $reparse = Get-ChildItem -LiteralPath $resolvedRun -Force -Recurse |
            Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 }
        if ($reparse) {
            throw 'cleanup refused because snapshot contains a reparse point'
        }
        Get-ChildItem -LiteralPath $resolvedRun -Force -Recurse |
            Where-Object { -not $_.PSIsContainer } |
            ForEach-Object { $_.IsReadOnly = $false }
        [IO.Directory]::Delete($resolvedRun, $true)
        if (Test-Path -LiteralPath $resolvedRun) {
            throw 'snapshot cleanup failed'
        }
    }
    'CLEANED=true'
}
