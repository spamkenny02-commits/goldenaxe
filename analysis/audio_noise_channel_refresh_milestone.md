# LecturesM1 du canal de bruit (2026-10-16)

864F compose maintenant le compteM1 de la selection de note8679 etdes
enveloppes854B avec ses instructions propres. Le helper8679 suit l'ordre
des six bits de priorite etses branches de silence/canal emprunte. Le
generateur864F controle le SHA du plan semantique audite, sans interpreter
des opcodes de ROM a l'execution. Les durées etles400 octets d'etat audio
restent ceux des modeles deja verifies.

Les blocs de dispatch agreges sont decomposes explicitement :109T
correspondent a15 fetches, incluant leJP86DE ;la continuationINC DE/JR
de18T correspond a2 fetches. Le multiplicateur de duree reprend le
compte4 ou6+2*((scale-1)&255) verifie pour8433. Les controlesF6/F7 gardent
leurs pointeurs etcompteurs de boucle, etles enveloppes gardent leurDE.

39360 executions isolees passent enPAL/NTSC, avec la ROM exacte de la
matrice de cout precedente :notes/durees,drapeaux,echelles,compteurs,
enveloppes0/1/128,controlesF6/F7 etleurs valeurs aux bornes. Le banc compare
M1 absolu,R,duree,400 octets audio,DE etdepilage. ContexteIXDED0 etDE8A0B ;
les combinaisons synthetiques ne prouvent pas leur occurrence naturelle.

1102 appels reels passent aussi sur6D->96 avec masque complet :501 NTSC
et601 PAL. Les anciens enregistrements de824 octets restent identiques
octet pour octet, etles traces originales completes restent identiques
aux referencesv0179. Tous les appels captures sont compares, sans saut
de commande unsupported. Le compteM1 live verifie aussi le delta deR
entre l'entree864F etle retour805C/0205, sans utiliser le delta observe
comme entree du modele. La valeurR d'entree elle-meme reste observee.

Limites :notes/contextes de la matrice etdu parcours, pas tous les etats
possibles du lecteur. Les commandes bruit autres queF6/F7 restent hors
portee du modele de sequence864F. Lecteur8000 complet,wrapperIRQ etR
depuis16D0 restent a composer avant le remplacement du hasardSGDK.
Le compteur suitGPG local, pas une preuve d'acquittementIRQ materiel.
SortiesPSG,progression complete etmateriel reel restent ouverts.
ROMv0183 etsources natives inchangees.

Reproduire (fixtures etcaptures precedentes requises) :

- python tools/generate_noise_channel_refresh.py
- python tools/validate_audio_noise_channel_refresh.py
- python tools/build_live_noise_refresh_core.py
- Capturer6D/FF via profile_paid_passage_loader_phases.main,repertoire
  noise-refresh-live/6d-ff,coeur genesis_plus_gx_livenoiserefresh_libretro.dll,
  capture_music=True.
- python tools/validate_live_noise_refresh.py
- python tools/archive_audio_noise_refresh_research.py

L'archive locale audio-noise-refresh-research-v0183-r1 conserve outils,fixtures,
captures,references,coeurs etrapports avec manifesteSHA-256.
