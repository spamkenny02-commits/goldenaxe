# Lecteur audio original8000 compose (v0183 inchangee)

Le modele assemble arbitrage8097,tempo807E,fondu80C8,dispatch80FF,
priorite/restauration81F8,compensation60Hz et sept emplacements de canaux.
Les canaux de tonalite84C7 et de bruit864F transmettent leur DE final :
le registre peut influencer la lecture d'une enveloppe sur table.
Les modeles precisent maintenant les modifications de D/E par les ADSR.

33480 cas isoles couvrent81F8,avec les29 requetes d'effets valides,requete
vide/80,priorites et combinaisons de proprietaires des canaux DF30/DF60.
10752 cas distincts couvrent les256 valeurs de pause du lecteur8000 et
les conditions de compensation60Hz. Etat400 octets,cout complet et DE
final sont compares a la ROM non modifiee. Les matrices de tonalite/bruit
(20680/39360 cas) sont aussi reexecutees avec comparaison de DE en sortie.
Ces fixtures utilisent un amorcage specifique,sansIRQ,et des contextes
synthetiques ;elles ne couvrent pas toutes les combinaisons naturelles.

La capture complete du parcours6D->96/masqueFF contient601 appels par
region,soit1202 appels. Chacun correspond au modele en400 octets,DE et
cycles, sans commande ignoree. Les couts vont de616 a17472T en NTSC,
et2831 a17414T en PAL,uniquement sur ce parcours. Ils ne sont pas des
bornes universelles. Tous les appels sont rapproches des couples d'evenements
IRQ1A2/1A5 ou202/205. La premiere capture exploratoire ne couvrait que202/205 ;
elle n'est pas utilisee comme preuve de couverture complete. L'observateur
corrige couvre les deux retours :551+50 NTSC,559+42 PAL. Les tableaux
complets de cycles restent identiques a la referencev0179.

La ROM restev0183. Il s'agit d'un calcul du travail du lecteur SMS, pas
d'une nouvelle correction native ou d'une preuve de formes d'onde PSG.
Les commandes utilisant R,les restaurations8211 appelees depuis certaines
fins de sequence,les autres commandes du bruit et des combinaisons de
canaux restent explicitement non couvertes. L'integration du calcul des
interruptions aux chargements natifs reste a faire,ainsi que la validation
d'une progression naturelle complete et sur materiel reel.

Reproduire :

- python tools/validate_audio_priority_effect_cost.py
- python tools/validate_audio_reader_gates_cost.py
- python tools/validate_audio_tone_channel_cost.py
- python tools/validate_audio_noise_channel_cost.py
- python tools/build_live_envelope_core.py --reader
- python tools/validate_live_audio_reader_cost.py (captures locales requises)
- python tools/archive_audio_reader_research.py

Modeles,fixtures,captures et bibliotheques sont conserves localement dans
audio-reader-research-v0183 avec manifeste SHA-256.
