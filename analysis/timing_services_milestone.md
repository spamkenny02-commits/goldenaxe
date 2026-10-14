# v0011 — transitions des marchands et cadence

ROM : `versions/v0011-174b1015/gaw-megadrive-v0011.bin`, 512 Kio, SHA-256 `174b10157b48d7f44ff7a271195b7d4367aa5ae219e32f757ddabf419b4f1aa9`.

## Corrections

Le remplacement des graphismes du marchand pouvait afficher des motifs de la maison avec les nouvelles tuiles. La zone de jeu est maintenant masquée avant la réutilisation des tuiles, en gardant le HUD. Les transferts utiles sont groupés dans les VBlank, au lieu de transférer les 512 tuiles par le CPU pendant l'affichage. La sortie recharge les graphismes par blocs bornés avant de réafficher la pièce.

La routine SMS 77B7..782B révèle le portrait avec huit masques tournants sur le plan de couleur 2. Cette séquence manquante est traduite. Le texte précède maintenant l'apparition des produits, suivant 78CE/779B/7719.

La conversion des plans SMS vers les pixels Mega Drive utilise une table de 256 entrées à la place des calculs répétés pour chaque plan et chaque ligne. Elle conserve les pixels, tout en supprimant des dépassements de temps de calcul. La dernière ligne du récit conserve désormais sa temporisation avant le retour au titre. Les préparations de défilement respectent également les différences PAL/NTSC observées dans la source.

## Mesures dans Genesis Plus GX

La mesure compte les images émulées, et non le temps pris par le PC pour lancer les tests. Les deux machines utilisent la même cadence dans chaque mode : 59,922743 Hz en NTSC, 49,701459 Hz en PAL.

| Séquence | Résultat |
| --- | --- |
| Intro sans boutons, 65 lignes | Les cartes de scène et de texte correspondent. L'écart reste entre 13 et 14 images en NTSC, entre -5 et -4 en PAL ; il ne s'accumule plus. |
| Ancienne v0006, ligne 45 | Le retard atteignait 363 images, environ 6,06 secondes en NTSC. |
| Retour de l'intro au titre | NTSC : SMS 5959, MD 5971 ; PAL : SMS 5952, MD 5946. Ces petits écarts absolus restent présents. |
| Héros | Positions, direction, animation et compteur identiques sur 371 images, dans les deux modes. |
| Défilements horizontaux | 366 images comparées : états identiques. Gauche/droite : 37/38 images en NTSC, 36/36 en PAL. |
| Monstres, mouvements déterministes | Huit acteurs contrôlés, vitesses de ±0,25 à ±1,5 pixel par image : positions, vitesses et compteurs identiques sur 47 images. Cela ne couvre pas tous les comportements ni le hasard Z80. |
| Transition verticale 94 vers A4 | Le défilement est présent, mais la fin de préparation de la destination reste trop rapide sur MD : 25 contre 52 images d'état transition en NTSC, 24 contre 46 en PAL. Le délai du chargement d'acteurs reste à traduire. |

## Validation et limites

Les rapports sont archivés avec la ROM numérotée. Les sept cas du marchand couvrent les achats, refus, images stables et entrée/sortie avec HUD visible. Le contrôle supplémentaire de la révélation compare chaque image visible du portrait à un état réellement rendu par la SMS, avec normalisation des couleurs des DAC ; ce contrôle ne prouve pas l'identité de toutes les images du menu ni de leur calendrier absolu.

Des contrôles ciblés couvrent aussi les sauvegardes/rechargements, les auberges payantes, les dialogues et les 29 séquences de bruitages. Le portage complet du jeu, le flux aléatoire original et la cadence de tous les types de monstres ne sont pas terminés.

Reproduction : `tools/validate_intro.py` (option `--pal`), `tools/measure_timing.py` (option `--pal`), `tools/validate_merchant.py`, puis `tools/validate_service_transition.py`.
