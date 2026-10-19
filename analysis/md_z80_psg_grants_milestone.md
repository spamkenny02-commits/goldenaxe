# Fenêtres de transfert et de copie séparées

Le pilote expérimental utilisait le même seuil de vingt lignes pour autoriser
une copie interne de descripteur et pour autoriser un transfert 68000 vers la
file Z80. Les paquets déjà disponibles pouvaient ainsi attendre alors que le
transfert natif, plus court, disposait encore de temps avant la sortie active.

Le seuil de transfert passe à huit lignes selon le compteur de décision ; le
seuil des copies internes reste à vingt. Dans la branche des échéances à six
à vingt lignes, HL vaut vingt moins le nombre de lignes restantes. Une comparaison
de son octet bas autorise les transferts lorsque ce nombre dépasse huit.
Les champs, curseurs atomiques, prise de bus avec nouvelle vérification de
l'accord, durée de copie et séquence d'émission restent inchangés. Les délais
réels sont contrôlés dans les captures ; les seuils ne constituent pas une
preuve de marge physique sur toutes les phases.

## Chargement réel

Le [rapport de preuve](md_z80_psg_grant_eight_proof_report.json) conserve les
seize états intermédiaires ; le [rapport allégé](md_z80_psg_grant_eight_bare_report.json)
mesure le chargement sans leurs grosses copies. Le 68000 publie les paquets
pendant le lecteur source et le Z80 les restitue en parallèle.

| Version | Retard maximal NTSC, ticks maître | PAL |
| --- | ---: | ---: |
| Transfert et copie à vingt lignes, mesure allégée | 353 385 | 346 290 |
| Transfert à huit lignes, copie à vingt, mesure allégée | **169 395** | **169 605** |
| Même pilote, copies de preuve présentes | 4 331 175 | 4 337 715 |

Le maximum du banc allégé baisse d'environ 52 %, à environ 3,2 ms. Les
5 952 octets et leurs dates logiques, les traces d'IRQ, les états RAM/audio
finaux et les empreintes de données restent conformes dans chaque noyau.
Le noyau de preuve vérifie aussi les seize captures intermédiaires. Les minima
mesurés valent 975 / 900 ticks, sans écriture anticipée dans les cas retenus.

Le chargement est encore actif au moment de 5 872 des 5 952 écritures ;
4 468 surviennent hors du callback de publication. Les autres sont terminées
pendant le vidage final. Le nombre de tentatives attendant l'accord de transfert
descend de 1 219 / 1 182 à 909 / 854. Les callbacks représentent encore environ
11,7 % du temps moyen de chargement mesuré. La fin du producteur varie de
-1 532 842 à +414 187 ticks par rapport à la fin logique source en NTSC,
-1 556 044 à +423 254 en PAL : il reste à traiter délais et synchronisation.

## Régressions

Les [rejeux nominal](md_z80_psg_grant_eight_replay_report.json) et
[décalé de 3 419 ticks](md_z80_psg_grant_eight_edge_report.json) passent dans
les deux régions. Les vingt-quatre rafales partielles, les soixante-quatre
commandes mixtes et les 512 commandes longues conservent saturation et
rebouclages des curseurs, compteurs et dates. Les 2 768 intervalles internes
contrôlés au total dans les quatre noyaux retenus restent exactement à 315/630
ticks. RAM finale et image d'arrêt concordent avec le cœur sans observateur.

Les 7 241 publications visibles concordent avec les lectures physiques.
Les prises de bus mesurées sont au plus de 4 102 ticks dans le chargement vivant,
4 242 dans les rejeux, sans chevauchement des intervalles internes des rafales
vérifiées. Les écarts de compteur restent au plus de cinq lignes. Le plus grand
intervalle entre lectures est de 16 920 ticks sur une phase NTSC du rejeu,
proche de la borne de 17 100 : aucune garantie exhaustive de phase n'est acquise.

Un [essai de copie interne à douze lignes](md_z80_psg_grant_eight_copy_twelve_report.json)
passe la mesure allégée PAL/NTSC, avec des maxima de 169 320 / 169 455 ticks.
Il réduit un peu la moyenne mais ne change pratiquement pas le pire retard.
Il est conservé comme essai et ne remplace pas le pilote huit/vingt vérifié
par le noyau de preuve et les rejeux. La source retenue est restaurée octet
pour octet depuis sa capture vérifiée.

La ROM jouable reste **v0203**, inchangée. Les marqueurs natifs de diagnostic
ajoutent des écritures au PSG : les tests établissent le transport des octets
source, pas une onde sonore non instrumentée. Affichage, DMA, interruptions
natives, entrées, phase globale de boot et abandon immédiat restent hors de ce
banc. Le portage complet et l'intégration au jeu restent en cours.

`analysis/md-z80-grants-v0203` conserve sources et captures avant nettoyage
avec vérification des empreintes et récupération des fichiers générés.
Le Git reste local. La suite doit identifier les retards résiduels des paquets
et le coût de restitution, puis mesurer l'ensemble avec le rendu réel.
