# v0251 : horloge logique du sort et effacement avant rechargement

Le compteur C02F de la SMS avance une fois lors du plein traitement d'IRQ
appelé par0B95. Les interruptions audio survenues durant le travail ne
rajoutent pas de pas à cette horloge de jeu. Le portage avançait auparavant
selon toutes les images physiques. Le sort a maintenant un compteur modal,
utilisé pour les particules, le clignotement et les autres lectures de world_clock.
Le compteur reçoit un pas de préparation, un pas par itération et deux pas
de fermeture/restauration, comme les chemins observés 20DF/7226/1DE2.

Avant de remplacer les motifs d'effet par ceux de la salle, la zone de jeu
est effacée avec le mot SMS08FF et les sprites sont masqués. Cela évite
d'exposer une ancienne carte d'effet avec des graphismes déjà remplacés.

Neuf scénarios contrôlés passent : deux niveaux en NTSC/PAL, deux avec
acteurs, manque de magie, maison et donjon. Les 773 observations pendant
la boucle correspondent au compteur source attendu pour leur itération.
Les séquences de cartes et les données finales restent vérifiées.

Un observateur distinct laisse les instructions de la ROM SMS intactes.
Les modèles de 6B33/6C65 correspondent sur 232 étapes de dessin, et le
compteur natif de 0938 correspond sur 232 préparations de sprites. Ce dernier
accepte les descripteurs en ROM basse, dont6EAE. Il réutilise la traduction
annotée existante en sommant les cycles sans exécuter le modèle d'interruptions.
Ces vérifications sont faites sur l'hôte ; elles ne prouvent pas les timings 68k.

La cadence physique reste approximative : les modèles de coût ne sont pas
encore branchés sur l'ordonnanceur jouable. Les positions des particules
et les retours intérieurs ne sont pas déclarés exacts image par image.
Les captures ajoutées après observation RAM manquent le callback vidéo déjà
passé ; les fichiers RAM/VDP existent mais aucune comparaison de pixels
alignés sur l'horloge n'est revendiquée ici. Il reste à prévoir ces captures
avant le callback ou à utiliser l'image suivante des deux machines.

La v0250 est conservée comme compilation intermédiaire. Le portage de la
campagne entière, la cadence générale, le RNG et les formes d'onde restent
incomplets.
