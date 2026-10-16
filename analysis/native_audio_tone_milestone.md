# Composition tonale native — v0192

La routine SMS 84C7 est traduite en C compile en 68000 et raccordee aux
six canaux tonaux de la ROM jouable. Elle compose les routines de sequence
8357, de modulation 82C5 et d'enveloppe 854B deja traduites. Elle conserve
DE entre les composants et fournit les cycles T et lectures M1 de la
routine complete, au lieu de perdre les couts dans l'ancien assemblage C.

Les retours anticipes des composants terminent uniquement ce canal.
Les ecritures PSG sont preparees puis publiees apres succes. Si une
lecture ou commande echoue, les 400 octets et DE sont restaures ; aucune
ecriture PSG partielle n'est publiee. La copie SGDK respecte son ABI
`memcpy(..., u16)` sur 68000.

## Preuves

- 10 340 vecteurs historiques, dont le modele de composition a ete
  compare aux instructions SMS d'origine : etat complet, cycles, M1 et DE.
- 10 512 contextes supplementaires par region executes dans le code SMS
  intact : 1 248 par emplacement tonal, puis 3 024 notes tenues. Notes,
  frequences brutes, terminaisons, priorites, EA, boucles et appels imbriques,
  drapeaux, transposition, modulation et enveloppes sont compares sur les
  400 octets, T/M1 et DE. La variation de R du code source est aussi verifiee.
- Les 20 852 vecteurs sont passes en code 68000 PAL et NTSC sans echec.
- 18 refus sur hote verifient la restauration complete apres une lecture
  de flux impossible, une commande non traduite apres mutation et une
  lecture de table de vibrato impossible apres une nouvelle note.
- 252 scenarios de la ROM jouable : six emplacements, nouvelles notes,
  maintien et relachement. Trois interruptions par scenario, soit 756
  etats complets, correspondent a la SMS pour DE et les registres PSG
  audibles. Ces scenarios injectent un etat audio controle.
- Les 50 scenarios de sequence et 120 scenarios de bruit sont repasses,
  ainsi que les 13 pistes, 29 bruitages, 29 effets prioritaires en deux
  regions, conservation de DE, fondu, musique et effets du menu
  Nouveau jeu/Continue et six retours naturels d'inventaire.

Les fixtures d'appels emploient le pointeur de pile de canal valide 30.
Une premiere fixture a garde une valeur aleatoire, ce qui a produit un
appel au-dela des 400 octets du dernier emplacement : le composant l'a
explicitement refuse. La fixture corrigee utilise 30 pour tous les
emplacements ; elle conserve les appels imbriques dans la RAM capturee.

## Limites et suite

Cette etape remplace l'assemblage tonal existant par la composition
verifiee. Elle ne raccorde pas encore ses couts a l'horloge du jeu.
Le lecteur 8000 complet et les interruptions restent a composer, puis
les registres R, le generateur aleatoire et les attentes du jeu a raccorder.
Les commandes E3/EC/EF/FE/FF restent explicitement refusees, comme dans
le decodeur commun precedent. Les limites de lecture RAM et de chaine
de commandes restent explicites ; elles ne prouvent pas tous les contextes
possibles de la SMS. La liste de sortie PSG est bornee a 512 octets.

Les controles ne prouvent ni l'identite des formes d'onde, ni le rendu
sur materiel physique, ni une progression naturelle complete jusqu'a
la fin. Le portage global reste incomplet.

Les sources et preuves sont figees dans `native-audio-tone-v0192` avec
manifeste SHA-256. Les captures volumineuses restent locales ; les sources,
outils, rapports et la ROM numerotee sont versions dans le Git local.
