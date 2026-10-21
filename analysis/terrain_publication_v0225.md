# V225 : publication du terrain au VBlank

Les routines SMS1B0E et49EA modifient la carte logicielle, puis ajoutent un
rectangle2x2 a la file de l'interruption. La MD transfere maintenant ces
changements au VBlank, avant le lecteur PSG et les publications de la scene.
La v224 ecrivait directement dans le VDP depuis la simulation.

Le cas controle de l'ennemi2B reproduit le defaut en PAL et NTSC : la v224
modifie la VRAM dans la meme image que la carte logicielle. La v225 respecte
le delai d'une image observe sur SMS. Les quatre mots finaux sont identiques
apres conversion des attributs ; les pixels opaques du carre16x16 restent
coherents avec la VRAM pendant les266 images controlees. La v224 ne presente
pas de dechirure dans ce cas : le defaut demontre est la publication anticipee.

Le code68000 conserve une copie des lignes touchees et les fusionne pour le
DMA. Une garde empeche l'interruption de lire cette copie pendant sa preparation.
Le tampon est independant de la sauvegarde du dialogue et des cartes modifiables
par les transitions. Il utilise1280 octets, avec quelques octets de controle.
La BSS termine aE43C :7108 octets restent au-dessus, sans constituer une mesure
exhaustive de l'utilisation de la pile sur toute la campagne.

Les124 cas de declenchement/repetition d'interrupteurs PAL/NTSC et les20 cas
de terrain du second sort passent. Leurs limites restent celles des fixtures
controlees : etats logiciels et cartes stables, pas une fidelite graphique
et sonore complete pour toutes les sequences intermediaires.

Un parcours NTSC depuis une nouvelle partie, sans injection RAM, obtient la
cle de1E5, ouvre la porte de1B5, active l'interrupteur UP de194, puis obtient
la seconde cle en193. Il couvre neuf salles de combat et dix salles distinctes.
SMS et MD finissent sans mort, avec les memes256 octets de drapeaux persistants
et1280 octets de carte. Chaque flux de boutons se rejoue dans un processus
neuf, avec RAM finale et PNG integralement identiques a sa propre execution.
Les rencontres, durees et PV different : cela ne prouve pas le hasard exact.

Le boss, le joyau, le reste du premier donjon et la campagne restent a faire.
Les essais de pilote incomplets ou errones sont archives comme diagnostics,
sans etre comptabilises comme reussites. Un ancien trajet fixe de v223 ne
rejoignait plus le donjon en v225 ; le prefixe md-v0225 a ete recalcule par
le pilote de marche, puis rejoue avec des boutons fixes avant les combats.

Reproduction :

- `./build.ps1`
- `python tools/validate_cell_publication.py` (puis `--pal`)
- `python tools/validate_cell_publication.py --baseline-v0224` (puis `--pal`)
- `python tools/validate_puzzles_gameplay.py` (puis `--pal`)
- `python tools/validate_second_spell_terrain.py`
- `python tools/verify_natural_dungeon_progress.py --verify-existing`
- `python tools/summarize_terrain_publication_release.py`

Les captures des parcours naturels contiennent les boutons et les rapports ;
les fichiers binaires de diagnostic sont recuperables dans l'archive locale
terrain-publication-v0225 apres verification SHA/gzip.
