# ruff: noqa: E501
"""Insert the correlated variant pages into the evolving case-study report."""

from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
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

from monte_carlo_simulator.io import load_risk_register

ROOT = Path(__file__).resolve().parents[2]
# Sorties de travail de l'étude de cas : générées, jamais versionnées.
WORK = ROOT / "data" / "output" / "case_study"
PDF = ROOT / "reports" / "case_study" / "etude_cas_batiment_monte_carlo.pdf"
V1 = WORK / "simulation_batiment"
V2 = WORK / "simulation_batiment_correlations"
REGISTER = WORK / "registre_risques_batiment_correlations.xlsx"
TMP = WORK / "tmp" / "pdfs" / "etude_cas_batiment" / "variant2"

pdfmetrics.registerFont(TTFont("V2Regular", "C:/Windows/Fonts/segoeui.ttf"))
pdfmetrics.registerFont(TTFont("V2Bold", "C:/Windows/Fonts/segoeuib.ttf"))
FONT, BOLD = "V2Regular", "V2Bold"
NAVY = colors.HexColor("#17365D")
BLUE = colors.HexColor("#2F75B5")
GREEN = colors.HexColor("#70AD47")
PALE = colors.HexColor("#EEF5FA")
GREY = colors.HexColor("#666666")

body = ParagraphStyle(
    "V2Body",
    fontName=FONT,
    fontSize=9.1,
    leading=12.8,
    textColor=colors.HexColor("#222222"),
    spaceAfter=7,
)
h1 = ParagraphStyle(
    "V2H1", parent=body, fontName=BOLD, fontSize=18, leading=22, textColor=NAVY, spaceAfter=12
)
h2 = ParagraphStyle(
    "V2H2",
    parent=body,
    fontName=BOLD,
    fontSize=12.5,
    leading=15,
    textColor=BLUE,
    spaceBefore=8,
    spaceAfter=7,
)
small = ParagraphStyle("V2Small", parent=body, fontSize=7.4, leading=9.5, spaceAfter=2)
caption = ParagraphStyle("V2Caption", parent=small, alignment=1, textColor=GREY, spaceAfter=8)
callout = ParagraphStyle(
    "V2Callout", parent=body, fontName=BOLD, fontSize=10.5, leading=14, textColor=NAVY, spaceAfter=8
)


def p(text, style=body):
    return Paragraph(text, style)


def table(rows, widths):
    formatted = []
    for index, row in enumerate(rows):
        style = ParagraphStyle(
            f"V2Table{index}{id(rows)}",
            parent=small,
            fontName=BOLD if index == 0 else FONT,
            textColor=colors.white if index == 0 else colors.HexColor("#222222"),
            alignment=1 if index == 0 else 0,
        )
        formatted.append([p(str(value), style) for value in row])
    result = Table(formatted, colWidths=widths, repeatRows=1, hAlign="LEFT")
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B7C9D6")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for index in range(2, len(rows), 2):
        commands.append(("BACKGROUND", (0, index), (-1, index), PALE))
    result.setStyle(TableStyle(commands))
    return result


def make_matrix_image() -> Path:
    register = load_risk_register(REGISTER)
    matrix = register.correlation_matrix
    if matrix is None:
        raise RuntimeError("The correlated register has no correlation matrix.")
    path = TMP / "correlation_matrix.png"
    fig, ax = plt.subplots(figsize=(10.5, 8.0))
    image = ax.imshow(matrix.values, vmin=-1, vmax=1, cmap="RdYlGn")
    labels = [name if len(name) <= 24 else name[:22] + "..." for name in matrix.item_names]
    ax.set_xticks(range(len(labels)), labels=labels, rotation=90, fontsize=5.5)
    ax.set_yticks(range(len(labels)), labels=labels, fontsize=5.5)
    for i in range(len(labels)):
        for j in range(len(labels)):
            value = matrix.values[i, j]
            if i == j or value != 0:
                ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=5, color="black")
    fig.colorbar(image, ax=ax, shrink=0.75, label="Correlation latente")
    fig.tight_layout()
    fig.savefig(path, dpi=170)
    plt.close(fig)
    return path


def create_pages() -> Path:
    TMP.mkdir(parents=True, exist_ok=True)
    matrix_path = make_matrix_image()
    v1 = pd.read_csv(V1 / "simulation_summary.csv").iloc[0]
    v2 = pd.read_csv(V2 / "simulation_summary.csv").iloc[0]
    baseline = pd.read_csv(V2 / "baseline_comparison.csv").iloc[0]
    pages = TMP / "variant2_pages.pdf"
    doc = SimpleDocTemplate(
        str(pages),
        pagesize=A4,
        leftMargin=1.55 * cm,
        rightMargin=1.55 * cm,
        topMargin=1.45 * cm,
        bottomMargin=1.45 * cm,
    )
    relations = [
        ["Relation", "Coefficient", "Justification"],
        ["Terrassement / fondations et gros œuvre", "0,30", "Conditions de sol communes."],
        [
            "Fondations et gros œuvre / hausse des matériaux",
            "0,50",
            "Exposition du gros œuvre au beton et à l'acier.",
        ],
        [
            "Électricité / plomberie",
            "0,25",
            "Modifications d'aménagement touchant plusieurs réseaux.",
        ],
        [
            "Supervision / retard administratif",
            "0,40",
            "Prolongation de la mobilisation de supervision.",
        ],
    ]
    comparison = [
        ["Indicateur", "Variante 1", "Variante 2", "Effet"],
        [
            "Moyenne",
            f"{v1['mean']:,.0f}",
            f"{v2['mean']:,.0f}",
            f"{(v2['mean'] / v1['mean'] - 1):+.2%}",
        ],
        [
            "Écart-type",
            f"{v1['std']:,.0f}",
            f"{v2['std']:,.0f}",
            f"{(v2['std'] / v1['std'] - 1):+.1%}",
        ],
        ["P80", f"{v1['P80']:,.0f}", f"{v2['P80']:,.0f}", f"{v2['P80'] - v1['P80']:+,.0f}"],
        ["P90", f"{v1['P90']:,.0f}", f"{v2['P90']:,.0f}", f"{v2['P90'] - v1['P90']:+,.0f}"],
    ]
    story = [
        p("11. Variante 2 corrélée", h1),
        p(
            "La variante 2 conserve les 18 postes, leurs distributions marginales, la baseline de 7 750 000 MAD, les 10 000 tirages et la graine 42. Seule une matrice parcimonieuse de quatre relations explicables est ajoutée.",
            body,
        ),
        p("11.1 Relations retenues", h2),
        table(relations, [6.3 * cm, 2.4 * cm, 8.7 * cm]),
        Spacer(1, 0.3 * cm),
        p(
            "Les coefficients sont des hypothèses synthétiques de travail. La matrice est symétrique, sa diagonale vaut 1 et elle est strictement définie positive.",
            callout,
        ),
        p(
            "La correlation est appliquee par une copule gaussienne avant transformation vers les distributions marginales. Les correlations impliquant un événement binaire sont donc atténuées apres discrétisation.",
            body,
        ),
        PageBreak(),
        p("11.2 Matrice de correlation", h1),
        Image(str(matrix_path), width=16.2 * cm, height=12.3 * cm),
        p(
            "Figure 4 - Matrice complète de la variante 2. Les coefficients hors diagonale non annotés valent zero.",
            caption,
        ),
        p(
            "La parcimonie évite d'introduire des dépendances non justifiees et permet d'isoler clairement leur effet sur la dispersion totale.",
            body,
        ),
        PageBreak(),
        p("11.3 Résultats de la variante 2", h1),
        Image(str(V2 / "simulation_histogram.png"), width=16.4 * cm, height=9.8 * cm),
        p(
            "Figure 5 - Distribution du coût total de la variante 2, 10 000 tirages, graine 42.",
            caption,
        ),
        table(comparison, [4.2 * cm, 4.2 * cm, 4.2 * cm, 4.8 * cm]),
        Spacer(1, 0.3 * cm),
        p(
            f"La moyenne reste presque stable, tandis que l'écart-type augmente. Le P90 atteint {v2['P90']:,.0f} MAD et la probabilité de dépasser la baseline atteint {baseline['exceedance_probability']:.2%}.",
            callout,
        ),
        PageBreak(),
        p("11.4 Sensibilité et interprétation", h1),
        Image(str(V2 / "sensitivity_tornado.png"), width=16.4 * cm, height=9.8 * cm),
        p("Figure 6 - Sensibilité de Spearman de la variante 2 corrélée.", caption),
        p(
            "Les fondations et le gros œuvre deviennent le premier facteur de sensibilite, devant la hausse exceptionnelle des matériaux. Ce resultat est cohérent avec la relation latente de 0,50 entre ces deux contributions.",
            body,
        ),
        p(
            "La variante 2 montre principalement un effet d'élargissement : le centre de la distribution varie peu, mais les quantiles de prudence augmentent. Elle constitue ainsi la référence corrélée utilisee pour mesurer ensuite l'effet additionnel du stress de la variante 3.",
            callout,
        ),
    ]
    doc.build(story)
    return pages


def overlay(page, number):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setFillColor(colors.white)
    c.rect(30, 12, A4[0] - 60, 40, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor("#B4C7DC"))
    c.line(1.5 * cm, 1.18 * cm, A4[0] - 1.5 * cm, 1.18 * cm)
    c.setFont(FONT, 8)
    c.setFillColor(GREY)
    c.drawString(
        1.5 * cm, 0.72 * cm, "Projet Monte-Carlo-Simulator - Étude de cas evolutive - Version 0.2"
    )
    c.drawRightString(A4[0] - 1.5 * cm, 0.72 * cm, f"Page {number}")
    c.save()
    buffer.seek(0)
    page.merge_page(PdfReader(buffer).pages[0])
    return page


def main() -> None:
    old = PdfReader(str(PDF))
    if len(old.pages) < 11:
        raise RuntimeError("The base report must contain at least the eleven variant-1 pages.")
    new = PdfReader(str(create_pages()))
    pages = list(old.pages[:11]) + list(new.pages)
    writer = PdfWriter()
    for index, page in enumerate(pages, start=1):
        writer.add_page(overlay(page, index))
    writer.add_metadata(
        {
            "/Title": "Étude de cas evolutive - Version 0.2",
            "/Author": "Équipe Monte-Carlo-Simulator",
        }
    )
    staged = TMP / "report_v02.pdf"
    with staged.open("wb") as stream:
        writer.write(stream)
    staged.replace(PDF)
    print(PDF)


if __name__ == "__main__":
    main()
