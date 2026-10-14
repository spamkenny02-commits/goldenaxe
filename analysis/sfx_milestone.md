# Bruitages natifs — v0006

ROM : `b82289fa4a91003b304285c77c9b41505c93e299a0ac9625641cb79d8138047e` (512 Kio).

Les 29 séquences PSG 90..AC sont traduites en 68000 avec les trois canaux auxiliaires, les priorités, la restauration des canaux musicaux et les commandes de coupure/fondu. Les 13 musiques restent vérifiées. Les actions, combats, ramassages, dialogues et plusieurs menus émettent maintenant leurs commandes sonores originales.

13 rapports courants archivés avec cette ROM et `sfx_patch_audit.json`. Les tests comparent 19 140 interruptions pour les 29 effets, 7 920 pour les arbitrages et 23 400 pour les musiques. Quatre actions déclenchées par les boutons normaux produisent leur première commande au même frame que la SMS. Ces contrôles ne prouvent pas l'identité des formes d'onde ni la fidélité de tous les scripts du jeu.

Restent notamment l'arbitrage des effets continus DE09 et des événements appartenant aux routines de jeu encore absentes. Le portage complet reste en cours.
