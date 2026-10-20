# Admission DMA native : cout des refus et autorisation recente

Le nouveau chemin optionnel `md_z80_video_span_try_hidden_grant` utilise
l'horodatage publie par le pilote Z80 apres son reechantillonnage prive.
Il exige les capacites refresh et fresh-grant, reconstruit V modulo128
et garde les memes limites : blocs1a4motifs, age1ligne (2pour1motif),
H32/224, affichage coupe, controle apres BUSREQ, exclusion229a234.
Les chemins du pilote proches d'une emission retirent l'autorisation.
Cette propriete du protocole est necessaire pour exclure une autorisation
vieille de128lignes; la capture controle aussi l'intervalle prive Z80.

Les fonctions natives precedentes sont conservees octet par octet. Aucun
nouveau chemin n'est active par defaut et la ROM jouable reste v0203.

## Resultats compares

La reference produit3504DMA par region avec14431/14469 prises du bus
sans transfert (NTSC/PAL), soit environ80pourcent des controles sous bus.
Deux precontroles ont ete mesures : avant les prechargements de registres,
puis juste avant BUSREQ. Ils conservent les gardes finales et les pixels,
mais font manquer trop de creneaux et sont rejetes pour leur delai video.
Leurs sources/captures restent accessibles pour reproduire ce resultat.

Le [rapport compare](md_class0_admission_comparison_report.json) distingue
le pilote recent seul du vrai consommateur de son horodatage :

| Chemin | Refus sous bus NTSC / PAL | Retard PSG maximal, ticks NTSC / PAL |
| --- | ---: | ---: |
| Reference refresh | 14431 / 14469 | 318720 / 290235 |
| Pilote fresh-grant, ancien consommateur | 42091 / 40455 | 192105 / 243240 |
| Pilote fresh-grant, nouveau consommateur | 10908 / 10645 | 394575 / 400410 |

Face a la reference, le nouveau consommateur reduit les refus de24.4/26.4
pourcent. Le delai moyen entre fin logique24BF et reaffichage du banc baisse
de12.2/13.2pourcent. Son maximum passe de9.462/8.262images a7.906/6.681.
Cela reste loin d'une preuve de cadence complete : le retard PSG maximal
augmente de75855/110175ticks et aucun seuil ne le declare acceptable.
Le chemin reste donc experimental, sans promotion dans la ROM jouable.

## Verification et limites

Les cinq noyaux passent48cas par region avec memes donnees source,
193motifs,319motifs residents,768mots de carte,32couleurs et image finale.
Le noyau complet grant-proof compare en plus768checkpoints RAM/audio et
186624mots VRAM/CRAM par region, sans ecart. Les contrats natifs passent
57controles de precontrole initial,59de retention/rejet d'age prepare,
et58de capacites/retention fresh-grant par region.

L'[audit physique](md_class0_admission_physical_report.json) identifie les
35040DMA des cinq noyaux par signatures natives revues. Les gardes H32,
les plages d'affichage coupe, l'ordre motifs/carte et les horloges restent
controles. Les gardes des deux noyaux fresh-grant couvrent les250valeurs V
autorisees, y compris0,127,128et255. Leur intervalle prive maximal est
15615ticks, strictement sous17100; les relectures completes gardent aussi
cette limite. Les emissions PSG ne sont pas anticipees et les intervalles
intrarafale restent exacts. La plage CPU palette tracee est verifiee dans
le noyau complet, pas pretendue mesuree dans le noyau sans trace.

La proximite du dernier echantillon de grant est bornee independamment.
La selection effective de son octet encode est le controle natif revu;
le banc ne trace pas directement chaque ecriture de cet octet. Le resultat
ne constitue pas une preuve materielle generale du protocole ni de tous
les chemins du jeu.

La publication mesuree attend la vidange du banc;24BF est un repere logique,
pas encore l'echeance originale d'activation d'affichage SMS. Les sprites,
les IRQ natives, le boot, le jeu complet, l'onde audio et l'integration
restent a terminer. Prochaine etape : reduire le cout/prioriser les envois
audio avant de choisir l'autorisation recente comme chemin du moteur.

Les preuves sont figees dans md-class0-admission-v0203 avec relecture SHA/gzip
integrale avant suppression des fichiers generes.

Archive finalisee :1052references compressees;448644034octets generes retires,
347595524octets nets liberes. Relecture independante puis reanalyse physique
depuis gzip : rapport strictement identique; comparaison regeneree identique.
