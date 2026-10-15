# Attentes VBlank et budget de chargement (ROMv0183 inchangee)

Le modele de travail0B95..0BB3 compte170T avantEI,puis4T pourEI,
29T par branche de scrutation prise et24T pour la derniere iteration.
Les22 octets de sauvegarde sur la pile,le retourC02E=0 et l'avanceC02F
exactement une fois sont controles. Les compteurs de branches sont des
entrees observees ;leur valeur future n'est pas encore predite.

Les six passages payants,en PAL/NTSC et avec masque de monstres00/FF,
produisent24 scenarios :13725 appels d'attente et14424 appels du lecteur
audio entier. Tous correspondent aux modeles pour les grandeurs controlees.
Le lecteur compare400 octets,DE et cycles ;l'attente compare cout horsIRQ,
prefixe avantEI,pile et drapeaux/horloge. L'observateur ajoute des compteurs
externes sans modifier les instructions de la ROM ;les tableaux complets
de cycles sont identiques aux referencesv0179 pour les24 cas.

Les etats d'entree du heros sont identiques aux captures precedentes.
En ajoutant les deux attentes mesurees par leurs decisions de boucle aux
modeles de graphismes,carte,HUD,historique,acteurs,heros,script,musique et
revelation,le travail complet16D0..0ACE correspond sans residu. Le travail
jusqu'a1FA7 est aussi controle. Les anciens intervalles0B95..0BB3 ne sont
plus exclus du bilan hors interruptions.

Les interruptions consacrees a l'audio pendant le chargement sont calculees
avec le lecteur independant et le cout du wrapper/vecteur/retour. Le travail
des interruptions completes reste mesure. Leur somme reconstruit exactement
le tempsIRQ total observe sur les24 scenarios. Ce bilan n'est donc pas
encore une prediction autonome de la duree physique :phase VBlank,decisions
de scrutation,IRQcompletes,entrees historique/hasard proviennent des captures.

Aucune modification native,aucun delai ajoute,ROMtoujoursv0183. Restent le
travailVDP/entrees/palette et l'attente de compteur video des IRQcompletes,
la phase future des interruptions,puis l'integration des timings natifs.
Les autres classes graphiques,etats d'histoire,boss,commandes audio ouvertes,
progression naturelle complete et materiel reel restent non verifies.

Reproduire :

- python tools/build_save_wait_core.py
- python tools/validate_save_wait_foreground.py (captures locales requises)
- python tools/archive_save_wait_research.py

Sources de mesure,fixtures,captures et bibliotheque sont conservees dans
save-wait-research-v0183 avec manifeste SHA-256.
