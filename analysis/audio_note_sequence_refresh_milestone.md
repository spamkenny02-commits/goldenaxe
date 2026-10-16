# LecturesM1 des notes etcommandes de sequence (2026-10-16)

8357 dispose maintenant d'un modele semantique avec calcul parallele du
cout etdes lecturesM1. Le generateur reprend les plans d'instructions du
modele de cout existant,avec annotations propres a ce fichier etcontrole
de son SHA-256. Il ne decode ni n'interprete les instructions de la ROM
a l'execution. Les branches etles modifications des400 octets audio
restent celles de la traduction semantique deja verifiee.

Les durées d'instructions ne suffisent pas en general a compterM1 :trois
sitesBIT7,(HL) de12T sont explicitement distingues desJR12T. Ils sont
identifies dans les cheminsF1/F2/F3 etverifies sur le codeCB7E original.
Le correctif de coutF3 -16T retireINC DE+JP, donc deux lectures ordinaires.
Le multiplicateur8433 est represente par4 lectures si scale1, sinon
6+2*((scale-1)&255). Le SHA du plan audite empeche une regeneration
silencieuse si ses instructions changent.

167552 executions passent enPAL/NTSC :103424 notes/repos/raw/tie/boucles/
appels/retours,59904 commandes deterministes,384 arretsF1/F2 et3840
controles de possessionF3. Chaque cas compare compteM1 absolu,R,duree,
400 octets audio,DE etdepilage du caller. Les arrets incluent816 depilages
positifs au total. Les fixtures sont exactement les ROMs des anciens
controles de cout,avec empreintes verifiees avant copie etexecution.
Les banques originales etles tables ne sont pas modifiees.

Le banc de commandes couvreE0/E1/E2/E4/E5/E6/E8/E9/EA/EB/ED/EE/F0/F4/F5/
F6/FA/FB/FC/FD, avec controles distinctsE7/F7/F8/F9 etF1/F2/F3. Les
entrees comportent des valeurs aux bornes etdes combinaisons synthetiques.
Les streams sont places dans la ROM fixe3600/3C00,avec contexteIXDE40
etcallers sousDI ;ils ne prouvent pas la jouabilite de toutes ces
combinaisons dans une partie naturelle.

Limites :commandes utilisantR etF1/F2 avec restauration8211 nonzero
toujours hors portee. Le modele de sequence ne compte pas encore les
canaux complets ni le wrapperIRQ ;R n'est pas predit depuis16D0 etle
hasardSGDK reste provisoire. Le compteur suit le coeurGPG local, pas une
preuve d'acquittementIRQ materiel. SortiesPSG,progression naturelle
complete etmateriel reel restent ouverts. ROM v0183 etsources natives
inchangees.

Reproduire (fixtures de cout precedentes requises) :

- python tools/generate_note_sequence_refresh.py
- python tools/validate_audio_note_sequence_refresh.py notes
- python tools/validate_audio_note_sequence_refresh.py commands
- python tools/validate_audio_note_sequence_refresh.py termination
- python tools/validate_audio_note_sequence_refresh.py ownership
- python tools/archive_audio_note_sequence_refresh_research.py

Le coeur est celui de build_audio_envelope_refresh_core.py. L'archive
locale audio-note-sequence-refresh-research-v0183 conserve outils,fixtures,
references,resultats,coeur etrapports avec manifesteSHA-256.
