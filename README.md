# Golden Axe Warrior — portage Mega Drive

Reconstruire Golden Axe Warrior à partir de la ROM Master System fournie,
puis porter sa logique Z80 en code natif 68000 avec SGDK. La fidélité à la
Master System passe avant les améliorations.

<!-- ROM-RELEASE:START -->
**Version courante : v0203 — 1024 Kio.**

[Télécharger la ROM v0203](versions/v0203-7660a4b5/gaw-megadrive-v0203.bin) · [Toutes les versions](versions/README.md)

Contrôles ciblés réussis ; portage complet encore non validé.

SHA-256 : `7660a4b5949d0f3362c4795ed5eb238f86c289708b51d1dda6eec669b4d3ecb7`  
Checksum Mega Drive : `368C`
<!-- ROM-RELEASE:END -->

## État du portage

La **v0203** corrige le flash d’une image de l’ancienne carte à la fin du
scrolling horizontal. Les parcours depuis la clairière et le retour du village
sont vérifiés en PAL/NTSC, avec des contrôles verticaux complémentaires.
Sur 3 004 images comparées à la v0202, seules les trois images du défaut
reproduit changent ; les états et la cadence des transitions restent identiques.
Voir les [preuves et limites de la v0203](analysis/scroll_publish_v0203.md).
Les v0204 à v0207 sont des diagnostics de scrolling/audio conservés pour recherche ;
la ROM recommandée reste la v0203.

La v0202 accélère la conversion des motifs de l’intro, du titre et de
l’inventaire : environ **39 % de coût CPU en moins pour cette routine**,
avec les mêmes pixels. La ROM reste à 1 Mio. Les noirs de l’inventaire PAL
et le premier palier du fondu du guerrier sont corrigés. Les six parcours
naturels d’inventaire, les bruitages, les 65 lignes/scènes de l’intro et
quatre variantes de cadence du titre passent en PAL/NTSC.
Voir les [preuves et limites de la v0202](analysis/pattern_pairs_milestone.md).
Les v0199–v0201 sont conservées comme versions intermédiaires de diagnostic.
Le portage complet et la cadence absolue depuis le boot restent à valider.

Les jalons ci-dessous concernent la chaîne expérimentale avec horloge,
qui reste distincte du chargement de la ROM jouable.

Le **lecteur audio complet du prototype** produit désormais les horodatages
PSG : **25 644 appels et 89 200 écritures par région** concordent avec la SMS,
puis passent en 68000 PAL/NTSC avec la file native. Les commandes globales,
priorités, mises en sourdine et sept canaux sont composés. Il reste à réaliser
le raccordement à l'horloge physique du jeu ; la v0203
reste inchangée.
Voir le [jalon du lecteur audio horodaté](analysis/reader_timing_milestone.md).

L'adaptateur d'interruption du prototype convertit aussi ces dates vers
l'horloge source : les **1 488 écritures des 24 chargements** concordent avec
la SMS. Le lecteur optimisé passe les mêmes 25 644 appels par région en 68000.
Les **24 chargements testés rentrent désormais dans leur budget**, avec une
marge minimale de 2,76 images NTSC et 3,73 images PAL. Les 1 488 événements
PSG sont aussi disponibles avant leurs échéances relatives. Il reste à
programmer les sorties physiques et à établir la phase globale depuis le boot.
Voir les [mesures, preuves et limites actuelles](analysis/native_copy_pointers_milestone.md).

Le profil instruction par instruction a permis d'optimiser deux copies de
buffers : le pire chargement du prototype passe de 22,98 à 19,95 images NTSC,
avec les mêmes états, pixels et dates PSG. Voir le
[jalon des copies natives](analysis/native_copy_pointers_milestone.md).
Le [jalon précédent des divisions natives](analysis/native_divu_loading_milestone.md)
conserve aussi les vérifications arithmétiques. La ROM jouable reste la v0203 ;
ces gains concernent la chaîne avec horloge encore en cours d'intégration.

Le lecteur horodaté alimente maintenant une **file bornée**, avec attente
quand elle est pleine et publication des paquets entiers. Les 24 entrées de
chargement passent dans quatre modes de file/compteurs, en conservant les
états SMS et les 1 488 écritures de référence. La mesure avec enfilage et
lecture garde au moins 2,28 images de marge NTSC et 3,24 en PAL. Le test émet
encore après le calcul ; le cadencement physique reste à raccorder.
Voir le [jalon du producteur audio avec file](analysis/queued_audio_milestone.md).

L'horloge vidéo native concorde maintenant avec **16 384 lectures physiques**
du compteur PAL/NTSC. Des rafales assembleur de diagnostic conservent aussi
les espacements audio rapprochés à 14 ticks maître près, relativement au premier
octet. Voir les [mesures et limites de l'horloge physique](analysis/md_io_clock_milestone.md).

Un premier chemin assembleur attend maintenant la position vidéo avant
d'émettre les octets préchargés depuis la file : **47 880 écritures** vérifiées
sur toutes les positions d'une ligne en PAL/NTSC, sans octet perdu ni image
sautée. Le retard maximal mesuré du premier octet est de 804 ticks maître ;
la précision et le raccordement au lecteur complet restent à finaliser.
Voir le [jalon de l'attente matérielle PSG](analysis/md_psg_wait_milestone.md).

Une conversion fusionnée des dates a aussi été validée contre la SMS, puis
écartée pour l'intégration car elle ralentit les chargements. Les essais de
contrôle d'horloge sont également revenus au code précédent après mesure.
Le [compte rendu des essais](analysis/master_reader_research.md) conserve les
résultats et les pistes déjà écartées ; la v0203 reste la ROM recommandée.

Les canaux mélodiques ont aussi leurs événements PSG datés : **20 852 cas
et 37 260 écritures par région** concordent avec la SMS sur les six emplacements
de canal, puis passent en 68000 PAL/NTSC. Les deux octets de fréquence, les
volumes et les enveloppes sont inclus. Les commandes globales et le lecteur
complet restent à composer, puis à relier à la cadence physique du jeu.
Voir le [jalon des canaux mélodiques horodatés](analysis/tone_channel_timing_milestone.md).

Le canal bruit complet produit ses écritures PSG horodatées : **30 670 cas
et 23 759 écritures par région** concordent avec la SMS et passent en 68000
PAL/NTSC, avec les commandes, enveloppes et fins de bruitage. Les fréquences,
les commandes globales et le lecteur complet restent à composer et intégrer.
Voir le [jalon du canal bruit horodaté](analysis/noise_channel_timing_milestone.md).

Les séquences de notes et commandes produisent maintenant des horodatages
par octet PSG : **85 760 cas et 5 888 écritures par région** concordent avec
la SMS, puis passent en 68000 PAL/NTSC avec publication dans la file native.
Les contrôles F1/F2/F3 et la restauration d'un bruitage sont inclus. Le canal
bruit, les fréquences et le lecteur complet restent à composer et intégrer.
Voir le [jalon des séquences horodatées](analysis/sequence_timing_milestone.md).

Les enveloppes audio disposent aussi d'événements PSG datés : 40 192 cas ADSR
et 13 400 cas de tables par région concordent avec les écritures SMS originales.
Les 53 600 cas natifs, comprenant les rejets, passent en 68000 PAL/NTSC ;
2 028 événements par région traversent la file avec la bonne échéance logique.
La cadence physique et le lecteur complet restent à raccorder au jeu.
Voir le [jalon des enveloppes horodatées](analysis/envelope_timing_milestone.md).

La première routine audio native horodatée est vérifiée : la sélection du
bruit (SMS8679), sur **9 216 cas par région**, produit le même état et le même
instant d'écriture PSG que l'original. Les 4 608 événements émis passent aussi
par la file native en 68000 PAL/NTSC, avec vérification de l'attente et de la
libération à l'échéance. Le lecteur audio complet reste à horodater et intégrer.
Voir le [jalon des horodatages du bruit](analysis/noise_note_timing_milestone.md).

Une file native de commandes PSG datées est prête pour séparer calcul audio
et publication : 119 273 commandes passent sur PC et en 68000 PAL/NTSC,
puis 12 000 commandes par région sont consommées par une interruption vidéo
pendant que la boucle principale les produit. Les horodatages calculés depuis
les instructions SMS et la sortie à la cadence exacte restent à raccorder.
Voir le [jalon de la file audio](analysis/psg_queue_milestone.md).

La préparation audio du prototype est maintenant comparée aux échéances
de chaque octet PSG du lecteur SMS original : **1 488 octets**, aucun calcul
en retard sur les 24 contextes retenus. La marge minimale est de 3,58 lignes
NTSC et 13,76 lignes PAL, avant le coût du futur mécanisme de publication.
La mise en attente, l'émission au bon instant et la phase globale restent
à intégrer ; la v0203 est inchangée.
Voir les [mesures audio et leurs limites](analysis/loading_psg_deadlines_milestone.md).

Le prototype effectue maintenant les transferts vidéo réels : 193 tuiles,
768 mots de carte et 32 couleurs sont vérifiés sur 24 contextes, avec des
écritures PSG effectives. Le total mesuré atteint 21,56–22,704 images NTSC
pour 22,710 côté SMS. La marge minimale n’est que de 1,64 ligne vidéo :
la cadence de publication reste à vérifier, avec les autres composants
d’affichage. La ROM jouable reste inchangée.
Voir le [jalon vidéo physique et ses limites](analysis/class0_video_milestone.md).

Le préfixe de chargement des graphismes couvre les trois classes de pièces :
56 cas source et 56 cas en 68000 pour chaque région passent. Il reste hors
du jeu actif ; voir le [jalon des trois classes](analysis/graphics_classes_prefix_milestone.md).

La composition audio du moteur avec calendrier évite désormais les copies
de sécurité imbriquées. Les 25 644 cas source passent en 68000 PAL/NTSC,
et 28 644 comparaisons vérifient aussi les commandes PSG et les rejets.
Au jalon audio précédent, le calcul seul passait de 22,34–23,51 à 20,87–22,04
images NTSC, pour 22,71 côté SMS. Cette mesure exclut les transferts vidéo
réels et ne prouve pas la cadence du jeu. Le binaire jouable reste exactement
la v0203. Voir le [jalon audio et ses limites](analysis/audio_stream_fast_milestone.md).

Avant cette optimisation audio, la chaîne native traitait déjà les commandes RLE et lignes
vidéo entières avant les interruptions. Les 16 points SMS restent conformes ;
7 040 cas d’horloge passent aussi en 68000 PAL/NTSC. Le calcul seul demandait alors
23–24 images NTSC sans compteurs internes, pour un budget SMS de 22,71.
Ce jalon de recherche utilisait la v0198. Le calcul direct de l’attente vidéo est vérifié
sur 3 933 000 positions/seuils ; les 32 693 cas IRQ passent en 68000 PAL/NTSC.
Le décodeur regroupe plusieurs commandes entre deux interruptions :
1 460 cas comparés et 16 cas longs supplémentaires en 68000 passent.
Une voie précalculée depuis la ROM valide aussi les 566 commandes et les
6 176 octets de motifs : elle demandait alors 22–24 images NTSC, encore sans marge
prouvée pour l’affichage. Les 24 parcours à 16 points SMS passent avec les
deux voies en 68000 PAL/NTSC. La construction régénère ces assets.
Voir les [mesures et limites actuelles](analysis/native_pattern_plan_milestone.md).

La chaîne native couvre désormais graphismes, cartes, HUD, attente,
transfert et préparation de palette jusqu’à 24BF, avec une seule horloge.
Les 24 contextes retrouvent 16 points SMS et passent en 68000 PAL/NTSC ;
les données VRAM/palette sont aussi comparées directement. Les 2 048 cas
de palette et 640 cas de regroupement sans IRQ passent dans les deux régions.
Le raccordement au jeu, les autres branches et le budget temps réel restent
à traiter. La ROM utilisée pour ces preuves était exactement v0198.
Voir les [preuves et limites](analysis/native_room_finish_milestone.md).

La conversion complète des cartes et la préparation du HUD sont traduites
avec l’horloge native jusqu’à 1DE8. Les 24 contextes retrouvent onze points
SMS, ainsi que les 1 536 octets de carte/HUD, et passent en 68000 PAL/NTSC.
Les 9 021 cas de jauges, or et gemmes concordent aussi avec la SMS sur les
octets et cycles, puis passent en 68000 dans les deux régions. L’attente, le transfert et la palette sont désormais couverts par le jalon
suivant ; le raccordement global et le budget réel restent à traiter. La ROM utilisée pour ces preuves était v0198.
Voir les [preuves et limites](analysis/native_room_hud_milestone.md).

La préparation native des cartes 190B est enchaînée au chargement graphique,
sur une seule horloge jusqu’à 24BC. Les 24 contextes retrouvent neuf points
SMS et passent en 68000 PAL/NTSC. Des captures indépendantes confirment les
cases et attributs modifiés, y compris les écritures de la coordonnée FF
dans la file vidéo. La conversion complète et le HUD sont désormais couverts par le jalon
suivant ; le raccordement global reste à faire. La ROM utilisée pour ces preuves était v0198.
Voir les [preuves et limites](analysis/native_world_map_milestone.md).

Le chargement graphique natif couvre désormais 16D0..24B9 avec une seule
horloge et des interruptions audio dynamiques. Les 24 parcours retrouvent
les six points de contrôle SMS et passent en 68000 PAL/NTSC. De nouvelles
captures confirment aussi les données graphiques, le terrain et les octets
copiés en SRAM. La ROM utilisée pour ces preuves était v0198 : le raccordement global,
les autres classes et la suite du chargement restent à réaliser.
Voir les [preuves et limites](analysis/native_graphics_load_milestone.md).

Le premier chargement graphique 16D0..1706 dispose maintenant d’une
traduction native avec horloge et interruptions audio dynamiques. Les
24 contextes SMS retrouvent phase, R, M1, RAM/audio et instants d’interruption ;
ils passent aussi en 68000 PAL/NTSC. L’audit corrige cinq lectures M1 manquantes
dans le compteur du décodeur précédent. La ROM utilisée pour ces preuves était exactement v0198 ;
la suite du chargement et le raccordement global restent à faire.
Voir les [preuves et limites](analysis/native_graphics_prefix_milestone.md).

La v0198 partage le décodeur natif des graphismes à quatre plans entre
le jeu et les contrôles : 515 vecteurs passent en C et en 68000 PAL/NTSC,
y compris les coûts Z80 T/M1. Elle corrige le début du noir à la fermeture
de l’inventaire en NTSC. Les bruitages du menu passent dans les deux régions.
Trois parcours NTSC concordent avec les fenêtres noires et la reprise SMS ;
en PAL, les images restent identiques à v0194, avec un écart d’une image
face à la SMS aux fins de chargement. Le contrôle strict PAL reste ouvert.
Le raccordement du chargement à l’horloge reste à réaliser.
Voir les [preuves et limites](analysis/native_patterns_milestone.md).

L'attente native couvre désormais 0B95..0BC5 et le retour réel au caller,
avec l'horloge, le lecteur audio et les interruptions dynamiques. Les
38 349 cas et 816 chaînes de deux attentes passent en 68000 PAL/NTSC :
phase, R, cycles, mémoire audio et instants d'interruption concordent avec
la SMS dans les contextes testés. Cela inclut les interruptions pendant
la restauration. Le raccordement au chargement et à la boucle du jeu
reste à faire ; la ROM jouable reste v0194.
Voir les [preuves et limites](analysis/native_wait_return_milestone.md).

Le travail sur l'horloge dispose maintenant d'une traduction native de
l'enveloppe d'interruption SMS 0137..0226 : état RAM, compteurs et coûts
vidéo/audio, avec attente de palette calculée depuis la phase raster.
Les contrôles de ce composant sont séparés de la ROM jouable ; son
raccordement à l'horloge du jeu reste à faire. La ROM courante reste v0194.
Voir les [preuves et limites](analysis/native_source_irq_milestone.md).

La v0194 raccorde le lecteur audio complet 8000 au code natif vérifié,
avec les coûts Z80/M1 conservés à chaque interruption. Les 25 644 vecteurs
passent en 68000 PAL/NTSC ; 33 788 états de la ROM jouable correspondent
à la SMS pour les 400 octets du lecteur et ses coûts d'exécution.
Le compteur de compensation suit désormais le débordement sur huit bits
du Z80, y compris hors de sa plage habituelle. Les régressions audio,
menus et inventaire passent. La v0193, défaillante au démarrage, reste
archivée et identifiée comme telle. L'horloge complète du jeu reste à intégrer.
Voir les [preuves et limites](analysis/native_audio_reader_milestone.md).

La v0192 raccorde la composition tonale 84C7 au code natif vérifié :
enchaînement des notes, relâchement, modulation et enveloppes, avec leurs
coûts Z80/M1. Les 20 852 vecteurs passent en 68000 PAL/NTSC ; 252 scénarios
de la ROM jouable concordent avec la SMS sur trois interruptions chacun,
y compris les registres PSG audibles. Les régressions audio, menus et
inventaire passent. L'horloge complète du jeu reste à intégrer.
Voir les [preuves et limites](analysis/native_audio_tone_milestone.md).

La v0191 raccorde le canal de bruit 864F/8679 au code natif vérifié.
Elle corrige aussi une sortie du lecteur audio : certains arrêts du canal
de bruit faisaient avancer le bruitage suivant une interruption trop tôt.
Les 39 886 cas de composant passent en 68000 PAL/NTSC, ainsi que 120
scénarios de mélange dans la ROM jouable. Les bruitages du curseur et de
validation de Nouveau jeu/Continue sont présents, audibles et déclenchés
aux mêmes images que sur SMS dans les quatre parcours testés.
Voir les [preuves et limites](analysis/native_audio_noise_milestone.md).

La v0190 raccorde les séquences tonales 8357 au lecteur natif : notes,
durées, commandes, boucles, appels et restauration. EA est prise en charge,
et les limites d'appels/boucles suivent désormais les accès RAM de la SMS.
Les 85 760 cas passent en 68000 PAL/NTSC ; 50 scénarios de la ROM jouable
correspondent à la SMS sur deux interruptions chacun. Les régressions audio,
menus et retour d'inventaire passent aussi.
Voir les [preuves et limites](analysis/native_audio_sequence_milestone.md).

La v0189 raccorde les hauteurs et modulations audio natives, avec les cycles
et lectures M1 d'origine. Les 59 852 cas passent sur hôte et 68000 PAL/NTSC.
Les miroirs de RAM audio sont désormais lus correctement ; 116 cas de
hauteur et 60 cas d'enveloppe correspondent à la SMS exécutée, en plus des
régressions audio et menus. La ROM reste à 1 Mio.
Voir les [preuves et limites](analysis/native_audio_pitch_milestone.md).

La v0188 raccorde les enveloppes ADSR et les 16 tables de volume au lecteur
natif vérifié. Le registre audio DE est conservé entre les canaux, notamment
pour la lecture de la commande `$83`. Les 53 600 cas de composant passent
sur hôte et en 68000 PAL/NTSC ; 22 400 retours audio et 48 cas limites
de la ROM jouable correspondent à la SMS dans les contextes testés.
Voir les [preuves et limites](analysis/native_audio_envelope_milestone.md).

La v0187 ajoute la file des effets prioritaires et la restauration des
canaux après un bruitage. Les routines SMS 81F8/8211 sont raccordées au
lecteur natif : 21 975 cas de composant passent sur hôte et en 68000,
puis 40 600 états de la ROM jouable correspondent à la SMS en PAL/NTSC
(399 octets hors routage GG et registres PSG audibles).
Voir les [preuves et limites](analysis/native_audio_priority_milestone.md).

La v0186 raccorde le dispatch audio natif vérifié (musique, bruitages et
commandes de contrôle). Les 2 304 cas de composant passent sur hôte et
en code 68000 PAL/NTSC ; 34 états contrôlés de la ROM jouable correspondent
aux 400 octets du lecteur SMS. Les coûts Z80/M1 sont désormais disponibles
pour cette routine, mais ne pilotent pas encore l'horloge du jeu.
Voir le [détail et les limites](analysis/native_audio_dispatch_milestone.md).

La v0185 rétablit les bruitages du menu Nouveau jeu/Continue : `$95` quand
le curseur change de ligne et `$AB` à la validation. Les parcours avec les
deux choix passent en PAL et en NTSC, avec des déclenchements aux mêmes
images que sur SMS et un canal d'effet audible. Appuyer vers le choix déjà
sélectionné reste silencieux. Ces contrôles ne remplacent pas une partie
complète ni une comparaison des formes d'onde audio.

Le portage est jouable mais reste incomplet. Les sources natives couvrent
l’intro avant le titre, le titre, les menus et dialogues, l’exploration,
les transitions, les combats, de nombreuses familles d’ennemis et boss,
les objets et sorts, les marchands, les récompenses, les sauvegardes et
la fin du jeu. Ces éléments ont des validations ciblées ; une partie
complète en progression naturelle reste à vérifier.

Les treize pistes musicales PSG et les bruitages ont un lecteur natif.
Leur synchronisation dans toutes les situations de jeu reste à contrôler.
Le binaire Mega Drive ne contient pas d’interpréteur Z80.

### Dernières corrections intégrées

- v0177 : conservation des récompenses et de la transformation des pièces,
  avec contrôles des retours dans les maisons et de la sauvegarde/reprise.
- v0178 : fondu musical B0 pendant les sorties de passages payants,
  puis lancement de la musique de destination avant la révélation.
- v0179 : fondus et révélation progressive des portes de maisons et de donjons,
  chargement masqué et restauration des couleurs des sprites.
- v0180 : attente explicite de la prochaine interruption vidéo avant la
  révélation, même lorsque l’affichage est désactivé. Les huit transitions
  de portes contrôlées ont un fondu d’entrée de 18 images, comme la SMS.
- v0181 : lecture des durées de notes au format brut 16 bits alignée sur la
  SMS, y compris lorsque le bit haut de la durée est positionné. Les 1 080
  cas ciblés, les 13 musiques et les 29 bruitages passent leurs contrôles.
- v0182 : arrêt conditionnel de séquence F3 lorsque le canal emprunté est
  actif, conforme à la SMS. Les 400 cas ciblés et les contrôles audio passent.

- v0183 : un silence du canal de bruit emprunté conserve la sortie PSG,
  comme sur SMS. Les 18 432 cas ciblés et les contrôles audio passent.

### Travail en cours

Rapprocher les durées de chargement et les animations de la SMS, en calculant
le travail original et les interruptions audio. Les routines de tempo,
fondu, arbitrage et traitement des commandes musicales/sonores ont des
modèles de coût vérifiés. Les enveloppes de volume ADSR et sur tables sont
également vérifiées. Les calculs de hauteur et de vibrato passent les tests
isolés ; le parcours observé en jeu utilise seulement le mode sans modulation.
Les notes, durées, silences, boucles, appels et retours de séquence ont
maintenant des coûts vérifiés en PAL et NTSC. Les arrêts F1/F2 sans restitution
8211 sont aussi contrôlés. Vingt commandes déterministes supplémentaires
et le partage F3 sont vérifiés sur des contextes isolés. Les commandes
utilisant le registre R et certaines restitutions restent à couvrir
avant une validation générale. La sélection
des notes de bruit (8679) dispose maintenant d’un modèle de coût vérifié ;
les notes, enveloppes et boucles F6/F7 du canal de bruit (864F) passent
39 360 cas isolés et les 1 102 appels d’un parcours en jeu. Les autres
commandes du bruit restent à couvrir. La composition des canaux de tonalité
(84C7) passe 20 680 cas isolés et les 3 372 appels du parcours observé,
qui utilise uniquement le vibrato sans modulation (mode 0). Le lecteur
complet correspond maintenant aux 1 202 appels du parcours contrôlé,
y compris ses deux sites de retour d’interruption. Les priorités passent
33 480 cas isolés et les conditions de pause/compensation passent 10 752 cas.
Les commandes utilisant R, certaines restitutions et les combinaisons
non couvertes restent à vérifier avant l’intégration aux chargements.
Le budget hors interruptions du chargement est désormais complet sur
24 scénarios de passages payants, avec 13 725 attentes VBlank et
14 424 appels audio contrôlés. Le travail des interruptions complètes
passe aussi 13 749 appels en jeu et 2 880 cas isolés. Le budget total
correspond aux 24 chargements contrôlés, avec les boucles et entrées
observées comme données. Les boucles de palette sont désormais prédites
depuis la phase d’entrée des 13 749 interruptions ; le compteur vidéo passe
149 500 positions isolées. Les 13 725 attentes VBlank sont maintenant
prédites depuis leur état d’entrée, avec 6 156 cas synthétiques supplémentaires.
La séquence de révélation est désormais prédite depuis un seul état
d’entrée : effacement, préparation, attente VBlank et réactivation de
l’affichage correspondent sur les 24 parcours et 7 220 cas isolés.
La routine graphique complète est également prédite depuis un seul état
sur les 24 parcours : motifs, métatuiles, terrain et copie SRAM, avec
six points de contrôle. Cela inclut les interruptions audio, la demande
de fondu musical B0 et la suspension des interruptions pendant la copie.
Le chargement de la carte est maintenant enchaîné à cette routine sans
état intermédiaire mesuré : les 24 parcours passent neuf points de
contrôle, avec les correctifs persistants et la file de tuiles.
Le HUD, son attente VBlank, le transfert vidéo et la restauration de
palette sont également enchaînés depuis l’état initial : les 24 parcours
passent maintenant 16 points de contrôle, avec les compteurs du HUD
fournis à l’entrée et les interruptions complètes calculées.
La suite du chargement (acteurs, historique) et les entrées de hasard
restent à prédire avant l’intégration aux timings natifs. Ces recherches
ne modifient pas encore la ROM v0183. Les lectures d’opcodes et le registre R
des interruptions vidéo passent désormais les 13 749 appels et 2 880 cas
isolés, sur leurs neuf étapes. Les files graphiques, motifs, HUD et lecteur
audio sont composés. Le premier trajet hors interruptions, du début du
chargement à la fin des motifs (16D0–1706), prédit maintenant R sur les
24 scénarios, avec 122 703 lectures d’opcodes et les interruptions audio
calculées. Ce calcul s’étend désormais jusqu’au retour de la routine
graphique complète (24B9) : six points de contrôle passent sur chacun
des 24 scénarios, soit 137 614 lectures hors interruptions, terrain et
copie SRAM compris. Le calcul atteint maintenant aussi le retour du
chargement de carte (24BC), avec neuf points par scénario : correctifs
persistants et file de tuiles sont inclus. HUD, attentes VBlank, acteurs
et historique restent à traiter. Les attentes VBlank calculent désormais
aussi R et les lectures des interruptions : 13 725 appels en jeu et
6 156 cas synthétiques correspondent. Le HUD est maintenant raccordé
depuis l’entrée du chargement jusqu’au retour 24BF : 384 comparaisons
sur les 24 scénarios, transfert et palette compris. Les jauges passent
aussi 18 042 cas isolés. L’historique est maintenant raccordé jusqu’à
l’entrée des acteurs : les 72 tirages aléatoires, leurs graines et R sont
prédits depuis l’état initial, avec 720 comparaisons sur les 24 parcours.
L’initialisation des acteurs atteint maintenant 1853 : types, statistiques,
persistance et compte actif correspondent sur les 24 parcours et les
1 536 combinaisons salle/masque. Le calcul couvre désormais aussi leurs
motifs, allocations partagées et conversions de palette jusqu’au retour
18E1 : R, timings, état des acteurs et motifs VRAM écrits correspondent.
Les routines du héros calculent maintenant R et la phase depuis leur
propre état d’entrée : 24 parcours et 13 150 cas isolés correspondent,
avec 475 octets d’état vérifiés. Ce raccordement est maintenant fait
depuis la RAM initiale du chargement : carte de collision et entrée du
héros sont reconstruites, avec 1 080 comparaisons jusqu’au retour 24E7.
Les scripts, la demande musicale et la préparation de révélation sont
maintenant raccordés jusqu’à la réactivation de l’affichage (0ACE), avec
1 320 comparaisons sur les 24 parcours. Le fondu/contours suivants, les
autres contextes et l’intégration native restent à vérifier. La récurrence
aléatoire et la progression de R sont maintenant traduites en C 68000 :
65 536 graines, 196 608 sorties et 66 816 progressions passent sur hôte
et dans une cartouche SGDK de test PAL/NTSC. Ces helpers attendent encore
le suivi natif de R. Le mécanisme d’horloge est maintenant aussi traduit
en C 68000 : 7 664 scénarios correspondent et cinq cas invalides sont
rejetés sur hôte et cartouche SGDK PAL/NTSC. Le callback audio dynamique
et le branchement au jeu restent à faire ; le hasard SGDK et les budgets
fixes sont encore utilisés en production.

La routine aléatoire originale est désormais vérifiée jusqu’à l’octet
produit à partir du registre R : 135 168 cas isolés et les 72 appels
d’historique des parcours contrôlés passent. La valeur de R à l’entrée
de la routine reste fournie ; son évolution depuis le début du chargement
et dans les interruptions reste à calculer avant de remplacer le hasard SGDK.
Le comptage des lectures d’opcodes du tempo, du fondu, de l’arrêt musical
et de l’arbitrage passe maintenant 66 530 cas isolés, avec contrôle de R,
des durées et de l’état audio. Le dispatch et la file des bruitages
prioritaires passent aussi 81 480 cas, avec les restitutions de canaux
prises en charge. Les enveloppes ADSR et sur tables passent maintenant
107 184 cas, avec contrôle de l’accumulateur, de DE et du dépilage des appels.
Les hauteurs et le vibrato passent aussi 118 832 cas, dont 32 dépilages
d’appel exercés avec des contextes synthétiques. Les notes et commandes
de séquence prises en charge passent 167 552 cas, dont 816 dépilages.
La composition des canaux de tonalité passe 20 680 cas isolés et les
3 372 appels d’un parcours en jeu, dont les anciennes captures restent
identiques. Le canal de bruit passe aussi 39 360 cas isolés et 1 102 appels
en jeu. Le lecteur complet compose maintenant ces comptes : 10 752 cas
de pause/compensation et 14 424 appels sur les 24 parcours passent, avec
les anciennes captures inchangées. Les commandes utilisant R, certaines
restitutions et les instructions du chargement restent à couvrir pour
calculer R depuis l’entrée. Le code des interruptions audio seules passe
15 360 cas isolés et 675 interruptions en jeu ; le vecteur et le lecteur
sont aussi vérifiés sur les 14 424 appels des parcours. Le corps des
interruptions vidéo complètes reste à composer pour ce comptage.

Restent aussi la fidélité du hasard au registre Z80 R, les différences de
combat et d’affichage encore ouvertes, la progression naturelle complète
et la vérification sur matériel Mega Drive.

## Fichiers utiles

- [Sources 68000/SGDK](megadrive/src/main.c) et [moteur des acteurs](megadrive/src/actors.c).
- [Journal des ROMs numérotées](versions/README.md) et [index des versions](versions/index.json).
- [Corrections v0180](analysis/reveal_wait_milestone.md).
- [Correction audio v0181](analysis/raw_note_duration_milestone.md).
- [Correction du partage audio v0182](analysis/audio_ownership_milestone.md).
- [Correction du silence du bruit emprunté v0183](analysis/noise_note_milestone.md).
- [Mesures des interruptions audio](analysis/audio_irq_milestone.md).
- [Calcul du traitement des musiques et bruitages](analysis/audio_dispatch_milestone.md).
- [Calcul des enveloppes de volume](analysis/audio_envelope_milestone.md).
- [Calcul de la hauteur des notes et du vibrato](analysis/audio_pitch_milestone.md).
- [Calcul des notes et du contrôle des séquences](analysis/audio_note_sequence_milestone.md).
- [Calcul du canal de bruit](analysis/audio_noise_channel_milestone.md).
- [Calcul des canaux de tonalité](analysis/audio_tone_channel_milestone.md).
- [Composition du lecteur audio](analysis/audio_reader_milestone.md).
- [Attentes VBlank et budget de chargement](analysis/save_wait_milestone.md).
- [Interruptions vidéo et budget conditionnel complet](analysis/full_irq_milestone.md).
- [Phase vidéo et prédiction des boucles de palette](analysis/irq_raster_milestone.md).
- [Prédiction des attentes VBlank](analysis/wait_raster_milestone.md).
- [Prédiction de la révélation depuis un seul état](analysis/reveal_phase_milestone.md).
- [Phase du début de chargement graphique](analysis/graphics_prefix_phase_milestone.md).
- [Phase de la routine graphique complète](analysis/graphics_load_phase_milestone.md).
- [Phase graphique et chargement de carte](analysis/world_map_phase_milestone.md).
- [Phase graphique, carte, HUD et attente vidéo](analysis/map_hud_phase_milestone.md).
- [Sortie du hasard original et registre R](analysis/rng_refresh_milestone.md).
- [Lectures d’opcodes des préfixes audio](analysis/audio_prefix_refresh_milestone.md).
- [Lectures d’opcodes du dispatch et des effets prioritaires](analysis/audio_control_refresh_milestone.md).
- [Lectures d’opcodes des enveloppes audio](analysis/audio_envelope_refresh_milestone.md).
- [Lectures d’opcodes des hauteurs et du vibrato](analysis/audio_pitch_refresh_milestone.md).
- [Lectures d’opcodes des notes et commandes de séquence](analysis/audio_note_sequence_refresh_milestone.md).
- [Composition des lectures d’opcodes des canaux de tonalité](analysis/audio_tone_channel_refresh_milestone.md).
- [Composition des lectures d’opcodes du canal de bruit](analysis/audio_noise_channel_refresh_milestone.md).
- [Composition des lectures d’opcodes du lecteur audio complet](analysis/audio_reader_refresh_milestone.md).
- [Lectures d’opcodes du vecteur et des interruptions audio seules](analysis/audio_irq_refresh_milestone.md).
- [Travail restant et notes techniques](analysis/world_next.md).
- [Ancien README conservé comme historique](analysis/README_historique_avant_v0180.md).

`gaw-megadrive.bin` est le binaire courant. `gaw-title-megadrive.bin` est
un alias du même binaire pour les anciens liens. Les anciennes ROMs
numérotées sont conservées sans écrasement dans `versions/`.

## Compilation et Git

Depuis ce dossier, dans PowerShell :

```powershell
.\build.ps1
python tools/verify_git_roms.py
```

La compilation utilise SGDK et Java ; leurs chemins peuvent être fournis
avec les paramètres `-Sgdk` et `-Java` de [build.ps1](build.ps1).
Chaque nouveau binaire reçoit un numéro de version. La version et le lien
affichés en tête de ce README sont actualisés par `tools/version_rom.py`.

Git conserve les sources, outils, rapports principaux et ROMs numérotées.
Les captures et fichiers temporaires volumineux restent disponibles localement.
Le travail reste dans le dépôt Git local, sur la branche `main`, sans dépôt
distant configuré. Il sera copié vers un nouveau dépôt lorsque demandé.
L’ancien dépôt GitHub V51 contient un autre arbre de code ; aucun changement
n’y a été envoyé depuis ce projet.

- [Lectures d’opcodes des interruptions vidéo complètes](analysis/full_irq_refresh_milestone.md).

- [Registre R pendant le chargement des motifs](analysis/graphics_prefix_refresh_milestone.md).

- [Registre R sur la routine graphique complète](analysis/graphics_load_refresh_milestone.md).

- [Registre R jusqu’au chargement de la carte](analysis/world_map_refresh_milestone.md).

- [Registre R pendant les attentes VBlank](analysis/wait_refresh_milestone.md).

- [Registre R jusqu’à la sortie du HUD](analysis/map_hud_refresh_milestone.md).

- [Tirages de l’historique depuis le début du chargement](analysis/history_refresh_phase_milestone.md).

- [Initialisation des acteurs et registre R](analysis/actor_prefix_refresh_milestone.md).

- [Graphismes des acteurs et registre R](analysis/actor_graphics_refresh_milestone.md).

- [Phases et registre R de l’initialisation du héros](analysis/hero_refresh_phase_milestone.md).

- [Chargement raccordé jusqu’au héros](analysis/loader_hero_refresh_milestone.md).

- [Chargement jusqu’à la réactivation de l’écran](analysis/loader_tail_refresh_milestone.md).

- [Routines aléatoires traduites en C 68000](analysis/native_source_rng_milestone.md).

- [Horloge d’instructions en C 68000](analysis/native_source_clock_milestone.md).
