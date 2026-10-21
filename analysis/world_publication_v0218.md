# v0218 : publication du monde au VBlank

La ROM jouable prepare maintenant les sprites et leurs tuiles masquees en RAM,
puis les publie au VBlank avant le lecteur musical. La v0210 copiait la table
apres le lecteur, parfois pendant le balayage. Sur PAL3120, cette copie occupait
les lignes31 a38 et pouvait montrer une liste partiellement mise a jour.
Le nouveau transfert termine vers la ligne228 dans cette capture, avant
l'image active. Le parcours NTSC correspondant termine a229, dans son VBlank.

La preparation et la consommation utilisent un drapeau publie apres les donnees,
avec barrieres compilateur. Le foreground attend la consommation avant de
reprendre la simulation. Les jobs et clones occupent2624 octets d'une union
partagee avec les7248 octets de sauvegarde des dialogues: ces phases sont
exclusives, et aucun second gros buffer permanent n'est ajoute au tas DMA.
Une assertion de compilation verifie la capacite du stockage.

Les mises a jour d'atlas du meme IRQ alimentent aussi les clones, tandis qu'une
pose volontairement retardee conserve le motif resident. Le statut de
depassement SMS garde son ordre de lecture avant la publication suivante.
La valeur Y=208 coupe maintenant la chaine materielle MD, y compris en tete;
les acteurs restent en RAM et les sprites apres le marqueur ne sont pas dessines.

## Cadence des transitions

Les routines originales208A/2090 et20CA/20D0 ont ete observees sans modifier la
ROM SMS. Elles terminent vingt etapes verticales, une par image dans les deux
regions. Le depart montant inclut les echanges de buffers2099; son attente
native est ajustee a ce chemin apres le deplacement de la publication.

Les quatre scrollings verticaux testes (haut/bas, PAL/NTSC) concordent maintenant
sur les80 images de publication et tous leurs intervalles. La pause d'une image
constatee dans l'ancien scrolling NTSC disparait sur ces parcours. Les dix fins
de transition testees restent stables des l'image suivante, sans ancienne carte.
Ces resultats ne prouvent pas la cadence de toutes les salles ni tous les
mouvements du heros; les ecarts de simulation restants sont conserves au rapport.

## Verification de la ROM complete

Les rapports joints a la ROM et le [bilan des controles](world_publication_v0218_report.json)
lient chaque resultat au meme SHA256:

- 12 images de jeu PAL/NTSC,614400 pixels de la zone jeu/HUD compares a une
 reconstruction independante VRAM/CRAM: aucun ecart;
- 5 transferts SAT observes par region, tous termines dans le VBlank; l'image3120
 du coeur observateur reste identique a celle du coeur standard;
- 40 images de test du terminateur et24 images de chevauchement de douze acteurs,
 avec conservation de la limite de huit sprites par ligne;
- 130 lignes/scenes de l'intro naturelle, retour au titre et cadence sans derive;
- 4 parcours de bruitages Nouveau jeu/Continue et6 parcours d'inventaire verifies,
 dont les deux premieres maisons.

Les differences d'images naturelles par rapport a v0210 sont controlees par la
reconstruction complete, et non ignorees. La phase des PNJ peut changer avec
l'ordonnancement: le PRNG SGDK provisoire ne reproduit pas encore le registre R
source. Aucun pourcentage global ni equivalence de toutes les trajectoires
n'est deduit de ces tests. L'animation des quatre tuiles de maison reste exclue
du controle statique d'inventaire, comme indique dans son rapport.

## Livraison et limites

Utiliser v0218/1Mio, checksumAA56. Les v0211..v0217 sont conservees comme etapes
intermediaires. Les chemins de publication immediate utilises hors de l'attente
normale du monde gardent leur comportement precedent. Les autres salles, une
partie complete, l'aleatoire source, le waveform et le materiel restent a valider.

Les preuves sont archivees localement avant nettoyage des captures generees.
Les rapports et le manifeste sont versionnes; les gros objets gzip restent locaux.

Archive finalisee:4781 references compressees,184074650 octets generes retires,
165540262 octets nets liberes (environ157,9Mio). Lecture gzip/SHA complete et
reconstruction identique apres nettoyage:614400 pixels RGB,80 etapes source
et10 transferts SAT VBlank. Les218 ROMs numerotees sont conservees.
