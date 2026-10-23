# Parcours naturel v0274 : premier donjon et début du deuxième

La ROM reste v0274, SHA-256 6af186deca6c86bfdeccaa607aab39f31345349b4d3a5861ad4d912b084c87f4.
Les changements de ce lot concernent les outils de parcours, sans nouveau binaire.

Le trajet natif part d'une nouvelle partie, termine le premier boss, récupère
le cristal, porte la vie maximale de 24 à 32 et ressort en B9 sans décès.
À la sortie, les 256 indicateurs de progression et les 1 280 octets de carte
correspondent au parcours SMS précédemment vérifié.

La suite rejoint naturellement l'entrée du deuxième donjon en 171, traverse
161 et 151, active l'interrupteur et récupère la clé en 152. SMS et MD réalisent
cette étape sans décès. Les 256 indicateurs et les 1 280 octets de carte sont
identiques à cet endroit. Les points de vie, rencontres et durées diffèrent.
Les relectures sans pilote adaptatif reproduisent les 8 192 / 65 536 octets
finaux de RAM et le PNG final pour chaque machine depuis le démarrage.

Les tentatives suivantes n'atteignent pas le boss 144 : le pilote finit par
mourir avec l'arme de départ. Ces échecs sont conservés dans le rapport.
Ils ne prouvent pas un défaut du portage. La récupération de la hache et
l'amélioration de la stratégie restent nécessaires pour continuer ce parcours.

Les outils acceptent maintenant une autre entrée de donjon et une séquence
précédente enregistrée, avec vérification du SHA de ROM et absence d'injections.
Le pilote sait activer tous les types d'interrupteurs référencés, contourner
les acteurs invulnérables et viser les satellites vulnérables. Sa lecture des
objets SMS utilise C4B0, corrigée depuis C360. Les séquences anciennes gardent
leurs commandes et leurs captures, sans nouvelle prétention sur leurs listes
d'objets observées. Un arrêt sur immobilité évite les attentes sans fin.
Le lecteur libretro prépare les commandes fixes une fois, ce qui rend les
longues relectures praticables ; le replay complet vérifie leur conservation.

Reproduction : tools/summarize_natural_campaign_v0274.py. Les traces et leurs
relectures sont archivées sans perte avant le nettoyage des fichiers générés.
La campagne complète, le flux R/IRQ original, la cadence globale, les formes
d'onde et le matériel réel restent non validés ou incomplets.
