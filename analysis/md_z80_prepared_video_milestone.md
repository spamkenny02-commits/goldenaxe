# Transfert vidéo préparé, v0203 inchangée

Le transfert expérimental prépare maintenant un jeton DMA de 12 octets une
seule fois par motif. Les attentes conservent le jeton et le motif ; un
transfert réussi consomme le jeton. Le contrôle du mode, des adresses et de
la frontière de banque de 128 Kio sort ainsi de la boucle de reprise.

Deux variantes conservant le verrou de publication du compteur ont dépassé
20 000 images : la première en NTSC, la seconde en PAL malgré ses 48 cas
NTSC terminés. Elles sont rejetées et conservées dans l'archive locale.
Ces captures montrent une progression insuffisante ; elles ne prouvent pas
à elles seules la cause de chaque refus ni une absence totale de progression.

La variante retenue sur le banc utilise seulement l'octet V atomique.
Elle ne lit aucun des octets du compteur multioctet : son verrou de
publication n'est donc plus un filtre vidéo. Sous BUSACK, le code contrôle
encore ready, error, grant et l'âge V avec une lecture indépendante du
compteur matériel. La fenêtre reste V brut 235–252, âge maximal deux lignes.
Les protections du producteur audio et de son horloge restent inchangées.

## Mesures sur la même fixture de motifs

| Banc allégé | NTSC | PAL |
| --- | ---: | ---: |
| Ancien cache de motif : pire fin vidéo après chargement, en images | 122,108 | 67,855 |
| Jeton préparé et octet V : même mesure | 37,009 | 18,960 |
| Tentatives de transfert de la nouvelle variante | 214 226 | 116 123 |
| Transferts pendant le chargement | 4 | 16 |
| Transferts après la requête de fin de livraison audio | 2 780 | 2 768 |

Les 2 784 demandes sont toutes transférées par région. Le pire retard audio
mesuré vaut 176 760 / 183 795 ticks maîtres, soit environ 3,3 / 3,5 ms.
Il n'y a aucune émission anticipée et les 96 espacements intrarafale de
315/630 ticks sont exacts par région. Ce gain de vidage ne constitue pas une
preuve de rendu à la cadence du jeu : presque tous les transferts restent
après le chargement, et la charge est synthétique.

## Preuves et limites

- Les [deux exécutions allégées](md_z80_psg_video_byte_stamp_bare_report.json)
  et les [deux exécutions avec les 16 états intermédiaires source](md_z80_psg_video_byte_stamp_proof_report.json)
  terminent leurs 48 cas, avec les octets PSG, IRQ et états source attendus.
  Les grandes copies du banc de preuve augmentent les retards audio ; elles
  ne servent pas de mesure de production.
- L'[analyse des instructions et captures physiques](md_z80_prepared_dma_windows_report.json)
  retrouve 11 136 transferts sur les quatre exécutions. Chaque transfert
  reste en VBlank. Le maintien du bus ne dépasse pas 3 886 ticks ; les
  intervalles de prélèvement Z80 restent strictement inférieurs à cinq
  lignes. Les contrôles de non-recouvrement avec les rafales sont conservés.
- Le [témoin intermédiaire](md_z80_dma_intermediate_video_byte_stamp_bare_report.json)
  vérifie un motif réellement différent en VRAM, aux images 56 NTSC et
  48 PAL. Les préfixes de capture sont identiques à l'exécution complète,
  et le cœur sans instrumentation reproduit RAM, VRAM et image.
- Les [26 contrôles natifs par région](md_video_prepared_contract_report.json)
  vérifient disposition du jeton, adresses invalides, chevauchement,
  frontière de banque, mode et conservation sur INVALID/WAIT/FAULT.
  Les rejets précoces testés ne lisent pas le faisceau et ne prennent pas
  le bus. Un premier échec du banc venait de son attente incorrecte d'un
  passage en 240 lignes NTSC, ignoré par SGDK ; sa ROM et son log sont gardés.
- L'[ancienne capture réanalysée](md_z80_prepared_prior_windows_report.json)
  conserve les métriques précédentes. Les rapports initiaux sont également
  gardés avant la correction de leur phrase générique « even stamp », qui
  ne décrivait plus le chemin préparé. Les résultats numériques sont inchangés.

Les IRQ natives restent masquées et un seul propriétaire contrôle VDP et
bus. Les sources doivent rester intactes jusqu'au transfert ; seul un
transfert de 32 octets est couvert. Les marqueurs PSG de diagnostic
empêchent encore une preuve de l'onde sonore originale. La prochaine étape
est de traiter des données du vrai rendu et ses échéances, plutôt que de
déduire sa cadence du vidage final de cette fixture.

L'archive locale `md-z80-prepared-video-v0203` garde les variantes rejetées,
sources, noyaux, captures et rapports avant tout nettoyage vérifié. Le Git
reste local. La ROM jouable **v0203** et son empreinte restent inchangées.
