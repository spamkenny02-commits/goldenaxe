# Historique des salles et entree du chargeur : horloge native

Travail du 24 octobre 2026, apres la ROM jouable v0275. Aucun nouveau numero
de ROM jouable n'est attribue a ces modules encore hors du chemin principal.

`source_room_history_timed` porte les instructions 1C15..1C96, leurs trois
tirages exterieurs ou cinq tirages de donjon, les scans CPIR, les decalages
d'historique et les restaurations des masques. Il appelle le generateur
04E1 natif avec la meme horloge, sans injecter R entre les tirages.

`source_room_actor_prefix` poursuit l'entree 24BF jusqu'au premier opcode
de 1780. Il efface les 32 octets C090..C0AF et les 336 octets C4B0..C5FF,
puis execute l'historique. Les LDIR gardent leurs frontieres d'interruption
et leur ordre de copie. Le chargement des ennemis 1780 lui-meme reste a
raccorder. Les pointeurs sont des vues explicites de la memoire SMS ; ils
ne supposent pas que le contexte IRQ compact contient toute la RAM C000.

## Verification executee

- 4 608 cas d'historique et 4 608 cas du prefixe complet, sur le Z80 de
  reference, en NTSC/PAL, avec et sans interruptions. Les instructions
  originales 1C15..1C96 et 24BF..24E3 sont preservees. Les trampolines de test
  initialisent R et observent l'entree/sortie ; ils ne representent pas le
  chargement naturel depuis le demarrage.
- Chaque groupe comprend 768 cas interrompus : graine, historique complet,
  256 masques, temps de premier plan et d'IRQ, nombre de M1, phase physique
  et echantillon final de R correspondent. Le prefixe verifie aussi les
  368 octets effaces. Les 768 IRQ sont comptes par groupe de 4 608 cas.
- Les 9 216 vecteurs sont executes par les memes modules compiles en 68000,
  sur une cartouche de diagnostic distincte, dans les deux regions :
  18 432 executions, aucune divergence. Les interruptions physiques MD sont
  coupees ; l'horloge virtuelle execute les IRQ source du modele de test.

Les tests utilisent une IRQ audio en pause de 563 T / 59 M1. Ils ne prouvent
pas encore les interruptions avec musique active, les effets d'un callback
qui modifie arbitrairement les donnees, la phase globale depuis le boot ou
le flux aleatoire de la ROM jouable. Le banc de collecte reinitialise sa
pile entre commandes et vide ses compteurs d'observation entre les cas,
sans modifier l'etat du CPU ni le registre R a l'interieur des routines.

La cartouche de diagnostic termine les 9 216 vecteurs a l'image 50 410 en
NTSC et 42 197 en PAL. Ce sont des temps de banc, incluant preparation et
comparaisons ; ils ne constituent pas une mesure de cadence du jeu.

La v0275 conserve son generateur SGDK provisoire. Ces modules doivent encore
recevoir l'horloge continue du vrai chargement et respecter le budget natif
avant de remplacer ce generateur. La campagne complete reste a verifier.

Rapports : [historique](history_timed_source_report.json),
[prefixe](history_prefix_timed_source_report.json),
[execution 68000](history_timed_68k_report.json).
