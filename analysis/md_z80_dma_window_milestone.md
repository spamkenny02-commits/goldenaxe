# Première primitive DMA coordonnée avec le Z80

`md_z80_video_dma_try` exécute un transfert de 32 octets quand le pilote
accorde le bus, avec un horodatage pair récent et dans une partie conservatrice
du VBlank. Les commandes DMA sont calculées avant la prise du bus. Après
BUSACK, le code relit un instantané complet, vérifie l'accord et l'âge du
compteur, puis écrit les commandes préparées et libère le bus. La fenêtre
raw V=235..252 exclut la duplication de six lignes du compteur NTSC.
Les deux mots de commande proviennent de la RAM, conformément au séquencement
du SGDK. La source doit être alignée, lisible par DMA et rester dans une banque
de 128 Kio. L'auto-incrément VDP est réglé à deux via SGDK, y compris sur WAIT.

## Résultats et limites de débit

Le [banc allégé](md_z80_psg_video_dma_snapshot_bare_report.json) et son
[homologue de preuve](md_z80_psg_video_dma_snapshot_proof_report.json) passent
les 48 cas source et 2 976 octets par région, leurs dates logiques, traces IRQ,
états finaux et empreintes. Le second conserve aussi les seize captures
intermédiaires. Les 384 intervalles de rafale contrôlés dans ces deux noyaux
restent exactement à 315/630 ticks ; aucune écriture anticipée n'est observée.
La plus grande distance entre lectures d'horloge est de 16 785 ticks,
sous la limite de 17 100. Les prises de bus audio restent sous 6 840 ticks.

L'[analyse des fenêtres physiques](md_z80_dma_windows_report.json) identifie
le chemin de succès par les instructions natives de commande DMA et son PC
de libération du bus, sans seuil de durée. Elle compte exactement **2 784 DMA
par région et par noyau**, tous en VBlank, avec un maximum de **3 676 ticks**
pour la demande jusqu'à la libération du bus. Chaque lecture du raster sous
bus acquis concorde avec son instant physique et les tables HV. Aucun
échantillonnage Z80 n'a lieu entre cette lecture et la libération ; une
instruction Z80 peut finir entre BUSREQ et BUSACK. Les prises de bus ne
chevauchent pas les intervalles internes des rafales PSG vérifiées.

Les requêtes de la fixture sont conservées en ordre et toutes terminées.
Le débit reste cependant très insuffisant : dans le banc allégé, seulement
**2 DMA NTSC et 14 PAL sur 2 784** finissent pendant les appels de chargement.
Les autres sont principalement vidés après la fin de l'audio. Le dernier
travail peut terminer jusqu'à **102,65 images NTSC ou 53,77 images PAL** après
le retour du chargement. Cette file de requêtes déterministes ne fixe aucune
échéance par image et ne constitue pas encore une file de rendu du jeu.

Le retard audio maximal vaut 270 870 / 269 280 ticks, soit environ 5 ms,
contre environ 9 ms dans la fixture d'écritures CPU. **Ces nombres ne mesurent
pas un gain à charge vidéo exécutée équivalente** : la fixture CPU exécutait
ses 2 784 uploads pendant le chargement, alors qu'ici presque tout est reporté.
La prochaine étape est le service régulier des travaux vidéo pendant le
calcul, avec leurs vraies échéances et des transferts bornés plus utiles.

## Témoin de transfert effectif

La parité du motif final alterne sur deux états et revient à l'initialisation
après un nombre pair de requêtes. Une image finale identique serait donc un
témoin insuffisant. Le [contrôle intermédiaire](md_z80_dma_intermediate_report.json)
rejoue le même noyau sans le modifier et capture un état pair : à l'image 57
NTSC (deux uploads) et 52 PAL (huit uploads), les 32 octets VRAM correspondent
au motif demandé et diffèrent de l'initialisation. DMA est activé et sa
longueur restante est nulle. Les traces IO sont exactement le préfixe des
mesures complètes ; RAM/VRAM à cette image concordent avec le cœur sans
observateur. L'image intermédiaire a aussi été inspectée visuellement.

## Essais refusés conservés

Le contrôle exigeant le même raw V ne permettait aucun DMA : le temps de
publication du timestamp le rend déjà ancien. Une tolérance de deux lignes
avec l'upload SGDK général permettait le transfert, mais dépassait la borne
d'horloge ; des arrêts de bus d'environ 11 500 ticks ont été observés.
L'appel SGDK rapide seul restait trop long dans un cas, avec un intervalle
d'échantillonnage de 19 245 ticks. Un garde d'une ligne empêchait à nouveau
le vidage. Ces quatre essais sont explicitement marqués en échec.

La préparation des commandes avant la section critique permet le premier
passage PAL/NTSC. Une mesure intermédiaire conservant exactement le même
timestamp avant/après BUSREQ passe aussi, avec 3 158 ticks d'arrêt maximal,
mais ne fournit pas non plus le débit attendu. La variante retenue accepte
un instantané pair plus récent une fois le Z80 arrêté ; elle ne constitue
pas une amélioration mesurée du débit sur cette fixture.

Les rapports initiaux comportaient une phrase générique des tests CPU
excluant le DMA. Seule cette limitation rédactionnelle a été corrigée pour
les trois rapports DMA réussis. Les rapports antérieurs sont conservés et
leurs empreintes liées aux versions corrigées ; tous les résultats, noyaux
et captures restent identiques.

La ROM jouable reste **v0203**, inchangée. La nouvelle primitive est
expérimentale et absente du jeu courant. IRQ natives, rendu SMS, sprites,
scrolling, commandes utilisateur et échéances d'image restent à raccorder.
Les marqueurs PSG empêchent toujours de valider une onde sonore originale
non instrumentée. Les tests couvrent des phases finies sur émulateur.
L'archive locale `md-z80-dma-window-v0203` conserve les essais réussis et
refusés avant nettoyage vérifié. Le Git reste local.
