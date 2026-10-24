# Chaine native jusqu'au devoilement complet - 24 octobre 2026

source_room_contours traduit1FB6..2002, avant le RET final :16 contours lus dans
la table2011, deux attentes0B95 par contour, puis copie de ses quatre cotes.
Les mots suivent l'ordre source : haut vers la droite, cote droit vers le bas,
bas vers la gauche, cote gauche vers le haut. Chaque mot relit le D600 vivant,
latch l'adresse VDP avec le DI/EI original et livre ses deux octets au miroir.

La chaine commence au meme16D0 que les etapes precedentes : graphismes, carte,
HUD, historique, ennemis, heros, scripts, musique, noir, rallumage, fondu puis
contours. L'horloge, la graine et la memoire ne sont pas reinjectees entre etapes.
Les copies video des IRQ sont actives pendant les attentes.

Validation :

-24 parcours source, six destinations exterieures ordinaires classe0, masques00/FF,
 NTSC/PAL.2 544 points comparent phase/temps/R/M1,331 octets RAM,400 audio et tous
 les decalages IRQ.48 points aux retours1FB6/2002 comparent temps et C02F.
 La carte VRAM finale3800..3DFF contient les1536 octets du D600 vivant.
-48 executions compilees68000 de la chaine passent,24 par region physique.
-64 cas directs du code Z80 original : quatre cartes completes de motifs,
 quatre selections HUD, palette active/sautee, deux regions. Toute la VRAM16KiB,
 RAM331/audio400 et le temps/M1/R finaux concordent. Le JP d'entree et le
 RET/JP de sortie du banc sont explicitement inclus dans la comparaison.

Un mot stable represente139T/17M1. Lorsqu'aucune interruption ne peut intervenir,
ce travail est regroupe, puis les octets sont publies avant l'operation suivante.
Le chemin instruction par instruction reste actif aux frontieres d'IRQ. Le meme
banc68000 passe de8947 a6544 images d'execution NTSC, et7490 a5479 PAL (-26,85 %).
Les vecteurs sont identiques et seul source_room_contours.c differe du temoin.
Ce sont des durees CPU de diagnostic, avec IRQ materielles desactivees, pas des
FPS du jeu ou une preuve de cadence physique. Temoin et vecteurs sont archives.

La chaine demeure hors du chemin jouable. Publication SGDK, cadence physique,
origine globale, autres classes/entrees et campagne complete restent ouverts.
Les plages graphiques source deja observees sont comparees dans la chaine ;
les autres octets de miroir en68000 ont une concordance hote, completee par les
64 cas directs ci-dessus. Cette validation ne prouve pas les instants physiques
par octet. La ROM jouable reste v0275 ; aucune version artificielle n'est creee.

Rapports : native_room_contours_report.json, native_room_contours_68k_report.json,
native_contours_unit_report.json et native_room_contours_performance_report.json.
