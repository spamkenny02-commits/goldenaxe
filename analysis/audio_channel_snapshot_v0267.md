# v0267 : cout audio et attente du sort

Le cas controle du sort niveau2 avec acteurs finit a la meme image que la
SMS en NTSC (3064), contre3082 en v0264. Les autres cas restent1..3 images
en avance ; cela ne prouve pas une synchronisation physique complete.

## Changements

Le canal audio conserve une sauvegarde48 octets lorsque son compteur ne va
pas lire une nouvelle sequence. Les routines tone/pitch/envelope ne modifient
alors que ce canal. Lorsque le compteur vaut1, la sauvegarde400 octets reste
necessaire : une sequence peut modifier les autres canaux. Sur rejet, le
canal est restaure et les sorties precedemment emises sont conservees comme
avant. Le lecteur rapide sans restauration n'est pas active en production.

Dans le sort, les attentes audio seules suivent le compteur absolu vtimer.
L'appel SGDK ON_VBLANK_START pouvait laisser passer une interruption de plus
lorsque le compteur et le drapeau VBlank etaient echantillonnes autour de son
debut. La publication video reste dans l'IRQ, avec traitement SGDK immediat
apres publication. Aucune publication directe en affichage actif n'est ajoutee.

Le comparateur inclut maintenant le vrai ecran vide initial quand la MD est
encore en phase preparation1 : il verifie les1280 octets VRAM et la SAT,
sans inclure l'ancienne salle. Les traces precedentes l'excluaient selon la
vitesse du processeur. L'essai266 avec une attente finale supplementaire
exposait une etape supplementaire et a ete rejete.265/266 sont conserves
comme essais ;267 est la version recommandee.

## Verification

- 25644 vecteurs source et6000 mutations compares aux modules v0264 : les400
 octets d'etat, DE, T/M1, commandes PSG et statut sont identiques. Les echecs
 du lecteur en flux sont compares aussi, y compris le canal restaure.
- 2840 appels directs tone/noise : tous les offsets acceptes, limites et
 compteurs0/1/2/255.333 refus identiques.
- Les25644 vecteurs source sont executes dans huit cartouches68000 separees,
 en PAL et NTSC :51288 cas sans erreur pour les400 octets, DE et couts source.
 Les empreintes des modules compiles correspondent a ceux de267. Ces petits
 programmes ne sont pas la ROM jouable et ne prouvent pas les formes d'onde.
- Douze scenarios du sort,626 etats ordonnes de carte et SAT identiques,
 neuf retours sans difference de pixels normalises (sept a horloge logique
 egale, deux apres inventaire a la meme image physique).
- Douze images naturelles de jeu : composition VRAM/CRAM coherente, aucun
 code audio non traite ; ce controle ne prouve pas une cadence SMS complete.
- Le lecteur musical passe de21907.75 a14733.425 cycles68k moyens sur80 IRQ
 du scenario charge observe, environ33% de reduction. Observation passive
 des entrees/retours sur les binaires264 et267 ; pas une mesure sur console.

Les couts source du sort restent verifies sur232 corps de carte et232 scenes,
plus341 variantes acceptees et171 refus communs au compteur de reference.
La prediction de l'IRQ suivante, le raster initial, la progression naturelle,
le RNG, les formes d'onde et la campagne complete restent a terminer.

Rapport : [audio_channel_snapshot_release_v0267_report.json](audio_channel_snapshot_release_v0267_report.json).
