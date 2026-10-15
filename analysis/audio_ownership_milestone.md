# v0182 : arret conditionnel de sequence F3

La routine originale 8786..87AE interrompt la sequence lorsque DE0F n'est
pas negatif, que les deux bits bas de l'argument F3 valent 3 et que le canal
DF30 est actif. Elle restitue les drapeaux du bruit DED0, vide les drapeaux
du canal courant, place FF dans DE0F et envoie FF au PSG.
La version native poursuivait toujours le traitement ordinaire de F3.
La nouvelle branche reproduit cet arret avant de continuer vers une note.

Preuve ciblee : 400 cas PAL/NTSC executent les routines originales et le
sound_sequence natif compile avec toutes les sources de production.
Les octets F3/E7/00 proviennent de la ROM originale a 9B2B ; leur contexte
d'execution est synthetique. Cinq drapeaux, quatre types de canaux, cinq
priorites et deux etats du canal emprunte sont testes. Les 400 octets du
lecteur sont compares. Avant correction : 120 divergences ; apres : aucune.
Ce test ne demontre pas une occurrence naturelle precise de ce conflit.

La recherche complementaire couvre 20 commandes deterministes sur 59904
cas et F3 sur3840 cas, avec etat complet, cout d'instructions et retour
depilant les appels lorsque requis. La banque6 originale reste intacte.
E2 est une commande de stereo Game Gear ; sur SMS son port06 est un miroir
du controle memoire. Le test E2 garde ses anciennes valeurs stereo a zero
pour conserver cartouche et RAM actives. Les autres combinaisons E2 ne sont
pas validees ici. EF pointe dans une table, les commandes utilisant R et
la restitution8211 restent explicitement hors du modele.

Validation de regression : treize musiques, vingt-neuf bruitages et fondu
87/B0/82 PAL/NTSC, soit44340 etats du lecteur et des registres PSG audibles.
La frequence du bruit muet est exclue. Pas de preuve de formes d'onde,
de materiel reel, de progression complete ou de timing global des chargements.

Les rapports du calcul des commandes portent sur v0181 ; la correction
native et ses regressions portent sur v0182. Le manifeste conserve les
captures et indique ces deux binaires. Les autres sources de production
sont identiques a v0181 ; seul le test F3 ci-dessus est ajoute a sound.inc.
