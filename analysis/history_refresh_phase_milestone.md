# Tirages de l'historique depuis le debut du chargement (2026-10-16)

Le modele relie maintenant 16D0 a l'entree du chargement des acteurs 1780.
Il prolonge graphismes/carte/HUD/attente/transfert/palette par le caller
24C5, les effacements, les trois essais d'historique 1C25 et la routine
aleatoire 04E1. Les seules entrees mesurees sont celles de 16D0 : R,
raster, RAM, audio, contexte HUD, salle, historique de 16 octets et
persistance de 256 octets. La graine C028 fait partie de la RAM initiale.

Les decisions CPIR, l'insertion de la salle dans l'historique, les graines
suivantes, le registre R lu par LD A,R et les octets tires sont calcules.
Aucun tirage, position de recherche, graine ou registre R intermediaire
observe n'alimente le modele. La routine 04E1 utilise sa recurrence native
et des plans d'instructions explicites ; ce n'est pas un interpreteur Z80.
Le planning des IRQ audio reste actif pendant ce travail.

Les 24 scenarios controles passent 30 points chacun (16 precedents plus
14 pour l'historique), soit 720 comparaisons. Les 72 octets rendus par la
routine aleatoire correspondent directement au registre A observe avant
RET. HL contient aussi la graine attendue aux points 04F7 et 04FD. Les
deltas M1, R, durees, phase, 331 octets RAM et 400 octets audio correspondent,
ainsi que l'historique et les 256 octets de persistance. Les offsets IRQ
correspondent et les traces SMS completes restent identiques a v0179.

Ces parcours produisent 31 octets aleatoires distincts. Les graines suivent
26509 -> 53018 -> 40500 -> 15464 ; les sorties different avec R selon les
timings du chargement. Les 72 recherches aleatoires manquent l'historique
et trouvent un octet de persistance FF. Les branches de correspondance et
de drapeau nul ne sont donc pas prouvees par cette couverture, meme si le
modele les exprime. Le remplacement de graine nulle n'apparait pas ici ;
la recurrence et le helper R disposent de leurs bancs isoles precedents.

Le coeur distinct observe les points ajoutes et un contexte de 277 octets :
salle2, historique16, persistance256, A1 et HL2. Les registres A/HL servent
uniquement a comparer les sorties, pas comme entrees de prediction.
Le fichier C de travail est restaure apres compilation. L'archive locale
conserve outils, captures, references et coeur avec manifeste SHA-256.
La regression du prefixe carte/HUD passe ses 24 scenarios.

Limites : parcours classe 0, C0AC=0, C041!=5, bit persistant 0 actif et
contexte HUD de base. C01B/C020..23 et les buffers d'effacement hors des
snapshots compares ne sont pas verifies. VRAM/palette/SRAM hors snapshots,
autres classes et commandes audio non couvertes restent ouverts. La
convention d'acquittement du coeur local n'est pas une preuve materielle.
Les acteurs, le heros et la fin du chargement restent a enchainer avant
integration du hasard et des delais natifs. La partie complete reste a
valider. ROM v0183 et sources natives inchangees.

Reproduire :

- `python tools/build_history_refresh_core.py`
- Capturer les six routes/masques 00/FF via
  `profile_paid_passage_loader_phases.main`, repertoire
  `history-refresh/TT-MM`, coeur
  `genesis_plus_gx_historyrefresh_libretro.dll`, `capture_music=True`.
- `python tools/validate_history_refresh_phase.py`
- `python tools/validate_map_hud_refresh.py`
- `python tools/archive_history_refresh_research.py`
