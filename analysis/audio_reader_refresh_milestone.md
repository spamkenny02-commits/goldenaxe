# LecturesM1 du lecteur audio complet (2026-10-16)

8000 compose maintenant les comptesM1 de l'arbitrage,tempo,fondu,dispatch,
file prioritaire etdes sept slots de canaux, avec ses propres instructions
de pause/compensation/selection. Les modeles semantiques de chaque helper
produisent leur etat,cout,DE etcompteM1 ;aucun horaire ni deltaR observe
n'est utilise pour calculer le compte du lecteur.

Le chemin de pause avec bit7 inclut les deuxPUSH etdeuxPOP agreges dans
les couts22T/20T etles10 iterationsOTIR. Les passages de compensation
comptent leurs retours anticipes. Les tests de slots comptentLD IX puis
BIT indexe, etleCALL conditionnel pris ounon pris avant chaque canal.
Les limites de commandes deja prises en charge restent inchangees.

10752 executions isolees passent enPAL/NTSC :tous les256 octets de pause,
trois valeurs de compensation etsept compteurs de phase. La ROM du banc
de cout precedent est reprise exactement, avec verification d'empreinte.
Les canaux sont inactifs lorsque le chemin normal continue. Les comptesM1
absolus,R,couts,400 octets audio etDE correspondent a l'execution originale.

14424 appels reels passent aussi sur24 parcours controles :six passages
payants,deux masques d'acteurs,PAL/NTSC. Chaque capture contient601 appels
complets du lecteur. Les enregistrements de824 octets sont identiques
octet pour octet aux captures d'attentes precedentes, etles traces
originales completes restent identiques aux referencesv0179.
Les deux sites de retourIRQ01A5/0205 sont controles separement par les
evenements deCALL/retour ;le cout de chaque appel correspond a son span.
Tous les appels captures sont compares sans ignorer les commandes.

Le contrat live donne un deltaR egal au compteM1 du helper, car le premier
fetch du lecteur est deja compte a l'entree etcelui du caller l'est au
retour. Le banc dont l'entree estCALL3000 conserve le deltaM1+1. Ces
conventions sont verifiees par compteur absolu etregistreR logique.

Limites :les commandes utilisantR,restaurations8211 non prises en charge,
commandes de bruit horsF6/F7 etindices invalides restent exclus. Ces
parcours ne prouvent pas toutes les combinaisons du jeu. R a l'entree du
lecteur reste observe ;les fetches du wrapperIRQ etdu travail horsIRQ
restent a calculer depuis16D0 avant de remplacer le hasardSGDK.
La convention d'acquittementIRQ materiel,les sortiesPSG etla progression
complete restent non verifiees. ROMv0183 etsources natives inchangees.

Reproduire (fixtures etcaptures precedentes requises) :

- python tools/validate_audio_reader_refresh.py
- python tools/build_live_reader_refresh_core.py
- Capturer les six routes etmasques00/FF via profile_paid_passage_loader_phases.main,
  repertoire reader-refresh-live/TT-MM,coeur genesis_plus_gx_livereaderrefresh_libretro.dll,
  capture_music=True.
- python tools/validate_live_reader_refresh.py
- python tools/archive_audio_reader_refresh_research.py

Le banc isole utilise le coeur build_audio_envelope_refresh_core.py.
L'archive locale audio-reader-refresh-research-v0183 contient outils,
fixtures,captures,references,coeurs etrapports avec manifesteSHA-256.
