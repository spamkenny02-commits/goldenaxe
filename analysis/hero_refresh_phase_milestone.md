# Phases et registre R de l'initialisation du heros (2026-10-16)

La routine 2C63..24E7 dispose maintenant d'un plan d'instructions complet
pour les timings, les lectures M1 et R. Il comprend les champs initiaux,
la pose 369F, l'effacement auxiliaire, defense/attaque, les tuiles de
contact, l'eau, la classification du terrain et les drapeaux d'amulette.
Les recherches CPIR et les branches sont calculees depuis les donnees ROM
et l'etat d'entree du heros.

Les 24 parcours controles passent six points chacun, soit 144 comparaisons
de M1/R, phase, duree, 331 octets RAM et 400 octets audio. Le retour compare
475 octets pertinents du heros et des collisions. Les offsets IRQ sont
predits et compares ; les traces SMS completes restent identiques a v0179.
Les snapshots de 8192 octets a l'entree et au retour proviennent du coeur
de lecture deja utilise par le banc semantique precedent.

Le banc isole reutilise sa fixture originale : 6 575 cas par region,
13 150 au total. Ils correspondent pour duree, M1, R et les 475 octets.
Les dimensions comprennent classes0/1/2, six anciens terrains, 17 objets
selectionnes, quatre directions, bornes d'equipement et de malediction,
tables de classification, eau/amulette/attributs et positions fines/bords.
Elles varient independamment, pas selon leur produit cartesien complet.
Les IRQ y sont desactivees ; aucune equivalence de phase n'est revendiquee
pour le descripteur virtuel du banc isole. Le planning des IRQ est compare
sur les parcours en jeu.

Le modele marque explicitement les instructions CB/ED : SET/RES sur les
collisions, rotations et tests de pose, ADD IY,BC et CPIR. Les LD(nn),HL
de 16T restent ordinaires, les LDI de copie de contact sont prefixes. Les
etats semantiques sont derives du modele hero_initialization_cost depuis
les entrees, sans lire les sorties mesurees comme donnees de prediction.

Limite centrale : ce modele commence avec la RAM complete, R, raster et
audio observes a 2C63. Il n'est pas encore raccorde au modele depuis16D0.
Il faut reconstruire les donnees initiales du heros et les tuiles de
collision a partir des sorties semantiques du chargement precedent. Une
comparaison independante de cette routine ne prouve pas ce raccordement.
Scripts, musique, retour/revelation et integration native restent a faire.

Autres limites : C01B/C020..23 exclus des snapshots compares, sorties
video non comparees ici, commandes audio non couvertes, convention GPG
d'acquittement non prouvee sur materiel. La partie complete reste ouverte.
ROM v0183 et sources natives inchangees. Outils, fixture, captures et coeur
distinct archives localement avec manifeste SHA-256 ; fichier C de travail
restaure apres compilation.

Reproduire :

- `python tools/build_hero_refresh_core.py`
- Capturer les six routes/masques 00/FF via
  `profile_paid_passage_loader_phases.main`, repertoire `hero-refresh/TT-MM`,
  coeur `genesis_plus_gx_herorefresh_libretro.dll`, `capture_music=True`.
- `python tools/validate_hero_refresh_phase.py`
- `python tools/validate_hero_refresh_unit.py`
- `python tools/archive_hero_refresh_research.py`
