$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$workspaceRoot = (Resolve-Path (Join-Path $projectRoot '../..')).Path
$harnessRoot = Join-Path $workspaceRoot 'work/second-boss-harness'
$srcRoot = Join-Path $harnessRoot 'src'
New-Item -ItemType Directory -Force -Path $srcRoot | Out-Null
Get-ChildItem -LiteralPath (Join-Path $projectRoot 'megadrive/src') -File | ForEach-Object {
    if ($_.Name -eq 'actors.c') { Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $srcRoot 'actors.inc') } elseif ($_.Name -eq 'main.c') {
        Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $srcRoot 'game_main.inc')
    } else { Copy-Item -LiteralPath $_.FullName -Destination $srcRoot }
}
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'second_boss_harness.c') -Destination (Join-Path $srcRoot 'main.c')
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'second_boss_cases.inc') -Destination $srcRoot
$sdkPath = (Resolve-Path (Join-Path $workspaceRoot 'work/sgdk')).Path.Replace('\','/')
$sdkUnix = '/' + $sdkPath.Substring(0,1).ToLower() + $sdkPath.Substring(2)
$previousPath = $env:Path
Push-Location $harnessRoot
try {
    $env:Path = "$sdkPath/bin;$previousPath"
    & "$sdkPath/bin/sh.exe" -c 'export PATH="$3/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" "JAVA=$2" -j2' build $sdkPath 'D:/jdk-25.0.1/bin/java.exe' $sdkUnix
    if ($LASTEXITCODE -ne 0) { throw 'World loader harness build failed' }
} finally { $env:Path = $previousPath; Pop-Location }


