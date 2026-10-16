# LecturesM1 du dispatch etdes effets prioritaires (2026-10-16)

Deux routines audio supplementaires disposent d'un modele de lecturesM1 :
80FF (dispatch musique/bruitage/controle) et81F8 (file prioritaire et
restauration8211). Les comptes sont derives des branches semantiques,
independamment du compteur observe. Les modeles de cout et d'etat deja
verifies restent utilises sans modification ;aucune source native change.

Le dispatch compte les13 demarrages musicaux,les29 effets,le repos80,
les controlesB0/B1/B2/B3 etles chemins definis de remise a zero. Les
copies81CA ont40 lecturesM1 :elles incluent9 LDI avec prefixeED ainsi que
les ecritures indexees. Le lookup8424 consomme9 lectures. Les chemins
vers83EF reprennent les829 lectures d'arret verifiees precedemment.
Les branches surDF60 bit6 etles modifications de possession des canaux
sont suivies dans l'ordre original avant la copie suivante.

La file prioritaire compte les branches de rejet/acceptation,les changements
de DE0E/DE0F,les canaux deja actifs etles restitutions via81C6. Elle utilise
le meme compte de copie de canal que le dispatch,avec les prefixesDD/FD
etDDCB/FDCB tels qu'executes par le coeur local. L'etat temporaire utilise
pour compter les branches conserve l'ordre des ecritures originales.

81480 executions passent enPAL/NTSC :48000 pour80FF et33480 pour81F8.
Chaque cas compare compteM1 absolu,valeursR entree/sortie,duree et400
octets audio. Le compteur read-only etle contratcaller3000/3003 sont ceux
du jalon audio-prefix-refresh. Les banques etles tables originales restent
intactes ;les callers fournissent les etats de contexte sousDI.

Limites :six commandes80FF hors table/non prises en charge sont exclues
(8E,8F,AD,AE,AF,B4). La file81F8 couvre0/80 etles29 effets valides, pas
les indices invalides niles appelants8211 seuls. Les combinaisons de
priorites et de drapeaux aux bornes sont parfois synthetiques. Pas encore
de compteM1 complet des canaux,enveloppes,commandes de sequence etwrapper
IRQ ;donc pas de predictionR depuis16D0 ni de remplacement du hasardSGDK.
Le compteur suit la conventionGPG locale, pas une preuve d'acquittement
IRQ materiel. Les sortiesPSG,la progression complete etle materiel restent
non verifies. ROM v0183 inchangee.

Reproduire :

- python tools/build_audio_prefix_refresh_core.py
- python tools/validate_audio_dispatch_refresh.py
- python tools/validate_audio_priority_effect_refresh.py
- python tools/archive_audio_control_refresh_research.py

Outils,fixtures,resultats,coeur etrapports sont conserves localement dans
audio-control-refresh-research-v0183 avec manifesteSHA-256.
