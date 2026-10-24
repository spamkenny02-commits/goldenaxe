# Transferts video des interruptions - 24 octobre 2026

Le module source_irq_video traduit les livraisons video de l'IRQ complete0137.
Il est branche, par un callback optionnel de SourceIrqContext, avant le travail
audio et la validation finale de l'IRQ. Sans callback, le comportement reste celui
du chemin precedent. Un echec apres publication impose l'abandon de la session.

Les miroirs recoivent les registres8/9/10, SAT64+128, le bitmap du heros en trois
plans avec insertion du quatrieme plan nul, les60 octets de HUD selectionnes et
les32 couleurs effectives6bits. La file0293 couvre les blocs ROM et SRAM, les
rectangles RAM avec pas64 et les descripteurs mixtes. Une copie compacte privee
simule le terminateur et les hauteurs modifies pendant une lecture de la file :
la RAM du contexte reste intacte pour le traitement canonique de l'interruption.
Les adresses VRAM rebouclent sur14bits. La SRAM optionnelle expose16KiB8000..BFFF.

Validation :

-288 cas sur le Z80 original : bitmap absent/banque4/banque5, quatre choix de HUD,
 six files (vide,ROM,SRAM,rectangle,mixte,auto-lecture), palette active/sautee,
 NTSC/PAL. Toute la VRAM16KiB,32 couleurs effectives et les registres8..10 sont
 compares. Les routines IRQ et les banques4/6 sont inchangees dans le banc.
-576 executions compilees68000 passent : les288 vecteurs dans chaque region
 physique, repartis en six cartouches pour respecter la taille ROM.
-La chaine16D0..premiere attente du contour a ete rejouee avec le callback actif :
 24 parcours source et48 executions68000 passent,1056 points controles. Les temps,
 R/M1, RAM/audio et tous les decalages IRQ demeurent identiques. Seules les plages
 graphiques deja observees ont une preuve source dans cette chaine ; les autres
 octets du miroir sont compares a l'hote, avec la preuve source separee ci-dessus.

Les IRQ materielles sont desactivees dans les cartouches de diagnostic68000.
Ces preuves concernent les donnees et l'horloge logique, pas les instants physiques
par octet, le rendu a l'ecran ou la cadence SGDK. La chaine reste hors du jeu ;
les contours, publication SGDK, origine globale, autres classes et campagne
complete restent ouverts. La ROM jouable reste v0275.

Rapports : native_irq_video_report.json, native_irq_video_68k_report.json et
native_room_reveal_report.json/native_room_reveal_68k_report.json actualises.
Les anciens rapports lies a leurs anciens SHA restent des preuves historiques.
