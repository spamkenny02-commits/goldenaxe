# Attribution des retards du chargement vivant

L'analyse de la capture retenue huit/vingt sépare le retard à l'entrée du
callback, sa préparation avant prise de bus, la prise de bus elle-même et le
temps restant jusqu'à la restitution Z80. Elle ne modifie pas le noyau mesuré.
Le [rapport](md_z80_psg_publication_latency_report.json) contient la
décomposition exacte des 5 952 octets PAL/NTSC.

| Composante du pire octet | NTSC, ticks maître | PAL, ticks maître |
| --- | ---: | ---: |
| Déplacement signé de l'entrée du callback par rapport à l'échéance | 96 730 | 96 893 |
| Callback avant demande de bus | 29 064 | 29 218 |
| Prise de bus | 3 948 | 3 941 |
| Restitution après libération du bus | 39 653 | 39 553 |
| Retard total | **169 395** | **169 605** |

Les deux pires octets sont le quatrième octet source, valeur 255, de cas
différents. Dans le premier cas NTSC, les quatre premiers callbacks entrent
aux ticks 602 446, 666 195, 745 162 et 808 428, pour des échéances de 684 705,
694 110, 703 515 et 711 240. Le premier dispose donc de marge, puis la
publication synchrone et le calcul intercalé consomment cette marge.
Réduire encore uniquement la durée de prise de bus ne peut pas supprimer
ce retard accumulé avant le quatrième callback.

La composante à l'entrée inclut calcul source, mise en FIFO, préparation du
callback et coûts des publications précédentes. Elle n'isole pas le coût
du lecteur. Les 48 octets déjà en retard à l'entrée dans chaque région
sont une observation de ce banc, pas une garantie sur tout le jeu.
La préparation avant bus inclut aussi les éventuelles nouvelles tentatives
attendant l'accord Z80. Après libération, l'intervalle inclut copie locale,
ordonnancement et attente intentionnelle : son maximum global n'est donc
pas une mesure de retard. Seule la somme signée est le retard de sortie.

L'outil vérifie les empreintes de l'archive, du rapport, du noyau et des
captures. Il identifie le chemin natif réussi par sa signature machine
(22 copies d'octet, publication de tête, miroir, retrait de l'accord,
libération du bus), et non par un seuil de durée. Il associe les publications
aux descripteurs FIFO reconstruits, vérifie les groupes de rafales sans
ambiguïté de frontière, puis vérifie l'égalité de chaque décomposition avec
le retard déjà contrôlé indépendamment. Les tentatives refusées ne sont pas
comptées comme publications.

Reproduction : `python tools/analyze_md_z80_publication_latency.py`.
Le prochain travail utile porte sur le coût natif par paquet et la copie
locale Z80, avec comparaison des mêmes états source et des dates physiques.
Ces résultats restent ceux d'un noyau instrumenté sans affichage, DMA ou
interruptions natives. La ROM jouable reste v0203 ; aucune nouvelle garantie
de délai ou d'onde sonore n'est acquise.
