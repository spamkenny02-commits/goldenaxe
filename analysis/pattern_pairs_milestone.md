# v0202 : conversion des motifs et cadence des interfaces

La ROM jouable v0202 utilise une table universelle de 65 536 paires de plans
SMS : deux lectures de table produisent une ligne Mega Drive, au lieu de
quatre. La table coûte256 Kio de ROM ; le binaire complet reste à1 Mio grâce
à l’espace disponible. Les lectures 16 bits sont explicitement alignées et
compatibles avec les écritures par octet du miroir SMS.

L’accélération est activée dans l’intro, le titre et l’inventaire. Les
chargements des portes et la conversion générale conservent leur ancienne
routine : leur temps CPU participe encore à leur cadence tant que l’horloge
source n’est pas raccordée. Les variantes globales v0199/v0200 avançaient
certains événements et sont conservées comme diagnostics, avec la v0201.

Les noirs de l’inventaire PAL avaient une image supplémentaire à l’entrée
et à la sortie. La publication du plan intervient maintenant au même délai
que les parcours SMS testés, sans modifier le moment de reprise du jeu.
Le fondu du titre calcule sa palette dans un tampon et la publie au VBlank,
évitant un premier palier du guerrier de 7 images au lieu de 6.

## Vérifications

- 65 536 paires testées indépendamment dans les deux moitiés de chaque ligne,
 sur PC et 68000, face à un oracle qui développe les bits en pixels. Compte
 nul et tampon mixte complet de 512 tuiles également vérifiés.
- Sur 32 conversions de 512 tuiles : 276 images CPU contre 169 en NTSC, 231
 contre 141 en PAL, soit environ39 pour cent de coût CPU en moins. Écran
 éteint et même entrée ; cette mesure n’est pas un gain global de FPS.
- Six parcours naturels d’inventaire PAL/NTSC retrouvent les mêmes fenêtres
 noires et la même reprise SMS, avec HUD conservé et fermeture silencieuse.
 Les motifs statiques parmi les 124 premiers sont vérifiés avant/après le
 menu ; les phases des quatre tuiles animées des maisons restent exclues.
- Les choix et validations Nouveau jeu/Continuer déclenchent les mêmes
 bruitages aux mêmes images que la SMS, avec sorties PSG actives.
- Quatre contrôles du titre : PAL/NTSC, intro passée ou démarrage naturel.
 33 poses de cape de 6 images, paliers du guerrier de 6, 8 lignes de titre à
 une image chacune,80 contrôles de pixels normalisés pour les DAC.
- Les65 lignes et cartes de scènes de l’intro concordent dans les deux
 régions. Les décalages absolus restent de 9..11 images NTSC et -13 PAL ;
 leur étendue ne dépasse plus 2 images. Le retour au titre est vérifié.
- Quatre allers-retours contrôlés maison/donjon conservent les fondus et
 l’ordre des commandes musicales ; le temps absolu de chargement n’est
 pas déclaré équivalent.

L’audit lie ces 11 rapports au même binaire, vérifie le checksum et les
copies, conserve la routine générale et vérifie que les autres sources
natives suivies sont inchangées depuis le commit 458dc5a.

## Limites et suite

Le portage complet, l’horloge commune depuis le boot, tous les embranchements,
les phases de sprites de l’intro et une partie complète naturelle restent
à vérifier. Les acteurs/héros et la cadence globale ne sont pas déclarés
terminés. Les cadres noirs et inventaires testés ne couvrent pas toutes les
possessions ni tous les donjons. Les pixels normalisés ne prouvent pas
l’équivalence des signaux vidéo ou audio sur matériel.

La conversion plus rapide offre maintenant de la marge réelle dans les
chemins actifs testés. La chaîne de chargement avec horloge reste une
recherche distincte à optimiser puis raccorder ; aucune table de phases
capturées n’est introduite.

Les rapports immuables sont joints à la ROM dans
[versions/v0202-f55643bb](../versions/v0202-f55643bb/).
