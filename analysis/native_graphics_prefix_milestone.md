# Chargement graphique 16D0..1706 : horloge native

`source_pattern_clock.c` traduit le premier chemin de chargement des motifs
exterieurs : classification avec changement de banque, requete musicale B0,
copie de palette et decompression 032A. Chaque instruction originale avance
`SourceClock`. Les appels RST28 conservent leurs DI/EI, les instructions ED
leurs deux lectures M1, et la fin de chaque plan met a jour C031/C032.
Les interruptions utilisent `SourceIrqContext` et le lecteur audio natif
avec leur etat courant. Aucun budget moyen ni tableau de phases par salle
n'intervient dans cette traduction.

Les 24 entrees source controlees (six passages, deux masques, PAL/NTSC)
retrouvent au point 1706 : phase raster, duree, R, M1, 331 octets de RAM,
400 octets audio et tous les instants d'acceptation des interruptions.
Chaque parcours comprend 868344 T et 122703 M1 de premier plan ; le travail
audio et ses dates varient selon l'etat initial. Les snapshots et traces
SMS precedents restent identiques aux originaux. Une seule entree 16D0
est fournie pour chaque parcours ; aucun etat intermediaire n'est reinjecte.

Les memes 24 vecteurs passent en code 68000 compile, dans les deux regions,
avec zero echec. Les autres champs du noyau (dont les details du journal
IRQ non exposes par les snapshots) sont controles par parite avec l'hote.
Le tampon de pixels et le pointeur de fin sont egalement verifies contre
le decodeur de reference, par hash FNV32 dans les noyaux 68000.

L'audit a corrige une erreur du jalon de decompression precedent : quatre
ED53 et un ED5B etaient comptes comme une seule lecture M1 chacun. Le total
de ce composant manquait cinq M1 ; les T et les pixels etaient corrects.
Le test hote precedent partageait cette erreur. Il utilise desormais la
classification M1 du modele audite, et le nouveau chemin d'horloge est
confronte aux compteurs M1/R reels des captures SMS. Les 515 vecteurs du
decodeur sont repasses sur hote et 68000 PAL/NTSC apres correction.
L'ancienne archive `native-patterns-v0198` est historique ; les rapports
racine corriges et la nouvelle archive font autorite pour ces compteurs.

Reproduction :

- `python tools/validate_native_patterns.py`
- `python tools/validate_native_patterns_68k.py`
- `python tools/validate_native_graphics_prefix.py`
- `python tools/validate_native_graphics_prefix_68k.py`

La recompilation du jeu produit exactement la ROM v0198 existante,
SHA256 c7d010987bee974547b25d5d5734c666c2f684603972b1e4159a8dd584087818.
Le chemin d'horloge n'est pas encore raccorde au jeu. Le chemin rapide
de decodage utilise par le jeu est inchange ; aucune ROM supplementaire
n'est creee pour des octets identiques.

Portee restante : le reste du chargement, les classes graphiques autres
que ce changement class0, la propagation de phase depuis le demarrage,
les uploads physiques/conflits VRAM, puis la boucle globale du jeu.
Les differences PAL de transitions documentees en v0198 restent ouvertes.

Suite : le chemin class0 couvre maintenant16D0..24B9 sur une seule horloge,
avec six points source et des captures independantes des donnees graphiques.
Voir native_graphics_load_milestone.md ; le raccordement global reste ouvert.
