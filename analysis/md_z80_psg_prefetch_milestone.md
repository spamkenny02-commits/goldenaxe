# Préparation anticipée des commandes PSG

Le nouveau pilote expérimental `megadrive/z80/md_psg_prefetch_z80.asm` prépare
les commandes suivantes pendant les attentes suffisamment éloignées de la date
active. Le jeu, les chargements et le lecteur sonore restent en 68000. Le pilote
antérieur `md_psg_output_z80.asm` et la ROM jouable v0203 restent inchangés.

La file interprocesseur reste composée de 32 descripteurs de 22 octets en RAM
Z80, avec publication atomique du curseur par le 68000. Le nouveau pilote copie
chaque descripteur dans un tampon local avant de libérer son entrée de file.
Il dispose de seize tampons, une commande active et jusqu'à quinze suivantes.
Les valeurs occupent une seule page locale, avec seize valeurs possibles par
tampon. Les curseurs de préparation et de restitution avancent séparément.
`busy` reste actif lorsqu'une commande locale est encore en cours, même si la
file interprocesseur est vide. L'horloge publique reste impaire durant les
phases critiques ; des relevés privés bornent les copies et l'attente finale.

## Mesures retenues

Le [rapport final](md_z80_psg_prefetch_measured_report.json) mesure le même trajet
chargement/IRQ/lecteur/file natif, avec deux origines et deux régions physiques.
Les 5 952 octets source et les points de contrôle restent conformes.

| Pilote | Retard maximal NTSC, ticks maître | PAL |
| --- | ---: | ---: |
| Publications privées, copie déroulée | 84 390 | 84 345 |
| Préparation anticipée, mesures de profondeur | **32 385** | **33 795** |

Le retard maximal baisse encore d'environ 60 %, à environ 0,63 ms. Le retard
minimal mesuré reste de 3 480 / 3 540 ticks. Cette précision est encore
insuffisante pour accepter le pilote comme ordonnanceur fidèle.

Le banc conserve les 24 cas de rafale partielle par région et les 512 commandes
de la session longue. Il ajoute 64 commandes mixtes, 32 à 315 ticks et 32 à 630,
avec 416 valeurs distinctement calculées par région. Les seize positions locales
sont parcourues, y compris une rafale maximale terminant sur la fin de page.
Les 1 192 intervalles internes contrôlés sont exacts dans Genesis Plus GX.
Le compteur de diagnostic confirme 64 préparations anticipées dans la session
longue finale et une profondeur maximale de quinze commandes en attente.

Les captures contrôlent 1 885 publications d'horloge contre les lectures vidéo
physiques indépendantes. Les intervalles maximaux de lecture sont de
15 585 / 16 080 ticks, sous la borne de 17 100 ; les écarts de compteur restent
au plus de cinq lignes. Les prises de bus mesurées restent au plus à 4 242 ticks
et ne chevauchent pas les intervalles internes des rafales vérifiées. Le calcul
68000 témoin concorde avec son oracle indépendant. RAM finale et image d'arrêt
concordent avec le cœur sans observateur. Les rebouclages de la file, du compteur
de ligne et des dates logiques restent testés.

## Essais intermédiaires conservés

* `prefetch-two` : un tampon d'avance, rejeté après une erreur d'horloge NTSC.
* `prefetch-guard` : les relevés supplémentaires corrigent cette erreur sur les
  cas testés, mais la latence maximale monte à 128 370 / 128 415 ticks.
* `prefetch-sixteen` : le tampon circulaire fonctionne sur les valeurs testées,
  mais un intervalle de lecture de 17 400 ticks dépasse la borne ; rejeté NTSC.
* `prefetch-bounded` : les copies sont échantillonnées séparément ; vérifié dans
  les deux régions, puis étendu au parcours des seize positions.
* `prefetch-slots` : le parcours mixte passe en PAL/NTSC, puis deux compteurs de
  diagnostic rendent la préparation anticipée et sa profondeur observables.
* `prefetch-depth` : rejet de l'assemblage, branche relative devenue trop longue.
  La version finale utilise un saut absolu et passe le banc complet.

Les échecs interrompus en NTSC ne sont pas présentés comme des essais PAL.
Les sources, journaux et captures de chaque variante sont conservés dans
`analysis/md-z80-psg-prefetch-v0203` avant nettoyage vérifié des fichiers générés.

## Travail restant

Le calcul source se termine encore avant la restitution temporisée. Le calcul
68000 simultané est un témoin polynomial, pas le véritable chargement vivant.
Les tests n'activent ni DMA ni interruptions natives. Il reste à réduire le
coût de passage entre commandes prêtes et à tenir leurs échéances, puis raccorder
le vrai producteur et mesurer l'ensemble avec affichage, entrées et interruptions.
La phase globale depuis le boot, l'abandon immédiat sur erreur, le jeu complet
et la console réelle restent à vérifier. Ce jalon ne change pas la recommandation
de ROM jouable et n'établit aucun nouveau pourcentage global de finition.
