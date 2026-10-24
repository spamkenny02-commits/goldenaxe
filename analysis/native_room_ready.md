# Chargement natif jusqu'au heros, aux scripts et a la musique

Travail du 24 octobre 2026, apres v0275. La chaine experimentale arrive
desormais a1FA7, apres l'initialisation du heros, les scripts de salle et
la selection musicale.1FA7 precede encore la revelation de l'ecran et le
fondu : la ROM jouable reste v0275, avec son generateur provisoire.

`source_hero_initialize` porte2C63, la selection des pointeurs d'animation,
l'effacement des objets auxiliaires, les forces d'attaque/defense, le cache
de collision3x8 octets et les regles de terrain/equipement. Les ecritures
visibles par les IRQ, notamment C042/C043, gardent leurs frontieres source.

`source_room_tail` porte5B20 et1CAF : pointeurs de scripts, coordonnee et
direction, drapeau de salle vide, choix de musique exterieur/maison/donjon,
drapeau de boss et suppression d'une commande musicale deja active. Il
termine avec l'etat de jeu12 et le prochain opcode de1FA7 deja precharge.

`source_room_load_class0_ready` compose toutes les etapes depuis16D0 sur une
seule horloge. Une memoire de corps8192 octets partage les vraies vues de
carte, metatuiles, terrain, acteurs, equipement et scripts. Les pages du
contexte IRQ compact et ses400 octets audio restent les vues actives au
travers de `source_room_memory`. Aucun etat de heros, collision, R, graine ou
musique observe en cours de chargement n'est injecte dans cette chaine.

Le suivi optionnel de cette memoire enregistre maintenant C065/C066, l'en-tete
DCA0 et les metadonnees C06E aux instructions qui les ecrivent. Les anciens
appels sans memoire complete restent disponibles. Le chemin exige toujours
un vrai changement de banque graphique et le chargeur de carte conserve
sa portee precedente : six destinations exterieures, bit0 actif et C0AC nul.

## Verification et cout natif

- 13 150 cas source/C d'initialisation du heros en NTSC/PAL : trois classes,
 six anciens terrains,17 selections, quatre directions, limites de niveaux,
 malediction, tuiles, attributs et coordonnees.475 octets touches/preserves,
 temps, M1 et R correspondent. Dimensions independantes, pas un produit
 cartesien complet ; IRQ source coupees dans ce banc unitaire.
- 288 cas source/C de scripts et musique : trois classes, morceaux ordinaires
 et speciaux, boss, salle vide, commande precedente et direction. Etats,
 temps, M1 et R correspondent avec IRQ source coupees.
- 24 chargements complets controles de passages payants correspondent au Z80
 sur888 points, avec musique et IRQ actives, depuis une seule entree16D0.
 Les475 octets d'entree et de sortie du heros,1280 octets de carte de collision,
 les champs scripts/musique, acteurs, historique, masques et pixels d'ennemis
 sont verifies contre les observations originales. Les72 tirages sont calcules
 par l'horloge native, sans valeurs intermediaires observees.
- La chaine complete compilee en68000 execute les24 vecteurs dans les deux
 regions :48 executions sans divergence. Les IRQ physiques MD sont coupees,
 les IRQ SMS et le lecteur musical restent actifs dans l'horloge virtuelle.
 Les autres octets de corps/miroir comparent a la parite hote, sans revendication
 d'identite complete de la RAM SMS, notamment de sa pile.

La conversion de palette regroupe maintenant une ligne complete lorsque le
planificateur prouve l'absence d'IRQ dans les2290T/351M1 correspondants. Les
ecritures sont terminees avant la prochaine operation d'horloge. Pres d'une
interruption, le chemin par instruction conserve les effets partiels. Les
156 cas couvrant80 types et les96 conversions/scratch precedents repassent,
ainsi que l'ancienne chaine jusqu'a18E1 sans la memoire complete optionnelle.

Sur le meme banc68000, avec exactement les memes vecteurs et controles, le
total passe de6895 a2626 images en NTSC et de5772 a2199 en PAL, environ62%
de moins. Seul `source_actor_graphics.c` change entre ces deux mesures. Le
banc inclut preparation, comparaisons et initialisation SGDK : ce gain ne
mesure ni les FPS du jeu ni le respect des echeances physiques du rendu.

Les captures ont une preparation controlee, distincte de la campagne naturelle.
La revelation/fondu a partir de1FA7, le rendu physique, le budget CPU aux
echeances, l'entree d'horloge depuis le boot, les autres chemins de chargement,
les formes d'onde et la campagne complete restent ouverts. Le traitement de
la prochaine IRQ complete devra aussi recevoir le vrai compte de tuiles du
bitmap du heros avant de consommer C042.

Rapports : [heros](native_hero_initialize_report.json),
[scripts/musique](native_room_tail_report.json),
[chaine](native_room_ready_report.json),
[68000](native_room_ready_68k_report.json),
[cout du banc](native_room_ready_performance_report.json).
