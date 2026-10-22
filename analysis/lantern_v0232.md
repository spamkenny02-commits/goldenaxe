# v0232 : lanterne et palette du boss

La lanterne, objet 3, ne declenchait aucune action dans la v0229.
La v0232 traduit 2FD2..3020 et BDBE/BE78 de la banque 5 :

- Activation dans une salle sombre, commande sonore A9 et quarante attentes
  d'affichage avec la table originale de couleurs 13..15.
- Fondu 0ACE vers la palette normale du donjon, retour a l'arme de base et
  actualisation de son icone. La lanterne reste possedee, sans cout de magie.
- Eclairage conserve apres l'inventaire ; une nouvelle activation dans cette
  salle eclairee ne relance pas l'effet et conserve la selection de la lanterne.

Le drapeau C0AE est maintenant initialise par la selection musicale 1CD8/1CF3,
conserve pendant l'attente de disparition du boss et efface a l'apparition du
cristal 2AB1. La palette du donjon et la lanterne utilisent ce drapeau. Examiner
uniquement le bit 40 des acteurs etait insuffisant : il est efface des le debut
de la disparition, avant la fin de cette attente. Les couleurs 13..15 restent
noires dans ce contexte, comme sur SMS.

Les v0230 et v0231 sont conservees comme compilations intermediaires. Utiliser
la v0232, qui comprend la gestion du drapeau pendant la disparition du boss.

## Verification

Six cas controles : salle normale, contexte de boss et contexte de disparition,
en NTSC et PAL. Les cartouches demarrent normalement et entrent dans le premier
donjon avant l'installation d'une fixture de salle sombre 1D3, de possession et
de contexte de boss. La phase initiale est alignee une fois. Les seize couleurs
de fond correspondent sur les 58 images d'activation de chaque cas, soit 348
images comparees. Le maintien de l'eclairage apres le menu et la nouvelle
selection/activation de la lanterne passent dans les six cas.

Huit cas de selection d'inventaire par region passent sur cette compilation.
Le parcours naturel jusqu'a l'entree du premier donjon fonctionne aussi en
PAL/NTSC. Le lecteur audio ne signale aucune commande non prise en charge.

```
python tools/validate_lantern_gameplay.py --tag nouveau-test
python tools/validate_lantern_gameplay.py --tag nouveau-test-pal --pal
python tools/validate_lantern_gameplay.py --tag nouveau-test-boss --boss
python tools/validate_lantern_gameplay.py --tag nouveau-test-death --boss-death
```

Ces fixtures ne prouvent pas une acquisition naturelle de la lanterne ou un
combat complet dans une salle sombre. La comparaison porte sur les couleurs
logiques, sans egalite globale des images, du minutage VDP ou des formes d'onde.
Le hasard source, les autres objets incomplets et la campagne restent a porter
ou a verifier. Le portage complet n'est pas declare termine.
