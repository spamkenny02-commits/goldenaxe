# V0220 : publication du texte des conversations au VBlank

La copie CPU des 130 motifs de texte pouvait traverser le balayage de l’écran.
Sur le dialogue du premier PNJ, la v0219 présente dix images incohérentes en
NTSC et cinq en PAL : les pixels affichés diffèrent du texte en mémoire vidéo
à la fin de l’image. La v0220 prépare les motifs en RAM, puis confie leur DMA
à l’interruption VBlank avant le lecteur musical. Le producteur attend la fin
de la copie avant de réutiliser le buffer. Il n’ajoute aucun second buffer.

Le chemin s’applique aux conversations/services utilisant house_dialogue_active.
L’intervalle minimal de publication du bitmap est de deux images ; le défilement
conserve son attente NTSC supplémentaire. Ce choix ne prouve pas que toutes
les dates de chaque mot correspondent à la source.

## Vérifications

- Premier PNJ : position contrôlée après entrée normale dans la maison,
  151 images actives par région. Les 2 512 640 pixels de la zone de texte
  concordent avec un décodage indépendant des motifs, palette et table vidéo.
  Zéro image incohérente en v0220 contre 10 NTSC / 5 PAL en v0219.
- Six PNJ : bitmap, pixels de texte hors marqueur clignotant et restauration
  du décor/état comparés à la source SMS ; un trajet de conversation se fait
  entièrement au contrôleur. Ces tests existants sont en NTSC.
- Premier marchand : sept cas d’achat/refus/inventaire plein ou objet possédé,
  et un trajet naturel de refus/sortie. État, bitmap du message et absence de
  coupure du HUD sur les images d’entrée/sortie testées sont vérifiés en NTSC.
- Défilement du dialogue d’ouverture : les listes d’images des quatre poses
  sont identiques à la v0219 en PAL/NTSC. Le contrôle strict de durée SMS
  échoue sur les deux ROMs : la pose finale NTSC dure une image de trop.
  Ce défaut préexistant est conservé comme limite, pas déclaré corrigé.

Le test de pixels ne prouve pas à lui seul les cycles exacts de transfert.
Tous les marchands, l’audio en forme d’onde, le hasard Z80, une partie complète
et la console physique restent hors de ces vérifications.

ROM 1 Mio : versions/v0220-b49be582/gaw-megadrive-v0220.bin.
SHA-256 : b49be582d3019f00e396840b1d0716b75f3ada775e298c75049c1e0216266202.
Checksum Mega Drive : 2A09.
