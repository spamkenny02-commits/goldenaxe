# Compteur actualisé sur la ligne reconnue

Le service Z80 expérimental réutilise désormais la lecture verticale qui vient
de reconnaître la ligne cible. La ligne absolue du descripteur est conservée sur
la pile pendant le chargement des registres de sortie, puis dans HL pendant
l'attente. Sur la branche de reconnaissance, deux écritures locales mettent à
jour le compteur et le dernier V lu, avant EXX et l'attente horizontale. Cela
supprime le second relevé complet à cet endroit. La branche d'échéance dépassée
conserve le relevé générique. Les dates, valeurs, tampons et acquittements ne
changent pas. Le jeu et le lecteur audio source restent en 68000.

La conversion des échéances était surtout pénalisée par une entrée tardive dans
l'attente : les publications et décisions consomment du temps après le relevé
retourné. Le seuil d'entrée passe de trois à cinq lignes avant la date ; la marge
de copie reste de vingt lignes. Dans les cas testés, le compteur demeure actualisé
au plus toutes les cinq lignes physiques, malgré ce changement de seuil.

## Contrôle indépendant de la branche courte

Le banc reconnaît une mise à jour courte seulement lorsqu'une lecture du site
d'attente verticale est immédiatement suivie d'une lecture du site horizontal.
Il vérifie auparavant les octets assemblés : comparaison, saut conditionnel vers
les deux écritures aux adresses du compteur et du dernier V, EXX, puis lecture
horizontale. Les lectures verticales qui bouclent ou partent vers le relevé
générique ne sont donc pas comptées comme des mises à jour courtes.

Les comparaisons de publications restent fondées sur les dates physiques lues
par l'observateur, et non sur la seule ligne fournie par le descripteur. La borne
de cinq lignes entre mises à jour demeure contrôlée. La publication visible doit
toujours correspondre à l'une des deux dernières lectures qualifiées ; ce contrôle
n'a pas été assoupli pour faire passer les essais.

## Résultats retenus

| Variante | Retard maximal NTSC, ticks maître | PAL |
| --- | ---: | ---: |
| Préparation des registres précédente | 16 725 | 16 470 |
| Ligne cible relue dans le descripteur | 17 085 | 16 830 |
| Ligne cible conservée sur la pile | 16 305 | 16 215 |
| Même variante, décalage physique de 3 419 ticks | 18 031 | 15 766 |
| Entrée anticipée dans l'attente | **15 435** | **15 390** |
| Même pilote, décalage physique de 3 419 ticks | **15 286** | **15 391** |

Le [rapport nominal](md_z80_psg_earlier_wait_report.json) et le
[rapport de frontière](md_z80_psg_earlier_edge_report.json) correspondent au même
pilote restauré octet pour octet depuis la capture nominale. Les minima sont de
810 / 795 ticks en phase nominale, contre 3 540 / 3 510 auparavant. Parmi les
5 952 écritures source nominales, 1 204 ont moins d'une ligne de retard, contre
aucune auparavant. La médiane source descend de 9 690 / 9 510 à 7 132,5 / 7 140
ticks. Le maximum reste autour de 0,29 ms : la livraison fidèle à l'échéance
source n'est toujours pas atteinte.

Chaque phase conserve 5 952 octets source, les points de contrôle natifs,
les 24 rafales partielles par région, le parcours mixte de 64 commandes sur
seize positions et les 512 commandes longues avec saturation et rebouclages.
Les 2 384 intervalles internes contrôlés au total restent exacts à 315/630 ticks.
RAM finale, image d'arrêt et calcul 68000 témoin restent conformes aux contrôles
indépendants. Les deux régions et les deux phases vérifient 3 952 publications
visibles et 5 140 mises à jour courtes. La profondeur de quinze commandes et les
64 préparations anticipées finales restent observées.

Le gain de délai réduit aussi la marge de certains relevés : le maximum entre
lectures atteint 16 860 ticks en NTSC nominal, sous la borne de 17 100 avec
seulement 240 ticks de marge. Les autres maxima sont 15 885 en PAL nominal,
15 480 / 15 645 en phase décalée. Les écarts de compteur restent au plus de
cinq lignes. Ces cas sélectionnés ne prouvent pas toutes les phases ni les
pauses de DMA et d'interruptions du jeu complet.

## Variantes non retenues

`fresh-coarse` ajoute un relevé privé après publication. Le contrôle rejette en
NTSC une ancienne publication encore visible alors qu'elle n'est plus parmi
les deux dernières lectures qualifiées. `serialized-clock` invalide le statut
avant le relevé suivant et passe le banc nominal, avec des retards maximaux de
15 660 / 15 510 ticks. Mais le même pilote en phase décalée (`serialized-edge`)
atteint 17 550 ticks entre lectures sur le cas NTSC 141 et est rejeté avant le
PAL. Cette famille n'est pas retenue dans le fichier du pilote.

Les sources et captures de tous les essais sont conservées dans l'archive
`analysis/md-z80-psg-counter-v0203` avant nettoyage avec récupération vérifiée.

La ROM jouable recommandée reste **v0203**, inchangée. Le producteur source
termine encore avant la restitution ; le travail simultané reste un témoin.
Il reste à obtenir une marge d'horloge robuste sur davantage de phases et à
réduire les retards résiduels, puis à mesurer le vrai producteur avec le son.
DMA, interruptions natives, entrées, phase globale depuis le boot, abandon
immédiat, jeu complet et matériel réel restent à vérifier. Le portage reste
en cours et le Git reste local.
