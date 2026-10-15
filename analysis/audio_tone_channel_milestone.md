# Composition des canaux de tonalite84C7 (ROMv0183 inchangee)

Le modele compose la lecture8357, l'initialisation du vibrato827D,
l'initialisation ADSR82A8, le relachement85EB, la hauteur82C5 et les
enveloppes854B. Il ajoute les tests de drapeaux, les instructions de liaison
et les retours anticipes propres au canal. DE est transmis explicitement :
il change lors de la lecture de sequence, de l'initialisation du vibrato
ou de l'ajout du detune, et peut influencer une enveloppe sur table83.

20680 cas isoles PAL/NTSC correspondent aux400 octets du lecteur et au cout
complet d'instructions. La banque6 et ses tables restent intactes. Le test
utilise un amorcage/double appel et des flux synthetiques en ROM fixe,
IX=DE40,DE initial8A0B,IRQs desactivees. La matrice echantillonnee modulo7
varie notes,durees,drapeaux,echelles,compteurs,vibrato0/1/128,enveloppe0/1/128,
relachement0/1 et detune0/128. Les indices initiaux sont0, le type est80 et
le pointeur de vibrato est explicitement8A0B. Ce n'est pas une couverture
exhaustive des modes ou des interactions,ni une preuve de survenue naturelle.

Sur le parcours controle6D->96/masqueFF :3372 appels (1547 NTSC,1825 PAL)
correspondent a la prediction en memoire et en cycles. Aucun appel observe
n'est ignore. DE40/DE70/DEA0 sont actifs,ainsi que DF00/DF30 sur quelques
images ;DF60 n'est pas appele. Le vibrato reste au mode0. Les enveloppes
observees sont2/6/7/8/16. Les captures contiennent notes nouvelles et tenues.
Les tableaux complets de cycles restent identiques a la referencev0179,
ce qui controle l'absence d'effet de l'observateur sur le parcours original.

La ROM restev0183 ;aucune correction native n'est ajoutee dans cette etape.
Le modele de cout SMS ne valide pas globalement le canal natif ni les formes
d'onde PSG. Restent les combinaisons non observees,les commandes utilisant R,
la restitution8211,le lecteur audio complet,puis l'integration du calcul aux
chargements. Le jeu complet et le materiel reel restent non verifies.

Reproduire :

- python tools/validate_audio_tone_channel_cost.py
- python tools/build_live_envelope_core.py --tone
- python tools/validate_live_tone_channel_cost.py (captures locales requises)
- python tools/archive_tone_channel_research.py

Sources de mesure,fixtures,captures et bibliotheques sont conservees dans
audio-tone-channel-research-v0183 avec manifeste SHA-256.
