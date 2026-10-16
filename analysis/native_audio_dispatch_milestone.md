# Dispatch audio natif — v0186

La routine SMS 80FF est désormais traduite dans `source_audio_dispatch.c`
et appelée par le lecteur de la ROM jouable. Les anciennes implémentations
séparées du démarrage de musique, des bruitages et des commandes de contrôle
ont été remplacées par ce même code vérifié.

Le helper conserve les 400 octets de l'état source, les cycles Z80 et les
lectures M1 de chaque branche couverte. Il renvoie explicitement les écritures
PSG et les demandes de silence ; le lecteur applique ces sorties au matériel MD.
Les tables et séquences restent celles de la ROM SMS fournie.

2 304 cas passent sur hôte, puis dans une cartouche SGDK exécutée en 68000
sous Genesis Plus GX, en PAL et NTSC : comparaison directe des 400 octets,
des cycles, de M1 et des décisions PSG. Parmi ces cas, 48 vérifient le rejet
sans mutation des six commandes non auditées 8E, 8F, AD, AE, AF et B4.
Le jeu garde son ancien repli d'arrêt pour ces commandes ; leur comportement
original reste à porter. Le test du helper est une preuve de composant,
distincte du raccordement dans le jeu.

Dans la ROM jouable, 34 états contrôlés (17 en PAL et 17 en NTSC) correspondent
aux 400 octets du lecteur SMS après une interruption : commandes d'arrêt,
fondu, restauration, musiques et bruitages aux bornes des tables.
Le modèle Python est aussi comparé, sauf pour 8D qui utilise immédiatement
la commande de bruit F2 encore absente de son modèle temporel. Dans ce cas,
la comparaison reste directe entre les deux ROMs exécutées.

Les contrôles séparés couvrent les 13 musiques (1 800 états par piste), les
29 bruitages (660 états par effet), le fondu 87/B0/82 en PAL et NTSC,
la musique du menu et ses sons de déplacement/validation en parcours naturel.
Les rapports attachés à la version enregistrent le hash du binaire testé.

Les coûts calculés ne pilotent pas encore l'horloge du jeu. Il reste à raccorder
les effets prioritaires et les canaux au comptage natif, compléter les commandes
hors modèle, puis intégrer le callback d'interruption, le registre R et le
générateur aléatoire original. La production utilise encore le hasard SGDK
et des budgets fixes. Les tests ne prouvent ni une partie complète, ni une
égalité des formes d'onde, ni le comportement sur console physique.
