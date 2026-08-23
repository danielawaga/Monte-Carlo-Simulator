# ruff: noqa: E501
"""Integrate variant 3 into the evolving case-study PDF."""

from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[2]
# Sorties de travail de l'étude de cas : générées, jamais versionnées.
WORK = ROOT / "data" / "output" / "case_study"
PDF = ROOT / "reports" / "case_study" / "etude_cas_batiment_monte_carlo.pdf"
TMP = WORK / "tmp" / "pdfs" / "etude_cas_batiment" / "variant3"
V3 = WORK / "simulation_batiment_stress"

FONT_PATH = Path("C:/Windows/Fonts/segoeui.ttf")
BOLD_PATH = Path("C:/Windows/Fonts/segoeuib.ttf")
pdfmetrics.registerFont(TTFont("V3Regular", str(FONT_PATH)))
pdfmetrics.registerFont(TTFont("V3Bold", str(BOLD_PATH)))
FONT, BOLD = "V3Regular", "V3Bold"
NAVY = colors.HexColor("#17365D")
BLUE = colors.HexColor("#2F75B5")
PALE = colors.HexColor("#EEF5FA")
GREY = colors.HexColor("#666666")

body = ParagraphStyle(
    "BodyV3",
    fontName=FONT,
    fontSize=9.2,
    leading=13,
    textColor=colors.HexColor("#222222"),
    spaceAfter=7,
)
h1 = ParagraphStyle(
    "H1V3", parent=body, fontName=BOLD, fontSize=18, leading=22, textColor=NAVY, spaceAfter=12
)
h2 = ParagraphStyle(
    "H2V3",
    parent=body,
    fontName=BOLD,
    fontSize=12.5,
    leading=15,
    textColor=BLUE,
    spaceBefore=8,
    spaceAfter=7,
)
small = ParagraphStyle(
    "SmallV3", parent=body, fontSize=7.4, leading=9.4, alignment=TA_LEFT, spaceAfter=3
)
caption = ParagraphStyle(
    "CaptionV3", parent=small, alignment=TA_CENTER, textColor=GREY, spaceAfter=8
)
bullet = ParagraphStyle("BulletV3", parent=body, leftIndent=14, firstLineIndent=-8, spaceAfter=4)


def P(text, style=body):
    return Paragraph(text, style)


def table(data, widths):
    rows = []
    for i, row in enumerate(data):
        style = (
            small
            if i
            else ParagraphStyle(
                f"Header{id(data)}",
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
    result.setStyle(TableStyle(commands))
    return result


def make_comparison_chart():
    path = TMP / "comparaison_variantes_1_2_3.png"
    labels = ["Moyenne", "P50", "P80", "P90"]
    values = np.array(
        [
            [7.928325, 7.904221, 8.243501, 8.431266],
            [7.930657, 7.887998, 8.275998, 8.500278],
            [8.488603, 8.436226, 8.992818, 9.282370],
        ]
    )
    x = np.arange(len(labels))
    width = 0.24
    fig, ax = plt.subplots(figsize=(8.8, 4.0))
    for offset, row, name, color in zip(
        (-width, 0, width),
        values,
        ("Variante 1", "Variante 2", "Variante 3"),
        ("#5B9BD5", "#17365D", "#ED7D31"),
        strict=True,
    ):
        bars = ax.bar(x + offset, row, width, label=name, color=color)
        for bar in bars:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.018,
                f"{bar.get_height():.3f}",
                ha="center",
                fontsize=7,
            )
    ax.set_ylim(7.65, 9.48)
    ax.set_ylabel("Millions de MAD")
    ax.set_xticks(x, labels)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False, ncol=3, loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=190, bbox_inches="tight")
    plt.close(fig)
    return path


def create_pages():
    TMP.mkdir(parents=True, exist_ok=True)
    chart = make_comparison_chart()
    pages = TMP / "variant3_pages.pdf"
    doc = SimpleDocTemplate(
        str(pages),
        pagesize=A4,
        leftMargin=1.55 * cm,
        rightMargin=1.55 * cm,
        topMargin=1.45 * cm,
        bottomMargin=1.45 * cm,
    )
    stress = [
        ["Hypothèse", "Variante 2", "Variante 3", "Raison du stress"],
        [
            "Terrassement (mode / max)",
            "400 / 650 k",
            "430 / 750 k",
            "Sol et évacuations défavorables",
        ],
        [
            "Gros œuvre (mode / max)",
            "1 900 / 2 500 k",
            "2 000 / 2 800 k",
            "Quantités et prix sous tension",
        ],
        ["CVC (mode / max)", "550 / 800 k", "580 / 900 k", "Importation et redimensionnement"],
        ["Finitions (mode / max)", "950 / 1 300 k", "1 000 / 1 500 k", "Choix tardifs et reprises"],
        ["Supervision (moy. / σ)", "300 / 45 k", "320 / 60 k", "Mobilisation plus longue"],
        [
            "Sol difficile (p / impact)",
            "12 % / 350 k",
            "18 % / 450 k",
            "Reconnaissances incomplètes",
        ],
        [
            "Hausse matériaux (p / impact)",
            "20 % / 450 k",
            "30 % / 600 k",
            "Choc plus fréquent et sévère",
        ],
        ["Retard (p / impact)", "18 % / 250 k", "25 % / 350 k", "Délais externes renforcés"],
        ["Modification (p / impact)", "15 % / 300 k", "20 % / 400 k", "Arbitrages tardifs"],
        ["Fournisseur (p / impact)", "10 % / 220 k", "15 % / 300 k", "Chaîne fragilisée"],
        ["Négociation (p / impact)", "25 % / -120 k", "15 % / -80 k", "Opportunité réduite"],
    ]
    comparison = [
        ["Indicateur", "Variante 1", "Variante 2", "Variante 3", "V3 - V2"],
        ["Moyenne", "7 928 325", "7 930 657", "8 488 603", "+557 946"],
        ["P50", "7 904 221", "7 887 998", "8 436 226", "+548 229"],
        ["Écart-type", "374 795", "412 005", "579 914", "+40,8 %"],
        ["P80", "8 243 501", "8 275 998", "8 992 818", "+716 820"],
        ["P90", "8 431 266", "8 500 278", "9 282 370", "+782 092"],
        ["Dépassement baseline", "65,96 %", "63,88 %", "90,86 %", "+26,98 pts"],
    ]
    story = [
        P("12. Variante 3 stressée", h1),
        P(
            "La variante 3 conserve les 18 postes, la baseline de 7 750 000 MAD, la matrice de corrélation de la variante 2, les 10 000 tirages et la graine 42. Seules les hypothèses explicitement recensées ci-dessous sont dégradées.",
            body,
        ),
        P("12.1 Hypothèses modifiées", h2),
        table(stress, [4.7 * cm, 3.3 * cm, 3.3 * cm, 6.1 * cm]),
        Spacer(1, 0.25 * cm),
        P(
            "Le stress n’est pas une prévision centrale. Il représente un contexte défavorable plausible destiné à tester la robustesse des décisions budgétaires.",
            body,
        ),
        PageBreak(),
        P("13. Comparaison consolidée des trois variantes", h1),
        table(comparison, [3.8 * cm, 3.2 * cm, 3.2 * cm, 3.2 * cm, 4.0 * cm]),
        Spacer(1, 0.35 * cm),
        Image(str(chart), width=16.6 * cm, height=7.5 * cm),
        P("Figure 7 - Comparaison de la moyenne et des percentiles des trois variantes.", caption),
        P(
            "Contrairement aux corrélations seules, le stress déplace fortement le centre de la distribution et épaissit sa queue haute. La hausse de P90 (+782 092 MAD par rapport à la variante 2) dépasse celle de la moyenne (+557 946 MAD).",
            body,
        ),
        PageBreak(),
        P("14. Distribution simulée de la variante 3", h1),
        Image(str(V3 / "simulation_histogram.png"), width=16.6 * cm, height=9.5 * cm),
        P(
            "Figure 8 - Distribution du coût total, variante 3 stressée, 10 000 tirages, graine 42.",
            caption,
        ),
        table(
            [
                ["Repère", "Montant", "Écart à la baseline"],
                ["P50", "8 436 226 MAD", "+686 226 MAD (+8,85 %)"],
                ["P80", "8 992 818 MAD", "+1 242 818 MAD (+16,04 %)"],
                ["P90", "9 282 370 MAD", "+1 532 370 MAD (+19,77 %)"],
            ],
            [4.0 * cm, 5.0 * cm, 8.4 * cm],
        ),
        Spacer(1, 0.3 * cm),
        P(
            "La baseline est dépassée dans 90,86 % des simulations. Dans ce scénario, elle ne peut donc plus être interprétée comme un budget prudent.",
            body,
        ),
        PageBreak(),
        P("15. Sensibilité et interprétation de la variante 3", h1),
        Image(str(V3 / "sensitivity_tornado.png"), width=16.2 * cm, height=9.7 * cm),
        P("Figure 9 - Sensibilité de Spearman, variante 3 stressée.", caption),
        P(
            "La hausse exceptionnelle des matériaux devient le premier facteur (rho = 0,615), suivie des fondations et du gros œuvre (rho = 0,600). Le sol difficile (rho = 0,290), le retard (rho = 0,279) et la modification tardive (rho = 0,268) complètent le groupe prioritaire.",
            body,
        ),
        P("15.1 Lecture décisionnelle", h2),
        P(
            "Le scénario stressé montre que la contingence requise dépend fortement du contexte retenu. Un budget P80 proche de 8,993 M MAD représente environ 1,243 M MAD de réserve au-dessus de la baseline actuelle. Cette valeur ne doit pas être adoptée mécaniquement : elle sert à matérialiser l’exposition si plusieurs hypothèses se dégradent simultanément.",
            body,
        ),
        P("15.2 Limites", h2),
        P(
            "Les stress sont des hypothèses de travail et non des prévisions issues de données historiques. Leur sévérité devra être examinée poste par poste avec des spécialistes du coût, du planning, du marché et de la géotechnique.",
            body,
        ),
        PageBreak(),
        P("16. Programme des prochaines mises à jour", h1),
        P(
            "Les trois variantes sont désormais développées. Les prochaines mises à jour porteront sur la validation et la décision, non sur la création d’un quatrième registre.",
            body,
        ),
        P("16.1 Validation métier", h2),
        P(
            "• Revoir les fourchettes continues et les probabilités avec des spécialistes du projet.",
            bullet,
        ),
        P(
            "• Rechercher des historiques permettant d’étayer ou de recalibrer les corrélations.",
            bullet,
        ),
        P(
            "• Définir le niveau de confiance budgétaire cible en fonction de l’appétence au risque.",
            bullet,
        ),
        P(
            "• Documenter les mesures de réduction et, si nécessaire, simuler un scénario après traitement.",
            bullet,
        ),
        P("16.2 Décisions à formaliser", h2),
        P("• Baseline ou enveloppe de référence retenue.", bullet),
        P("• Niveau P50, P80 ou P90 utilisé pour la contingence.", bullet),
        P("• Risques prioritaires, responsables et calendrier de réponse.", bullet),
        P("• Conditions déclenchant une nouvelle simulation.", bullet),
        PageBreak(),
        P("17. Sources et traçabilité", h1),
        P(
            "Les sources publiques présentées dans les versions précédentes restent applicables. Elles justifient les familles de travaux et les principes méthodologiques, mais pas directement les valeurs synthétiques.",
            body,
        ),
        P(
            "1. Ministère des Habous et des Affaires islamiques, bordereau public de construction à Azrou.<br/><font color='#2F75B5'>https://habous.gov.ma/fr/index.php?cf_id=36&amp;link_id=353&amp;option=com_mtree&amp;task=att_download</font>",
            small,
        ),
        P(
            "2. Haut-Commissariat au Plan du Maroc, Indices des prix et production.<br/><font color='#2F75B5'>https://www.hcp.ma/Indices-des-prix-et-production_r343.html</font>",
            small,
        ),
        P(
            "3. HM Treasury, Green Book supplementary guidance: optimism bias.<br/><font color='#2F75B5'>https://www.gov.uk/government/publications/green-book-supplementary-guidance-optimism-bias</font>",
            small,
        ),
        P(
            "4. HM Treasury, The Green Book 2026.<br/><font color='#2F75B5'>https://www.gov.uk/government/publications/the-green-book-appraisal-and-evaluation-in-central-government/the-green-book-2026</font>",
            small,
        ),
        P(
            "5. Homes England, Optimism Bias and Contingency.<br/><font color='#2F75B5'>https://www.gov.uk/government/publications/optimism-bias-and-contingency-at-homes-england/optimism-bias-and-contingency-at-homes-england-accessible-version</font>",
            small,
        ),
        P(
            "6. Traçabilité interne : registres des variantes 1, 2 et 3 ; dossiers de simulation correspondants ; feuille stress_changes de la variante 3.",
            small,
        ),
        P("Journal de mise à jour", h2),
        table(
            [
                ["Version", "Contenu ajouté", "État"],
                ["0.1", "Projet fictif, règles, variante 1 et résultats", "Terminée"],
                ["0.2", "Variante 2, matrice et comparaison", "Terminée"],
                ["0.3", "Variante 3 stressée et comparaison consolidée", "Présente version"],
                ["1.0", "Validation métier, décisions et conclusion", "À venir"],
            ],
            [2.4 * cm, 11.0 * cm, 4.0 * cm],
        ),
    ]
    doc.build(story)
    return pages


def overlay_page(page, page_number, cover=False, scenario=False):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    if cover:
        c.setFillColor(colors.white)
        c.rect(38, 240, A4[0] - 76, 235, fill=1, stroke=0)
        data = [
            ["État du document", "Version 0.3 - trois variantes simulées"],
            ["Cas étudié", "Bâtiment administratif fictif R+1 d’environ 700 m² au Maroc"],
            ["Analyse", "Coût hors taxes en MAD"],
            ["Reproductibilité", "10 000 simulations, graine aléatoire 42"],
            ["Mise à jour suivante", "Validation métier et décisions budgétaires"],
        ]
        x, y, w, rh = 44, 435, 507, 24
        for i, (left, right) in enumerate(data):
            yy = y - i * rh
            c.setFillColor(colors.HexColor("#F2F2F2") if i % 2 == 0 else colors.white)
            c.rect(x, yy - rh, w, rh, fill=1, stroke=0)
            c.setStrokeColor(colors.HexColor("#B7C9D6"))
            c.rect(x, yy - rh, w, rh, fill=0, stroke=1)
            c.line(x + 125, yy - rh, x + 125, yy)
            c.setFont(BOLD, 8)
            c.setFillColor(colors.HexColor("#222222"))
            c.drawString(x + 5, yy - 16, left)
            c.setFont(FONT, 8)
            c.drawString(x + 131, yy - 16, right)
    if scenario:
        c.setFillColor(colors.white)
        c.rect(38, 500, A4[0] - 76, 215, fill=1, stroke=0)
        c.setFont(BOLD, 12.5)
        c.setFillColor(BLUE)
        c.drawString(44, 690, "1.1 Stratégie des trois variantes")
        boxes = [
            (44, "Variante 1", "Sans corrélation", "Réalisée", "#D9EAF7"),
            (224, "Variante 2", "Corrélations modérées", "Réalisée", "#E2F0D9"),
            (404, "Variante 3", "Stress ciblé", "Réalisée", "#FCE4D6"),
        ]
        for x, title, sub, status, fill in boxes:
            c.setFillColor(colors.HexColor(fill))
            c.setStrokeColor(BLUE)
            c.rect(x, 615, 145, 56, fill=1, stroke=1)
            c.setFillColor(NAVY)
            c.setFont(BOLD, 9)
            c.drawCentredString(x + 72.5, 652, title)
            c.setFont(FONT, 7.5)
            c.drawCentredString(x + 72.5, 638, sub)
            c.drawCentredString(x + 72.5, 624, status)
        c.setFillColor(colors.HexColor("#222222"))
        c.setFont(FONT, 8.6)
        text = c.beginText(44, 535)
        text.setLeading(12)
        text.textLine(
            "Les trois variantes conservent le m\u00eame projet et la m\u00eame structure de postes. Une seule famille"
        )
        text.textLine(
            "de param\u00e8tres est modifi\u00e9e \u00e0 la fois afin de s\u00e9parer les effets des corr\u00e9lations et du stress."
        )
        c.drawText(text)
    c.setFillColor(colors.white)
    c.rect(30, 12, A4[0] - 60, 40, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor("#B4C7DC"))
    c.line(1.5 * cm, 1.18 * cm, A4[0] - 1.5 * cm, 1.18 * cm)
    c.setFont(FONT, 8)
    c.setFillColor(GREY)
    c.drawString(
        1.5 * cm, 0.72 * cm, "Projet Monte-Carlo-Simulator - Étude de cas évolutive - Version 0.3"
    )
    c.drawRightString(A4[0] - 1.5 * cm, 0.72 * cm, f"Page {page_number}")
    c.save()
    buffer.seek(0)
    page.merge_page(PdfReader(buffer).pages[0])
    return page


def main():
    new_pages = PdfReader(str(create_pages()))
    old = PdfReader(str(PDF))
    pages = list(old.pages[:15]) + list(new_pages.pages)
    writer = PdfWriter()
    for index, page in enumerate(pages):
        writer.add_page(overlay_page(page, index + 1, cover=index == 0, scenario=index == 1))
    writer.add_metadata(
        {
            "/Title": "Étude de cas évolutive - Version 0.3",
            "/Author": "Équipe Monte-Carlo-Simulator",
        }
    )
    staged = TMP / "report_v03.pdf"
    with staged.open("wb") as stream:
        writer.write(stream)
    staged.replace(PDF)
    print(PDF)


if __name__ == "__main__":
    main()
