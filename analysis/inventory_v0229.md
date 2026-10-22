# v0229 : refus de selection dans l'inventaire

La v0228 ne produisait aucun bruitage en validant une case vide. Elle permettait
aussi de selectionner les objets des cases 9 et 11 dans une maison ou un donjon.
La source SMS 7326..7356 refuse ces deux selections lorsque C040 est non nul,
et demande le son A1 dans tous les cas de refus. La v0229 reprend ces conditions,
conserve l'objet equipe lors du refus et maintient AB pour une selection acceptee.

Huit cas controles par region couvrent une case vide, la hache possedee dans un
donjon et chacun des deux objets reserves dans les trois classes graphiques.
Les selections finales et commandes sonores correspondent a la SMS en NTSC et
PAL. La comparaison v0228 conserve les echecs observes avant la correction.
Ces fixtures injectent uniquement la possession initiale, la classe et des acteurs
vides ; elles ne prouvent pas une acquisition naturelle des objets 9 et 11,
ni une egalite des formes d'onde ou du minutage audio complet.

Un parcours distinct, depuis une nouvelle partie et sans injection RAM/SRAM,
recupere la hache dans la salle 1B6, ouvre l'inventaire, selectionne la case 1,
ferme le menu et execute l'attaque secondaire. SMS et MD montrent douze images
dans les etats d'attaque 4/5 sur cette sequence. La MD finit sans mort, la SMS
utilise un Continue. Les combats et leurs durees ne sont pas declares identiques.

Reproduction : Python 3.13 avec Pillow, puis :

```
python tools/validate_inventory_acceptance.py --tag nouveau-test
python tools/validate_inventory_acceptance.py --tag nouveau-test-pal --pal
```

La suite de la campagne, le hasard source et la cadence globale restent a terminer.
Cette version apporte une correction d'inventaire ; elle ne conclut pas le portage.
