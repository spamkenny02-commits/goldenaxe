# v0240 : carte du monde utilisable

L'objet 11 ne declenchait aucun affichage dans la v0235. La v0240 traduit
31E7..3291 et les routines 837C/83EC/844D de la banque2 :

- Apercu des 225 ecrans exterieurs, avec le cadre et la palette d'origine.
- Chaque pixel resulte du maximum des quatre categories de metatuiles du bloc
  2x2 correspondant, selon la table84DE. Les transformations de quete passent
  par les routines de preparation des salles deja portees.
- Dessin progressif pendant la generation et marqueur du heros selon sa salle
  et sa position. Le drapeau C0F5 permet l'alternance avec le marqueur de tresor.
- Fermeture par B ou C, retour a l'arme de base et restauration du decor,
  de la carte, des cellules et des metadonnees. L'objet reste possede.
- Activation ignoree dans les deux classes interieures.

Les ressources sont extraites de la ROM, sans images d'emulateur embarquees.
Le tampon partage des modales conserve les donnees de la salle pendant la
construction de l'apercu. Une assertion verifie la taille de cette sauvegarde.
La fermeture conserve le budget commun de restauration 16EF/1DE2 utilise par
l'inventaire ; sa reserve IRQ et le travail de controle restent approximatifs.

Les v0236..v0239 sont des compilations intermediaires conservees. Utiliser v0240.

## Preuves et limites

Seize cas controles en PAL/NTSC : carte normale, marqueur de tresor, modification
de quete en salle 11, combinaison des deux, fermeture par B, boutonB presse pendant
la generation et gardes interieures. Dans ce dernier cas de bouton, la SMS traite
la nouvelle pression lorsqu'elle reprend sa boucle d'attente ; la MD conserve ce
comportement. Les fixtures donnent la possession de l'objet et les drapeaux;
une seule phase d'horloge est alignee pour comparer les marqueurs.

Dans les dix cas d'apercu stabilise, les 5120 octets graphiques et 1280 octets de
carte de tuiles correspondent a la SMS. Les comparaisons couvrent 90 images,
dont 33 images consecutives par region pour le cycle des marqueurs. L'edition
de quete modifie reellement deux octets graphiques de la carte source.

Les douze retours exterieurs conservent chacun 160 cellules et 256 drapeaux de
salle par machine. Les 1536 octets de carte/HUD correspondent a la SMS et les
images stabilisees apres fermeture sont identiques apres normalisation des
couleurs MD vers la palette SMS observee. Les gardes interieures ne constituent
pas un parcours interieur naturel.

La generation reste trop rapide : elle termine environ 94 images avant la SMS
en NTSC et 80 en PAL dans les cas ordinaires mesures. La publication intermediaire
se fait par tuiles sur MD, tandis que la SMS ecrit ses plans pixel par pixel.
Le minutage complet d'ouverture/fermeture, la forme d'onde et l'acquisition
naturelle de cet objet restent a verifier ou a aligner. Le portage complet,
le hasard source et la suite de la campagne restent inacheves.

```
python tools/validate_world_overview.py --tag nouveau-test
python tools/validate_world_overview.py --tag nouveau-test-pal --pal
python tools/validate_world_overview.py --tag nouveau-test-tresor --treasure --sweep
python tools/validate_world_overview.py --tag nouveau-test-quete --edited
python tools/validate_world_overview.py --tag nouveau-test-b --close-b
```
