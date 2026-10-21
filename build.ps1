param([string]$Sgdk = "$PSScriptRoot\..\..\work\sgdk", [string]$Java = 'D:/jdk-25.0.1/bin/java.exe')
$ErrorActionPreference = 'Stop'
& python "$PSScriptRoot/tools/generate_actor_descriptor_words.py"
if ($LASTEXITCODE -ne 0) { throw 'Actor descriptor word generation failed' }
& python "$PSScriptRoot/tools/generate_dialogue_glyph_lookup.py"
if ($LASTEXITCODE -ne 0) { throw 'Dialogue glyph lookup generation failed' }
& python "$PSScriptRoot/tools/generate_pattern_pairs.py"
if ($LASTEXITCODE -ne 0) { throw 'Pattern pair table generation failed' }
& python "$PSScriptRoot/tools/generate_pattern_plan.py"
if ($LASTEXITCODE -ne 0) { throw 'Pattern asset plan generation failed' }
& python "$PSScriptRoot/tools/generate_class0_video.py"
if ($LASTEXITCODE -ne 0) { throw 'Class0 video asset generation failed' }
$sdkPath = (Resolve-Path -LiteralPath $Sgdk).Path.Replace('\','/')
$sdkUnix = '/' + $sdkPath.Substring(0,1).ToLower() + $sdkPath.Substring(2)
Push-Location "$PSScriptRoot\megadrive"
$previousPath = $env:Path
try {
    $env:Path = "$sdkPath/bin;$previousPath"
    # Launch by name inside MSYS so old GNU make can restart after updating deps.
    & "$sdkPath/bin/sh.exe" -c 'export PATH="$3/bin:$PATH"; make -f "$1/makefile.gen" "GDK=$1" "JAVA=$2" -j2' build $sdkPath $Java $sdkUnix
    if ($LASTEXITCODE -ne 0) { throw 'SGDK build failed' }
    # Native code and assets now require a 1 MiB cartridge image.
    & $Java -jar "$sdkPath/bin/sizebnd.jar" 'out/release/rom.bin' '-sizealign' '1048576'
    if ($LASTEXITCODE -ne 0) { throw 'ROM padding/checksum failed' }
    # Mega Drive checksum: additive big-endian words from 0x200 to ROM end.
    & python "$PSScriptRoot/tools/finalize_md_rom.py" 'out/release/rom.bin'
    if ($LASTEXITCODE -ne 0) { throw 'Mega Drive checksum failed' }
    Copy-Item -LiteralPath 'out/release/rom.bin' -Destination "$PSScriptRoot\gaw-title-megadrive.bin"
    Copy-Item -LiteralPath 'out/release/rom.bin' -Destination "$PSScriptRoot\gaw-megadrive.bin"
    & python "$PSScriptRoot/tools/version_rom.py"
    if ($LASTEXITCODE -ne 0) { throw 'ROM version archive failed' }
} finally { $env:Path = $previousPath; Pop-Location }
