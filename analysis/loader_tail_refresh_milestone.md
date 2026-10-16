# Chargement jusqu'a la reactivation de l'ecran (2026-10-16)

Le modele de16D0 atteint maintenant0ACE, apres le heros, la mise en place
des scripts5B20, le choix musical1CAF, le retour24ED et la preparation de
revelation1FA7/0AA4. Il comprend l'effacement video, les copies de palette,
l'attente VBlank0B95, la restauration et l'activation de l'affichage.
Seule la RAM initiale8192octets, R et la phase de16D0 sont fournis.

Le script derive ses pointeurs de salle depuis la ROM, copie le contact
du heros, conserve sa direction et traite le compte d'acteurs vide.
La musique derive sa commande de la table1D02 et ne la redemande que si
elle change. L'ecriture DE06 intervient a son point d'instruction dans
le planning : les IRQ audio suivantes lisent cet etat calcule.

Les24scenarios passent1320comparaisons de points, avec M1/R, durees,
phase,331octets RAM et400octets audio. Les72tirages d'historique, les
acteurs, les motifs VRAM ecrits, la collision et le heros restent verifies.
Une capture complete a0ACE compare aussi les pointeurs DCE0..DCE5,
C060..C065 et les champs de script C0A4/C0A5/C0A8. Les offsets IRQ
correspondent et les traces completes SMS restent identiques av0179.

Les24cas demandent la commande82h depuis l'ancienne commandeB0h.
La branche de salle speciale84h et la suppression d'une commande inchangee
ne sont pas prouvees par ces parcours. Les masques00/FF couvrent les
branches du compte d'acteurs vide ou non vide dans5B20.

La revelation distingue SET5,E etSET6,E (deux lecturesCB) des DJNZ
terminaux de meme duree8T. L'attente predit ses tours et les interruptions
depuis la phase et R calcules, puis son resultat alimente la restauration.
Le chemin temporel par defaut de revelation passe a nouveau ses24cas.
Le point0ACE precede le fondu et les16contours de revelation : cette
etape ne pretend pas compter leur animation ulterieure.

Le coeur distinct conserve la RAM initiale et ajoute une capture RAM
complete a0ACE, uniquement pour comparer les sorties. Les outils,
captures, references et coeur sont archives localement avec manifeste
SHA-256 ; le fichier C de travail est restaure apres compilation.
ROMv0183 et sources natives inchangees.

Limites : six sorties ordinaires de classe0, contexte HUD de base,
bit persistant0 actif et absence de suppression de boss. L'etat initial
du chargement reste observe. C01B/C020..23, buffers hors snapshots et
VRAM non allouee restent exclus. Le modele ne reconstruit pas chaque
octet des8192octets a tous les points. Autres classes, commandes audio
non couvertes, acquittement/INI sur materiel reel et partie complete
restent ouverts. L'integration68000 et la propagation de R avant/apres
cette chaine, notamment le fondu/contours et la simulation de jeu,
restent a realiser et verifier.

Reproduire :

- `python tools/build_loader_tail_refresh_core.py`
- Capturer les six routes et masques00/FF via
  `profile_paid_passage_loader_phases.main`, repertoire
  `loader-tail-refresh/TT-MM`, coeur
  `genesis_plus_gx_loadertailrefresh_libretro.dll`, `capture_music=True`.
- `python tools/validate_loader_tail_refresh.py`
- `python tools/validate_reveal_phase_prediction.py`
- `python tools/archive_loader_tail_refresh_research.py`
