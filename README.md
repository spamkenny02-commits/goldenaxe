# Golden Axe Warrior — portage Mega Drive

Reconstruire Golden Axe Warrior à partir de la ROM Master System fournie,
puis porter sa logique Z80 en code natif 68000 avec SGDK. La fidélité à la
Master System passe avant les améliorations.

<!-- ROM-RELEASE:START -->
**Version courante : v0180 — 1024 Kio.**

[Télécharger la ROM v0180](versions/v0180-3f155979/gaw-megadrive-v0180.bin) · [Toutes les versions](versions/README.md)

Contrôles ciblés réussis ; portage complet encore non validé.

SHA-256 : `3f15597956511409df72c59bab0303d917dc962fa394816d031db9825a6bafc7`  
Checksum Mega Drive : `442A`
<!-- ROM-RELEASE:END -->

## État du portage

Le portage est jouable mais reste incomplet. Les sources natives couvrent
l’intro avant le titre, le titre, les menus et dialogues, l’exploration,
les transitions, les combats, de nombreuses familles d’ennemis et boss,
les objets et sorts, les marchands, les récompenses, les sauvegardes et
la fin du jeu. Ces éléments ont des validations ciblées ; une partie
complète en progression naturelle reste à vérifier.

Les treize pistes musicales PSG et les bruitages ont un lecteur natif.
Leur synchronisation dans toutes les situations de jeu reste à contrôler.
Le binaire Mega Drive ne contient pas d’interpréteur Z80.

### Dernières corrections intégrées

- v0177 : conservation des récompenses et de la transformation des pièces,
  avec contrôles des retours dans les maisons et de la sauvegarde/reprise.
- v0178 : fondu musical B0 pendant les sorties de passages payants,
  puis lancement de la musique de destination avant la révélation.
- v0179 : fondus et révélation progressive des portes de maisons et de donjons,
  chargement masqué et restauration des couleurs des sprites.
- v0180 : attente explicite de la prochaine interruption vidéo avant la
  révélation, même lorsque l’affichage est désactivé. Les huit transitions
  de portes contrôlées ont un fondu d’entrée de 18 images, comme la SMS.

### Travail en cours

Rapprocher les durées de chargement et les animations de la SMS, en calculant
le travail original et les interruptions audio. Les routines de tempo,
fondu, arbitrage et traitement des commandes musicales/sonores ont des
modèles de coût vérifiés. Les enveloppes de volume ADSR et sur tables sont
également vérifiées. Les calculs de hauteur et de vibrato passent les tests
isolés ; le parcours observé en jeu utilise seulement le mode sans modulation.
Les séquences et le traitement complet des canaux restent à couvrir avant
l’intégration de ce calcul aux chargements natifs.

Restent aussi la fidélité du hasard au registre Z80 R, les différences de
combat et d’affichage encore ouvertes, la progression naturelle complète
et la vérification sur matériel Mega Drive.

## Fichiers utiles

- [Sources 68000/SGDK](megadrive/src/main.c) et [moteur des acteurs](megadrive/src/actors.c).
- [Journal des ROMs numérotées](versions/README.md) et [index des versions](versions/index.json).
- [Corrections v0180](analysis/reveal_wait_milestone.md).
- [Mesures des interruptions audio](analysis/audio_irq_milestone.md).
- [Calcul du traitement des musiques et bruitages](analysis/audio_dispatch_milestone.md).
- [Calcul des enveloppes de volume](analysis/audio_envelope_milestone.md).
- [Calcul de la hauteur des notes et du vibrato](analysis/audio_pitch_milestone.md).
- [Travail restant et notes techniques](analysis/world_next.md).
- [Ancien README conservé comme historique](analysis/README_historique_avant_v0180.md).

`gaw-megadrive.bin` est le binaire courant. `gaw-title-megadrive.bin` est
un alias du même binaire pour les anciens liens. Les anciennes ROMs
numérotées sont conservées sans écrasement dans `versions/`.

## Compilation et Git

Depuis ce dossier, dans PowerShell :

```powershell
.\build.ps1
python tools/verify_git_roms.py
```

La compilation utilise SGDK et Java ; leurs chemins peuvent être fournis
avec les paramètres `-Sgdk` et `-Java` de [build.ps1](build.ps1).
Chaque nouveau binaire reçoit un numéro de version. La version et le lien
affichés en tête de ce README sont actualisés par `tools/version_rom.py`.

Git conserve les sources, outils, rapports principaux et ROMs numérotées.
Les captures et fichiers temporaires volumineux restent disponibles localement.
Le travail reste dans le dépôt Git local, sur la branche `main`, sans dépôt
distant configuré. Il sera copié vers un nouveau dépôt lorsque demandé.
L’ancien dépôt GitHub V51 contient un autre arbre de code ; aucun changement
n’y a été envoyé depuis ce projet.
