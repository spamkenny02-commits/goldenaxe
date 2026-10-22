# v0235 : utilisation de la plume magique

La plume magique pouvait etre achetee mais n'avait aucun effet dans la v0232.
La v0235 traduit l'activation 30E8..3123 :

- Retour vers C0C2, le dernier point de sauvegarde ecrit, avec conservation
  du masque des ennemis de la carte quittee (18E2/18E9).
- Effacement 1F78 en vingt etapes et commande sonore A6. La source saute
  directement a 0B24 : aucun fondu noir supplementaire n'est ajoute.
- Consommation de la plume, retour a l'arme de base, chargement de la carte
  et reouverture de l'ecran par la routine existante 1FA7.
- Conservation des PV, de la magie, de l'or, des cles et du compteur de
  blessure. Le pas de mouvement restant apres 3112 est execute, comme le
  traitement commun 26E5..2753 de la SMS, avant la reinitialisation 2C63.
- Activation ignoree dans une maison ou un donjon, sans consommer l'objet.

L'exterieur etant deja charge, ses graphismes de fond sont reutilises. Seuls
les acteurs et le heros sont recharges. Les v0233/v0234 restent conservees
comme intermediaires ; utiliser la v0235.

## Verification et limites

Douze cas controles, six par region : retour vers 95, retour vers le village94,
refus dans les deux classes interieures, blessure en cours et mouvement en cours.
Les ressources et la reprise du mouvement passent dans chaque cas applicable.
Le masque de depart A1 correspond a la SMS. Le cas blesse conserve29 apres
chargement sur les deux machines ; le cas en mouvement arrive a X138 sur les
deux machines, consequence du dernier pas commun avant 2C63.

Les huit retours exterieurs comparent chacun1536 octets de carte/HUD et une
image stabilisee de49152 pixels, avec normalisation de la palette MD vers la
palette SMS observee : aucune difference. Les quatre gardes interieures utilisent
une classe graphique controlee, sans prouver un parcours interieur naturel.

Un parcours distinct demarre normalement, entre chez le premier marchand,
achete la plume, sort a pied, l'equipe dans l'inventaire puis l'utilise. Seul
l'or initial est fixe a60 ; aucune carte, position, possession ou sauvegarde
n'est injectee. SMS et MD reviennent en95 avec24 PV et0 or, plume consommee.

La duree complete n'est pas encore exacte : dans les fixtures ordinaires,
la reprise MD arrive4 images avant la SMS en NTSC et5 en PAL. Le parcours
d'achat mesure egalement5 images d'avance pour l'utilisation. Le budget commun
des acteurs conserve une reserve IRQ et un travail de controle approximatifs.
Les images intermediaires et la forme d'onde complete ne sont pas declarees
identiques. L'interaction exacte avec une collision ennemie le meme instant
et tous les points de sauvegarde restent a verifier.

```
python tools/validate_return_feather.py --tag nouveau-test
python tools/validate_return_feather.py --tag nouveau-test-pal --pal
python tools/validate_return_feather.py --tag nouveau-test-hurt --hurt 80
python tools/validate_return_feather.py --tag nouveau-test-moving --moving
python tools/play_feather_purchase.py --tag nouvel-achat
python tools/play_feather_purchase.py --tag nouvel-achat --sms
```

Le hasard source, les autres objets incomplets et la campagne restent a porter
ou a verifier. Cette version ne conclut pas le portage complet.
