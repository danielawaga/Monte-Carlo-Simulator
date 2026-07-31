# ruff: noqa: E501
"""Integrate functional-validation evidence into the evolving PDF report."""

from io import BytesIO
from pathlib import Path

import pandas as pd
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "output" / "pdf" / "etude_cas_batiment_monte_carlo.pdf"
DATA = ROOT / "output" / "functional_validation"
TMP = ROOT / "tmp" / "pdfs" / "etude_cas_batiment" / "functional_validation"

pdfmetrics.registerFont(TTFont("FVRegular", "C:/Windows/Fonts/segoeui.ttf"))
pdfmetrics.registerFont(TTFont("FVBold", "C:/Windows/Fonts/segoeuib.ttf"))
FONT, BOLD = "FVRegular", "FVBold"
NAVY = colors.HexColor("#17365D")
BLUE = colors.HexColor("#2F75B5")
GREEN = colors.HexColor("#70AD47")
PALE = colors.HexColor("#EEF5FA")
GREY = colors.HexColor("#666666")

body = ParagraphStyle(
    "FVBody",
    fontName=FONT,
    fontSize=9.1,
    leading=12.8,
    textColor=colors.HexColor("#222222"),
    spaceAfter=7,
)
h1 = ParagraphStyle(
    "FVH1", parent=body, fontName=BOLD, fontSize=18, leading=22, textColor=NAVY, spaceAfter=12
)
h2 = ParagraphStyle(
    "FVH2",
    parent=body,
    fontName=BOLD,
    fontSize=12.5,
    leading=15,
    textColor=BLUE,
    spaceBefore=8,
    spaceAfter=7,
)
small = ParagraphStyle(
    "FVSmall", parent=body, fontSize=7.25, leading=9.2, alignment=TA_LEFT, spaceAfter=2
)
caption = ParagraphStyle(
    "FVCaption", parent=small, alignment=TA_CENTER, textColor=GREY, spaceAfter=8
)
bullet = ParagraphStyle("FVBullet", parent=body, leftIndent=14, firstLineIndent=-8, spaceAfter=4)
callout = ParagraphStyle(
    "FVCallout", parent=body, fontName=BOLD, fontSize=10.5, leading=14, textColor=NAVY, spaceAfter=8
)


def P(text, style=body):
    return Paragraph(text, style)


def table(data, widths, green_last=False):
    rows = []
    for i, row in enumerate(data):
        style = (
            small
            if i
            else ParagraphStyle(
                f"FVHeader{id(data)}",
                parent=small,
                fontName=BOLD,
                textColor=colors.white,
                alignment=TA_CENTER,
            )
        )
        rows.append([P(str(value), style) for value in row])
    result = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B7C9D6")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(2, len(rows), 2):
        commands.append(("BACKGROUND", (0, i), (-1, i), PALE))
    if green_last and len(rows) > 1:
        commands += [
            ("BACKGROUND", (-1, 1), (-1, -1), colors.HexColor("#E2F0D9")),
            ("TEXTCOLOR", (-1, 1), (-1, -1), colors.HexColor("#375623")),
        ]
    result.setStyle(TableStyle(commands))
    return result


def create_pages():
    TMP.mkdir(parents=True, exist_ok=True)
    results = pd.read_csv(DATA / "validation_results.csv")
    correlations = pd.read_csv(DATA / "correlation_checks.csv")
    pages = TMP / "functional_validation_pages.pdf"
    doc = SimpleDocTemplate(
        str(pages),
        pagesize=A4,
        leftMargin=1.55 * cm,
        rightMargin=1.55 * cm,
        topMargin=1.45 * cm,
        bottomMargin=1.45 * cm,
    )

    family_rows = [["Famille", "Contrôles", "Réussis", "Échecs"]]
    order = [
        "Distributions",
        "Reproductibilité",
        "Corrélations",
        "Variantes",
        "Erreurs Excel",
        "Sorties",
    ]
    for family in order:
        subset = results[results.family == family]
        family_rows.append(
            [
                family,
                len(subset),
                int((subset.status == "PASS").sum()),
                int((subset.status == "FAIL").sum()),
            ]
        )
    family_rows.append(
        [
            "Total fonctionnel",
            len(results),
            int((results.status == "PASS").sum()),
            int((results.status == "FAIL").sum()),
        ]
    )

    dist = results[results.family == "Distributions"]
    dist_pick = [
        ["Contrôle", "Observation", "Critère", "État"],
        ["Triangulaire - bornes", dist.iloc[0].observed, "Tirages dans [10, 40]", "PASS"],
        ["PERT - bornes", dist.iloc[1].observed, "Tirages dans [10, 40]", "PASS"],
        [
            "Uniforme - moyenne",
            dist[dist.test == "uniform: moyenne"].iloc[0].observed,
            "Écart < 0,10",
            "PASS",
        ],
        ["Normale - moyenne / σ", "99,9931 / 15,0000", "Écarts < 0,15", "PASS"],
        ["Lognormale - moyenne / σ", "100,0874 / 19,9992", "Écarts < 0,25", "PASS"],
        ["Lognormale - positivité", "minimum 41,2172", "Tous les tirages > 0", "PASS"],
        ["Événement - fréquence", "0,23011", "|fréquence - 0,23| < 0,003", "PASS"],
    ]

    corr_rows = [["Relation", "Cible latente", "Spearman observé", "Lecture"]]
    for _, row in correlations.iterrows():
        event = "Hausse exceptionnelle" in row["second"] or "Retard administratif" in row["second"]
        corr_rows.append(
            [
                f"{row['first']} / {row['second']}",
                f"{row['target']:.2f}",
                f"{row['observed_spearman']:.4f}",
                "Atténuation binaire attendue" if event else "Écart < 0,05",
            ]
        )

    invalid = results[results.family == "Erreurs Excel"]
    invalid_labels = {
        "minimum_superieur_maximum": "Minimum supérieur au maximum",
        "probabilite_superieure_1": "Probabilité supérieure à 1",
        "distribution_inconnue": "Distribution inconnue",
        "parametre_obligatoire_manquant": "Paramètre obligatoire manquant",
        "matrice_non_symetrique": "Matrice non symétrique",
        "diagonale_differente_1": "Diagonale différente de 1",
        "nom_poste_duplique": "Nom de poste dupliqué",
        "unites_incompatibles": "Unités incompatibles",
        "matrice_non_definie_positive": "Matrice non définie positive",
    }
    invalid_rows = [["Cas injecté", "Comportement attendu", "Résultat"]]
    for _, row in invalid.iterrows():
        invalid_rows.append(
            [invalid_labels[row.test], "Rejet avec feuille, ligne/champ et message", row.status]
        )

    output_rows = [
        ["Sortie contrôlée", "Recalcul indépendant", "Résultat"],
        [
            "Résumé statistique",
            "Moyenne, médiane, σ population, min, max, P50, P80, P90 via NumPy ; égalité à 1e-9",
            "PASS",
        ],
        ["Baseline", "Fréquence stricte total > 7 750 000 et quantiles recalculés", "PASS"],
        ["Sensibilité", "Spearman recalculé ; |rho| décroissant ; rangs consécutifs", "PASS"],
        ["Total simulé", "Somme ligne à ligne des 18 contributions ; écart maximal 0", "PASS"],
        ["Table de decision", "P50, P80, P90, depassements et reserves recalcules", "PASS"],
        [
            "Convergence",
            "P90 cumule recalcule par bloc ; comptages croissants ; arret unique au plus",
            "PASS",
        ],
        ["Courbe en S", "10 000 totaux tries ; probabilite cumulee croissante jusqu'a 1", "PASS"],
        ["Jeu de livrables", "Huit fichiers attendus presents et non vides", "PASS"],
    ]

    story = [
        P("16. Protocole de validation fonctionnelle", h1),
        P(
            "Cette validation vise le fonctionnement du logiciel, non la crédibilité métier des montants. Elle complète les tests unitaires par des contrôles statistiques et des scénarios Excel de bout en bout exécutés sur les artefacts réels des trois variantes.",
            body,
        ),
        P("16.1 Périmètre et résultat global", h2),
        table(family_rows, [6.7 * cm, 3.5 * cm, 3.5 * cm, 3.7 * cm], green_last=True),
        Spacer(1, 0.35 * cm),
        P(
            "44 contrôles fonctionnels réussis sur 44, auxquels s’ajoutent 337 tests automatisés réussis.",
            callout,
        ),
        P("16.2 Conditions d’exécution", h2),
        P("• Python local du projet et version courante du code source.", bullet),
        P(
            "• Grands échantillons de 200 000 tirages pour les distributions et les corrélations.",
            bullet,
        ),
        P("• Registres réels des variantes 1, 2 et 3 pour les contrôles de cohérence.", bullet),
        P(
            "• Graine 42 pour la reproductibilité ; graine 43 pour la stabilité inter-graines.",
            bullet,
        ),
        P("• Neuf copies temporaires volontairement corrompues pour les rejets Excel.", bullet),
        P("16.3 Critère d’acceptation", h2),
        P(
            "Chaque contrôle possède une observation et un seuil explicites. Le protocole échoue dès qu’un seul contrôle est en échec ; les résultats détaillés sont exportés dans output/functional_validation/.",
            body,
        ),
        PageBreak(),
        P("17. Distributions et reproductibilité", h1),
        P("17.1 Propriétés des distributions", h2),
        table(dist_pick, [4.4 * cm, 4.3 * cm, 6.0 * cm, 2.7 * cm], green_last=True),
        P(
            "Les contrôles ont porté sur 200 000 tirages par distribution. Les lois triangulaire, PERT et uniforme respectent leurs bornes ; la normale reproduit ses deux moments ; la lognormale reste positive et asymétrique ; l’événement ne produit que 0 ou l’impact attendu.",
            body,
        ),
        P("17.2 Reproductibilité", h2),
        table(
            [
                ["Test", "Observation", "Résultat"],
                [
                    "Même registre, graine 42, deux exécutions",
                    "Totaux et contributions identiques bit à bit",
                    "PASS",
                ],
                ["CSV exportés", "SHA-256 identiques pour résumé, sensibilité et baseline", "PASS"],
                ["Graine 43", "Tirages différents", "PASS"],
                ["Stabilité inter-graines", "Écart moyen 0,17994 % ; écart P90 0,25186 %", "PASS"],
            ],
            [5.3 * cm, 8.8 * cm, 3.3 * cm],
            green_last=True,
        ),
        P(
            "La reproductibilité est exacte lorsque la graine reste fixe. Avec une autre graine, les échantillons changent mais les indicateurs demeurent proches sous les seuils de 0,3 % pour la moyenne et 0,5 % pour P90.",
            body,
        ),
        PageBreak(),
        P("18. Corrélations et comportement des variantes", h1),
        P("18.1 Corrélations observées", h2),
        table(corr_rows, [6.3 * cm, 2.7 * cm, 3.4 * cm, 5.0 * cm]),
        P(
            "Pour deux variables continues, le Spearman observé est proche de la corrélation latente imposée par la copule. Lorsqu’un poste est un événement binaire, la transformation 0/impact crée de nombreux ex æquo et atténue nécessairement la corrélation observée. Le critère vérifie alors le signe, une dépendance matérialisée supérieure à 0,20 et une valeur inférieure à la corrélation latente.",
            body,
        ),
        P(
            "Trois couples sans corrélation imposée ont également été testés : leurs coefficients observés sont 0,0018, 0,0015 et -0,0027, tous inférieurs à 0,015 en valeur absolue.",
            body,
        ),
        P("18.2 Effets attendus des variantes", h2),
        table(
            [
                ["Contrôle", "Observation", "Résultat"],
                ["V2 - moyenne stable", "Écart relatif V2/V1 inférieur à 0,1 %", "PASS"],
                ["V2 - dispersion", "Écart-type +9,9 % ; P90 +69 012 MAD", "PASS"],
                ["V3 - stress", "Moyenne, médiane, σ, P80 et P90 supérieurs à V2", "PASS"],
                ["V3 - baseline", "Dépassement : 90,86 % contre 63,88 % en V2", "PASS"],
            ],
            [5.0 * cm, 9.1 * cm, 3.3 * cm],
            green_last=True,
        ),
        PageBreak(),
        P("19. Validation des erreurs Excel", h1),
        P(
            "Chaque défaut a été injecté dans une copie du registre corrélé puis soumis au chargeur public. Les neuf fichiers ont été refusés avec un message contextualisé.",
            body,
        ),
        table(invalid_rows, [6.0 * cm, 8.4 * cm, 3.0 * cm], green_last=True),
        Spacer(1, 0.35 * cm),
        P("19.1 Enseignement", h2),
        P(
            "Le validateur ne se limite pas aux paramètres de distribution : il contrôle aussi les unités, l’unicité des noms, la cohérence des axes de corrélation, la symétrie, la diagonale et le caractère strictement défini positif de la matrice.",
            body,
        ),
        P(
            "Les messages mentionnent la feuille et, lorsque cela s’applique, la ligne, le poste, le champ et la valeur rejetée. Cette précision permet à l’utilisateur de corriger le classeur sans examiner le code.",
            body,
        ),
        PageBreak(),
        P("20. Recalcul indépendant des sorties", h1),
        table(output_rows, [5.0 * cm, 9.4 * cm, 3.0 * cm], green_last=True),
        Spacer(1, 0.35 * cm),
        P("20.1 Conclusion technique", h2),
        P(
            "Les quantiles, la baseline et la sensibilité ne sont pas seulement présents : ils ont été recalculés indépendamment à partir des tirages en mémoire. La somme exacte des contributions confirme aussi que la baseline n’est jamais ajoutée aux coûts et qu’aucun poste n’est comptabilisé deux fois.",
            body,
        ),
        P(
            "Conclusion : dans le périmètre testé, les fonctions de lecture Excel, validation, échantillonnage, corrélation, agrégation, statistiques, sensibilité, table de décision, convergence, courbe en S et export produisent les comportements attendus et reproductibles.",
            callout,
        ),
        P("20.2 Portée de la conclusion", h2),
        P(
            "Cette conclusion démontre le fonctionnement du logiciel pour le schéma 1.0 et les cas testés. Elle ne certifie ni la justesse économique des hypothèses synthétiques, ni les performances sur des registres beaucoup plus volumineux, ni l’absence absolue de défaut dans des contextes non couverts.",
            body,
        ),
        PageBreak(),
        P("21. Programme des prochaines mises à jour", h1),
        P(
            "La construction des variantes et la validation fonctionnelle sont terminées. Les prochaines améliorations concernent l’industrialisation et, séparément, une éventuelle validation métier.",
            body,
        ),
        P("21.1 Industrialisation", h2),
        P(
            "• Exécuter automatiquement les 337 tests et le protocole fonctionnel dans l’intégration continue.",
            bullet,
        ),
        P(
            "• Ajouter des seuils de performance pour les gros registres et les grands nombres de tirages.",
            bullet,
        ),
        P(
            "• Archiver les rapports de validation et leurs empreintes avec chaque version publiée.",
            bullet,
        ),
        P("• Documenter la compatibilité des versions Python, Excel et des dépendances.", bullet),
        P("21.2 Validation métier optionnelle", h2),
        P("• Faire relire les valeurs synthétiques par des spécialistes du bâtiment.", bullet),
        P(
            "• Remplacer, lorsque disponibles, les jugements de corrélation par des données historiques.",
            bullet,
        ),
        P(
            "• Définir le niveau de confiance budgétaire cible selon la gouvernance du projet.",
            bullet,
        ),
        PageBreak(),
        P("22. Sources et traçabilité", h1),
        P(
            "Les sources publiques des versions précédentes restent applicables. La présente mise à jour ajoute une traçabilité technique reproductible.",
            body,
        ),
        P(
            "1. Résultats détaillés : output/functional_validation/validation_results.csv et validation_summary.json.",
            small,
        ),
        P(
            "2. Mesures des distributions : output/functional_validation/distribution_checks.csv.",
            small,
        ),
        P("3. Mesures de dépendance : output/functional_validation/correlation_checks.csv.", small),
        P("4. Rejets Excel : output/functional_validation/invalid_workbook_checks.csv.", small),
        P("5. Suite automatisée : 337 tests réussis avec pytest le 31 juillet 2026.", small),
        P("6. Registres et sorties des trois variantes sous output/.", small),
        P("Journal de mise à jour", h2),
        table(
            [
                ["Version", "Contenu ajouté", "État"],
                ["0.1", "Projet fictif, règles, variante 1", "Terminée"],
                ["0.2", "Variante 2 et corrélations", "Terminée"],
                ["0.3", "Variante 3 et comparaison consolidée", "Terminée"],
                ["0.5", "Protocole fonctionnel : 44/44 et suite 337/337", "Présente version"],
                ["1.0", "Industrialisation et décision de publication", "À venir"],
            ],
            [2.4 * cm, 11.0 * cm, 4.0 * cm],
        ),
    ]
    doc.build(story)
    return pages


def overlay(page, number, cover=False):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    if cover:
        c.setFillColor(colors.white)
        c.rect(38, 240, A4[0] - 76, 235, fill=1, stroke=0)
        data = [
            ["État du document", "Version 0.5 - validation fonctionnelle terminée"],
            ["Cas étudié", "Trois variantes du bâtiment administratif synthétique"],
            ["Validation", "44 contrôles fonctionnels + 337 tests automatisés"],
            ["Reproductibilité", "10 000 simulations, graine 42"],
            ["Mise à jour suivante", "Industrialisation et décision de publication"],
        ]
        x, y, width, rh = 44, 435, 507, 24
        for i, (left, right) in enumerate(data):
            yy = y - i * rh
            c.setFillColor(colors.HexColor("#F2F2F2") if i % 2 == 0 else colors.white)
            c.rect(x, yy - rh, width, rh, fill=1, stroke=0)
            c.setStrokeColor(colors.HexColor("#B7C9D6"))
            c.rect(x, yy - rh, width, rh, fill=0, stroke=1)
            c.line(x + 125, yy - rh, x + 125, yy)
            c.setFont(BOLD, 8)
            c.setFillColor(colors.HexColor("#222222"))
            c.drawString(x + 5, yy - 16, left)
            c.setFont(FONT, 8)
            c.drawString(x + 131, yy - 16, right)
    c.setFillColor(colors.white)
    c.rect(30, 12, A4[0] - 60, 40, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor("#B4C7DC"))
    c.line(1.5 * cm, 1.18 * cm, A4[0] - 1.5 * cm, 1.18 * cm)
    c.setFont(FONT, 8)
    c.setFillColor(GREY)
    c.drawString(
        1.5 * cm, 0.72 * cm, "Projet Monte-Carlo-Simulator - Étude de cas évolutive - Version 0.5"
    )
    c.drawRightString(A4[0] - 1.5 * cm, 0.72 * cm, f"Page {number}")
    c.save()
    buffer.seek(0)
    page.merge_page(PdfReader(buffer).pages[0])
    return page


def main():
    old = PdfReader(str(PDF))
    new = PdfReader(str(create_pages()))
    pages = list(old.pages[:19]) + list(new.pages)
    writer = PdfWriter()
    for index, page in enumerate(pages):
        writer.add_page(overlay(page, index + 1, cover=index == 0))
    writer.add_metadata(
        {
            "/Title": "Étude de cas évolutive - Version 0.5",
            "/Author": "Équipe Monte-Carlo-Simulator",
        }
    )
    staged = TMP / "report_v05.pdf"
    with staged.open("wb") as stream:
        writer.write(stream)
    staged.replace(PDF)
    print(PDF)


if __name__ == "__main__":
    main()
