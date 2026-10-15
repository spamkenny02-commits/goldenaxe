# v0183 : silence du canal de bruit emprunte

La routine8679 selectionne le bruit depuis les bits0..5 de la note.
Si aucun n'est positionne, elle rejoint863E : marquer le canal en repos,
puis tester le bit2 de ses drapeaux. Un canal emprunte ne doit pas envoyer
de coupure PSG. Le helper natif envoyait cette coupure sans tester le bit2.
La correction ajoute cette condition, sans autre changement de production.

Le banc cible execute le helper original, non modifie, et sound_noise_note
compile depuis toutes les sources natives. Le canal PSG de bruit est rendu
audible avant chaque cas avec E6/F0 pour observer une coupure intempestive.
Les400 octets du lecteur et les deux registres PSG bruit/volume sont compares,
y compris lorsque le canal est muet. Le modele semantique et le nombre
complet de cycles de la routine originale sont egalement compares.
Le petit trampoline de preparation coute59T ; ce cout est retire des mesures.

18432 cas PAL/NTSC couvrent les256 valeurs de note,les drapeaux0/4/128/132,
les volumes globaux0/15/255 et les decalages de bruit0/3/255. Ces contextes
sont synthetiques ; les notes basses ne sont pas toutes transmises a8679
par le lecteur normal. Aucun evenement naturel precis n'est revendique.
Avant :144 divergences PSG, sans divergence RAM. Apres :aucune divergence.

Les treize musiques,29 bruitages et fondus87/B0/82 passent egalement44340
comparaisons d'etats du lecteur et de registres PSG audibles. La frequence
du bruit muet est exclue seulement de ces regressions generales. Aucune
preuve de formes d'onde ou de validation sur materiel n'est apportee ici.

ROMv0183,1Mio,SHA-256 ec1677f7 (voir manifeste de version pour le hash complet).
Les captures avant/apres,modeles,fixtures,bibliotheques de mesure et sources
natives sont preserves localement dans audio-noise-note-v0183 avec manifeste.
README,rapports,outils et ROM sont suivis dans Git local.

Le traitement complet du canal de bruit (864F),les autres canaux,les commandes
utilisant R,la restitution8211,le lecteur complet et son integration au
calcul des chargements restent a terminer. Le jeu complet reste non valide.
