# Premier service matériel de sorties PSG

La ROM recommandée reste **v0203**, SHA-256
`7660a4b5949d0f3362c4795ed5eb238f86c289708b51d1dda6eec669b4d3ecb7`.
La reconstruction produit les mêmes octets et les 207 ROMs numérotées restent
vérifiées dans le Git local. Le nouveau backend n'est pas raccordé au jeu jouable.

## Répartition du travail

Le jeu, les chargements, le lecteur musical traduit et le calcul des événements
PSG restent en **68000**. Le petit programme Z80 nouveau reçoit uniquement des
octets déjà calculés et leurs échéances, puis attend la position vidéo et écrit
au PSG. Il ne contient aucune logique originale du jeu ou du lecteur musical.

Le premier essai plaçait la file en RAM 68000 : c'était une erreur de transport.
Le Z80 peut écrire cette RAM mais ne peut pas la lire. Le cœur utilisé renvoie
explicitement une lecture inutilisée pour cette zone ; l'essai n'atteignait pas
l'état prêt. La file se trouve maintenant dans la RAM Z80, accessible au 68000
par BUSREQ, conformément au mode de communication décrit dans la
[documentation de développement](https://www.plutiedev.com/using-the-z80).
L'émulateur n'a pas été modifié pour contourner cette contrainte.

## Protocole conservé

* Une file de **32 descripteurs de 22 octets**, en RAM Z80 à `1000..12BF`.
  Les curseurs de publication/consommation sont des octets qui rebouclent à 256.
* Chaque descripteur contient une date de ligne 16 bits, la position V/H, le
  type de rafale, son nombre d'octets et 16 valeurs alignées à droite.
* Le 68000 prépare tout le descripteur avant de demander le bus. Il écrit les
  22 octets par accès **octet**, puis publie le nouveau curseur en un seul accès.
* Le Z80 accorde les transferts à distance des sorties imminentes. Le 68000
  vérifie encore l'accord après prise du bus et le révoque après un transfert.
  La copie assembleur est déroulée pour borner la durée de l'arrêt.
* Le Z80 copie localement les valeurs avant de libérer le descripteur. Un
  indicateur `busy` distingue une file vide d'un dernier descripteur encore joué.
* Le statut et l'horloge sont publiés en RAM 68000, dans le sens matériel permis.
  La séquence de publication reste impaire pendant l'attente critique et la
  rafale, pour empêcher la lecture d'un horodatage devenu trop ancien.

Ce protocole est distinct de `SourcePsgQueue`, qui garde son contrat sur un seul
68000. Une erreur n'autorise pas à réessayer une IRQ source déjà partiellement
traitée. L'arrêt fourni au backend est un **arrêt après vidage**, pas encore un
abandon immédiat de tous les sons en attente.

## Vérification native

Le [banc du backend](md_z80_psg_report.json) exécute d'abord le véritable
chargement/IRQ/lecteur/file natifs et contrôle les 16 points source, les traces
d'IRQ, RAM/audio et empreintes des données. Il publie ensuite les événements
calculés vers le service Z80 avec deux origines, normale et rebouclée.
Les valeurs de référence servent aux vérifications, pas à fabriquer les sorties.

Les **5 952 octets source**, leur ordre et leurs dates logiques sont conservés
sur les deux régions physiques. Les 24 cas synthétiques supplémentaires par
région couvrent chaque longueur de 1 à 16 octets à 315 ticks maître et de 1 à 8
à 630 ticks. Tous les **488 intervalles internes vérifiés** sont exactement
égaux à la cadence attendue dans le cœur utilisé.

Un essai de **512 commandes par région**, espacé sur plus de 81 000 lignes,
force la file pleine, deux rebouclages des curseurs 8 bits, un rebouclage du
compteur de lignes 16 bits et le recalage de la référence temporelle. L'origine
près de `FFFFFFFF` vérifie aussi le rebouclage des dates source 32 bits. Les
curseurs finissent tous deux à zéro, après livraison de toutes les commandes.

Le 68000 effectue un calcul polynomial observable pendant ces échanges :
**503 793 itérations NTSC et 514 415 PAL**, dont le résultat est recalculé
indépendamment sur hôte. Cela prouve le fonctionnement concurrent avec ce travail
témoin, pas la marge CPU du chargement réel en fonctionnement simultané.

L'observateur ajoute seulement des journaux hôte des lectures H/V, écritures PSG
Z80 et demandes de bus. Les trois fichiers amont modifiés pour le construire
sont restaurés octet pour octet. La RAM complète et l'image de fin du banc
correspondent au cœur normal. Les **2 181 publications d'horloge visibles et
stables** sont comparées aux dernières lectures physiques du Z80. Les mises à
jour du compteur ne franchissent jamais plus de cinq lignes ; une interruption
atteignant six lignes peut devenir ambiguë et n'est pas prise en charge.

La durée maximale des transferts après l'origine est de **4 242 ticks maître**,
moins de deux lignes. Aucun arrêt de bus mesuré ne recouvre l'intérieur d'une
rafale vérifiée. Les douze écritures de mise en silence du démarrage SGDK
précèdent l'origine et restent séparées des sorties du jeu.

## Retard encore trop élevé

| Sorties source | NTSC | PAL |
| --- | ---: | ---: |
| Retard minimal, ticks maître | 3 810 | 3 780 |
| Retard maximal, ticks maître | 182 865 | 182 460 |

Le maximum représente environ **3,4 ms**, soit plus de 53 lignes. La cadence
interne d'une rafale est exacte, mais la préparation et les changements entre
descripteurs retardent le début de certaines rafales. **Ce résultat ne satisfait
pas l'ordonnancement fidèle recherché.** Aucun seuil de retard n'a été abaissé
pour promouvoir ce backend dans le jeu ; les mesures restent des mesures de
prototype, avec contrôle de non-anticipation et d'intégrité des données.

Un essai de chemin rapide a séparé les mises à jour privées et publiques de
l'horloge et utilisé les registres alternatifs. Il a régressé : retards encore
élevés et défauts de compteur en PAL. Ses sources, ROMs et captures sont
conservées comme recherche rejetée. La version de base vérifiée a été restaurée
avant la vérification finale ; le noyau obtenu est identique à son premier
instantané vérifié.

Le [modèle C du producteur](md_z80_bridge_report.json) ajoute **12 000
descripteurs**, 23 rebouclages de curseur par région et 249 rejets de file pleine
par région. Les cibles sont comparées aux tables H/V indépendantes. Les rejets
de format, ordre, horizon, attente et défaut gardent les données, le curseur,
le nombre publié et la dernière date intacts. Ce modèle ne simule pas la sûreté
de BUSREQ ; celle-ci relève des mesures natives précédentes.

## Limites et suite

Le test est en H32, mode 5, 224 lignes, interruptions 68000 masquées et sans DMA.
La référence commence à la ligne physique 100 ; la phase globale depuis le boot
n'est pas établie. Le client d'horloge doit être servi avant un rebouclage complet
de 65 535 lignes, y compris pendant les périodes sans son. Les durées d'accès au
bus et la cadence sont des mesures dans Genesis Plus GX ; une console réelle
reste à vérifier.

Le producteur de chargement termine avant la lecture temporisée de ces événements.
Le calcul simultané est un témoin, et non le chargement réel. Il reste à préparer
les commandes suivantes avant leur échéance, réduire l'attente finale, raccorder
le producteur vivant, composer les DMA et les entrées au bon instant, puis définir
l'abandon sur erreur et la phase globale du jeu.

`analysis/md-z80-psg-v0203` conserve les sources et les captures compressées de
la version retenue et des essais rejetés. Le nettoyage ne retire des fichiers
générés qu'après vérification de leur récupération octet pour octet. La ROM SMS,
les sources, le Git et les ROMs numérotées sont préservés. Le portage reste en cours.
