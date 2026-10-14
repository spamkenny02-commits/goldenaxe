# Checksum Mega Drive — 9 octobre 2026

ROM `gaw-megadrive.bin`, 512 Kio, SHA-256 `5d10a02a28e07170d10ec9b02354e81c42dc7a6185d1c48c7d636489c021d107`.

Le build applique désormais le checksum additif Mega Drive après le remplissage à 512 Kio et avant les copies de livraison. Les mots big-endian de 0x200 jusqu’à la fin de la cartouche sont additionnés modulo 65536 ; résultat701E écrit à 0x18E. La méthode est vérifiée contre `work/genesis-plus-gx/core/loadrom.c` lignes202..212 et288. Le checksum XOR produit automatiquement par le makefile SGDK est remplacé à la dernière étape. Le validateur général `tools/validate.py` contrôle désormais la somme additive.

Par rapport au parent d32d3208, seuls les deux octets0x18E/0x18F changent. Le code68000, les ressources, les vecteurs et les autres champs d’en-tête sont strictement identiques. Les trois copies de ROM concordent ; le fichier SMS fourni sur D: reste identique. Aucun changement à l’écran titre, dont le signalement a été retiré par l’utilisateur.

`tools/validate_md_checksum.py` compare les deux ROM et exécute chacune dans un processus frais du même cœur Genesis Plus GX : intro1600 images, écran titre900 images, partie4000 images. Treize captures comparent intégralement la RAM, la VRAM, la CRAM, les registres VDP et les PNG. Les trois pistes audio complètes sont identiques. Un premier essai dans un même processus conservait des octets inutilisés de pile entre les chargements ; les exécutions séparées éliminent ce résidu sans exclure de RAM de la comparaison. Rapport : `validation/md_checksum_report.json`, code0.

Les vingt rapports du parent restent des preuves historiques liées au SHA-256 d32d3208, sans réécriture de leur empreinte ni présentation comme une suite rejouée sur le nouveau binaire. Le rapport de checksum conserve leur liste, leurs hashes et la preuve que le code et les ressources n’ont pas changé. Les anciens scripts d’audit de jalon qui exigent le XOR décrivent les binaires historiques ; ne pas les utiliser pour certifier ce nouvel en-tête. La suite complète n’a pas été rejouée.

Le portage complet reste inachevé. Prochaine traduction : familles36/37 et projectiles19/1E, en vérifiant d’abord les pointeurs de dispatch2B65 pour éviter toute confusion entre indices. Suppression des tirs liée au débordement de sprites495E, RNG Z80R, autres familles, quêtes, donjons, dialogues conditionnels, effets audio et différences de timing restent à terminer.

Les dialogues PNJ ont aussi ete rejoues sur le nouveau binaire : six conversations comparees a la SMS, parcours reel et restauration verifies,162 images d entree/sortie avec affichage actif et decor non noir. `validation/house_dialogue_report.json`, code0. Timing exact des dialogues non revendique.
