# Horloge native : traitement par blocs avant raccordement

La ROM jouable reste v0198. Ce jalon optimise la chaîne native 16D0..24BF,
encore indépendante du chargement actif du jeu. Le portage complet reste ouvert.

Les décodeurs032A et0C00 traitent désormais les blocs déterministes avant
la prochaine interruption. Les passages proches de VINT, les états DI/EI
et le premier opcode préchargé conservent les étapes détaillées. Les copies
et les paires de colonnes du plan vidéo utilisent le même principe. Les
écritures sont terminées avant la prochaine opération de l’horloge.
Une voie inline traite les blocs uniques ; le calcul des répétitions évite
la division quand tout le bloc tient. Les produits16x16 utilisent MULU.W
sur68000. Aucun coût source T/M1 n’est supprimé.

## Vérifications

- 24 contextes,16 points SMS par contexte : phase, R, M1, RAM/audio,
  interruptions et données logiques toujours identiques ; compilation68000
  exécutée en PAL et NTSC, zéro échec.
- 1 244 cas du décodeur032A et2 340 cas du décodeur0C00 comparés à la
  version scalaire archivée : tous les octets, états et interruptions concordent.
- 4 480 cas arithmétiques de répétition/bloc, dont gardes, limites VINT,
  retours de compteurs et opérandes16 bits maximaux : référence scalaire
  identique sur PC et68000 dans les deux régions.
- Le jeu de9 021 valeurs HUD est revérifié séparément contre le code SMS.

## Mesure et limites

Le noyau de preuve complet passe de38 514 à3 768 images NTSC et de32 223
à3 153 PAL. Il inclut des hashes et des copies de contrôle : ces nombres
ne mesurent pas la vitesse du jeu.

Le profilage sans ces hashes, avec les quatre appels natifs seuls entre
les lectures de vtimer, demande54–55 images NTSC pour22,71 images de
travail SMS, et44–45 PAL pour19,57. Le précédent profilage avec les mêmes
compteurs demandait74–77 et62–63 respectivement (voir les valeurs brutes
archivées pour les intervalles exacts). Les compteurs ne comptent pas les
blocs inline. Les lectures de temps par interruption ajoutent un petit coût.
Le sous-total IRQ reste une estimation, pas une décomposition CPU exacte.

Ces mesures restent un budget minimal : écran éteint, sortie PSG ignorée,
sans téléversement graphique ni cadence interactive. La chaîne demande
encore environ2,4 fois son budget SMS ; elle ne peut pas être activée telle
quelle en prétendant respecter les timings. Restent également la continuité
de phase depuis le démarrage, les autres branches/classes et la suite des
acteurs/héros. Aucune accélération de la ROM jouable n’est revendiquée.

Rapports : [horloge](clock_repeat_fast_report.json),
[68000](clock_repeat_fast_68k_report.json),
[décodeur032A](pattern_clock_batch_report.json),
[décodeur0C00](ram_clock_batch_report.json),
[chaîne68000](native_room_finish_68k_report.json),
[budget](native_loading_budget_report.json).
