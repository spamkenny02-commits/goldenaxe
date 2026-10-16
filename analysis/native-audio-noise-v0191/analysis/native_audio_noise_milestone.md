# Canal de bruit natif — v0191

La ROM jouable raccorde maintenant les routines 864F/8679 au code C compile
en 68000. Le canal utilise les enveloppes et commandes communes deja
traduites, avec conservation des 400 octets du lecteur, de DE et des couts
Z80/M1 de chaque routine. Les sequences tonales partagent le decodeur.

## Correction observable

Une fin F1/F2, ou certaines sorties F3, quitte tout le lecteur SMS 8000.
La v0190 continuait les canaux d'effets suivants. Le diagnostic conserve
montre un compteur d'effet a 2 sur SMS contre 1 sur MD. Avec la v0191,
les deux compteurs valent 2 et les 400 octets correspondent en PAL/NTSC.
Une fin de table d'enveloppe, elle, quitte seulement le canal : cette
distinction est conservee et verifiee.

## Controles conserves

- 28 896 cas hote : 19 680 contextes du canal et 9 216 du selecteur de bruit.
- 10 990 contextes supplementaires par region executes dans le code SMS
  d'origine : commandes, terminaisons, priorites, enveloppes tenues,
  miroirs RAM, boucles et appels imbriques. Comparaison des 400 octets,
  de DE, des cycles T, des lectures M1 et du type de retour.
- 39 886 vecteurs passes dans le composant compile en 68000, pour chacune
  des deux regions. Aucun echec.
- 85 760 vecteurs tonaux repasses en 68000 PAL/NTSC apres le partage du
  decodeur. Les captures source historiques restent la reference de ces
  vecteurs ; elles ne sont pas presentees comme une nouvelle execution SMS.
- 120 scenarios de la ROM jouable, soit 360 interruptions comparees a
  la SMS : 400 octets, DE et registres PSG audibles, avec musique et effets.
- Regressions de la ROM courante : 13 musiques, 29 effets, priorites des
  29 effets en PAL/NTSC, conservation de DE, fondu, musique et bruitages
  du menu Nouveau jeu/Continue et six retours naturels d'inventaire.

Les commandes de curseur 95 et de validation AB sont audibles, avec les
memes images de declenchement que sur SMS dans les quatre parcours du
menu (Nouveau jeu/Continue, PAL/NTSC). Appuyer vers le choix deja
selectionne reste silencieux, comme sur SMS.

## Limites

Les contextes E2 de comparaison SMS gardent le routage GG neutre : le
port 06 est miroir du controle cartouche sur SMS. Ce controle ne prouve
pas un comportement stereo sur materiel Game Gear.

Les commandes E3, EC, EF, FE et FF demandent encore le contexte R/source
et sont explicitement refusees. Les lectures de RAM non capturee et les
chaines de plus de 256 commandes non terminantes echouent sans publier
d'etat ou d'ecritures PSG partielles. Le modele Python historique du canal
de bruit reste plus limite que le composant C compare ici au code source.

Les couts de ce canal sont disponibles, mais le lecteur 8000 complet,
la composition tonale 84C7 et l'horloge complete des interruptions ne
les accumulent pas encore pour piloter le jeu. L'integration native de R
et du generateur aleatoire reste a faire. Les controles ne prouvent ni
l'identite des formes d'onde, ni le fonctionnement sur console physique,
ni une progression naturelle complete jusqu'a la fin du jeu.

Les sources, outils, rapports, journaux et captures de cette etape sont
figes localement dans `native-audio-noise-v0191`, avec un manifeste SHA-256.
Les fichiers volumineux de recherche restent locaux ; la ROM numerotee,
les rapports de publication et les sources utiles sont versions dans Git.
