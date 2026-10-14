# Golden Axe Warrior MD v0178

La sortie des passages payants declenche maintenant le fondu de la musique
pendant le chargement,puis le theme exterieur avant la revelation de l'ecran,
comme le code SMS. Auparavant,la commande de fondu manquait et le theme
exterieur attendait la fin de la revelation.

ROM :gaw-megadrive-v0178.bin,1 Mio,checksum3DDA. Sources completes,symboles,
profils audio et cinq rapports actuels archives avec source_evidence_manifest.json.
Les versions precedentes restent conservees.

Controles :24 parcours des six passages PAL/NTSC avec/sans ennemis,1800 etats
alignes du lecteur audio et des registres PSG,3072 chargements avec horloge
verifiee et20 scenarios de paiement/sortie/retour de menu.

Cette version corrige l'ordre des commandes musicales de ces passages. La duree
physique encore trop courte de certains chargements,l'alignement des interruptions,
les phases audio naturelles,le registre aleatoire de rafraichissement Z80 et la
progression complete restent a terminer. Les horodatages et formes d'onde audio
du jeu complet ne sont pas declares identiques a la SMS.
