# Graphismes d'ennemis sur la chaine native de chargement

Travail du 24 octobre 2026, apres v0275. Le code du chargeur experimental est
prolonge jusqu'a 18E1. Il reste hors du chemin jouable : la ROM recommandee
est toujours v0275 et son generateur SGDK n'est pas remplace par cette etape.

`source_actor_graphics` porte la reutilisation des types deja charges,
l'allocation des tuiles, les descripteurs ROM, le decodage quatre plans et
la conversion de palette. `source_pattern_decode` reutilise le decodeur
032A avec une adresse VDP logique explicite ; les appels precedents gardent
leur adresse4000. Le nouveau chargeur utilise les adresses6000..7FFF et un
miroir natif de la VRAM SMS. Les donnees restent issues de la ROM originale.

`source_actor_remap` reproduit 1D0D, y compris DI/EI, les lectures INI du
coeur de reference et les ecritures par plan. Sa memoire temporaire occupe
D100..D16F : palette16, tuile32 et64 indices de pixels, repartis sur huit
lignes. Un controle direct du Z80 a detecte une reutilisation erronee de
D130 pour chaque ligne dans le premier brouillon ; les huit lignes ont
maintenant leurs emplacements originaux. Les1024 octets de terrain sont
compares dans les tests fonctionnels pour verifier aussi les octets preserves.

`source_room_load_class0_graphics` raccorde ce travail a la chaine16D0
precedente : decor, carte, HUD, attente, palette, historique, tirages,
liste d'ennemis puis leurs graphismes. La meme horloge et le meme contexte
IRQ/audio traversent tous les appels. Aucune valeur de R, graine ou phase
n'est reinjectee entre les etapes. C067 dispose d'une vue explicite, car il
n'appartient pas au contexte RAM compact de l'adaptateur IRQ.

## Verification executee

- 24 sorties de passages payants SMS : six destinations, masques00/FF,
  NTSC/PAL. Depuis une seule entree16D0 observee,624 points correspondent
  jusqu'a18E1 pour les temps, phases, M1, R, IRQ et331 octets RAM/400 audio.
  Les72 tirages de reapparition, l'historique, les masques, les768 octets
  d'ennemis, leur compteur, l'allocation et les pixels d'ennemis correspondent.
  Les6176 octets graphiques du decor et1536 octets carte/HUD sont aussi
  verifies contre les donnees derivees de la ROM.
- La chaine complete compilee en68000 execute les24 vecteurs dans les deux
  regions :48 executions sans divergence. Les IRQ physiques sont coupees,
  les IRQ SMS et leur musique active restent executes dans l'horloge virtuelle.
  Chaque etat de controle est compare directement a la ROM du banc pendant
  l'execution, ce qui evite de conserver32 etats RAM simultanement : cette
  retention privait auparavant le demarrage SGDK de sa memoire d'allocation.
- Le composant1853..18E1 est egalement verifie separement sur les24 entrees.
- 156 cas source/C supplementaires couvrent les80 types trouves dans les
  512 listes,64 cas de reutilisation et12 masques partiels mixtes. Les IRQ
  source sont actives avec l'audio en pause. Les pixels, l'allocation, les
  acteurs et1024 octets temporaires correspondent, ainsi que les points
  de temps/R/M1/RAM/audio. Ce n'est pas une exploration de toutes les
  combinaisons de salles et de masques.
- 96 conversions source/C ciblent les tables10/20, quatre adresses incluant
  des changements de page et la fin de VRAM,32/64/128 octets et quatre motifs.
  Les pixels et toute la zone temporaire correspondent. La table10 et les
  ressources individuelles de boss restent ici des preuves source/C hote ;
  leur execution specifique en68000 n'est pas prouvee par la matrice ordinaire.

La composition de la carte reste limitee aux six destinations exterieures
prises en charge par `source_world_map_load`, classe0 changee, bit0 actif,
C0AC nul. La couverture des80 ressources n'etend pas cette portee du chargeur.
Les captures de passages ont une preparation controlee, distincte d'une
campagne naturelle. Le rendu et les commutations de banques physiques MD ne
sont pas realises par ce chargeur logique.

18E1 precede encore le RET du chargeur d'ennemis, l'initialisation du heros,
les scripts et la selection musicale finale. Ces etapes, l'horloge depuis le
boot, les autres classes, le budget CPU/rendu, les formes d'onde et la campagne
complete restent ouverts. Les temps des cartouches de diagnostic incluent
leurs controles et ne prouvent pas la cadence de la ROM jouable.

Rapports : [chaine complete](native_room_graphics_report.json),
[68000](native_room_graphics_68k_report.json),
[composant](native_actor_graphics_report.json),
[80 types](native_actor_assets_report.json),
[conversion et memoire temporaire](native_actor_remap_report.json).
