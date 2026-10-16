# Chargement raccorde jusqu'au heros (2026-10-16)

Le modele 16D0..24E7 utilise maintenant uniquement la RAM complete de
8192 octets, R et la phase d'entree du chargement. Le contexte HUD,
l'historique, la persistance, l'equipement et la salle sont derives de
cette RAM initiale. L'etat audio d'entree est verifie identique a sa zone
RAM. Aucune RAM mesuree a l'entree du heros ne sert a la prediction.

La carte de collision est reconstruite depuis la ROM : metatuiles de
classe0, correctifs de portails, metatuiles supplementaires et attributs,
RLE de salle, metadonnees persistantes et transformation secondaire de
case. Ses 1280 octets correspondent sur les 24 scenarios, soit 30720
octets compares. Cette reconstruction est semantique, sans execution
generique de code Z80.

Le modele reconstitue ensuite les champs du loader (banque graphique,
musique demandee, allocation et compte d'acteurs, effacements, historique,
persistance, acteurs), puis execute le RET des acteurs et le CALL du
heros dans le planning de phase. Les 475 octets pertinents d'entree du
heros, ses champs d'equipement lus et la carte de collision correspondent
aux mesures utilisees uniquement comme assertions. Le plan 2C63 deja
verifie prend alors cet etat calcule.

Les 24 parcours passent 1080 comparaisons de points au total jusqu'a24E7.
M1/R, phase, duree, 331 octets RAM, 400 octets audio, historique/persistance,
acteurs et motifs VRAM ecrits restent verifies. Les 72 tirages aleatoires
precedents correspondent directement au registre A. Les 475 octets du
heros au retour correspondent aussi. Les offsets IRQ sont predits et
les traces completes SMS restent identiques a v0179.

Le coeur distinct ajoute une capture complete de RAM a16D0, accompagnee
du timestamp, et conserve les points/captures de sortie precedents.
Les snapshots a2C63/24E7 sont des comparaisons, pas des entrees. Le fichier
C de travail est restaure apres compilation. L'archive locale conserve
outils, captures, references et coeur avec manifeste SHA-256, ainsi que
le banc hero precedent de13150cas comme reference du helper inchange.
ROM v0183 et sources natives inchangees.

Limites : six salles ordinaires de classe0 avec changement de banque,
C0AC=0, C041!=5 au chargement, bit persistant0 actif et contexte HUD de base.
La RAM initiale du chargement reste observee ; le modele ne prouve pas
encore son obtention depuis le lancement du jeu. Il ne revendique pas
la reconstruction de tous les8192octets a chaque point. C01B/C020..23,
sorties hors snapshots et octets VRAM non alloues restent exclus. Autres
classes/boss, commandes audio non couvertes et materiel reel restent
ouverts. Scripts, musique, retour/revelation et integration native des
delais/hasard sont les prochains raccordements. Partie complete non prouvee.

Reproduire :

- `python tools/build_loader_hero_refresh_core.py`
- Capturer les six routes et masques00/FF via
  `profile_paid_passage_loader_phases.main`, repertoire
  `loader-hero-refresh/TT-MM`, coeur
  `genesis_plus_gx_loaderherorefresh_libretro.dll`, `capture_music=True`.
- `python tools/validate_loader_hero_refresh.py`
- `python tools/archive_loader_hero_refresh_research.py`
