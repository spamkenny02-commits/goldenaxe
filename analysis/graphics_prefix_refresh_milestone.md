# Registre R pendant le chargement des motifs (2026-10-16)

Le trajet 16D0..1706 calcule maintenant le registre R depuis un seul etat
d'entree, avec le planning des interruptions audio deja predit par la phase
video. Il comprend la selection de classe, le changement de banque, la
copie de palette et le decodage RLE des motifs. Les lectures de chaque
instruction sont composees avec celles du lecteur et du corps des IRQ.

Les 24 scenarios de passages payants, six routes, masques 00/FF et deux
regions, correspondent pour les lectures M1, le registre R final, les
durees, les 331 octets RAM compares et les 400 octets audio. Les premieres
entrees R/raster/RAM/audio sont observees ; aucune valeur intermediaire de
R ou d'interruption n'est fournie au modele. Les offsets IRQ sont predites
et compares aux observations.

Le trajet execute 122 703 lectures M1 hors interruptions. Les parcours
NTSC ajoutent 5 484 lectures pour 15 IRQ audio ; les parcours PAL en
ajoutent 5 604 pour 13 IRQ. Le delta du compteur global et le registre R
correspondent aux deux points de controle dans les 24 cas. Les anciens
enregistrements de phase/RAM/audio restent identiques octet par octet et
les traces SMS completes correspondent aux references v0179.

Le plan distingue explicitement RES 7,B (deux lectures, 8T) du dernier
DJNZ d'une boucle (une lecture, 8T). Les noeuds 16/21T de ce plan sont
LDI/LDIR et les noeuds 20T ED53/ED5B. Ce compte est propre au plan audite,
pas une conversion generale entre duree et nombre de lectures. R conserve
son bit 7 et evolue modulo 128. Le point initial est apres la premiere
lecture de l'instruction ; le point final a deja lu le premier opcode de
l'instruction suivante. Le modele respecte cette convention.

Limites : uniquement classe 0 avec changement de banque et affichage
desactive. C01B et C020..23 ne sont pas compares ; VRAM/palette non
modelisees ici. La convention GPG locale d'acquittement IM1 reste inchangee,
sans revendication sur son exactitude materielle. Le reste du chargement,
les acteurs et l'historique doivent encore propager R avant integration
du hasard et des delais natifs. Autres commandes audio, classes graphiques
et partie complete non prouvees. ROM v0183 et sources natives inchangees.

Reproduire :

- `python tools/build_graphics_prefix_refresh_core.py`
- Capturer les six routes et masques via
  `profile_paid_passage_loader_phases.main`, repertoire
  `graphics-prefix-refresh/TT-MM`, coeur
  `genesis_plus_gx_graphicsprefixrefresh_libretro.dll`, `capture_music=True`.
- `python tools/validate_graphics_prefix_refresh.py`
- `python tools/validate_graphics_prefix_phase.py` pour la regression du plan.
- `python tools/archive_graphics_prefix_refresh_research.py`

L'archive locale conserve les outils, captures, references, coeur et
rapports avec manifeste SHA-256. Le fichier C de travail du coeur est
restaure apres compilation de la DLL distincte.
