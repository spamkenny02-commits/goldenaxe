# Parcours naturel jusqu’au donjon1 — ROM jouable v0223

Le pilote démarre une nouvelle partie, valide le nom et le récit, puis marche
depuis la clairière95 jusqu’à l’entréeB9 du donjon1E4. Il consulte l’état du jeu
en lecture seule pour choisir les directions et reprendre son chemin après
un recul. Il ne modifie ni les ROMs, ni la RAM, ni la SRAM et n’utilise aucun
checkpoint préparé. La logique de déplacement, les ennemis, les collisions,
les dégâts et les transitions sont ceux des jeux exécutés.

Les neuf écrans extérieurs95,94,A4,B4,B5,B6,B7,B8,B9 sont franchis, puis
l’entrée1E4 est révélée. Une pression normale de cinq images déplace le héros
deY152 àY144 dans la première salle. Le flag de visite et le checkpoint du
donjon sont vérifiés. Le compteur de contrôlabilité ne se contente pas du
changement de numéro de salle : il attend l’initialisation du héros après
la révélation native, puis vérifie la commande de déplacement.

## Résultats

| Mesure | SMS NTSC | MD NTSC | SMS PAL | MD PAL |
| --- | --- | --- | --- | --- |
| Première salle publiée | 4074 | 4131 | 4010 | 4011 |
| Héros prêt après révélation | 4163 | 4220 | 4096 | 4097 |
| Intervalle de cette entrée | 89 | 89 | 86 | 86 |
| Vie à l’arrivée | 10 | 18 | 14 | 20 |

L’intervalle est mesuré entre la première publication de la salle destination
et la première initialisation au repos après révélation. Les phases vidéo
intermédiaires ne sont pas déclarées identiques par cette seule durée.
Les événements rencontrés et les commandes de récupération diffèrent entre
SMS et MD ; les temps du trajet complet ne sont donc pas comparables comme
un test de vitesse à entrées identiques.

Les flux de boutons résultants sont rejoués dans quatre processus d’émulateur
frais, sans pilote ni consultation de RAM pour les décisions. La RAM finale
complète (8192octets SMS /65536octets MD) et le PNG final de chaque replay sont
identiques à son exécution pilotée. Les images du décor192/224lignes, recadrées
sur256x160, concordent après normalisation de palette avant et après le pas
intérieur :163840pixels comparés au total. Le HUD est exclu puisque la vie diffère.

## Portée et suite

Cette validation porte sur le binaire v0223 inchangé, SHA-256
39e6995514a87d170d4d1fc713938a3645905842fe93a340415c80e996057a31.
Elle établit un trajet réellement jouable depuis une nouvelle partie jusqu’à
la première salle. Le donjon, son boss, son cristal et le jeu complet ne sont
pas terminés par ce test. Les différences de rencontres/PV restent à expliquer
et corriger ; le hasard Z80, l’horloge globale, l’audio et tous les parcours
restent hors d’une validation complète de fidélité.

Les essais antérieurs du pilote sont conservés comme diagnostics. Les cas
retenus sont sms-06/md-04 enNTSC et sms-pal-01/md-pal-01 enPAL, puis leurs
replays-fresh. Les premiers essais utilisaient un simple état de salle ; la
preuve finale exige la révélation, un HUD visible et une commande effective.

Reproduction dans un dossier de validation neuf, avec la v0223 et ses symboles :

```powershell
python tools/natural_dungeon_route.py --sms --trial 06
python tools/natural_dungeon_route.py --trial 04
python tools/natural_dungeon_route.py --sms --pal --trial 01
python tools/natural_dungeon_route.py --pal --trial 01
python tools/verify_natural_dungeon_route.py
```

Le paramètre --trial conserve chaque essai sans écraser les précédents.
Le plan de marche est tiré des données ROM ; ce plan seul ne constitue pas
une preuve de parcours. Le rapport et les captures des exécutions réelles
font autorité.
