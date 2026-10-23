# v0242 : cloche de glace et animation de l'eau

La routine SMS 3124..31E6 est portée en 68000 : bruitage A4, restriction
aux extérieurs, remplacement des cellules 3F par 3A, huit masques de gel,
conversion des acteurs visibles et suppression des acteurs inactifs.
La possession, la sélection et la magie sont conservées comme sur SMS.
Les métatiles 38/3E et les passages 96/AA/CB suivent 1A30/1A50.
Le drapeau temporaire est réinitialisé lors du chargement des acteurs.

La routine extérieure 69CA..6A04 manquait : ses quatre motifs d'eau sont
maintenant extraits de la ressource RLE de la banque 11 puis publiés à
l'image suivante toutes les huit images, avec les quatre phases d'origine.
La v0241 conservée contient la première implémentation de la cloche ; elle
partait encore d'une eau sans animation de motifs. La v0242 la remplace.

## Vérification ciblée

Huit cas contrôlés : eau NTSC, eau PAL, acteurs visibles/inactifs dont un boss,
retour inventaire, interaction avec la carte du monde, passage 96, refus
maison et refus donjon. Les données finales de salle, métatiles, drapeaux,
ressources et possession correspondent à la SMS dans ces cas.
Les 768 octets d'acteurs correspondent au premier verrouillage du gel dans
le cas avec acteurs ; cela ne prouve pas les tirages aléatoires ultérieurs.

Les neuf états de motifs (initial et huit étapes) sont présents aux images
2999, 3002, 3004, 3006, 3008, 3010, 3012, 3014 et 3016 sur les deux machines,
en PAL et NTSC dans la scène testée. Seize captures complètes normalisées
pour la palette et le décalage vertical MD ont zéro différence de pixels.

## Limites

Salle, possession, ressources et une phase d'horloge initiale sont fournis
par le contrôleur de test. L'acquisition naturelle, tous les passages,
les écritures à l'intérieur d'une ligne vidéo et les formes d'onde audio
ne sont pas établis par ces vérifications. Le portage complet reste en cours.

Rapport : [ice_bell_release_v0242_report.json](ice_bell_release_v0242_report.json).
