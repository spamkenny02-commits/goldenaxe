# Phase de la routine graphique complete (2026-10-16)

Le modele enchaine maintenant toute la routine graphique 16D0, de son
entree au retour a24B9. Il utilise uniquement la phase CPU/VDP,336 octets
RAM et400 octets audio captures a16D0. Les etats intermediaires ne sont
pas des entrees : ils sont calcules a partir du modele precedent.

La suite du decodeur de motifs couvre le decodeur RAM par plans0C00,
la sauvegarde des metatuiles,le correctif de terrain1A30,le retour de
palette de donjon,les metatuiles supplementaires81C0,le decodage de terrain
et la copie1024 octets en SRAM. Les repetitions des LDIR sont des
instructions distinctes. Les branches des donnees compressees et les
retenues d'adresse sont calculees depuis les octets originaux. Le travail
du decodeur est aussi confronte au modele de cout deja verifie.

Le passage0444 coupe les interruptions pendant la copieSRAM ;043A les
reactive avec la latence d'une instruction apresEI. Le modele conserve
le VINT eventuellement latche pendant la copie et accepte l'interruption
a la meme frontiere d'instruction que le coeur original. Le lecteur audio
est execute aux phases predites, avec la demandeB0 emise au point original.

Les24 parcours controles (six passages payants,deux masques d'acteurs,
PAL/NTSC) correspondent aux six points :1706,170E,1720,1733,1748,24B9.
Chaque point compare la duree depuis16D0,la phase,l'etatIRQ/VDP,331 octets
RAM etles400 octets audio. Tous les horairesIRQ du segment correspondent.
Les traces originales completes sont identiques aux referencesv0179.

Limites : changement vers classe0,affichage coupe,C0AC0,salles ordinaires
des passages observes. Le modele suppose le changement de classe/banque
qui est verifie par ces parcours,mais ne reconstruit pas les ombres de
banque hors de la capture. C01B etC020..23 sont exclus des comparaisons.
Les octets de metatuiles/terrain/VRAM/palettes/SRAM hors de la capture ne
sont pas produits par ce modele de phase. La suite carte/HUD/acteurs et
historique/hasard reste a enchainer. Les contextes IRQ imbriques,HINT,NMI,
reset etautres modes video restent hors portee.

Pas de modification de la ROM v0183 ni des sources natives. L'integration
des timings,les autres classes graphiques,la progression naturelle
complete et le materiel reel restent a verifier.

Reproduire (captures locales requises) :

- python tools/build_graphics_load_phase_core.py
- Capturer les six routes et masques00/FF via profile_paid_passage_loader_phases.main,
  repertoire graphics-load-phase/TT-MM,coeur genesis_plus_gx_graphicsloadphase_libretro.dll,
  capture_music=True.
- python tools/validate_graphics_load_phase.py
- python tools/archive_graphics_load_phase_research.py

L'archive locale graphics-load-phase-research-v0183 conserve les outils,
captures,coeur etrapports avec un manifesteSHA-256.
