# Attente, transfert et palette : chaine native 16D0..24BF

La preparation graphique, les cases et le HUD sont maintenant suivis par
229C/0B95, la restauration 0BB3..0BC5, le transfert 22A3 et la palette 1DEB.
Une seule horloge et un seul contexte IRQ/audio sont conserves depuis 16D0
jusqu'a 24BF. Les 16 points SMS retrouvent durees, raster, R/M1, 331 octets RAM,
400 octets audio et tous les instants/categories d'interruption sur les 24
contextes controles. Cela inclut l'IRQ video complete de l'attente, son nombre
de tours de polling et les retours reels 0BB3/22A3 sans double prefetch.

Les 24 vecteurs passent egalement en 68000 compile PAL/NTSC. Un nouvel
observateur source confirme directement les 1536 octets du name table VRAM
3800..3DFF et les 16 octets de palette RAM DCB0..DCBF au point24BF. Les anciens
records de phase restent identiques, ainsi que R et les deltas M1.

Le transfert OUTI/DJNZ decremente B deux fois par octet : 12 groupes de 128
octets. Les interruptions y sont coupees. Le nouvel API
`source_clock_repeat_disabled` regroupe les blocs stables meme a travers
VINT, conserve l'etat pending et laisse le IN status final l'acquitter.
Les anciens octets du fichier source_clock.c restent un prefixe exact ;
l'API ajoutee ne remplace pas les chemins d'horloge deja verifies.
640 contextes de raster/R/pending/region et durees sont compares au pas
instructionnel lent, avec sept gardes de rejet sans mutation. Ces controles
passent aussi en 68000 dans les deux regions, zero echec.

La palette est aussi accessible separement. Les 2048 combinaisons de
clignotement, selection 0..3 et compteur 0..255 executent les instructions
originales 1DEB, avec un retour de controle vers 24BF. Les 16 octets, T, M1 et R
concordent avec le natif dans les deux regions ; les 2048 vecteurs passent
ensuite en 68000 PAL/NTSC. Le source n'est modifie qu'au boot/retour marqueur,
les instructions de preparation de palette restent intactes.

Reproduction :

- `python tools/validate_native_room_finish.py`
- `python tools/validate_native_room_finish_68k.py`
- `python tools/build_roomfinish_data_core.py`
- `python tools/validate_roomfinish_source_data.py`
- `python tools/validate_clock_disabled_repeat.py`
- `python tools/validate_native_palette.py`
- `python tools/validate_finish_units_68k.py`

Les tampons logiques appartiennent au caller : la carte transferee occupe
patterns+3800, la palette cells+B0, comme dans la memoire source. L'API ne
remplace pas les uploads physiques SAT/CRAM ni le renderer Mega Drive.
L'IRQ video native calcule ses etats/couts ; ce jalon ne prouve pas tous ses
effets physiques VRAM. Les captures independantes couvrent les plages citees.

Le scope reste class0, six destinations, changement de banque, C0AC=0,
C041!=5, bit0 sauvegarde positionne, mode 4/VINT sans NMI/reset/interlace.
Les cinq octets status/joy exclus du comparatif RAM ne deviennent pas
implicitement verifies. Les entrees de phase/R/RAM/audio/HUD restent observees,
sans reinjection entre les 16 points. Le test de palette isole desactive IRQ ;
la chaine precedente valide leur ordonnancement dynamique.

La recompilation conserve les octets exacts de v0198. Le raccordement global
reste ouvert : autres classes/branches, suite acteurs/heros/historique/RNG,
phase issue du demarrage et budget temps reel. Les noyaux de verification
ne prouvent pas a eux seuls le debit reel du jeu. Le regroupement des blocs
sans IRQ est une premiere reduction de ce cout, pas une validation globale.
