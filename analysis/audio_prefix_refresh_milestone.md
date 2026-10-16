# LecturesM1 des prefixes audio (2026-10-16)

Le calcul du registreR dispose maintenant de comptes de lecturesM1 pour
quatre routines originales :tempo807E,fondu80C8,arret83EF etarbitrage8097.
Les comptes sont derives des branches semantiques, pas des observations.
Ils sont ajoutes a des wrappers autour des modeles de cout/etat existants ;
aucune logique native ni aucun ancien modele de cout n'est remplace.

Les cas de tempo consomment4,6 ou24 lectures. Le fondu compte ses branches
de compteur et de volume ;le passage par83EF inclut l'effacement de394
octets viaLDIR etles10 emissionsOTIR. L'arret complet consomme829 lectures,
donc plusieurs tours du compteur7bits. L'arbitrage compte aussi les
prefixesDD/FD des instructionsIX/IY etses trois decisions successives.

66530 executions originales passent enPAL/NTSC :2048 cas de tempo,
8192 de fondu,2 d'arret direct et56288 d'arbitrage. Pour chaque execution,
le banc compare le compteM1 absolu,les valeursR entree/sortie,la duree et
les400 octets d'etat audio. Le compteur absolu de l'observateur suit les
R++ deja presents dans le coeur ainsi que les increments d'acceleration
des boucles ;il n'ajoute aucun cycle etne modifie aucun registreCPU.
Les banques originales etles tables de priorite restent intactes.

Le caller3000 est unCALL :son premier fetch est deja compte a l'entree
de l'observateur. A3003,le premier fetch du retourcaller est aussi compte.
Le delta du compteur moins1 donne donc les fetches du helper complet ;
le delta logique deR vaut fetches+1 entre ces deux observations. Le banc
verifie ces deux conventions independamment des couts enT-states.

Limites :banc isole sousDI,avec cas synthetiques de volumes/requetes et
priorites aux bornes. Ce travail ne compte pas encore toutes les lectures
de dispatch,canaux,enveloppes,commandes etwrapperIRQ. Il ne predit donc
pas encoreR depuis16D0 etne remplace pas le hasardSGDK. Le compteur suit
la convention du coeurGPG local ;l'acquittementIRQ materiel reste a
verifier separement. Progression complete,sortiesPSG et materiel reel
restent ouverts. ROMv0183 etsources natives inchangees.

Reproduire :

- python tools/build_audio_prefix_refresh_core.py
- python tools/validate_audio_prefix_refresh.py
- python tools/archive_audio_prefix_refresh_research.py

L'archive locale audio-prefix-refresh-research-v0183 conserve outils,
fixtures,captures,resultats etcoeur avec manifesteSHA-256.
