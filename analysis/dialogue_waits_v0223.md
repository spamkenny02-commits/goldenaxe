# V0223 : attente des pages et des messages finaux

Les instructions SMS 07F4..080F remettent C02F à zéro, attendent une nouvelle
pression d’un bouton (masque30 de C021), dessinent le marqueur selon le bit3,
puis écrivent FF dans C02F lors de la validation. Le port utilisait un compteur
local décalé d’une image et conservait l’ancienne phase globale.

La v0223 reproduit ces opérations dans l’attente intermédiaire. En intérieur,
une direction ne valide plus une page intermédiaire. Les alias de boutons MD
existants sont conservés. La boucle finale 7447/627A emploie le masque3F,
sans réinitialisation du compteur ni animation du marqueur : les appels des
services auberge/sauvegarde et du marchand « magie pleine » utilisent désormais
cette attente finale. Les autres dialogues finaux l’utilisaient déjà.

## Comparaisons dans les ROMs exécutées

- Page naturelle d’ouverture, PAL/NTSC : 64 images relatives par région,
  compteur RAM et marqueur physique exacts. La v0222 échouait sur les64 valeurs
  du compteur et7 marqueurs par région. Validation à2200 : compteurFF,
  marqueurFC, puis compteur00 à2201, identiques à la source.
- Deux pauses de test en contexte intérieur : une direction conserve la page,
  puis un bouton la poursuit ; les trois bitmaps1040octets correspondent à la
  SMS. Les copies de test changent uniquement le texte d’ouverture/checksum ;
  le drapeau intérieur MD est une injection RAM explicite. La v0222 échoue.
- Message final de refus à l’auberge : 120 marqueurs physiques fixesFC par cas,
  deux validations (action/haut) et deux régions. Fermeture et ressources
  correspondent à la source. Les quatre cas échouaient sur la v0222.
- Sauvegarde : trois slots, payloads592octets, reprise à froid, annulations,
  écrasement, conservation des autres slots et reprise après mort passent.
  Les exports SRAM sont normalisés comme à l’import : voie impaire MD,
  puis fin effacée FF si l’export ne contient pas toute la capacité.
- Marchand « magie pleine », six PNJ et trajet naturel de conversation enNTSC.
- Douze validations finales du récit, PAL/NTSC, et quatre poses du premier
  défilement conservent leurs résultats ciblés.

Les entrées d’attente ne sont pas synchronisées en date absolue : l’attente de
première page reste10images tardive enNTSC et18enPAL. Le code continue de
faire avancer l’horloge hors de ces attentes selon son organisation native ;
les suppressions d’IRQ SMS, les chargements, les autres parcours et le fluxR
ne sont pas reproduits globalement. L’entrée initiale dans le monde conserve
son recalage provisoire. Ce jalon ne prouve donc pas l’horloge complète,
la cadence audio, les formes d’onde ni le fonctionnement sur console physique.

ROM : versions/v0223-39e69955/gaw-megadrive-v0223.bin, 1Mio.
SHA-256 : 39e6995514a87d170d4d1fc713938a3645905842fe93a340415c80e996057a31.
Checksum Mega Drive : 51E2.
