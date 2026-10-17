# Decodage natif des motifs SMS 032A — v0198

Le decodeur a quatre plans est maintenant partage entre le jeu et les
controles natifs (`source_pattern.c`). Les autres grammaires de cartes,
a un ou deux plans, gardent leur routine distincte. Aucun CPU Z80 n'est
execute par la ROM Mega Drive.

L'API peut fournir les totaux de travail Z80 T/M1 de 032A : commandes,
copies litterales/repetitions, DJNZ avec B=0 (256 octets), retenues de
destination et appels RST28. La destination SMS est explicite pour calculer
ces retenues. Le chemin utilise par le jeu ne demande pas ces compteurs.

515 vecteurs passent en C hote et en 68000 PAL/NTSC, avec et sans mesure.
Ils comprennent les motifs exterieurs reels a ROM3C010, des flux vides,
des litteraux de 256 octets et des flux generes avec une graine fixe.
L'hote compare tous les octets et les pointeurs de fin ; le noyau 68000
compare un hash FNV32 du tampon complet, le pointeur et les compteurs.
Les totaux T/M1 sont compares au modele d'instructions deja utilise par
les preuves de chargement ; ce jalon n'ajoute pas de capture source
independante. Voir `native_patterns_report.json` et
`native_patterns_68k_report.json`.

Reproduction : `python tools/validate_native_patterns.py`, puis
`python tools/validate_native_patterns_68k.py`. Le second compile une
cartouche de controle separee avec SGDK et attend son indicateur de fin.

La v0198 conserve 1 Mio. Les controles naturels des bruitages de selection
et de validation, puis des entrees/sorties d'inventaire dans l'exterieur
et les deux premieres maisons, sont compares a la SMS et a v0194.
Les rapports sont archives avec la ROM numerotee. Les trois parcours NTSC
ont les memes fenetres noires et la meme image de reprise que la SMS.
En PAL, les images capturees sont identiques a v0194 ; les fins de noir
restent decalees d une image face a la SMS. Le controle strict
validate_menu_transitions demeure donc non satisfait en PAL.

Ce changement prepare le chargement a fournir son travail a l'horloge.
Les totaux ne constituent pas une chronologie d'interruptions : RST28
inclut DI/EI et exige encore un raccordement instruction par instruction.
Le raccordement global de l'horloge, les autres etapes du chargement et
la validation d'une partie naturelle complete restent ouverts.

Le controle des transitions a detecte un noir commence une image trop tard
a la sortie de l'inventaire. Ce resultat se reproduit avec le binaire
archive v0194 : il ne provient pas du nouveau decodeur. La v0198 publie
le noir avant l'attente de VBlank en NTSC, puis charge les motifs.
La publication PAL conserve son attente prealable pour eviter un noir
trop precoce, observe avec la v0197 intermediaire. La duree totale
de la transition reste calculee depuis le meme instant. Les versions
intermediaires v0195/v0196/v0197 sont conservees avec le controle non satisfait.
Le chemin rapide sans comptage evite aussi les calculs de mesure dans
la boucle interne du decodeur utilisee par le jeu.

Suite : l audit du chemin chronometre a corrige cinq lectures M1 manquantes
(quatre ED53 et un ED5B). Les rapports racine et les 515 vecteurs corriges
font autorite ; l archive precedente reste historique. Le premier chemin
16D0..1706 retrouve maintenant les captures SMS avec son horloge et ses
interruptions dynamiques. Voir native_graphics_prefix_milestone.md.
