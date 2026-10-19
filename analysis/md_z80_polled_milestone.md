# Préparation unique pendant les attentes de transfert

`md_z80_psg_push_poll` prépare et valide un descripteur une seule fois,
puis réessaie le même transfert tant qu'il retourne WAIT, dans la limite
du nombre de tentatives fourni. Zéro tentative est invalide ; FULL et les
autres erreurs retournent immédiatement. L'API unitaire existante conserve
une seule tentative. Les deux entrées réutilisent la même préparation.
Le bloc, le producteur et son horloge appartiennent au même appel synchrone :
aucun jeton différé ni cache persistant n'est introduit.

Chaque tentative continue d'utiliser le protocole existant : contrôle de
l'accord, BUSREQ, nouveau contrôle de l'accord, copie bornée, publication
atomique et retrait de l'accord avant libération du bus. Épuiser les tentatives
laisse les données publiées, la tête, le compteur du producteur et sa dernière
date inchangés. Un éventuel rafraîchissement préalable de l'horloge conserve
le comportement documenté de l'ancienne API.

| Chargement réel allégé | Retard maximal NTSC | PAL |
| --- | ---: | ---: |
| Lecture groupée, préparation à chaque tentative | 166 155 | 166 020 |
| Lecture groupée, jusqu'à 128 tentatives par préparation | **162 180** | **162 435** |

Les nombres sont en ticks maître. Le gain supplémentaire sur le maximum
est d'environ 2,2 à 2,4 %, soit un retard encore proche de 3,0 ms. Les moyennes
passent de 11 285 / 11 354 à 10 982 / 10 917 ticks. Les durées cumulées des
callbacks baissent de 1,5 / 1,0 %. Les diagnostics `grant_wait` comptent
désormais les appels externes épuisés, pas toutes les tentatives internes :
leurs nombres ne peuvent pas être comparés aux anciens comme un gain de vitesse.

Le [banc allégé](md_z80_psg_poll128_bare_report.json) et son
[homologue de preuve](md_z80_psg_poll128_proof_report.json) passent les 48 cas
et 2 976 octets source par région, états finaux, traces IRQ, dates logiques et
empreintes de données. Le second conserve les seize états intermédiaires.
Les copies diagnostiques y portent le maximum à 4 295 610 / 4 300 140 ticks ;
ce n'est pas le budget du banc allégé.

Le [rejeu de l'API unitaire](md_z80_psg_poll_shared_edge_report.json) et celui
de la [nouvelle API](md_z80_psg_poll128_edge_report.json) passent chacun en PAL
et NTSC, décalés de 3 419 ticks : rafales partielles, 64 commandes mixtes,
512 commandes longues, saturation et bouclages u8/u16/u32. Leurs retards
maximaux sont respectivement 16 321 / 15 136 et 16 321 / 15 211 ticks. Ils ne
reproduisent donc pas exactement les maxima du noyau compilé antérieur ; la
cadence physique dépend aussi du code natif et des demandes de bus.
Les 2 768 intervalles internes contrôlés dans les quatre noyaux restent
exactement à 315/630 ticks. Aucune écriture anticipée ; les lectures d'horloge
restent espacées de moins de 17 100 ticks et les prises de bus mesurées sont
au plus de 4 130 ticks. RAM et image d'arrêt concordent avec le cœur sans
observateur. Cela reste une couverture finie des phases, sans garantie exhaustive.

Les [12 016 vérifications du pont existant](md_z80_bridge_polled_shared_report.json)
passent sur PC après le partage de la préparation. Les
[132 vérifications dédiées](md_z80_polled_report.json) comptent les tentatives
exactes avec des limites 0/1/2/8/128/65 535, succès après attente, épuisement
et reprise, erreurs immédiates et absence de publication partielle. Les
22 octets du descripteur concordent avec l'API unitaire pour cinq formes
de rafale. Ces tests de modèle ne remplacent pas les mesures natives.

La nouvelle entrée reste expérimentale, activable dans le banc avec
`--poll-transfer 128 --bulk-drain`. Aucun calcul source ne progresse à
l'intérieur de sa boucle synchrone. La ROM jouable demeure **v0203**,
inchangée. Affichage, DMA, interruptions natives, entrées, boot et jeu complet
restent hors de ces noyaux. Les marqueurs natifs au PSG empêchent encore de
revendiquer une onde sonore originale non instrumentée.

L'archive locale `md-z80-polled-v0203` conserve sources, rapports et captures
avant nettoyage vérifié. Le Git reste local.
