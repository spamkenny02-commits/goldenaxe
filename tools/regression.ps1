param([switch]$SkipFire)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath "$PSScriptRoot\..").Path
$smsRom = "$projectRoot\input\original.sms"
$mdRom = "$projectRoot\gaw-megadrive.bin"

function Invoke-Capture([string]$Rom,[string]$Directory,[int]$Frames,[string]$Capture,[string[]]$Press) {
    $captureArgs = @("$PSScriptRoot\run_core.py",$Rom,'--frames',"$Frames",'--out',"$projectRoot\validation\$Directory",'--capture',$Capture)
    foreach ($buttonSequence in $Press) { $captureArgs += @('--press',$buttonSequence) }
    & python @captureArgs
    if ($LASTEXITCODE -ne 0) { throw "Capture failed: $Directory" }
}

& python "$PSScriptRoot\extract_inventory.py"
if ($LASTEXITCODE -ne 0) { throw 'Inventory extraction failed' }
& python "$PSScriptRoot\extract_actors.py"
if ($LASTEXITCODE -ne 0) { throw 'Actor resource extraction failed' }
& "$projectRoot\build.ps1"
if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
& python "$PSScriptRoot\validate_sfx.py"
if ($LASTEXITCODE -ne 0) { throw 'Native29 sound effects differ from SMS' }
& python "$PSScriptRoot\validate_sfx_priority.py"
if ($LASTEXITCODE -ne 0) { throw 'Native effect/music arbitration differs from SMS' }
& python "$PSScriptRoot\validate_sfx_hooks.py"
if ($LASTEXITCODE -ne 0) { throw 'Gameplay buttons do not start original sound effects' }
$smsBoot = @('200:220:0','920:935:0')
$mdBoot = @('920:935:0')
Invoke-Capture $smsRom 'sms' 1000 '600,800,900,950,1000' @('200:220:0')
Invoke-Capture $mdRom 'md' 800 '30,120,300,450,650,700,750,800' @()
Invoke-Capture $smsRom 'sms-menu' 1100 '900,1000,1100' $smsBoot
Invoke-Capture $mdRom 'md-menu' 1100 '900,1000,1100' $mdBoot
Invoke-Capture $smsRom 'sms-new' 1300 '1000,1150,1300' ($smsBoot + @('1050:1065:0'))
Invoke-Capture $mdRom 'md-new' 1300 '1000,1150,1300' ($mdBoot + @('1050:1065:0'))
$edits = @('1050:1065:0','1200:1204:8','1240:1244:7','1280:1284:8','1320:1324:0')
Invoke-Capture $smsRom 'sms-edit' 1450 '1450' ($smsBoot + $edits)
Invoke-Capture $mdRom 'md-edit' 1450 '1450' ($mdBoot + $edits)
$finishName = @('1050:1065:0','1200:1204:8','1280:1340:5','1360:1420:7','1450:1460:8')
Invoke-Capture $smsRom 'sms-dialogue' 2000 '1700,2000' ($smsBoot + $finishName)
Invoke-Capture $mdRom 'md-opening' 2016 '1700,2000,2004,2008,2012,2016' ($mdBoot + $finishName)
$worldInputs = $finishName + @('2200:2210:8','2400:2410:8')
Invoke-Capture $smsRom 'sms-world-check' 2800 '2000,2300,2500,2800' ($smsBoot + $worldInputs)
Invoke-Capture $mdRom 'md-world' 2800 '2008,2300,2500,2800' ($mdBoot + $worldInputs)
& python "$PSScriptRoot\extract_world.py"
if ($LASTEXITCODE -ne 0) { throw 'World reconstruction failed' }
$movementInputs = $worldInputs + @('2600:2620:7','2650:2690:4','2720:2760:6','2790:2830:5','2855:2940:4','2950:2970:5')
$movementFrames = (2600..2970) -join ','
Invoke-Capture $smsRom 'sms-movement' 2970 $movementFrames ($smsBoot + $movementInputs)
Invoke-Capture $mdRom 'md-movement' 2970 $movementFrames ($mdBoot + $movementInputs)
& python "$PSScriptRoot\movement_reference.py"
if ($LASTEXITCODE -ne 0) { throw 'Movement reference differs from SMS' }
& python "$PSScriptRoot\validate_movement.py"
if ($LASTEXITCODE -ne 0) { throw 'Native movement differs from SMS' }
$transitionInputs = $worldInputs + @('2600:2649:6','2700:2714:4','2750:2900:6','3000:3100:7')
$transitionFrames = ((2765..2820)+(3070..3130)+2900) -join ','
Invoke-Capture $smsRom 'sms-transition-detail' 3130 $transitionFrames ($smsBoot + $transitionInputs)
Invoke-Capture $mdRom 'md-transition' 3130 $transitionFrames ($mdBoot + $transitionInputs)
& python "$PSScriptRoot\validate_transition.py"
if ($LASTEXITCODE -ne 0) { throw 'Native room transition differs from SMS' }
$verticalInputs = $worldInputs + @('2600:2649:6','2700:2714:4','2750:2900:6','3000:3060:5')
$verticalFrames = (3000..3160) -join ','
Invoke-Capture $smsRom 'sms-vertical-check' 3160 $verticalFrames ($smsBoot + $verticalInputs)
Invoke-Capture $mdRom 'md-vertical' 3160 $verticalFrames ($mdBoot + $verticalInputs)
& python "$PSScriptRoot\validate_vertical.py"
if ($LASTEXITCODE -ne 0) { throw 'Vertical scrolling milestone regression failed' }
& python "$PSScriptRoot\actor_reference.py"
if ($LASTEXITCODE -ne 0) { throw 'Room actor loading reference differs from SMS' }
& python "$PSScriptRoot\validate_actors.py"
if ($LASTEXITCODE -ne 0) { throw 'Native room actor loading differs from SMS' }
& python "$PSScriptRoot\sprite_reference.py"
if ($LASTEXITCODE -ne 0) { throw 'Actor descriptor reference differs from SMS' }
& python "$PSScriptRoot\validate_actor_sprites.py"
if ($LASTEXITCODE -ne 0) { throw 'Native actor renderer differs from SMS in isolated test' }
& python "$PSScriptRoot\validate_actor_tick.py"
if ($LASTEXITCODE -ne 0) { throw 'Native actor counters differ from SMS in isolated test' }
& python "$PSScriptRoot\actor_ai_reference.py"
if ($LASTEXITCODE -ne 0) { throw 'Ground actor reference differs from SMS' }
& python "$PSScriptRoot\validate_actor_ai.py"
if ($LASTEXITCODE -ne 0) { throw 'Native ground actor behavior differs in isolated test' }
& python "$PSScriptRoot\validate_mobile_actors.py"
if ($LASTEXITCODE -ne 0) { throw 'Native mobile actor/projectile/terrain behavior differs in isolated test' }
& python "$PSScriptRoot\validate_flying_actors.py"
if ($LASTEXITCODE -ne 0) { throw 'Native flying arithmetic or aimed projectiles differ from SMS' }
& python "$PSScriptRoot\validate_emerging_actors.py"
if ($LASTEXITCODE -ne 0) { throw 'Native resting/emerging enemies differ from SMS' }
& python "$PSScriptRoot\validate_fixed_shooter.py"
if ($LASTEXITCODE -ne 0) { throw 'Native fixed placements or hidden shooter differ from SMS' }
& python "$PSScriptRoot\validate_fixed_rooms.py"
if ($LASTEXITCODE -ne 0) { throw 'Fixed emitters absent after cold checkpoint load' }
& python "$PSScriptRoot\validate_jumping_actors.py"
if ($LASTEXITCODE -ne 0) { throw 'Native jumping arithmetic or adjacent shadow differs from SMS' }
& python "$PSScriptRoot\validate_jumping_rooms.py"
if ($LASTEXITCODE -ne 0) { throw 'Jumping bodies or attached shadows absent after cold checkpoint load' }
& python "$PSScriptRoot\validate_water_jump.py"
if ($LASTEXITCODE -ne 0) { throw 'Native water emergence/leaping differs from SMS' }
& python "$PSScriptRoot\validate_water_rooms.py"
if ($LASTEXITCODE -ne 0) { throw 'Water actors absent or inactive after cold checkpoint load' }
& python "$PSScriptRoot\validate_trap_walker.py"
if ($LASTEXITCODE -ne 0) { throw 'Hidden trap placement, terrain or projectile16 differs from SMS' }
& python "$PSScriptRoot\validate_trap_room.py"
if ($LASTEXITCODE -ne 0) { throw 'Hidden trap does not activate through real movement after checkpoint load' }
& python "$PSScriptRoot\validate_burst_walkers.py"
if ($LASTEXITCODE -ne 0) { throw 'Burst walker states or projectile19/1E motion differs from SMS' }
& python "$PSScriptRoot\validate_burst_pool.py"
if ($LASTEXITCODE -ne 0) { throw 'Burst transient pool allocation differs from SMS' }
& python "$PSScriptRoot\validate_burst_rooms.py"
if ($LASTEXITCODE -ne 0) { throw 'Burst walkers or their shots absent after checkpoint load' }
& python "$PSScriptRoot\validate_actor_spawn.py"
if ($LASTEXITCODE -ne 0) { throw 'Native ground actor spawning contract differs' }
if (!(Test-Path -LiteralPath "$projectRoot\validation\sms-ranged-observe\capture.json")) {
    Invoke-Capture $smsRom 'sms-ranged-observe' 4400 '3680,3690,3700,3710,3720,3730,3740,3750' ($smsBoot + $verticalInputs)
}
& python "$PSScriptRoot\validate_ranged.py"
if ($LASTEXITCODE -ne 0) { throw 'Native ranged/projectile logic differs in isolated test' }
& python "$PSScriptRoot\validate_shield.py"
if ($LASTEXITCODE -ne 0) { throw 'Native shield reflection differs from SMS' }
& python "$PSScriptRoot\validate_damage.py"
if ($LASTEXITCODE -ne 0) { throw 'Native hero damage differs from SMS' }
& python "$PSScriptRoot\validate_attack.py"
if ($LASTEXITCODE -ne 0) { throw 'Native attack poses regression failed' }
& python "$PSScriptRoot\validate_attack_motion.py"
if ($LASTEXITCODE -ne 0) { throw 'Native moving attack regression failed' }
& python "$PSScriptRoot\validate_enemy_damage.py"
if ($LASTEXITCODE -ne 0) { throw 'Native enemy damage contract regression failed' }
& python "$PSScriptRoot\validate_drop.py"
if ($LASTEXITCODE -ne 0) { throw 'Native drop allocation regression failed' }
& python "$PSScriptRoot\validate_particles.py"
if ($LASTEXITCODE -ne 0) { throw 'Native explosion regression failed' }
& python "$PSScriptRoot\validate_loot.py"
if ($LASTEXITCODE -ne 0) { throw 'Native loot regression failed' }
& python "$PSScriptRoot\validate_death.py"
if ($LASTEXITCODE -ne 0) { throw 'Native death/menu milestone differs from SMS' }
& python "$PSScriptRoot\validate_resume.py"
if ($LASTEXITCODE -ne 0) { throw 'Native checkpoint fade/reveal regression failed' }
& python "$PSScriptRoot\validate_resume_capacity.py"
if ($LASTEXITCODE -ne 0) { throw 'Enlarged capacity Continue regression failed' }
& python "$PSScriptRoot\validate_heal.py"
if ($LASTEXITCODE -ne 0) { throw 'Native heal regression failed' }
& python "$PSScriptRoot\validate_potion.py"
if ($LASTEXITCODE -ne 0) { throw 'Native potion regression failed' }
& python "$PSScriptRoot\validate_healing_route.py"
if ($LASTEXITCODE -ne 0) { throw 'Normal healing item route regression failed' }
& python "$PSScriptRoot\validate_inventory.py"
if ($LASTEXITCODE -ne 0) { throw 'Native inventory regression failed' }
if (!$SkipFire) {
& python "$PSScriptRoot\validate_fire.py"
if ($LASTEXITCODE -ne 0) { throw 'Native fire projectile regression failed' }
& python "$PSScriptRoot\validate_fire_route.py"
if ($LASTEXITCODE -ne 0) { throw 'Normal fire inventory route regression failed' }
& python "$PSScriptRoot\validate_fire_damage.py"
if ($LASTEXITCODE -ne 0) { throw 'Native fire damage regression failed' }
}
& python "$PSScriptRoot\validate_save.py"
if ($LASTEXITCODE -ne 0) { throw 'Native save/Continue regression failed' }
& python "$PSScriptRoot\validate_all_save_points.py"
if ($LASTEXITCODE -ne 0) { throw 'All unconditional save points regression failed' }
& python "$PSScriptRoot\validate_mobile_room52.py"
if ($LASTEXITCODE -ne 0) { throw 'Room52 enemy contact/death observation failed' }
& python "$PSScriptRoot\validate_merchant.py"
if ($LASTEXITCODE -ne 0) { throw 'First-village merchant regression failed' }
& python "$PSScriptRoot\validate_all_merchants.py"
if ($LASTEXITCODE -ne 0) { throw 'All merchant variants regression failed' }
& python "$PSScriptRoot\validate_healer.py"
if ($LASTEXITCODE -ne 0) { throw 'First-village healer regression failed' }
& python "$PSScriptRoot\validate_healer_natural.py"
if ($LASTEXITCODE -ne 0) { throw 'Natural healer route regression failed' }
& python "$PSScriptRoot\validate_paid_healer.py"
if ($LASTEXITCODE -ne 0) { throw 'Paid/free inns regression failed' }
& python "$PSScriptRoot\validate_expanded_doors.py"
if ($LASTEXITCODE -ne 0) { throw 'Expanded direct doors regression failed' }
foreach ($livingMask in @('0x80','0x01','0x55','0xaa')) {
    & python "$PSScriptRoot\validate_expanded_doors.py" --limit 1 --mask $livingMask --no-exit
    if ($LASTEXITCODE -ne 0) { throw "Living actor mask regression failed: $livingMask" }
}
& python "$PSScriptRoot\audit_door_masks.py"
if ($LASTEXITCODE -ne 0) { throw 'Persisted door mask audit failed' }
& python "$PSScriptRoot\validate.py"
if ($LASTEXITCODE -ne 0) { throw 'Validation failed' }
