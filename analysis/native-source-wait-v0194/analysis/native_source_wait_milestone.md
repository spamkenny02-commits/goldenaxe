# Attente source, horloge et interruptions dynamiques natives

`source_irq_context.c/.h` raccorde le lecteur audio natif 8000 et les
effets/couts de l'interruption video au callback de `source_clock`.
Les couts T/M1 proviennent du RAM/audio courant, sans budget fixe.
Les entrees raster viennent de l'ordonnanceur ; compensation, compteurs,
files et musique evoluent pendant chaque interruption.

`source_wait.c/.h` traduit le prefixe et la boucle 0B95..0BB3. Le point
0BB3 est le debut de restauration, POP AF, et non le RET final.
L'appel rend l'horloge a ce point, apres le fetch de l'opcode suivant.
La restauration du mapping/registres et le RET 0BC5 restent a traduire
dans la continuation. Cette limite correspond exactement aux captures
d'attente conservees ; ce travail ne pretend pas couvrir tout le chargement.

## Optimisation des tours stables

Le premier banc 68000 montrait que l'execution native instruction par
instruction de la boucle d'attente etait couteuse, meme sans ecart logique.
`source_clock_repeat` accumule donc les blocs stables de 29T/3M1 tant
qu'aucune interruption ne peut intervenir. Il s'arrete a ou avant VINT,
et refuse l'acceleration si une interruption est deja en attente, si EI
bloque encore l'acceptation, ou si le premier fetch doit etre traite.
Les instructions proches des evenements gardent leur execution ordinaire.

Cette optimisation preserve le temps SMS, R et les compteurs. Elle evite
de consommer inutilement le CPU 68000 pour une attente source ; elle ne
constitue pas encore une mesure de vitesse de la ROM jouable, qui utilise
toujours sa boucle actuelle. Les fonctions preexistantes de l'horloge
sont conservees ; la nouvelle fonction est ajoutee a leur suite.

## Preuves

- 13 725 attentes de parcours reels : six passages payants, deux masques
  et PAL/NTSC. Les entrees initiales sont capturees ; tout le reste est
  calcule par les composants C natifs. Durations, phase raster, R, M1,
  331 octets RAM, 400 octets audio et instants/types d'IRQ correspondent
  aux anciennes captures source, dont les empreintes sont verifiees.
- 6 156 contextes DI/EI/IRQ latchee reexecutes dans les fixtures SMS
  d'origine et compares directement au code natif : donnees d'entree et
  de retour, polling, durees, R/M1 et acceptations d'interruptions.
  Ils couvrent aussi les chemins audio seul precedant l'interruption complete.
- Les 19 881 vecteurs passent en code 68000 PAL/NTSC, dans dix cartouches
  de test de moins de 4 Mio. Les champs supplementaires non observes dans
  les captures sont controles pour parite avec l'hote, pas declares prouves
  par la SMS.
- Les 13 725 entrees d'IRQ reelles sont aussi comparees aux sidecars source
  0137 : raster et R correspondent exactement. Le point d'observation GPG
  est apres le premier fetch de l'opcode 0137 ; les six fetches du vecteur
  plus ce fetch expliquent la convention +7 du callback natif.
- 11 520 contextes de l'acceleration, dont 320 lots non nuls, correspondent
  a l'execution ordinaire 13T/4T/12T : toutes les combinaisons de latches,
  premiers fetches, limites de repetition et phases au bord de VINT.
- Sept controles sur hote verifient les diagnostics du callback et la
  publication de l'etat/PSG/trace : entrees invalides, audio non traduit,
  reset, IRQ imbriquee, puis succes des deux chemins.

## Limites et travail restant

C01B, statut VDP, et C020..C023, entrees/bords pause/joypad, sont exclus
des comparaisons d'attente, comme dans les recherches source precedentes.
Le banc fournit joy=0. Les comptes de motifs viennent des assets d'origine.
Ces donnees devront etre raccordees au moteur video et aux entrees du jeu.

Le callback refuse explicitement une interruption video qui traverserait
un nouveau VINT avant de finir : son ordonnanceur imbrique reste a faire.
Il expose aussi le reset sans executer sa cible 009A. Les erreurs rendent
le cout invalide, mis a zero, sans inventer un budget de remplacement.
L'audio en flux peut avoir publie les effets de canaux reussis avant une
erreur ulterieure ; le diagnostic impose alors d'arreter cette composition.

Les entrees initiales R/raster/RAM restent observees. La propagation depuis
le debut du chargement, la restauration 0BB3..0BC5, les autres portions
du code principal, puis le raccordement du hasard natif et des attentes
dans la ROM restent a terminer. Les commandes audio non auditees conservent
leurs refus explicites. La convention d'acquittement physique de R, les
formes d'onde et une progression naturelle complete ne sont pas prouves.

La ROM v0194 et le code de sa boucle jouable sont inchanges. Les composants
nouveaux sont verifies dans des bancs separes. Les sources, captures et
rapports sont figes dans `native-source-wait-v0194` avec manifeste SHA-256 ;
les fichiers volumineux restent locaux et les sources/rapports sont dans Git.
