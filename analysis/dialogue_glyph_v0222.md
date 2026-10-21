# V0222 : dessin natif des caractères plus rapide

Chaque ligne de huit pixels du glyphe est décalée et combinée par OR dans
un ou deux octets du bitmap SMS conservé en RAM. L’ancienne boucle examinait
séparément les huit pixels de chacune des dix lignes. La nouvelle routine
conserve les pixels déjà présents et coupe le débordement à la colonne 26.
Elle utilise la police originale, sans LUT de captures ni nouveau buffer.

## Mesure dans la ROM jouable

Même entrée naturelle dans le récit, même nom et mêmes boutons, aucune
injection RAM ni modification des ROMs de production. La référence SMS
capturée reste byte-identique avant et après l’optimisation.

| Attente de fin de première page | SMS | v0221 | v0222 | Gain |
| --- | --- | --- | --- | --- |
| NTSC | 1596 | 1613 | 1606 | 7 images |
| PAL | 1583 | 1602 | 1601 | 1 image |

Les 37 publications complètes de la source, comprenant 29 bitmaps distincts,
se retrouvent dans l’ordre sur MD dans les deux régions, avec les mêmes
indices de couleurs. Ce gain concerne ce parcours, pas tout le jeu.

## Vérifications

- Compilation hôte des fonctions exactes avant/après : 1 714 176 cas,
  toutes les valeurs d’un octet de ligne, 216 abscisses et 31 ordonnées.
  Comparaison sur fond non nul et gardes mémoire, y compris au bord droit.
- 26 textes de test exécutés par les renderers SMS et 68000 : glyphes,
  changements de mode, substitution du nom/nombre, retours à la ligne,
  mots longs et pauses. Seule la ressource texte des copies de test est modifiée.
- Première page naturelle : tous les bitmaps complets conservés dans l’ordre.
- Quatre poses du premier défilement : dates et durées toujours exactes dans
  les deux régions ; début du bitmap suivant inchangé, durée NTSC exacte.
- Six PNJ et trajet naturel de conversation/restauration en NTSC.
- 302 images cohérentes de texte de PNJ dans les deux régions ; publication
  VBlank de la v0220 conservée.

Le retard de première page reste de 10 images NTSC et 18 PAL. La durée du
premier bitmap suivant le défilement reste une image trop longue en PAL.
Le travail de transfert, la cadence des autres textes, les IRQ/audio et le
hasard Z80 restent à aligner ; les formes d’onde, tout le jeu et la console
physique ne sont pas validés par ces tests.

ROM : versions/v0222-13edb546/gaw-megadrive-v0222.bin, 1 Mio.
SHA-256 : 13edb546df3bb0f6a5466843170323fbaa9b258355e171672391fcbef61b7ce8.
Checksum Mega Drive : 4545.
