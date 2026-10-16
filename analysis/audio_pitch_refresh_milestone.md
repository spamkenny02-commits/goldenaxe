# LecturesM1 des hauteurs etdu vibrato (2026-10-16)

Le modele82C5 dispose maintenant d'un compteM1 derive de ses branches,
en plus de l'etat audio,HL,DE dans les modes sur tables,cout etdepilage
deja representes. Aucune logique native ni ancien modele n'est modifie.

Les chemins comprennent mode0,retard de vibrato,cadence du pas,addition
signee avec debordement,retournement de phase etmodulations sur tables.
Les operationsIX/IY,CB/ED etles helpers de lookup sont comptes avec leurs
lectures de prefixes. Les commandes de tables00..7F,80,83 et84..FF gardent
leurs reprises etlectures viaDE, comme l'original. Les arrets81/82
retirent un niveau de caller etretournent l'adresse restauree dansHL.

118832 executions passent enPAL/NTSC. Le banc reprend les59400 contextes
par region du cout de hauteur precedent puis ajoute16 probes de depilage
par region. Il compare le compteM1 absolu,R,duree,400 octets audio,HL et
depilage. DE est aussi compare pour les modes de tables ou le modele
le produit. Les registres non exposes par le modele ne sont pas revendiques.

Le banc precedent n'observait aucun depilage dans les huit tables de
hauteur/index utilises. Les nouveaux probes emploient deliberement les
modes synthetiques41(29h)/index127(7Fh) et45(2Dh)/index21(15h) :les mots deja presents en
ROM pointent respectivement a0503 et5000, ou les octets81/82 existent.
Les routines etles tables ne sont pas modifiees. Ces32 executions
confirment le chemin d'instructions de depilage, pas son occurrence dans
une musique naturelle. Les adresses etmodes sont conserves dans le rapport.

Limites :matrice de valeurs aux bornes etcombinaisons choisies, pas produit
cartesien de tous les etats. Les indices/base/counters de certains probes
sont synthetiques. Le coeur suit la conventionM1/R locale ;pas de preuve
d'acquittementIRQ materiel. Les commandes de sequence,canaux complets et
wrapperIRQ restent a compter etcomposer avant de predireR depuis16D0 et
remplacer le hasardSGDK. SortiesPSG,progression naturelle complete et
materiel reel restent ouverts. ROM v0183 etsources natives inchangees.

Reproduire :

- python tools/build_audio_pitch_refresh_core.py
- python tools/validate_audio_pitch_refresh.py
- python tools/archive_audio_pitch_refresh_research.py

L'archive locale audio-pitch-refresh-research-v0183 conserve outils,
fixtures,resultats,coeur etrapport avec manifesteSHA-256.
