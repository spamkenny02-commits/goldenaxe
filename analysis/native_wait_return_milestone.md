# Attente complete et retour au caller en C natif

`source_wait_restore.c/.h` complete l'attente native 0B95..0BB3 par les
instructions 0BB3..0BC5 et le retour effectif au caller. La restauration
compte 149T/17M1, avec une acceptation d'IRQ possible entre chaque
instruction et avant le fetch de l'opcode du caller. Le cout total n'est
donc pas traite comme un delai constant ajoute apres l'attente.

`source_wait_complete` compose les deux parties sur la meme horloge,
le meme RAM et le meme lecteur audio natif. Les variables et ressources
du caller C gardent leur etat propre ; les registres et mapper Z80 n'ont
pas de restauration physique equivalente a executer en 68000. Leurs
instructions contribuent au cout source. L'observateur SMS verifie
separement que la banque d'origine est bien restauree au retour.

## Comparaison a la SMS

Un observateur en lecture seule ajoute les snapshots a l'entree 0B95,
au debut de restauration 0BB3 et au vrai caller. Le dernier est determine
depuis l'adresse de retour sur la pile au RET 0BC5, et non depuis une
adresse de caller supposee. Les attentes doubles qui reviennent a 0B95
sont finalisees avant l'enregistrement de l'attente suivante.

- 6 156 attentes completes dans les fixtures DI/EI/IRQ latchee d'origine.
  Les anciens snapshots entree/0BB3 restent identiques octet pour octet,
  ainsi que leurs deltas M1 et R. Le compteur d'observation M1 global peut
  avoir une origine differente entre runs, car le frontend arrete maintenant
  les fixtures terminees sans emuler leurs images inactives restantes.
- 18 468 contextes de restauration avec cadres de pile synthetiques
  equilibres : DI, EI+NOP et EI juste avant le premier POP ; temporisations
  au bord de VINT, pauses 0/1/128, compteurs 0/1/255 et musique 00/84.
  Le code original 0BB3..0BC5, vecteur, interruptions et lecteur reste
  intact. Seul l'octet precedent 0BB2 est remplace par EI dans cette fixture
  pour construire le cas d'inhibition. Il y a 1 476 cas NTSC et 1 548 cas
  PAL avec interruption effective pendant la restauration.
- 13 725 attentes completes de parcours reels, six routes de passages
  payants, deux masques et deux regions. Les anciennes traces source de
  cycles, etats et attente restent identiques. Le point de reset de
  l'observation a l'image 4199 est conserve. Les six callers observes sont
  24F6, 0B95, 0ADC, 22A3, 0AC0 et 1FBF.
- Les 38 349 vecteurs passent en code 68000 PAL/NTSC, dans vingt cartouches
  de test de moins de 4 Mio. Phase, R/M1, durees, 331 octets RAM et les
  400 octets audio correspondent a la SMS. Les champs supplementaires
  purement natifs sont verifies pour parite avec l'hote.
- 816 chaines de deux attentes sont aussi executees sur hote et 68000
  PAL/NTSC. L'etat, l'audio et l'horloge restent vivants entre les deux
  appels, sans reinjection de l'entree source intermediaire. Le dernier
  caller et tous les instants d'IRQ correspondent aux captures source.

## Limites et suite

Les entrees initiales R/raster/RAM sont encore observees. Les cinq octets
de statut/entrees C01B et C020..C023 restent exclus des comparaisons
d'attente, comme dans les etapes precedentes ; le banc fournit joy=0.
Les valeurs de registres Z80 du caller ne sont pas emulees. Les banques
restaurees sont observees sur SMS, tandis que le code natif utilise ses
pointeurs de ressources explicites.

L'horloge complete depuis le debut du chargement, le hasard natif et le
raccordement a la boucle jouable restent a terminer. Les chemins de reset,
les interruptions video imbriquees et certaines commandes audio gardent
leurs diagnostics explicites. Il n'y a pas de preuve de materiel physique,
de formes d'onde identiques ou de progression naturelle complete.

La ROM v0194 et tous les fichiers natifs preexistants sont inchanges.
Le nouveau helper est valide dans des bancs separes. Le frontend de test
peut s'arreter apres le signal de fin reel et verifie toujours tous les
cas attendus ; ses appels sans cette option conservent leur comportement.
Les sources, observateur, outils, rapports et captures sont figes dans
`native-wait-return-v0194` avec manifeste SHA-256. Les fichiers volumineux
restent locaux ; les sources et rapports sont versions dans le Git local.
