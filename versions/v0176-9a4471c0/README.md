# Golden Axe Warrior MD v0176

Le chargement apres la sortie haute des passages payants conserve maintenant
un seul tick d'horloge de jeu, comme la SMS. Les interruptions audio restent
actives pendant la conversion des graphismes. La palette des sprites utilise
ensuite cette horloge corrigee.

ROM : gaw-megadrive-v0176.bin,1 Mio,checksum351C. Les versions precedentes
restent conservees. Les sources completes,symboles,rapports et outils sont
archives avec leurs empreintes dans source_evidence_manifest.json.

Controles :24 sorties SMS reelles pour etablir la regle,3072 chargements natifs
(six destinations,tous les masques d'ennemis,PAL/NTSC),18528 cas de regles et20
scenarios en jeu (paiement,refus,fonds insuffisants,sortie et retour de menu).

Cette version corrige l'horloge pendant ce chargement. La duree reelle trop
courte de certaines transitions,l'alignement des interruptions,les phases de
reapparition et le generateur aleatoire SMS restent a terminer. Une partie
complete et la fidelite globale ne sont pas encore validees.

Les traces de reference SMS ont ete produites avec la ROM MD v0175 a cote :
leur empreinte MD designe cette ancienne comparaison diagnostique. Les quatre
rapports de validation a la racine portent bien l'empreinte de la v0176.
