# Registre R pendant les attentes VBlank (2026-10-16)

Le modele 0B95..0BB3 compte maintenant les lectures M1 et le registre R
en plus de la phase, des boucles, des interruptions et de l'etat memoire.
Il prend R/raster/RAM/audio a l'entree de l'attente. Les tours de boucle,
l'acceptation des IRQ et les lectures de leurs corps sont calcules, sans
utiliser les nombres de tours ou les deltas R observes comme entrees.

Le prefixe de sauvegarde consomme 19 lectures : PUSH IX et PUSH IY sont
prefixes. Chaque tour du test de gate consomme trois lectures, y compris
le dernier. Le total hors IRQ est donc 22 + 3*tours_pris. Les IRQ completes
composent sprites, motifs, HUD, palette, file graphique, audio et entrees ;
les IRQ audio seules composent sauvegardes, lecteur, delai et restauration.
Le vecteur et le RET sont inclus selon la convention du coeur GPG local.
Le point 0BB3 est apres la premiere lecture de son opcode POP AF, comme
le point initial 0B95 est apres celle de PUSH AF.

Les 13 725 attentes des 24 parcours controles passent les deltas M1, R
final, boucles, durees, offsets IRQ, 331 octets RAM et 400 octets audio.
Ces captures ont une IRQ par attente. Les anciens enregistrements de phase
et d'attente restent identiques octet par octet ; les traces SMS completes
restent identiques aux references v0179.

Les 6 156 cas synthetiques reutilisent les fixtures du banc de phase :
delais de caller, entree DI, EI+NOP et chute depuis EI, IRQ latchee,
palette sautee ou transferee, compensation et compteurs 0/1/255.
Les traces d'attente precedentes restent identiques et les nouveaux deltas
M1/R correspondent. Les routines originales et banques 4/6 sont intactes ;
le caller et le byte 0B94 du cas EI sont synthetiques comme dans le banc
precedent. Le calcul optionnel R laisse le chemin temporel par defaut
disponible ; la regression carte/HUD passe ses 24 scenarios.

Limites : R et l'etat d'entree de chaque attente restent observes. Le
raccordement au calcul hors interruptions du HUD depuis 16D0 reste a faire,
puis les acteurs et l'historique. C01B et C020..23 sont exclus des
comparaisons ; joy0 est utilise pour le modele d'entrees, sans revendication
de preuve du port manette. Autres modes video, NMI/reset, interruptions
imbriquees, commandes audio non couvertes et partie complete restent ouverts.
L'acquittement IM1 local n'ajoute pas de R++ explicite ; aucune equivalence
materielle n'est revendiquee sur ce point. ROM v0183 et sources natives
inchangees, integration native des delais/hasard encore a venir.

Reproduire :

- `python tools/build_wait_refresh_core.py`
- Capturer les six routes/masques avec
  `profile_paid_passage_loader_phases.main`, repertoire `wait-refresh/TT-MM`,
  coeur `genesis_plus_gx_waitrefresh_libretro.dll`, `capture_music=True`.
- `python tools/validate_wait_refresh.py`
- `python tools/validate_wait_refresh_unit.py`
- `python tools/validate_map_hud_phase.py`
- `python tools/archive_wait_refresh_research.py`

L'archive locale conserve outils, fixtures, captures, references, rapports
et coeur avec manifeste SHA-256. Le fichier C de travail est restaure
apres compilation de la DLL distincte.
