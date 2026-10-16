# LecturesM1 de l'interruption audio seule (2026-10-16)

Le modele0137..0226 ajoute maintenant au lecteur8000 les lecturesM1 de
la selection du typeIRQ,sauvegarde des registres,mapping de banque,
compteurC030,restauration etretour. Les cinq parties consomment3,21,1,
3/5 et19 lectures respectivement, plus une pourRET. Le corps sans le
lecteur consomme donc48 ou50 lectures selonC030.

Le vecteur38..42 execute six instructions (PUSH AF,IN BF,OR A,JP p,
LD C01B,A,JP0137), de59T et6 lecturesM1. Le coeurGPG local ajoute13T pour
l'acceptationIM1 mais aucunR++ explicite dans ce chemin :le compte de
six instructions ne pretend pas mesurer un increment de rafraichissement
a l'acquittement materiel. Cette convention reste un point separe de la
fidelite materielle, pas une modification silencieuse du coeur.

15360 cas isoles passent enPAL/NTSC :les256 compteursC030,cinq valeurs
de pause,deux compensations ettrois phases du lecteur. Un caller sous
VINT-desactive construit une pile equilibree(PUSH AF puisJP0137). Le
stub47T/4M1 est compte separement. Les routines0137..0226 etbanque6 sont
intactes ;le banc compareM1,R,duree,400 octets audio,C030,horloge,gate et
banque restauree. Il inclut60 compteurs nuls et15300 non nuls.

Les24 parcours controles(six passages,deux masques,PAL/NTSC) correspondent
a14424 vecteurs etlecteurs. Les675 interruptions audio seules passent
aussi les quatre spans0137->01E3->0202->0205->0226 :M1,R,duree etcompteur
de sortie. Les six instructions de vecteur sont verifiees sur tous les
passages qui conduisent a0137. Les anciens enregistrements lecteur,
comptesM1/R etevenementsIRQ sont inchanges, etles traces originales
completes restent identiques aux referencesv0179.

Les675 cas live ontC030 nul ;la branche non nulle est donc prouvee par le
banc isole, pas revendiquee comme couverture naturelle. LeRET final est
verifie dans ce banc etcompte depuis l'opcode original ;le pointlive0226
est a l'entree duRET, pas apres son execution.

Limites :corpsIRQcomplete avec gate nonzero etinstructions horsIRQ
restent a compter avant de predireR depuis16D0. Les commandes de lecteur
non prises en charge gardent leurs bornes. Le hasardSGDK reste provisoire.
Pas de preuve des sortiesPSG,du materiel reel nide la progression complete.
ROMv0183 etsources natives inchangees.

Reproduire :

- python tools/validate_audio_irq_refresh.py
- python tools/build_audio_irq_refresh_core.py
- Capturer les six routes etmasques00/FF via profile_paid_passage_loader_phases.main,
  repertoire audio-irq-refresh-live/TT-MM,coeur genesis_plus_gx_audioirqrefresh_libretro.dll,
  capture_music=True.
- python tools/validate_live_audio_irq_refresh.py
- python tools/archive_audio_irq_refresh_research.py

Le banc isole utilise le coeur build_audio_envelope_refresh_core.py.
L'archive locale audio-irq-refresh-research-v0183 conserve outils,fixtures,
captures,references,coeurs etrapports avec manifesteSHA-256.
