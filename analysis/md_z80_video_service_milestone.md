# Coût des points de service vidéo

Deux emplacements de service ont été mesurés avec le chargement source réel,
la primitive DMA de 32 octets et les mêmes 2 784 requêtes par région. Un
service inséré avant/après les fonctions d'horloge permet de réessayer les
travaux pendant le calcul, mais son coût natif peut annuler le bénéfice.
Le producteur audio reste sur 68000 et les interruptions natives sont masquées.

| Banc allégé | Retard audio maximal NTSC / PAL, ticks | DMA terminés pendant les chargements NTSC / PAL |
| --- | ---: | ---: |
| Référence précédente | 270 870 / 269 280 | 2 / 14 |
| Service toutes les 64 frontières des quatre fonctions d'horloge | 1 727 310 / 1 735 380 | 3 / 7 |
| Motif préparé une fois par travail, sans service ajouté | 183 645 / 183 930 | 0 / 0 |
| Motif conservé, service aux seuls blocs répétés sous DI | 183 675 / 183 885 | 8 / 14 |

Le service large effectue 38 872 appels de compteur par région et dépasse
30 ms de retard : il est refusé comme optimisation. Le service des seuls
blocs `repeat_disabled` effectue 1 344 appels, préserve le petit budget audio,
mais ne résout pas le débit vidéo. Ces wrappers restent optionnels dans les
outils ; les fonctions de l'horloge du portage ne sont pas modifiées.
Le générateur partagé reproduit exactement le C du premier essai mesuré.

La préparation unique du motif supprime une dépense de la fixture : elle
produit exactement 2 784 motifs pour 2 784 requêtes, au lieu de refaire les
huit lignes à chacune des tentatives. Elle ramène le retard audio vers 3,4 ms,
mais **ne constitue pas un gain de rendu du jeu**. Aucun de ses DMA ne finit
pendant les appels de chargement dans cette mesure ; le dernier peut encore
terminer 122,11 images NTSC ou 67,86 images PAL après leur retour. Avec les
points de service limités, ces maxima restent à 133,90 / 63,66 images.

## Contrôles conservés

Les quatre noyaux passent chacun les 48 cas et 2 976 octets par région,
leurs dates logiques, traces IRQ, états finaux et empreintes. Le noyau
[de preuve avec motif conservé](md_z80_psg_video_pattern_cache_proof_report.json)
vérifie aussi les seize captures intermédiaires ; ses grosses copies
diagnostiques ne servent pas de mesure du budget allégé. Les deux essais
de points de service n'ont que les contrôles finaux du mode allégé.
Les 768 intervalles de rafale vérifiés au total restent exactement à 315/630
ticks, sans émission anticipée. La plus grande distance entre lectures
d'horloge reste de 16 785 ticks, sous 17 100.

L'[analyse physique](md_z80_video_service_trials_windows_report.json) retrouve
les 2 784 commandes réussies dans chaque région/noyau, par les instructions
de transfert et leur PC de libération. Les deux allocations de registre
observées dans le code compilé sont vérifiées explicitement. Les arrêts
DMA restent en VBlank, au plus de 3 732 ticks, sans chevauchement des
intervalles internes des rafales PSG contrôlées. Tous les travaux de la
fixture finissent, et RAM/image d'arrêt concordent avec le cœur sans observateur.

Un [témoin intermédiaire](md_z80_dma_intermediate_video_pattern_cache_bare_report.json)
confirme des pixels réellement modifiés, différents de l'initialisation,
avec la préparation conservée. La trace IO est exactement le préfixe de la
mesure complète, et la même image/RAM/VRAM est obtenue sans observateur.
Les compteurs d'upload y incluent le premier chargement CPU d'initialisation.

## Ce que les nouvelles mesures changent pour la suite

Les nouvelles statistiques distinguent les tentatives qui atteignent la
lecture du raster, celles qui prennent le bus et les commandes effectivement
émises. Dans la référence précédente, 334 076 / 204 445 tentatives s'arrêtent
avant la première lecture du raster, sur 348 876 / 221 030 tentatives totales.
Il s'agit des gardes précédant cette lecture ; ces nombres ne distinguent
pas à eux seuls l'accord, la publication impaire et la fenêtre V.
Ajouter des points de service ne suffit donc pas à établir un débit utile.
Il faut maintenant réduire le travail répété dans la tentative de transfert,
puis servir les travaux aux frontières du chargement/rendu sans casser les
optimisations des opérations d'horloge sémantique.

L'analyse des fenêtres utilise désormais des recherches dans les chronologies
triées. Une [régression sur la capture archivée](md_z80_dma_window_regression_report.json)
conserve exactement les anciennes métriques et lignes de cas. Les outils
d'analyse et de témoin peuvent récupérer les captures/noyaux depuis l'archive
avec contrôle des empreintes ; aucun téléchargement n'est nécessaire.

La ROM jouable reste **v0203**, inchangée. Les motifs sont synthétiques ;
rendu SMS, IRQ natives, sprites, scrolling et échéances d'image restent à
intégrer. Les marqueurs PSG empêchent encore une preuve de l'onde sonore
originale. Aucun point de service de cet essai n'est retenu comme solution
de rendu. L'archive locale `md-z80-video-service-v0203` conserve les sources,
rapports et captures avant nettoyage vérifié. Le Git reste local.
