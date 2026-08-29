param(
    [Parameter(Mandatory = $true)][ValidatePattern('^[a-z0-9-]+$')][string]$Label,
    [Parameter(Mandatory = $true)][int]$ExpectedExit
)

$ErrorActionPreference = 'Stop'
$source = (Resolve-Path -LiteralPath 'C:\Users\point\AppData\Local\Temp\pontius-orch-task1').Path
$python = (Resolve-Path -LiteralPath 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe').Path
$gitExe = (Resolve-Path -LiteralPath 'C:\Program Files\Git\cmd\git.exe').Path
$tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd([IO.Path]::DirectorySeparatorChar)
$runRoot = Join-Path $tempRoot ("pontius-orch-task1-$Label-" + [guid]::NewGuid().ToString('N'))
$harness = Join-Path $runRoot 'harness'
$gitHome = Join-Path $runRoot 'git-home'
$childTemp = Join-Path $runRoot 'child-temp'
$sourceHead = (& $gitExe -C $source rev-parse HEAD).Trim()
$runFull = [IO.Path]::GetFullPath($runRoot)
$expectedLeaf = "^pontius-orch-task1-$([regex]::Escape($Label))-[0-9a-f]{32}$"
if ($sourceHead -ne 'b4a16549bbfc4a923e12a1f9b0ab74faa981ac8a' -or
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
        'checkout', '--detach', $sourceHead
    ))
    if (Test-Path -LiteralPath (Join-Path $harness '.git\objects\info\alternates')) {
        throw 'clone has object alternates'
    }
    foreach ($relative in @(
        'tools\__init__.py',
        'tools\test_orchestration\__init__.py',
        'tools\test_orchestration\errors.py',
        'tools\test_orchestration\model.py',
        'tools\test_orchestration\configuration.py',
        'tests\orchestration_test_support.py',
        'tests\test_test_orchestration_configuration.py'
    )) {
        Copy-Item -LiteralPath (Join-Path $source $relative) -Destination (Join-Path $harness $relative) -Force
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
        'PYTHONDONTWRITEBYTECODE' = '1'
        'PYTHONSAFEPATH' = '1'
        'PYTHONNOUSERSITE' = '1'
        'PYTHONHASHSEED' = '0'
        'PYTHONUTF8' = '1'
    }.GetEnumerator()) {
        $psi.Environment[$pair.Key] = [string]$pair.Value
    }
    foreach ($argument in @('-B', '-P', 'tests/test_test_orchestration_configuration.py', '-v')) {
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
