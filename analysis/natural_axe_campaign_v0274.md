# Hache et poursuite naturelle de la v0274

La ROM reste v0274 : aucun code du jeu ni binaire modifié dans ce lot.
Le parcours SMS et MD part d'une nouvelle partie, récupère la hache en 1B6,
l'équipe dans le menu par les commandes normales, tue le premier boss,
récupère son cristal et ressort en B9. Ces deux trajets n'ont aucun décès.
À la sortie, les 256 indicateurs et les 1 280 octets de carte correspondent.
Les commandes fixes rejouées depuis le démarrage reproduisent la totalité de
la RAM finale (8 192 / 65 536 octets) et le PNG final, pour chaque machine.

Les trajets suivants atteignent le deuxième donjon avec la hache. La SMS
utilise un Continue normal sur le trajet extérieur ; MD y arrive sans décès.
Le deuxième boss, type 63 en 144, est atteint sur MD. Il n'est pas vaincu
par le pilote. Les autres essais échouent ou atteignent leur limite de frames.
Les tentatives et leurs commandes sont conservées ; elles ne prouvent pas
un défaut du jeu, ni l'achèvement du deuxième donjon.

L'examen des scripts a retrouvé la clé nécessaire en 160, en complément de
celle de 152. La clé de 131 permet ensuite de franchir la porte vers le boss.
Le pilote peut désormais équiper la hache, passer sans combattre dans des
salles explicitement choisies, ramasser des coeurs et objets de gel utiles,
et utiliser Continue en extérieur. Ses limites de reprises sont paramétrables.
Une modification expérimentale de visée à partir des rectangles de collision
n'a pas amélioré le parcours complet et est retirée. Ses essais restent archivés.
La sortie de donjon utilise le numéro et la capacité de vie du préfixe,
au lieu de supposer systématiquement le premier cristal et 32 HP. Le retour
natif du premier donjon est réexercé avec ce code.

Reproduction des constats : tools/summarize_axe_campaign_v0274.py.
Le rapport lie les captures et les relectures par leur SHA-256.
Les différences de rencontres, commandes, vie et durée SMS/MD restent explicites.
La campagne entière, le flux R/IRQ original, la cadence globale, les formes
d'onde, la campagne PAL et le matériel réel restent à terminer ou vérifier.
