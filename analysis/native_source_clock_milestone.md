# Horloge d'instructions en C68000 (2026-10-16)

source_clock.c/source_clock.h portent maintenant le mecanisme de phase
et de progression R du modele Python. Les routines traduites fourniront
les Tstates et lectures M1 de chaque instruction, avec les effets DI,
EI et lecture du statut VDP. L'horloge conserve la phase raster modulo
la frame, le prochain VINT, le latch pending, l'inhibition apres EI,
les budgets foreground/IRQ et R.

Un callback recoit la phase, le temps et R a l'entree0137. Il doit fournir
le travail complet de l'interruption depuis l'acceptation jusqu'au RET,
calcule depuis son vrai etat RAM/audio. Une absence de callback ou des
couts invalides fait echouer l'etape ; aucun cout moyen n'est substitue.
La lecture de statut du vecteur a35T gere la coalescence, et une lecture
de statut foreground gere la suppression lors du passage a la ligne193.
La convention IM1 GPG locale est conservee, sans increment R supplementaire
d'acquittement materiel revendique.

Les tests hote comparent18valeurs par scenario au modele de phase/R deja
verifie : raster, delai VINT, duree, budgets T/M1, R, IFF/latch/EI, compte
d'interruptions, suppressions/coalescences et sommes des entrees IRQ.
Ils passent7664scenarios valides et5rejets. Les cas comprennent les deux
longueurs262/313lignes, les deux bits7 de R, les bornes de VINT, les
etats IFF/EI/latch, les effets de statut et64sequences longues qui traversent
plusieurs frames.480cas suppriment un VINT,340 coalescent une assertion
pendant le vecteur et3752acceptent au moins une interruption.

Le chemin courant evite les divisions32bits : additions, comparaisons et
soustractions suffisent pour les instructions et IRQ de moins d'une frame.
Les sommes et R restent identiques sur tous les cas apres optimisation.
Cette optimisation du composant ne mesure pas encore la vitesse du jeu.

Le meme C, sans inlining, est execute dans une cartouche SGDK independante
enPAL etNTSC. Les7669cas terminent avec zero echec et5rejets dans chaque
region. Les attentes sont generees depuis le modele Python, pas depuis
le code C teste. Les sequences longues ont necessite une execution plus
longue que le premier budget du banc ; les compteurs ont confirme leur
progression sans echec avant l'execution complete.

Limites : le callback du banc utilise un cout constant derive du lecteur
audio en pause et du wrapper deja verifies. La traduction des couts et
mutations audio/IRQ dynamiques en C reste a faire. Les plans d'instructions
sont synthetiques ; ils testent le mecanisme, pas encore une transition de
jeu executee par ce C. Seul le mode4/192,VINT actif,HINT inactif est pris
en charge. Horloge et noyau RNG ne sont pas branches dans la production.
Les routines existantes du jeu et la ROMv0183 restent inchangees ; les
nouveaux helpers C sont additionnels. Le hasard SGDK et les budgets fixes
ne sont donc pas encore remplaces. Materiel reel et partie complete restent
ouverts.

Reproduire :

- `python tools/validate_native_source_clock.py`
- `python tools/validate_native_source_clock_68k.py`
- `python tools/archive_native_source_clock.py`

Sources, reference Python, donnees de cas, DLL hote, cartouche, symboles,
captures et rapports sont archives localement avec manifeste SHA-256.
La cartouche de validation est un banc, pas une nouvelle ROM jouable.
