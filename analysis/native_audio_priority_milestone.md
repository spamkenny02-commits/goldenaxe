# Effets prioritaires et restauration — v0187

Les routines SMS 81F8 (file DE09) et 8211 (restauration) sont maintenant
traduites dans `source_audio_priority.c` et raccordées à la ROM jouable.
Le lecteur traite la file après le dispatch, avant la compensation PAL/NTSC.
Les commandes F1/F2 rappellent la restauration quand DE0E contient un effet
prioritaire, comme le CALL8211 original à 8850. F1 conserve aussi le latch
stéréo source dans la RAM, même si le PSG Mega Drive reste mono.

Le composant produit l'état source, les cycles Z80, les lectures M1, le
registre DE de sortie et les écritures PSG à appliquer. Les tests couvrent
les effets actifs ou libres, l'emprunt de tone3/bruit, les priorités acceptées
ou refusées, les demandes d'effacement et les valeurs conservées de DE.

## Preuves ciblées

- Hôte : 21 975 cas natifs, dont 16 748 pour la file et 5 227 pour l'entrée
  directe de restauration. Les 400 octets sont comparés, ainsi que T/M1/DE
  et les décisions PSG. Quinze cas invalides sont rejetés sans mutation.
- 68000 : les mêmes 21 975 cas passent dans une cartouche SGDK de test,
  sans écart, en PAL et NTSC sous Genesis Plus GX.
- Source : l'entrée 8211 originale et sa banque restent intactes. Un appelant
  de test fournit A et DE ; 5 220 cas par région correspondent exactement
  aux 400 octets, aux cycles, aux lectures M1, à R et au DE retourné.
  La file 81F8 repose aussi sur le modèle déjà vérifié séparément sur SMS.
- ROM jouable : 29 effets × deux régions × 700 états = 40 600 comparaisons
  après initialisation contrôlée. Pour chaque effet : demande DE09, bruitage
  normal95 qui l'interrompt, effacement80 puis nouvelle demande. Les 399
  octets hors routage GG et tous les registres PSG audibles correspondent
  à l'exécution réelle de la ROM SMS.
- Régressions séparées : 13 musiques, 29 bruitages ordinaires, fondu87/B0/82,
  musique et sons du menu Nouveau jeu/Continue.

Ces comparaisons utilisent des injections d'état ou des appelants de test,
sauf les parcours naturels du menu. Elles ne prouvent pas les événements
de jeu qui alimentent la file DE09, les formes d'onde, le matériel physique
ou une partie complète. Les indices invalides restent explicitement hors
portage et signalés par le lecteur, sans lecture de table arbitraire.

## Travail restant

Les coûts calculés n'alimentent pas encore le callback de l'horloge native.
Le comptage natif des canaux, des séquences et des enveloppes, les commandes
hors modèle (dont F2 du canal de bruit), la propagation de R et l'intégration
du générateur aléatoire original restent nécessaires. Le jeu conserve donc
encore le hasard SGDK et les budgets fixes. Le portage complet reste ouvert.
