# Du miroir graphique SMS aux tuiles Mega Drive

Le nouveau banc utilise les 16 384 octets du miroir graphique réellement
produit par le chargement 68000, la carte, le HUD et la préparation de salle.
Chaque chargement convertit ses 512 tuiles avec `pattern_convert`, puis les
transfère en VRAM Mega Drive aux indices 16–527 via les jetons DMA préparés.
La source reste intacte jusqu'au vidage complet ; les conversions et jetons
ne sont pas recalculés pendant WAIT.

Après chaque transfert, le 68000 relit les 16 mots du VDP et les compare au
motif avant de libérer le tampon. Au total, les deux variantes en PAL/NTSC
effectuent **98 304 transferts et 1 572 864 lectures de mots**, sans différence.
Les 512 tuiles finales sont aussi vérifiées octet par octet par une conversion
Python indépendante des quatre plans SMS. L'empreinte du miroir correspond
à l'état final source attendu ; elle est identique dans les quatre captures.

## Contrôles terminés

| Variante | NTSC, image de fin | PAL, image de fin |
| --- | ---: | ---: |
| Allégée | 21 136 | 13 120 |
| Avec les 16 états source intermédiaires | 21 656 | 13 511 |

Les [rapports allégés](md_z80_psg_video_source_patterns_bare_report.json) et
[avec états intermédiaires](md_z80_psg_video_source_patterns_proof_report.json)
terminent 48 cas par région. Les états, IRQ, dates et octets PSG attendus
concordent. Aucun octet audio n'est émis en avance et les 96 espacements
intrarafale par région restent exacts. Le cœur sans instrumentation donne
la même RAM, la même VRAM et la même image finale.

L'[analyse physique du DMA](md_z80_source_video_windows_report.json) retrouve
les 98 304 transferts par leur chemin d'instructions compilé, sans les
déduire des seuls compteurs. Tous restent en VBlank, hors des rafales PSG.
Le maintien maximal du bus vaut 4 138 ticks maîtres et l'intervalle maximal
de prélèvement Z80 vaut 16 785 ticks, inférieur à cinq lignes (17 100).
La [réanalyse des anciennes captures](md_z80_source_video_prior_windows_report.json)
conserve leurs résultats numériques.

Le premier lancement a atteint la fin native, puis l'observateur a échoué
sur `output`, renommé `output.lto_priv.0` par LTO. La correction du choix de
symbole ne change aucun octet du noyau ; son empreinte initiale est conservée.
Les captures complètes viennent de la relance corrigée. La classification
des fenêtres dans le validateur utilise ensuite une recherche dans les dates
triées, au lieu d'une recherche linéaire pour chaque tentative. L'analyse
physique des chemins compilés reste indépendante de cette classification.

## Ce que ce banc ne valide pas

L'image est un **atlas de contrôle**, avec palette et disposition de diagnostic,
et inclut les régions inutilisées du miroir. Elle ne reproduit pas encore la
scène SMS, ses palettes, sa carte, ses sprites et son scrolling.

Tous les transferts commencent après le travail source et la livraison audio.
Le pire vidage après chargement allégé vaut environ 330 images NTSC et
173 PAL. Ces durées comprennent la relecture de chaque mot VDP et le service
par blocs de seulement 32 octets ; elles ne mesurent pas le coût d'un moteur
de rendu de production. Le retard audio allégé reste voisin de 3 ms, mais ne
prouve pas un rendu simultané à charge équivalente. Les grandes copies des
états source augmentent le retard du banc complet.

Il faut maintenant mesurer le transfert réel sans relecture dans le chemin
de production, regrouper les travaux et servir leurs échéances, puis raccorder
carte, palette et sprites. Les IRQ natives sont toujours masquées et les
marqueurs PSG de diagnostic excluent une preuve de l'onde sonore originale.

L'archive locale `md-z80-source-video-v0203` conserve noyaux, sources, table
de conversion, captures et rapports avant nettoyage vérifié. Les descriptions
génériques de l'ancien motif répété ont été retirées des métadonnées ; les
rapports d'origine sont gardés et leurs résultats numériques sont identiques.
Le Git reste local. La ROM jouable **v0203** est inchangée.

La première relecture d'archive a rencontré une erreur CRC gzip avant toute
suppression. Une relecture séparée des 372 références compressées a ensuite
réussi sans différence d'empreinte ni de contenu ; la cause transitoire reste
indéterminée. Cette première archive est conservée intacte sous
`md-z80-source-video-v0203-failed-readback`, avec son manifeste et son journal.
Une nouvelle archive est reconstruite dans un répertoire distinct et doit
réussir tous les contrôles avant le nettoyage des fichiers générés d'origine.
