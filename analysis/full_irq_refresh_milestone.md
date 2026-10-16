# Lectures d'opcodes des interruptions video (2026-10-16)

Le modele de l'interruption complete 0137..01E2 compose maintenant les
lectures M1 avec les couts et l'etat memoire deja verifies. Les neuf parties
couvrent les deux transferts de sprites, les motifs, le HUD, la palette,
la file graphique, le mapping audio, le lecteur et les entrees/compteurs.
Le registre R conserve son bit 7 et progresse modulo 128 pour chaque lecture.

Les 2 880 cas controles PAL/NTSC passent avec le meme fixture que le banc
de cout precedent : branches de palette/HUD, pause, compteur de delai,
boutons precedents et compensation. Les neuf deltas M1/R, les durees,
les 336 octets RAM et les 400 octets audio correspondent. Les boucles de
palette sont predites depuis la phase raster d'entree et le cout du prefixe,
sans utiliser leur nombre observe comme entree du modele.

Les 24 parcours de passages payants, six routes avec masques 00/FF et
PAL/NTSC, passent 13 749 interruptions completes. Les transferts SAT
consomment 155 et 262 lectures, les motifs 4 ou 248, le HUD 7 ou 141,
et les files graphiques 14, 94 ou 447 sur ces captures. Le lecteur audio
est compose depuis son etat d'entree et ses commandes prises en charge.
Les anciens enregistrements RAM/cout et lecteur restent identiques octet
par octet ; les traces SMS completes restent identiques aux references v0179.

Le coeur d'observation conserve les dix points M1/R et la phase raster
d'entree dans un enregistrement de 152 octets. Il ajoute uniquement des
compteurs et des lectures d'etat au coeur local, sans modifier ses timings
ni sa convention d'acquittement IM1. Son fichier source de travail est
restaure apres compilation dans une DLL distincte.

Limites : les points s'arretent avant le RET final. Le vecteur et le RET
sont comptes depuis les instructions originales et verifies par les
bancs precedents ; cette capture ne prouve pas un increment R materiel a
l'acquittement. Les autres combinaisons de files, de motifs et de commandes
audio ne sont pas exhaustivement couvertes. Les entrees R, raster, boutons
et etats RAM restent des donnees observees. La propagation de R dans le
chargement hors interruptions, les acteurs et l'historique restent a
composer avant de remplacer le hasard provisoire dans le portage natif.
Pas de preuve de partie complete ni de materiel reel.

ROM v0183 et sources natives inchangees. Reproduire :

- `python tools/build_full_irq_refresh_core.py`
- `python tools/validate_full_irq_refresh.py` (fixture du banc full_irq_unit)
- Capturer les six routes et masques 00/FF avec
  `profile_paid_passage_loader_phases.main`, repertoire
  `full-irq-refresh-live/TT-MM`, coeur
  `genesis_plus_gx_fullirqrefresh_libretro.dll`, `capture_music=True`.
- `python tools/validate_live_full_irq_refresh.py`
- `python tools/archive_full_irq_refresh_research.py`

L'archive locale conserve les outils, fixture, captures, references,
rapports et coeur avec manifeste SHA-256.
