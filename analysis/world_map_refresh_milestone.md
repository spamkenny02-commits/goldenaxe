# Registre R jusqu'au chargement de la carte (2026-10-16)

Le modele enchaine maintenant 16D0..24BC depuis un seul etat d'entree :
routine graphique complete puis carte 190B, metadonnees, correctifs
persistants, terrain et remise a zero de la file de tuiles. Les entrees
sont R/raster/RAM/audio a 16D0, la salle et son bit de sauvegarde 0 actif.
Les valeurs intermediaires de R et les interruptions ne sont pas fournies.

Les 24 parcours controles passent neuf points chacun, soit 216 comparaisons
de lectures M1, registre R, phase video, duree, 331 octets RAM et 400 octets
audio. Les comptes hors interruptions vont de 139 479 a 140 109 selon la
carte. Les IRQ ajoutees consomment 6 250 lectures pour 17 interruptions
en NTSC et 6 522 pour 15 en PAL. Leurs offsets sont predites et verifies.
Les enregistrements precedents restent identiques octet par octet, ainsi
que les traces SMS completes par rapport aux references v0179.

Le plan distingue les instructions ordinaires 2A/22 LD HL,(nn)/LD(nn),HL
de 16T des LDI de meme duree. Les copies de lignes de tuiles restent a
deux lectures par LDI, tandis que les acces aux pointeurs de salle/file
en consomment une. SBC HL,DE (ED52) est explicitement compte a deux
lectures. Les metadonnees par defaut FF/FF/00 continuent de copier le motif
0 vers DDBC/DDFC ; ces octets restent compares dans les snapshots.

Le chemin temporel par defaut passe de nouveau ses 24 scenarios, et la
regression du calcul R graphique precedent passe aussi. Un coeur distinct
observe les neuf points ; le fichier C de travail est restaure apres
compilation. Outils, captures, references et coeur sont archives localement
avec manifeste SHA-256. Aucun changement de la ROM v0183 ni des sources
natives.

Limites : six salles de passages payants, classe 0 avec changement de
banque, affichage desactive, C0AC=0, C041!=5 et bit persistant 0 actif.
C01B et C020..23 restent exclus des comparaisons. Le contenu decode hors
snapshots, VRAM/palette/SRAM et autres classes ne sont pas prouves ici.
La convention locale GPG d'acquittement est conservee sans preuve sur
materiel reel. HUD, attentes VBlank, acteurs et historique doivent encore
propager R avant integration du hasard et des delais au portage natif.
Les commandes audio non couvertes et la partie complete restent ouvertes.

Reproduire :

- `python tools/build_world_map_refresh_core.py`
- Capturer les six routes et masques 00/FF via
  `profile_paid_passage_loader_phases.main`, repertoire
  `world-map-refresh/TT-MM`, coeur
  `genesis_plus_gx_worldmaprefresh_libretro.dll`, `capture_music=True`.
- `python tools/validate_world_map_refresh.py`
- `python tools/validate_world_map_phase.py`
- `python tools/validate_graphics_load_refresh.py`
- `python tools/archive_world_map_refresh_research.py`
