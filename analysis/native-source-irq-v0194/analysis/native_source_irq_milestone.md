# Enveloppe d'interruption SMS en C natif

La routine 0137..0226 dispose maintenant d'une traduction dans
`source_irq.c/.h`, compilee pour le 68000. Elle traduit les effets sur
les 336 octets C000..C04F et DD00..DDFF, et les cycles T/lectures M1.
Les transferts video eux-memes restent executes par le moteur SGDK
existant : ce composant prepare l'horloge source, il ne remplace pas
le rendu du jeu et n'est pas encore raccorde a la ROM jouable.

Le chemin audio seul conserve les registres modelises et decremente le
compteur C030. Le chemin video/audio decrit neuf etapes : les deux
transferts SAT, les motifs, le HUD, la palette, les files graphiques,
le mapping audio, le lecteur et les entrees/compteurs. Le cout du lecteur
vient du composant 8000 natif, pas d'un budget audio constant.

L'attente de palette est calculee depuis la phase raster a l'entree de
0137 et les couts des etapes precedentes. Elle utilise le compteur vertical
SMS 192 lignes PAL/NTSC et le seuil E0/F0 selon la compensation. Le nombre
de passages observe dans les captures n'est pas une entree du calcul.
Le nombre de motifs en attente est fourni par le decodeur d'asset ; les
validateurs le lisent dans les donnees ROM d'origine et verifient leur hash.

## Preuves

- 2 880 interruptions controlees historiques : 336 octets, neuf couts T/M1,
  attente de palette et deltas R compares aux captures source conservees.
- 13 749 interruptions video/audio capturees sur six routes de passages
  payants, deux masques et deux regions. Les captures sont identiques aux
  archives historiques. Le lecteur audio natif conserve aussi ses 400
  octets, DE et son cout face aux captures SMS de ces appels.
- 15 360 cas du chemin audio seul : les 256 compteurs C030, cinq valeurs
  de pause, deux compensations et trois phases. Les couts/M1 et le compteur
  sont compares aux executions source. Le caller synthetique 47T/4M1 est
  explicitement remplace par le vecteur 72T/6M1 pour le total d'interruption.
- 704 nouveaux cas executes dans le code SMS intact : motifs avec compteurs
  0/1/2/255, transferts lineaires avec compteurs 0/1/2/255 et banques
  0/4/128/255, rectangles de hauteurs 0/1/2/255 et largeurs
  0/1/127/128/255, puis files mixtes. Les compteurs nuls de boucle valent
  256 et la largeur doublee deborde bien sur huit bits. Les neuf etapes,
  RAM, attentes de palette et R correspondent dans les deux regions.
- Les 32 693 vecteurs sont rejoues dans des cartouches SGDK en code 68000
  PAL/NTSC, avec comparaison des 336 octets, des neuf etapes et du total.
- Douze refus verifies sur hote conservent les 336 octets et annulent la
  sortie : phase/region/entrees invalides, asset non capture, file hors
  fenetre et debordements du cout audio. Trois controles supplementaires
  verifient le passage au reset depuis les instructions originales ; cette
  branche n'est pas revendiquee comme directement comparee au materiel.

## Limites et raccordement restant

Le total comprend les 72T/6M1 du vecteur et le RET final, avec la convention
IM1 du coeur local GPG. Il ne prouve pas l'increment physique de R pendant
l'acquittement. Les captures video se terminent avant l'execution du RET ;
celui-ci est compte depuis l'opcode, comme dans les recherches precedentes.

Le reset expose une demande a l'adresse 009A, avant les compteurs de fin
et le RET. L'execution du reset cible n'est pas traduite dans ce composant.
Les entrees raster, joypad et RAM initiales restent observees. La phase
et R doivent encore etre raccordes a l'ordonnanceur natif et au code
principal ; aucun point d'entree initial n'est suppose connu par ces tests.

Les nouveaux essais de files longues desactivent les interruptions VDP.
Ils prouvent l'etat et le cout du corps, pas l'ordonnancement d'interruptions
imbriquees quand une charge synthetique traverse plusieurs images.
Les valeurs graphiques effectivement transferees, les formes d'onde,
le materiel physique et une partie naturelle complete restent hors scope.

La ROM v0194 et tous les fichiers natifs existants sont inchanges.
Les nouvelles fonctions ne sont pas raccordees a sa boucle d'execution.
Les sources, outils et preuves sont figes dans `native-source-irq-v0194`
avec manifeste SHA-256. Les captures volumineuses restent locales ; les
sources, rapports et documentation sont enregistres dans le Git local.
