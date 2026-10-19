# Registres préparés avant la ligne cible

Le pilote Z80 expérimental prépare maintenant les registres de sortie avant
d'attendre la ligne cible. EXX les conserve pendant que les registres principaux
servent aux relevés d'horloge. Après reconnaissance de la ligne, un relevé privé
actualise le compteur puis EXX rétablit les registres prêts. Les deux sorties
possibles de l'attente verticale, ligne reconnue et échéance dépassée, rétablissent
le même jeu de registres avant restitution. Les chemins directs sans attente
continuent de charger normalement leurs registres. Aucun code original du jeu
ou du lecteur musical n'est déplacé sur le Z80.

La copie anticipée cesse désormais à vingt lignes de la date active, contre dix
auparavant. Un relevé supplémentaire sépare l'acquittement de copie du calcul
des pointeurs de rafale. Les délais de boucle éloignée sont réduits de huit à
une itération : une prise de bus native au mauvais instant laisse ainsi davantage
de marge avant le prochain relevé. La fréquence de publication augmente ; le
calcul 68000 témoin reste vérifié, mais cela ne prouve pas le budget du jeu réel.
La commande locale suivante, si sa ligne arrive dans une ou deux lignes, peut
réutiliser le relevé effectué en fin de rafale et passer à l'attente avec ses
registres déjà préparés. Les dates plus éloignées conservent le chemin général.

## Mesures natives

| Variante | Retard maximal NTSC, ticks maître | PAL |
| --- | ---: | ---: |
| Passage direct précédent | 21 720 | 20 985 |
| Registres préparés avant attente | 20 745 | 20 745 |
| Marge de copie accrue | 19 050 | 18 990 |
| Boucle éloignée raccourcie | 20 160 | 20 145 |
| Passage vers commandes à une ou deux lignes | **16 725** | **16 470** |
| Même pilote, restitution décalée de 3 419 ticks | **16 741** | **16 726** |

Le maximum mesuré descend autour de 0,31 ms. Les valeurs ne constituent toujours
pas une livraison fidèle aux échéances source : le retard dépasse encore une
ligne de 3 420 ticks. Les minima restent de 3 540 / 3 510 ticks en phase nominale.

Le [rapport nominal](md_z80_psg_shadow_ready_report.json) et le
[rapport de frontière de ligne](md_z80_psg_shadow_edge_report.json) correspondent
au même pilote. Le décalage du second banc est explicite : les points de contrôle
du producteur source restent inchangés, puis la base logique du seul service de
restitution recule de 3 419 ticks. Les écritures physiques attendues sont donc
reculées d'autant dans la vérification. Ce test ne modifie pas les dates source
pour les faire concorder avec des sorties tardives.

Chacune des deux phases vérifie les 5 952 octets de chargement, les points source,
les 24 rafales partielles par région, les 64 commandes mixtes sur seize positions
et les 512 commandes longues avec saturation/rebouclages. Les 2 384 intervalles
internes de rafale contrôlés au total restent exacts à 315/630 ticks. La profondeur
de quinze commandes et les 64 préparations anticipées de la session finale
restent observées. Le calcul témoin, la RAM finale et l'image d'arrêt concordent
avec les vérifications indépendantes et le cœur sans observateur.

Les 3 922 publications visibles concordent avec les lectures physiques. Le plus
grand intervalle de lecture vaut 15 210 ticks, contre 16 935 précédemment,
pour une borne de 17 100. Les écarts du compteur restent au plus de cinq lignes.
Les prises de bus mesurées restent au plus à 4 242 ticks et ne chevauchent pas
les intervalles internes des rafales contrôlées. Ces résultats couvrent les cas
et phases testés, pas l'ensemble des phases ni une console réelle.

Le banc accepte désormais `--phase-offset` uniquement avec un nom de variante,
borne sa valeur à une ligne, et inscrit ce décalage dans le rapport. Les variantes
de pilote et les tests de préchargement demandent aussi un nom explicite afin
de protéger les captures de référence.

La ROM jouable reste **v0203**, inchangée. Le vrai producteur n'est toujours pas
exécuté en parallèle de la restitution : le calcul simultané reste un témoin.
DMA, interruptions natives, entrées, phase depuis le boot, abandon immédiat,
jeu complet et matériel réel restent à vérifier. La suite doit réduire encore
le coût de l'attente finale, vérifier les marges sur davantage de phases, puis
mesurer le vrai chargement vivant avec le service sonore. Le portage reste en cours.

Sources et captures sont conservées dans `analysis/md-z80-psg-shadow-v0203` avant
nettoyage vérifié des fichiers générés. Le Git reste local.
