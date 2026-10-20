# Transferts contigus de une à quatre tuiles

La nouvelle primitive native `md_z80_video_span` prépare un jeton RAM de
14 octets pour transférer 32 à 128 octets contigus. Elle conserve source et
commande pendant WAIT et consomme le jeton après transfert. Les contrôles
portent sur la RAM du jeton, l'alignement, le chevauchement, la frontière de
banque de 128 Kio et la limite VRAM. Les API précédentes restent disponibles.

Sous BUSACK, la primitive recontrôle erreur, ready, grant et l'octet V atomique.
La fenêtre reste V brut 235–252. L'âge maximal est réduit à une ligne pour
les blocs de deux à quatre tuiles, et reste deux lignes pour une seule tuile.
Ce changement n'élargit pas le contrat de l'horloge Z80 : ses prélèvements
doivent toujours rester séparés de moins de cinq lignes.

## Même miroir source, moins de transferts

Chaque cas charge toujours les 512 mêmes tuiles issues du miroir SMS réel.
Les blocs de quatre ramènent les commandes de 24 576 à **6 144 par région**,
avec la même VRAM et la même image finales. Les sources, IRQ, dates et octets
PSG passent les 48 cas PAL/NTSC, et le banc complet conserve les 16 états
intermédiaires. Voir les rapports [allégé](md_z80_psg_video_source_span4_bare_report.json)
et [complet](md_z80_psg_video_source_span4_proof_report.json).

| Pire fin vidéo après chargement, en images | NTSC | PAL |
| --- | ---: | ---: |
| Une tuile avec relecture de chaque mot, référence précédente | 329,516 | 172,447 |
| Quatre tuiles avec la même relecture | 235,884 | 100,733 |
| Quatre tuiles sans relecture diagnostique | 141,537 | 70,213 |
| Service pendant la livraison audio, avec relecture | 414,398 | 86,944 |

Ces valeurs décrivent ces bancs, pas la cadence du jeu. Supprimer la relecture
change la charge de diagnostic ; son gain ne peut pas être attribué au seul
regroupement des transferts. Dans la [variante sans relecture](md_z80_psg_video_source_span4_no_readback_report.json),
la conversion Python indépendante et la capture du cœur sans instrumentation
vérifient toutes les tuiles finales. Cette variante n'apporte pas de relecture
directe de chacun de ses transferts intermédiaires.

## Tailles partielles et coexistence avec le son

Le [banc de blocs partiels](md_z80_psg_video_source_span3_tail_report.json)
commence chaque cas par une tuile, puis deux, puis des blocs de trois, avec
un dernier bloc de deux. Ses 8 256 transferts par région exercent donc les
tailles une, deux et trois, avec relecture de chaque mot et les mêmes 512
tuiles finales. Les [44 contrôles natifs par région](md_video_span_contract_report.json)
vérifient aussi les tailles, frontières, modes, rejets atomiques et la
conservation du jeton sur INVALID/WAIT/FAULT.

Le [service pendant la livraison audio](md_z80_psg_video_source_span4_delivery_report.json)
effectue **12 blocs NTSC et 19 PAL avant le dernier événement PSG**. Les
captures vérifient les octets, l'absence d'émission anticipée, les espacements
intrarafale et l'absence de BUSREQ dans une rafale. Les mots vidéo sont relus
sans différence. Il s'agit d'une preuve limitée de coexistence de vrais
transferts graphiques de 128 octets et d'une fin de flux audio actif.

Ce point de service ne constitue pas une solution de débit : presque tous
les travaux restent après le son et le pire cas NTSC régresse fortement.
La variante est conservée comme test de coexistence, sans être retenue comme
ordonnanceur de production. Tous les travaux commencent encore après le
chargement logique ; aucun rendu pendant ce chargement n'est établi ici.

L'[analyse physique des chemins compilés](md_z80_video_spans_windows_report.json)
retrouve les **65 664 transferts** des cinq variantes en PAL/NTSC. Tous restent
en VBlank. Le maintien maximal du bus vaut 6 214 ticks maîtres ; les
prélèvements Z80 restent espacés d'au plus 16 785 ticks, sous 17 100.
Les quatre variantes avec relecture comparent 3 145 728 mots au total.
La [réanalyse des anciennes captures](md_z80_video_spans_prior_windows_report.json)
reproduit leurs résultats.

L'affichage reste un atlas de contrôle. Carte, palettes, sprites, IRQ natives
et échéances du rendu complet restent à raccorder. Les marqueurs PSG
empêchent encore de valider l'onde sonore originale. La ROM jouable **v0203**
est inchangée et le Git reste local. L'archive `md-z80-video-spans-v0203`
conserve sources, noyaux, captures et rapports avant nettoyage vérifié.
