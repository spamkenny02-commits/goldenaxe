# v0271 : cadence de generation de la carte du monde

L'apercu finissait94 images trop tot en NTSC et80 en PAL dans la v0240.
La v0271 finit a la meme image SMS en NTSC et une image avant en PAL dans
les cas ordinaires. Les18 cas exterieurs testes finissent entre0 et1 image
avant la SMS, y compris les drapeaux de quete et les passages geles.

## Portage

Le decodage190B prepare160 cellules ; la reconstruction native des640 mots
d'une salle complete etait inutile pour l'apercu. Elle est retiree de ce
chemin. Les transformations de salle et les donnees sauvegardees restent
traitees par les routines natives existantes.

Le cout de190B est produit a la compilation depuis les instructions, RLE
et metadonnees ROM, pour les deux valeurs de drapeau et les deux etats de
la cloche. Les 1024 entrees16bits incluent les salles non utilisees a zero.
Le jeu ne contient pas l'interpreteur Python de developpement et ne lit
aucune capture d'emulateur. Les deux nouvelles tables occupent2064 octets.

Le cout844D de chaque pixel depend des quatre categories de cellules :
selection du demi-octet, retenue du calcul d'adresse et comparaison au
maximum precedent. Les boucles de rotation et les entrees/sorties VDP
comptent aussi. Les couts de boucles3220..3250 sont cumules sans arrondir
chaque salle. Le calcul deja passe sur MD consomme ce delai ; le jeu attend
seulement le travail source qui reste.

Pendant cette construction, la source fait des IRQ audio seules. Le budget
par interruption MD est59736 T en NTSC ou71364 en PAL, moins524 et le cout
du lecteur musical semantique courant. Ce debit se termine apres la musique,
avant la reprise du premier plan. Le travail complet de generation ordinaire
est27611056 T hors IRQ ; avec tous les drapeaux27829148 ; avec gel27646729 ;
avec les deux27863835. Aucune duree totale par salle issue d'un film n'est
embarquee. La publication MD conserve les tuiles completes de chaque salle.

## Verification

Un coeur d'observation distinct lit les entrees/sorties des routines sur la
ROM SMS inchangee. Les sources du coeur de travail sont restaurees apres sa
compilation. Les deltas retirent les vraies interruptions observees.

- 1125 chargements190B et leurs160 cellules,45000 projections844D et cinq
 generations completes : couts exacts. Quatre combinaisons quete/gel et un
 cas PAL. Les huit types de metadonnees exterieures rencontres sont verifies.
- Le vrai compteur C extrait de la production est compile sur l'hote :1125
 couts de salle correspondent au modele et aux instructions source.
- 22 scenarios PAL/NTSC :18 exterieurs et quatre gardes interieures. Dans les
 16 apercus stabilises,5120 octets graphiques et1280 octets de carte sont
 exacts ;108 images normalisees correspondent, dont deux cycles33 images
 des marqueurs. Les deux fermetures tenues pendant le dessin passent aussi.
- 18 retours :160 cellules et trois metadonnees restaurees ;256 drapeaux
 conserves, sauf les trois bits de passage attendus lorsque la cloche est
 active ;1536 octets de carte/HUD et l'image stabilisee correspondent.
- Regressions :401 etats et36 images du loot charge, sort niveau2 avec
 acteurs et12 compositions naturelles sans code audio non traite.

## Limites

La possession et les drapeaux sont controles. Une phase d'horloge est encore
alignee apres construction pour comparer les marqueurs. Le compteur C02F
complet pendant la modale, l'entree raster, le contexte terrain5 et le minutage
de restauration restent ouverts. Les dates mesurees portent sur la fin de
construction ; les ecritures pixel/plan de la SMS et les tuiles MD ne sont pas
une publication raster identique. Acquisition naturelle, partie complete,
RNG source, formes d'onde et materiel reel restent a terminer.

Rapport : [world_overview_pacing_release_v0271_report.json](world_overview_pacing_release_v0271_report.json).
