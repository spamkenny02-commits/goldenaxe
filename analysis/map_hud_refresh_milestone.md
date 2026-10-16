# Registre R jusqu'a la sortie du HUD (2026-10-16)

Le calcul compose maintenant 16D0..24BF depuis un seul etat d'entree :
graphismes, carte, preparation du tilemap, HUD, attente VBlank, restauration
des registres, transfert video sous DI/EI et palette. R/raster/RAM/audio,
les 16 octets de contexte HUD et la salle sont fournis uniquement a 16D0.
Les valeurs intermediaires de R, de phase et d'interruption sont calculees.

Les 24 scenarios passent les 16 points de controle chacun, soit 384
comparaisons M1/R, phase, duree, 331 octets RAM et 400 octets audio. Ils
comprennent chacun une interruption complete pendant l'attente du HUD.
Le nombre de lectures hors IRQ varie avec la salle et les tours d'attente :
177 032..177 185 en NTSC, 180 853..181 006 en PAL. Les interruptions
ajoutent 9 030 lectures pour 22 IRQ en NTSC, 9 402 pour 19 en PAL.
Les anciens snapshots et les traces completes SMS v0179 sont inchanges.

Les noeuds prefixes sont explicites : SRL/BIT/SET du tilemap, SRL/NEG de
la jauge partielle, BIT 7,(HL) des gemmes, PUSH/POP IX et INC IY. Les
instructions LD(nn),HL de palette restent ordinaires malgre leurs 16T,
tandis que les LDI/OUTI consomment deux lectures. Le calcul de l'attente
VBlank est raccorde a R produit par le HUD, puis le resultat alimente la
restauration et le transfert. Aucune valeur R mesuree intermediaire n'est
utilisee pour ce raccordement.

Le banc de jauges reutilise la ROM synthetique precedente et execute les
routines HUD originales. Ses 18 042 cas (9 021 par region) correspondent
pour duree, M1 et R : toutes les valeurs vie/magie pour les capacites
valides 8..128, bornes de capacite 0/7/129/255, tous les montants d'or et
les 512 masques de gemmes. Les dimensions varient independamment, pas
selon leur produit cartesien. Les IRQ sont desactivees dans ce banc ;
leur composition est couverte par les parcours et le banc d'attente.

Le chemin temporel par defaut garde ses resultats sur les 24 parcours.
Les captures M1 du coeur d'attente sont reutilisees sans nouvelle mesure
intrusive. Outils, fixtures, captures, references et coeur sont archives
localement avec manifeste SHA-256. ROM v0183 et sources natives inchangees.

Limites : parcours classe 0 avec changement de banque, affichage desactive,
C0AC=0, C041!=5, bit persistant 0 actif. Leur contexte HUD est vie24/max24,
magie24/max24, or10, aucune gemme, aucune malediction et armure1. Les autres
jauges sont couvertes par le banc isole ; les branches de malediction ne
sont pas prouvees par ces parcours. C01B et C020..23 sont exclus des
comparaisons et le contenu VRAM/palette/SRAM hors snapshots reste a verifier.
La convention locale GPG d'acquittement IM1 n'est pas une preuve materielle.
Acteurs, historique, commandes audio non couvertes, integration native du
hasard/delais et partie complete restent ouverts.

Reproduire :

- Captures existantes `wait-refresh/TT-MM` avec le coeur
  `genesis_plus_gx_waitrefresh_libretro.dll` et `capture_music=True`.
- `python tools/validate_map_hud_refresh.py`
- `python tools/validate_hud_refresh_unit.py`
- `python tools/validate_map_hud_phase.py`
- `python tools/archive_map_hud_refresh_research.py`
