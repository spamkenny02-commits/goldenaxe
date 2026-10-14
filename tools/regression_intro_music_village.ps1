$ErrorActionPreference = 'Stop'
# Run after build.ps1 (or the general regression) to validate the current binary.
foreach ($validator in @('validate_intro.py','validate_music.py','validate_village_doors.py','validate_house_dialogue.py')) {
    & python "$PSScriptRoot\$validator"
    if ($LASTEXITCODE -ne 0) { throw "Validation failed: $validator" }
}
