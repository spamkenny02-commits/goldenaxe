# v0273 : compteur logique de la carte du monde

La v0271 gardait une duree de dessin proche de la SMS, mais son compteur de
jeu suivait toutes les interruptions MD pendant cette modale. Un alignement
fourni apres le dessin masquait l'ecart des marqueurs dans les anciens tests.
Le nouveau test ne regle l'horloge qu'avant activation, a2850. La v0271 y
echoue : compteur non fige et29 images de marqueur differentes sur33 en NTSC.

## Changement natif

La modale capture son compteur d'entree. Les deux attentes completes de
preparation ajoutent deux pas logiques ; la construction et les copies SRAM
n'ajoutent aucun pas ; chaque tour d'attente de l'apercu ajoute un pas ; la
fermeture20DA puis1DE2 ajoutent deux pas. A la sortie, world_clock_shift reprend
la valeur finale de la modale pour les animations et la simulation du jeu.
Les autres modales ne changent pas. Le sort plein ecran conserve son compteur.

Toutes les tuiles de l'apercu sont deja publiees par les225 salles. Le passage
3250..3267 ne recharge pas ces tuiles sur SMS : il restaure les cellules et
change la couleur du marqueur. Le rechargement complet MD est donc retire.
Le budget source ajoute le cout restant3559T : restauration du numero de salle,
activation SRAM, LDIR160, desactivation SRAM et couleur. Ce cout est derive
des instructions et verifie dans les cinq captures source conservees.
La v0272 est l'essai avant ce dernier raccordement ; utiliser la v0273.

## Preuves

- 22 scenarios :18 exterieurs et quatre gardes interieures. Possession,
 drapeaux et un seul alignement initial de l'horloge sont controles. Les
 captures verifient qu'aucune ecriture de test n'a lieu apres2850.
- 16159 observations du compteur pendant la construction sur les deux
 machines : une valeur figee identique, egale a l'entree plus les deux
 attentes de preparation.
- 168 images de l'apercu identiques au meme compteur logique, y compris
 quatre cycles33 images des marqueurs. Les5120 octets graphiques et1280
 octets de carte restent identiques dans les16 apercus stabilises.
- 18 retours au meme compteur : image normalisee et1536 octets de carte/HUD
 identiques,160 cellules et trois metadonnees restaurees ;256 drapeaux
 verifies avec les trois bits de passage attendus pour la cloche.
- Les traces source NTSC et PAL observent deux increments de fermeture.
 Les1125 couts190B et45000 projections precedents restent verifies, avec
 cinq couts3559T pour la fin de construction.
- Regressions : loot charge401 etats/36 images, sort niveau2 avec acteurs,
 et12 compositions naturelles sans erreur audio.

## Limites physiques

Le compteur est maintenant correct relativement aux iterations de la routine.
Le debut de sa boucle attend encore parfois une image trop tot : zero dans
le cas ordinaire NTSC, une en PAL. Il n'y a aucune correction cachee de ce
compteur dans le jeu pour faire passer les tests. Les rapports conservent
les comparaisons a la meme image physique : quatre echantillons different
parmi les168 images stabilisees de cette matrice. Les comparaisons au meme
compteur declarent explicitement le decalage0/1, sans modifier la RAM.

Les changements de compteur a l'ouverture/fermeture peuvent aussi arriver
une image apart pendant les ecrans caches. Ce n'est pas une preuve de raster
identique, de phase globale depuis le boot, de hasard source, de forme d'onde,
d'acquisition naturelle ou de partie complete. Ces points restent ouverts.

Rapport : [overview_clock_release_v0273_report.json](overview_clock_release_v0273_report.json).
