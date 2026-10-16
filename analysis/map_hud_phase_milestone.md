# Phase graphique,carte etHUD depuis une entree (2026-10-16)

La prediction16D0 se prolonge maintenant jusqu'a24BF, au retour de1DE2.
Le modele conserve les etapes graphiques et de carte precedentes puis
ajoute2279 (preparation de640 mots de carte),1E4E (HUD),229C (attente et
transfert video) etla restauration de palette qui suit.

Les entrees sont exclusivement celles de16D0 :phaseCPU/VDP,336 octets RAM,
400 octets audio et16 octets de contexteHUD (vie/max,magie/max,or,neuf
drapeaux de gemmes,malediction etarmure). Salle etbit persistant0 actif
restent des entrees de portee des passages payants. Aucun etat de phase,
horaireIRQ ou compte de boucle intermediaire observe n'est utilise.

Les jauges sont traduites en plans d'instructions, avec leurs branches
pour segments pleins/partiels/vides etles divisions par soustractions de
l'affichage de l'or. Les modeles de cout existants verifient leurs totaux.
Le passage0B95 recoit sa phase calculee apres la preparation duHUD ;
les modeles d'attente et d'IRQcomplete predisent le rendez-vousVBlank,
ses effets audio etles331 octets RAM verifies. Le transfert gardeDI
pendant les12 blocs de128 octets (OUTI etDJNZ decrementent tous deuxB),
puis acquitte le statut etreactive lesIRQ avec la latenceEI originale.

Les24 parcours controles (six passages payants,deux masques d'acteurs,
PAL/NTSC) passent16 points de controle depuis16D0. Cela inclut1DE5 apres
preparation de carte,1DE8 apresHUD,0B95 et0BB3 autour de l'attente,22A3
apres restauration des registres,1DEB apres transfert,24BF apres palette.
Chaque point compare duree,phase,VDP/latchIRQ,331 octets RAM et400 octets
audio. Les16 octets de contexteHUD restent identiques a ceux d'entree.
Tous les horairesIRQ du segment correspondent. Les traces originales
completes restent identiques aux referencesv0179.

Limites :classes/salles/masques etcontextesHUD observes ;pas de preuve de
phase sur toutes les combinaisons possibles de jauges ou curse/armure.
Les couts des jauges ont des validations anterieures plus larges, sans
que cela prouve toutes les phases futures de leurs combinaisons.
Les octets rendus de carte/HUD/VRAM/palette hors des captures ne sont pas
reconstruits par ce modele de phase. C01B etC020..23 sont exclus des
comparaisons ;les entrees controleur du modeleIRQ sont nulles. Pas de
HINT/NMI/reset niIRQ imbriquee. Les acteurs,historique/hasard etla fin du
chargement restent a enchainer. Integration native,progression naturelle
complete etmateriel reel restent non verifies.

ROM v0183 etsources natives inchangees. Outils,captures etcoeur sont
archives localement dans map-hud-phase-research-v0183 avec manifesteSHA-256.

Reproduire (captures locales requises) :

- python tools/build_map_hud_phase_core.py
- Capturer les six routes etmasques00/FF via profile_paid_passage_loader_phases.main,
  repertoire map-hud-phase/TT-MM,coeur genesis_plus_gx_maphudphase_libretro.dll,
  capture_music=True.
- python tools/validate_map_hud_phase.py
- python tools/archive_map_hud_phase_research.py
