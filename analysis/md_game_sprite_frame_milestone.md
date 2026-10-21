# Publication MD des sprites produits par l'interruption du jeu

`MdGameSpriteFrame` relie le paquet SAT de `SourceGameIrqContext` au flux
`MdSmsSprite8Stream`. Le callback de l'interruption copie les192 octets et
les dates source dans son propre stockage. Le travail VDP se fait ensuite
par transferts caches de1 a4 tuiles, puis quatre blocs couvrant les64 entrees
SAT Mega Drive, meme pour une liste vide.

Les attentes conservent le paquet et les donnees preparees. Une seconde
interruption complete avant la fin de livraison est une erreur fatale:
aucune table n'est remplacee ou abandonnee pour masquer un retard. Les dates
source sont conservees; leur presence ne prouve pas une livraison physique
a l'heure. Un seul proprietaire foreground utilise le VDP, interruptions
natives masquees et affichage coupe. Le buffer de motifs reste immutable.

## Verification physique

Le [banc68000](md_game_sprite_frame_report.json) reprend les133 cas de la
chaine0938 ->0B95 ->IRQ originale ->retour dans chaque region. Le callback
compare d'abord chaque valeur/date OUTI a l'original SMS puis remet la table
au nouveau module. Apres retour de la routine, la SAT en RAM du jeu est
volontairement ecrasee avant le premier transfert: le rendu doit utiliser
sa copie possedee. L'execution sans trace reste comparee a la chaine source.

Pour chaque cas, la VRAM physique issue des DMA est capturee et decodee
independamment du convertisseur natif. Les49152 pixels du plan de sprites
concordent avec la SAT originale et les motifs planaires SMS. Les entrees
apres la fin de liste sont toutes nulles, y compris apres un cas plus rempli.

Par region PAL/NTSC:

- 133 compositions et133 plans physiques exacts, soit6537216 pixels compares;
- 1132 travaux DMA et71936 mots VRAM relus sans erreur;
- 217 interruptions source et592 octets PSG toujours compares exactement;
- des attentes reelles de transfert, sans perte du paquet;
- 5 controles natifs de propriete avec date enveloppee, file pleine, erreur
 fatale, refus de reconfiguration pendant livraison et date malformee.

Le [controle de recuperation](md_game_sprite_frame_recovery_report.json)
compare aussi les octets des entrees banques/RAM/traces effectivement lies
au binaire68000 aux preuves source precedentes. Il peut relire les captures
VRAM dans l'archive gzip apres nettoyage.

## Limites et suite

Le banc utilise un buffer de motifs capture, des statuts VDP observes et
une RAM initiale fournie. L'affichage reste coupe; le resultat prouve le
contenu VRAM du plan de sprites, pas une image composite ni son instant de
revelation. Les commandes PSG restent comparees dans la chaine logique;
ce banc ne les livre pas encore au PSG materiel. Le coprocesseur Z80 sert
ici a autoriser les DMA bornes avec son horloge et ses grants existants.

La suite doit reunir livraison physique PSG et sprites, mesurer les delais
aux dates de la SMS et integrer les motifs/evolutions autonomes des acteurs.
Le boot et une partie complete du nouveau moteur restent non valides.
La ROM jouable recommandee restev0203; ce noyau n'est pas une v0208.

Les preuves sont figees dans `md-game-sprite-frame-v0203` avant nettoyage.

Archive finalisee:387 references compressees;36800813 octets generes retires,
33383292 octets nets liberes (environ31,8Mio). La recuperation des266 plans
physiques depuis gzip et le controle des octets ROM donnent le meme rapport
apres nettoyage, octet par octet. Les207 ROMs numerotees sont conservees.
