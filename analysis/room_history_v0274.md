# v0274 : historique des salles et réapparition des ennemis

Le port ne réinitialisait jamais les masques des salles entièrement vidées.
La routine 1C15..1C90 de la SMS est maintenant traduite en C natif et appelée
avant le chargement des acteurs, sur chaque entrée réelle de salle.

- Extérieur et maisons (octet haut nul) : trois tirages, historique de 16 salles.
- Donjons : cinq tirages, quatre premières entrées du même historique partagé.
- Exceptions des donjons : 1E, 5E, 9C, B8, BE, C9.
- Seul un masque nul devient FF ; un masque non nul reste intact.
- Une salle déjà présente ne déplace pas la file, mais les tirages ont lieu.
- La routine 1C97 initialise aussi DCF0..DCFF : nouvelle partie = historique nul.
- L'historique reste hors de la charge SRAM de 592 octets. La salle 95 utilisée
  comme fond temporaire à la reprise ne consomme pas de tentative supplémentaire.

## Vérification

`tools/validate_room_history.py` compare le C compilé à 1C15..1C96 inchangé dans
la ROM SMS. Seuls le démarrage et le service de tirage sont remplacés par un
banc à entrées contrôlées. Les 6 656 cas comparent les 16 octets d'historique,
les 256 masques et le nombre exact de tirages (3/5), notamment les exceptions,
les protections, les masques partiels et les changements de couche.

`tools/validate_room_history_game.py` exerce le binaire jouable en NTSC/PAL :
nouvelle partie, entrées 95/94/A4 avec masques préparés, 2 102 observations.
La file et les réinitialisations sont observées dans la RAM du jeu compilé.
Ces parcours ne prouvent pas une campagne naturelle complète.

## Limites

Les tirages utilisent encore SGDK. La séquence exacte dépendant du registre R
et des interruptions SMS reste à intégrer au jeu. Les tests isolés du nouveau
service `source_rng_timed` sont conservés séparément ; ils ne constituent pas
une validation du générateur aléatoire de cette ROM. Les flux Continue/décès,
la cadence complète et le matériel réel restent à vérifier.
