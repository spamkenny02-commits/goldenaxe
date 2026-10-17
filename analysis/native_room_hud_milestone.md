# Conversion complete de carte et HUD natifs, chaine 16D0..1DE8

`source_room_hud.c` prolonge la chaine graphique/cases avec 2279 et 1E4E.
Les 160 metatuiles deviennent 640 mots de tuiles (1280 octets), puis les
256 octets du HUD sont prepares : carte RLE, decalage des motifs,
icone 2x2, gemmes, or, magie, vie et attributs de priorite.

Les 24 contextes controles retrouvent les onze points SMS depuis 16D0
jusqu'a 1DE8 : durees, phases raster, R/M1, 331 octets RAM, 400 octets audio
et tous les instants d'acceptation des interruptions. Une seule horloge
et un seul contexte IRQ/audio traversent les fonctions, sans reinjection
intermediaire. Les 24 vecteurs passent egalement en 68000 compile PAL/NTSC.

Un nouvel observateur SMS lit les hashes FNV32 des 1280 octets de carte et
256 octets du HUD au point 1DE8. Ils correspondent directement aux sorties
natives sur les 24 parcours. Les anciens records de phase restent identiques,
ainsi que R et les deltas M1. Le contenu complet du buffer 1536 octets est
aussi controle contre un decodeur de reference distinct.

Les jauges conservent les octets source et la semantique DJNZ. En particulier,
une capacite dont le compteur derive vaut zero produit 256 tours. Les ecritures
peuvent donc depasser DB00..DBFF et atteindre les cases DC00..DCFF puis la
file DD00..DDFF. L'API conserve ce partage de memoire avec SourceIrqContext.
La vie partielle utilise 8F-(reste>>1), la magie vide utilise 91, l'or conserve
les trois chiffres avec zeros et les neuf gemmes reprennent les mots source.

Un controle de valeurs execute l'original 1E4E pour 9021 contextes distincts
dans les deux regions. Il compare octet par octet les 768 octets DB/DC/DD et
les cycles de premier plan, avec report de memoire entre les cas. Les valeurs
de vie/magie couvrent 0..255 pour les capacites8..128 par 8, avec les bornes
0,7,129,255 selectionnees ; l'or couvre 0..255 et les gemmes les 512 masques.
Ces dimensions varient independamment autour du contexte de base, pas selon
leur produit cartesien. M1 est compare au modele d'instructions audite ;
la phase/R/IRQ dynamique est couverte par les 24 chaines precedentes.
Les 9021 vecteurs sont aussi rejoues en 68000 PAL/NTSC, en dix lots
avec zero echec. La memoire est conservee entre les cas ; chaque lot reprend
l etat final source du lot precedent.

Reproduction :

- `python tools/validate_native_room_hud.py`
- `python tools/validate_native_room_hud_68k.py`
- `python tools/build_roomhud_data_core.py`
- `python tools/validate_roomhud_source_data.py`
- `python tools/validate_native_hud_values.py`
- `python tools/validate_native_hud_values_68k.py`

Les mises en situation des 24 parcours et le boot de controle des jauges
restent distincts d'une partie naturelle. Le second conserve 1E4E et ses
routines d'origine ; 1DE8 est un marqueur RET apres le CALL, IRQ desactivees.
Il ne constitue pas une preuve de synchronisation globale du jeu.

Le scope de la chaine reste celui des six salles class0, changement de
banque, C0AC=0, C041!=5 et bit0 de sauvegarde positionne. Restent l'attente
de transfert, l'upload video, la palette, les acteurs/heros/historique/RNG,
les autres branches et la propagation de phase avant raccordement global.
La ROM jouable v0198 reste inchangee tant que ce raccordement n'est pas fait.

Les noyaux de controle incluent journaux, hashes et comparaisons. Leur
execution ne prouve pas le budget temps reel du jeu. Le raccordement doit
etre profile et les boucles d horloge doivent pouvoir regrouper le travail
sans interruption avant activation, tout en conservant les points source.

Suite : la chaine va maintenant a24BF avec attente/restauration/transfert/
palette, seize points source, capturesVRAM1536 etpalette16, plus2048 cas de
palette source/68000 et640 controles de regroupementIRQoff. Voir
native_room_finish_milestone.md ; le raccordement temps reel reste ouvert.
