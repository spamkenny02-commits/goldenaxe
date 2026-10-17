# Fenêtres de commandes du décodeur032A

Le décodeur lit désormais plusieurs commandes ROM complètes en avance,
additionne leurs T/M1 exacts, puis les traite comme un seul bloc si elles
tiennent avant VINT et dans la limite65535T de l’API. Le second passage
écrit leurs octets décodés avant la prochaine opération d’horloge. Une
commande isolée, une interruption en attente ou la proximité d’une limite
conservent les chemins par commande, par octet et par instruction existants.
Les fins de plan et les écritures C031/C032 restent hors de ces fenêtres.
L’entrée ROM est immuable, distincte du miroir graphique de sortie.

## Vérifications

- 1460 comparaisons face au décodeur scalaire immuable : les24 contextes
  réels,192 variantes de phase,514 flux synthétiques dans les deux régions,
  puis216 cas à longues suites de2..1024 commandes. Comparaison des16384
  octets graphiques,336 RAM,400 audio, de l’horloge et des journaux IRQ.
- Un noyau68000 supplémentaire compare octet par octet les fenêtres aux
  chemins scalaires pour16 cas longs, en PAL et NTSC physiques, avec les
  deux régions logiques. Les295/324/325/1024 commandes par plan couvrent
  les bords de budget et la limite65535T. Zéro différence ;9406/7870 images
  de contrôle, sans prétendre mesurer la vitesse du jeu.
- La chaîne complète conserve ses16 points SMS sur24 contextes et passe
  en68000 PAL/NTSC ; son noyau de preuve termine en3104/2597 images.

## Gain mesuré et limites

Sans compteurs internes, le calcul des quatre appels demande maintenant
23–24 images NTSC et18–20 PAL, pour22,71/19,57 de travail SMS. Avant ce
changement, le même protocole donnait24–25 et19–20. Le gain est modeste,
de l’ordre d’une image selon le cas et l’alignement du binaire. La résolution
du chronométrage est d’une image ; les mesures instrumentées sont séparées.

Le profil reste un budget minimal : écran éteint, PSG ignoré, sans transferts
réels ni cadence interactive. La marge nécessaire au raccordement n’est
pas prouvée. Le premier chargement graphique reste la cible principale ;
préparer les données et leurs coûts depuis la ROM à la compilation est une
piste à évaluer, avec les mêmes contrôles de phase et de données.
La continuité depuis le démarrage et les autres branches restent ouvertes.

La ROM reconstruite est toujours exactement v0198. Ce jalon ne revendique
aucune accélération du jeu actif ni la fin du portage.

Rapports : [décodeur](pattern_clock_batch_report.json),
[fenêtres68000](pattern_windows_68k_report.json),
[chaîne68000](native_room_finish_68k_report.json),
[budget sans compteurs](native_loading_budget_bare_report.json).
