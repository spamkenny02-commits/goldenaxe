# Sortie du hasard04E1 etregistreR (2026-10-16)

Le modele de04E1 verifie maintenant l'octet aleatoire produit, en plus
de la graine suivante etdu cout deja verifies. Il prend comme entreeR
la valeur a l'entree d'instruction04E1 apres la premiere lectureM1.
Il ajoute17 lecturesM1 jusqu'a la lecture deR parED5F, ou18 si la graine
nulle est remplacee par733C. La routine entiere consomme21 ou22 lectures,
en comptant le premier opcode. L'observateurED5F intervient avant la
seconde lecture du prefixe : celle-ci doit aussi etre incluse.

Les sept bits bas deR evoluent modulo128 ;le bit7 reste programme.
Ceci correspond au manuel Zilog,section Memory Refresh (R) Register :
https://www.zilog.com/docs/z80/um0080.pdf (page imprimee3/PDF16).
Les macrosLD_R_A/LD_A_R etles prefixesED du coeur GPG local ont aussi
ete inspectes. Aucune modification de l'etatCPU n'est faite par l'observateur.

135168 cas isoles passent : toutes les65536 graines avecR fourni par le
caller, puis les256 valeursR pour huit graines, enPAL etNTSC. Les callers
fixentR parLD R,A puisCALL04E1 ;la routine originale04E1..04FD reste
strictement intacte. Les cas couvrent debordements7bits,bit7 haut/bas et
le remplacement de graine nulle. Le banc exhaustif n'attend pas une image
par graine ;les observations sont recoltees sans modifier le CPU.

Les72 appels d'historique sur24 passages controles correspondent aussi :
graine,cout,R au point de lecture,R au retour etoctet produit. Aucun de
ces72 appels ne contient uneIRQ. Les traces originales completes restent
identiques aux referencesv0179. Pour ces appels,la valeurR a l'entree
04E1 reste observee ;le modele calcule son evolution locale seulement.

Limites :pas encore de calculR depuis l'entree16D0, ni de comptage des
lecturesM1 dans tous les chemins du lecteur audio/IRQ. Un appel04E1
interrompu demande aussi le nombre de lectures de son interruption ;
aucun cas positif de cette sorte n'est revendique dans le parcours.
La fonctiontake_interrupt du GPG local ne contient pas d'incrementR
explicite dans son cheminIM1 ;ce coeur seul ne constitue donc pas une
preuve du comportement de rafraichissement a l'acquittement sur materiel.
Ce point reste a verifier avant de figer une convention materielle.

Le hasardSGDK reste provisoire dans le portage. Aucun remplacement natif,
nouvelleROM ou validation complete du hasard en jeu n'est revendique.
ROM v0183 etsources natives inchangees. L'archive rng-refresh-research-v0183
conserve localement modeles,fixtures,captures etcoeur avec manifesteSHA-256.

Reproduire :

- python tools/build_rng_refresh_core.py
- python tools/validate_rng_refresh.py
- Capturer les six routes etmasques00/FF via profile_paid_passage_loader_phases.main,
  repertoire rng-refresh-live/TT-MM,coeur genesis_plus_gx_rngrefresh_libretro.dll,
  capture_music=True.
- python tools/validate_live_rng_refresh.py
- python tools/archive_rng_refresh_research.py
