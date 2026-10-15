# Prediction des attentes VBlank (ROMv0183 inchangee)

Le modele0B95 utilise seulement la phaseCPU/VDP,le latchIRQ/IFF,336 octets
RAM pertinents et400 octets du lecteur audio a l'entree. Il simule les
frontieres d'instruction du prologue et de la scrutation,le blocage d'une
instruction apresEI et la conservation de A par l'interruption. La phase
VINT suit le GPG local(mode4/192 lignes,assertion a la ligne physique193).
Les IRQaudio seules et completes sont calculees avec les modeles existants ;
les boucles de palette sont predites depuis leur phase d'entree calculee.

13725 attentes sur24 parcours controles correspondent :comptes de branches,
duree totale,travailIRQ,phase d'acceptation de chaque interruption,horloge
et drapeau de sortie. Aucun compte de boucle ni horaireIRQ observe n'est
utilise comme entree de cette prediction. Les traces originales completes
restent identiques aux referencesv0179. Les24 budgets de chargement passent
avec les attentes et les IRQcompletes calculees depuis leurs etats d'entree.

6156 cas synthetiques supplementaires couvrent les entreesDI/EI et les
interruptions deja latchees,en PAL/NTSC. Le banc efface un ancienVINT avant
le delai controle ;les nouveauxVINT restent latchees normalement. Les cas
PALsupplementaires couvrent les latchees absentes de la premiere matrice.
Les suites audio-seule puisIRQcomplete sont exercees. Le caller0B94 est
remplace parEI pour un contexte ;0B95 et ses routines/banques4/6 restent
intacts. Les contextes avecIRQimbriquee,desactivations longues invalides,
NMI,Reset,HINT et autres modes ne sont pas couverts.

Point essentiel du contrat :la capture est a l'entree d'instruction APRES
la decision d'interruption du coeur. Le premierPUSH ne refait donc pas
cette decision. Le drapeauafter_ei a deja ete consomme a ce point ;l'EI
du prologue bloque ensuite le premierLD comme dans le programme original.

Les phases/etats d'entree des attentes,les entrees historique/hasard et la
chronologieIRQ dans le travail de chargement ENTRE les attentes restent
observes. Le chargement entier n'est pas encore predit autonomement depuis
son seul etat initial. Aucun delai natif n'est ajoute,ROMtoujoursv0183.
La progression naturelle complete,les sorties physiquesVDP/PSG et le
materiel reel restent non verifies.

Reproduire :

- python tools/build_wait_raster_core.py
- python tools/validate_wait_raster_prediction.py (captures locales requises)
- python tools/validate_wait_raster_unit.py
- python tools/validate_wait_raster_unit.py --pal-latched
- python tools/validate_wait_predicted_loading_budget.py (captures requises)
- python tools/archive_wait_raster_research.py

Modeles,fixtures,captures et bibliotheque sont conserves localement dans
wait-raster-research-v0183 avec manifeste SHA-256.
