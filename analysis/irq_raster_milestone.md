# Phase video et boucles de palette (ROMv0183 inchangee)

Le modele predit les decisions0186 depuis la phaseCPU/VDP a l'entree de
l'IRQ,le cout des quatre etapes precedant la palette et le drapeauDE03.
Les comptes observes de boucles ne sont pas utilises comme entrees.
Le portSMS lit le VCounter apres les11T de l'instructionIN ;une iteration
prise ajoute27T. Le modele utilise3420 cycles maitres par ligne et la
conversion mode4/192 lignes :262/DA enNTSC,313/F2 enPAL,avec le saut de
compteur. La valeurE0 correspond ainsi a la ligne physique230 enNTSC,
etF0 a la ligne240 enPAL dans les modes controles.

13749 interruptions des24 parcours controles correspondent :comptes de
branches et cout de l'etape palette. Les phases sont relevees une seule
fois a l'entree de chaque interruption. Les traces de cycles completes
restent identiques aux referencesv0179. Le materiel emule estSMS2(21h).

149500 positions supplementaires sont comparees a la vraie fonction
vdp_hvc_r du GPG local via un wrapper isole. Tous les262/313 numeros de
ligne,tous les pas de15 cycles maitres jusqu'a3765 et certains voisins
aux limites sont testes. Les globaux sont sauvegardes/restaures. Un latch
HCounter nonnul evite une tableH noninitialisee ;le VCounter mode4 reste
actif. Ce test verifie l'emulateur local,pas le materiel reel ni tous les
modes video. Les modes entrelaces,Mode5 et compatibiliteMegaDrive sont exclus.

Le budget conditionnel16D0..0ACE passe les24 scenarios avec les boucles
palette predites. Les13725 attentes0B95 et14424 appels audio restent controles.
Les boucles d'attente0B95,la chronologie/phase d'entree desIRQ et les entrees
historique/hasard proviennent encore des captures. Il ne s'agit donc pas
encore d'une prediction autonome du chargement,ni d'un delai natif integre.
ROMtoujoursv0183 ;progression naturelle complete et materiel restent ouverts.

Reproduire :

- python tools/build_irq_raster_core.py
- python tools/build_vcounter_oracle.py
- python tools/validate_vcounter_phase_unit.py
- python tools/validate_irq_raster_phase.py (captures locales requises)
- python tools/validate_raster_loading_budget.py (captures locales requises)
- python tools/archive_irq_raster_research.py

Modeles,sources du compteur,fixtures,captures et bibliotheques sont conserves
localement dans irq-raster-research-v0183 avec manifeste SHA-256.
