# LecturesM1 des canaux de tonalite (2026-10-16)

84C7 compose maintenant les modelesM1 de sequence8357,de hauteur82C5 et
d'enveloppe854B avec ses propres instructions. Le generateur garde le
modele semantique etses branches, ajoute les comptes des sous-routines
aux pointsCALL etcontrole le SHA du plan de cout audite. Aucun opcode
de la ROM n'est interprete a l'execution de cet outil.

20680 executions isolees passent enPAL/NTSC :notes,durees,drapeaux,echelles,
compteurs,pitch0/1/128,enveloppes0/1/128,relachement ettranspose. La matrice
modulo7 du banc precedent est reprise avec sa ROM exacte etson empreinte.
Les mesures comparent compteM1 absolu,R,duree,400 octets audio,DE etdepilage.
Le contexteIX estDE40,DE initial8A0B ;ce n'est pas un produit cartesien
de tous les etats des six canaux.

3372 appels reels passent aussi sur le parcours controle6D->96 avec masque
complet, enPAL/NTSC. L'observateur ajoute seulement trois valeurs par appel :
compteM1, R a l'entree etR au retour. Les enregistrements precedents de824
octets (entree/sortie audio,DE,A,cout,depilage) sont strictement identiques,
etles traces originales completes restent identiques aux referencesv0179.
Tous les appels captures sont compares, sans saut de commande unsupported.
Les modes etslots observes sont detailles dans le rapport ;le parcours
utilise uniquement le mode de hauteur0.

Le contrat live differe du caller isole :a84C7,le premier fetch du helper
est deja compte ;au retour dans le lecteur,le premier fetch de l'instruction
suivante est aussi compte. Le delta du compteur etdeR vaut donc le compteM1
du helper, sans le+1 du banc dont l'entree est auCALL3000. Ce contrat est
verifie sur chaque appel avec le compteur absolu etle registreR logique.

Limites :R a l'entree du helper reste observe, pas predit depuis16D0.
Les commandesR etrestaurations non prises en charge gardent leurs bornes.
Canal de bruit,lecteur complet etwrapperIRQ restent a composer avant le
calculR du chargement entier etle remplacement du hasardSGDK. Les sorties
PSG,la progression complete etle materiel reel restent non verifies.
ROMv0183 etsources natives inchangees.

Reproduire (fixtures etcaptures precedentes requises) :

- python tools/generate_tone_channel_refresh.py
- python tools/validate_audio_tone_channel_refresh.py
- python tools/build_live_tone_refresh_core.py
- Capturer6D/FF via profile_paid_passage_loader_phases.main,repertoire
  tone-refresh-live/6d-ff,coeur genesis_plus_gx_livetonerefresh_libretro.dll,
  capture_music=True.
- python tools/validate_live_tone_refresh.py
- python tools/archive_audio_tone_refresh_research.py

L'archive locale audio-tone-refresh-research-v0183 conserve outils,fixtures,
captures,references,coeurs etrapports avec manifesteSHA-256.
