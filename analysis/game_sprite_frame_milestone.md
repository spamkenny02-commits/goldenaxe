# Raccordement natif sprites, attente et interruption du jeu

La chaine native execute maintenant0938 (construction SAT), CALL0B95
(sauvegarde/attente), l'interruption originale du jeu et la restauration
jusqu'au retour de l'appelant. `source_game_frame.c` compose les traductions
existantes sans interpreter les opcodes Z80. `source_game_irq.c` relie la RAM
C000..DFFF de8192 octets au contexte compact336 de l'IRQ et a son audioDE00.

## Comportement source retrouve

L'interruption complete ne preserve pas tous les registres de la construction
et laisse la banque6 active. Elle est autorisee seulement apres la sauvegarde
0B95 viaC02E. Pendant0938, le chemin audio seul preserve registres et banque.
Le nouveau contexte refuse une interruption complete pendant la construction;
la restauration0BB4 reinstalle la banque sauvegardee par l'appelant.

Le vecteur003F ecrit aussi le statut VDP dansC01B. Une constante128 etait
incorrecte: les captures donnent159 (208IRQ) ou223 (9IRQ) par region.
Les bits inutilises du mode4 sont lus a1; le depassement de sprites peut
varier. Un fournisseur explicite donne ce statut a chaqueIRQ. Ce banc utilise
les entrees materielles observees; il ne predit pas encore le statut source.

La table192 octets est copiee dans un paquet possede par le contexte avant
l'audio. Ses deux dates de premier OUTI termine sont entree0137+234T pour
Y64 et+1315T pourX/tuiles128. Les octets suivants arrivent chaque16T.
Le consommateur doit copier le paquet avant le retour, car la prochaineIRQ
le remplace. Un echec peut survenir apres une publication video: la session
est alors fatale, sans rejeu de l'interruption.

## Verification

Le [banc source/hote](game_sprite_frame_report.json) conserve les routines
originales0938,0B95,vecteur/IRQ et banques4/6/12 octet par octet. Un appelant
RAM fournit133 cas: captures d'acteurs et matrices de tri/capacite/visibilite.
Les requetes de tuiles, HUD et file video sont vides; le test varie les
phases raster et l'attente de palette. L'affichage source est coupe.

En PAL et NTSC,133 cas par region passent sur hote puis sur le
[68000 reel du coeur d'emulation](game_sprite_frame_68k_report.json):

- 217IRQ par region, dont84 audio seules et133 completes;
- 25536 octets SAT et592 octets PSG, toutes valeurs et dates exactes;
- 4 points par cas:0938,0B95,0BB3 et retour appelant;
- PC, temps master, raster,R/IFF et930 octets RAM compares a ces points;
- chaque entreeIRQ compare aussi temps/raster/R avant fourniture du statut;
- execution sans trace identique sur8192 octets finaux et compteurs d'horloge;
- 5 controles de refus/etat fatal/propriete du paquet par region, hote et68000.

Le [controle des donnees liees](game_sprite_frame_assets_report.json) relit
les vrais octets de la ROM68000 et les compare integralement aux captures,
aux banques originales et aux donnees d'entree. Apres nettoyage il peut
recuperer ces fichiers dans les objets gzip verifies de l'archive.

## Limites et suite

Le statut materiel et la RAM a l'entree0938 sont fournis, pas reconstruits
depuis le boot. Les ecritures de pile Z80 ne sont pas comparees. Le consommateur
video recoit ici la SAT seule; les autres etapes IRQ gardent leurs effets RAM
et leur cout source mais leurs sorties VDP restent a raccorder. Ce banc ne
prouve ni livraison MD a l'echeance, ni waveform, ni execution sur console.

La prochaine etape relie ce paquet IRQ au rendu SMS8 natif et a sa publication
VDP, puis aux motifs et a la progression autonome des acteurs. La ROM jouable
restev0203/1Mio. La ROM de test est un noyau de diagnostic, pas une v0208.
Les207 ROMs numerotees et les sources sont conservees.

Les preuves sont figees dans `game-sprite-frame-v0203` avant nettoyage.

Archive finalisee:180 references compressees;33770209 octets generes retires,
28764045 octets nets liberes (environ27,4Mio). Lecture gzip/SHA complete et
reconstruction des donnees de la ROM68000 identique apres nettoyage.
