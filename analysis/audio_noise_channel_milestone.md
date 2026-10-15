# Cout du canal de bruit original864F (v0183 inchangee)

Le modele compose les routines de selection du bruit8679, d'enveloppe854B
et de duree/reset839B/83A4, puis le traitement de volume8530. Il compte
separement les instructions de liaison et les retours propres au canal.
Les commandes F6/F7 utilisent le trampoline8670..8677, distinct de celui
des canaux de tonalite. Les autres commandes sont explicitement exclues.

39360 cas isoles PAL/NTSC correspondent a la ROM originale :400 octets
d'etat et cout complet du canal. Les helpers et tables de la banque6
restent intacts ; seul l'amorcage, le double appel de test et les flux
synthetiques en ROM fixe sont prepares. IX=DED0,DE=8A0B,IRQs desactivees.
Les notes,durees,reutilisations de duree,compteurs0/1/2/255,emprunt,
enveloppes0/1/128,debordements de multiplication et boucles F6/F7 sont
couverts dans la matrice decrite par le rapport. Indice d'enveloppe initial0.
Les valeurs limites synthetiques ne prouvent pas une occurrence en jeu.

Sur le parcours controle6D->96/masqueFF :1102 appels (501 NTSC,601 PAL)
correspondent a la prediction en memoire et en cycles. Aucun appel observe
n'est ignore ;32 appels commencent par F6/F7. DE et les etats d'enveloppe
sont lus a l'entree reelle. Les tableaux complets de cycles sont identiques
aux captures v0179 : l'observateur ne change pas le parcours original.
Il observe le retour805C et egalement0205 pour detecter une sortie du lecteur.
Aucune sortie globale n'est rencontree dans ce parcours.

La ROM de production reste v0183 :aucune modification de jeu dans cette
etape. Ce modele de cout original ne constitue pas une validation generale
du canal natif ou des formes d'onde. Les autres commandes du bruit,les
canaux de tonalite complets,la restitution8211,les commandes utilisant R
et le lecteur entier restent a couvrir avant l'integration aux chargements.
La progression naturelle complete et le materiel reel restent non verifies.

Reproduire :

- python tools/validate_audio_noise_channel_cost.py
- python tools/build_live_envelope_core.py --noise
- python tools/validate_live_noise_channel_cost.py (captures locales requises)
- python tools/archive_noise_channel_research.py

Les captures, modeles, fixtures et bibliotheques de mesure sont conserves
localement dans audio-noise-channel-research-v0183 avec manifeste SHA-256.
