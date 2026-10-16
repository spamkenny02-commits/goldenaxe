# LecturesM1 des enveloppes audio (2026-10-16)

La routine854B dispose maintenant de comptesM1 pour les enveloppesADSR
etles enveloppes sur tables. Les comptes suivent les branches semantiques,
independamment du compteur observe. Les modeles d'etat/cout deja verifies
fournissent toujours400 octets audio,accumulateur,DE etindication de
depilage ;aucune logique native n'est modifiee.

ADSR couvre attaque,decroissance,maintien etrelachement,les limites de
valeur/pas,les rebonds etl'arret863E. Les operationsIX/CB sont comptees
avec leurs prefixes. Le chemin qui emet un silencePSG est distingue du
canal emprunte qui conserve la sortie. Les phases etles drapeaux synthetiques
composes suivent l'ordre de priorite des tests de l'original.

Les tables couvrent les16 enveloppes,leurs valeurs etcommandes80/81/82/83.
Le compteur tient compte des boucles,reprises etarrets qui retirent une
adresse de retour de la pile. La commande83 lit(++DE), comme l'original ;
le contexteDE explicite est donc conserve dans le modele. Les entrees
RAM hors de la capture etles indices invalides restent exclus.

107184 executions passent enPAL/NTSC :80384 ADSR et26800 sur tables.
Chaque cas compare compteM1 absolu,valeursR,duree,400 octets audio,A,DE
etdepilage. Les cas sur tables incluent2160 depilages de caller. Le banc
charge explicitementDE depuis les octets de contexte avant leCALL, y
compris pour les casADSR. Les banques etroutines originales restent
intactes ;les callers sousDI etl'observateur sont les seuls ajouts.

Le coeur read-only est derive du compteurM1 precedent, avec observation
des retours3003 ou3053. Le premier fetch duCALL3000 est deja compte
a l'entree, etle premier fetch apres retour l'est aussi :delta absolu-1
donne le compteM1 du helper, tandis que deltaR vaut ce compte+1 modulo128
avec bit7 conserve. Les arrets qui depilent la pile gardent ce contrat.

Limites :dimensions choisies, pas de produit cartesien de tous les octets
de tous les canaux. Certaines phases/valeurs sont synthetiques. Le contexte
DE est fourni, pas predit depuis une partie naturelle. Les comptesM1 des
canaux complets,hauteurs/commandes de sequence etwrapperIRQ restent a
composer ;R n'est pas encore predit depuis16D0 etle hasardSGDK reste
provisoire. L'acquittementIRQ materiel,les sortiesPSG etla progression
complete restent non verifies. ROM v0183 etsources natives inchangees.

Reproduire :

- python tools/build_audio_envelope_refresh_core.py
- python tools/validate_audio_envelope_refresh.py
- python tools/validate_audio_envelope_refresh.py --table
- python tools/archive_audio_envelope_refresh_research.py

L'archive locale audio-envelope-refresh-research-v0183 contient outils,
fixtures,resultats,coeur etrapports avec manifesteSHA-256.
