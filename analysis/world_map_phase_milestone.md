# Phase graphique puis carte depuis une entree (2026-10-16)

Le modele190B est maintenant enchaine au modele graphique16D0, sans
capture intermediaire utilisee comme entree. La phase CPU/VDP,336 octets
RAM et400 octets audio initiaux viennent uniquement de16D0. La salle de
destination et son bit persistant0=1 sont des entrees de contexte : le
banc impose ce bit avant de lancer les passages payants.

Le decodeur RAM0C00,la recherche des metadonnees,la selection du bit
persistant,les correctifs de cellules1B0E,le correctif de terrain1A30,
le retour de salle speciale et la remise a zero de la file sont decrits
instruction par instruction. Le modele produit la phase et le lecteur
audio jusqu'au retour a24BC. La fileDD00 et son pointeurC034 sont
reconstruits pour les points de controle ; les mises a jour des tuiles
laissent leurs octets residuels dans la file comme l'original.

La salle1A utilise les metadonnees par defaut FF/FF/00. Le correctif lit
alors le motif0 (XOR A a1AB4) et copie ses deux lignes aDDBC etDDFC, a
l'interieur de la zone de file. Ces huit octets sont calcules par le
decodeur de metatuiles depuis la ROM. Une premiere interpretation visait
le motif255 ; la capture diagnostiqueD0F8 ajoutee pour l'investigation
reste archivee mais n'est pas une entree du modele ni de sa validation.
Ce comportement original n'est pas masque par une exclusion de RAM.

La selection1951/195E lit son masque a ROM004D viaLD DE,004D puisLD A,(DE).
Une ancienne annotation indiquaitC04D ; elle est corrigee dans l'outil
de cout actuel. Il s'agit d'une correction documentaire, sans changement
du calcul de cout existant ni des archives historiques.

Les24 parcours controles (six passages payants,deux masques d'acteurs,
PAL/NTSC) passent les neuf points de controle, dont192A apres decodage,
192D apres metadonnees/persistance et24BC apres retour. Chaque point
compare duree,phase,registreVDP/latchIRQ,331 octets RAM et400 octets audio.
Tous les horairesIRQ du segment sont calcules et correspondent.
Le cout horsIRQ de la carte correspond au modele de cout deja verifie.
Les traces originales completes restent identiques aux referencesv0179.

Limites : classe0 changee,affichage coupe,C0AC0,C041!=5 etbit persistant0
actif pour les salles observees. Les octets de carte/metatuiles/VRAM/SRAM
hors de la capture ne sont pas reconstruits par ce modele de phase.
C01B etC020..23 ne sont pas compares. Pas de prediction du HUD,de l'attente
qui le suit,des acteurs ni de l'historique/hasard a ce stade. Autres
classes graphiques,IRQ imbriquees,HINT,NMI/reset restent hors portee.
La progression naturelle complete etle materiel reel ne sont pas valides.

ROM v0183 et sources natives inchangees ; l'integration des timings est
encore a faire. L'archive locale world-map-phase-research-v0183 contient
outils,captures,coeur etrapports avec un manifesteSHA-256.

Reproduire (captures locales requises) :

- python tools/build_world_map_phase_core.py
- Capturer les six routes et masques00/FF via profile_paid_passage_loader_phases.main,
  repertoire world-map-phase/TT-MM,coeur genesis_plus_gx_worldmapphaseextra_libretro.dll,
  capture_music=True.
- python tools/validate_world_map_phase.py
- python tools/archive_world_map_phase_research.py
