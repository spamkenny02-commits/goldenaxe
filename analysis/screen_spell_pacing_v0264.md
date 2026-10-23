# v0264 : cadence du sort, sprites et restauration

Le portage conserve le travail de dessin 6B33/6C65, les calculs des
particules 6E3F/044E et la préparation de sprites 0938. Les délais entre
publications tiennent compte de ce travail, du transfert 22C6 et d'un IRQ
sans requête de tuiles/HUD, avec le coût audio courant. Ce dernier est une
prévision du travail futur, et non une reproduction complète de l'ordonnanceur.

La préparation des sprites est traduite sous une forme algébrique plus
rapide que l'annotation instruction par instruction. Les tables de sinus,
produits bornés et adresses de records évitent les opérations 32 bits lentes.
La table SAT calculée sert directement à l'affichage ; la limite de huit
sprites par ligne et le découpage à la fenêtre SMS restent appliqués.
Les collisions mises à jour par 0938 sont reportées dans les acteurs réels.
Le niveau 2 copie ses lignes depuis des mots de carte prétraduits.

La mémoire logicielle des motifs déjà envoyés au VDP sert temporairement
au calcul. Ses 4 Kio supérieurs sont sauvegardés dans l'espace modal existant,
puis restaurés avant le rechargement de la salle. Aucun tampon permanent
supplémentaire de 8 Kio n'a été ajouté. Le passage par l'inventaire après le
sort vérifie notamment que les motifs et caractères conservés sont utilisables.

## Mesures ciblées

Onze scénarios passent : deux niveaux PAL/NTSC, deux avec acteurs, maison,
donjon, manque de magie et deux passages par l'inventaire. Les 598 changements
de carte affichée et leurs tables de sprites correspondent dans le même ordre
à la SMS, avec positions et numéros de motifs identiques.

| Cas extérieur sans ennemis | Fin MD moins SMS |
| --- | --- |
| Niveau 1 NTSC | -1 image |
| Niveau 1 PAL | -1 image |
| Niveau 2 NTSC | -2 images |
| Niveau 2 PAL | -3 images |

Le cas chargé du niveau 2 NTSC finit encore 18 images après la SMS : il
reste un problème de budget CPU. Le cas avec acteurs du niveau 1 finit
2 images avant la SMS. Ces mesures portent sur la fin de l'effet, pas sur
une identité de chaque instant d'écriture vidéo ni de la restauration.

Neuf captures de retour ont zéro différence après normalisation des couleurs
et du décalage vertical MD : sept alignent le compteur logique du jeu, deux
comparent le même numéro d'image après ouverture/fermeture de l'inventaire.
Cela explique les différences précédemment mesurées en intérieur sans
permettre de déclarer les deux machines synchronisées en temps réel.

Le compteur de coût a été comparé à 232 étapes de carte et 232 scènes de
sprites observées sur la ROM SMS inchangée. La version algébrique conserve
également les résultats, le coût et les 8 Kio d'état sur 341 variantes valides ;
171 variantes non acceptées ont le même résultat de refus. Quatre coûts
fixes d'IRQ sont recoupés avec le modèle canonique. Ces comparaisons hôtes
ne prouvent pas une exécution 68k au cycle près.

## Limites

Les possessions, ressources, salles, éventuels acteurs gelés et une phase
initiale sont contrôlés. L'acquisition naturelle du sort et la campagne
complète ne sont pas vérifiées. Le raster initial, la prévision de travail
audio des IRQ intermédiaires, les formes d'onde et le RNG restent incomplets.
Les v0252..v0263 sont conservées comme intermédiaires. Les essais v0261/v0262
avec publication immédiate ont échoué sur les cartes partielles ; la v0264
conserve la publication en interruption vidéo.

Rapport : [screen_spell_pacing_release_v0264_report.json](screen_spell_pacing_release_v0264_report.json).
