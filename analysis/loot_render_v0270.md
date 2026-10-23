# v0270 : objets au sol et cout de rendu

Avec sept objets au sol, la v0267 manquait deux pas de simulation en NTSC
pendant leur duree de vie. Le compteur de clignotement prenait du retard et
la disparition arrivait a3363 au lieu de3361 dans le cas controle.
La v0270 conserve les regles source et evite ces pas manques.

## Changements

Le controle SMS de huit sprites par ligne utilise d'abord douze bandes de
seize lignes. Une bande compte chaque sprite8x8 qui la touche, independamment
de X ou des pixels transparents. Si aucune bande ne contient plus de huit
entrees, aucune ligne ne peut depasser huit. Si une bande est chargee, le
balayage exact precedent reste utilise. La coupure des sprites aux bords du
viewport192 lignes et le terminateur D0 sont conserves.

La preparation des parties de sprites avance directement le pointeur dans
le cache SGDK et ecrit le mot taille/lien8x8, avec les memes coordonnees,
indices et attributs. Les animations de decor en jeu utilisent le convertisseur
rapide deja present : eau exterieure, maisons et motifs de donjon. Les copies
SMS et les transferts video restent inchanges ; aucune regle de minuterie
ni tirage aleatoire n'est modifie.

## Verification

- 14 durees de vie controlees : types8..14 en PAL et NTSC, sept objets a la
 fois, un alignement initial de l'horloge. Les336 octets de records et les
 positions/salle/horloge correspondent sur5614 images.504 captures ont zero
 difference apres normalisation des couleurs. Les objets temporaires sont
 retires a3361 sur les deux machines ; les cles restent presentes a3400.
- 7 ramassages NTSC :280 etats des336 octets de loot,768 octets d'acteurs,
 or/vie/magie/cles/style et266 captures exactes. Couvre aussi le gel d'un
 acteur et la saturation de la cle de98 a99. Ces ressources sont fournies
 par les fixtures ; ce n'est pas une acquisition naturelle de campagne.
- 23584 configurations comparent les vrais corps C du controle de sprites
 precedent et actuel :6498 debordements,17019 chemins de masquage,
 5120 terminateurs. Resultats identiques pour statut, masquage et coupure.
- 24000 emissions comparent les vrais corps C de preparation des sprites,
 les descripteurs ROM,640 octets de cache et48 octets d'entite :10845 cas
 emettent au moins une partie. Le banc hote adapte l'ordre du mot taille/lien
 au68000 ; les images natives ci-dessus valident son utilisation en jeu.
- 6 regressions du sort : niveau1 PAL/NTSC, niveau2 avec acteurs PAL/NTSC,
 maison et donjon. Cartes, positions, motifs, ressources et horloge passent.
- 2 regressions cloche/eau PAL/NTSC : les huit etapes arrivent aux memes
 images source.12 images naturelles ont une composition VRAM/CRAM coherente
 et aucun code audio non traite.

La v0268 corrigeait les petites pieces mais laissait deux images de retard
aux grands objets NTSC. La v0269 ramenait ce retard a une image. Ces binaires
sont conserves ; utiliser la v0270.

## Limites

Les positions et objets sont controles. Les captures de duree de vie sont
36 points choisis par scenario, pas un film de toutes les images. La voie
de debordement reste plus couteuse que les bandes non chargees ; aucune
preuve de cadence globale, de partie complete, de RNG source ou de forme
d'onde analogique n'est revendiquee. Le hasard SGDK reste provisoire.

Rapport : [loot_render_release_v0270_report.json](loot_render_release_v0270_report.json).
