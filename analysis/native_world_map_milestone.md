# Preparation native des cartes 190B, chaine 16D0..24BC

La chaine native conserve maintenant la meme horloge et le meme contexte
IRQ/audio depuis 16D0, a travers le chargement graphique complet, puis 190B
jusqu'au retour 24BC. Les neuf points 1706,170E,1720,1733,1748,24B9,192A,192D,
24BC retrouvent les captures SMS sur les 24 contextes controles disponibles.
La duree, phase raster, R/M1, 331 octets RAM, 400 octets audio et tous les
instants d'acceptation des interruptions concordent. Aucun etat intermediaire
n'est injecte. Les 24 vecteurs passent aussi en 68000 compile PAL/NTSC.

`source_world_map.c` decode les 160 cases, cherche les trois octets de
metadonnees dans la banque2, applique la transformation persistante et la
transformation eventuelle de la case suivante, prepare les deux rangs de
tuiles de chaque case modifiee, puis restaure les metatuiles animees et vide
la file video. Le decodeur RAM0C00 est extrait dans `source_ram_planes.c`
et partage avec le chargement graphique. Les controles de celui-ci sont
repasses apres cette extraction, sur hote et 68000 dans les deux regions.

DC00..DCFF utilise le tampon de cases du caller. DD00..DDFF utilise la RAM
de `SourceIrqContext`, car cette zone sert aussi de file video. Les acces
sont partages, y compris pour la coordonnee speciale FF : la modification
de DCFF et les deux rangs de tuiles en DDBC/DDC0 sont conserves. Les INC L
de la file respectent aussi le retour sur l'octet bas. La conversion complete
des cases vers la carte de tuiles 1DE2 n'est pas encore dans cette API.

Un observateur SMS distinct ajoute des hashes FNV32 de 160 cases, trois
octets de metadonnees, huit octets de tuiles de la modification principale
et deux cases modifiee/suivante. Ces valeurs sont confrontees directement
aux sorties natives sur les 24 parcours. Tous les anciens records de phase
restent identiques ; R et les deltas M1 restent exacts. Les buffers complets
de controle utilisent aussi une sentinelle pour verifier que les autres
octets ne sont pas ecrases. Les octets non reecrits du jeu reel restent
fournis par le caller ; leurs valeurs ne sont pas supposees nulles.

Reproduction :

- `python tools/build_world_data_core.py`
- `python tools/validate_native_world_map.py`
- `python tools/validate_world_source_data.py`
- `python tools/validate_native_world_map_68k.py`

Les mises en situation originales des six passages sont conservees ; ce
controle n'est pas une partie naturelle complete. Le scope natif est celui
audite : graphismes exterieurs class0 avec changement de banque, C0AC=0,
C041!=5, six salles de destination et bit0 de sauvegarde deja positionne.
Les autres salles/branches et valeurs de sauvegarde restent a traduire.

La recompilation produit les octets exacts de v0198. Le chemin d'horloge
reste separe de la ROM jouable tant que le demarrage et les appels precedents
ne transmettent pas leur phase logique. Restent notamment 1DE2/HUD, acteurs,
heros, historique/RNG et revelation, puis leur raccordement global.
