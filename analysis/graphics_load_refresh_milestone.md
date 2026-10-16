# Registre R sur la routine graphique complete (2026-10-16)

Le calcul M1/R s'etend de 16D0 jusqu'au retour 24B9 de la routine
graphique de classe 0. Il enchaine les motifs, les deux plans RAM de
metatuiles, leurs copies, les correctifs de terrain, les metatuiles
supplementaires, les quatre plans du terrain et la copie SRAM sous DI/EI.
Seul l'etat initial 16D0 (R, raster, RAM et audio) est fourni au modele.
Les etats intermediaires et le planning des interruptions sont calcules.

Les 24 scenarios controles passent six points chacun, soit 144 comparaisons
de M1/R, phase video, duree, 331 octets RAM et 400 octets audio. Les anciens
enregistrements d'etat et les traces SMS v0179 sont inchanges. Le modele
consomme 137 614 lectures M1 hors interruptions, plus 6 250 pour 17 IRQ en
NTSC ou 6 132 pour 14 IRQ en PAL. Le registre R et les deltas du compteur
global correspondent a chaque point, pas uniquement au retour final.

Le plan temporel partage accepte une fabrique de processeur et un modele
de prefixe optionnels. Son chemin par defaut garde les resultats precedents,
verifies sur les 24 scenarios. Les deux instructions SLA C a 81EC/81EE
portent explicitement deux lectures M1 ; les fins DJNZ de meme duree 8T
restent a une lecture. Les autres nouveaux noeuds prefixes sont les copies
LDI/LDIR. La copie SRAM respecte la suspension puis la reprise des IRQ.

Un coeur distinct observe les six points sans changer les timings. Les
captures brutes de phase et d'etat restent identiques aux anciennes, et
les evenements complets identiques aux references. Le fichier C de travail
est restaure apres compilation. Les outils, references, captures et coeur
sont conserves dans une archive locale avec manifeste SHA-256.

Limites : changement de banque classe 0, affichage desactive, C0AC=0 ;
les autres classes/branches ne sont pas couvertes. C01B et C020..23 sont
exclus des comparaisons RAM ; le contenu VRAM/palette/SRAM hors snapshots
n'est pas verifie ici. La convention locale GPG d'acquittement IM1 est
conservee sans preuve materielle. Carte, HUD, attentes, acteurs et historique
doivent encore propager R avant integration du hasard/delais natifs.
Commandes audio non prises en charge et partie complete restent ouvertes.
ROM v0183 et sources natives inchangees.

Reproduire :

- `python tools/build_graphics_load_refresh_core.py`
- Capturer les six routes avec masques 00/FF via
  `profile_paid_passage_loader_phases.main`, repertoire
  `graphics-load-refresh/TT-MM`, coeur
  `genesis_plus_gx_graphicsloadrefresh_libretro.dll`, `capture_music=True`.
- `python tools/validate_graphics_load_refresh.py`
- `python tools/validate_graphics_load_phase.py`
- `python tools/archive_graphics_load_refresh_research.py`
