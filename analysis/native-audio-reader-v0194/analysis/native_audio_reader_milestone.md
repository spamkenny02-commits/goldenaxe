# Lecteur audio complet natif — v0194

La routine SMS 8000 est traduite et raccordee au lecteur de la ROM jouable.
Elle compose le verrou de pause, les files de commandes, le tempo, le
fondu, le dispatch, les effets prioritaires, la compensation et les sept
canaux. Les fins du canal de bruit qui quittent tout le lecteur sont
conservees. Le cout T/M1 complet, hors CALL d'entree, est stocke a chaque
interruption dans `sound_source_work`.

Le compteur de compensation suit maintenant les operations sur huit bits
du Z80 : increment avec debordement, puis remise a zero si la valeur est
superieure ou egale a six. L'ancien modulo six differe pour certaines
valeurs hors de 0..5, notamment 6 et 255. La correction est verifiee sur
les 256 valeurs ; une occurrence naturelle de cet etat n'est pas revendiquee.

## Preuves

- 5 376 contextes historiques de pause et compensation, dont les modeles
  ont ete compares aux instructions SMS d'origine.
- 14 424 appels reels du lecteur, captures lors des sorties payantes de
  six routes avec deux masques et deux regions. Les captures et leurs
  empreintes historiques sont conservees. Les 400 octets, T/M1 et DE
  correspondent au composant natif sans ignorer de commande non prise en charge.
- 5 844 nouveaux contextes par region executes dans la routine SMS intacte :
  2 048 compensations, 1 000 dispatchs, 1 116 priorites, 1 536 combinaisons
  de canaux et 144 fins de bruit. Toutes les valeurs de phase et les 128
  masques de canaux actifs sont inclus. Les 400 octets, T/M1, DE et la
  variation de R du code SMS sont verifies.
- Les 25 644 vecteurs passent en code 68000 PAL/NTSC, sans echec, dans
  huit cartouches de test inferieures a 4 Mio chacune.
- Le lecteur de la ROM jouable est compare au lecteur SMS mesure : 110
  scenarios et 33 788 etats sur deux regions. Etat complet et couts T/M1
  correspondent. Les registres PSG audibles correspondent pour les 13
  pistes et 29 effets, soit 33 684 etats ; les cas de pause/phase ne
  pretendent pas comparer les registres physiques herites du demarrage.
- Les regressions de musique, bruitages, priorites, DE, sequences, canal
  de bruit, canaux tonaux, fondu, menus et inventaire passent pour cette ROM.
  Le retour d'inventaire compare les motifs statiques parmi 124 tuiles,
  en excluant les quatre motifs animes des interieurs, pas une image complete.

## RAM et publication PSG

La premiere integration, v0193, utilisait un tampon global capable de
retenir toutes les ecritures des sept canaux. Son augmentation de BSS
provoquait un ecran noir avant l'installation du callback audio.
Cette compilation est conservee et marquee `boot_failed`.

La v0194 publie chaque prefixe/canal reussi via un callback, en gardant
le tampon de canal existant sur la pile. Elle evite une double execution
du lecteur. La BSS se termine a E0FFDF2C, contre E0FFE124 pour v0192 :
504 octets statiques sont economises. Les 8 404 octets physiques au-dessus
de la BSS comprennent le tas et la pile ; ils ne sont pas une mesure du
tas libre. Les tests de demarrage, menus et retours d'inventaire passent.

L'API de capture utilisee pour la recherche conserve un tampon complet et
restaure les 400 octets et DE en cas de refus. L'API de production diffuse
les ecritures par canal : les effets des canaux deja reussis restent publies
si un canal suivant refuse un contexte. Trois controles sur hote verifient
ces contrats distincts. Le cout est alors invalide et mis a zero, avec
diagnostic explicite ; aucun cout invente n'est utilise.

## Travail restant

Le cout du lecteur est maintenant disponible dans la ROM, mais ne pilote
pas encore une horloge SMS complete. L'enveloppe d'interruption, les acces
video et le code principal restent a composer avant le raccordement de R,
du generateur aleatoire natif et des attentes du jeu.

Les commandes E3/EC/EF/FE/FF et certains dispatchs non audites restent
explicitement refuses. Les bornes de lecture RAM et de chaines de commandes
restent celles des composants precedents. Les preuves ne couvrent pas
toutes les combinaisons possibles ni leur accessibilite naturelle.

Les mesures ne prouvent ni l'identite des formes d'onde, ni les instants
exacts de chaque ecriture PSG sur materiel physique, ni une progression
naturelle complete jusqu'a la fin. Le portage global reste incomplet.

Les sources, outils, rapports et captures sont figes localement dans
`native-audio-reader-v0194`, avec un manifeste SHA-256. Les ROMs numerotees,
rapports de publication et sources utiles sont versions dans le Git local.
