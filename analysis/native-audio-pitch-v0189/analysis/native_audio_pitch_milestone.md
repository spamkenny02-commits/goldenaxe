# Hauteurs, modulations et miroirs RAM — v0189

La routine SMS82C5 est traduite dans `source_audio_pitch.c` et raccordée au
lecteur de la ROM jouable. Elle conserve le délai de modulation, les compteurs,
le delta signé16bits, l'inversion du pas, les huit tables de hauteur, les
commandes80/83 et les retours anticipés81/82. Le composant renvoie HL, DE,
les400 octets audio, les cycles Z80 et les lectures M1.

Le suivi de DE couvre désormais aussi l'entrée indépendante en vibrato :
DE est conservé pendant le délai puis reçoit le pointeur de modulation.
Le modèle précédent n'exposait explicitement DE que pour les tables de
hauteur. Cette extension a été comparée aux instructions originales.

`source_audio_memory.c` partage les lectures entre hauteur, enveloppes et
séquences. Les400 octets audio DE00..DF8F et leurs miroirs FE00..FF8F utilisent
le même état, comme la RAM SMS répétée tous les8Kio. Cela corrige notamment
la commande de volume83 après une transposition négative donnant DE=FFxx.
La ROM fixe et la banque6 restent les données originales. Une lecture de
RAM non fournie est signalée, sans la remplacer par des octets de banque6.

## Preuves ciblées

- Source : 59 848 cas par région, sur82C5/banque6 inchangés avec un appelant
  DI contrôlé. Les400 octets, cycles, M1, R, HL, DE et retours anticipés
  correspondent. Les432 cas de tables de modulation en RAM comprennent
  les adresses DE40/FE40/DF70/FF70. Les16 retours81/82 utilisent des modes
  synthétiques hors des huit tables habituelles.
- Natif : 59 852 cas passent sur hôte, puis en code68000 sous Genesis Plus
  GX, en PAL et NTSC. Les mêmes sorties sont comparées directement, sur
  sept positions de canal et quatre adresses de retour. Trois lectures
  de RAM non fournie sont refusées sans mutation ; FFFF+1 est aussi testé.
- Enveloppes : les53 600 cas existants repassent sur hôte et68000 avec le
  lecteur mémoire partagé. Les autres branches ne régressent pas.
- ROM jouable : 116 états contrôlés couvrent les six canaux tonals, le
  vibrato signé, les compteurs, les tables de modulation ROM/RAM et les
  lectures de hauteur83 via DE/FE/DF/FF. Les400 octets et DE correspondent
  à la SMS exécutée et au modèle après une interruption.
- 60 autres états couvrent les enveloppes et leurs limites, dont six
  transpositions négatives lisant FF81..FF8F dans chacune des deux régions.
- Les22 400 retours DE/399 octets (hors routage GG), les13 musiques,
  les29 bruitages ordinaires, les29 effets prioritaires PAL/NTSC, le fondu
  musical et les parcours naturels du menu passent leurs régressions.

Les états et demandes audio sont contrôlés dans ces tests, sauf les parcours
naturels du menu. Les comparaisons de registres PSG ne prouvent pas une
égalité des formes d'onde ni le comportement d'une console physique.

## Travail restant

Les coûts calculés n'alimentent pas encore l'horloge du jeu. Le comptage
natif des séquences et des canaux, les commandes hors modèle (dont F2 du
canal de bruit), les autres zones RAM nécessaires aux lectures indirectes,
le callback d'interruption, R et le hasard original restent à raccorder.
Les boucles de contrôle non terminantes sont refusées après256 étapes.
La production conserve encore le hasard SGDK et des budgets fixes ; la
fidélité globale et une partie complète restent à vérifier.
