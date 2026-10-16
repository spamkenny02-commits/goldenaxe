# Séquences tonales natives — v0190

La routine SMS 8357 est traduite dans `source_audio_sequence.c` et appelée
par les six canaux tonals du lecteur jouable. Elle couvre les notes, silences,
fréquences16bits, durées et répétitions de durée, liaisons, commandes
déterministes, boucles F7, appels F8, retours F9, contrôle d'emprunt F3 et
terminaisons F1/F2 avec restauration8211. Les cycles Z80, lectures M1, DE
et retours anticipés sont conservés pour la future horloge native.

La commande EA, auparavant refusée par le lecteur MD, est maintenant
traduite. Les indices de boucle se replient sur8bits comme sur SMS, et les
appels ne sont plus limités artificiellement au-dessus de la position2A :
les accès restent bornés par les400 octets de RAM sonore effectivement fournis.

Les écritures PSG sont préparées puis appliquées après succès. Une commande
non couverte, une lecture de RAM non fournie ou une boucle non terminante
ne laisse pas une séquence partiellement modifiée. La liste de512 écritures
couvre deux sorties par commande sur la limite de256 contrôles.

## Vérifications ciblées

- 83 776 cas sur hôte reprennent les fixtures déjà vérifiées sur les
  instructions8357 originales : 51 712 notes/durées, 29 952 commandes,
  192 terminaisons et1 920 cas d'emprunt. Les400 octets, T/M1, DE et retours
  anticipés correspondent au modèle source.
- 1 984 cas supplémentaires par région comparent directement le nouveau C
  aux instructions SMS inchangées : 1 728 terminaisons avec restauration
  active, 256 séquences EA placées dans la RAM et ses miroirs DE/FE/DF/FF.
  État, cycles, M1, DE et retour anticipé correspondent ; la progression
  de R source est contrôlée à partir des lectures d'opcodes observées.
- Les85 760 cas passent ensuite en code68000 sous Genesis Plus GX, en PAL
  et NTSC, sur trois cartouches de test. Les fixtures compactes reconstruisent
  sans perte l'état attendu et comparent directement chacun des400 octets.
- Trois cas de refus passent sur hôte et68000 PAL/NTSC : RAM non fournie,
  EC après des écritures PSG préparées et des modifications d'état, boucle
  F6 non terminante. Ils vérifient le contrat de refus sans mutation ni
  sortie PSG à appliquer, pas l'équivalence SMS des commandes non portées.
- Dans la ROM jouable, 50 scénarios PAL/NTSC, chacun sur deux interruptions,
  correspondent à la SMS pour les400 octets et DE. EA activée/désactivée,
  miroirs RAM, indices F7 étendus/repliés, cinq appels imbriqués puis retours,
  F1/F2 et restauration sont exercés. Le PSG de la voix0 est comparé : période
  et volume, ou volume seul pour une terminaison.
- Les13 musiques, 29 bruitages ordinaires, 29 effets prioritaires PAL/NTSC,
  retours DE, fondu musical et parcours naturels du menu passent à nouveau.
- Le retour normal de l'inventaire passe dans l'extérieur initial et les
  deux premières maisons, en PAL/NTSC. Les124 motifs de fond contrôlés
  restent corrects ; les quatre motifs animés sont distingués de l'égalité
  statique. Ce contrôle ne couvre pas tous les donjons ni tout le framebuffer.

Les listes PSG ne sont pas vérifiées indépendamment dans les83 776 fixtures
de composant ; les comparaisons de registres utilisent les exécutions de la
ROM jouable. Les états audio sont contrôlés, sauf les parcours naturels du
menu et de l'inventaire. Les formes d'onde et le matériel physique ne sont
pas prouvés équivalents.

## Suite nécessaire

Le canal de bruit864F conserve encore son chemin précédent. Le comptage
natif des canaux, des enveloppes/notes du bruit, puis le lecteur/IRQ complet
restent à composer. E3/EC/EF/FE/FF ne sont pas encore portées avec leur
contexte et R ; les autres régions RAM restent non fournies. Les coûts ne
pilotent donc pas encore l'horloge du jeu. Le hasard SGDK et les budgets
fixes sont toujours présents, et une partie complète reste à vérifier.
