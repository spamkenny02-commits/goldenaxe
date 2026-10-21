# v0210 : limite SMS des sprites integree a la ROM jouable

La ROM complete applique maintenant la limite de huit sprites8x8 par ligne
au rendu du monde, au lieu de calculer uniquement le statut de depassement.
Chaque entree visible en Y compte, meme transparente ou hors ecran en X.
Les lignes des entrees excedentaires deviennent transparentes. Les autres
lignes et les attributs de chaque sprite restent conserves.

La correction lit le motif actuellement resident en VRAM, afin de respecter
le retard volontaire de publication des poses du heros. Les lignes masquees
utilisent deux zones de tuiles alternees1024..1087 et1152..1215. Une tuile
transparente commune1216 evite de recopier chaque sprite entierement masque.
Le buffer suivant ne modifie donc pas les clones references par l'ancienne
SAT. Les plans et leurs tuiles512 originales restent aux adresses existantes.

Les premieres compilationsv0208/v0209 sont conservees pour historique mais
ne sont pas recommandees. La version jouable retenue estv0210/1Mio,
SHA256 `4678a4f4` (hash complet dans l'index), checksumMegaDrive5779.

## Controles cibles

Le rapport `playable_sprite_limit_v0210_report.json` execute les vraies ROMs
v0203/v0210 depuis le boot, avec commandes normales jusqu'au premier jeu.
Une fixture RAM place ensuite douze acteurs aux hauteurs decalees de3pixels
pour exercer des masquages partiels et complets. Pour12 images par region,
le plan VRAM MD est compare a un raster independant limite a huit entrees,
a partir des tuiles originales non masquees et de l'ordre reel des sprites.
Le resultat concorde pour chaque pixel;7495 pixels excedentaires sont
supprimes dans chaque serie. Positions, salle et etat du jeu concordent.
La phase temporelle d'ordre des sprites n'est pas validee par ce controle.

Dix captures naturelles NTSC restent identiques octet par octet a v0203.
En PAL, neuf restent identiques; l'image3120 differe sur la seule ligne
(160,35)..(168,36), dont le plan physique suit maintenant la limite SMS.

Le rapport d'inventaire joint a la ROM verifie aussi six parcours normaux:
exterieur et deux premieres maisons, en PAL et NTSC. Les tuiles statiques
restent correctes avant/apres ouverture; les phases des quatre tuiles
animees de maison restent exclues de cette egalite, comme dans le test initial.

## Limites

Il s'agit d'une amelioration integree a la version jouable, pas de
l'integration complete du nouveau moteur a horloge source. Ces controles
ne prouvent ni une partie complete, ni la cadence de toutes les scenes,
ni le waveform ou l'execution sur console. La limite est appliquee au
rendu du monde; les autres ecrans et le zoom/taille8x16 restent hors scope.

Preuves archivees avant nettoyage:816 references compressees,22762752 octets
generes retires et18094558 octets nets liberes (environ17,3Mio). Relecture
gzip/SHA complete et24 plans physiques recuperes et recomparables apres retrait.
Les210 ROMs numerotees sont conservees.
