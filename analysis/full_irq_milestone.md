# Interruptions video et budget conditionnel complet (ROMv0183 inchangee)

Le modele0137..01E2 compte neuf etapes : SAT64,SAT128,motifs3B07,
HUD1F54,palette,file0293,mappage audio,lecteur8000 et entrees/compteurs.
Le cout de chaque instruction de liaison est inclus. Les transferts OUTI
sont comptes selon la boucle originale ;OUTI etDJNZ decrementent chacun B,
ce qui donne32 ecritures dans les boucles initialisees a40h.
La file couvre les descripteurs1 (ROM/RAM) et les rectangles>=2.

13749 interruptions completes sur24 parcours controles correspondent aux
neuf couts et aux336 octets observes(C000..C04F/DD00..DDFF). Aucun cas
capture n'est ignore ;le nombre de captures correspond aux appels1A2.
Les14424 appels audio sont controles independamment pour400 octets,DE et
cycles. Les tableaux complets de cycles sont identiques aux referencesv0179.

2880 cas isoles supplementaires varient saut de palette,drapeauxHUD,
compteurPause,delai,anciens boutons/etatPause et compensation video,
en PAL etNTSC. L'appelant et le cadreAF sont synthetiques ;les routines
fixes d'IRQ et les banques4/6 restent intactes. File vide et canaux audio
inactifs dans cette matrice. Ce n'est pas une couverture exhaustive des
entrees,file,banques,transferts ou combinaisons naturelles.

Le bilan16D0..0ACE assemble maintenant le travail horsIRQ,y compris les
deux attentes0B95,675 interruptions audio seules et48 interruptions
completes dans les24 chargements. La somme des couts calcules correspond
exactement au temps total observe,sans utiliser les durees observees des
IRQcompletes comme cout d'entree. Le controle jusqu'a1FA7 passe aussi.

Ce bilan reste conditionnel :les decisions de scrutationVBlank et de
compteur video,les valeurs des ports d'entree,la chronologie desIRQ et les
entrees historique/hasard sont fournies par les captures. La phase future
et ces decisions ne sont pas encore predites. Aucun delai natif n'est
ajoute,la ROM restev0183. Les sortiesVDP/PSG en pixels/formes d'onde,le
materiel reel,les autres classes/story/boss et le jeu complet ne sont pas
valides par ce travail. Les lectures de compte de motifs en RAM ou banque
hors16 banques,les queues horsplage capturee et la brancheReset sont exclues.

Reproduire :

- python tools/build_full_irq_core.py
- python tools/validate_full_irq_unit.py
- python tools/validate_full_irq_cost.py (captures locales requises)
- python tools/validate_complete_loading_budget.py (captures locales requises)
- python tools/archive_full_irq_research.py

Sources,fixtures,captures requises et bibliotheque sont conservees localement
dans full-irq-research-v0183 avec manifeste SHA-256.
