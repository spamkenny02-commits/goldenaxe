# Graphismes des acteurs et registre R (2026-10-16)

Le calcul depuis 16D0 atteint maintenant 18E1, l'entree du RET du loader
d'acteurs. Il ajoute l'allocation des motifs, la recherche des types deja
charges, le decodage RLE et la conversion de palette 1D0D a l'initialisation
des types/statistiques/persistance deja verifiee. Les 768 octets d'acteurs
sont mis a jour avec les indices de motifs alloues ou partages.

La conversion de palette est decrite instruction par instruction, avec
DI/EI autour des lectures VDP, les 32 INI par tuile du coeur local (20T),
l'extraction des couleurs et la reconstruction des quatre plans. Les
instructions ED et CB sont comptees explicitement, notamment OUT(C),r,
SLA/SRL(HL), SBC HL,DE et les rotations. Le RLE reutilise le plan 032A
avec ses effets sur les interruptions et C031.

Les 24 scenarios passent 936 comparaisons au total, dont les nouveaux
points avant/apres RLE, apres conversion et au retour des acteurs.
M1/R, phase, duree, 331 octets RAM, 400 octets audio et 768 octets d'acteurs
correspondent. Les 72 tirages d'historique precedents restent verifies.
Les offsets IRQ et les traces completes SMS correspondent a v0179.

Le coeur observe aussi les 8192 octets VRAM a partir de 2000 au retour
18E1, avec l'allocation C067 et le timestamp. Seule la region effectivement
allouee est comparee : 19 648 octets cumules sur les 24 scenarios, avec
les motifs et palettes calcules depuis la ROM par la reference semantique.
Les octets non alloues peuvent conserver des graphismes anterieurs ; ils
ne sont pas revendiques comme sorties de ce loader.

Les 1 536 combinaisons des six salles et des 256 masques passent aussi
dans la fixture originale de cout des acteurs : loader complet, M1/R,
durees, 768 octets, compte actif, allocation et region VRAM ecrite. Les
masques mixtes couvrent le partage de types deja charges et les conversions
de palette. Le caller desactive les IRQ ; leur planning est verifie sur
les parcours en jeu, pas par une phase artificielle dans ce banc.

Le modele partage les phases d'interruption precedentes et les donnees
ROM ; il n'execute pas d'instructions Z80 generiques. Un coeur distinct
observe les points et motifs, puis son fichier C de travail est restaure.
Outils, fixture, captures, references et coeur sont archives localement
avec manifeste SHA-256. ROM v0183 et sources natives inchangees.

Limites : six salles ordinaires, classe 0 et contexte HUD de base ; boss
et autres classes restent ouverts. C01B/C020..23 et les buffers RAM hors
snapshots ne sont pas compares. Les motifs VDP sont compares au retour,
pas a chaque ecriture. Convention GPG INI/acquittement conservee sans
preuve materielle. Heros, scripts, musique et fin du chargement doivent
encore etre raccordes avant integration native du hasard et des delais.
Les commandes audio non couvertes et la partie complete restent ouvertes.

Reproduire :

- `python tools/build_actor_graphics_refresh_core.py`
- Capturer les six routes/masques 00/FF via
  `profile_paid_passage_loader_phases.main`, repertoire
  `actor-graphics-refresh/TT-MM`, coeur
  `genesis_plus_gx_actorgraphicsrefresh_libretro.dll`, `capture_music=True`.
- `python tools/validate_actor_graphics_refresh.py`
- `python tools/validate_actor_graphics_refresh_unit.py`
- `python tools/archive_actor_graphics_refresh_research.py`
