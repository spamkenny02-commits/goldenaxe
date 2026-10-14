$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$workspaceRoot = (Resolve-Path (Join-Path $projectRoot '../..')).Path
$harnessRoot = Join-Path $workspaceRoot 'work/actor-loader-harness'
$sdkPath = (Resolve-Path (Join-Path $workspaceRoot 'work/sgdk')).Path.Replace('\','/')
$sdkUnix = '/' + $sdkPath.Substring(0,1).ToLower() + $sdkPath.Substring(2)
Copy-Item -LiteralPath (Join-Path $projectRoot 'megadrive/src/actors.c'),(Join-Path $projectRoot 'megadrive/src/actors.h'),(Join-Path $projectRoot 'megadrive/src/actor_data.c') -Destination (Join-Path $harnessRoot 'src')
$previousPath = $env:Path
Push-Location $harnessRoot
try {
    $env:Path = "$sdkPath/bin;$previousPath"
    & "$sdkPath/bin/sh.exe" -c 'export PATH="$3/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" "JAVA=$2" -j2' build $sdkPath 'D:/jdk-25.0.1/bin/java.exe' $sdkUnix
    if ($LASTEXITCODE -ne 0) { throw 'Loader harness build failed' }
} finally { $env:Path = $previousPath; Pop-Location }
