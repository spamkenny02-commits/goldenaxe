# Chargement 68000 et sorties PSG Z80 simultanés

Le banc démarre maintenant le service sonore avant d'exécuter le chargement
natif, au lieu de terminer tous les calculs avant la restitution. Le chargement,
ses interruptions logiques et le lecteur audio traduits restent en 68000. Le
Z80 reçoit uniquement les valeurs et dates calculées par ce producteur vivant.
Les références source servent aux comparaisons après calcul, pas à fabriquer
les écritures. La ROM jouable recommandée reste **v0203**, inchangée.

## Anticipation corrigée

Ce contexte révèle une écriture anticipée de 690 ticks avec l'ancien pilote :
cas 6, origine 32 bits rebouclée, cinquième octet. La lecture verticale vaut 35
et la cible 37. La soustraction sur un octet donne 254 ; la correction NTSC de
6 transforme cette valeur en 4, interprétée à tort comme une ligne déjà passée.
Cette correction était appliquée même sans franchissement de la discontinuité
vidéo. Les états source restent corrects : il s'agit d'une erreur de restitution.
La [régression figée](md_z80_live_early_regression.json) lie valeurs, dates,
ancien noyau, pilote et capture par empreintes.

`md_psg_prefetch_z80.asm` remplace cette décision par un relevé privé du compteur
absolu 16 bits, puis une comparaison signée à la ligne absolue attendue. Tant que
la ligne est future, il continue d'attendre ; sur la ligne cible, il attend H ;
après celle-ci, il émet. Le compteur est relevé pendant l'attente, ce qui conserve
sa borne de cinq lignes. Les essais retenus n'ont plus d'écriture anticipée.
L'ancienne variante de marge, affectée par la même heuristique, reste préservée
octet pour octet dans `megadrive/research` et dans son archive historique.

## Publication au moment de la production

Deux raccordements sont comparés. Le premier vide la file source après l'IRQ
complète ; le second conserve la publication atomique du paquet dans la file,
puis transmet immédiatement les paquets depuis le callback du lecteur, avant
que celui-ci termine toute l'IRQ. Le producteur et cette file restent sur un
seul 68000 ; le protocole interprocesseur séparé garde ses curseurs et BUSREQ.
Le callback peut attendre un accord de transfert, mais n'attend pas que toutes
les valeurs publiées soient jouées avant de laisser le chargement reprendre.

Chaque raccordement dispose d'un noyau de preuve vérifiant les seize états
intermédiaires et d'un noyau de mesure sans ces grosses copies. Les deux
contrôlent les dates/valeurs source, états finaux RAM/audio, traces d'IRQ et
empreintes des données. Les copies omises ne constituent pas une vérification
des états intermédiaires dans le noyau allégé ; son noyau de preuve les couvre.

| Publication | Copies intermédiaires | Retard maximal NTSC, ticks maître | PAL |
| --- | --- | ---: | ---: |
| Après IRQ | Présentes | 5 862 660 | 5 798 220 |
| Après IRQ | Omises | 1 403 745 | 1 403 325 |
| Dès chaque paquet, fin balisée avant la requête d'horloge | Présentes | 4 546 605 | 4 538 160 |
| Dès chaque paquet, même balisage | Omises | **353 385** | **346 290** |

La publication immédiate divise donc le maximum du banc allégé par environ
quatre, autour de 6,6 ms. Les minima valent 975 / 1 050 ticks. Les 5 952 octets,
leur ordre et leurs dates logiques restent conformes dans chacun des quatre
noyaux, pour les mêmes 24 contextes, deux origines et deux régions physiques.
Ces retards réels ne se comparent pas directement aux quelque 0,29 ms du rejeu
déjà calculé : ils incluent maintenant le coût de production et de publication.
Les échéances fidèles ne sont toujours pas tenues dans tous les cas.

Le [rapport complet par paquet](md_z80_psg_live_boundary_proof_report.json) est la
preuve d'états ; le [rapport allégé](md_z80_psg_live_boundary_bare_report.json)
porte la mesure de coût. Le chargement réel est actif au moment de 5 882 des
5 952 écritures du noyau allégé. Parmi elles, 4 156 surviennent hors du callback
de publication. Ce sont des calculs natifs et la petite instrumentation restante,
et non le témoin polynomial du précédent banc. Les écritures restantes sont
terminées pendant le vidage final. Le marqueur de fin précède la requête
d'horloge afin de ne pas compter son éventuelle attente comme du chargement.
Cette requête et celle de fin de livraison sont contrôlées par des lectures HV
natives indépendantes. Les premières variantes à marqueur après requête sont
aussi conservées ; elles ne servent pas au comptage final du chevauchement.

Le temps de fin du producteur varie aussi autour de la fin logique source :
de -1 513 948 à +827 937 ticks en NTSC, -1 503 489 à +826 052 en PAL. Un simple
facteur global de vitesse ne résoudrait donc pas le problème. Les callbacks de
publication consomment encore environ 12 % du temps de chargement mesuré, avec
des attentes d'accord BUSREQ ; il faut séparer ce coût de celui des routines
de calcul avant de choisir les prochaines optimisations.

## Régressions et portée

Le pilote corrigé repasse le rejeu préchargé dans les deux régions et aux offsets
physiques 0 et 3 419. Les vingt-quatre rafales partielles, les soixante-quatre
commandes mixtes sur seize positions et les 512 commandes longues conservent
leurs saturations et rebouclages. Les 2 384 intervalles internes contrôlés dans
ces deux phases restent exacts à 315/630 ticks. Les six variantes vivantes
conservées ajoutent 1 152 contrôles d'intervalles source. Les publications et écarts de compteur sont
vérifiés contre les lectures physiques. RAM finale et image d'arrêt concordent
avec le cœur sans observateur pour les huit noyaux retenus.

Le premier build vivant échoue sur un en-tête de relais manquant ; il est conservé
sans résultat d'émulation. Le suivant termine les contrôles natifs mais son
dépouillement échoue : les marqueurs de diagnostic sur le port PSG sont tronqués
à un octet. Les marqueurs utilisent ensuite trois octets distincts. La capture
suivante révèle l'anticipation et est rejetée avant le PAL. Ces étapes sont
conservées séparément et ne sont pas présentées comme des validations réussies.

Les noyaux utilisent des écritures natives de diagnostic au port PSG pour cadrer
les mesures. La concordance porte sur les écritures source du Z80 ; elle ne
prouve pas un rendu audio sans écritures supplémentaires. Affichage et IRQ
natives restent désactivés, sans DMA ni entrées vivantes. Les interruptions
source sont produites par le modèle logique du chargement, pas par un ordonnanceur
complet du jeu. Phase depuis le boot, abandon immédiat et console réelle restent
à vérifier. Le producteur n'est plus préchargé, mais ce banc n'est pas la ROM
jouable complète et n'y est pas intégré.

Les sources et captures sont conservées dans `analysis/md-live-z80-v0203` avant
nettoyage avec décompression et vérification des empreintes. Le Git reste local.
La suite doit profiler la disponibilité des paquets et les attentes de transfert,
puis optimiser et synchroniser calculs, son, affichage, DMA et entrées du jeu.
