# Lecture groupée de la FIFO native

Le producteur mesuré retirait chaque événement avec une validation complète
de la file, puis tentait encore une lecture pour constater qu'elle était vide.
`source_psg_queue_take_many` valide une fois les arguments et curseurs, copie
les événements arrivés à échéance jusqu'à la capacité de sortie, puis libère
le curseur consommateur une fois les copies terminées. L'interface de lecture
unitaire et le producteur restent inchangés. La nouvelle API retourne OK avec
zéro événement pour une file vide, un événement futur ou une capacité nulle ;
INVALID conserve sortie, compteur et curseurs.

| Chargement réel allégé | Retard maximal NTSC | PAL |
| --- | ---: | ---: |
| Lecture unitaire, pilote huit/vingt | 169 395 | 169 605 |
| Lecture groupée, même pilote | **166 155** | **166 020** |

Les nombres sont en ticks maître. Le gain est modeste, environ 2 % sur le
maximum, pour un retard restant d'environ 3,1 ms. Le temps cumulé des callbacks
baisse d'environ 2,9 % en NTSC et 2,8 % en PAL. Le retard moyen vaut
11 285 / 11 354 ticks, contre 11 366 / 11 405 auparavant. Aucune garantie
globale de délai n'est acquise.

Le [banc allégé](md_z80_psg_bulk_drain_bare_report.json) et son
[homologue de preuve](md_z80_psg_bulk_drain_proof_report.json) passent chacun
les 48 chargements et 2 976 octets par région, leurs dates logiques, états
finaux RAM/audio, empreintes et traces IRQ. Le second conserve aussi les
seize états intermédiaires ; ses copies diagnostiques portent le maximum à
4 282 035 / 4 294 230 ticks, et ne représentent pas le budget sans ces copies.
Les 384 intervalles internes vérifiés dans ces deux noyaux restent exactement
à 315/630 ticks. Pas d'écriture anticipée dans les captures retenues ; bornes
d'horloge et de prise de bus respectées. RAM et image d'arrêt concordent
avec le cœur sans observateur.

Le [test sur PC](psg_queue_bulk_report.json) compare la lecture groupée à
la lecture unitaire pour 4 096 cas et 168 179 événements : capacités de file
1 à 32 768, curseurs et dates rebouclés, échéances égales/futures, sorties
nulles de capacité zéro, capacités de sortie partielles ou excessives, fin
de sortie inchangée et huit erreurs atomiques. Un
[noyau 68000](md_psg_bulk_report.json) compare encore 640 cas et 24 730
événements dans chaque région, sur des capacités 1 à 512. Ses 332 166
vérifications et son hash concordent avec la même exécution C sur PC.
Ces tests ne prouvent pas une préemption IRQ concurrente.

Deux autres essais sont rejetés. Le chemin Z80 spécialisé pour un octet
conserve les données mais donne 170 775 / 170 760 ticks de retard maximal.
La récupération de la capture diagnostique depuis les emplacements FIFO
encore intacts donne 170 040 / 169 905 ticks ; elle n'améliore pas le banc.
Cette dernière variante reste limitée à une fixture de 128 événements au
plus dans 512 emplacements, sans garantie générale de conservation.
Le pilote Z80 retenu a été restauré aux octets du huit/vingt précédent.

La lecture groupée est disponible dans les sources et activable dans le
banc avec `--bulk-drain`. Elle n'est pas intégrée au jeu. La ROM jouable
reste **v0203**, inchangée. L'affichage, le DMA, les interruptions natives,
la phase de boot et le jeu complet restent à valider ensemble. Les marqueurs
PSG natifs ajoutent toujours des écritures : la conformité des octets source
n'établit pas une onde sonore non instrumentée.

L'archive locale `md-psg-bulk-v0203` conserve rapports, sources et captures
avant le nettoyage vérifié. Le Git reste local.
