# ruff: noqa: E501
"""Generate the evolving PDF report for the synthetic building case study."""

from pathlib import Path

import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[2]
# Sorties de travail de l'étude de cas : générées, jamais versionnées.
WORK = ROOT / "data" / "output" / "case_study"
OUTPUT = ROOT / "reports" / "case_study" / "etude_cas_batiment_monte_carlo.pdf"
TMP = WORK / "tmp" / "pdfs" / "etude_cas_batiment"
HISTOGRAM = WORK / "simulation_batiment" / "simulation_histogram.png"
TORNADO = WORK / "simulation_batiment" / "sensitivity_tornado.png"
BASELINE_CHART = TMP / "baseline_percentiles.png"

NAVY = colors.HexColor("#17365D")
BLUE = colors.HexColor("#2F75B5")
LIGHT_BLUE = colors.HexColor("#D9EAF7")
PALE_BLUE = colors.HexColor("#EEF5FA")
ORANGE = colors.HexColor("#ED7D31")
GREEN = colors.HexColor("#70AD47")
RED = colors.HexColor("#C00000")
GREY = colors.HexColor("#666666")
LIGHT_GREY = colors.HexColor("#F2F2F2")


def register_fonts() -> tuple[str, str]:
    candidates = [
        (
            Path("C:/Windows/Fonts/arial.ttf"),
            Path("C:/Windows/Fonts/arialbd.ttf"),
        ),
        (
            Path("C:/Windows/Fonts/calibri.ttf"),
            Path("C:/Windows/Fonts/calibrib.ttf"),
        ),
    ]
    for regular, bold in candidates:
        if regular.exists() and bold.exists():
            pdfmetrics.registerFont(TTFont("ReportRegular", str(regular)))
            pdfmetrics.registerFont(TTFont("ReportBold", str(bold)))
            return "ReportRegular", "ReportBold"
    return "Helvetica", "Helvetica-Bold"


FONT, FONT_BOLD = register_fonts()


def P(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#B4C7DC"))
    canvas.line(1.5 * cm, 1.18 * cm, A4[0] - 1.5 * cm, 1.18 * cm)
    canvas.setFont(FONT, 8)
    canvas.setFillColor(GREY)
    canvas.drawString(1.5 * cm, 0.72 * cm, "Projet Monte-Carlo-Simulator - Étude de cas évolutive")
    canvas.drawRightString(A4[0] - 1.5 * cm, 0.72 * cm, f"Page {doc.page}")
    canvas.restoreState()


styles = getSampleStyleSheet()
body = ParagraphStyle(
    "Body",
    parent=styles["BodyText"],
    fontName=FONT,
    fontSize=9.3,
    leading=13.2,
    alignment=TA_JUSTIFY,
    textColor=colors.HexColor("#222222"),
    spaceAfter=7,
)
h1 = ParagraphStyle(
    "H1",
    parent=body,
    fontName=FONT_BOLD,
    fontSize=18,
    leading=22,
    textColor=NAVY,
    spaceBefore=4,
    spaceAfter=12,
)
h2 = ParagraphStyle(
    "H2",
    parent=body,
    fontName=FONT_BOLD,
    fontSize=12.5,
    leading=15,
    textColor=BLUE,
    spaceBefore=8,
    spaceAfter=7,
)
h3 = ParagraphStyle(
    "H3",
    parent=body,
    fontName=FONT_BOLD,
    fontSize=10.5,
    leading=13,
    textColor=NAVY,
    spaceBefore=6,
    spaceAfter=4,
)
small = ParagraphStyle(
    "Small",
    parent=body,
    fontSize=7.6,
    leading=10,
    alignment=TA_LEFT,
    spaceAfter=3,
)
caption = ParagraphStyle(
    "Caption",
    parent=small,
    fontName=FONT,
    fontSize=7.8,
    leading=10,
    alignment=TA_CENTER,
    textColor=GREY,
    spaceBefore=3,
    spaceAfter=8,
)
bullet_style = ParagraphStyle(
    "Bullet",
    parent=body,
    leftIndent=14,
    firstLineIndent=-8,
    bulletIndent=4,
    spaceAfter=4,
)
cover_title = ParagraphStyle(
    "CoverTitle",
    parent=h1,
    fontSize=28,
    leading=34,
    alignment=TA_CENTER,
    textColor=colors.white,
)
cover_subtitle = ParagraphStyle(
    "CoverSubtitle",
    parent=body,
    fontSize=13,
    leading=18,
    alignment=TA_CENTER,
    textColor=colors.white,
)
callout = ParagraphStyle(
    "Callout",
    parent=body,
    fontName=FONT_BOLD,
    fontSize=10,
    leading=14,
    textColor=NAVY,
    alignment=TA_LEFT,
)


def bullet(text: str) -> Paragraph:
    return P(f"• {text}", bullet_style)


def table(data, widths, header=True, font_size=7.3, row_bgs=None) -> Table:
    wrapped = []
    for row_index, row in enumerate(data):
        style = small
        if header and row_index == 0:
            style = ParagraphStyle(
                "TableHeader",
                parent=small,
                fontName=FONT_BOLD,
                textColor=colors.white,
                alignment=TA_CENTER,
            )
        wrapped.append([P(str(value), style) if value is not None else "" for value in row])
    result = Table(wrapped, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY if header else LIGHT_GREY),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B7C9D6")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for row_index in range(1 if header else 0, len(data)):
        if row_bgs and row_index in row_bgs:
            commands.append(("BACKGROUND", (0, row_index), (-1, row_index), row_bgs[row_index]))
        elif row_index % 2 == 0:
            commands.append(("BACKGROUND", (0, row_index), (-1, row_index), PALE_BLUE))
    result.setStyle(TableStyle(commands))
    return result


def make_baseline_chart() -> None:
    labels = ["Baseline", "Moyenne", "P50", "P80", "P90"]
    values = [7.75, 7.928325, 7.904221, 8.243501, 8.431266]
    bar_colors = ["#ED7D31", "#5B9BD5", "#70AD47", "#4472C4", "#17365D"]
    fig, ax = plt.subplots(figsize=(8.4, 3.2))
    bars = ax.barh(labels, values, color=bar_colors, height=0.58)
    ax.set_xlim(7.5, 8.55)
    ax.set_xlabel("Coût total (millions de MAD)")
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)
    for bar, value in zip(bars, values, strict=True):
        ax.text(
            value + 0.015,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.3f}",
            va="center",
            fontsize=9,
        )
    ax.spines[["top", "right", "left"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(BASELINE_CHART, dpi=180, bbox_inches="tight")
    plt.close(fig)


def scenario_diagram() -> Table:
    cells = [
        P(
            "<b>Variante 1</b><br/>Référence sans corrélation<br/><font size='8'>Réalisée</font>",
            callout,
        ),
        P(
            "<b>Variante 2</b><br/>Corrélations modérées et justifiées<br/><font size='8'>À construire</font>",
            callout,
        ),
        P(
            "<b>Variante 3</b><br/>Stress sur valeurs et événements<br/><font size='8'>À définir</font>",
            callout,
        ),
    ]
    arrows = [P("→", cover_subtitle), P("→", cover_subtitle)]
    diagram = Table(
        [[cells[0], arrows[0], cells[1], arrows[1], cells[2]]],
        colWidths=[5.1 * cm, 0.7 * cm, 5.1 * cm, 0.7 * cm, 5.1 * cm],
    )
    diagram.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), LIGHT_BLUE),
                ("BACKGROUND", (2, 0), (2, 0), colors.HexColor("#E2F0D9")),
                ("BACKGROUND", (4, 0), (4, 0), colors.HexColor("#FCE4D6")),
                ("BOX", (0, 0), (0, 0), 1.0, BLUE),
                ("BOX", (2, 0), (2, 0), 1.0, GREEN),
                ("BOX", (4, 0), (4, 0), 1.0, ORANGE),
                ("BACKGROUND", (1, 0), (1, 0), colors.white),
                ("BACKGROUND", (3, 0), (3, 0), colors.white),
                ("TEXTCOLOR", (1, 0), (3, 0), NAVY),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    return diagram


def build_report() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    make_baseline_chart()

    doc = BaseDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=1.55 * cm,
        rightMargin=1.55 * cm,
        topMargin=1.45 * cm,
        bottomMargin=1.45 * cm,
        title="Étude de cas évolutive - Projet bâtiment administratif",
        author="Équipe Monte-Carlo-Simulator",
        subject="Construction et comparaison de trois registres de risques synthétiques",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    doc.addPageTemplates(PageTemplate(id="main", frames=[frame], onPage=footer))

    story = []

    cover_box = Table(
        [
            [P("ÉTUDE DE CAS ÉVOLUTIVE", cover_subtitle)],
            [P("Simulation Monte Carlo des coûts d’un bâtiment administratif", cover_title)],
            [
                P(
                    "Construction progressive de trois variantes de registre de risques",
                    cover_subtitle,
                )
            ],
        ],
        colWidths=[17.4 * cm],
        rowHeights=[1.4 * cm, 5.6 * cm, 1.7 * cm],
    )
    cover_box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), NAVY),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BOX", (0, 0), (-1, -1), 1.2, NAVY),
            ]
        )
    )
    story += [Spacer(1, 2.0 * cm), cover_box, Spacer(1, 1.0 * cm)]
    story += [
        table(
            [
                ["État du document", "Version initiale après simulation de la variante 1"],
                ["Cas étudié", "Bâtiment administratif fictif R+1 d’environ 700 m² au Maroc"],
                ["Analyse", "Coût hors taxes en MAD"],
                ["Reproductibilité", "10 000 simulations, graine aléatoire 42"],
                ["Mise à jour suivante", "Variante 2 avec corrélations modérées et justifiées"],
            ],
            [4.2 * cm, 13.2 * cm],
            header=False,
            font_size=8.5,
        ),
        Spacer(1, 0.7 * cm),
        P(
            "Ce rapport est conçu comme une documentation vivante. Les hypothèses, résultats et décisions seront complétés à chaque nouvelle variante sans effacer l’historique des choix.",
            callout,
        ),
        PageBreak(),
    ]

    story += [P("1. Objet et logique de l’étude", h1)]
    story += [
        P(
            "L’objectif est de construire un cas d’étude synthétique suffisamment réaliste pour éprouver l’ensemble du workflow du simulateur Monte Carlo : saisie Excel, contrôle des paramètres, tirages probabilistes, percentiles, sensibilité, comparaison à une baseline et, dans un second temps, prise en compte des corrélations.",
            body,
        ),
        P(
            "Les données ne proviennent pas d’un projet confidentiel. Elles sont pédagogiques, arrondies et explicables. Elles ne doivent donc pas être utilisées comme un bordereau officiel de prix. Leur rôle est de produire un scénario cohérent permettant de discuter la méthode et les décisions budgétaires.",
            body,
        ),
        P("1.1 Stratégie des trois variantes", h2),
        scenario_diagram(),
        Spacer(1, 0.4 * cm),
        P(
            "Les trois variantes conservent le même projet et, autant que possible, la même structure de postes. Une seule famille d’hypothèses est modifiée à la fois. Cette règle rend les écarts de résultats interprétables : l’effet des corrélations peut être séparé de l’effet d’un stress sur les coûts ou les événements.",
            body,
        ),
        P("1.2 Questions auxquelles la comparaison devra répondre", h2),
        bullet("Quel budget correspond aux niveaux de confiance P50, P80 et P90 ?"),
        bullet("La baseline actuelle offre-t-elle une confiance suffisante ?"),
        bullet("Quels postes expliquent le plus la variabilité du coût total ?"),
        bullet(
            "Les corrélations augmentent-elles principalement la dispersion ou déplacent-elles aussi les percentiles ?"
        ),
        bullet("Quelle est la sensibilité des décisions à un scénario de stress raisonnable ?"),
        PageBreak(),
    ]

    story += [P("2. Présentation du projet fictif", h1)]
    story += [
        table(
            [
                ["Caractéristique", "Hypothèse retenue"],
                ["Ouvrage", "Bâtiment administratif R+1"],
                ["Surface indicative", "Environ 700 m²"],
                ["Localisation", "Maroc, sans localisation précise"],
                ["Périmètre", "Travaux, études, contrôle et risques de réalisation"],
                ["Exclusions", "Terrain, financement et fiscalité"],
                ["Monnaie", "Dirham marocain (MAD), montants hors taxes"],
                ["Baseline", "7 750 000 MAD"],
            ],
            [4.4 * cm, 13.0 * cm],
        ),
        P("2.1 Pourquoi ces familles de postes ?", h2),
        P(
            "Le découpage reprend les familles courantes visibles dans les bordereaux publics marocains de bâtiment : installation de chantier, terrassements et fouilles, fondations et béton armé, enveloppe, lots techniques, finitions et aménagements extérieurs. Un bordereau public du ministère des Habous relatif à un centre commercial illustre notamment la présence de l’installation de chantier, des fouilles, du béton de propreté, du béton en fondation et des armatures. Cette source justifie la structure des lots, mais pas les montants retenus.",
            body,
        ),
        P(
            "Les études, contrôles et la supervision sont ajoutés pour représenter les prestations de conception, de contrôle et de pilotage. Les risques événementiels couvrent ensuite les aléas qui seraient mal représentés par un simple élargissement des bornes : sol difficile, choc sur les matériaux, retard administratif, changement de programme ou défaillance d’un fournisseur.",
            body,
        ),
        P("2.2 Principes de prudence documentaire", h2),
        bullet("Les valeurs sont qualifiées d’hypothèses synthétiques dans le registre."),
        bullet(
            "Les sources publiques servent à justifier la structure et la méthode, jamais à présenter les montants comme des prix officiels."
        ),
        bullet("Les montants sont arrondis afin d’éviter une fausse précision."),
        bullet("Une future donnée réelle devra être anonymisée et conservée hors du dépôt public."),
        PageBreak(),
    ]

    continuous = [
        ["Poste", "Loi", "Paramètres (kMAD)", "Raison principale"],
        [
            "Études et contrôles",
            "Normale",
            "μ 250 ; σ 20",
            "Prestation relativement contractualisée et symétrique.",
        ],
        [
            "Installation du chantier",
            "PERT",
            "220 ; 280 ; 380",
            "Durée, sécurité et moyens temporaires.",
        ],
        ["Terrassement", "PERT", "300 ; 400 ; 650", "Sol, volumes, évacuation et productivité."],
        [
            "Fondations et gros œuvre",
            "PERT",
            "1 600 ; 1 900 ; 2 500",
            "Béton, acier, quantités et productivité.",
        ],
        [
            "Étanchéité et toiture",
            "Triangulaire",
            "400 ; 500 ; 700",
            "Peu d’information au-delà des trois points.",
        ],
        [
            "Façades et menuiseries",
            "PERT",
            "650 ; 750 ; 1 000",
            "Dimensions, matériaux, vitrage et fournisseurs.",
        ],
        [
            "Électricité",
            "PERT",
            "550 ; 650 ; 850",
            "Niveau d’équipement et modifications des réseaux.",
        ],
        ["Plomberie et sanitaires", "PERT", "400 ; 480 ; 650", "Quantités et gamme des appareils."],
        [
            "Climatisation et ventilation",
            "PERT",
            "450 ; 550 ; 800",
            "Dimensionnement et prix d’équipements spécialisés.",
        ],
        [
            "Revêtements et finitions",
            "PERT",
            "800 ; 950 ; 1 300",
            "Choix tardifs, reprises et qualité attendue.",
        ],
        [
            "Aménagements extérieurs",
            "PERT",
            "350 ; 450 ; 700",
            "Périmètre initial moins défini et conditions du site.",
        ],
        [
            "Supervision du chantier",
            "Normale",
            "μ 300 ; σ 45",
            "Coût régulier, sensible à une prolongation.",
        ],
    ]
    story += [P("3. Postes continus de la variante 1", h1)]
    story += [
        P(
            "Les paramètres sont affichés en milliers de MAD pour alléger la lecture. Dans Excel, tous les montants sont saisis en MAD complets. Pour PERT et la loi triangulaire, l’ordre est minimum, valeur la plus probable, maximum. Pour la loi normale, μ désigne la moyenne et σ l’écart-type.",
            body,
        ),
        table(continuous, [4.1 * cm, 2.1 * cm, 3.1 * cm, 8.1 * cm], font_size=7.0),
        Spacer(1, 0.3 * cm),
        P(
            "La somme des valeurs centrales ou moyennes des douze postes est de <b>7 460 000 MAD</b>. La baseline de 7 750 000 MAD contient donc une réserve initiale de 290 000 MAD, soit environ 3,9 % de cette estimation centrale.",
            callout,
        ),
        PageBreak(),
    ]

    events = [
        ["Événement", "Prob.", "Impact kMAD", "Justification"],
        [
            "Sol plus difficile que prévu",
            "12 %",
            "+350",
            "Reconnaissances géotechniques supposées incomplètes.",
        ],
        [
            "Hausse exceptionnelle des matériaux",
            "20 %",
            "+450",
            "Choc commun possible sur acier, ciment, équipements et finitions.",
        ],
        [
            "Retard administratif ou de raccordement",
            "18 %",
            "+250",
            "Prolongation possible de la supervision et des installations temporaires.",
        ],
        [
            "Modification tardive du programme",
            "15 %",
            "+300",
            "Études, reprises et commandes supplémentaires.",
        ],
        [
            "Défaillance ou remplacement d’un fournisseur",
            "10 %",
            "+220",
            "Nouvel achat, différence de prix ou retard.",
        ],
        [
            "Négociation commerciale favorable",
            "25 %",
            "-120",
            "Opportunité de remise ou de regroupement des commandes.",
        ],
    ]
    distributions = [
        ["Distribution", "Paramètres utilisés", "Règle d’emploi"],
        [
            "Beta-PERT",
            "minimum, mode, maximum ; λ = 4 par défaut",
            "Choix principal lorsqu’une estimation centrale crédible existe. Les tirages sont concentrés près du mode.",
        ],
        [
            "Triangulaire",
            "minimum, mode, maximum",
            "À utiliser lorsque seules trois estimations simples sont défendables.",
        ],
        [
            "Normale",
            "moyenne, écart-type",
            "Réservée aux coûts stables, approximativement symétriques, avec une dispersion faible devant la moyenne.",
        ],
        [
            "Événement",
            "probabilité, impact",
            "Zéro si l’événement ne survient pas ; impact positif pour une menace, négatif pour une opportunité.",
        ],
    ]
    story += [P("4. Événements et règles de distribution", h1)]
    story += [
        P("4.1 Risques événementiels", h2),
        table(events, [5.0 * cm, 1.5 * cm, 2.2 * cm, 8.7 * cm], font_size=7.1),
        P(
            "Les événements rares restent séparés des postes continus. Cette séparation évite de gonfler artificiellement les maxima des lots et permet de distinguer clairement la probabilité d’occurrence de la gravité financière.",
            body,
        ),
        P("4.2 Rôle des distributions", h2),
        table(distributions, [3.0 * cm, 4.5 * cm, 9.9 * cm], font_size=7.1),
        PageBreak(),
    ]

    maturity = [
        ["Maturité du poste", "Minimum indicatif", "Maximum indicatif", "Interprétation"],
        [
            "Bien défini ou contractualisé",
            "-5 % à -10 %",
            "+10 % à +15 %",
            "Faible incertitude résiduelle.",
        ],
        [
            "Moyennement défini",
            "-10 % à -15 %",
            "+20 % à +30 %",
            "Hypothèses encore susceptibles d’évoluer.",
        ],
        [
            "Encore incertain",
            "-15 % à -25 %",
            "+35 % à +60 %",
            "Quantités, choix ou conditions de site peu stabilisés.",
        ],
    ]
    story += [P("5. Règles de construction des paramètres", h1)]
    story += [
        P("5.1 Trois points crédibles", h2),
        bullet(
            "Le minimum décrit un déroulement favorable mais plausible, jamais un cas idéal impossible."
        ),
        bullet(
            "La valeur la plus probable représente l’estimation centrale raisonnable avec les informations disponibles."
        ),
        bullet(
            "Le maximum décrit un déroulement défavorable mais encore crédible. Les catastrophes rares sont modélisées comme événements séparés."
        ),
        P("5.2 Dispersion adaptée à la maturité", h2),
        table(maturity, [4.5 * cm, 3.0 * cm, 3.0 * cm, 6.9 * cm], font_size=7.2),
        P(
            "Ces intervalles sont des repères pédagogiques et non des normes automatiques. Ils servent à éviter deux défauts : appliquer le même pourcentage à tous les postes, ou choisir des bornes sans rapport avec la maturité technique du lot.",
            body,
        ),
        P("5.3 Asymétrie et prudence", h2),
        P(
            "Les coûts disposent généralement de plus de mécanismes de hausse que de baisse : quantités supplémentaires, reprises, inflation, retards, modifications ou indisponibilité d’un fournisseur. Pour cette raison, le maximum est souvent plus éloigné du mode que le minimum. Cette asymétrie ne doit toutefois pas servir à compter deux fois un même risque déjà présent dans la liste des événements.",
            body,
        ),
        P("5.4 Arrondi et traçabilité", h2),
        bullet("Arrondir les montants à 10 000 ou 50 000 MAD."),
        bullet("Documenter dans chaque ligne la raison de la loi et de sa dispersion."),
        bullet(
            "Conserver la baseline comme référence de comparaison, sans jamais l’ajouter aux tirages."
        ),
        bullet("Modifier une famille d’hypothèses à la fois entre deux variantes."),
        PageBreak(),
    ]

    story += [P("6. Variante 1 - Registre sans corrélation", h1)]
    story += [
        P(
            "La première variante contient 18 lignes actives : 12 postes continus et 6 événements. Elle ne comporte aucune feuille de corrélations. Les postes sont donc simulés indépendamment. Cette hypothèse constitue une référence de comparaison, pas une affirmation selon laquelle les risques réels seraient indépendants.",
            body,
        ),
        P("6.1 Paramètres d’exécution", h2),
        table(
            [
                ["Paramètre", "Valeur"],
                ["Nombre de tirages", "10 000"],
                ["Graine aléatoire", "42"],
                ["Unité", "MAD"],
                ["Baseline", "7 750 000 MAD"],
                ["Corrélations", "Aucune"],
                ["Tests automatisés", "337 tests réussis"],
            ],
            [5.2 * cm, 12.2 * cm],
        ),
        P("6.2 Résumé statistique", h2),
        table(
            [
                ["Indicateur", "Résultat", "Lecture"],
                ["Moyenne", "7 928 325 MAD", "Coût moyen simulé."],
                [
                    "Médiane / P50",
                    "7 904 221 MAD",
                    "Une simulation sur deux est inférieure à ce montant.",
                ],
                ["Écart-type", "374 795 MAD", "Dispersion autour de la moyenne."],
                ["P80", "8 243 501 MAD", "80 % des simulations sont inférieures à ce montant."],
                ["P90", "8 431 266 MAD", "90 % des simulations sont inférieures à ce montant."],
                [
                    "Minimum observé",
                    "6 798 203 MAD",
                    "Extrême de l’échantillon, pas une borne contractuelle.",
                ],
                [
                    "Maximum observé",
                    "9 719 143 MAD",
                    "Extrême de l’échantillon, pas une borne contractuelle.",
                ],
            ],
            [4.0 * cm, 4.0 * cm, 9.4 * cm],
        ),
        Spacer(1, 0.25 * cm),
        P(
            "Premier constat : la moyenne et les trois percentiles décisionnels sont supérieurs à la baseline. La réserve initiale de 290 000 MAD ne procure donc pas un niveau de confiance élevé dans ce scénario.",
            callout,
        ),
        PageBreak(),
    ]

    story += [P("7. Distribution simulée", h1)]
    story += [
        Image(str(HISTOGRAM), width=16.6 * cm, height=9.5 * cm),
        P(
            "Figure 1 - Histogramme du coût total simulé et repères de percentiles. Source : sortie du simulateur, variante 1, 10 000 tirages, graine 42.",
            caption,
        ),
        P(
            "L’histogramme représente la fréquence des coûts totaux produits par les 10 000 tirages. La distribution est centrée autour de 7,9 M MAD et présente une queue à droite, cohérente avec des fourchettes de coût asymétriques et plusieurs événements de menace à impact positif.",
            body,
        ),
        P(
            "Les percentiles répondent à une question de confiance budgétaire. P80 n’est pas une hausse certaine de 493 501 MAD par rapport à la baseline : il s’agit du budget qui ne serait dépassé que dans environ 20 % des simulations, sous réserve que les hypothèses du registre soient jugées crédibles.",
            body,
        ),
        PageBreak(),
    ]

    story += [P("8. Comparaison à la baseline", h1)]
    story += [
        Image(str(BASELINE_CHART), width=16.7 * cm, height=6.4 * cm),
        P(
            "Figure 2 - Position de la baseline par rapport à la moyenne et aux percentiles de la variante 1.",
            caption,
        ),
        table(
            [
                ["Mesure", "Valeur", "Écart à la baseline", "Écart relatif"],
                ["P50", "7 904 221 MAD", "+154 221 MAD", "+1,99 %"],
                ["P80", "8 243 501 MAD", "+493 501 MAD", "+6,37 %"],
                ["P90", "8 431 266 MAD", "+681 266 MAD", "+8,79 %"],
                ["Probabilité de dépassement", "65,96 %", "-", "-"],
            ],
            [4.7 * cm, 4.0 * cm, 4.5 * cm, 4.2 * cm],
        ),
        Spacer(1, 0.3 * cm),
        P(
            "La baseline de 7,75 M MAD est dépassée dans 65,96 % des simulations. Autrement dit, elle correspond à un niveau de confiance inférieur à P50. Pour viser P80, la réserve totale par rapport à l’estimation centrale de 7,46 M MAD devrait atteindre environ 783 501 MAD, sous les hypothèses de la variante 1.",
            body,
        ),
        P(
            "Cette conclusion reste conditionnelle. Elle ne signifie pas que le projet coûtera exactement P80 ou P90 ; elle indique le compromis entre budget et confiance produit par le modèle actuel.",
            body,
        ),
        PageBreak(),
    ]

    story += [P("9. Analyse de sensibilité", h1)]
    story += [
        Image(str(TORNADO), width=16.6 * cm, height=9.7 * cm),
        P(
            "Figure 3 - Diagramme tornado fondé sur la corrélation de rang de Spearman entre chaque contribution simulée et le coût total.",
            caption,
        ),
        P(
            "Les principaux facteurs associés à la variation du coût total sont la hausse exceptionnelle des matériaux (ρ = 0,474), les fondations et le gros œuvre (ρ = 0,446), le sol plus difficile que prévu (ρ = 0,306), la modification tardive du programme (ρ = 0,271) et le retard administratif ou de raccordement (ρ = 0,266).",
            body,
        ),
        P(
            "Le coefficient de Spearman mesure une association monotone, pas une causalité. Il dépend aussi de la plage et de la probabilité données à chaque poste. Un poste important mais très stable peut apparaître moins sensible qu’un événement plus petit mais très variable.",
            body,
        ),
        P(
            "L’opportunité de négociation est corrélée positivement au total lorsqu’on mesure la contribution monétaire simulée : sa contribution vaut soit 0, soit -120 000 MAD ; les valeurs les plus élevées de cette contribution, c’est-à-dire 0, accompagnent logiquement des totaux plus élevés.",
            body,
        ),
        PageBreak(),
    ]

    story += [P("10. Interprétation et limites de la variante 1", h1)]
    story += [
        P("10.1 Enseignements provisoires", h2),
        bullet(
            "La baseline est insuffisante pour atteindre P50, P80 ou P90 dans le registre actuel."
        ),
        bullet("Le risque de prix des matériaux et le gros œuvre dominent la sensibilité."),
        bullet(
            "Les risques géotechniques, de programme et de retard constituent un second groupe prioritaire."
        ),
        bullet(
            "La simulation produit déjà une information décisionnelle, mais sa qualité dépend directement de la crédibilité des hypothèses."
        ),
        P("10.2 Limites", h2),
        bullet(
            "Les montants et probabilités sont synthétiques et n’ont pas encore été validés par un spécialiste métier."
        ),
        bullet(
            "L’indépendance entre postes peut sous-estimer la probabilité de plusieurs hausses simultanées."
        ),
        bullet(
            "Les percentiles issus de 10 000 tirages comportent une erreur d’échantillonnage faible mais non nulle."
        ),
        bullet(
            "Le modèle traite les impacts événementiels comme déterministes lorsqu’ils surviennent."
        ),
        bullet(
            "Une courbe en S empirique est désormais produite ; le calendrier de décaissement et l inflation temporelle restent hors du modèle."
        ),
        P("10.3 Décision avant de poursuivre", h2),
        P(
            "La variante 1 devient la référence figée de comparaison. Les prochaines modifications ne devront pas l’écraser. Les mêmes nombres de tirages, graine, percentiles et conventions d’unité seront conservés pour isoler l’effet des hypothèses nouvelles.",
            callout,
        ),
        PageBreak(),
    ]

    correlations = [
        ["Relation envisagée", "Coefficient initial", "Justification à valider"],
        [
            "Terrassement / fondations et gros œuvre",
            "0,30",
            "Des conditions de sol défavorables peuvent affecter les deux lots.",
        ],
        [
            "Fondations et gros œuvre / hausse des matériaux",
            "0,50",
            "Le gros œuvre consomme beaucoup de béton et d’acier.",
        ],
        [
            "Électricité / plomberie",
            "0,25",
            "Les modifications d’aménagement peuvent toucher plusieurs réseaux.",
        ],
        [
            "Supervision / retard administratif",
            "0,40",
            "Un retard augmente la durée de mobilisation de la supervision.",
        ],
    ]
    story += [P("11. Programme des prochaines mises à jour", h1)]
    story += [
        P("11.1 Variante 2 - Corrélations modérées", h2),
        table(correlations, [6.0 * cm, 3.0 * cm, 8.4 * cm], font_size=7.2),
        P(
            "Ces coefficients sont des propositions de travail, pas des valeurs validées. La matrice devra être symétrique, avoir une diagonale égale à 1 et être strictement définie positive. La documentation devra préciser la source ou le jugement ayant conduit à chaque relation.",
            body,
        ),
        P("11.2 Variante 3 - Stress", h2),
        bullet("Conserver la structure du projet et les corrélations validées de la variante 2."),
        bullet(
            "Élargir de manière explicite certaines bornes supérieures ou augmenter certaines probabilités."
        ),
        bullet("Réduire éventuellement la valeur ou la probabilité de l’opportunité commerciale."),
        bullet(
            "Éviter un stress uniforme : cibler les hypothèses qui représentent un contexte réellement défavorable."
        ),
        P("11.3 Tableau de comparaison à compléter", h2),
        table(
            [
                ["Indicateur", "Variante 1", "Variante 2", "Variante 3"],
                ["Hypothèse distinctive", "Indépendance", "Corrélations", "Stress"],
                ["Moyenne", "7,928 M MAD", "À calculer", "À calculer"],
                ["P50", "7,904 M MAD", "À calculer", "À calculer"],
                ["P80", "8,244 M MAD", "À calculer", "À calculer"],
                ["P90", "8,431 M MAD", "À calculer", "À calculer"],
                ["Dépassement baseline", "65,96 %", "À calculer", "À calculer"],
                ["Premier facteur de sensibilité", "Hausse matériaux", "À calculer", "À calculer"],
            ],
            [5.2 * cm, 4.1 * cm, 4.1 * cm, 4.0 * cm],
        ),
        PageBreak(),
    ]

    story += [P("12. Sources et traçabilité", h1)]
    story += [
        P(
            "Les références suivantes justifient les familles de travaux et les principes méthodologiques. Elles ne justifient pas directement les montants synthétiques.",
            body,
        ),
        P(
            "1. Ministère des Habous et des Affaires islamiques, bordereau public de construction d’un centre commercial à Azrou, comprenant notamment installation de chantier, fouilles, béton et armatures.<br/><font color='#2F75B5'>https://habous.gov.ma/fr/index.php?cf_id=36&amp;link_id=353&amp;option=com_mtree&amp;task=att_download</font>",
            small,
        ),
        P(
            "2. Haut-Commissariat au Plan du Maroc, rubrique Indices des prix et production, utilisée comme point d’entrée pour le contexte des variations de prix.<br/><font color='#2F75B5'>https://www.hcp.ma/Indices-des-prix-et-production_r343.html</font>",
            small,
        ),
        P(
            "3. HM Treasury, Green Book supplementary guidance: optimism bias. La guidance recommande des ajustements explicites fondés sur des projets passés ou similaires lorsque les prévisions tendent à être optimistes.<br/><font color='#2F75B5'>https://www.gov.uk/government/publications/green-book-supplementary-guidance-optimism-bias</font>",
            small,
        ),
        P(
            "4. HM Treasury, The Green Book 2026. Le document mentionne l’analyse Monte Carlo pour les projets comportant plusieurs variables fortement incertaines et distingue la contingence destinée à couvrir les risques résiduels.<br/><font color='#2F75B5'>https://www.gov.uk/government/publications/the-green-book-appraisal-and-evaluation-in-central-government/the-green-book-2026</font>",
            small,
        ),
        P(
            "5. Homes England, Optimism Bias and Contingency. Le rapport présente la prévision par classe de référence et l’usage de niveaux tels que P50 et P80 pour éclairer la contingence.<br/><font color='#2F75B5'>https://www.gov.uk/government/publications/optimism-bias-and-contingency-at-homes-england/optimism-bias-and-contingency-at-homes-england-accessible-version</font>",
            small,
        ),
        P(
            "6. Fichiers internes de traçabilité : registre Excel synthétique, résumé de simulation, comparaison baseline, sensibilité Spearman, histogramme et tornado produits par Monte-Carlo-Simulator.",
            small,
        ),
        Spacer(1, 0.5 * cm),
        P("Journal de mise à jour", h2),
        table(
            [
                ["Version", "Contenu ajouté", "État"],
                [
                    "0.1",
                    "Projet fictif, règles de paramétrage, variante 1 et résultats complets",
                    "Présente version",
                ],
                ["0.2", "Variante 2, matrice de corrélation et comparaison", "À venir"],
                ["0.3", "Variante 3 stressée et comparaison consolidée", "À venir"],
                ["1.0", "Validation métier, objections, décisions et conclusion", "À venir"],
            ],
            [2.5 * cm, 10.9 * cm, 4.0 * cm],
        ),
    ]

    doc.build(story)
    print(OUTPUT)


if __name__ == "__main__":
    build_report()
