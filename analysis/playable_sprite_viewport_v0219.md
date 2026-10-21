# ROM jouable v0219 : limites verticales des sprites

La v0219 corrige les pixels de sprites qui débordaient dans les bandes noires
Mega Drive au-dessus et en dessous des 192 lignes de jeu Master System.
Le masque des lignes hors champ est appliqué indépendamment du dépassement
de huit sprites par ligne. Il réutilise les motifs temporaires existants ;
aucune allocation permanente supplémentaire n’est ajoutée.

La table des sprites conserve ses entrées et le terminateur Y=208. Le masque
hors champ ne déclenche pas le statut de débordement SMS. Le registre vidéo
SMS observé ne demande ni masquage de la colonne gauche ni décalage horizontal.

## Vérifications ciblées

- Dix cas : cinq hauteurs d’un acteur immobilisé par injection RAM après un
  démarrage normal, en PAL et NTSC. Cent images vérifiées : 5 734 400 pixels
  de sprites et 819 200 pixels RGB des bandes noires. Les pixels visibles
  concordent avec la v0218 ; les pixels hors champ sont masqués.
- Douze captures naturelles : composition indépendante depuis VRAM/CRAM,
  sans différence sur les 614 400 pixels comparés de la zone jeu/HUD.
- Six parcours naturels d’inventaire : clairière et deux premières maisons,
  en PAL/NTSC. Les motifs fixes restaurés concordent avec la source SMS.
  Les quatre motifs animés de chaque maison sont exclus de l’égalité statique ;
  leurs différences sont conservées dans le rapport.

Les rapports sont liés au SHA-256 exact de cette ROM. Ces vérifications ne
prouvent ni la fidélité de tous les parcours et phases animées, ni la cadence
complète du jeu, ni le fonctionnement sur console réelle. Le flux aléatoire
Z80 reste à porter. L’intro et le son ne sont pas modifiés par cette version.

ROM : `versions/v0219-7518d3c1/gaw-megadrive-v0219.bin` (1 Mio).
SHA-256 : `7518d3c174b117b299c1317b5921e351de7e96eee44fcd4a7d3d43566854cce7`.
Checksum Mega Drive : `227C`.
