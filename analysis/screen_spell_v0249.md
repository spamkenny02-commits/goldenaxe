# v0249 : les deux niveaux du sort plein écran

Portage natif de 30A7, 37B3/37BD et 6AFB..6EAD : coût de 32 points de magie,
états du héros 6/7, 22 effets successifs au niveau 1 et quatre colonnes
animées au niveau 2. Les ressources graphiques et tables viennent de la ROM.
Les six motifs du héros incluent les deux motifs des huit particules.

Le sort efface les objets auxiliaires et la moitié supérieure des acteurs,
comme 6DEA. Les autres acteurs éligibles reçoivent les dégâts diminués de
leur défense (minimum 1 seulement en cas de soustraction négative), avec
la référence d'attaque C300. La sélection retourne ensuite à l'arme de base.
La possession est conservée. Le retour recharge les graphismes et métatuiles
de la classe courante, puis reconstruit la salle avec ses cellules actuelles.

La publication des cartes et sprites passe par le DMA en interruption vidéo.
Les cartes natives sont mises à jour avec les cellules modifiées, sans
reconvertir toute la carte à chaque image. Le stockage modal existant est
réutilisé ; aucun second tampon permanent de salle n'a été ajouté.

## Vérification ciblée

Neuf cas : niveaux 1/2 en NTSC/PAL, deux cas avec acteurs, magie insuffisante,
maison et donjon. Les deux derniers utilisent des cellules de salles réelles
avec classe et possession contrôlées. Ils ne constituent pas un parcours naturel.
Les 81 changements affichés du niveau 1 et les 28 du niveau 2 correspondent
à la SMS dans le même ordre : 436 comparaisons de cartes physiques au total.
Les motifs d'effet et les six motifs héros/particules correspondent dans
552 comparaisons de tuiles. Les 768 octets d'acteurs correspondent au moment
de l'application des dégâts dans les deux cas avec acteurs.
Cinq retours extérieurs ont zéro différence de pixels après normalisation.

## Écarts conservés

Le déclenchement et la durée ne sont pas encore synchronisés. Dans les cas
extérieurs sans acteur, la fin de l'effet MD arrive en avance :

| Niveau | NTSC | PAL |
| --- | --- | --- |
| 1 | 20 images | 83 images |
| 2 | 4 images | 7 images |

Les particules dépendent de l'horloge ; leurs positions ne sont donc pas
encore validées image par image. La durée du rechargement reste approximative.
Au retour, les captures contrôlées de maison et donjon présentent encore
214 et 142 pixels différents après normalisation, respectivement.
Les formes d'onde audio et l'acquisition naturelle ne sont pas établies.
Le portage de la campagne entière reste en cours.

Les v0244..v0248 sont conservées comme compilations intermédiaires.
Rapport : [screen_spell_release_v0249_report.json](screen_spell_release_v0249_report.json).
