# Affichage actif et écritures VRAM avec le lecteur vivant

Le banc peut désormais activer le vrai raster H32/224 pendant le chargement
68000 et la restitution PSG Z80. Une tuile et une palette diagnostiques sont
installées avant le démarrage audio. Le mode `cpu` remplace ensuite les
32 octets de cette tuile à chaque callback de publication, par le chemin
CPU du SGDK. La tuile est répétée sur le plan A pour rendre le raster visible.
Ce motif synthétique teste la coexistence matérielle ; ce n'est pas le rendu
du jeu ni une comparaison de pixels avec la SMS.

| Banc | Retard maximal NTSC | PAL |
| --- | ---: | ---: |
| Lecture groupée + tentatives bornées, affichage désactivé | 162 180 | 162 435 |
| Affichage activé, tuile préchargée | 162 315 | 162 225 |
| Affichage activé, écritures CPU, mesure allégée | **473 790** | **479 190** |
| Même charge CPU, seize captures intermédiaires | 4 834 395 | 4 862 625 |

Les nombres sont en ticks maître. Le raster seul ne change pratiquement pas
le maximum. Le test avec écritures CPU atteint en revanche environ **9 ms**,
contre environ 3 ms sans ces écritures. Ce résultat ne permet pas d'intégrer
le pilote en conservant simplement les transferts vidéo existants. La dernière
ligne comporte en plus les copies de preuve, et ne mesure pas le budget allégé.
Les marqueurs de callback incluent ici le coût de l'écriture vidéo.

Les [mesures avec raster](md_z80_psg_video_display_bare_report.json),
[avec écritures CPU](md_z80_psg_video_cpu_bare_report.json) et leur
[homologue de preuve](md_z80_psg_video_cpu_proof_report.json) passent chacune
les 48 cas source et 2 976 octets par région, les dates logiques, traces IRQ,
états finaux et empreintes. Le dernier noyau vérifie aussi les seize points
intermédiaires. Les 576 intervalles de rafale vérifiés au total restent
exactement à 315/630 ticks. Aucune émission anticipée dans ces captures ;
les lectures d'horloge restent espacées de moins de 17 100 ticks et les prises
de bus de publication sont au plus de 4 102 ticks.

Chaque noyau CPU exécute 2 784 appels d'upload pendant le chargement par région,
en plus de l'initialisation. Les états physiques finaux confirment les 32 octets
attendus, les 896 entrées du plan A et le mode vidéo. L'image capturée comporte
les huit couleurs attendues et a été inspectée visuellement. VRAM, registres
et image sont conservés avec leurs empreintes. Le cœur sans observateur
termine sur la même image d'arrêt avec la même RAM que le cœur instrumenté.

## DMA : contrainte identifiée, test dynamique restant

L'[audit statique](md_dma_z80_policy_report.json) vérifie que le SDK local
configure `HALT_Z80_ON_DMA=1`. Il vérifie aussi directement dans la ROM v0203
le chemin VRAM de `DMA_doDmaFast` : A0 pointe sur BUSREQ, le bus est pris à
0x26E76, le DMA est déclenché à 0x26E82 et le bus libéré à 0x26E86. Les sources
du cœur montrent aussi un modèle d'attente du Z80 quand le DMA occupe le bus
68000. Ce sont des preuves statiques ciblées ; aucune incompatibilité DMA
n'est présentée ici comme un défaut reproduit en exécution.

Le pilote PSG exige des lectures rapprochées et protège ses rafales avec
un accord de transfert. Les prises de bus pour DMA devront être coordonnées
avec cet accord et leur durée mesurée. Le prochain travail porte sur ces
fenêtres vidéo, puis les interruptions natives et le rendu du jeu. Simplement
désactiver l'arrêt Z80 dans le SDK ne constitue pas une solution validée.

La ROM jouable reste **v0203**, inchangée. Aucun DMA, sprite, scrolling,
contrôle utilisateur ou IRQ natif du jeu n'est validé par cette fixture.
Les marqueurs natifs au PSG ajoutent des écritures et empêchent encore de
revendiquer une onde sonore originale non instrumentée. Le retard maximal
reste sans garantie globale de fidélité.

L'archive locale `md-z80-video-v0203` conserve sources, rapports et captures
avant nettoyage vérifié. Le Git reste local.
