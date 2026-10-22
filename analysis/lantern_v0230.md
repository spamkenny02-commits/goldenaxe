# v0230 : utilisation de la lanterne

La selection de l'objet 3 ne declenchait aucune action dans la v0229.
La v0230 traduit 2FD2..3020 et les routines BDBE/BE78 de la banque 5 :

- Activation uniquement lorsque la salle du donjon est sombre.
- Commande sonore A9, quarante attentes d'affichage et animation des couleurs
  13..15 avec la table originale deja extraite de la ROM.
- Passage a la palette normale du donjon par le fondu 0ACE.
- Retour a l'arme de base et actualisation de son icone ; la lanterne reste
  possedee et ne consomme pas de magie.
- L'inventaire conserve l'eclairage. Une nouvelle activation dans la salle
  eclairee ne relance pas la sequence et conserve la selection de la lanterne.

La selection de palette de chaque nouvelle salle recalcule son obscurite,
comme auparavant. L'eclairage ne devient pas un drapeau de sauvegarde global.

## Verification

Les deux cartouches demarrent normalement et entrent dans le premier donjon.
Une fixture controlee place ensuite la salle sombre 1D3, sa carte et la lanterne
possedee. La phase initiale est alignee une fois pour comparer l'animation.
Les seize couleurs de fond correspondent sur les 58 images de l'activation,
en NTSC et PAL : 40 images d'effet, puis le fondu avant le retour a l'arme.
La reouverture du menu, la selection de la lanterne et une deuxieme pression
dans la salle eclairee passent aussi. Huit cas d'inventaire par region passent.
Le parcours naturel jusqu'a l'entree du premier donjon reste fonctionnel
dans les deux regions sur cette compilation.

```
python tools/validate_lantern_gameplay.py --tag nouveau-test
python tools/validate_lantern_gameplay.py --tag nouveau-test-pal --pal
```

Cette preuve utilise des fixtures de salle/possession et une phase initiale
controlee. Elle ne prouve pas une acquisition naturelle de la lanterne,
ni l'egalite globale des images, des formes d'onde ou de la cadence du jeu.
Les parcours enregistres necessaires restent dans les archives locales.
Le hasard, les autres objets encore incomplets et la campagne restent a porter
ou a verifier. Le portage complet n'est pas declare termine.
