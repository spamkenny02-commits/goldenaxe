# Horloge auxiliaire et premier raccordement audio pendant les chargements

La ROM recommandée reste **v0203**, SHA-256
`7660a4b5949d0f3362c4795ed5eb238f86c289708b51d1dda6eec669b4d3ecb7`.
La reconstruction produit exactement les mêmes octets et les 207 ROMs numérotées
sont vérifiées dans le Git local. Aucun envoi distant.

## Horloge pendant le calcul natif

Le prototype ne peut plus se contenter de lire souvent le compteur vidéo : une
routine de chargement peut occuper plusieurs images entre deux lectures.
Un petit programme dédié sur le **Z80 matériel** compte donc les lignes et
publie six octets dans la RAM 68000, avec un numéro de séquence protégeant
la lecture. Il ne contient aucune logique du jeu ni du lecteur musical, et
n'émet aucun son. Le lecteur audio original traduit et les écritures PSG
restent exécutés par le 68000.

Le client natif combine cette publication avec une lecture atomique du compteur
H/V. Il n'arrête pas le Z80 après le démarrage. Le point de départ explicite est
la ligne physique 100, en H32, mode 5, 224 lignes, sans entrelacement ni latch H/V.
Le source Z80 est placé dans `megadrive/z80` : SGDK traite les `.asm` de `src`
comme de l'assembleur 68000.

| Mesure du banc natif | Publication initiale, délai 24 | Publication retenue, délai 48 |
| --- | ---: | ---: |
| Surcoût NTSC | 6,0316 % | 3,8613 % |
| Surcoût PAL | 6,0366 % | 3,8637 % |
| Intervalle maximal entre lectures Z80 | 8 265 ticks maître | 12 945 ticks maître |
| Lectures 68000 vérifiées | 1 200 par région | 1 200 par région |
| Rebouclages du compteur de lignes | 14 par région | 14 par région |

Le surcoût inclut les appels du client, le stockage des résultats et la contention
du bus ; ce n'est ni le coût isolé du timer, ni une mesure du jeu complet.
Le calcul témoin donne exactement le même résultat avec et sans service.
Toutes les dates retournées correspondent aux lectures physiques observées,
y compris après des calculs de plusieurs images et au rebouclage 32 bits.
L'émulateur avec observation et le cœur normal terminent avec la même RAM
complète et à la même image.

Un contrôle C sur hôte ajoute **523 639 cas** : toutes les lignes PAL/NTSC,
les 171 positions H32 et les cinq âges de publication admis, puis 32 000 lectures
après de longues interruptions du client. Les tables H/V du cœur servent de
référence indépendante. Les lectures non prêtes, séquences impaires, publication
future d'une ligne, vieillissement de cinq lignes et défauts persistants sont
rejetés sans altérer l'heure ni la sortie. Ce contrôle arithmétique complète le
banc natif ; il ne prouve pas la concurrence matérielle à lui seul.

Preuves : [horloge retenue](md_service_clock_candidate_report.json),
[réglage initial](md_service_clock_report.json), [client C](md_service_client_report.json).

## Raccordement effectif pendant le chargement : voie bloquante insuffisante

Le nouveau banc exécute les 24 contextes de chargement provenant de la SMS,
avec deux origines temporelles, sur les deux régions physiques. À chaque IRQ
source, le véritable lecteur traduit publie ses événements dans la file bornée.
Le callback de fin d'IRQ prépare ces événements, relit l'heure via le service,
puis les écrit au PSG avant de laisser reprendre le chargement. Les valeurs
jouées sont produites par ce lecteur ; les listes SMS servent uniquement à vérifier.

Les **5 952 octets**, leur ordre, les dates logiques, les traces d'IRQ, les états
RAM/audio et les données calculées concordent. Le banc complet vérifie aussi les
16 points intermédiaires de chaque contexte. Un second banc omet leurs copies
de diagnostic pendant le chargement, puis contrôle les états finaux et empreintes
après la mesure. Les remplissages des buffers de test précèdent l'origine ; les
empreintes de diagnostic sont calculées après la mesure de fin.

| Voie sans copies intermédiaires | NTSC | PAL |
| --- | ---: | ---: |
| Retard PSG maximal, ticks maître | 4 027 546 | 4 040 381 |
| Octets retardés d'au moins une ligne | 828 / 2 976 | 829 / 2 976 |
| Retard maximal de fin du calcul, ticks maître | 4 460 610 | 4 471 730 |

Ces chiffres **invalident cette stratégie bloquante pour le portage fidèle**.
Ils ne sont pas présentés comme un budget réussi. Attendre le dernier octet
d'une IRQ consomme du temps dont le calcul suivant a besoin ; la marge mesurée
auparavant avec une file simplement remplie ne suffit pas à prouver cet
ordonnancement. Les copies intermédiaires amplifient encore le défaut dans le
banc complet, dont le retard maximal dépasse huit millions de ticks.

Les deux bancs retrouvent la même RAM et la même image de fin avec le cœur
normal. Les douze écritures PSG de mise en silence effectuées par SGDK au
chargement du driver sont séparées des sorties du jeu par l'origine physique.
Le tout premier essai comptait aussi le remplissage des buffers et ces écritures
de démarrage ; ses captures et sources sont conservées comme recherche rejetée.

Preuves : [banc complet](md_loading_audio_report.json),
[mesure sans copies intermédiaires](md_loading_audio_bare_report.json).

## Limites et suite

Le service remplace exclusivement le driver Z80 matériel. Une publication doit
rester âgée de moins de cinq lignes ; les DMA ou demandes de bus atteignant
cette durée ne sont pas pris en charge et peuvent provoquer une ambiguïté
indétectable. Le client doit lire avant le rebouclage complet du compteur 16 bits,
et sa lecture de séquence doit se terminer avant 128 publications. Les interruptions
sont masquées et l'affichage désactivé dans ces bancs.

La suite consiste à faire avancer le producteur pendant les attentes audio,
à borner les intervalles de service et à mesurer chaque échéance réelle. Il faut
ensuite composer les transferts vidéo/DMA, la lecture des commandes au bon instant,
l'arrêt sur défaut et la phase globale depuis le démarrage. Aucun de ces contrôles
ne valide encore le jeu complet ni une console réelle.

L'archive locale immuable `analysis/md-service-clock-v0203` conserve les sources,
ROMs de diagnostic et captures compressées avec empreintes. Le nettoyage des
fichiers générés intervient uniquement après vérification de leur récupération
octet pour octet. L'objectif de portage reste en cours.
