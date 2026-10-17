# IRQ natives : calcul direct de l’attente vidéo

La boucle source teste le compteur V toutes les405 unités de temps maître.
Sa première lecture acceptée est désormais calculée à partir des plages
réelles du compteur Mode4/192 PAL ou NTSC, y compris leurs discontinuités.
Le nombre de lectures, les T et les M1 source restent identiques.

Le chemin audio seul vérifie ses débordements avant de modifier son unique
octet RAM ; son instantané de restauration de336 octets devient inutile.
Les IRQ complètes conservent leur restauration sur refus. L’adaptateur IRQ
évite aussi deux divisions modulo lorsque les bornes déjà validées permettent
une soustraction. Les callbacks, publications audio et erreurs sont conservés.

## Vérifications

- 3 933 000 comparaisons face à la référence scalaire immuable : chaque unité
  de balayage PAL/NTSC, deux seuils, tous les336 octets RAM, neuf étapes T/M1,
  coût total et nombre de lectures vidéo. État de file vidéo valide fixé.
- 31 989 vecteurs issus des instructions SMS repassent sur PC ; avec les704
  cas de files supplémentaires,32 693 passent en68000 dans les deux régions.
- 12 refus et3 passages de reset audités restent conformes ; les7 contrôles
  de publication et d’erreur de l’adaptateur passent.
- La chaîne de chargement retrouve toujours ses16 points SMS sur24 contextes,
  puis passe en68000 PAL/NTSC. Le noyau complet termine en3117/2608 images
  de contrôle ; ces durées incluent les hashes et ne mesurent pas le jeu.

## Budget réel encore insuffisant

Le profilage possède maintenant une mesure sans compteurs internes ni
chronométrage par IRQ, avec seulement les lectures de vtimer autour des
quatre appels et aux six points graphiques. Elle donne24–25 images NTSC
et19–20 PAL pour22,71 et19,57 images de travail SMS. Le profil instrumenté
reste conservé séparément ; les sous-totaux IRQ sont approximatifs.

Le premier décodage des6176 octets de motifs représente à lui seul12–13
images NTSC et9–10 PAL dans la mesure sans compteurs. Il est la prochaine
cible. La résolution est d’une image ; code et instrumentation modifient
également l’alignement du binaire. On ne revendique pas une équivalence
cycle par cycle du temps CPU physique à partir de ces durées.

Le calcul dépasse encore le budget dans certains cas, avant même les envois
graphiques. L’écran est éteint et le PSG ignoré pendant le profilage. La
continuité de phase depuis le démarrage, les autres branches et le raccordement
au jeu restent à réaliser. La ROM jouable reconstruite reste v0198, identique.
Le portage complet reste en cours.

Rapports : [balayage exhaustif](irq_poll_fast_report.json),
[IRQ68000](native_source_irq_68k_report.json),
[budget sans compteurs](native_loading_budget_bare_report.json),
[budget instrumenté](native_loading_budget_report.json).
