# Rafales préparées et attente finale sur le faisceau

La ROM recommandée reste **v0203**, SHA-256
`7660a4b5949d0f3362c4795ed5eb238f86c289708b51d1dda6eec669b4d3ecb7`.
Le présent jalon concerne le prototype de synchronisation audio. Le portage
complet, la phase globale et toute l'aventure restent à vérifier.

## Changement

`source_md_psg_plan` regroupe les événements avant de lancer le consommateur.
Les suites à 315 ticks sont réunies jusqu'à 16 octets ; celles à 630 ticks,
jusqu'à huit octets. Le plan contient la date du premier octet, les valeurs et
un décalage vers la bonne portion d'une séquence assembleur déroulée. Il ne
reprend plus le calcul d'horloge au milieu de ces rafales.

Le planificateur conserve chaque date et chaque octet, même aux rebouclages
32 bits. Les erreurs de capacité, d'ordre, de fenêtre temporelle et de pointeur
sont refusées avant toute modification des sorties. Les suites dépassant
16/8 octets sont découpées : leur reconstruction logique est vérifiée, mais
leur cadence aux frontières entre blocs reste à améliorer.

`source_md_psg_plan_beam` prépare ensuite la position vidéo de chaque premier
octet à partir d'une origine physique fournie par l'appelant. L'arrondi va vers
le prochain palier H32 de 20 ticks et traite les reports de ligne et d'image.
Ces divisions sont effectuées avant l'initialisation de l'horloge physique.

Le consommateur suit d'abord son horloge absolue, puis passe à une attente
directe V/H quand la date se trouve à moins d'une ligne. Une lecture V fraîche
reconnaît une position déjà dépassée pour éviter d'attendre l'image suivante.
Une lecture HV cohérente vérifie ensuite l'entrée dans la ligne attendue.
Le compteur est aussi actualisé après la dernière écriture, avant le retour.

## Mesures des vrais chargements

Les 24 chargements natifs, leurs interruptions, lecteur horodaté et file
produisent les octets réellement rejoués. Les 16 points d'état SMS, R/M1,
RAM/audio, traces IRQ et empreintes restent vérifiés. Deux origines logiques
par scénario et deux régions physiques donnent **5 952 écritures source**.
Les octets et leur ordre concordent tous ; aucune écriture n'est anticipée.

| Retard des écritures source, ticks maître | NTSC | PAL |
| --- | --- | --- |
| Ancien rejeu continu, jalon précédent | 1 396..3 138 | 1 392..3 145 |
| Plan et attente finale préparés | 297..2 249 | 300..2 237 |

Le maximum de cette matrice passe de **3 145 à 2 249 ticks**, environ 28,5 % de
moins. Les phases de rafraîchissement du bus peuvent varier entre compilations ;
ces bornes mesurées ne sont pas une garantie de précision sur tous les flux.

Le test synthétique de huit octets à 315 ticks n'a plus de pause entre ses
deux moitiés. Dans le jalon précédent, l'intervalle entre le quatrième et le
cinquième octet atteignait 3 794 ticks pour 315 demandés. Le chemin préparé
mesure 308 ticks à cet endroit, avec le rafraîchissement du bus actif.

Le chemin brut conservé pour les comparaisons reste fonctionnel : mêmes états
et octets, avec un maximum de 3 230 ticks NTSC / 3 243 PAL dans le contrôle de
compatibilité courant. Son défaut sur les rafales de huit octets est conservé
comme témoin ; il n'est pas corrigé par le simple ajout du nouveau chemin.

## Couverture de la position vidéo et des plans

Une cartouche complémentaire balaie chaque phase horizontale **0..3419** avec
un octet, 16 octets à 315 ticks et huit octets à 630 ticks. Cela représente
**10 260 groupes / 85 500 écritures par région**, soit **171 000 écritures**.
L'origine physique vient d'un marqueur sur V=90, suivi du germe sur V=100.
Les origines logiques zéro et `FFFF0000` alternent.

| Mesure du balayage, ticks maître | NTSC | PAL |
| --- | --- | --- |
| Retard du premier octet | 296..1 889 | 294..1 875 |
| Retard de tous les octets | 264..1 889 | 263..1 875 |
| Écart relatif à la cadence source dans une rafale | -42..+7 | -42..+7 |
| Intervalle maximal entre échantillons d'horloge | 9 730 | 9 226 |

Chaque valeur finale du temps natif, V et H est comparée à la lecture physique
observée indépendamment. Les états RAM complets et les images d'arrêt sont
identiques avec le cœur normal et le cœur d'observation. Le test inclut les
reports de ligne, les ruptures H et le rafraîchissement du bus.

La préparation des plans est également vérifiée sur **21 024 cas hôte** et
**2 024 cas par région en 68000** : suites de tailles 1..512, mélanges, dates
égales, reports 32 bits et refus atomiques. Les blocs reconstruisent chaque
événement d'origine. En plus, **12 650 cas de projection vidéo par exécution**
couvrent toutes les lignes PAL/NTSC, 11 phases aux frontières et deux origines,
contre les tables HV du cœur. Les entrées assembleur de toutes les tailles
1..16 et 1..8 sont vérifiées au port avec des octets distincts.

## Limites et prochaine intégration

L'horloge exige des échantillons espacés de moins de trois lignes, soit
10 260 ticks maître. Cette fenêtre reste plus petite que la répétition V la
plus proche, six lignes NTSC. Le test contrôle les intervalles, initialisation
comprise. Les interruptions restent masquées et aucun DMA n'est autorisé dans
le consommateur ; un trou long peut fausser le compteur sans être détecté.

Le producteur termine encore avant le rejeu bloquant. La préparation des plans
et les sorties n'ont pas encore un budget CPU vérifié avec calculs, VINT et
transferts graphiques simultanés. Le germe V=100 n'établit pas la phase globale
du jeu depuis le boot. Les écarts résiduels sont mesurés, pas une tolérance de
fidélité accordée par l'utilisateur. Les suites dépassant les capacités de
rafale et les autres classes graphiques restent à traiter.

Prochaine étape : examiner les espacements et longueurs du lecteur complet,
puis réveiller un consommateur pendant la production, avec gestion de pression
de file et arrêt sur erreur fatale. Mesurer les dates au port et le coût CPU
avec les graphismes, avant toute intégration à la ROM jouable.

Preuves courantes : `md_psg_replay_beam_report.json`,
`md_psg_beam_sweep_report.json`, `md_psg_plan_report.json` et
`md_psg_replay_compat_report.json`. L'essai intermédiaire de regroupement seul
reste dans `md_psg_replay_planned_report.json`, avec son binaire et les sources
antérieures restaurées octet par octet contre ses empreintes. Les preuves sont
gelées dans `analysis/md-psg-prepared-v0203`. Git reste local ; les 207 ROMs
numérotées sont vérifiées et la v0203 reste inchangée.
