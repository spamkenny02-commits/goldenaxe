# Routines aleatoires traduites en C68000 (2026-10-16)

source_rng.c/source_rng.h traduisent maintenant la recurrence04E1, la
sortie XOR avec R et la progression du registre de rafraichissement.
L'API recoit explicitement R a l'instant LD A,R ; elle ne fabrique pas
cette valeur depuis le compteur de frames Mega Drive. Le bit7 reste
conserve et les sept bits bas progressent modulo128.

La traduction passe les65536graines,196608couples graine/R de sortie et
66816progressions R, dont les grandes valeurs de compte32bits. Le banc
hote compare aux modeles semantiques deja verifies contre la ROM SMS.
La recurrence traite aussi la graine resultante nulle remplacee par733Ch.

Le meme fichier C est compile par SGDK dans une cartouche de test
independante. Le code68000 est execute sous Genesis Plus GX, enPAL puis
enNTSC, avec les memes65536/196608/66816cas et zero echec. Une table des
graines attendues est produite par le modele Python, puis lue par le
programme68000. Les fonctions sont presentes dans les symboles ; le
test desactive leur inlining. Ce banc prouve les valeurs du composant,
pas les timings Z80 ni la progression de jeu.

La ROM de jeu restev0183. Les fichiers existants du jeu sont inchanges ;
les nouveaux helpers ne sont pas encore appeles par la production.
Les jeux continuent donc d'utiliser le hasard SGDK provisoire. Brancher
le helper exige encore la propagation native de R et de la graine avant,
pendant et apres les chargements. Remplacer le hasard par une estimation
de R depuis les frames ne satisferait pas ce raccordement.

L'audit a aussi confirme que les delais actuels reposent sur un budget
fixe et des couts de ressources. Le modele d'instructions16D0..0ACE
precedent peut guider leur remplacement, mais sa phase/R d'entree
restent observees dans les bancs : leur production native doit etre
implementee et verifiee. Autres contextes, fondu/contours, simulation,
materiel reel et partie complete restent ouverts.

Reproduire :

- `python tools/validate_native_source_rng.py`
- `python tools/validate_native_source_rng_68k.py`
- `python tools/archive_native_source_rng.py`

La cartouche sous validation/native-rng-68k est un banc de test, pas
une nouvelle version jouable. L'archive locale conserve sources, table,
objet/assembleur68000, DLL hote, cartouche, symboles, captures et rapports
avec manifeste SHA-256.
