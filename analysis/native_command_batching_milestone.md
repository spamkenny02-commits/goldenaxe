# Commandes RLE et lignes vidéo sans interruption

La chaîne16D0..24BF traite maintenant une commande RLE complète quand elle
tient avant VINT. Ses coûts comprennent les franchissements de page, les
branches finales et tous les M1. La voie par octet/instruction reste active
près des interruptions. Les blocs acceptent jusqu’à65535 lectures M1 ;
aucun coût source n’est supprimé.

La conversion des métatiles traite une ligne entière quand elle tient dans
la fenêtre. Les boucles de décalage des128 caractères et d’attributs du HUD
utilisent aussi un bloc entier. Les instructions ordinaires ont une voie
inline équivalente ; préchargement, DI/EI, IRQ en attente et franchissements
qui nécessitent le gestionnaire complet conservent ce gestionnaire.

## Preuves

- 24 parcours retrouvant les16 points source SMS : temps, phase, R/M1,
  interruptions, RAM/audio et données graphiques. Compilation68000 PAL/NTSC :
  zéro échec, noyaux terminés en3149/2635 images de contrôle.
- 1244 cas032A et2340 cas0C00, comparés aux implémentations scalaires
  immuables : données, horloge et interruptions identiques.
- 1536 comparaisons de conversion complète et HUD contre le code scalaire,
  avec les256 valeurs de santé/magie/or indépendamment, bornes de capacités,
  masques de gemmes, IFF et phases VINT PAL/NTSC. Comparaison des1536 octets
  du plan,256 cases,336 octets RAM,400 audio et des journaux IRQ.
- 7040 cas d’horloge, sur PC et68000 PAL/NTSC : répétitions, blocs avec M1
  sur16 bits et instructions ordinaires. Gardes, compteurs, R et limites
  VINT sont comparés à la référence immuable. Un callback IRQ manquant
  produit le même refus et conserve le même état.
- Le contrôle des9021 valeurs HUD contre le code SMS est également relancé.

## Budget et travail restant

À protocole identique, la chaîne passe de54–55 à25–27 images de calcul
NTSC ; PAL de44–45 à20–22. Le travail SMS correspondant vaut environ22,71
et19,57 images. Le gain mesuré est donc voisin de50 pour cent, selon le cas.
Il porte sur les quatre appels natifs, sans hashes ni copies de vérification.
Les compteurs et lectures de temps IRQ ajoutent un petit coût ; leur
sous-total est une estimation.

Ce profilage reste un budget minimal : écran éteint, PSG ignoré, sans envoi
graphique ni cadence interactive. Certains cas dépassent déjà le budget
SMS. Le raccordement exige encore des gains, la continuité de phase depuis
le démarrage et les autres branches du chargement. Le portage complet,
les acteurs et le héros ne sont pas déclarés terminés.

La ROM reconstruite reste v0198 avec les mêmes octets. Aucun gain de vitesse
du jeu actif n’est revendiqué à ce stade.

Rapports : [budget](native_loading_budget_report.json),
[chaîne68000](native_room_finish_68k_report.json),
[horloge68000](clock_repeat_fast_68k_report.json),
[HUD avec IRQ](hud_clock_batch_report.json).
