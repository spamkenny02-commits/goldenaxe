# v0013 — délai de préparation des acteurs

ROM : `versions/v0013-4ab93fb4/gaw-megadrive-v0013.bin`, 512 Kio. SHA-256 : `4ab93fb473e026f95828ceca1d1881cb1d81b2b756bc8bc9871912322782b977`.

## Traduction

La source 1780 charge une seule fois les graphismes de chaque type d'acteur encore présent, via le décodeur 032A et, selon son descripteur, la conversion de couleurs 1D0D. Le portage utilisait déjà les graphismes convertis, mais reprenait le jeu immédiatement après les avoir copiés. Cela avançait la fin de la transition 94 vers A4 de 27 images en NTSC et de 22 en PAL.

L'extraction calcule maintenant le travail nominal des boucles Z80 pour les 33 types graphiques. Ces coûts sont intégrés à la ROM comme métadonnées des ressources. Le chargeur natif les additionne une seule fois par type effectivement conservé par le masque de persistance. La transition possède une étape de préparation pendant laquelle les interruptions et la musique continuent, mais le héros et les ennemis restent à l'arrêt.

Il n'y a ni valeur d'attente propre à A4, ni état d'émulateur injecté dans la cartouche. Le calcul de durée utilise les cycles vidéo des deux modes et des allocations approximatives de 20 000 T pour le contrôle du chargeur et de 3 072 T par image pour les interruptions. Ces allocations ne constituent pas encore une traduction exacte du calendrier de toutes les routines.

## Preuves

`validate_loading_budget.py` compare quatre masques de persistance, dans chacun des deux modes. Les comptes d'acteurs, allocations de tuiles et sommes des coûts natifs correspondent aux ressources attendues dans les huit cas.

| Cas | NTSC SMS / MD | PAL SMS / MD |
| --- | --- | --- |
| Salle complète FF, trajet naturel | 52 / 52 images | 46 / 46 images |
| Quatre acteurs 26, masque F0 | 29 / 28 | 27 / 27 |
| Un acteur 26, masque 80 | 29 / 28 | 27 / 27 |
| Un acteur 20, masque 08 | 50 / 49 | 44 / 44 |

Les mesures naturelles comparent aussi le héros et les défilements horizontaux : aucun écart des champs suivis en PAL ou NTSC. Les huit mouvements déterministes d'ennemis restent identiques sur 47 images. Le contrôle vertical compare 161 images : les états du héros et de la transition correspondent ; le premier écart de pixels reste à l'image 3099, lorsque les positions d'apparition dépendent du hasard original qui n'est pas encore reproduit.

Le profilage de recherche mesure le chargeur original entre les images 3070 et 3097 en NTSC, 3069 et 3091 en PAL. Il observe 1 494 274 T de travail hors interruptions dans les deux modes. Les deux conversions de couleurs sont contrôlées contre les compteurs du cœur de référence. Ce cœur facture 20 T à INI via ses tables de base et supplémentaires ; le modèle nominal de la cartouche conserve 16 T pour cette instruction. Cette différence et les budgets d'interruptions sont explicitement distingués dans les rapports, sans prétendre à une validation matérielle complète.

Le cœur de recherche est une DLL séparée dans `work/`, construite par `build_timing_core.py`. Les sondes lisent PC, registres et cycles, sans modifier le CPU émulé. Ce cœur n'est pas lié au portage Mega Drive.

## Validation et suite

Neuf rapports courants et leur audit sont archivés avec la ROM v0013. Ils couvrent les mesures PAL/NTSC, les huit masques, les compteurs d'acteurs, le défilement vertical, les sept achats/refus du marchand, les images de révélation du portrait et les 65 lignes de l'intro dans les deux modes. Le checksum standard et les trois copies de la ROM correspondent. Aucun nouveau contrôle intégral de tout le jeu n'est revendiqué.

Restent notamment les trois avances d'une image des masques NTSC ci-dessus, le calcul précis des interruptions et de la phase vidéo pour toutes les salles, le hasard Z80 et les familles d'acteurs encore absentes. Les corrections des marchands et de l'intro de v0011 sont conservées.
