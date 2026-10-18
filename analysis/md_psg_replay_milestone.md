# Rejeu continu du lecteur natif vers les ports PSG

La ROM recommandée reste **v0203**, SHA-256
`7660a4b5949d0f3362c4795ed5eb238f86c289708b51d1dda6eec669b4d3ecb7`.
Le présent chemin est un prototype de synchronisation, pas une nouvelle ROM
jouable. Le but reste un portage fidèle de toute l'aventure.

## Chaîne effectivement exécutée

La cartouche de `tools/validate_md_psg_replay.py` exécute les 24 scénarios
de chargement natifs déjà comparés à la SMS : logique de chargement,
interruptions source, lecteur audio horodaté et file bornée. Avant toute sortie,
les 16 points d'état de chaque scénario, RAM/audio, R/M1, traces IRQ et les
empreintes de données restent comparés aux vecteurs source gelés.

Le contenu réellement produit par cette file est copié dans un tableau stable
de `SourcePsgEvent`, puis consommé par `source_md_psg_replay` en assembleur.
Les octets émis ne sont pas remplacés par les valeurs attendues du test.
Chaque scénario est exécuté avec deux origines logiques : zéro et `FFFF0000`,
pour vérifier le rebouclage 32 bits. Les deux régions physiques exécutent les
24 scénarios, y compris les calendriers source de l'autre région : cette
matrice vérifie les dates maître, pas un mode de jeu à régions mélangées.

Cela donne **48 chargements et 2 976 écritures source par région physique**,
soit **5 952 écritures** au total. Tous les octets et leur ordre concordent
avec les captures SMS d'origine.

## Horloge continue

Le consommateur conserve un temps maître modulo 32 bits pendant tout le flux.
Il calcule le nombre de lignes écoulées à partir des différences V, corrige
les ruptures NTSC EA→E5 et PAL 02→CA, puis ajoute la différence de phase H32.
La multiplication par 3 420 n'est effectuée qu'en changeant de ligne.
Les paires à 630 ticks et les quadruplets à 315 ticks utilisent des rafales.

Un marqueur est observé sur la ligne physique 90. L'origine du rejeu est le
début de la ligne 100 suivante, sans ambiguïté de valeur V. Les dates source
sont comparées à cette origine indépendante de la date de sortie effective.
À la fin de chacun des 48 flux, le temps natif, V et H correspondent exactement
à la dernière lecture physique observée, après quantification à 20 ticks.
La RAM complète et l'image d'arrêt concordent avec le cœur normal.

Le contrat impose moins de deux lignes physiques entre lectures, y compris
l'initialisation. Dans la cartouche finale, les intervalles mesurés sont :

| Intervalle en ticks maître | NTSC | PAL |
| --- | --- | --- |
| Lecture initiale → première lecture assembleur | 5 572..6 538 | 5 866..6 818 |
| Entre lectures du consommateur, cas synthétiques inclus | 1 316..4 732 | 1 316..4 732 |

La limite contractuelle est 6 840 ticks. L'initialisation PAL a donc encore
peu de marge ; un réveil asynchrone ne peut pas reprendre ce germe sans tenir
compte du temps passé. Un trou long peut rester indétectable à cause des
valeurs V répétées. Le germe physique utilisé ici ne résout pas la phase depuis
le boot du jeu.

## Dates effectivement émises et limites révélées

| Retard des écritures source, ticks maître | NTSC | PAL |
| --- | --- | --- |
| Minimum..maximum | 1 396..3 138 | 1 392..3 145 |

Aucune écriture source n'est anticipée. Le retard maximal de cette matrice
reste inférieur à une ligne vidéo de 3 420 ticks, mais le nouveau chemin est
moins précis que l'attente isolée du jalon précédent. Les mesures ne sont pas
une autorisation de relâcher la fidélité ; la précision reste à améliorer.

Sept contrôles natifs complémentaires testent une mise en sourdine de quatre
octets, deux quadruplets contigus, une séquence mixte, un flux vide, une région
invalide, une erreur persistante et un germe invalide/null. Les cas d'erreur
prévus n'émettent aucun octet. Le germe invalide laisse la structure inchangée.

Le cas synthétique de huit octets à 315 ticks expose un défaut de cadence :
le passage entre deux quadruplets reprend le calcul d'horloge et le dispatch.
Le retard atteint **5 906 ticks NTSC / 6 002 ticks PAL**. Les octets restent
ordonnés, mais cette suite n'est pas fidèlement cadencée. Le cas est conservé
comme limite explicite, pas présenté comme une validation de sa cadence.

## Intégration restante

Le producteur termine son calcul avant le rejeu ; il ne tourne pas pendant
le consommateur synchrone. L'affichage et les interruptions sont désactivés,
sans transfert graphique pendant le flux. Le test ne démontre donc ni le
respect des échéances pendant les calculs, ni le budget CPU du jeu, ni le
fonctionnement sous VINT/DMA et pression de file.

Prochaine étape : préparer les échéances avant la section critique, raccourcir
l'attente finale et traiter les longues rafales sans reprendre le calcul
entre groupes. Raccorder ensuite un consommateur réveillé aux événements
publiés, avec arrêt sur toute erreur fatale, et mesurer simultanément calculs,
ports audio et transferts graphiques. La phase globale et toute l'aventure
restent à vérifier ; la ROM jouable ne doit pas utiliser directement ce rejeu
bloquant.

Preuves : `analysis/md_psg_replay_report.json` et archive immuable
`analysis/md-psg-replay-v0203`. Sources, documentation et ROM restent dans le
Git local, sans publication distante.

Le fichier `disassembly.txt` conservé dans l'archive est un relevé exploratoire
antérieur à la dernière compilation. Pour désassembler le résultat final,
utiliser le `rom.out` archivé avec le `rom.bin` dont l'empreinte est dans le rapport.
