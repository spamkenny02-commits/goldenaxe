# Phase du debut de chargement graphique (2026-10-16)

Le modele de phase couvre maintenant 16D0..1706 : classification du decor,
changement de banque, demande de fondu musical B0, copie de palette et
decompression des motifs par 032A. Il part uniquement de la capture a
16D0 (phase CPU/VDP,336 octets RAM et400 octets audio). Chaque instruction
est representee avec sa duree ; les RST28 de chaque octet decompressent
avec leur DI/EI reel. Le modele calcule les IRQ audio et leurs effets sur
le lecteur pendant cette sequence longue, au lieu de prendre leurs
horaires observes comme donnees d'entree.

Les 24 parcours controles (six passages payants,deux masques d'acteurs,
PAL/NTSC) correspondent pour la duree totale,la phase finale,331 octets RAM,
les400 octets audio et chaque horaire d'acceptation d'interruption.
Les traces originales sont identiques aux references v0179. Le cout hors
interruption correspond aussi au modele de cout graphique deja verifie.

Le fondu B0 est demande au point de l'instruction originale qui ecrit DE06,
pas arbitrairement au debut du chargement. La valeur C031 issue de chaque
plan RLE est produite au point de l'instruction originale. Les donnees
compressees originales determinent les branches,les repetitions et les
retenues d'adresse ; aucun horaire IRQ mesure n'est reutilise.

Limites : changement vers classe0,affichage deja coupe,banque differente,
salles ordinaires des parcours observes. Le changement de classe et les
ombres de banque hors des336 octets captures sont des hypotheses de portee.
C01B etC020..23 sont exclus de la comparaison RAM. Le contenu VRAM et les
octets de palette ne sont pas modelises par cet outil. Les IRQ utilisent
le lecteur audio deja couvert ; ses commandes non couvertes restent hors
portee. La suite apres1706 et la prediction du chargement entier depuis
une seule entree restent a terminer,ainsi que l'integration native.
ROM v0183 et sources natives inchangees ; aucun resultat materiel reel
ni partie complete n'est revendique.

Reproduire :

- python tools/build_graphics_prefix_phase_core.py
- Capturer les six routes et masques00/FF via profile_paid_passage_loader_phases.main,
  repertoire graphics-prefix-phase/TT-MM,coeur genesis_plus_gx_graphicsprefixphase_libretro.dll,
  capture_music=True.
- python tools/validate_graphics_prefix_phase.py
- python tools/archive_graphics_prefix_phase_research.py

Captures et modeles sont conserves localement dans graphics-prefix-phase-research-v0183
avec manifeste SHA-256. Le Git conserve les outils,rapports et le manifeste.
